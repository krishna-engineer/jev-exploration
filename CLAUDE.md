# jev-exps

## Working rules
- When reporting next set of actions (commands you'll run, or files you plan to create or change, packages to be added, etc), list them as separate bullet points, one action per bullet. Never bundle several actions into one prose sentence. This is so that actual user doesn't miss your plan of action.

## Layout
- `model_related/` holds the model catalog code. `fetch.py` pulls models.dev `api.json`, flattens first-party models, and writes `model_catalog.json`.
- `model_catalog.json` (repo root) is generated output, committed to git. Regenerate it by running `fetch.py`, not by hand.
- `ROADMAP.md` is a reference for the plan, not the sole truth. Plans change in conversation, so don't treat it as fixed; question it when something looks off and keep it updated. It is listed in `.gitignore`, so it is not in git.