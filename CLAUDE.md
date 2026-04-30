# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a two-phase project:
- **Phase 1 (complete):** AI-powered crime mystery story generator using Google Gemini
- **Phase 2 (in progress):** Interactive text game engine built on top of Phase 1 stories, using the **Game Engine Rule Generation** template. There will frontend comprised of Next.js.

The player assumes the role of detective (or companion) and can type free-form actions. A Drama Manager agent intervenes when needed to keep the story coherent without breaking player agency.

## Setup

```bash
pip install -r requirements.txt
```

Create a `.env` file in the project root:
```
GEMINI_API_KEY=<your-api-key>
GEMINI_MODEL_NAME=gemini-2.5-flash   # optional, this is the default
```

## Running

```bash
python main.py
```

State persists to `state/current_state.json` after each phase (supports resuming interrupted runs). Final story output goes to `output/final_story.txt`.

## Environment Variables (`src/config.py`)

| Variable | Default | Purpose |
|---|---|---|
| `GEMINI_API_KEY` | required | Google Gemini API key |
| `GEMINI_MODEL_NAME` | `gemini-2.5-flash` | Model selection |
| `MAX_LOOP_PROCESSES` | `15` | Max narrative loop iterations before forcing resolution |
| `MAX_RED_HERRINGS` | `3` | Max misleading clues per story |

## Architecture

![Phase 1 and 2 Architecture Diagram](architecture_pictures/Phase%201%20and%202.png)
![Phase 3 Architecture Diagram](architecture_pictures/Phase%203.png)
![Phase 4 Architecture Diagram](architecture_pictures/Phase%204.png)

The system runs as a **4-phase pipeline**. Phases 1–3 are pre-computation (story + world generation). Phase 4 is the interactive runtime.

### Phase 1 & 2 — Story Generation

Orchestrated by `MetaController` in `src/meta_controller.py`. Phases are loaded dynamically via `importlib`.

**Data Flow:**
```
data/initialization_prompts.json  (pre-authored setting, protagonist, characters)
    ↓
Phase 1 (01_initialize.py)  →  hidden crime truth + protagonist goal  →  current_state.json
    ↓
Phase 2 (02_loop.py)        →  iterative story beats (up to MAX_LOOP_PROCESSES)  →  current_state.json
```

Each Phase 2 loop iteration: generates 3 action options → selects the most suspenseful → tracks subplots, clues, elements, and `dare_fate`. Tension escalates as `loop_step` approaches `MAX_LOOP_PROCESSES`. The hidden crime truth is generated in Phase 1 but is never revealed to the protagonist during the loop.

### Phase 3 — Detail Addition & World Building

Takes the raw story outline and produces everything the game engine needs to run.

```
PROTAGONIST + GOAL + HIDDEN TRUTHS + STORY ELEMENTS
    ↓
Fixer          →  fixed outline + resolved plot holes  →  current_state.json
    ↓
Plot Point Annotator  →  annotated fixed outline
    ↓
Dependency Analyzer   →  causal dependencies between plot points
    ↓
World Graph Builder   →  navigable location graph (rooms + connections)
    ↓
Object & NPC Placer   →  objects and characters assigned to locations
```

The **Dependency Analyzer** tracks which plot points must precede others — this feeds the Drama Manager's intervention logic at runtime.
The **World Graph Builder** generates the minimal set of locations needed to support all story events, with commonsense-valid adjacency. 
The **Object & NPC Placer** assigns objects and npc within the story 

### Phase 4 — Runtime (Interactive Text Game)

The runtime loop consumes `current_state.json` (which now includes world state) and runs the interactive session.

```
PLAYER input
    ↓
Action Classifier  →  OR →  Rule Generator (new/unknown action)
                       →  Precondition Checker (known action)
                            ↓
                         Validator
                            ↓
                         Action Executor  →  Drama Manager
                                                ↓
                                          (one of 4 interventions)
                                                ↓
                                          back to PLAYER
```

**Drama Manager interventions (triggered after Action Executor proposes an outcome):**
1. **Block Player** — prevents the action (communicated via an in-world companion, not a raw system message)
2. **Plan Repair** — patches the current plot to accommodate an unexpected player path
3. **Generate New Content** — creates new objects, locations, or NPCs with cascading preconditions (recursive depth-limited)
4. **Retrofit Rules** — retroactively updates existing action rules to be consistent with new world elements

The Drama Manager approves actions that are constituent or consistent with the story. It only intervenes when:
- A protected state variable (required for the mystery to be solvable) would be violated
- Commonsense bounds are exceeded (no alien invasions, time travel, resurrections, etc.)
- The action would make the crime permanently unsolvable

**Player sheet:** Location, inventory, skills — passed as context on every Gemini call to prevent hallucinated inconsistencies.

**World map registry:** Acts as a dictionary for all locations, objects, and NPCs. Updated by the Drama Manager; blocks only when a proposed change would cause a contradiction.

### Key Modules

- **`src/state_manager.py`** — `StoryState` wraps `current_state.json`. Every `update()` persists state. All phases and the runtime read/write through this object.
- **`src/llm_client.py`** — Gemini wrapper: `generate_text()` (prose, temperature 0.8) and `generate_json()` (structured output with schema validation, temperature 0.7).
- **`src/prompts.py`** — All LLM prompts and JSON response schemas.
- **`data/initialization_prompts.json`** — Pre-authored story seed (setting, character roster, protagonist). Swap this file to change the story universe.

### Development Note

Story generation produces different output each run. During development, generate a story once, save `current_state.json`, and load that saved state rather than re-running the generator on every iteration. This ensures reproducible debugging of the game engine and Drama Manager logic.
