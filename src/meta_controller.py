import importlib
import sys
import os
from src.llm_client import LLMClient
from src.state_manager import StoryState
from src.config import BASE_DIR


class MetaController:
    def __init__(self):
        self.llm = LLMClient()
        self.state = StoryState()

    def run_phase(self, phase_module_name: str) -> None:
        print(f"\n--- Running Phase: {phase_module_name} ---")
        try:
            if BASE_DIR not in sys.path:
                sys.path.insert(0, BASE_DIR)

            module = importlib.import_module(f"src.phases.{phase_module_name}")

            if hasattr(module, "execute"):
                module.execute(self)
            else:
                print(f"Error: Module {phase_module_name} has no execute() function.")

        except ImportError as e:
            print(f"Error loading phase {phase_module_name}: {e}")
        except Exception as e:
            print(f"Exception during {phase_module_name}: {e}")
            raise

    def run_all(self):
        """Run the full pre-generation pipeline to produce a game-ready world."""
        print("Starting Story & World Generation Pipeline...")

        # Phase 1 — Hidden truth + goal
        self.run_phase("01_initialize")

        # Phase 2 — Narrative loop (story beats)
        self.run_phase("02_loop")

        # Phase 3a — Fix + structure plot points
        self.run_phase("03_fixer")

        # Phase 3b — Annotate with preconditions/effects
        self.run_phase("04_plot_point_annotator")

        # Phase 3c — Build causal dependency graph
        self.run_phase("05_dependency_analyzer")

        # Phase 3d — Build navigable world map
        self.run_phase("06_world_graph_builder")

        # Phase 3e — Place objects and NPCs
        self.run_phase("07_object_npc_placer")

        print("\nGeneration complete! World is ready to play.")
        print("Run again and choose 'Play' to start the interactive game.")

    def play_game(self):
        """Start the interactive game loop using the generated world."""
        from src.runtime.game_loop import GameLoop

        # Verify generation has been run
        if not self.state.get("world_graph", {}).get("rooms"):
            print("ERROR: No world found. Run 'Generate Story' first.")
            return

        if not self.state.get("annotated_plot_points"):
            print("ERROR: No plot points found. Run 'Generate Story' first.")
            return

        game = GameLoop(self)
        game.run()
