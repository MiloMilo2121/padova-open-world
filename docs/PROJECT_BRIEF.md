# Project brief

## Goal

Build a native macOS open-world game set in Padova, starting from a blank project. The first deliverable is one small, navigable district with a complete build–run–test loop. Expand only after measuring performance and playability on the target Mac.

The primary development and performance target is a fanless MacBook Air M4 with 16 GB RAM. Other Apple Silicon MacBooks should get an appropriate quality setting. A proposed first benchmark is 1080p at 60 fps on the M4 Air, with a lower-quality option; this is a goal, **not** a measured result. Measure sustained play for at least 20 minutes, including memory use, frame times, thermals, and loading stutter. Neither the original empty scene nor the new cartographic survey scene establishes performance for finished gameplay.

## Why this stack

Unity 6.3 LTS with the Universal Render Pipeline provides a native Mac Player and adjustable rendering quality. Its local CLI and Pipeline package expose the Editor and development Player to agents for scene construction, C# evaluation, compilation, tests, builds, runtime input, screenshots, and performance counters. The CLI and Pipeline package are still experimental, so agents must verify command results and avoid relying on undocumented behavior.

Blender is the local asset authoring tool. Its MCP is installed for Codex and Claude Code, but Blender must be running for live asset operations. Keep source `.blend` files and exported Unity assets under version control when they become part of the game.

## Constraints and decisions

- Keep development, builds, and testing local. The Unity project has `cloudEnabled: 0` and no Cloud project ID. Do not link the web-created Unity Cloud project or add paid hosted services without a new request.
- Use Git for source control. `Library/`, logs, and builds are generated locally and ignored.
- Build a small playable district before a whole city. Use streaming, level of detail, bounded texture and mesh budgets, limited active traffic, and graphics quality presets as the world grows.
- Prefer original, public-domain, or appropriately licensed assets. Record attribution and usage rights for any third-party city data or art before shipping.
- Do not treat the old Three.js code or the older `.context/photoreal-padova-plan.md` as current architecture. That document predates the Unity reset and remains only as research history.

## Next product milestone

Start in the real historic core around Palazzo della Ragione and the Erbe, Frutta and Signori piazzas. The user's explicit requirement is real street layout and real buildings: no guessed or merely plausible shapes or façades. Use public sources for now. Missing geographic or architectural evidence stays unresolved. See [REAL_WORLD_DATA.md](REAL_WORLD_DATA.md) for the municipal survey import, its age and the remaining façade/roof work.

Specify and implement one playable Padova block: player movement, a repeatable route, basic environment and collision, streaming boundary, and a measurable objective. Add a deterministic agent test that sends input, checks player position and objective state, captures the rendered result, and compares frame-time and memory metrics against an established baseline. The survey scene now has input/state checks for exploration and record selection; walking, objectives and district streaming still need their own gameplay scenarios.
