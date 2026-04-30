import json
from src.prompts import DRAMA_MANAGER_PROMPT, DRAMA_MANAGER_SCHEMA


def drama_manager_review(player_input: str, classification: dict, context: dict, llm) -> dict:
    """
    Reviews the proposed action and decides whether to approve, block, or intervene.

    Returns: {decision, reason, companion_message, approved_outcome_description, story_patch}
    """
    all_plot_points = context.get("annotated_plot_points") or []
    completed = set(context.get("completed_plot_points") or [])

    remaining = [pp["id"] for pp in all_plot_points if pp.get("id") not in completed]
    completed_list = list(completed)

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

    result = llm.generate_json(prompt=prompt, schema=DRAMA_MANAGER_SCHEMA)

    if not result:
        # Default to approving if DM call fails
        return {
            "decision": "approve",
            "reason": "Default approval",
            "companion_message": "",
            "approved_outcome_description": classification.get("proposed_outcome_description", "Nothing happens."),
            "story_patch": []
        }

    return result
