# Company Brain note schemas

Frontmatter, naming, and folder for every Company Brain note type. Extends `references/ai-first-rules.md` (which still governs: preamble, universal fields, recency markers, wikilinks, confidence, anti-fabrication). Where a type exists in both files, the fields here are added on top of the AI-first schema.

The `brain` CLI parses these fields (`brain refresh`, `brain check`), so spelling matters: lowercase keys, values from the enumerations below, links as quoted `"[[wikilinks]]"`.

## Universal fields (every note)

```yaml
date: YYYY-MM-DD          # creation date, YYYY-MM-DD
updated: YYYY-MM-DD       # last meaningful edit (optional)
type: <type>              # from the tables below
tags: [<type>, ...]       # always include the type
ai-first: true
layer: company            # company | team | personal  (must match the folder)
team: "[[Platform]]"      # required when layer is team
owner: "[[Jane Doe]]"     # accountable person, where meaningful
last-checked: YYYY-MM-DD  # optional: the owner confirmed the facts; set only by /company-brain:checkin
checkin: never            # optional: never | priority. Keeps a note out of check-ins, or asks about it first
```

`last-checked` moves only when the owner looks at the facts. `updated` is the last meaningful edit, so a link-only or formatting change must not touch it.

Exempt from the universal fields: kanban boards (`kanban-plugin: board` frontmatter only), `Home.md`, `CLAUDE.md`, `README.md`, `index.md`, `log.md`, everything in `Templates/`, `Sources/`, `Exports/`, `.company-brain/`.

## Periods and names

- Year: `YYYY`. Quarter: `YYYY-Qn` (fiscal quarters follow `company.fiscal_year_start` in `brain.yaml`; month 1 means calendar quarters). ISO week: `YYYY-Www`.
- `brain period` prints the current year, quarter, week, and the file names a daily, weekly, or team update should use today. Use it instead of computing dates by hand.

## Folder and filename by type

`<L>` is the layer root: `Company`, `Teams/<Team>`, or `Personal`.

| Type | Folder | Filename pattern |
|---|---|---|
| `me` | `Personal/` | `Me.md` |
| `person` | `Company/Org/People/` | `<Full Name>.md` |
| `team` | `Teams/<Team>/` | `<Team>.md` |
| `mission` / `vision` / `values` | `Company/` | `Mission.md`, `Vision.md`, `Values.md` |
| `strategy` | `<L>/Strategy/` | `Strategy - <horizon or name>.md` |
| `vpc` | `<L>/Strategy/` | `VPC - <Segment>.md` |
| `bmc` | `<L>/Strategy/` | `BMC - <Business or product>.md` |
| `objective` (annual) | `<L>/OKRs/` | `<YYYY> - <Owner> - O<n> - <Title>.md` |
| `objective` (quarterly) | `<L>/OKRs/` | `<YYYY-Qn> - <Owner> - O<n> - <Title>.md` |
| `objective` (personal goal) | `Personal/Goals/` | `<YYYY-Qn> - <First name> - G<n> - <Title>.md` |
| `plan` | `<L>/Planning/` | `Annual Plan <YYYY>.md`, `Quarterly Plan <YYYY-Qn>.md` (team: prefix `<Team> - `) |
| `outcome` | `<L>/Discovery/` | `OUT - <Title>.md` |
| `opportunity` | `<L>/Discovery/` | `OPP - <Title>.md` |
| `solution` | `<L>/Discovery/` | `SOL - <Title>.md` |
| `experiment` | `<L>/Discovery/` | `EXP - <Title>.md` |
| `project` | `<L>/Projects/` | `<Project name>.md` |
| `meeting` | `<L>/Meetings/` | `<YYYY-MM-DD> - <Meeting title>.md` |
| `one-on-one` | `Personal/1-1s/` | `1-1 - <Person>.md` (one running note per person) |
| `decision` | `<L>/Decisions/` | `DEC-<YYYY-MM-DD> - <Title>.md` |
| `daily` | `Personal/Daily/` | `<YYYY-MM-DD>.md` |
| `weekly` | `Personal/Weekly/` | `<YYYY>-W<WW>.md` |
| `team-update` | `Teams/<Team>/Weekly/` | `<YYYY>-W<WW> - <Team> - <Person>.md` |
| `team-weekly` | `Teams/<Team>/Weekly/` | `<YYYY>-W<WW> - <Team> - Team Weekly.md` |
| `knowledge` | `<L>/Knowledge/` (personal: `Personal/Notes/`) | `<Title>.md` |
| `hub` | any | `<Scope> <Area>.md`: `Company OKRs.md`, `Platform OKRs.md`, `Company Discovery.md` (scope is Company or the team name) |
| board | `<L>/` | `<Team> Board.md`, `My Board.md`, `Company/Roadmap/Company Roadmap.md`, `Teams/<Team>/<Team> Roadmap.md` |

