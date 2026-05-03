import json
from src.prompts import FIXER_PROMPT, FIXER_SCHEMA

# Method to execute the fixer phase of the story generation process
def execute(controller):
    print("  -> Starting The Fixer Phase (structured plot points)...")

    # Get the data from the current_state.json file that was generated in the loop phase
    protagonist_name = controller.state.get("protagonist", {}).get("Name", "The Detective")
    goal = controller.state.get("goal", "Solve the crime")
    hidden_truth = controller.state.get("hidden_truth", {}).get("hidden_truth_summary", "")
    story_elements = controller.state.get("story_elements", [])

    # If there are no story elements, leave
    if not story_elements:
        print("     No story elements found. Skipping fixer phase.")
        return

    # Create the prompt for the fixer phase
    fixer_prompt = FIXER_PROMPT.format(
        protagonist_name=protagonist_name,
        goal=goal,
        hidden_truth=hidden_truth,
        story_elements=json.dumps(story_elements, indent=2)
    )

    print("     Reviewing and restructuring story outline...")

    # Generate the structure plot points and identify plot holes
    fixer_data = controller.llm.generate_json(
        prompt=fixer_prompt,
        schema=FIXER_SCHEMA
    )

    # Update the state with the generated plot points and fixed plot holes
    plot_points = fixer_data.get("plot_points", [])
    plot_holes_fixed = fixer_data.get("plot_holes_fixed", [])

    # If the plot points were generated, update the state and print the results
    if plot_points:
        controller.state.update("plot_points", plot_points)
        controller.state.update("plot_holes_fixed", plot_holes_fixed)
        print(f"     Generated {len(plot_points)} structured plot points.")
        print(f"     Fixed {len(plot_holes_fixed)} plot holes.")
    else:
        print("     Failed to generate structured plot points.")
