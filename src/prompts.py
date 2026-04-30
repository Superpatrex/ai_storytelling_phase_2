# ─────────────────────────────────────────────────────────────────────────────
# PHASE 1: INITIALIZATION PROMPTS
# ─────────────────────────────────────────────────────────────────────────────

INIT_CRIME_PROMPT = """
A crime has been committed. The protagonist ({protagonist_name}, the {protagonist_occupation}) must solve it.
First, establish the hidden truth of the crime. Who did it, how did they do it, and why?
The protagonist does not know this yet, but it is the absolute truth of the story.

To bound the search space, also pre-generate a specific list of potential suspects (including the actual culprit), their apparent motives, their stated alibis (and whether they are lying), and the key locations where the story will take place.
"""

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

INIT_GOAL_PROMPT = """
The protagonist ({protagonist_name}) is trying to solve the following crime:
{crime_summary}

What is the protagonist's immediate, concrete, over-arching goal? E.g., "Find the murder weapon", "Identify the killer", etc.
Also, define a 'dire_fate': what terrible, specific consequence will immediately occur if they fail to achieve this goal?
"""

INIT_GOAL_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "goal": {"type": "STRING"},
        "dire_fate": {"type": "STRING"}
    },
    "required": ["goal", "dire_fate"]
}

# ─────────────────────────────────────────────────────────────────────────────
# PHASE 2: NARRATIVE LOOP PROMPTS
# ─────────────────────────────────────────────────────────────────────────────

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
- Sabotage of the investigation (active suspect interference).
- Time running out (ticking clock elements).

Restrict the protagonist's actions and focus primarily to the pre-established Suspects and Key Locations.
Keep the details ambiguous. Do not reveal the final truth, the actual culprit, or overly obvious critical clues too early. Retain the suspense.
For each option, detail whether the obstacle/clue is a red herring.
"""

LOOP_OPTIONS_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "options": {
            "type": "ARRAY",
            "description": "An array of exactly 3 distinct action and obstacle options.",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "action": {"type": "STRING"},
                    "reasoning": {"type": "STRING"},
                    "problem": {"type": "STRING"},
                    "is_red_herring": {"type": "BOOLEAN"},
                    "new_information": {"type": "STRING"},
                    "goal_achieved": {"type": "BOOLEAN"}
                },
                "required": ["action", "reasoning", "problem", "is_red_herring", "new_information", "goal_achieved"]
            }
        }
    },
    "required": ["options"]
}

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

LOOP_EVALUATOR_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "best_option_index": {"type": "INTEGER"},
        "explanation": {"type": "STRING"}
    },
    "required": ["best_option_index", "explanation"]
}

# ─────────────────────────────────────────────────────────────────────────────
# PHASE 3a: FIXER — Outputs structured plot points (not free text)
# ─────────────────────────────────────────────────────────────────────────────

FIXER_PROMPT = """
You are a master storyteller editing a suspenseful crime mystery.
Protagonist: {protagonist_name} | Goal: "{goal}"
True crime facts (do NOT reveal to protagonist): {hidden_truth}

Raw story elements to fix:
{story_elements}

Your task:
1. Fix all logical inconsistencies and plot holes.
2. Ensure red herrings make sense given the hidden truth.
3. Remove or integrate any abandoned characters/locations/threads.
4. Enforce strict state continuity — if evidence is destroyed or lost early, it cannot reappear.
5. Output the corrected story as an ordered list of structured plot points.

For each plot point assign:
- id: unique string like "pp_001", "pp_002", etc.
- sequence: integer order (1, 2, 3...)
- description: a clear, concise description of the event (1-3 sentences)
- type: one of "event" (something happens), "clue" (evidence found/discovered), "obstacle" (something blocks progress), "resolution" (final confrontation or solution)
- is_red_herring: true if this clue/event is intentionally misleading
- location_hint: the name of the location where this takes place
- characters_involved: list of character names directly involved

