import json
from src.prompts import WORLD_BUILDER_PROMPT, WORLD_BUILDER_SCHEMA


# Method to execute the world graph builder phase of the story generation process
def execute(controller):
    print("  -> Starting World Graph Builder Phase...")

    # Get the state data needed to build the world map
    setting = controller.state.get("setting", {})
    hidden_truth = controller.state.get("hidden_truth", {})
    plot_points = controller.state.get("annotated_plot_points", [])

    if not plot_points:
        print("     No plot points found. Skipping world builder.")
        return

    # Extract key locations and format the setting string for the prompt
    key_locations = hidden_truth.get("locations", [])
    setting_str = f"{setting.get('location', 'Unknown')} ({setting.get('time', 'Modern Day')})"

    # Extract location hints from plot points for the builder
    location_hints = [
        {"plot_point_id": pp["id"], "location_hint": pp.get("location_hint", "Unknown")}
        for pp in plot_points
    ]

    # Create the prompt for the world graph builder
    prompt = WORLD_BUILDER_PROMPT.format(
        setting=setting_str,
        key_locations=json.dumps(key_locations, indent=2),
        location_hints=json.dumps(location_hints, indent=2)
    )

    print("     Building navigable world graph...")

    # Generate the world graph with the LLM
    data = controller.llm.generate_json(
        prompt=prompt,
        schema=WORLD_BUILDER_SCHEMA
    )

    rooms = data.get("rooms", [])
    starting_room_id = data.get("starting_room_id", "")

    if not rooms:
        print("     Failed to generate world graph.")
        return

    # Update the state with the generated world graph and starting room
    world_graph = {
        "rooms": rooms,
        "starting_room_id": starting_room_id
    }
    controller.state.update("world_graph", world_graph)

    print(f"     World built: {len(rooms)} rooms, starting at '{starting_room_id}'.")
    for room in rooms:
        exits = [c["direction"] for c in room.get("connections", [])]
        print(f"       {room['name']} → exits: {', '.join(exits) if exits else 'none'}")
