import json
from src.prompts import DRAMA_MANAGER_PROMPT, DRAMA_MANAGER_SCHEMA


# Function to review a proposed player action and decide whether to approve, block, or intervene
def drama_manager_review(player_input: str, classification: dict, context: dict, llm) -> dict:
    # Get the plot point data for the drama manager to reason about
    all_plot_points = context.get("annotated_plot_points") or []
    completed = set(context.get("completed_plot_points") or [])

    # Split plot points into completed and remaining for the drama manager's context
    remaining = [pp["id"] for pp in all_plot_points if pp.get("id") not in completed]
    completed_list = list(completed)

    # Create the drama manager prompt with full story state and the proposed action
    prompt = DRAMA_MANAGER_PROMPT.format(
        hidden_truth=json.dumps(context.get("hidden_truth", {}), indent=2),
        protected_variables=json.dumps(context.get("protected_variables", []), indent=2),
        dependency_graph=json.dumps(context.get("dependency_graph", []), indent=2),
        player_input=player_input,
        action_type=classification.get("action_type", "consistent"),
        proposed_outcome=classification.get("proposed_outcome_description", ""),
        proposed_world_changes=json.dumps(classification.get("proposed_world_changes", []), indent=2),
        completed_plot_points=json.dumps(completed_list, indent=2),
        remaining_plot_points=json.dumps(remaining, indent=2)
    )

    # Generate the drama manager decision with the LLM
    result = llm.generate_json(prompt=prompt, schema=DRAMA_MANAGER_SCHEMA)

    # Default to approving if DM call fails
    if not result:
        return {
            "decision": "approve",
            "reason": "Default approval",
            "companion_message": "",
            "approved_outcome_description": classification.get("proposed_outcome_description", "Nothing happens."),
            "story_patch": []
        }

    return result
