import json
from src.prompts import PLOT_POINT_ANNOTATOR_PROMPT, PLOT_POINT_ANNOTATOR_SCHEMA

# Method to execute the plot point annotator
def execute(controller):
    print("  -> Starting Plot Point Annotator Phase...")

    # Get the plot points from the fixer phase output
    plot_points = controller.state.get("plot_points", [])
    if not plot_points:
        print("     No plot points found. Skipping annotator phase.")
        return

    # Get the story context needed to annotate the plot points
    protagonist_name = controller.state.get("protagonist", {}).get("Name", "The Detective")
    goal = controller.state.get("goal", "Solve the crime")
    setting = controller.state.get("setting", {})
    characters = controller.state.get("characters", [])

    # Format the setting and characters for the prompt
    setting_str = f"{setting.get('location', 'Unknown')} ({setting.get('time', 'Modern Day')})"
    characters_str = json.dumps([
        {"name": c.get("Name", ""), "role": c.get("Role", "")}
        for c in characters
    ], indent=2)

    # Create the prompt for the plot point annotator
    prompt = PLOT_POINT_ANNOTATOR_PROMPT.format(
        protagonist_name=protagonist_name,
        goal=goal,
        setting=setting_str,
        characters=characters_str,
        plot_points=json.dumps(plot_points, indent=2)
    )

    print("     Annotating plot points with preconditions and effects...")

    # Generate the annotated plot points and protected variables with the LLM
    data = controller.llm.generate_json(
        prompt=prompt,
        schema=PLOT_POINT_ANNOTATOR_SCHEMA
    )

    annotated = data.get("annotated_plot_points", [])
    protected = data.get("protected_variables", [])

    if not annotated:
        print("     Failed to annotate plot points.")
        return

    # Merge annotations back onto the original plot points so all fields are in one place
    annotation_map = {a["id"]: a for a in annotated}
    merged = []
    for pp in plot_points:
        ann = annotation_map.get(pp["id"], {})
        merged.append({
            **pp,
            "preconditions": ann.get("preconditions", []),
            "effects": ann.get("effects", []),
            "is_protected": ann.get("is_protected", False)
        })

    controller.state.update("annotated_plot_points", merged)
    controller.state.update("protected_variables", protected)

    print(f"     Annotated {len(merged)} plot points.")
    print(f"     Identified {len(protected)} protected variables.")
