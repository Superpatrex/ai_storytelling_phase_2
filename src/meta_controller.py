import importlib
import sys
import os
from src.llm_client import LLMClient
from src.state_manager import StoryState
from src.config import BASE_DIR

# Class that controls the overall story narrative generation process, executing each phase one by one
class MetaController:
    # Constructor for the Meta controller. Instantiates the LLM Client and the Story State Class
    def __init__(self):
        self.llm = LLMClient()
        self.state = StoryState()
    
    # Method that runs the specific story state based on the key
    def run_phase(self, phase_module_name: str) -> None:
        print(f"\n--- Running Phase: {phase_module_name} ---")
        try:
             # Ensure src is in sys.path
             if BASE_DIR not in sys.path:
                  sys.path.insert(0, BASE_DIR)
             
             module = importlib.import_module(f"src.phases.{phase_module_name}")
             
             if hasattr(module, "execute"):
                 module.execute(self)
             else:
                 print(f"Error: Module {phase_module_name} does not have an execute() function.")
                 
        except ImportError as e:
             print(f"Error loading phase {phase_module_name}: {e}")
        except Exception as e:
             print(f"Exception during {phase_module_name}: {e}")

    def run_all(self):
        print("Initializing Story Generation...")

        # Run the first stage of the story generation process to generate the goal and the hidden truths
        self.run_phase("01_initialize")
        
        # Run the second stage of the story generation process to form the overall narrative outline
        self.run_phase("02_loop")

        # Run the first part of the third stage of the story generation process to fix the overall outline and plot holes 
        self.run_phase("03_fixer")
        
        # Run the second part of the third stage of the story generation process to form the final story from the fixed story outline
        self.run_phase("04_details")

        print("\nStory generation complete! Check the output/ directory.")
