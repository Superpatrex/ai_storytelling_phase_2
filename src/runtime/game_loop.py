from src.runtime.action_classifier import classify_action
from src.runtime.rule_generator import generate_rule
from src.runtime.drama_manager import drama_manager_review

MOVEMENT_DIRECTIONS = {
    "north", "south", "east", "west",
    "northeast", "northwest", "southeast", "southwest",
    "up", "down", "inside", "outside", "back"
}


class GameLoop:
    def __init__(self, controller):
        self.controller = controller
        self.llm = controller.llm
        self.state = controller.state
        self._init_player_state()

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
            print("ERROR: You are in an unknown location.")
            return

        print(f"\n{'═' * 60}")
        print(f"  {room['name'].upper()}")
        print(f"{'═' * 60}")
        print(room["description"])

        connections = room.get("connections", [])
        if connections:
            exits = [f"{c['direction']} ({c.get('label', c['to_room_id'])})" for c in connections]
            print(f"\nExits: {', '.join(exits)}")

        room_objects = self._objects_in_room(room["id"])
        if room_objects:
            print(f"You see: {', '.join(o['name'] for o in room_objects)}")

        room_npcs = self._npcs_in_room(room["id"])
        if room_npcs:
            print(f"People here: {', '.join(n['name'] for n in room_npcs)}")

        inventory = self.state.get("player_state", {}).get("inventory", [])
        if inventory:
            print(f"Carrying: {', '.join(inventory)}")

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
                print(f"You head {direction}.")
                return True
        print(f"You can't go {direction} from here.")
        return False

    def _parse_movement(self, text: str) -> str | None:
        """Return direction string if the input is a movement command, else None."""
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

    def _apply_rule_result(self, rule_result: dict):
        """Add new rule, objects, and locations generated by the rule engine."""
        new_rule = rule_result.get("new_rule")
        if new_rule:
            rules = self.state.get("action_rules", [])
            if not any(r["id"] == new_rule["id"] for r in rules):
                rules.append(new_rule)
                self.state.update("action_rules", rules)
                print(f"     [New rule created: '{new_rule['verb']}']")

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
                    print(f"     [New object added to world: '{obj['name']}' in {obj.get('suggested_location_id', '?')}]")
                    # Rename suggested_location_id → location_id for consistency
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
                    print(f"     [New location added: '{loc['name']}']")

                    # Add reverse connection from the existing room
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
            print(f"     [Retrofitted {len(rule_updates)} existing rule(s)]")

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
        completed = self.state.get("completed_plot_points", [])
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
        print(f"\n{'═' * 60}")
        print("  MYSTERY SOLVED!")
        print(f"{'═' * 60}")
        print(f"The culprit was: {hidden_truth.get('culprit_name', 'Unknown')}")
        print(f"Motive:          {hidden_truth.get('motive', 'Unknown')}")
        print(f"Method:          {hidden_truth.get('method', 'Unknown')}")
        print(f"\n{hidden_truth.get('hidden_truth_summary', '')}")
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
        # Fast-path: movement
        direction = self._parse_movement(player_input)
        if direction:
            self._try_move(direction)
            return

        print("\n  [Thinking...]")
        context = self._build_context()

        # Step 1: Classify
        classification = classify_action(player_input, context, self.llm)
        action_type = classification.get("action_type", "consistent")

        # Step 2: Handle exceptional actions immediately (DM blocks)
        if action_type == "exceptional":
            reason = classification.get("exception_reason", "You shouldn't do that here.")
            # Deliver block in-world via drama manager
            dm_result = drama_manager_review(player_input, classification, context, self.llm)
            msg = dm_result.get("companion_message") or reason
            print(f"\n  A voice nearby warns you: \"{msg}\"")
            return

        # Step 3: Generate rule for unknown actions
        if action_type == "new_rule_needed":
            print("  [Working out how to do that...]")
            rule_result = generate_rule(player_input, context, self.llm)

            # Check if preconditions for the new rule aren't met
            unmet_msg = rule_result.get("preconditions_not_met_message", "")
            new_objs = rule_result.get("new_objects_needed", [])
            new_locs = rule_result.get("new_locations_needed", [])

            self._apply_rule_result(rule_result)

            if new_objs or new_locs:
                items = [o["name"] for o in new_objs] + [l["name"] for l in new_locs]
                print(f"\n  To do that, you'd need: {', '.join(items)}.")
                if unmet_msg:
                    print(f"  {unmet_msg}")
                return

            if unmet_msg:
                print(f"\n  {unmet_msg}")
                return

            # Re-classify now that the rule exists
            context = self._build_context()
            classification = classify_action(player_input, context, self.llm)

        # Step 4: Drama Manager review
        dm_result = drama_manager_review(player_input, classification, context, self.llm)
        decision = dm_result.get("decision", "approve")

        if decision == "block":
            msg = dm_result.get("companion_message", "You feel something stopping you.")
            print(f"\n  A voice nearby warns you: \"{msg}\"")
            return

        # Step 5: Apply changes and show outcome
        changes = classification.get("proposed_world_changes", [])
        self._apply_world_changes(changes)

        if decision == "plan_repair":
            self._apply_story_patch(dm_result.get("story_patch", []))

        outcome = (dm_result.get("approved_outcome_description")
                   or classification.get("proposed_outcome_description")
                   or "Nothing seems to happen.")
        print(f"\n  {outcome}")

        # Step 6: Check win
        if self._check_win(changes):
            self._show_win()

        self.state.save()

    # ── Main loop ────────────────────────────────────────────────────────────

    def run(self):
        protagonist = self.state.get("protagonist", {})
        goal = self.state.get("goal", "Solve the crime")

        print(f"\n{'═' * 60}")
        print(f"  INTERACTIVE MYSTERY")
        print(f"{'═' * 60}")
        print(f"You are {protagonist.get('Name', 'The Detective')}.")
        print(f"Your goal: {goal}")
        print(f"\nType actions in plain English (aim for ~5 words).")
        print(f"Commands: look | inventory | help | quit")

        self.display_location()

        while not self.state.get("game_complete", False):
            try:
                raw = input("\n> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGame saved. Goodbye!")
                break

            if not raw:
                continue

            cmd = raw.lower()

            if cmd == "quit":
                print("Game saved. Goodbye!")
                break
            elif cmd in ("look", "l"):
                self.display_location()
            elif cmd in ("inventory", "i", "inv"):
                inv = self.state.get("player_state", {}).get("inventory", [])
                print(f"Carrying: {', '.join(inv)}" if inv else "You are carrying nothing.")
            elif cmd == "help":
                print("Actions: look, inventory, go [direction], or describe any action.")
                print("Exits are shown after your location name.")
            else:
                self.process_action(raw)
                self.display_location()

        if self.state.get("game_complete"):
            print("\nThank you for playing!")
