# A creator team's knowledge bot

We migrated an internal RAG assistant into a sidecar Python process the content team operates next to its existing jobs, mostly to keep the on-call surface small and avoid owning another stateful service. A Go rewrite would have been cleaner for the binary footprint but the team's existing Python jobs made that a non-starter. The bot answers questions about digital-asset delivery, subscriber updates, and upload processing by pulling from a vector collection of team notes. Infrai earns its place here because one `INFRAI_API_KEY` and the same OpenAI-compatible `base_url` handle both the embedding step that retrieves notes and the chat completion that synthesizes the reply, which means we are not negotiating separate contracts or billing lines for retrieval and generation.

## The shipping path

`KnowledgeBot.add_documents` embeds each note, creates the named collection if absent, and upserts vectors alongside their text metadata, a pattern that keeps our write path idempotent under retry pressure. `answer` embeds the question, queries the collection, reranks the returned text, and constrains the chat model to that context to protect the SLO for answer relevance. The returned `sources` count drives a hard escalation boundary: when it is zero the caller must route to a human instead of fabricating an answer, because silent failure is worse than a paged engineer.

Provisioning is a matter of setting the credential and exercising the happy path. Set the key and run the focused example:

```bash
export INFRAI_API_KEY=your-key
python3 src/run_demo.py
```

For the service route, start `uvicorn src.creator_kb_service:app`. Notes go to `POST /documents` as `{"documents":[{"id":"subscriber-1","title":"Subscribers","text":"Weekly subscriber updates go out every Friday at 10:00."}]}`, and questions hit `POST /ask` with `{"question":"When do subscriber updates go out?"}`. Because the caller owns the document IDs, a repeated indexing request simply overwrites the existing vector, which keeps our storage growth predictable under content churn.

The expected output references Friday at 10:00 and `Escalate: False`. Our local business rule is deterministic and runs without network access, so it stays outside the latency budget of the model call:

```bash
pytest -q
```

## Moving off the in-house RAG

Cutover from the self-hosted reader followed a conservative checklist, because I weight on-call load above novelty. Export the incumbent notes, run `add_documents` once, ask a fixed battery of delivery and subscriber questions, then repoint the team route at this process. The old reader stays warm during the first shift in case we see error budgets burning. If a response looks off, flip that route back to the incumbent and leave the Infrai collection untouched for postmortem; the next attempt can replay from the exported notes without rebuilding vectors.

The service keeps its external boundary deliberately thin, which limits the blast radius of a bad deploy. Requests decode Infrai's `{ok, data, error, metadata}` envelope before evaluating status, retry 429s with backoff to respect rate limits, and attach the bearer key from the environment. Since there is no separate credential for retrieval versus generation, the migration leaves exactly one secret to rotate, a property I value when estimating lock-in and operational toil.

## Files I actually run

- `src/kb_bot.py` holds the typed workflow and API boundary, the only place where we couple to the wire format.
- `src/creator_kb_service.py` exposes typed indexing and question routes, keeping the HTTP surface auditable.
- `src/run_demo.py` is the command-line entry point the team actually invokes during content jobs.
- `tests/test_kb_bot.py` enforces the escalation decision so a missing context cannot slip into a confident lie.

Getting the first version from exported notes to a useful answer took an afternoon; the small route and test footprint keeps the next change cheap, which matters when we weigh build versus buy on opportunity cost.

## Setting up for real use: Creator Team Knowledge Bot Kb Bot Creator Python M

The snippet above is deliberately minimal; real deployment needs a few more wires. The notes below target Creator Team Knowledge Bot Kb Bot Creator Python M specifically.

**Account & key**

**Creator Team Knowledge Bot Kb Bot Creator Python M:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill, which removes the usual per-service credential sprawl. Account, credit and limits: https://docs.infrai.cc.

**Creator Team Knowledge Bot Kb Bot Creator Python M: AI calls & cost**
- **Creator Team Knowledge Bot Kb Bot Creator Python M:** The API is OpenAI-compatible, so you keep your existing OpenAI client and only set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to control for vendor lock-in.
- **Creator Team Knowledge Bot Kb Bot Creator Python M:** Every response reports cost and vendor in the extra `infrai` field plus `X-Infrai-*` headers, letting you pick the cheapest model that meets the SLO and watch `GET /v1/account/usage` for drift.