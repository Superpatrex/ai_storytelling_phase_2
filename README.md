# Team Holy Cow
# Template 3: Game Engine Rule Generation
Sorry about the video. I realized in editing that there was the zoom pictures over the slides. The final demo shows both a walkthrough of the game and a demonstration of the feature of template 3 within the game. Also `video_story.txt` has the total story that was reached within the video and `video_current_state.json` has the updated progression based on the video (if you want to use that instead of the `current_state.json` delete the `current_state.json` and rename the `video_current_state.json` to `current_state.json`)
# Running Instructions
## Running from Canvas Download
Welcome to the CIPHER (Crime Interactive Platform with Heuristic Engine Rules)! For running the story generation process from the canvas download, activate the pre-built virtual environment with `source venv/bin/activate`. You can verify all modules are present by running `pip freeze` and comparing against the list below. If there are any issues associated with the `venv` folder, delete the folder and recreate it using `python3 -m venv venv` then do `source venv/bin/activate` to enter into the virtual environment then `pip install -r requirements.txt`.

```
annotated-doc==0.0.4
annotated-types==0.7.0
anyio==4.12.1
certifi==2026.2.25
cffi==2.0.0
charset-normalizer==3.4.5
click==8.3.3
cryptography==46.0.5
distro==1.9.0
fastapi==0.136.1
google-auth==2.49.1
google-genai==1.67.0
h11==0.16.0
httpcore==1.0.9
httptools==0.7.1
httpx==0.28.1
idna==3.11
pyasn1==0.6.2
pyasn1_modules==0.4.2
pycparser==3.0
pydantic==2.12.5
pydantic_core==2.41.5
python-dotenv==1.2.2
PyYAML==6.0.3
requests==2.32.5
sniffio==1.3.1
starlette==1.0.0
tenacity==9.1.4
typing-inspection==0.4.2
typing_extensions==4.15.0
urllib3==2.6.3
uvicorn==0.46.0
uvloop==0.22.1
watchfiles==1.1.1
websockets==16.0
```

To run the application run `python server.py`. This will start the server to allow the frontend and backend to communicate.

To run the frontend, create a new terminal then run the following command `cd frontend` from the base directory. Then run `npm install` to install all of the necessary npm packages for the Next.js frontend. Then run `npm run dev` to then run the frontend.

## Downloading from GitHub
For running the story generation process from GitHub, make sure that you download the codebase from this [link](https://github.com/Superpatrex/ai_storytelling_phase_2). This is the link to the github therefore `clone` the `main` branch for the project.

After that ensure that you create a virtual environment for the application or simply install the pip modules by hand (I would recommend creating the visual environment). To do this run `python3 -m venv .venv` to create the virtual environment then `source .venv/bin/activate` to enter into the virtual environment. After that ensure that the proper python modules are downloaded by running `pip install -r requirements.txt`.

`NOTE:` If a requirements.txt file does not exist an exhaustive list can be found below.

```
annotated-doc==0.0.4
annotated-types==0.7.0
anyio==4.12.1
certifi==2026.2.25
cffi==2.0.0
charset-normalizer==3.4.5
click==8.3.3
cryptography==46.0.5
distro==1.9.0
fastapi==0.136.1
google-auth==2.49.1
google-genai==1.67.0
h11==0.16.0
httpcore==1.0.9
httptools==0.7.1
httpx==0.28.1
idna==3.11
pyasn1==0.6.2
pyasn1_modules==0.4.2
pycparser==3.0
pydantic==2.12.5
pydantic_core==2.41.5
python-dotenv==1.2.2
PyYAML==6.0.3
requests==2.32.5
sniffio==1.3.1
starlette==1.0.0
tenacity==9.1.4
typing-inspection==0.4.2
typing_extensions==4.15.0
urllib3==2.6.3
uvicorn==0.46.0
uvloop==0.22.1
watchfiles==1.1.1
websockets==16.0
```

Additionally, create a `.env` file and place it within the root of the projects structure. This `.env` file needs to have 4 elements with appropriate values

```
GEMINI_API_KEY=
GEMINI_MODEL_NAME=gemini-2.5-flash
MAX_LOOP_PROCESSES=15
MAX_RED_HERRINGS=3
```

To run the application run `python server.py`. This will start the server to allow the frontend and backend to communicate.

To run the frontend, create a new terminal then run the following command `cd frontend` from the base directory. Then run `npm install` to install all of the necessary npm packages for the Next.js frontend. Then run `npm run dev` to then run the frontend.

# Architecture
Architecture diagrams can be found in the `diagrams/` folder:
- `initialization_and_story_generation_diagram.png` — story initialization and generation pipeline
- `runtime_diagram.png` — game runtime loop and drama manager
- `frontend_diagram.png` — frontend architecture
- `detail_addition_diagram.png` — detail addition phase

The representative parts of each component can be found in the code as follows:
- Initialization & story generation: `src/phases/`
- Game runtime & drama manager: `src/runtime/drama_manager.py`, `src/runtime/game_loop.py`
- Action classification & rule generation: `src/runtime/action_classifier.py`, `src/runtime/rule_generator.py`
- Frontend: `frontend/`
- Server/API layer: `server.py`

# NOTES

The application takes about 15 minutes for generation of a new story (hopefully you will enjoy the minigame in the meantime) and costs about .50 - .60 cents for generation and variable amounts depending upon length of interaction.

The current `.env` file has a live API key for the project. It is capped at 5 dollars but please don't over use it!!!