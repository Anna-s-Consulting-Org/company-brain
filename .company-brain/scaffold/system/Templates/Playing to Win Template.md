<%*
const f = tp.file.folder(true);
const layer = f.startsWith("Company") ? "company" : f.startsWith("Teams") ? "team" : "personal";
const team = f.startsWith("Teams/") ? f.split("/")[1] : "";
const horizon = await tp.system.prompt("horizon, for example YYYY-YYYY");
-%>
---
date: <% tp.date.now("YYYY-MM-DD") %>
type: strategy
tags: [strategy]
ai-first: true
layer: <% layer %>
team: <% team ? '"[[' + team + ']]"' : "" %>
framework: playing-to-win
horizon: <% horizon %>
status: draft
owner: "[[TBD]]"
---

# <% tp.file.title %>

## For future agent
This note is a strategy choice cascade in the Playing to Win form (Lafley and Martin) for <% horizon %> at the <% layer %> layer: winning aspiration, where to play, how to win, capabilities, management systems.

## 1. Winning aspiration
What does winning look like, for whom? Connects to [[Vision]].
- TBD

## 2. Where to play
Segments, geographies, channels, offers, and value-chain stages we choose, and the ones we choose not to play in.
| Dimension | We play | We do not play |
|---|---|---|
| Customer segments | TBD | TBD |
| Geography | TBD | TBD |
| Offers | TBD | TBD |
| Channels | TBD | TBD |

## 3. How to win
Cost leadership or differentiation, and the specific advantage in each chosen place. Link the value proposition canvas per segment.
- TBD

## 4. Capabilities that must be in place
- TBD

## 5. Management systems
How we will measure and run it: OKRs ([[Company OKRs]]), cadence ([[Company Planning]]), the roadmap ([[Company Roadmap]]).
- TBD

## Coherence check
Each choice should reinforce the ones above and below it. Contradictions found: TBD

Method: [[Playing to Win]].