The FINAL plot point must be of type "resolution".
"""

FIXER_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "plot_points": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "id": {"type": "STRING"},
                    "sequence": {"type": "INTEGER"},
                    "description": {"type": "STRING"},
                    "type": {"type": "STRING"},
                    "is_red_herring": {"type": "BOOLEAN"},
                    "location_hint": {"type": "STRING"},
                    "characters_involved": {"type": "ARRAY", "items": {"type": "STRING"}}
                },
                "required": ["id", "sequence", "description", "type", "is_red_herring", "location_hint", "characters_involved"]
            }
        },
        "plot_holes_fixed": {
            "type": "ARRAY",
            "items": {"type": "STRING"}
        }
    },
    "required": ["plot_points", "plot_holes_fixed"]
}

# ─────────────────────────────────────────────────────────────────────────────
# PHASE 3b: PLOT POINT ANNOTATOR — Adds preconditions and effects
# ─────────────────────────────────────────────────────────────────────────────

PLOT_POINT_ANNOTATOR_PROMPT = """
You are a game designer converting a mystery story outline into an interactive game structure.

Story context:
- Protagonist: {protagonist_name}
- Goal: {goal}
- Setting: {setting}
- Characters: {characters}

Structured plot points to annotate:
{plot_points}

For each plot point, define:

PRECONDITIONS — what must be true for this plot point to be reachable/triggerable:
Use these types:
  - "player_location": player must be at a specific location (value = location_hint from plot point)
  - "has_item": player must have a specific item in inventory (value = item id/name)
  - "knows_fact": player must have learned a specific piece of information (value = fact string)
  - "npc_present": a specific NPC must be in the same location (value = npc name)
  - "plot_point_completed": another plot point must have been completed first (value = plot point id)
  - "object_state": an object must be in a specific state (value = "object_id:state_value")

EFFECTS — what changes in the world when this plot point is triggered:
Use these types:
  - "reveal_object": makes a hidden object discoverable (target_id = object id, value = location_id)
  - "gain_knowledge": player learns a fact (target_id = "player", value = fact string)
  - "change_object_state": changes object state (target_id = object id, value = new state)
  - "change_npc_state": changes NPC state (target_id = npc id, value = new state)
  - "complete_plot_point": marks this plot point done (target_id = this plot point id, value = "done")
  - "unlock_location": makes a room accessible (target_id = room id, value = "accessible")

IS_PROTECTED — true if this plot point involves evidence or an NPC that MUST remain intact for the mystery to be solvable. Mark as protected if destroying this clue/character would make it impossible to ever solve the crime.

Also output a list of PROTECTED_VARIABLES — state conditions that must remain true for the mystery to remain solvable. These are the "causal spans" the drama manager will protect.
"""

PLOT_POINT_ANNOTATOR_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "annotated_plot_points": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "id": {"type": "STRING"},
                    "preconditions": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "description": {"type": "STRING"},
                                "type": {"type": "STRING"},
                                "value": {"type": "STRING"}
                            },
                            "required": ["description", "type", "value"]
                        }
                    },
                    "effects": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "description": {"type": "STRING"},
                                "type": {"type": "STRING"},
                                "target_id": {"type": "STRING"},
                                "value": {"type": "STRING"}
                            },
                            "required": ["description", "type", "target_id", "value"]
                        }
                    },
                    "is_protected": {"type": "BOOLEAN"}
                },
                "required": ["id", "preconditions", "effects", "is_protected"]
            }
        },
        "protected_variables": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "description": {"type": "STRING"},
                    "object_or_npc_id": {"type": "STRING"},
                    "required_condition": {"type": "STRING"},
                    "needed_for_plot_point_id": {"type": "STRING"}
                },
                "required": ["description", "object_or_npc_id", "required_condition", "needed_for_plot_point_id"]
            }
        }
    },
    "required": ["annotated_plot_points", "protected_variables"]
}

# ─────────────────────────────────────────────────────────────────────────────
# PHASE 3c: DEPENDENCY ANALYZER — Causal ordering between plot points
# ─────────────────────────────────────────────────────────────────────────────

DEPENDENCY_ANALYZER_PROMPT = """
You are analyzing a mystery story's plot structure to build a causal dependency graph.

Annotated plot points:
{annotated_plot_points}

For each plot point, determine:

DEPENDS_ON — list the IDs of plot points that MUST be completed before this one can occur.
Base this on the preconditions: if a precondition requires "plot_point_completed", that is a dependency.
Also use narrative logic — if a clue discovered in pp_002 is required to know where to look in pp_005, then pp_005 depends on pp_002.

CAUSAL_SPANS — conditions that must remain continuously true across a range of plot points.
For example: "the victim's diary must exist" must remain true from pp_001 until pp_007 when it is finally read.
If a condition is violated in the middle, later plot points that depend on it cannot execute.

