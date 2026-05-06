import asyncio
import os
import base64
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

async def test_repro():
    api_key = os.getenv("GOOGLE_API_KEY")
    client = genai.Client(api_key=api_key, http_options={'api_version': 'v1beta'})
    model_id = "gemini-3.1-flash-live-preview"
    
    config = {
        "response_modalities": ["AUDIO"]
    }

    print("Connecting to Gemini...")
    async with client.aio.live.connect(model=model_id, config=config) as session:
        print("Connected.")
        
        for i in range(2):
            print(f"--- Turn {i+1} ---")
            await session.send_realtime_input(text=f"Give me a 1-word response for turn {i+1}")
            async for response in session.receive():
                if response.server_content:
                    print(f"Received content, turn_complete={response.server_content.turn_complete}")
                    if response.server_content.turn_complete:
                        break
            print(f"Turn {i+1} finished.")
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(test_repro())
