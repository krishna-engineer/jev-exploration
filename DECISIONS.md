# Decisions

Why we chose what we chose, and what we deferred. `ROADMAP.md` holds the plan; this file holds the reasoning.

## Price ranking uses `price_in + price_out` (2026-10-07)

**Decision:** V1 ranks models by the plain sum of input and output price per 1M tokens. The weights live as constants (`PRICE_IN_WEIGHT`, `PRICE_OUT_WEIGHT`, both 1) at the top of `recommender/rank.py`, so changing them is a one-line edit.

**Rejected:** a weighted blend such as `price_in * 3 + price_out` as the default. The 3 stands in for "tasks send about 3x more input than they generate", which is a guess that varies a lot by task (summarization is far more input-heavy than long-form writing). The plain sum also assumes a ratio (1:1), but it is easier to explain and adds no hidden policy. A separate config file was also rejected as more machinery than two numbers need.

**Deferred:** a per-request cost estimate from expected token volume, where the in/out ratio comes from the task itself (possibly from a Jev judgment). The constants would then become a default. See "Later ideas" in `ROADMAP.md`.

**Note:** the sum only orders models. It is not a real per-request cost.

## Tie-breaks: newest release, then largest context (2026-10-15)

**Decision:** the sort key is `(price, age in days, -context)`, ascending. Many models share a price, so ties go to the newest release, then the largest context window.

**Why:** without tie-breaks the order of equally priced models depends on catalog order, which is arbitrary. Age is computed as days since `release_date`; a smaller age sorts first.

**Note:** "larger context wins ties" and "newer wins ties" are policy choices, not facts. Revisit them if a quality signal arrives.

## `premium` means costliest, not best (2026-10-07)

**Decision:** `cost_preference: "premium"` ranks by price descending. It is done by negating the price part of the key (sign `-1`), not by `reverse=True`.

**Why:** with no quality signal, price is the only proxy available, and it does not prove a model is better. The reason text states this plainly. Negation keeps the tie-break direction the same in both modes; `reverse=True` would flip ties to oldest-first.

**Revisit:** when a benchmark signal exists, `premium` can rank by quality instead. If more sort fields with their own directions are added, switch from negation to a stable multi-pass sort or a table of `(key, reverse)` pairs.

**Note:** any `cost_preference` other than `"premium"` (including typos) behaves as `cheapest`, in both ranking and the reason text.

## Missing or zero prices are dropped in `filter_models` (2026-10-15)

**Decision:** models with a price of 0 in either direction are removed at the start of `filter_models`.

**Why:** a missing price stored as 0 would win `cheapest` for the wrong reason, and would pass any `max_price_*` cap (`0 <= cap`). Eligibility is `filter_models`' job, so `rank_models` can assume prices are real.

**Note:** `fetch.py` already skips models with no `cost` object and fails loudly if `input` or `output` is absent, so a `None` price cannot reach the catalog. Only the zero case needed a guard.

## Models with no release date count as oldest (2026-10-15)

**Decision:** `get_age_in_days` returns `UNKNOWN_AGE_DAYS = 3650` (about 10 years) when `release_date` is missing, so those models lose ties.

**Why:** a missing date says nothing about whether a model can do the job, so dropping it would lose valid candidates. The constant only has to exceed the age of any real model.

**Rejected:** a "realistic" value such as 4 years, because real models can already be near that age and the margin shrinks daily.

## Response shape: one reason, a ranked list (2026-10-15)

**Decision:** `recommend_model` returns `{"recommendation", "reason", "ranked"}`. The reason explains only the first model. `ranked` is the top 3 and includes that first model.

**Why:** the user's question has one answer, so the explanation belongs to it. A reason on every model would repeat the pool size and requirements, and the prices are already in the records. The reason does not mention runners-up, because `ranked` shows them.

**Empty case:** if nothing passes the filters, `recommendation` is `None`, `ranked` is `[]`, and the reason says no model meets the requirements.

## No fixed gold set of expected models (2026-10-15)

**Decision:** we do not pin expected model IDs in tests or evals.

**Why:** prices and available models keep changing, so a fixed "right model" goes stale after the next catalog refresh. For the ranking code, check by hand-written requirement dicts and inspect the reasons. For the eval set, expect fields in the requirement dict (for example "this task needs vision") instead of model names.