Be conservative — only mark dependencies that are logically required. Leave optional ordering flexible so the player has agency.
"""

DEPENDENCY_ANALYZER_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "dependencies": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "plot_point_id": {"type": "STRING"},
                    "depends_on": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "causal_spans": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "condition_description": {"type": "STRING"},
                                "must_remain_true_from_id": {"type": "STRING"},
                                "must_remain_true_until_id": {"type": "STRING"}
                            },
                            "required": ["condition_description", "must_remain_true_from_id", "must_remain_true_until_id"]
                        }
                    }
                },
                "required": ["plot_point_id", "depends_on", "causal_spans"]
            }
        }
    },
    "required": ["dependencies"]
}

# ─────────────────────────────────────────────────────────────────────────────
# PHASE 3d: WORLD GRAPH BUILDER — Navigable location graph
# ─────────────────────────────────────────────────────────────────────────────

WORLD_BUILDER_PROMPT = """
You are building the navigable world map for a mystery text game.

Setting: {setting}
Key story locations (from story generator): {key_locations}
Plot point location hints: {location_hints}

Build a connected graph of rooms. Rules:
1. Every location referenced in the plot points must be a room.
2. Add intermediate rooms if adjacent plot-point locations would violate commonsense (e.g., a bedroom and a restaurant should not be directly connected without a hallway/lobby between them).
3. All rooms must be reachable from a starting room (the main entrance/lobby).
4. Keep the world minimal — only rooms needed by the story plus necessary connectors.
5. Directions must use compass directions (north, south, east, west) or logical directions (up, down, inside, outside).
6. Each connection must be bidirectional — if room A connects north to room B, room B connects south to room A.

For each room provide:
- id: snake_case unique identifier (e.g., "grand_lobby", "east_wing_corridor")
- name: display name (e.g., "Grand Lobby")
- description: 2-3 sentence atmospheric description appropriate for the mystery setting
- connections: list of exits with direction, destination room id, and brief label
- story_event_ids: list of plot point ids that take place in this room (from location_hints)
"""

WORLD_BUILDER_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "rooms": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "id": {"type": "STRING"},
                    "name": {"type": "STRING"},
                    "description": {"type": "STRING"},
                    "connections": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "direction": {"type": "STRING"},
                                "to_room_id": {"type": "STRING"},
                                "label": {"type": "STRING"}
                            },
                            "required": ["direction", "to_room_id", "label"]
                        }
                    },
                    "story_event_ids": {"type": "ARRAY", "items": {"type": "STRING"}}
                },
                "required": ["id", "name", "description", "connections", "story_event_ids"]
            }
        },
        "starting_room_id": {"type": "STRING"}
    },
    "required": ["rooms", "starting_room_id"]
}

# ─────────────────────────────────────────────────────────────────────────────
# PHASE 3e: OBJECT & NPC PLACER — Assigns objects/NPCs to rooms
# ─────────────────────────────────────────────────────────────────────────────

OBJECT_NPC_PLACER_PROMPT = """
You are populating a mystery game world with objects and characters.

Story context:
- Setting: {setting}
- Characters: {characters}
- Plot points: {plot_points}
- World rooms: {rooms}
- Protected variables (must not be destroyed): {protected_variables}

OBJECTS: Identify all physical objects referenced in the plot points that the player can interact with.
For each object:
- Give it a unique snake_case id (e.g., "silver_letter_opener")
- Place it in the most logical starting room
- Mark is_protected=true if it appears in the protected_variables list
- Mark can_be_picked_up=true if it is something a person could carry
- Link it to the plot point it is first involved in

NPCS: Place each character from the story in their most logical starting location.
- Give each NPC a snake_case id derived from their name (e.g., "dr_marcus_vane")
- Place them in a room consistent with their role and the early story
- Mark can_move=true for NPCs who move around during the story
- Link them to all plot point ids they are involved in

