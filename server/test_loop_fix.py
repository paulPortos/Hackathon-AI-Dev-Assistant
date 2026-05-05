import asyncio
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

async def test_repro():
    api_key = os.getenv("GOOGLE_API_KEY")
    client = genai.Client(api_key=api_key, http_options={'api_version': 'v1beta'})
    model_id = "gemini-3.1-flash-live-preview"
    
    config = {"response_modalities": ["AUDIO"]}

    async with client.aio.live.connect(model=model_id, config=config) as session:
        print("Connected.")
        
        async def listen():
            try:
                while True:
                    print("Starting receive loop...")
                    async for response in session.receive():
                        if response.server_content:
                            if response.server_content.turn_complete:
                                print("Turn complete in loop.")
                                # In the current consumers.py, this would exit the loop!
                    print("Receive loop finished naturally.")
            except Exception as e:
                print(f"Receive error: {e}")

        asyncio.create_task(listen())
        
        print("Sending Turn 1")
        await session.send_realtime_input(text="Say 'One'")
        await asyncio.sleep(3)
        
        print("Sending Turn 2")
        await session.send_realtime_input(text="Say 'Two'")
        await asyncio.sleep(3)
        
        print("Done.")

if __name__ == "__main__":
    asyncio.run(test_repro())
