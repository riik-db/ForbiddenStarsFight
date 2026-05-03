# ForbiddenStarsFight

Battle simulator + analysis pipeline for the board game *Forbidden Stars*.

The repo contains:
- A Python simulator (`new_ver/`) that generates millions of battles.
- A Postgres database (via Docker) to store aggregated results.
- A Metabase instance (via Docker) to explore the results in dashboards.
- A longer writeup in `documentation/README.md`.

## 5-minute Quickstart (No Python Setup)

Prereqs:
- Docker Desktop installed and running;
- clone the repo.

From the repo root:

```bash
docker-compose -p forbiddenstars_battle_simulator up -d
```

What you get:
- Metabase: `http://localhost:3000/`
- Postgres: `localhost:5432` (db/user/pass: `mydb` / `postgres` / `postgres`)

Metabase login:
- Username (email): `orks@waagh.com`
- Password: `Eldar123`

## How Things Fit Together

Typical flow:
1. Run simulations -> writes `.pkl` batches to a folder (default: `sim_results/`).
2. Analyse batches -> aggregates results and pushes into Postgres tables.
3. Explore results -> Metabase reads from Postgres.

Code map (start here):
- `new_ver/README.md` explains the main modules + script entry points.
- `documentation/README.md` contains the methodology + results writeup.

## Running Simulations

Fast “does this work?” run (generates local output):

```bash
docker-compose -p forbiddenstars_battle_simulator exec app python sim_run.py
```

Full matrix run (all stages + matchups) + push to Postgres:

```bash
docker-compose -p forbiddenstars_battle_simulator exec app python run_all.py
```

Notes:
- `new_ver/sim_run.py` deletes the output directory if it already exists.
- `new_ver/run_all.py` is a script (no `if __name__ == "__main__":` guard) and will execute immediately.

## Adding A New Faction (Checklist)

Where you change things:
- `new_ver/game_set_up.py`: add units + card definitions/stats for the faction.
- `new_ver/card_abilities.py`: implement the card effects / state mutations.
- `new_ver/sim_run.py`: only touch this if a card requires a new engine hook (try to keep it rare).

Suggested workflow (non-coder friendly):
1. Copy an existing faction as a template in `new_ver/game_set_up.py`.
2. Add the new faction’s cards one-by-one, starting with the simplest effects.
3. For each card effect, implement in `new_ver/card_abilities.py` and do a tiny test run (small `n`) before moving on.
4. When all cards are implemented, run the full matchup(s) and validate in Metabase.

## AI-Assisted Faction Implementation (Recommended)

If you’re not comfortable coding, using an AI assistant can speed things up a lot, but you still need to verify behavior.

Good prompt pattern (copy/paste, then fill in faction details):
- “In `new_ver/game_set_up.py`, add a new faction named `<FACTION>` by mirroring the structure used for `<EXISTING_FACTION>`. Create units (tiers, dice, hp, morale, counts) and combat cards with the same schema as existing factions.”
- “In `new_ver/card_abilities.py`, implement these new card effects for `<FACTION>` using existing helper patterns (rout/unroute/temp tokens/dice). Return a patch, not just code snippets.”
- “List edge cases to test for each card, and point to where in `sim_run.py` the effect is applied (if relevant).”

What to double-check (always):
- No card effect accidentally edits the *other* side’s units when it shouldn’t.
- Routed/killed flags behave consistently across rounds.
- Any “choose X” decisions should be randomized (by design). Assume, that players make mistakes, thus they cannot be perfect.

## Reset / Clean Slate

If something feels off/broken and you want to return to the repo’s predefined baseline (schema + bundled Metabase DB file):

Stop everything and wipe Docker state (drops Postgres volume data):

```bash
docker-compose -p forbiddenstars_battle_simulator down -v
```

Copy repo's original `init.sql.gz` and `metabase_test.db/`

```bash
docker-compose -p forbiddenstars_battle_simulator up -d
```