Filenames are globally unique on purpose: Obsidian resolves `[[links]]` by filename, so two notes called `Weekly.md` in different layers would be ambiguous. The owner or team in the name is what keeps them apart.

## Type schemas

### `me`
```yaml
type: me
person: "[[Jane Doe]]"
teams: ["[[Platform]]"]
role: "TBD"
manager: "[[TBD]]"
timezone: UTC
email: "TBD"              # optional; work address only
```

### `person` (shared profile, company layer)
```yaml
type: person
role: "Product Manager"
team: "[[Platform]]"
manager: "[[Sam Lee]]"     # drives the org chart
location: "TBD"
start_date: TBD
timeline:                  # bi-temporal, append-only (see ai-first-rules.md)
  - fact: "Product Manager, Platform"
    from: YYYY-MM-DD
    until: present
    learned: YYYY-MM-DD
```
A shared profile holds only facts the person would be comfortable seeing on the company intranet. Impressions, feedback, and 1:1 content belong in `Personal/1-1s/`.

### `team`
```yaml
type: team
lead: "[[Sam Lee]]"
parent: "[[Engineering]]"  # optional: department or parent team
mission: "One sentence"
slack: "#team-platform"     # optional
rituals: ["weekly sync Tue", "retro biweekly"]
```

### `mission`, `vision`, `values`
```yaml
type: mission              # or vision, values
status: draft              # draft | approved
approved_by: "[[TBD]]"
review_by: YYYY-MM-DD
```

### `strategy`
```yaml
type: strategy
framework: kernel          # kernel | playing-to-win | both
horizon: "YYYY-YYYY"
status: draft              # draft | approved | superseded
supersedes: "[[...]]"      # optional
```

### `vpc` (Value Proposition Canvas)
```yaml
type: vpc
segment: "Mid-market PS teams"
status: hypothesis         # hypothesis | partially-validated | validated | retired
fit: problem-solution      # none | problem-solution | product-market | business-model
evidence: ["[[YYYY-MM-DD - Customer interview Acme]]"]
strategy: "[[Strategy - YYYY-YYYY]]"
```
Body sections (fixed names, parsed by `brain check`): `## Customer jobs`, `## Pains`, `## Gains`, `## Products and services`, `## Pain relievers`, `## Gain creators`, `## Fit`, `## Assumptions to test`.

### `bmc` (Business Model Canvas)
```yaml
type: bmc
status: draft
```
Body sections: the nine blocks (`## Customer segments`, `## Value propositions`, `## Channels`, `## Customer relationships`, `## Revenue streams`, `## Key resources`, `## Key activities`, `## Key partnerships`, `## Cost structure`).

### `objective` (OKR objective, holding its key results)
```yaml
type: objective
level: company             # company | team | personal
period: YYYY-Qn            # YYYY for annual objectives
owner: "[[Jane Doe]]"
parent: "[[YYYY - Company - O1 - Become the default AI workspace#^kr2]]"   # what this ladders up to
status: on-track           # on-track | at-risk | off-track | done | dropped
last_checkin: YYYY-MM-DD
```
Key results are list items in the `## Key results` section, each with inline Dataview fields and a block id so other notes can link to one KR:

```markdown
- **KR1** Weekly active teams from 1200 to 2000 [baseline:: 1200] [target:: 2000] [current:: 1450] [unit:: teams] [confidence:: medium] [owner:: [[Jane Doe]]] ^kr1
- **KR2** Ship the self-serve onboarding flow [progress:: 0.4] [confidence:: high] [owner:: [[Sam Lee]]] ^kr2
```
- Progress is `progress::` when given (0.0 to 1.0), else computed from `baseline`, `target`, `current`, clamped to 0..1. Objective score is the mean of its KR progress.
- Link to a KR as `[[<objective note>#^kr1]]`. `parent:` may point at an objective or at one KR; prefer the KR.
- Check-ins append a row to `## Check-ins`: `| YYYY-MM-DD | KR1 | 1450 | medium | note |`.
- Scoring convention: 0.7 is a good outcome for an ambitious KR; 1.0 every time means the target was not ambitious.

### `plan`
```yaml
type: plan
horizon: quarterly         # annual | quarterly
period: YYYY-Qn
status: draft              # draft | committed | closed
```

