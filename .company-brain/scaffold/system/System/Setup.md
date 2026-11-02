---
date: {{TODAY}}
type: system
tags: [system]
ai-first: true
layer: company
---

# Setup

## For future agent
This note is the installation and onboarding guide for Company Brain: opening the vault in Obsidian, installing the plugin in Claude Code, configuring the vault path, optional Claude Desktop and claude.ai Project access, sharing through git, and onboarding a teammate.

## 1. Obsidian
1. Open Obsidian, Open folder as vault, choose this folder.
2. Settings, Community plugins, turn off Restricted mode, then install and enable **Dataview**, **Kanban**, **Templater**, and **Calendar** (if they are not already in `.obsidian/plugins/`).
3. Templater: templates folder is `Templates` (preconfigured). Daily notes core plugin: folder `Personal/Daily`, template `Templates/Daily Note Template` (preconfigured).
4. Graph view is colour-coded by layer: company blue, teams green, personal orange, system grey.

## 2. Claude Code plugin
From any terminal (or `!` in Claude Code):
```
claude plugin marketplace add "<path to this folder>"
claude plugin install company-brain@company-brain
```
Restart Claude Code. Then `/company-brain:setup`. Inside this folder the plugin finds the brain automatically; to use it from other folders or Cowork, set the plugin option **Company Brain folder** (`vault_path`) to this folder via `/plugin`.

The engine needs `python3` (stock macOS is fine) and, for the MCP server, `uv`.

## 3. Optional: Claude Desktop chat
Add to Claude Desktop's MCP configuration (Settings, Developer, Edit config), with your paths:
```json
{
  "mcpServers": {
    "company-brain": {
      "command": "uv",
      "args": ["run", "--no-project", "--with", "mcp<2", "python", "<brain>/.company-brain/mcp/vault/server.py"],
      "env": { "COMPANY_BRAIN_PATH": "<brain>" }
    }
  }
}
```

## 4. Optional: Claude Project for claude.ai users
Run `/company-brain:export`, create a Project on claude.ai, paste `Exports/Claude Project/PROJECT_INSTRUCTIONS.md` into its instructions, and upload the other files. Read-only; re-export after planning.

## 5. Sharing through git
1. Create a **private** repository in your company's organization.
2. `git remote add origin <url>`; check that `.gitignore` lists `Personal/` before the first commit; commit and push.
3. Protect the main branch so company-layer changes go through pull requests.
4. Once pushed, add the marketplace to `.claude/settings.json` so teammates are offered the plugin when they trust the folder:
```json
{
  "extraKnownMarketplaces": {
    "company-brain": { "source": { "source": "github", "repo": "<org>/<repo>", "path": ".claude-plugin/marketplace.json" } }
  },
  "enabledPlugins": { "company-brain@company-brain": true }
}
```

## 6. Onboarding a teammate
1. Get a copy of the repository and open it in Obsidian (step 1).
2. Install the plugin (step 2), then run `/company-brain:setup`: it creates their own `Personal/` layer and shared profile.
3. `./brain connect --sync` to mount shared sources on their machine.
4. First week: `/company-brain:daily` each morning, `/company-brain:weekly` on Friday.
