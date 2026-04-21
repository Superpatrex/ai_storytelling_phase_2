import json
from src.prompts import FIXER_PROMPT, FIXER_SCHEMA

# Method that runs the first part of the third phase of the story generation process
def execute(controller):
    print("  -> Starting The Fixer Phase...")
    
    # Load the protagonist, goal, hidden truth, and story elements from the controller
    protagonist_name = controller.state.get("protagonist", {}).get("name", "The Detective")
    goal = controller.state.get("goal", "Solve the crime")
    hidden_truth = controller.state.get("hidden_truth", {}).get("hidden_truth_summary", "")
    story_elements = controller.state.get("story_elements", [])
    
    # If there are no story elements then just leave
    if not story_elements:
          print("     No story elements found. Skipping fixer phase.")
          return

    elements_str = json.dumps(story_elements, indent=2)

    # Format the fixer prompt with the protagonist, goal, hidden truths, and the story elements that have been generated
    fixer_prompt = FIXER_PROMPT.format(
         protagonist_name=protagonist_name,
         goal=goal,
         hidden_truth=hidden_truth,
         story_elements=elements_str
    )
    
    print("     Reviewing and fixing story outline...")

    # Get the fixed outline by passing in the prompt and the schema
    fixer_data = controller.llm.generate_json(
         prompt=fixer_prompt, 
         schema=FIXER_SCHEMA
    )

    # Get the fixed outline and the plot holes from our fixed data
    fixed_outline = fixer_data.get("fixed_outline", "")
    plot_holes_fixed = fixer_data.get("plot_holes_fixed", [])

    # If they exist then update the controller with the fixed outline
    if fixed_outline:
        controller.state.update("fixed_outline", fixed_outline)
        controller.state.update("plot_holes_fixed", plot_holes_fixed)
        
        print("     Story outline fixed and saved.")
        print(f"     Fixed {len(plot_holes_fixed)} plot holes.")
    else:
        print("     Failed to generate fixed outline.")
