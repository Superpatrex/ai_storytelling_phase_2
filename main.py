import os
from src.meta_controller import MetaController
import src.ui as ui
from src.config import STATE_DIR


def main():
    print("╔══════════════════════════════════════════╗")
    print("║    AI Interactive Mystery Generator      ║")
    print("╚══════════════════════════════════════════╝")
    print()

    state_file = os.path.join(STATE_DIR, "current_state.json")
    has_existing_state = os.path.exists(state_file)

    if has_existing_state:
        print("An existing game state was found.")
        print("  [1] Play the existing story")
        print("  [2] Generate a new story (overwrites existing)")
        print("  [3] Quit")
        choice = input("\nChoice: ").strip()
    else:
        print("No existing game found.")
        print("  [1] Generate a new story")
        print("  [2] Quit")
        choice = input("\nChoice: ").strip()
        # Remap so [1] = generate when no state exists
        if choice == "1":
            choice = "2"
        elif choice == "2":
            choice = "3"

    if choice == "1" and has_existing_state:
        controller = MetaController()
        controller.play_game()

    elif choice == "2":
        # Fresh generation — wipe previous state
        if os.path.exists(state_file):
            os.remove(state_file)
            print("Previous state cleared.")
        controller = MetaController()
        controller.run_all()

    else:
        print("Goodbye!")


if __name__ == "__main__":
    main()