### Discovery: `outcome`, `opportunity`, `solution`, `experiment`
```yaml
# outcome: the measurable result the team is driving (usually one KR)
type: outcome
kr: "[[YYYY-Qn - Platform - O1 - Faster onboarding#^kr1]]"
metric: "Time to first board, median minutes"
status: active             # active | achieved | dropped

# opportunity: a customer need, pain, or desire (from research, never invented)
type: opportunity
parent: "[[OUT - Faster time to value]]"     # an outcome or a parent opportunity
segment: "[[VPC - Mid-market PS teams]]"
evidence: ["[[YYYY-MM-DD - Customer interview Acme]]"]
opportunity_size: 4        # 1-5: how many customers, how often, how painful
status: open               # open | targeted | parked | solved

# solution: one way to address an opportunity
type: solution
parent: "[[OPP - Setup takes too long]]"
impact: 4                  # 1-5, expected effect on the outcome
effort: 2                  # 1-5, relative cost to deliver
confidence: medium         # high | medium | low
reach: 800                 # optional, for RICE: people or events per quarter
status: idea               # idea | exploring | validated | planned | building | shipped | dropped
roadmap: next              # now | next | later | none
project: "[[Onboarding revamp]]"             # optional, once it becomes a project

# experiment: an assumption test for a solution
type: experiment
parent: "[[SOL - Guided setup checklist]]"
assumption: "Admins will complete a 5-step checklist in one sitting"
assumption_type: usability # desirability | viability | feasibility | usability | ethical
method: "Prototype test with 5 admins"
success_criteria: "4 of 5 finish under 10 minutes"
result: pending            # pending | passed | failed | inconclusive
```

### `project`
```yaml
type: project
status: active             # planning | active | on-hold | completed | archived
okrs: ["[[YYYY-Qn - Platform - O1 - Faster onboarding#^kr1]]"]
solution: "[[SOL - Guided setup checklist]]"   # optional
impact: 4                  # optional, for prioritization
effort: 3
roadmap: now               # now | next | later | none
start: YYYY-MM-DD
due: YYYY-MM-DD
```

### `meeting`
```yaml
type: meeting
meeting_type: team         # all-hands | leadership | team | one-on-one | external | workshop
attendees: ["[[Jane Doe]]", "[[Sam Lee]]"]
source: calendar           # calendar | granola | zoom | gemini | manual
project: "[[...]]"         # optional
```
Body: `## Agenda`, `## Notes`, `## Decisions`, `## Action items` (`- [ ] [[Owner]] action @{YYYY-MM-DD}`).

### `one-on-one` (personal only)
```yaml
type: one-on-one
person: "[[Sam Lee]]"
cadence: weekly
```
One running note per person, newest session on top under `## <YYYY-MM-DD>` headings. Candid content goes under `## Private`.

### `decision`
```yaml
type: decision
status: accepted           # proposed | accepted | superseded | rejected
decided_by: ["[[Jane Doe]]"]
context: "[[...]]"         # the meeting, project, or OKR it came from
supersedes: "[[...]]"      # optional
```

### `daily`, `weekly`, `team-update`, `team-weekly`
```yaml
type: daily                # Personal/Daily
week: YYYY-Www

type: weekly               # Personal/Weekly
week: YYYY-Www
period: YYYY-Qn
krs: ["[[...#^kr1]]"]      # KRs this week's work moved

type: team-update          # Teams/<Team>/Weekly, one per person per week
week: YYYY-Www
author: "[[Jane Doe]]"
krs: ["[[...#^kr1]]"]

type: team-weekly          # Teams/<Team>/Weekly, one per team per week
week: YYYY-Www
contributors: ["[[Jane Doe]]", "[[Sam Lee]]"]
```

### `knowledge` (ingested source summary or reference note)
```yaml
type: knowledge
source_path: "Sources/GTM Strategy/YYYY plan.pdf"   # or source_url
source_type: pdf           # pdf | doc | gdoc | sheet | slides | web | transcript | md
ingested: YYYY-MM-DD
confidence: stated
```

### `source` (a captured file from folder ingestion)
A knowledge note that stands for one source file, written by `/company-brain:ingest` in a folder batch. The helper `scripts/ingest_batch.py` recognises it by `type: source`, found under the layer's Knowledge folder.
```yaml
type: source
source_path: "/absolute/path/from/the/plan"   # the source's identity for completion receipts; machine-specific, so keep in Personal
source_file_hash: "<64 hex>"                   # SHA-256 of the file's bytes, from the plan
source_type: md            # md | pdf | audio | image
ingested: YYYY-MM-DD
confidence: stated
```
Everything else follows `knowledge`. A completion receipt (a hidden comment in `log.md`) says the work for that source version is done; it does not judge extraction quality.

### `crew-log`, `crew-lessons` (written by `scripts/crew.py`)
```yaml
type: crew-log             # one note per day in Personal/Crew/: one line per job (time | agent | area | what | where)
type: crew-lessons         # lessons agents leave each other; open until a human runs keep or drop
```

### `hub`, `framework`, `system`, generated views
```yaml
type: hub                  # area index notes (Company.md, Company OKRs.md, Platform Discovery.md ...)
type: framework            # System/Frameworks theory notes
type: system               # System docs
type: okr-tree             # generated by brain refresh
type: prioritization       # generated
type: org-chart            # generated
```

## Auto blocks

Generated content lives between markers that `brain refresh` rewrites; everything outside them is preserved:

```markdown
<!-- brain:auto:start okr-tree -->
...generated...
<!-- brain:auto:end okr-tree -->
```
Never hand-edit inside the markers; edit the source notes and run `brain refresh`.
