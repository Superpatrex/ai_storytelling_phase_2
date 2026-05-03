from src.runtime.action_classifier import classify_action
from src.runtime.rule_generator import generate_rule
from src.runtime.drama_manager import drama_manager_review
from src.runtime.precondition_checker import check_preconditions
from src.runtime.validator import validate_changes

MOVEMENT_DIRECTIONS = {
    "north", "south", "east", "west",
    "northeast", "northwest", "southeast", "southwest",
    "up", "down", "inside", "outside", "back"
}


# Class that manages the interactive game loop, player actions, and world state updates
class GameLoop:
    # Initialization for the GameLoop
    def __init__(self, controller, output_callback=None):
        self.controller = controller
        self.llm = controller.llm
        self.state = controller.state
        self.output_callback = output_callback
        self._init_player_state()

    # Internal method to send output to the frontend callback or print to the console
    def _emit(self, text: str, category: str = "narrative"):
        if self.output_callback:
            self.output_callback({"type": "game_output", "text": text, "category": category})
        else:
            print(text)

    # ── Initialization ─────────────────────────────────────────────────────

    def _init_player_state(self):
        """Set up player state at game start if not already present."""
        if self.state.get("player_state"):
            return

        protagonist = self.state.get("protagonist", {})
        world_graph = self.state.get("world_graph", {"rooms": [], "starting_room_id": ""})
        start_id = world_graph.get("starting_room_id") or (
            world_graph["rooms"][0]["id"] if world_graph["rooms"] else "unknown"
        )

        skills = protagonist.get("Skills", [])
        if isinstance(skills, str):
            skills = [skills]

        self.state.update("player_state", {
            "current_location_id": start_id,
            "inventory": [],
            "knowledge": [],
            "skills": skills
        })

    # ── World lookups ───────────────────────────────────────────────────────

    def _get_room(self, room_id: str) -> dict:
        rooms = self.state.get("world_graph", {}).get("rooms", [])
        return next((r for r in rooms if r["id"] == room_id), None)

    def _current_room(self) -> dict:
        loc_id = self.state.get("player_state", {}).get("current_location_id", "")
        return self._get_room(loc_id)

    def _objects_in_room(self, room_id: str) -> list:
        return [
            o for o in self.state.get("objects", [])
            if o.get("location_id") == room_id
            and not o.get("in_inventory")
            and o.get("visible", True)
        ]

    def _npcs_in_room(self, room_id: str) -> list:
        return [
            n for n in self.state.get("npcs", [])
            if n.get("current_location_id") == room_id
        ]

    # ── Display ─────────────────────────────────────────────────────────────

    def display_location(self):
        room = self._current_room()
        if not room:
            self._emit("ERROR: You are in an unknown location.", "error")
            return

        self._emit("", "separator")
        self._emit(f"  {room['name'].upper()}", "room_name")
        self._emit(room["description"], "room_desc")

        connections = room.get("connections", [])
        if connections:
            exits = [f"{c['direction']} → {c.get('label', c['to_room_id'])}" for c in connections]
            self._emit(f"Exits: {', '.join(exits)}", "exits")

        room_objects = self._objects_in_room(room["id"])
        if room_objects:
            self._emit(f"You see: {', '.join(o['name'] for o in room_objects)}", "objects_present")

        room_npcs = self._npcs_in_room(room["id"])
        if room_npcs:
            self._emit(f"People here: {', '.join(n['name'] for n in room_npcs)}", "npcs_present")

        inventory = self.state.get("player_state", {}).get("inventory", [])
        if inventory:
            self._emit(f"Carrying: {', '.join(inventory)}", "inventory_line")

        if self.output_callback:
            self.output_callback({
                "type": "game_location",
                "room": room,
                "objects": room_objects,
                "npcs": room_npcs,
                "inventory": inventory,
            })

    # ── Movement (fast path, no LLM) ────────────────────────────────────────

    def _try_move(self, direction: str) -> bool:
        room = self._current_room()
        if not room:
            return False
        for conn in room.get("connections", []):
            if conn["direction"].lower() == direction.lower():
                player_state = self.state.get("player_state", {})
                player_state["current_location_id"] = conn["to_room_id"]
                self.state.update("player_state", player_state)
                self._emit(f"You head {direction}.", "system")
                return True
        self._emit(f"You can't go {direction} from here.", "system")
        return False

    # Method to parse a movement command and return the direction string, or None if not a movement command
    def _parse_movement(self, text: str) -> str | None:
        text = text.lower().strip()
        if text in MOVEMENT_DIRECTIONS:
            return text
        for d in MOVEMENT_DIRECTIONS:
            if text == f"go {d}" or text == f"move {d}" or text == f"walk {d}":
                return d
        return None

    # ── World state changes ──────────────────────────────────────────────────

    def _apply_world_changes(self, changes: list):
        objects = self.state.get("objects", [])
        npcs = self.state.get("npcs", [])
        player_state = self.state.get("player_state", {})
        inventory = player_state.get("inventory", [])
        knowledge = player_state.get("knowledge", [])
        completed = self.state.get("completed_plot_points", [])

        obj_map = {o["id"]: o for o in objects}
        npc_map = {n["id"]: n for n in npcs}

        for change in changes:
            ctype = change.get("type", "")
            target = change.get("target_id", "")
            value = change.get("new_value", "")

            if ctype == "pick_up_item":
                obj = obj_map.get(target)
                if obj and obj.get("can_be_picked_up") and not obj.get("in_inventory"):
                    obj["in_inventory"] = True
                    obj["location_id"] = None
                    if obj["name"] not in inventory:
                        inventory.append(obj["name"])

            elif ctype == "drop_item":
                room = self._current_room()
                obj = obj_map.get(target)
                if obj and obj.get("in_inventory"):
                    obj["in_inventory"] = False
                    obj["location_id"] = room["id"] if room else None
                    if obj["name"] in inventory:
                        inventory.remove(obj["name"])

            elif ctype == "reveal_object":
                obj = obj_map.get(target)
                if obj:
                    obj["visible"] = True
                    if value:
                        obj["location_id"] = value

            elif ctype == "gain_knowledge":
                if value and value not in knowledge:
                    knowledge.append(value)

            elif ctype == "change_object_state":
                obj = obj_map.get(target)
                if obj:
                    obj.setdefault("state", {})["status"] = value

            elif ctype == "change_npc_state":
                npc = npc_map.get(target)
                if npc:
                    npc.setdefault("state", {})["status"] = value

            elif ctype == "complete_plot_point":
                if target and target not in completed:
                    completed.append(target)

            elif ctype == "move_to_room":
                room = self._get_room(target)
                if room:
                    player_state["current_location_id"] = target

        player_state["inventory"] = inventory
        player_state["knowledge"] = knowledge
        self.state.update("objects", objects)
        self.state.update("npcs", npcs)
        self.state.update("player_state", player_state)
        self.state.update("completed_plot_points", completed)

    # Method to add a new rule, objects, and locations generated by the rule engine to the world state
    def _apply_rule_result(self, rule_result: dict):
        new_rule = rule_result.get("new_rule")
        if new_rule:
            rules = self.state.get("action_rules", [])
            if not any(r["id"] == new_rule["id"] for r in rules):
                rules.append(new_rule)
                self.state.update("action_rules", rules)
                self._emit(f"[New rule created: '{new_rule['verb']}']", "system")

        new_objects = rule_result.get("new_objects_needed", [])
        if new_objects:
            objects = self.state.get("objects", [])
            existing_ids = {o["id"] for o in objects}
            for obj in new_objects:
                if obj["id"] not in existing_ids:
                    obj.setdefault("visible", True)
                    obj.setdefault("in_inventory", False)
                    obj.setdefault("state", {})
                    obj.setdefault("is_protected", False)
                    obj.setdefault("linked_plot_point_id", "")
                    objects.append(obj)
                    self._emit(f"[New object added: '{obj['name']}' in {obj.get('suggested_location_id', '?')}]", "system")
                    obj["location_id"] = obj.pop("suggested_location_id", "")
            self.state.update("objects", objects)

        new_locs = rule_result.get("new_locations_needed", [])
        if new_locs:
            world_graph = self.state.get("world_graph", {"rooms": [], "starting_room_id": ""})
            rooms = world_graph["rooms"]
            existing_ids = {r["id"] for r in rooms}
            room_map = {r["id"]: r for r in rooms}

            for loc in new_locs:
                if loc["id"] not in existing_ids:
                    new_room = {
                        "id": loc["id"],
                        "name": loc["name"],
                        "description": loc["description"],
                        "connections": [{"direction": "back",
                                         "to_room_id": loc["connect_to_room_id"],
                                         "label": "back the way you came"}],
                        "story_event_ids": []
                    }
                    rooms.append(new_room)
                    self._emit(f"[New location added: '{loc['name']}']", "system")

                    origin = room_map.get(loc["connect_to_room_id"])
                    if origin:
                        origin["connections"].append({
                            "direction": loc["direction_from_existing"],
                            "to_room_id": loc["id"],
                            "label": loc["name"]
                        })

            self.state.update("world_graph", world_graph)

        rule_updates = rule_result.get("existing_rules_to_update", [])
        if rule_updates:
            self._retrofit_rules(rule_updates)

    # Method to apply rule updates returned by the rule generator or Drama Manager
    def _retrofit_rules(self, updates: list):
        if not updates:
            return
        rules = self.state.get("action_rules", [])
        rule_map = {r["id"]: r for r in rules}
        applied = 0
        for upd in updates:
            rule = rule_map.get(upd.get("rule_id", ""))
            if not rule:
                continue
            if upd.get("updated_preconditions"):
                rule["preconditions"] = upd["updated_preconditions"]
            if upd.get("updated_effects_description"):
                rule["effects_description"] = upd["updated_effects_description"]
            applied += 1
            self._emit(f"[Rule updated: '{rule.get('verb', upd['rule_id'])}']", "system")
        if applied:
            self.state.update("action_rules", rules)

    # Method to apply story patches from the drama manager to modify or remove plot points
    def _apply_story_patch(self, patches: list):
        plot_points = self.state.get("annotated_plot_points", [])
        for patch in patches:
            action = patch.get("action", "")
            pp_id = patch.get("plot_point_id", "")
            new_desc = patch.get("new_description", "")
            if action == "modify":
                for pp in plot_points:
                    if pp["id"] == pp_id:
                        pp["description"] = new_desc
                        break
            elif action == "remove":
                plot_points = [pp for pp in plot_points if pp["id"] != pp_id]
        self.state.update("annotated_plot_points", plot_points)

    # ── Win condition ────────────────────────────────────────────────────────

    def _check_win(self, changes: list) -> bool:
        plot_points = self.state.get("annotated_plot_points", [])
        for change in changes:
            if change.get("type") == "complete_plot_point":
                pp_id = change.get("target_id", "")
                for pp in plot_points:
                    if pp.get("id") == pp_id and pp.get("type") == "resolution":
                        return True
        return False

    def _show_win(self):
        hidden_truth = self.state.get("hidden_truth", {})
        self._emit(f"\n{'═' * 50}", "win")
        self._emit("  MYSTERY SOLVED!", "win")
        self._emit(f"{'═' * 50}", "win")
        self._emit(f"The culprit was: {hidden_truth.get('culprit_name', 'Unknown')}", "win")
        self._emit(f"Motive:          {hidden_truth.get('motive', 'Unknown')}", "win")
        self._emit(f"Method:          {hidden_truth.get('method', 'Unknown')}", "win")
        self._emit(f"\n{hidden_truth.get('hidden_truth_summary', '')}", "win")
        self.state.update("game_complete", True)

    # ── Context builder ──────────────────────────────────────────────────────

    def _build_context(self) -> dict:
        room = self._current_room()
        room_id = room["id"] if room else ""
        return {
            "protagonist": self.state.get("protagonist", {}),
            "goal": self.state.get("goal", ""),
            "setting": self.state.get("setting", {}),
            "hidden_truth": self.state.get("hidden_truth", {}),
            "player_state": self.state.get("player_state", {}),
            "current_room": room,
            "room_objects": self._objects_in_room(room_id),
            "room_npcs": self._npcs_in_room(room_id),
            "annotated_plot_points": self.state.get("annotated_plot_points", []),
            "completed_plot_points": self.state.get("completed_plot_points", []),
            "dependency_graph": self.state.get("dependency_graph", []),
            "protected_variables": self.state.get("protected_variables", []),
            "action_rules": self.state.get("action_rules", []),
        }

    # ── Main action pipeline ─────────────────────────────────────────────────

    def process_action(self, player_input: str):
        direction = self._parse_movement(player_input)
        if direction:
            self._try_move(direction)
            return

        self._emit("\n  [Thinking...]", "system")
        context = self._build_context()

        classification = classify_action(player_input, context, self.llm)
        action_type = classification.get("action_type", "consistent")

        if action_type == "exceptional":
            reason = classification.get("exception_reason", "You shouldn't do that here.")
            dm_result = drama_manager_review(player_input, classification, context, self.llm)
            msg = dm_result.get("companion_message") or reason
            self._emit(f"\n  A voice nearby warns you: \"{msg}\"", "warning")
            return

        if action_type == "new_rule_needed":
            self._emit("  [Working out how to do that...]", "system")
            rule_result = generate_rule(player_input, context, self.llm)

            unmet_msg = rule_result.get("preconditions_not_met_message", "")
            new_objs = rule_result.get("new_objects_needed", [])
            new_locs = rule_result.get("new_locations_needed", [])

            self._apply_rule_result(rule_result)

            if new_objs or new_locs:
                items = [o["name"] for o in new_objs] + [l["name"] for l in new_locs]
                self._emit(f"\n  To do that, you'd need: {', '.join(items)}.", "system")
                if unmet_msg:
                    self._emit(f"  {unmet_msg}", "system")
                return

            if unmet_msg:
                self._emit(f"\n  {unmet_msg}", "system")
                return

            context = self._build_context()
            classification = classify_action(player_input, context, self.llm)

        # Precondition check — deterministic, no LLM call
        action_type = classification.get("action_type", "consistent")
        if action_type in ("constituent", "consistent"):
            pc_result = check_preconditions(classification, context)
            if not pc_result["all_met"]:
                self._emit(f"\n  {pc_result['unmet_message']}", "system")
                return

        dm_result = drama_manager_review(player_input, classification, context, self.llm)
        decision = dm_result.get("decision", "approve")

        if decision == "block":
            msg = dm_result.get("companion_message", "You feel something stopping you.")
            self._emit(f"\n  A voice nearby warns you: \"{msg}\"", "warning")
            return

        # generate_content: world element is missing — run rule generator to fill the gap
        if decision == "generate_content":
            hint = dm_result.get("content_hint") or player_input
            self._emit("  [Generating missing world content...]", "system")
            rule_result = generate_rule(hint, context, self.llm)
            self._apply_rule_result(rule_result)
            context = self._build_context()

        # retrofit_rules: existing rules are inconsistent with new world state
        elif decision == "retrofit_rules":
            self._retrofit_rules(dm_result.get("rules_to_retrofit", []))

        # plan_repair is handled after changes are applied (below)

        # Validate proposed changes — strips impossible ones before applying
        raw_changes = classification.get("proposed_world_changes", [])
        val_result = validate_changes(raw_changes, self.state)
        for r in val_result["rejected"]:
            self._emit(f"  [Skipped: {r['reason']}]", "system")
        changes = val_result["valid_changes"]

        self._apply_world_changes(changes)

        if decision == "plan_repair":
            self._apply_story_patch(dm_result.get("story_patch", []))

        outcome = (dm_result.get("approved_outcome_description")
                   or classification.get("proposed_outcome_description")
                   or "Nothing seems to happen.")
        self._emit(f"\n  {outcome}", "narrative")

        if self._check_win(changes):
            self._show_win()

        self.state.save()

    # ── Main loop (CLI only) ─────────────────────────────────────────────────

    def run(self):
        protagonist = self.state.get("protagonist", {})
        goal = self.state.get("goal", "Solve the crime")

        self._emit(f"\n{'═' * 50}", "system")
        self._emit(f"  INTERACTIVE MYSTERY", "system")
        self._emit(f"{'═' * 50}", "system")
        self._emit(f"You are {protagonist.get('Name', 'The Detective')}.", "system")
        self._emit(f"Your goal: {goal}", "system")
        self._emit(f"\nType actions in plain English (aim for ~5 words).", "system")
        self._emit(f"Commands: look | inventory | help | quit", "system")

        self.display_location()

        while not self.state.get("game_complete", False):
            try:
                raw = input("\n> ").strip()
            except (EOFError, KeyboardInterrupt):
                self._emit("\nGame saved. Goodbye!", "system")
                break

            if not raw:
                continue

            cmd = raw.lower()

            if cmd == "quit":
                self._emit("Game saved. Goodbye!", "system")
                break
            elif cmd in ("look", "l"):
                self.display_location()
            elif cmd in ("inventory", "i", "inv"):
                inv = self.state.get("player_state", {}).get("inventory", [])
                self._emit(f"Carrying: {', '.join(inv)}" if inv else "You are carrying nothing.", "system")
            elif cmd == "help":
                self._emit("Actions: look, inventory, go [direction], or describe any action.", "system")
                self._emit("Exits are shown after your location name.", "system")
            else:
                self.process_action(raw)
                self.display_location()

        if self.state.get("game_complete"):
            self._emit("\nThank you for playing!", "system")
