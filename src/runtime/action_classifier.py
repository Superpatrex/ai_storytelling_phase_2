import json
from src.prompts import ACTION_CLASSIFIER_PROMPT, ACTION_CLASSIFIER_SCHEMA


def classify_action(player_input: str, context: dict, llm) -> dict:
    """
    Classifies the player's action and proposes world state changes.
    Returns: {action_type, triggered_plot_point_id, proposed_world_changes,
              proposed_outcome_description, exception_reason, is_commonsense_valid}
    """
    current_room = context.get("current_room") or {}
    player_state = context.get("player_state") or {}
    room_objects = context.get("room_objects") or []
    room_npcs = context.get("room_npcs") or []
    all_plot_points = context.get("annotated_plot_points") or []
    completed = set(context.get("completed_plot_points") or [])

    # Only pass pending (incomplete) plot points to reduce prompt size
    pending_plot_points = [
        {k: v for k, v in pp.items() if k != "effects"}  # hide effects from classifier
        for pp in all_plot_points
        if pp.get("id") not in completed
    ]

    exits = [
        f"{c['direction']} ({c.get('label', c['to_room_id'])})"
        for c in current_room.get("connections", [])
    ]

    obj_names = [o["name"] for o in room_objects if not o.get("in_inventory")]
    npc_names = [n["name"] for n in room_npcs]

    prompt = ACTION_CLASSIFIER_PROMPT.format(
        protagonist_name=context.get("protagonist", {}).get("Name", "The Detective"),
        goal=context.get("goal", "Solve the crime"),
        current_room_name=current_room.get("name", "Unknown"),
        current_room_description=current_room.get("description", ""),
        exits=", ".join(exits) if exits else "none",
        room_objects=", ".join(obj_names) if obj_names else "nothing visible",
        room_npcs=", ".join(npc_names) if npc_names else "no one",
        inventory=", ".join(player_state.get("inventory", [])) or "nothing",
        knowledge=", ".join(player_state.get("knowledge", [])) or "nothing yet",
        pending_plot_points=json.dumps(pending_plot_points, indent=2),
        protected_variables=json.dumps(context.get("protected_variables", []), indent=2),
        action_rules=json.dumps(context.get("action_rules", []), indent=2),
        player_input=player_input
    )

    result = llm.generate_json(prompt=prompt, schema=ACTION_CLASSIFIER_SCHEMA)

    if not result:
        return {
            "action_type": "consistent",
            "triggered_plot_point_id": "",
            "is_commonsense_valid": True,
            "proposed_world_changes": [],
            "proposed_outcome_description": "Nothing seems to happen.",
            "exception_reason": ""
        }

    return result
