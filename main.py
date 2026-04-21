import os
from src.meta_controller import MetaController
from src.config import STATE_DIR

def main():
    print("Welcome to the AI Suspense Story Generator")
    print("==========================================")

    # Look for the current_state.json file
    state_file = os.path.join(STATE_DIR, "current_state.json")

    # If the file is there delete it since we need to restart the ai story generation cycle
    if os.path.exists(state_file):
        os.remove(state_file)
        print("Cleaned up previous state file.")
        
    # Initialize the Meta Controller that will interface with the LLM
    controller = MetaController()
    
    # Run all four steps being the initialization phase,loop phase, fixer phase, and details phase
    controller.run_all()

if __name__ == "__main__":
    main()
