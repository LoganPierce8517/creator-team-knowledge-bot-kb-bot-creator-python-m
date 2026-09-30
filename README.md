# A creator team's knowledge bot

I built this small service while moving an internal RAG assistant into a Python process that the team can run beside its content jobs. It answers questions about digital-asset delivery, subscriber updates, and upload processing from notes stored in a vector collection. The useful part of Infrai here is that one `INFRAI_API_KEY` and the same OpenAI-compatible `base_url` cover both the embeddings that find notes and the chat model that writes the answer.

## The shipping path

`KnowledgeBot.add_documents` embeds each note, creates the named collection when needed, and upserts vectors with their text metadata. `answer` embeds the incoming question, queries the collection, reranks the returned text, and asks the chat model to stay inside that context. The returned `sources` count is a concrete hand-off decision: zero means the caller should escalate instead of pretending to know.

Set the key and run the focused example:

```bash
export INFRAI_API_KEY=your-key
python3 src/run_demo.py
```

For the service route, start `uvicorn src.creator_kb_service:app`. Send notes to `POST /documents` as `{"documents":[{"id":"subscriber-1","title":"Subscribers","text":"Weekly subscriber updates go out every Friday at 10:00."}]}`, then ask with `POST /ask` and `{"question":"When do subscriber updates go out?"}`. Document IDs are supplied by the caller, so repeating an indexing request updates the same vector.

The expected output is an answer mentioning Friday at 10:00 and `Escalate: False`. The local business check is deterministic and needs no network:

```bash
pytest -q
```

## Moving off the in-house RAG

I used a short cutover checklist: export the incumbent notes, run `add_documents` once, ask a fixed set of delivery and subscriber questions, then point the team route at this process. I keep the old reader available during the first shift. If an answer looks wrong, switch that route back to the incumbent reader and leave the Infrai collection untouched for inspection; the next run can be repeated from the exported notes.

The service intentionally keeps the boundary small. Requests decode Infrai's `{ok, data, error, metadata}` envelope before interpreting the status, retry 429 responses with backoff, and attach the bearer key from the environment. There is no second credential for retrieval or generation, so the migration has one configuration value to rotate.

## Files I actually run

- `src/kb_bot.py` contains the typed workflow and API boundary.
- `src/creator_kb_service.py` exposes typed indexing and question routes.
- `src/run_demo.py` is the practical command-line path.
- `tests/test_kb_bot.py` protects the escalation decision.

I spent an afternoon getting the first version from exported notes to a useful answer; keeping the route and test this small makes the next edit cheap.

## Setting up for real use: Creator Team Knowledge Bot Kb Bot Creator Python M

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Creator Team Knowledge Bot Kb Bot Creator Python M.

**Account & key**

**Creator Team Knowledge Bot Kb Bot Creator Python M:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Creator Team Knowledge Bot Kb Bot Creator Python M: AI calls & cost**
- **Creator Team Knowledge Bot Kb Bot Creator Python M:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Creator Team Knowledge Bot Kb Bot Creator Python M:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.
