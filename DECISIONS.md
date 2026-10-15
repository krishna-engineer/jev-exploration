# Decisions

Why we chose what we chose, and what we deferred. `ROADMAP.md` holds the plan; this file holds the reasoning.

## Price ranking uses `price_in + price_out` (2026-10-07)

**Decision:** V1 ranks models by the plain sum of input and output price per 1M tokens. The weights live as constants (`PRICE_IN_WEIGHT`, `PRICE_OUT_WEIGHT`, both 1) at the top of `model_related/filter_n_rank.py`, so changing them is a one-line edit.

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