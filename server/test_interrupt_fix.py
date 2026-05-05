import asyncio
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

async def test_interrupt_repro():
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
                                print("Turn complete.")
                            if response.server_content.interrupted:
                                print("Interrupted!")
                    print("Receive loop finished naturally.")
            except Exception as e:
                print(f"Receive error: {e}")

        asyncio.create_task(listen())
        
        print("Sending Turn 1 (Long)")
        await session.send_realtime_input(text="Tell me a very long story.")
        await asyncio.sleep(2)
        
        print("Interrupting with audio...")
        dummy_audio = b'\x00' * (16000 * 2) # 1s silence
        await session.send_realtime_input(audio=types.Blob(
            data=dummy_audio,
            mime_type="audio/pcm;rate=16000"
        ))
        
        await asyncio.sleep(5)
        print("Done.")

if __name__ == "__main__":
    asyncio.run(test_interrupt_repro())
