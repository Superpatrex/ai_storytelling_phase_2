def check_preconditions(classification: dict, context: dict) -> dict:
    """
    Deterministically check whether all preconditions for a classified action are satisfied.
    Called after classification and rule generation, before Drama Manager review.

    Only meaningful for 'constituent' and 'consistent' action types.

    Returns:
        {
            "all_met":      bool,
            "met":          list of satisfied precondition dicts,
            "unmet":        list of unsatisfied precondition dicts,
            "unmet_message": str — player-facing explanation (empty if all met),
        }
    """
    action_type = classification.get("action_type", "consistent")
    if action_type not in ("constituent", "consistent"):
        return {"all_met": True, "met": [], "unmet": [], "unmet_message": ""}

    preconditions = _gather_preconditions(classification, context)
    if not preconditions:
        return {"all_met": True, "met": [], "unmet": [], "unmet_message": ""}

    player_state = context.get("player_state", {})
    inventory   = {item.lower() for item in player_state.get("inventory", [])}
    knowledge   = [k.lower() for k in player_state.get("knowledge", [])]
    location    = player_state.get("current_location_id", "")
    room_npcs   = context.get("room_npcs", [])
    room_objects = context.get("room_objects", [])

    met, unmet = [], []
    for pc in preconditions:
        if _is_satisfied(pc, inventory, knowledge, location, room_npcs, room_objects):
            met.append(pc)
        else:
            unmet.append(pc)

    unmet_message = ""
    if unmet:
        parts = [pc.get("description") or pc.get("value", "") for pc in unmet]
        unmet_message = "You can't do that yet — " + "; ".join(p for p in parts if p) + "."

    return {
        "all_met": len(unmet) == 0,
        "met": met,
        "unmet": unmet,
        "unmet_message": unmet_message,
    }


def _gather_preconditions(classification: dict, context: dict) -> list:
    action_type = classification.get("action_type")

    if action_type == "constituent":
        pp_id = classification.get("triggered_plot_point_id", "")
        for pp in context.get("annotated_plot_points", []):
            if pp.get("id") == pp_id:
                return pp.get("preconditions", [])

    elif action_type == "consistent":
        rule_id = classification.get("matched_rule_id", "")
        if rule_id:
            for rule in context.get("action_rules", []):
                if rule.get("id") == rule_id:
                    return rule.get("preconditions", [])

    return []


def _is_satisfied(
    pc: dict,
    inventory: set,
    knowledge: list,
    location: str,
    room_npcs: list,
    room_objects: list,
) -> bool:
    ptype = pc.get("type", "")
    value = str(pc.get("value", "")).lower()

    if ptype == "has_item":
        return any(value in item or item in value for item in inventory)

    if ptype == "knows_fact":
        return any(value in k or k in value for k in knowledge)

    if ptype == "player_location":
        return location == pc.get("value", "")

    if ptype == "npc_present":
        return any(
            value in n.get("id", "").lower() or value in n.get("name", "").lower()
            for n in room_npcs
        )

    if ptype == "object_state":
        for obj in room_objects:
            state = obj.get("state", {}).get("status", "").lower()
            if value in state or value in obj.get("id", "").lower() or value in obj.get("name", "").lower():
                return True
        return False

    return True  # unknown type — be permissive
