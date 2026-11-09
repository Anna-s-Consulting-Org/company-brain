---
description: "Add a task to the right board with priority, due date and links"
argument-hint: "<task>"
---

Run the Company Brain `board` skill in add-a-task mode. Arguments, if any: $ARGUMENTS

This is the board skill's **Add** step for one task: parse the task from `$ARGUMENTS` (or the latest task in the conversation), infer priority, due date, and the project, KR, or person it links to, and add one card to `Personal/My Board.md` (Inbox, or This week when due within 7 days). A team commitment goes on the team board only after asking. Link the card from today's daily note under `## Notes and captures`.

1. Read `.company-brain/skills/board/SKILL.md` in this brain and follow it step by step. If this brain has no `.company-brain/` folder, read `<engine>/skills/board/SKILL.md`, with `<engine>` from the **Company Brain** line of the session context.
2. The brain is this folder (the one holding `brain.yaml`) and `brain` in the skill means `./brain`. Where the skill says `${CLAUDE_SKILL_DIR}`, use the folder that holds that `SKILL.md`.
3. Read `CLAUDE.md` first if it is not loaded yet. Its rules on layers, AI-first notes and propagation apply to every write.

With the plugin installed, the same skill also runs as `/company-brain:board`.
