import json
from src.prompts import (
    LOOP_OPTIONS_PROMPT, LOOP_OPTIONS_SCHEMA,
    LOOP_EVALUATOR_PROMPT, LOOP_EVALUATOR_SCHEMA
)
from src.config import MAX_LOOP_PROCESSES, MAX_RED_HERRINGS

# Method that runs the second phase of the story generation process
def execute(controller):
    print(f"  -> Starting Suspense Loop (Max processes: {MAX_LOOP_PROCESSES})...")
    
    # Load in story variables from the initialization prompt and initialization phase
    protagonist_name = controller.state.get("protagonist", {}).get("name", "The Detective")
    goal = controller.state.get("goal", "Solve the crime")
    dire_fate = controller.state.get("dire_fate", "Something terrible will happen.")
    hidden_truth_data = controller.state.get("hidden_truth", {})
    hidden_truth = hidden_truth_data.get("hidden_truth_summary", "")
    suspects = hidden_truth_data.get("suspects", [])
    locations = hidden_truth_data.get("locations", [])
    
    # Load in the actions taken and the story elements
    actions_taken_history = controller.state.get("actions_taken", [])
    story_elements = controller.state.get("story_elements", [])
    
    # Load in the number of red herrings used so far
    red_herrings_used = controller.state.get("red_herrings_used", 0)

     
    # For each step in the look process
    for step in range(1, MAX_LOOP_PROCESSES + 1):
        print(f"     --- Step {step}/{MAX_LOOP_PROCESSES} ---")

        # Update what step we are currently at
        controller.state.update("loop_step", step)
        
        history_str = ""
     
        for i, past in enumerate(actions_taken_history):
             history_str += f"{i+1}. Tried: {past.get('action')}. Result: {past.get('outcome')}\n"
          
        suspects_str = ", ".join([f"{s.get('name')} (Motive: {s.get('apparent_motive')}, Alibi: {s.get('alibi')})" for s in suspects]) if suspects else "Unknown"
        locations_str = ", ".join(locations) if locations else "Unknown"

        # Create an options prompt with all the relevant information for the current state of the story
        options_prompt = LOOP_OPTIONS_PROMPT.format(
             protagonist_name=protagonist_name,
             goal=goal,
             dire_fate=dire_fate,
             hidden_truth=hidden_truth,
             suspects=suspects_str,
             locations=locations_str,
             step=step,
             max_steps=MAX_LOOP_PROCESSES,
             actions_taken=history_str if history_str else "None yet."
        )
        
        # Alert the user if they have reached the maximum number of red herrings
        sys_instruction_options = ""
        if red_herrings_used >= MAX_RED_HERRINGS:
             sys_instruction_options = "IMPORTANT: You have reached the maximum number of red herrings. Ensure that NONE of the 3 generated options include a red herring obstacle."
             
        print("         Generating 3 options...")

        # Get the 3 options for what happens next in the story based on the prompt and the schema
        options_data = controller.llm.generate_json(
             prompt=options_prompt, 
             schema=LOOP_OPTIONS_SCHEMA,
             system_instruction=sys_instruction_options
        )
        options_list = options_data.get("options", [])
        
        # If we have not generated the 3 options then leave
        if not options_list or len(options_list) != 3:
             print("         Failed to generate exactly 3 options. Skipping step.")
             continue

        options_json_str = json.dumps(options_list, indent=2)

        # Create a prompt for the evaluation of the 3 optons
        evaluator_prompt = LOOP_EVALUATOR_PROMPT.format(
             protagonist_name=protagonist_name,
             goal=goal,
             hidden_truth=hidden_truth,
             options_json=options_json_str
        )
        
        print("         Evaluating options to pick the best one...")

        # Get the best option and using the prompt and schema for the evaluation
        evaluation_data = controller.llm.generate_json(
             prompt=evaluator_prompt, 
             schema=LOOP_EVALUATOR_SCHEMA
        )
        
        best_index = evaluation_data.get("best_option_index", 0)
        explanation = evaluation_data.get("explanation", "Default fallback.")
        
        if best_index not in [0, 1, 2]:
             best_index = 0
             
        print(f"         Selected Option {best_index + 1}: {explanation}")
        
        # Get the defaults of the best prompt
        best_option = options_list[best_index]
        current_action = best_option.get("action", "")
        reasoning = best_option.get("reasoning", "")
        problem = best_option.get("problem", "A mysterious setback occurred.")
        is_red_herring = best_option.get("is_red_herring", False)
        new_info = best_option.get("new_information", "")
        goal_achieved = best_option.get("goal_achieved", False)
        
        # If we have a red herring then set the red herring flag if we are still allowed to use it
        if is_red_herring and red_herrings_used >= MAX_RED_HERRINGS:
             is_red_herring = False
             
        # If we have a red herring then increase the count and update the controller
        if is_red_herring and not goal_achieved:
             red_herrings_used += 1
             controller.state.update("red_herrings_used", red_herrings_used)
             
        # Set the outcome of this action
        if goal_achieved:
             outcome = f"Goal Achieved! Resolution: {problem} | Discovered: {new_info}"
        else:
             outcome = f"Problem: {problem} | Discovered: {new_info} | Was Red Herring: {is_red_herring}"
        
        # Add this action to the list of actions that has been taken
        actions_taken_history.append({
             "action": current_action,
             "outcome": outcome
        })

        # Update the actions taken and the story elements in the controller state
        controller.state.update("actions_taken", actions_taken_history)
        
        # Add the action and the obstacle as story elements to the story along with the description and reasoning
        story_elements.append({
             "type": "action",
             "description": current_action,
             "reasoning": reasoning
        })

        # Add the obstacles as a story elements as well with the description, whether it was a red herring, and new information learned
        story_elements.append({
             "type": "resolution" if goal_achieved else "obstacle",
             "description": problem,
             "is_red_herring": is_red_herring if not goal_achieved else False,
             "new_info": new_info
        })

        # Update the story elements in the controller state
        controller.state.update("story_elements", story_elements)
        
        if goal_achieved:
             print(f"  -> Goal achieved at step {step}! Ending loop early.")
             break

    print(f"  -> Loop finished after {step} processes.")
