import json
from src.prompts import RULE_GENERATOR_PROMPT, RULE_GENERATOR_SCHEMA

MAX_RULE_DEPTH = 2  # Maximum recursive depth for cascading new content


# Function to generate a new action rule for an unknown player action
def generate_rule(player_input: str, context: dict, llm, depth: int = 0) -> dict:
    # Get the current room, player state, and setting for the prompt context
    current_room = context.get("current_room") or {}
    player_state = context.get("player_state") or {}
    setting = context.get("setting") or {}
    setting_str = f"{setting.get('location', 'Unknown')} ({setting.get('time', 'Modern Day')})"

    # Format NPCs and objects visible in the current room so the LLM knows who/what is present
    room_npcs = context.get("room_npcs") or []
    room_objects = context.get("room_objects") or []
    npc_names = ", ".join(n["name"] for n in room_npcs) or "no one"
    obj_names = ", ".join(o["name"] for o in room_objects if not o.get("in_inventory")) or "nothing"

    # Create the rule generator prompt with the current game context
    prompt = RULE_GENERATOR_PROMPT.format(
        player_input=player_input,
        current_room_name=current_room.get("name", "Unknown"),
        room_npcs=npc_names,
        room_objects=obj_names,
        inventory=", ".join(player_state.get("inventory", [])) or "nothing",
        setting=setting_str,
        action_rules=json.dumps(context.get("action_rules", []), indent=2)
    )

    # Generate the new rule with the LLM
    result = llm.generate_json(prompt=prompt, schema=RULE_GENERATOR_SCHEMA)

    # Return a default result if the LLM call fails
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
