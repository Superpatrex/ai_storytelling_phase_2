# Initialization prompts

# This is the prompt that generates the hidden truth of the crime
INIT_CRIME_PROMPT = """
A crime has been committed. The protagonist ({protagonist_name}, the {protagonist_occupation}) must solve it.
First, establish the hidden truth of the crime. Who did it, how did they do it, and why?
The protagonist does not know this yet, but it is the absolute truth of the story.

To bound the search space, also pre-generate a specific list of potential suspects (including the actual culprit), their apparent motives, their stated alibis (and whether they are lying), and the key locations where the story will take place.
"""

# This is the prompt schema for the initial hidden truth generation including suspects, locations, hidden truths, etc..
INIT_CRIME_SCHEMA = {
     "type": "OBJECT",
     "properties": {
         "culprit_name": {"type": "STRING"},
         "motive": {"type": "STRING"},
         "method": {"type": "STRING"},
         "hidden_truth_summary": {"type": "STRING"},
         "suspects": {
             "type": "ARRAY",
             "items": {
                 "type": "OBJECT",
                 "properties": {
                     "name": {"type": "STRING"},
                     "apparent_motive": {"type": "STRING"},
                     "alibi": {"type": "STRING"},
                     "is_alibi_false": {"type": "BOOLEAN"}
                 }
             }
         },
         "locations": {
             "type": "ARRAY",
             "items": {"type": "STRING"}
         }
     },
     "required": ["culprit_name", "motive", "method", "hidden_truth_summary", "suspects", "locations"]
}

# This is the prompt that generates the protagonist's initial goal based on the hidden truth of the crime and the protagonist's character
INIT_GOAL_PROMPT = """
The protagonist ({protagonist_name}) is trying to solve the following crime:
{crime_summary}

What is the protagonist's immediate, concrete, over-arching goal? E.g., "Find the murder weapon", "Identify the killer", etc.
Also, define a 'dire_fate': what terrible, specific consequence will immediately occur if they fail to achieve this goal?
"""

# This is the prompt schema for the initial goal generation, it returns the goal and the dire fate if the goal is not achieved
INIT_GOAL_SCHEMA = {
     "type": "OBJECT",
     "properties": {
          "goal": {"type": "STRING"},
          "dire_fate": {"type": "STRING"}
     },
     "required": ["goal", "dire_fate"]
}

# Loop Generation Prompts

# This is the prompt for the loop generation it takes in the protagonist, goal, dire fate, hidden truths, suspects, and locations as context.
# This is the main driver of the narrative process and returns three different options that can be used.
LOOP_OPTIONS_PROMPT = """
The protagonist, {protagonist_name}, has the goal: "{goal}".
If they fail, they face this dire fate: "{dire_fate}"
Here is a summary of the true crime (DO NOT reveal this to the protagonist):
{hidden_truth}

Pre-established search space:
Suspects: {suspects}
Key Locations: {locations}

Tension Tracker (Countdown): This is step {step} of {max_steps}. The stakes and suspense must escalate significantly as the steps approach the maximum limit. Time is running out.

Here are the actions the protagonist has taken so far, and their outcomes:
{actions_taken}

The protagonist is currently trying to achieve their goal.
Based on the hidden truth of the crime, generate 3 distinct options for what happens next.
For each option, the protagonist must take a concrete new action. 

CRITICAL INSTRUCTION ON PACING: 
If the current step is close to the max limit (e.g., step is {max_steps} or closely approaching it) AND sufficient clues have been gathered, the options CAN and SHOULD allow the protagonist to finally achieve their goal and directly confront the hidden truth. If an option achieves the ultimate goal, set `goal_achieved` to true, and describe the climax/resolution in the 'problem' field instead of a failure.
If the goal is NOT achieved, they must instead encounter a new obstacle or problem preventing complete success, raising the stakes and increasing suspense.

CRITICAL INSTRUCTION - MINIMIZE DEATHS:
Do NOT rely on constantly killing off characters to generate suspense. Instead, focus on:
- Near-misses and physical danger.
- Discovering terrifying secrets or betrayal.
- Psychological tension and paranoia.
- Sabotage of the investigation (active suspect interference, e.g., the criminal working to hide, remove, or obfuscate clues).
- Time running out (ticking clock elements).

Restrict the protagonist's actions and focus primarily to the pre-established Suspects and Key Locations.
Keep the details ambiguous. Do not reveal the final truth, the actual culprit, or overly obvious critical clues too early. Retain the suspense.
For each option, detail whether the obstacle/clue is a red herring.
"""

