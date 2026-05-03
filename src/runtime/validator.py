from src.state_manager import StoryState


# Function to validate and sanitize proposed world state changes before applying them
def validate_changes(proposed_changes: list, state: StoryState) -> dict:
    # Get the player's current state including location and inventory
    player_state   = state.get("player_state", {})
    inventory      = set(player_state.get("inventory", []))
    current_loc    = player_state.get("current_location_id", "")

    # Build maps for quick lookup of objects, NPCs, rooms, and plot points
    obj_map   = {o["id"]: o for o in state.get("objects", [])}
    npc_map   = {n["id"]: n for n in state.get("npcs", [])}
    room_map  = {r["id"]: r for r in state.get("world_graph", {}).get("rooms", [])}
    pp_map    = {pp["id"]: pp for pp in state.get("annotated_plot_points", [])}
    completed = set(state.get("completed_plot_points", []))
    protected = {pv.get("object_or_npc_id") for pv in state.get("protected_variables", [])}

    valid_changes, rejected, warnings = [], [], []

    # Validate each proposed change and split into valid and rejected lists
    for change in proposed_changes:
        ctype  = change.get("type", "")
        target = change.get("target_id", "")
        reason = _reject_reason(
            ctype, target, change,
            obj_map, npc_map, room_map, pp_map,
            completed, protected, inventory, current_loc,
            warnings,
        )
        if reason:
            rejected.append({"change": change, "reason": reason})
        else:
            valid_changes.append(change)

    return {"valid_changes": valid_changes, "rejected": rejected, "warnings": warnings}


# Helper to determine if a proposed change should be rejected, returning the reason or None
def _reject_reason(
    ctype: str,
    target: str,
    change: dict,
    obj_map: dict,
    npc_map: dict,
    room_map: dict,
    pp_map: dict,
    completed: set,
    protected: set,
    inventory: set,
    current_loc: str,
    warnings: list,
) -> str | None:
    """Return a rejection reason string, or None if the change is acceptable."""

    if ctype == "pick_up_item":
        obj = obj_map.get(target)
        if not obj:
            return f"object '{target}' does not exist in the world"
        if not obj.get("can_be_picked_up", True):
            return f"'{obj.get('name', target)}' cannot be picked up"
        if obj.get("in_inventory"):
            return f"'{obj.get('name', target)}' is already in inventory"
        if obj.get("location_id") != current_loc:
            warnings.append(f"pick_up_item: '{target}' is not in the current room")

    elif ctype == "drop_item":
        obj = obj_map.get(target)
        if not obj:
            return f"object '{target}' does not exist"
        if obj.get("name", "") not in inventory and not obj.get("in_inventory"):
            return f"'{obj.get('name', target)}' is not in inventory"

    elif ctype == "reveal_object":
        if target and target not in obj_map:
            warnings.append(f"reveal_object: '{target}' not found; change skipped silently")

    elif ctype == "gain_knowledge":
        value = change.get("new_value", "").strip()
        if not value:
            return "gain_knowledge requires a non-empty new_value"

    elif ctype == "change_object_state":
        obj = obj_map.get(target)
        if not obj:
            warnings.append(f"change_object_state: '{target}' not found")
        elif obj.get("is_protected"):
            warnings.append(f"changing state of protected object '{obj.get('name', target)}'")

    elif ctype == "change_npc_state":
        if target and target not in npc_map:
            warnings.append(f"change_npc_state: NPC '{target}' not found")

    elif ctype == "complete_plot_point":
        if target in completed:
            return f"plot point '{target}' is already completed"
        if target and target not in pp_map:
            warnings.append(f"complete_plot_point: '{target}' not found in story")
        if target in protected:
            warnings.append(f"completing '{target}' affects a protected variable")

    elif ctype == "move_to_room":
        if target and target not in room_map:
            # LLMs sometimes use a display name or character name instead of the room ID.
            # Try fuzzy matching against room IDs and names before rejecting.
            target_lower = target.lower()
            fuzzy = next(
                (r for r in room_map.values()
                 if target_lower in r["id"].lower()
                 or target_lower in r.get("name", "").lower()
                 or r["id"].lower() in target_lower
                 or r.get("name", "").lower() in target_lower),
                None
            )
            if fuzzy:
                change["target_id"] = fuzzy["id"]
            else:
                return f"room '{target}' does not exist"

    return None
