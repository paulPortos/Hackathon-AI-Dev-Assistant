import asyncio
import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

async def test_gemini_direct():
    api_key = os.getenv("GOOGLE_API_KEY")
    client = genai.Client(api_key=api_key, http_options={'api_version': 'v1beta'})
    model_id = "gemini-3.1-flash-live-preview"
    config = {"response_modalities": ["AUDIO"]}
    
    print(f"Connecting to Gemini {model_id}...", flush=True)
    try:
        async with client.aio.live.connect(model=model_id, config=config) as session:
            print("Connected successfully!", flush=True)
            await session.send_realtime_input(text="Hello")

            async for response in session.receive():
                print(f"Received response: {response}")
                break
    except Exception as e:
        print(f"Connection failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_gemini_direct())