# This is the schema for the loop generation prompt, it returns options for the protagonist/characters to take
LOOP_OPTIONS_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "options": {
            "type": "ARRAY",
            "description": "An array of exactly 3 distinct action and obstacle options.",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "action": {"type": "STRING", "description": "The specific action the protagonist takes."},
                    "reasoning": {"type": "STRING", "description": "Why the protagonist thinks this will work."},
                    "problem": {"type": "STRING", "description": "The immediate obstacle preventing success, or the final escalating resolution if goal_achieved is true."},
                    "is_red_herring": {"type": "BOOLEAN", "description": "Whether this obstacle/clue is a red herring."},
                    "new_information": {"type": "STRING", "description": "What new, possibly misleading, info did they learn?"},
                    "goal_achieved": {"type": "BOOLEAN", "description": "True if the protagonist successfully achieved their overarching goal in this step."}
                },
                "required": ["action", "reasoning", "problem", "is_red_herring", "new_information", "goal_achieved"]
            }
        }
    },
    "required": ["options"]
}

# This is the prompt for the loop evaluation, when we receive the three options we want to evaluate them and pick the most suspenseful and fitting option
LOOP_EVALUATOR_PROMPT = """
You are a master storyteller editing a suspenseful crime mystery.
The protagonist, {protagonist_name}, has the goal: "{goal}".
Here is a summary of the true crime:
{hidden_truth}

Here are 3 possible action/obstacle options for what happens next:
{options_json}

Evaluate these 3 options and pick the best one.
The best option is the one that generates the MOST psychological suspense, logically addresses the story state, appropriately resolves the main goal if it's time to conclude, and avoids unnecessary deaths. If an option achieved the goal and the tension indicates it's a fitting end, prefer it. Otherwise, pick the best obstacle.

Return the 0-indexed integer of the best option (0, 1, or 2), and a brief explanation of why it is the best.
"""

# This is the schema for the loop evaluation prompt, 
LOOP_EVALUATOR_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "best_option_index": {"type": "INTEGER", "description": "The 0-indexed integer of the chosen option (0, 1, or 2)."},
        "explanation": {"type": "STRING", "description": "Why this option is the best."}
    },
    "required": ["best_option_index", "explanation"]
}

# Details and Fixer Prompts

# This prompt is for the fixer section of the generation process. It takes the raw story elements and fixes any logical inconsistencies and makes red herrings make sense in context
FIXER_PROMPT = """
You are a master storyteller editing a suspenseful crime mystery.
Here is the raw sequence of events, actions, problems, and information gathered by the protagonist ({protagonist_name}) trying to achieve their goal: "{goal}".
The true facts of the crime are:
{hidden_truth}

Raw Story Elements:
{story_elements}

Your task is to review these plot points, smooth out any logical inconsistencies, ensure the red herrings make sense in the context of the hidden truth, and assemble them into a cohesive, highly suspenseful narrative outline. Fix any plot holes.

CRITICAL CONSTRAINTS:
1. Prune Abandoned Threads: Identify any characters, locations, or clues that were introduced early but never used again. Either weave them meaningfully into the resolution or COMPLETELY REMOVE them from the final outline.
2. State Continuity: Pay strict attention to the state of physical evidence and locations. If a piece of evidence is described as destroyed, lost, or consumed in an earlier step, it CANNOT be used or found by a character later in the story. Ensure absolute chronological logic.
"""

# This is the schema for the fixer section of the generation process. It returns a fixed outline and the specific plot holes that were fixed
FIXER_SCHEMA = {
     "type": "OBJECT",
     "properties": {
          "fixed_outline": {"type": "STRING", "description": "The logically consistent outline of the story."},
          "plot_holes_fixed": {"type": "ARRAY", "items": {"type": "STRING"}, "description": "A list of inconsistencies you resolved."}
     },
     "required": ["fixed_outline", "plot_holes_fixed"]
}

# This prompt is for the details section. It creates a fluent, final story based on the fixed outline
DETAILS_PROMPT = """
You are a master author. Based on the following meticulously planned and perfectly logical story outline, write a fluent, highly engaging, and suspenseful final story.
Do not just list the events. Write it as prose. Show, don't tell. Build the tension culminating in the resolution.

Outline:
{fixed_outline}
"""
