---
description: "Load company context (identity, mission, OKRs, strategy) in progressive levels"
argument-hint: "[0-3 or a question]"
---

Run the Company Brain `context` skill. Arguments, if any: $ARGUMENTS

1. Read `.company-brain/skills/context/SKILL.md` in this brain and follow it step by step. If this brain has no `.company-brain/` folder, read `<engine>/skills/context/SKILL.md`, with `<engine>` from the **Company Brain** line of the session context.
2. The brain is this folder (the one holding `brain.yaml`) and `brain` in the skill means `./brain`. Where the skill says `${CLAUDE_SKILL_DIR}`, use the folder that holds that `SKILL.md`.
3. Read `CLAUDE.md` first if it is not loaded yet. Its rules on layers, AI-first notes and propagation apply to every write.

With the plugin installed, the same skill also runs as `/company-brain:context`.
