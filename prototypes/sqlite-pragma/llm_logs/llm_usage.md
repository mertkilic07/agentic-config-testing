# LLM usage log

- LLM: Claude (Anthropic), used through a chat session on 10 November 2026.
- System choice: SQLite was selected as the first subject system because it is open source, needs no
  installation, and offers both compile-time and runtime options. This first round focuses on its
  runtime options (PRAGMAs).
- Input given to the LLM: the SQLite PRAGMA documentation and the task "Build a configuration space
  model of SQLite's runtime options (options, values, and constraints), and write scripts that apply
  each configuration to SQLite, run a small workload, and check the results against the model."

| Artifact | Produced by | Manual changes |
|---|---|---|
| model/model.json | LLM | none yet – validation by the team pending |
| scripts/generate_configs.py | LLM | none |
| scripts/run_one.py | LLM | none |
| scripts/run_all.py | LLM | none |

- All three scripts ran correctly on the first attempt (no fixes needed).
- Observations to discuss: the LLM chose a test oracle for each constraint (C2–C5) and marked the
  rollback check as invalid under journal_mode=OFF instead of reporting it as a failure.
