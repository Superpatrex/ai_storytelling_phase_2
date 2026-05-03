import json
from src.prompts import OBJECT_NPC_PLACER_PROMPT, OBJECT_NPC_PLACER_SCHEMA


# Method to execute the object and NPC placer phase of the story generation process
def execute(controller):
    print("  -> Starting Object & NPC Placer Phase...")

    # Get the state data needed to place objects and NPCs in the world
    setting = controller.state.get("setting", {})
    characters = controller.state.get("characters", [])
    plot_points = controller.state.get("annotated_plot_points", [])
    world_graph = controller.state.get("world_graph", {"rooms": []})
    protected_variables = controller.state.get("protected_variables", [])

    if not plot_points or not world_graph.get("rooms"):
        print("     Missing plot points or world graph. Skipping placer phase.")
        return

    setting_str = f"{setting.get('location', 'Unknown')} ({setting.get('time', 'Modern Day')})"

    # Pass only room ids and names to keep prompt size manageable
    rooms_summary = [
        {"id": r["id"], "name": r["name"]}
        for r in world_graph["rooms"]
    ]

    # Create the prompt for the object and NPC placer with relevant context
    prompt = OBJECT_NPC_PLACER_PROMPT.format(
        setting=setting_str,
        characters=json.dumps([
            {"Name": c.get("Name", ""), "Role": c.get("Role", ""), "Reason": c.get("Reason", "")}
            for c in characters
        ], indent=2),
        plot_points=json.dumps([
            {"id": pp["id"], "description": pp["description"],
             "location_hint": pp.get("location_hint", ""),
             "characters_involved": pp.get("characters_involved", [])}
            for pp in plot_points
        ], indent=2),
        rooms=json.dumps(rooms_summary, indent=2),
        protected_variables=json.dumps(protected_variables, indent=2)
    )

    print("     Placing objects and NPCs in the world...")

    # Generate object and NPC placements with the LLM
    data = controller.llm.generate_json(
        prompt=prompt,
        schema=OBJECT_NPC_PLACER_SCHEMA
    )

    objects = data.get("objects", [])
    npcs = data.get("npcs", [])

    if not npcs:
        print("     Failed to place NPCs.")
        return

    # Initialize runtime state fields on objects
    for obj in objects:
        obj.setdefault("visible", True)
        obj.setdefault("in_inventory", False)
        obj.setdefault("state", {})

    # Initialize runtime state fields on NPCs
    for npc in npcs:
        npc.setdefault("state", {"alive": True, "interrogated": False})

    # Update the state with the placed objects and NPCs
    controller.state.update("objects", objects)
    controller.state.update("npcs", npcs)

    print(f"     Placed {len(objects)} objects and {len(npcs)} NPCs.")