## No hand-made quality tiers in V1 (2026-09-30)

**Decision:** V1 ranks on catalog facts only (filters, `reasoning` flag, price).

**Why:** tiers would be subjective, and many models do near-equal work.

**Deferred:** an objective quality signal from a public benchmark leaderboard, weighted alongside price.

## Query rewriting is deferred; reword the Jev questions for now (2026-10-28)

**Decision:** V1 fixes misjudged answers by rewording the individual Jev questions. Rewriting the task text before it reaches Jev is deferred.

**Why:** in the first test run, scale confused the judgments. "Classify 2 million tickets" got a huge `context_size` and a raised `reasoning_difficulty`, because Jev judged the whole job and not one request. Rewording (for example "in a single request") is the smallest fix. It is a patch per question, though.

**Deferred:** a query-rewriting step that turns the raw task into a normalized description before judging (for example, restating a batch job as one item plus a volume note). It is the more general fix, because the same ambiguity can recur in any question.

## `judge_task` returns the answers and the metadata (2026-11-02)

**Decision:** `judge_task` returns `(answers, meta)`. `answers` is the plain dict of judgments, and `meta` holds the model version and token usage.

**Why:** the translate step should receive only the judgments, not Jev's response envelope, so a change in the SDK's metadata can't break it and tests can pass a hand-made dict. The metadata is still needed for logging and cost tracking, so it travels separately and is not thrown away.

## Judge metadata stays internal (2026-11-02)

**Decision:** the judge's metadata (model version, token usage) is written to the call log and is never returned to clients. In the log it is named `judge_meta`, not `jev_meta`.

**Why:** clients asked which model to use for a task. They have no use for which model judged it. Returning it would tie the public contract to an implementation detail, and the judge may change (a different model, several models, or plain rules). The generic log name means a log reader doesn't change either.

## `requirement` stays in the pipeline result but not in the API response (2026-11-02)

**Decision:** `recommend_for_task` returns `requirement` next to `recommendation`, `reason` and `ranked`. The FastAPI response model will leave `requirement` out.

**Why:** the pipeline result is useful for scripts, tests and logs. The API is a public contract. By Hyrum's Law, any field clients can observe gets depended on, and the field names (`needs_reasoning`, `min_context`, `tool_call`) mirror our internal catalog and judging logic. Adding a field later is a safe change and removing one breaks clients, so the API starts minimal and the `reason` text carries the explanation.

**Revisit:** if clients need to see why the pool was narrowed, expose a trimmed summary of the requirement as an additive change.

## Input gate: one yes/no question, threshold 0.7 (2026-11-09)

**Decision:** Jev also answers `is_valid_task` (Noul). Below 0.7, the pipeline skips translate and rank and returns a fixed message with no recommendation. The call is still logged. A missing answer counts as invalid.

**Why:** greetings and chit-chat have no task to match, and ranking them would return a model that looks like a real answer.

**Evidence:** about 15 test inputs. Real tasks scored 0.86 or more, non-tasks 0.51 or less. Run-to-run noise is about 0.03.

**Wording:** one claim only, with strict criteria. The instructions for this and the other Jev questions are a first version and will likely need changes. Let the eval set drive them, not single cases.

**Note:** not a security control. An injection-style input still scored 0.88.

## Call log: stdlib logging, own logger (2026-11-09)

**Decision:** one JSON line per call goes to `logs/judgments.jsonl` through a dedicated logger, `recommender.calls` (see `call_log.py`). It is kept apart from the normal `getLogger(__name__)` loggers.

**Why:** call records are data, not diagnostics, so they need their own file and format. A logging failure must never break a recommendation.

**Note:** the record keys are a contract. Renaming one (we once wrote `judgements` for `judgments`) splits the log into two formats.

**Deferred:** central `dictConfig`, log rotation.

## Result shape is built only in `schemas.py` (2026-11-09)

**Decision:** `create_ranking_output` in `recommender/schemas.py` is the only place the keys `recommendation`, `reason` and `ranked` are written. `rank.py` and `pipeline.py` both call it.

**Why:** the shape was about to be written in three places. Now a rename is a one-line edit. Its parameters are keyword-only, so arguments can't be swapped by mistake.

**Rejected:** `utils.py`, because catch-all modules collect unrelated code.