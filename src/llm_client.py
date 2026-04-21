import json
from google import genai
from google.genai import types
from src.config import GEMINI_API_KEY, DEFAULT_MODEL

# Class that interfaces with the LLM for the story generation process
class LLMClient:
    # Constructor for the LLM Client 
    def __init__(self, model_name: str = DEFAULT_MODEL):

        # Initialize the model name
        self.model_name = model_name

        # Initialize the client from the Google AI API
        self.client = genai.Client(api_key=GEMINI_API_KEY)

    # Method that generates the text from the LLM based on the prompt
    def generate_text(self, prompt: str, system_instruction: str = None, temperature: float = 0.7) -> str:

        # Create configuration for the temperature
        config = types.GenerateContentConfig(
             temperature=temperature
        )

        if system_instruction:
            config.system_instruction = system_instruction
        
        # Call the LLM API with the configuration and the prompt
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config,
            )
            return response.text.strip()
        except Exception as e:
            print(f"Error generating text: {e}")
            return ""

    # Method that generates a structured json response based on the LLM prompt and the LLM schema 
    def generate_json(self, prompt: str, schema: dict, system_instruction: str = None, temperature: float = 0.7) -> dict:

        # Create configuration for the temperature and the schema that is passed in
        config = types.GenerateContentConfig(
            temperature=temperature,
            response_mime_type="application/json",
            response_schema=schema,
        )

        if system_instruction:
            config.system_instruction = system_instruction

        # Call the LLM API with the configuration and the prompt
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config,
            )

            return json.loads(response.text)
        except Exception as e:
            print(f"Error generating JSON: {e}")
            return {}
