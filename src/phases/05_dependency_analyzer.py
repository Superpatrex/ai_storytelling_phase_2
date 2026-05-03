import json
from src.prompts import DEPENDENCY_ANALYZER_PROMPT, DEPENDENCY_ANALYZER_SCHEMA


# Method to execute the dependency analyzer phase of the story generation process
def execute(controller):
    print("  -> Starting Dependency Analyzer Phase...")

    # Get the annotated plot points from the state
    annotated_plot_points = controller.state.get("annotated_plot_points", [])
    if not annotated_plot_points:
        print("     No annotated plot points found. Skipping dependency analysis.")
        return

    # Create the prompt for the dependency analyzer
    prompt = DEPENDENCY_ANALYZER_PROMPT.format(
        annotated_plot_points=json.dumps(annotated_plot_points, indent=2)
    )

    print("     Analyzing causal dependencies between plot points...")

    # Generate the causal dependency graph with the LLM
    data = controller.llm.generate_json(
        prompt=prompt,
        schema=DEPENDENCY_ANALYZER_SCHEMA
    )

    dependencies = data.get("dependencies", [])

    if not dependencies:
        print("     Failed to generate dependency graph.")
        return

    # Update the state with the generated dependency graph
    controller.state.update("dependency_graph", dependencies)

    # Count non-trivial dependencies for reporting
    with_deps = sum(1 for d in dependencies if d.get("depends_on"))
    with_spans = sum(1 for d in dependencies if d.get("causal_spans"))
    print(f"     Dependency graph built: {len(dependencies)} nodes, "
          f"{with_deps} with prerequisites, {with_spans} with causal spans.")
