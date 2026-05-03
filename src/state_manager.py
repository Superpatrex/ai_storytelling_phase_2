import json
import os
from typing import Dict, Any
from src.config import STATE_DIR

# Class that saves and updates the story state to the json file
class StoryState:
    # Initialization for the StoryState
    def __init__(self, state_file: str = "current_state.json"):
        self.state_file: str = state_file
        self.state_path: str = os.path.join(STATE_DIR, state_file)
        self.state: Dict[str, Any] = {
            # ── Phase 1: Initialization ────────────────────────────────────
            "protagonist": {},       # Name, Role, Reason, Connection of the protagonist
            "characters": [],        # Supporting cast from initialization_prompts.json
            "setting": {},           # Location and time from initialization_prompts.json
            "hidden_truth": {},      # Culprit, motive, method, summary, suspects, locations
            "goal": "",              # Protagonist's overarching goal
            "dire_fate": "",         # Consequence of failure

            # ── Phase 2: Narrative Loop ────────────────────────────────────
            "loop_step": 0,
            "actions_taken": [],     # History of {action, outcome} dicts
            "current_action": None,
            "red_herrings_used": 0,
            "story_elements": [],    # Raw {type, description, ...} from loop

            # ── Phase 3a: Fixer ────────────────────────────────────────────
            "plot_points": [],       # Structured [{id, sequence, description, type, ...}]
            "plot_holes_fixed": [],  # List of strings describing fixed issues

            # ── Phase 3b: Plot Point Annotator ─────────────────────────────
            "annotated_plot_points": [],   # [{id, preconditions, effects, is_protected}]
            "protected_variables": [],     # [{description, object_or_npc_id, required_condition, ...}]

            # ── Phase 3c: Dependency Analyzer ──────────────────────────────
            "dependency_graph": [],  # [{plot_point_id, depends_on, causal_spans}]

            # ── Phase 3d: World Graph Builder ──────────────────────────────
            "world_graph": {"rooms": [], "starting_room_id": ""},

            # ── Phase 3e: Object & NPC Placer ──────────────────────────────
            "objects": [],   # [{id, name, description, location_id, can_be_picked_up, ...}]
            "npcs": [],      # [{id, name, current_location_id, can_move, ...}]

            # ── Phase 4: Runtime ───────────────────────────────────────────
            "player_state": {},          # {current_location_id, inventory, knowledge, skills}
            "action_rules": [],          # Generated rules [{id, verb, description, preconditions, ...}]
            "completed_plot_points": [], # IDs of plot points that have been triggered
            "game_complete": False,
        }
        self.load()

    # Method to update the key-value pair within the json file
    def update(self, key: str, value: Any) -> None:
        self.state[key] = value
        self.save()

    # Method to append a value to a list in the json file
    def append_to_list(self, key: str, value: Any) -> None:
        if key not in self.state or not isinstance(self.state[key], list):
            self.state[key] = []
        self.state[key].append(value)
        self.save()

    # Method to get a value from the json file or a default value if the key does not exist
    def get(self, key: str, default: Any = None) -> Any:
        return self.state.get(key, default)

    # Method to load the state from the json file if it exists
    def load(self) -> None:
        if os.path.exists(self.state_path):
            try:
                with open(self.state_path, "r") as f:
                    data = json.load(f)
                    for k, v in data.items():
                        self.state[k] = v
            except json.JSONDecodeError:
                print(f"Warning: Could not decode {self.state_path}. Starting fresh.")
            except Exception as e:
                print(f"Error loading state: {e}")

    # Method to save the current state to the json file
    def save(self) -> None:
        try:
            with open(self.state_path, "w") as f:
                json.dump(self.state, f, indent=4)
        except Exception as e:
            print(f"Error saving state: {e}")
