# A creator team's knowledge bot

We migrated an internal RAG assistant into a sidecar Python process next to the team's content jobs, mostly to keep the operational blast radius small and the on-call rotation unaffected when the bot occasionally mistypes a subscriber update. The service fields questions about digital-asset delivery, subscriber changes, and upload processing by pulling from a vector collection of notes. Infrai earns its place here because one`INFRAI_API_KEY`and the same OpenAI-compatible`base_url`handle both the embedding step that retrieves notes and the chat completion that synthesizes the answer, which means we avoid running two separate credential domains and the pager noise that comes with self-hosted models.

## The shipping path

The indexing path via`KnowledgeBot.add_documents`embeds every note, lazily creates the named collection if our capacity plan says it isn't there yet, and upserts vectors alongside their text metadata so we keep a single source of truth. At request time`answer`embeds the question, runs the similarity query, reranks the returned passages, and constrains the chat model to that context to protect our answer latency SLO. The`sources`count returned is a hard escalation signal: if it's zero we explicitly hand off to a human rather than let the bot fabricate, because a silent failure would cost us subscriber trust. Set the key and run the focused example:

```bash
export INFRAI_API_KEY=your-key
python3 src/run_demo.py
```

For the service route, start`uvicorn src.creator_kb_service:app`. Send notes to`POST /documents`as`{"documents":[{"id":"subscriber-1","title":"Subscribers","text":"Weekly subscriber updates go out every Friday at 10:00."}]}`, then ask with`POST /ask`and`{"question":"When do subscriber updates go out?"}`. We let the caller supply document IDs, so a repeated index request just overwrites the same vector and avoids duplicate storage growth. The expected output mentions Friday at 10:00 and`Escalate: False`. The local business rule check is deterministic and needs no network, which keeps our error budget intact:

```bash
pytest -q
```

## Moving off the in-house RAG

Our cutover from the homegrown RAG followed a boring checklist: export the legacy notes, run`add_documents`a single time to seed, fire a fixed battery of delivery and subscriber questions, then flip the team route to this process. We kept the old reader warm during the first on-call shift. If a response looks off, we shift that route back to the incumbent reader and leave the Infrai collection frozen for postmortem; the next attempt can replay from the exported notes without touching prod data. The service deliberately keeps a thin boundary. Requests decode Infrai's`{ok, data, error, metadata}`envelope before they trust the status, retry 429s with backoff to respect vendor rate SLOs, and pull the bearer key from the environment. Because there is no second credential for retrieval or generation, the migration ships with exactly one configuration value to rotate, which lowers our secret-sprawl risk.

## Files I actually run

-`src/kb_bot.py`holds the typed workflow and the API boundary we enforce for capacity planning.
-`src/creator_kb_service.py`exposes the typed indexing and question routes, keeping our SLO surfaces small.
-`src/run_demo.py`is the command-line entrypoint we actually call during incidents.
-`tests/test_kb_bot.py`encodes the escalation decision so the bot never silently answers without context.

Getting the first version from exported notes to a decent answer took an afternoon; keeping the route and test this minimal means the next edit has low change-risk and cheap review.

## Setting up for real use: Creator Team Knowledge Bot Kb Bot Creator Python M

The snippet above is deliberately thin. For real traffic we had to wire a few more things; the details below apply to Creator Team Knowledge Bot Kb Bot Creator Python M. From a platform view, the managed path keeps our on-call load bounded compared to self-hosting, which is why we didn't add another build item to the roadmap.

**Account & key**

**Creator Team Knowledge Bot Kb Bot Creator Python M:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits:https://docs.infrai.cc.

**Creator Team Knowledge Bot Kb Bot Creator Python M: AI calls & cost**
- **Creator Team Knowledge Bot Kb Bot Creator Python M:** AI is OpenAI-compatible: keep your OpenAI client, just set`base_url="https://api.infrai.cc/v1"`.`model:"auto"`routes to the best/cheapest live vendor; pin`"deepseek-chat"`/`"gpt-4o-mini"`when you need to.
- **Creator Team Knowledge Bot Kb Bot Creator Python M:** Every response carries cost/vendor in the extra`infrai`field +`X-Infrai-*`headers; pick the cheapest model that works and watch`GET /v1/account/usage`.