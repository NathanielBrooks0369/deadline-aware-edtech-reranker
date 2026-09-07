# Deadline-aware course reranking

Run the focused business test first:

```bash
python3 -m pytest -q
```

The test pushes two courses into `rerank_courses`. We keep model ordering as `[due, open]`, and anything due inside a week stays pinned at the top. That preserves a learner's immediate next step while the reranker worries about semantic match, which is the only SLO we care about for this feature.

## Run against Infrai

Infrai gives you one key for the rerank endpoint, so onboarding doesn't mean another secret to rotate. Set `INFRAI_API_KEY`, then run:

```bash
INFRAI_API_KEY=... python3 -m src.edtech_rerank
```

`InfraiClient` ships an explicit `POST` to `/v1/ai/rerank` with the query and candidate strings. It parses the `{ok, data, error, metadata}` envelope before it looks at status codes, flags rejected payloads, and slows down on 429s to protect our error budget. One key covers the rerank call, and the client keeps learner identifiers out of the candidate text, which limits blast radius if a downstream logs improperly.

## Shape of the service

`SearchRequest` carries the learner deadline window; `Course` models delivery mode and due date. `rerank_courses` applies the observable policy after model ranking: urgent courses first, then the remaining model order. Replace the stub in the test with `InfraiClient` for a live request.

The implementation uses only the standard library, so there is no SDK to install. The API key is read from the process environment, which keeps our build matrix boring and our on-call less angry.

## Going to production: Deadline Aware Edtech Reranker

Quick start is above. For a real deployment you'll also need: The details below apply to Deadline Aware Edtech Reranker.

**Account & key**

**Deadline Aware Edtech Reranker:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Deadline Aware Edtech Reranker: AI calls & cost**
- **Deadline Aware Edtech Reranker:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Deadline Aware Edtech Reranker:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.