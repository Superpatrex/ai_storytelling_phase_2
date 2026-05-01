import importlib
import sys
import os
from src.llm_client import LLMClient
from src.state_manager import StoryState
from src.config import BASE_DIR

PHASE_LABELS = {
    "01_initialize": "Initializing story",
    "02_loop": "Writing story beats",
    "03_fixer": "Fixing plot holes",
    "04_plot_point_annotator": "Annotating plot points",
    "05_dependency_analyzer": "Analyzing dependencies",
    "06_world_graph_builder": "Building world map",
    "07_object_npc_placer": "Placing objects & characters",
}


class MetaController:
    def __init__(self, progress_callback=None):
        self.llm = LLMClient()
        self.state = StoryState()
        self.progress_callback = progress_callback

    def _emit_progress(self, phase: str, status: str):
        if self.progress_callback:
            self.progress_callback({
                "type": "generation_progress",
                "phase": phase,
                "status": status,
                "label": PHASE_LABELS.get(phase, phase),
            })

    def run_phase(self, phase_module_name: str) -> None:
        self._emit_progress(phase_module_name, "starting")
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
            self._emit_progress(phase_module_name, "error")
            raise

        self._emit_progress(phase_module_name, "complete")

    def run_all(self):
        """Run the full pre-generation pipeline to produce a game-ready world."""
        print("Starting Story & World Generation Pipeline...")

        self.run_phase("01_initialize")
        self.run_phase("02_loop")
        self.run_phase("03_fixer")
        self.run_phase("04_plot_point_annotator")
        self.run_phase("05_dependency_analyzer")
        self.run_phase("06_world_graph_builder")
        self.run_phase("07_object_npc_placer")

        print("\nGeneration complete! World is ready to play.")

    def play_game(self):
        """Start the interactive game loop using the generated world."""
        from src.runtime.game_loop import GameLoop

        if not self.state.get("world_graph", {}).get("rooms"):
            print("ERROR: No world found. Run 'Generate Story' first.")
            return

        if not self.state.get("annotated_plot_points"):
            print("ERROR: No plot points found. Run 'Generate Story' first.")
            return

        game = GameLoop(self)
        game.run()
