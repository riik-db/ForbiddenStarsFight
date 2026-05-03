# Simulator

Python implementation of the Forbidden Stars battle simulator + analysis/push tooling.

## Quick Orientation

- `sim_run.py` generates battle simulations and writes `.pkl` batches to disk.
- `analyse_run_test.py` reads those `.pkl` batches, aggregates results, and pushes them to Postgres.
- `run_all.py` is a simple orchestrator that runs all matchups across stages by calling the two modules above.

## Entry Points (`__main__`)

- `sim_run.py`
  - Has `if __name__ == "__main__":` and runs a small sample simulation batch.
  - Behavior: calls `run_simulations(...)` with hardcoded parameters (writes to `output_dir='test'`).
  - Note: `run_simulations(...)` deletes `output_dir` if it already exists. For clean up.
- `analyse_run_test.py`
  - Has `if __name__ == "__main__":` and runs `worker_test_v2('sim_results','public')`.
  - Expects a folder like `sim_results/` containing `.pkl` batches produced by `sim_run.py`.
  - If data push breaks via parent code, then can easily retry via it.

## Modules

- `game_set_up.py`
  - Static game definitions (units, counts, dice, morale, etc.) used by the simulator.
- `utils.py`
  - Shared helper functions used by the simulator (e.g., unit selection / randomization utilities).
- `card_abilities.py`
  - Card effect implementations and helper routines that mutate battle state (routing, un-routing, temp tokens, etc.).
- `sim_run.py`
  - Core simulation engine:
  - Builds initial battle state from `game_set_up.py` + helpers in `utils.py`.
  - Applies card effects from `card_abilities.py`.
  - Runs batches in parallel via `ProcessPoolExecutor`.
  - Persists results as pickled dictionaries to `output_dir`.
- `analyse_run_test.py`
  - Post-processing + DB push:
  - Loads `.pkl` batches, aggregates fight/round/card stats into tables.
  - Connects to Postgres using `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` environment variables (defaults to localhost/postgres).
  - Deletes old rows for the same `(att_faction, def_faction, stage)` before inserting new aggregates.
- `run_all.py`
  - Orchestrates full runs across stages and matchup combinations.

## Notes / Footguns

- `sim_run.run_simulations(...)` removes the output directory if it exists (uses `shutil.rmtree(output_dir)`).
- `run_all.py` executes immediately on import; treat it as a script, not a library module.

