import asyncio
import json
import os
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# FastAPI app setup with CORS middleware to allow requests and responses from the frontend
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ThreadPoolExecutor for running blocking tasks without blocking the event loop
executor = ThreadPoolExecutor(max_workers=2)

_controller = None
_game_loop = None

# API endpoint to check the status of the current game state
@app.get("/api/status")
async def get_status():
    # Check if there's an existing state and return some basic info about the current story and protagonist
    from src.config import STATE_DIR
    state_file = os.path.join(STATE_DIR, "current_state.json")
    has_state = os.path.exists(state_file)

    # If there's a state, try to load the story name and protagonist name for display purposes
    story_name = None
    protagonist_name = None
    if has_state:
        try:
            with open(state_file) as f:
                data = json.load(f)
            setting = data.get("setting", {})
            story_name = setting.get("location")
            protagonist_name = data.get("protagonist", {}).get("Name")
        except Exception:
            pass

    return {
        "has_state": has_state,
        "story_name": story_name,
        "protagonist_name": protagonist_name,
    }

# WebSocket endpoint to handle real-time communication for story generation and gameplay actions
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global _controller, _game_loop
    await websocket.accept()
    loop = asyncio.get_event_loop()

    # Main loop to receive messages from the frontend and handle different types of requests
    try:
        while True:
            # Wait for a message from the frontend
            data = await websocket.receive_json()
            msg_type = data.get("type")

            # If the message is to start generation, run the generation pipeline and send progress updates
            if msg_type == "start_generation":
                await _handle_generation(websocket, loop)

            elif msg_type == "reset_game":
                from src.config import STATE_DIR
                state_file = os.path.join(STATE_DIR, "current_state.json")
                if os.path.exists(state_file):
                    os.remove(state_file)
                _controller = None
                _game_loop = None
                await websocket.send_json({"type": "reset_complete"})

            elif msg_type == "start_game":
                await _handle_start_game(websocket, loop)

            elif msg_type == "player_action":
                player_input = data.get("input", "").strip()
                if player_input:
                    await _handle_action(websocket, loop, player_input)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass


# Helper function to handle story generation over the WebSocket, streaming progress events to the frontend
async def _handle_generation(websocket: WebSocket, loop: asyncio.AbstractEventLoop):
    global _controller
    from src.meta_controller import MetaController
    from src.config import STATE_DIR

    # Clear any existing state before starting a fresh generation
    state_file = os.path.join(STATE_DIR, "current_state.json")
    if os.path.exists(state_file):
        os.remove(state_file)

    q: asyncio.Queue = asyncio.Queue()
    done = asyncio.Event()

    # Callback to forward progress events from the background thread to the WebSocket queue
    def progress_cb(event: dict):
        loop.call_soon_threadsafe(q.put_nowait, event)

    _controller = MetaController(progress_callback=progress_cb)

    # Run the full generation pipeline in a thread to avoid blocking the event loop
    def run():
        try:
            _controller.run_all()
        except Exception as e:
            loop.call_soon_threadsafe(
                q.put_nowait, {"type": "error", "message": str(e)}
            )
        finally:
            loop.call_soon_threadsafe(done.set)

    asyncio.ensure_future(loop.run_in_executor(executor, run))

    # Stream progress events to the frontend until generation is complete
    while not (done.is_set() and q.empty()):
        if not q.empty():
            await websocket.send_json(q.get_nowait())
        else:
            await asyncio.sleep(0.02)

    await websocket.send_json({"type": "generation_complete"})


# Helper function to start the game loop and send the initial location description to the frontend
async def _handle_start_game(websocket: WebSocket, loop: asyncio.AbstractEventLoop):
    global _controller, _game_loop
    from src.meta_controller import MetaController
    from src.runtime.game_loop import GameLoop

    # Load the controller from the existing state if it is not already initialized
    if _controller is None:
        _controller = MetaController()

    if not _controller.state.get("world_graph", {}).get("rooms"):
        await websocket.send_json({
            "type": "error",
            "message": "No world found. Generate a story first.",
        })
        return

    q: asyncio.Queue = asyncio.Queue()
    done = asyncio.Event()

    # Callback to forward game output events from the background thread to the WebSocket queue
    def output_cb(event: dict):
        loop.call_soon_threadsafe(q.put_nowait, event)

    _game_loop = GameLoop(_controller, output_callback=output_cb)

    # Send the protagonist name and goal to the frontend to display at game start
    protagonist = _controller.state.get("protagonist", {})
    goal = _controller.state.get("goal", "Solve the crime")

    await websocket.send_json({
        "type": "game_start",
        "protagonist": protagonist.get("Name", "The Detective"),
        "goal": goal,
    })

    # Display the starting location in a background thread and stream output events
    def show_location():
        try:
            _game_loop.display_location()
        finally:
            loop.call_soon_threadsafe(done.set)

    asyncio.ensure_future(loop.run_in_executor(executor, show_location))

    while not (done.is_set() and q.empty()):
        if not q.empty():
            await websocket.send_json(q.get_nowait())
        else:
            await asyncio.sleep(0.02)

    await websocket.send_json({"type": "action_complete", "game_complete": False})


# Helper function to handle a player action and stream the game response back to the frontend
async def _handle_action(
    websocket: WebSocket, loop: asyncio.AbstractEventLoop, player_input: str
):
    global _game_loop

    if _game_loop is None:
        await websocket.send_json({"type": "error", "message": "Game not started."})
        return

    q: asyncio.Queue = asyncio.Queue()
    done = asyncio.Event()

    # Update the output callback so events go to this WebSocket connection's queue
    def output_cb(event: dict):
        loop.call_soon_threadsafe(q.put_nowait, event)

    _game_loop.output_callback = output_cb

    # Handle built-in commands or pass the input to the game loop for processing
    def run():
        try:
            cmd = player_input.lower()
            if cmd in ("look", "l"):
                _game_loop.display_location()
            elif cmd in ("inventory", "i", "inv"):
                inv = _game_loop.state.get("player_state", {}).get("inventory", [])
                text = f"Carrying: {', '.join(inv)}" if inv else "You are carrying nothing."
                _game_loop._emit(text, "system")
            elif cmd == "help":
                _game_loop._emit("Commands: look, inventory, go [direction], or describe any action.", "system")
                _game_loop._emit("Exits are shown after your location description.", "system")
            else:
                _game_loop.process_action(player_input)
                if not _game_loop.state.get("game_complete"):
                    _game_loop.display_location()
        except Exception as e:
            output_cb({"type": "game_output", "text": f"Error: {e}", "category": "error"})
        finally:
            loop.call_soon_threadsafe(done.set)

    asyncio.ensure_future(loop.run_in_executor(executor, run))

    # Stream game output events to the frontend until the action is complete
    while not (done.is_set() and q.empty()):
        if not q.empty():
            await websocket.send_json(q.get_nowait())
        else:
            await asyncio.sleep(0.02)

    game_complete = _game_loop.state.get("game_complete", False) if _game_loop else False
    await websocket.send_json({"type": "action_complete", "game_complete": game_complete})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
