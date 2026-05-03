// Backend WebSocket and REST API URLs
export const WS_URL = "ws://localhost:8000/ws";
export const API_URL = "http://localhost:8000";

// Union type for all messages the server can send over the WebSocket
export type ServerMessage =
  | { type: "generation_progress"; phase: string; status: "starting" | "complete" | "error"; label: string }
  | { type: "generation_complete" }
  | { type: "game_start"; protagonist: string; goal: string }
  | { type: "game_output"; text: string; category: "narrative" | "system" | "location" | "warning" | "win" | "error" | "room_name" | "room_desc" | "exits" | "objects_present" | "npcs_present" | "inventory_line" | "separator" }
  | { type: "game_location"; room: Room; objects: WorldObject[]; npcs: NPC[]; inventory: string[] }
  | { type: "action_complete"; game_complete: boolean }
  | { type: "reset_complete" }
  | { type: "error"; message: string };

// Shape of a navigable room in the world graph
export interface Room {
  id: string;
  name: string;
  description: string;
  connections: { direction: string; to_room_id: string; label?: string }[];
}

// Shape of an interactive object placed in the world
export interface WorldObject {
  id: string;
  name: string;
  description: string;
}

// Shape of an NPC placed in the world
export interface NPC {
  id: string;
  name: string;
}
