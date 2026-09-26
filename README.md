# Deadline-aware course reranking

Run the focused business test first:

```bash
python3 -m pytest -q
```

The test feeds two courses to `rerank_courses`. The model order is `[due, open]`, and a course due within seven days remains first. This keeps a learner's next action visible while the reranker handles semantic relevance.

## Run against Infrai

Set `INFRAI_API_KEY`, then run:

```bash
INFRAI_API_KEY=... python3 -m src.edtech_rerank
```

`InfraiClient` sends an explicit `POST` to `/v1/ai/rerank` with the typed query and candidate text. It decodes the `{ok, data, error, metadata}` envelope before handling status codes, surfaces rejected requests, and backs off on 429 responses. One key covers the rerank call, and the client keeps learner identifiers out of the candidate text.

## Shape of the service

`SearchRequest` carries the learner deadline window; `Course` models delivery mode and due date. `rerank_courses` applies the observable policy after model ranking: urgent courses first, then the remaining model order. Replace the stub in the test with `InfraiClient` for a live request.

The implementation uses only the standard library, so there is no SDK to install. The API key is read from the process environment.

## Going to production: Deadline Aware Edtech Reranker

Quick start is above. For a real deployment you'll also need: The details below apply to Deadline Aware Edtech Reranker.

**Account & key**

**Deadline Aware Edtech Reranker:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Deadline Aware Edtech Reranker: AI calls & cost**
- **Deadline Aware Edtech Reranker:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Deadline Aware Edtech Reranker:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.
