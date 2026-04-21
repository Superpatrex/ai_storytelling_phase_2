import json
import os
from typing import Dict, Any, List, Optional
from src.config import STATE_DIR

# Class that saves and updates the story state to the json file
class StoryState:
    # Initialized the story state with all the necessary keys and default values of our json file
    def __init__(self, state_file: str = "current_state.json"):
        self.state_file: str = state_file
        self.state_path: str = os.path.join(STATE_DIR, state_file)
        self.state: Dict[str, Any] = {
            "protagonist": {}, # Name, Role, Reason, and Connection of the central protagonist of the story
            "characters": [], # List of characters in the story that contains the Name, Role, Reason, and Connection
            "hidden_truth": {}, # Pre-generated initialization of the hidden crime story. Includes the culprit name, motive, method, hidden truth summary, suspects, and potential locations.
            "goal": "", # The protagonist's goal
            "loop_step": 0, # The specific iteration of the loop cycle
            "actions_taken": [], # A list of all the actions that has been taken within the story
            "current_action": None, # The current action that the protagonist or characters are taking within the current iteration of the story
            "red_herrings_used": 0, # The number of red herrings that has been used within the story
            "story_elements": [] # The list of story elements that has been taken either for the action or the obstacle
        }

        # Load the dictionary into the json file 
        self.load()

    # Update the state with a new value for that specific key and then saves it to the json file
    def update(self, key: str, value: Any) -> None:
        self.state[key] = value
        self.save()

    # Appends a value to a list within the json file for a specific key
    def append_to_list(self, key: str, value: Any) -> None:
        if key not in self.state or not isinstance(self.state[key], list):
            self.state[key] = []
        self.state[key].append(value)
        self.save()

    # Retrieves a value from the current state json file for a specific key
    def get(self, key: str, default: Any = None) -> Any:
        return self.state.get(key, default)

    # Loads the state from the json file if it exists otherwise it will start with the default state structure defined in the __init__ method. This allows us to persist the state across different runs of the program and also to recover from any potential crashes or interruptions without losing all progress.
    def load(self) -> None:
        if os.path.exists(self.state_path):
            try:
                with open(self.state_path, "r") as f:
                    data = json.load(f)
                    # Merge loaded data with default structure to ensure keys exist
                    for k, v in data.items():
                        self.state[k] = v
            except json.JSONDecodeError:
                print(f"Warning: Could not decode {self.state_path}. Starting fresh.")
            except Exception as e:
                print(f"Error loading state: {e}")

    # Saves the current state to the json file.
    def save(self) -> None:
        try:
            with open(self.state_path, "w") as f:
                json.dump(self.state, f, indent=4)
        except Exception as e:
            print(f"Error saving state: {e}")
