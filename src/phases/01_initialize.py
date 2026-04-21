import os
import json
from src.config import BASE_DIR
from src.prompts import (
    INIT_CRIME_PROMPT, INIT_CRIME_SCHEMA,
    INIT_GOAL_PROMPT, INIT_GOAL_SCHEMA
)

# Method that runs the first phase of the story generation process
def execute(controller):
    # Load Setting, Protagonist, and Characters (basically initialization prompts)
    print("  -> Loading Pre-generated Context (Setting, Characters)...")
    data_path = os.path.join(BASE_DIR, "data", "initialization_prompts.json")
    
    with open(data_path, "r") as f:
         story_context = json.load(f)
         
    # Get the settings information and the time information
    setting_info = story_context.get("Setting", "Unknown Setting")
    time_info = story_context.get("Time", "Modern Day")
    
    # Get the protagonist information as well
    protagonist_data = story_context.get("Protagonist", {})
    controller.state.update("protagonist", protagonist_data)
    
    # Also save the characters information so that we can use that
    characters = story_context.get("Characters", [])
    controller.state.update("characters", characters)
    
    # Save the settings
    controller.state.update("setting", {"location": setting_info, "time": time_info})
    
    print(f"     Protagonist loaded: {protagonist_data.get('Name', 'Unknown')}")
    print(f"     {len(characters)} other characters loaded.")

    # Generate the hidden truth narrative
    print("  -> Generating Hidden Truth (The Crime)...")
    
    # Get all the character names so that we can select a culprit
    character_names = ", ".join([c.get("Name", "") for c in characters])
    
    # Get a crime report for the protagonist
    crime_prompt = INIT_CRIME_PROMPT.format(
        protagonist_name=protagonist_data.get("Name", "The Detective"),
        protagonist_occupation=protagonist_data.get("Role", "Investigator")
    )
    
    # Add the environment to the crime prompt as well for the hidden truths
    crime_prompt += f"\n\nSETTING:\nLocation: {setting_info}\nTime: {time_info}\n"
    crime_prompt += f"\nAVAILABLE SUSPECTS TO CHOOSE FROM:\n{character_names}\n"
    crime_prompt += "Ensure the culprit comes from this list of suspects."

    # Get the crime data using the crime prompt using the crime schema
    crime_data = controller.llm.generate_json(
        prompt=crime_prompt,
        schema=INIT_CRIME_SCHEMA
    )

    # Update the controller with the hidden truths
    if "hidden_truth_summary" in crime_data:
        controller.state.update("hidden_truth", crime_data)
        print("     Crime initialized.")
    else:
        print("     Failed to initialize crime.")

    # Generate an initial goal and dire fate for the story
    print("  -> Defining Protagonist's Immediate Goal...")

    # Create our initial prompt using the protagonist and the hidden truths
    goal_prompt = INIT_GOAL_PROMPT.format(
        protagonist_name=protagonist_data.get("Name", "The Detective"),
        crime_summary=crime_data.get("hidden_truth_summary", "A mysterious unsolved crime.")
    )

    # Get the goal and fire fate from the LLM using the prompt and the schema
    goal_data = controller.llm.generate_json(
        prompt=goal_prompt,
        schema=INIT_GOAL_SCHEMA
    )

    # Make sure we got a goal and a dire fate and add it to our controller
    if "goal" in goal_data and "dire_fate" in goal_data:
        goal = goal_data.get("goal")
        dire_fate = goal_data.get("dire_fate")
        controller.state.update("goal", goal)
        controller.state.update("dire_fate", dire_fate)
        print(f"     Goal set: {goal}")
        print(f"     Dire Fate set: {dire_fate}")
        
        # Snapshot saving removed: StateManager already auto-saves to current_state.json on update.
    else:
         print("     Failed to set goal.")
