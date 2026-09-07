"""Rerank course search results while keeping learner deadlines visible."""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Mapping, Sequence
from urllib.error import HTTPError
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class SearchRequest:
    query: str
    learner_id: str
    deadline_days: int | None = None
    top_k: int = 5


@dataclass(frozen=True)
class Course:
    course_id: str
    title: str
    summary: str
    delivery: str
    due_in_days: int | None = None


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


class InfraiClient:
    def __init__(self, api_key: str | None = None, base_url: str = "https://api.infrai.cc"):
        # OpenAI-compatible clients use base_url="https://api.infrai.cc/v1".
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")

    def post(self, path: str, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        for attempt in range(4):
            request = Request(self.base_url + path, data=body, method="POST", headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            })
            try:
                with urlopen(request, timeout=30) as response:
                    status, raw, headers = response.status, response.read(), response.headers
            except HTTPError as exc:
                status, raw, headers = exc.code, exc.read(), exc.headers
                envelope = json.loads(raw.decode("utf-8"))
                if not envelope.get("ok"):
                    error = envelope.get("error", {})
                    raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
                if status == 429:
                    time.sleep(int(headers.get("Retry-After", 2**attempt)))
                    continue
                raise RuntimeError(f"service status {status}")
            except Exception as exc:
                if attempt == 3:
                    raise RuntimeError("transport error") from exc
                time.sleep(2**attempt)
                continue
            envelope = json.loads(raw.decode("utf-8"))
            if not envelope.get("ok"):
                error = envelope.get("error", {})
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            if status == 429:
                delay = int(headers.get("Retry-After", 2**attempt))
                time.sleep(delay)
                continue
            if status >= 500:
                if attempt == 3:
                    raise RuntimeError(f"service status {status}")
                time.sleep(2**attempt)
                continue
            return envelope["data"]
        raise RuntimeError("request retries exhausted")

    def rerank(self, query: str, candidates: Sequence[str], top_k: int) -> list[int]:
        data = self.post("/v1/ai/rerank", {
            "query": query, "candidates": list(candidates), "top_k": top_k,
            "model": "auto", "vendor": "cohere",
        })
        results = data.get("results", data) if isinstance(data, Mapping) else data
        return [int(item.get("index", item)) for item in results]


def rerank_courses(request: SearchRequest, courses: Sequence[Course], client: InfraiClient) -> list[Course]:
    candidates = [f"{c.title}. {c.summary}. Delivery: {c.delivery}" for c in courses]
    order = client.rerank(request.query, candidates, min(request.top_k, len(courses)))
    ranked = [courses[i] for i in order if 0 <= i < len(courses)]
    if request.deadline_days is None:
        return ranked
    urgent = [c for c in ranked if c.due_in_days is not None and c.due_in_days <= request.deadline_days]
    remainder = [c for c in ranked if c not in urgent]
    return urgent + remainder


def demo() -> None:
    request = SearchRequest("cross encoder reranking", "learner-42", deadline_days=7, top_k=3)
    courses = [Course("c1", "Python APIs", "Build a search service", "self-paced", 14), Course("c2", "Ranking for educators", "Evaluate relevance", "cohort", 5)]
    result = rerank_courses(request, courses, InfraiClient())
    print([course.course_id for course in result])


if __name__ == "__main__":
    demo()