Only create objects that are explicitly mentioned or clearly implied by the plot points.
Do not invent objects that have no story relevance.
"""

OBJECT_NPC_PLACER_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "objects": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "id": {"type": "STRING"},
                    "name": {"type": "STRING"},
                    "description": {"type": "STRING"},
                    "location_id": {"type": "STRING"},
                    "can_be_picked_up": {"type": "BOOLEAN"},
                    "linked_plot_point_id": {"type": "STRING"},
                    "is_protected": {"type": "BOOLEAN"}
                },
                "required": ["id", "name", "description", "location_id", "can_be_picked_up", "linked_plot_point_id", "is_protected"]
            }
        },
        "npcs": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "id": {"type": "STRING"},
                    "name": {"type": "STRING"},
                    "current_location_id": {"type": "STRING"},
                    "can_move": {"type": "BOOLEAN"},
                    "linked_plot_point_ids": {"type": "ARRAY", "items": {"type": "STRING"}}
                },
                "required": ["id", "name", "current_location_id", "can_move", "linked_plot_point_ids"]
            }
        }
    },
    "required": ["objects", "npcs"]
}

# ─────────────────────────────────────────────────────────────────────────────
# RUNTIME: ACTION CLASSIFIER
# ─────────────────────────────────────────────────────────────────────────────

ACTION_CLASSIFIER_PROMPT = """
You are the game engine for an interactive mystery. Classify the player's action and propose its outcome.

PLAYER: {protagonist_name}
GOAL: {goal}

CURRENT WORLD STATE:
Location: {current_room_name} — {current_room_description}
Exits: {exits}
Objects here: {room_objects}
People here: {room_npcs}
Player inventory: {inventory}
Player knowledge: {knowledge}

PENDING PLOT POINTS (not yet completed):
{pending_plot_points}

PROTECTED VARIABLES (must not be violated):
{protected_variables}

EXISTING ACTION RULES:
{action_rules}

PLAYER INPUT: "{player_input}"

Classify this action as one of:
- "constituent": directly triggers a pending plot point (the player is doing exactly what the story intended)
- "consistent": doesn't trigger a plot point but is commonsense-valid and doesn't harm the story (exploring, examining objects, asking questions not tied to a plot point)
- "exceptional": would permanently violate a protected variable (destroy a critical clue, kill a critical witness, do something that makes the mystery unsolvable)
- "new_rule_needed": the action is novel and commonsense-valid but no existing rule covers it; requires rule generation

COMMONSENSE BOUNDS — classify as exceptional if the action involves:
- Resurrection of the dead
- Time travel or reality-altering powers
- Technology that doesn't exist in the setting
- Aliens, magic (unless setting explicitly supports it)
- Permanent destruction of a protected object/NPC

For "constituent" actions, identify which plot point id is triggered (triggered_plot_point_id).
Propose the world state changes and a narrative outcome description.

For "exceptional" actions, provide a brief exception_reason explaining why it's blocked (this will be reworded by the drama manager for in-world delivery).

Proposed world changes use these types: pick_up_item, drop_item, reveal_object, gain_knowledge, change_object_state, change_npc_state, complete_plot_point, move_to_room.
"""

ACTION_CLASSIFIER_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "action_type": {"type": "STRING"},
        "triggered_plot_point_id": {"type": "STRING"},
        "is_commonsense_valid": {"type": "BOOLEAN"},
        "proposed_world_changes": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "type": {"type": "STRING"},
                    "target_id": {"type": "STRING"},
                    "new_value": {"type": "STRING"},
                    "description": {"type": "STRING"}
                },
                "required": ["type", "target_id", "new_value", "description"]
            }
        },
        "proposed_outcome_description": {"type": "STRING"},
        "exception_reason": {"type": "STRING"}
    },
    "required": ["action_type", "triggered_plot_point_id", "is_commonsense_valid",
                 "proposed_world_changes", "proposed_outcome_description", "exception_reason"]
}

# ─────────────────────────────────────────────────────────────────────────────
# RUNTIME: RULE GENERATOR
# ─────────────────────────────────────────────────────────────────────────────

RULE_GENERATOR_PROMPT = """
You are the rule engine for a mystery text game. The player wants to perform an action that has no existing rule.

PLAYER INPUT: "{player_input}"
CURRENT LOCATION: {current_room_name}
PLAYER INVENTORY: {inventory}
SETTING: {setting}
EXISTING RULES: {action_rules}

Generate a new game rule for this action. The rule must:
1. Be commonsense-valid within the setting
2. Have clear preconditions the player must meet
3. Describe what effects the action has on the world

If the action requires objects or locations that don't currently exist in the game world, specify them in new_objects_needed or new_locations_needed. These will be added to the world (the player will then need to find/create them — this is the cascading precondition mechanic).

