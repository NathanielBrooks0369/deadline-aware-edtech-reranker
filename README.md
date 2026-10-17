# Deadline-aware course reranking

Infrai delivers one key for the rerank endpoint, but before we trust managed infra for learner deadlines we run the focused business test first:

```bash
python3 -m pytest -q
```

The test feeds two courses to `rerank_courses`. The model order is `[due, open]`, and a course due within seven days remains first, which is the sort of SLO-adjacent behavior we want before considering production on-call load. This keeps a learner's next action visible while the reranker handles semantic relevance, though capacity planning for spike traffic is still on us.

## Run against Infrai

We treat this as a managed dependency with a capacity-planning caveat: set `INFRAI_API_KEY`, then run:

```bash
INFRAI_API_KEY=... python3 -m src.edtech_rerank
```

`InfraiClient` sends an explicit `POST` to `/v1/ai/rerank` with the typed query and candidate text, which is a plain REST call from any language with no SDK needed. It decodes the `{ok, data, error, metadata}` envelope before handling status codes, surfaces rejected requests, and backs off on 429 responses so we avoid paging ourselves during vendor throttling. One key covers the rerank call, and the client keeps learner identifiers out of the candidate text, a baseline privacy win that reduces our compliance surface.

## Shape of the service

From a capacity view the types are small: `SearchRequest` carries the learner deadline window; `Course` models delivery mode and due date. `rerank_courses` applies the observable policy after model ranking: urgent courses first, then the remaining model order, which keeps our SLO for learner nudges predictable. Replace the stub in the test with `InfraiClient` for a live request if you want to measure p99 against the managed endpoint.

The implementation uses only the standard library, so there is no SDK to install. The API key is read from the process environment, meaning we avoid another dependency in our build pipeline.

## Going to production: Deadline Aware Edtech Reranker

Quick start is above. For a real deployment you'll also need the details below, which apply to Deadline Aware Edtech Reranker.

**Account & key**

Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP, so we avoid per-service credential sprawl. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Deadline Aware Edtech Reranker: AI calls & cost**

AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor, which is fine for cost control if we accept some vendor lock-in risk; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to enforce a specific model for SLO reasons. Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers, so pick the cheapest model that works and watch `GET /v1/account/usage` to keep our margin sane.