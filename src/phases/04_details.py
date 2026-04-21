import os
from src.prompts import DETAILS_PROMPT
from src.config import OUTPUT_DIR


def execute(controller):
   
    print("  -> Starting Final Details Phase...")
    
    # Get the fixed outline from the fixer phase (the first section of the third phase)
    fixed_outline = controller.state.get("fixed_outline", "")
    
    # If we don't have a fixed outline just leave
    if not fixed_outline:
        print("     No fixed outline found. Exiting details phase.")
        return

    # format the details prompt and get a prompt for the detail phase
    details_prompt = DETAILS_PROMPT.format(fixed_outline=fixed_outline)
    
    print("     Generating final story prose... (This may take a moment)")
    
    # Generate a final story using the details prompt
    final_story = controller.llm.generate_text(
        prompt=details_prompt, 
        temperature=0.8
    )

    # If we successfully generated a final story then...
    if final_story:

        # Make a file
        output_filename = "final_story.txt"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
         
        # Write the final story into that text file
        try:
            with open(output_path, "w") as f:
                f.write(final_story)
            print(f"\n   >>> Success! Final story saved to: {output_path} <<<")
        except Exception as e:
            print(f"Error saving final story: {e}")

        # Update the controller
        controller.state.update("final_story", final_story)
    else:
        print("     Failed to generate final story.")
