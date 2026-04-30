import json
from src.prompts import FIXER_PROMPT, FIXER_SCHEMA


def execute(controller):
    print("  -> Starting The Fixer Phase (structured plot points)...")

    protagonist_name = controller.state.get("protagonist", {}).get("Name", "The Detective")
    goal = controller.state.get("goal", "Solve the crime")
    hidden_truth = controller.state.get("hidden_truth", {}).get("hidden_truth_summary", "")
    story_elements = controller.state.get("story_elements", [])

    if not story_elements:
        print("     No story elements found. Skipping fixer phase.")
        return

    fixer_prompt = FIXER_PROMPT.format(
        protagonist_name=protagonist_name,
        goal=goal,
        hidden_truth=hidden_truth,
        story_elements=json.dumps(story_elements, indent=2)
    )

    print("     Reviewing and restructuring story outline...")

    fixer_data = controller.llm.generate_json(
        prompt=fixer_prompt,
        schema=FIXER_SCHEMA
    )

    plot_points = fixer_data.get("plot_points", [])
    plot_holes_fixed = fixer_data.get("plot_holes_fixed", [])

    if plot_points:
        controller.state.update("plot_points", plot_points)
        controller.state.update("plot_holes_fixed", plot_holes_fixed)
        print(f"     Generated {len(plot_points)} structured plot points.")
        print(f"     Fixed {len(plot_holes_fixed)} plot holes.")
    else:
        print("     Failed to generate structured plot points.")
