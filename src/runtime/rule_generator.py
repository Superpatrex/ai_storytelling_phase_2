import json
from src.prompts import RULE_GENERATOR_PROMPT, RULE_GENERATOR_SCHEMA

MAX_RULE_DEPTH = 2  # Maximum recursive depth for cascading new content


def generate_rule(player_input: str, context: dict, llm, depth: int = 0) -> dict:
    """
    Generates a new action rule for an unknown player action.
    May recursively generate rules for sub-actions if new objects/locations are needed.

    Returns: {new_rule, new_objects_needed, new_locations_needed,
              existing_rules_to_update, preconditions_not_met_message}
    """
    current_room = context.get("current_room") or {}
    player_state = context.get("player_state") or {}
    setting = context.get("setting") or {}
    setting_str = f"{setting.get('location', 'Unknown')} ({setting.get('time', 'Modern Day')})"

    prompt = RULE_GENERATOR_PROMPT.format(
        player_input=player_input,
        current_room_name=current_room.get("name", "Unknown"),
        inventory=", ".join(player_state.get("inventory", [])) or "nothing",
        setting=setting_str,
        action_rules=json.dumps(context.get("action_rules", []), indent=2)
    )

    result = llm.generate_json(prompt=prompt, schema=RULE_GENERATOR_SCHEMA)

    if not result:
        return {
            "new_rule": None,
            "new_objects_needed": [],
            "new_locations_needed": [],
            "existing_rules_to_update": [],
            "preconditions_not_met_message": "You're not sure how to do that."
        }

    # If new objects or locations are needed and we haven't hit depth limit,
    # notify the caller — the game_loop will add these to the world and inform the player.
    if depth < MAX_RULE_DEPTH:
        new_objs = result.get("new_objects_needed", [])
        new_locs = result.get("new_locations_needed", [])
        if new_objs or new_locs:
            print(f"     [Rule Generator depth {depth}] New content needed: "
                  f"{len(new_objs)} objects, {len(new_locs)} locations.")

    return result