If adding new objects affects how any existing rules work (e.g., a new "heavy ladder" object means "pick up" should check weight), list those existing rules in existing_rules_to_update with a description of the update needed.

Precondition types: player_location, has_item, knows_fact, npc_present, object_state
"""

RULE_GENERATOR_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "new_rule": {
            "type": "OBJECT",
            "properties": {
                "id": {"type": "STRING"},
                "verb": {"type": "STRING"},
                "description": {"type": "STRING"},
                "preconditions": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "description": {"type": "STRING"},
                            "type": {"type": "STRING"},
                            "value": {"type": "STRING"}
                        },
                        "required": ["description", "type", "value"]
                    }
                },
                "effects_description": {"type": "STRING"}
            },
            "required": ["id", "verb", "description", "preconditions", "effects_description"]
        },
        "new_objects_needed": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "id": {"type": "STRING"},
                    "name": {"type": "STRING"},
                    "description": {"type": "STRING"},
                    "suggested_location_id": {"type": "STRING"},
                    "can_be_picked_up": {"type": "BOOLEAN"}
                },
                "required": ["id", "name", "description", "suggested_location_id", "can_be_picked_up"]
            }
        },
        "new_locations_needed": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "id": {"type": "STRING"},
                    "name": {"type": "STRING"},
                    "description": {"type": "STRING"},
                    "connect_to_room_id": {"type": "STRING"},
                    "direction_from_existing": {"type": "STRING"}
                },
                "required": ["id", "name", "description", "connect_to_room_id", "direction_from_existing"]
            }
        },
        "existing_rules_to_update": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "rule_id": {"type": "STRING"},
                    "update_description": {"type": "STRING"}
                },
                "required": ["rule_id", "update_description"]
            }
        },
        "preconditions_not_met_message": {"type": "STRING"}
    },
    "required": ["new_rule", "new_objects_needed", "new_locations_needed",
                 "existing_rules_to_update", "preconditions_not_met_message"]
}

# ─────────────────────────────────────────────────────────────────────────────
# RUNTIME: DRAMA MANAGER
# ─────────────────────────────────────────────────────────────────────────────

DRAMA_MANAGER_PROMPT = """
You are the Drama Manager for an interactive mystery game. Your role is to preserve the mystery's solvability and narrative integrity while giving the player maximum agency.

HIDDEN TRUTH (never reveal this to the player directly):
{hidden_truth}

PROTECTED VARIABLES:
{protected_variables}

DEPENDENCY GRAPH (causal spans):
{dependency_graph}

PLAYER'S PROPOSED ACTION: "{player_input}"
CLASSIFICATION: {action_type}
PROPOSED OUTCOME: {proposed_outcome}
PROPOSED WORLD CHANGES: {proposed_world_changes}

COMPLETED PLOT POINTS: {completed_plot_points}
REMAINING PLOT POINTS: {remaining_plot_points}

Make one of these decisions:

"approve" — the action is fine. Provide the final narrative outcome text shown to the player.

"block" — the action would make the mystery permanently unsolvable, violate a protected variable, or is out-of-bounds for the setting. Provide a companion_message: an in-world reason delivered by a nearby character or narrative voice (NOT a system message). Make it feel natural, like a friend warning you — similar to a sidekick saying "I don't think we should do that here."

"plan_repair" — the player found an alternative path to a plot point that wasn't anticipated. Approve the action but patch the plot: mark the relevant plot point as reachable via this new path. Provide story_patch entries.

"generate_content" — the action is valid but requires new world content (the rule generator should have already handled this, but if something is still missing, flag it here).

"retrofit_rules" — the action reveals that an existing rule needs updating for consistency.

IMPORTANT: Prefer "approve" when possible. Only block when truly necessary to protect story solvability. The player should feel in control. When blocking, the companion message must feel organic, not like a game system rejection.
"""

DRAMA_MANAGER_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "decision": {"type": "STRING"},
        "reason": {"type": "STRING"},
        "companion_message": {"type": "STRING"},
        "approved_outcome_description": {"type": "STRING"},
        "story_patch": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "action": {"type": "STRING"},
                    "plot_point_id": {"type": "STRING"},
                    "new_description": {"type": "STRING"}
                },
                "required": ["action", "plot_point_id", "new_description"]
            }
        }
    },
    "required": ["decision", "reason", "companion_message", "approved_outcome_description", "story_patch"]
}
