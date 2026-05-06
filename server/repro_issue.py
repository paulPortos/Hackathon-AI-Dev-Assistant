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
        "response_modalities": ["AUDIO"],
        "speech_config": {
            "voice_config": {
                "prebuilt_voice_config": {
                    "voice_name": "Puck"
                }
            }
        }
    }

    print("Connecting to Gemini...")
    async with client.aio.live.connect(model=model_id, config=config) as session:
        print("Connected.")
        
        # Start sending audio chunks continuously like the frontend
        async def send_audio_continuously():
            dummy_audio = b'\x00' * 3200 # 0.1s of 16kHz 16-bit PCM
            try:
                while True:
                    await session.send_realtime_input(audio=types.Blob(
                        data=dummy_audio,
                        mime_type="audio/pcm;rate=16000"
                    ))
                    await asyncio.sleep(0.1)
            except Exception as e:
                print(f"Error sending audio: {e}")

        sender_task = asyncio.create_task(send_audio_continuously())
        
        print("Sending initial text input...")
        await session.send_realtime_input(text="Hello, tell me a short joke.")
        
        try:
            async for response in session.receive():
                print(f"Received response: turn_complete={getattr(response.server_content, 'turn_complete', False)}")
                if response.server_content and response.server_content.turn_complete:
                    print("Turn complete detected.")
                    # Let's see if the loop continues
                    
                if response.server_content and response.server_content.interrupted:
                    print("Interrupted detected.")
        except Exception as e:
            print(f"Error receiving: {e}")
        finally:
            sender_task.cancel()
            print("Session closed.")

if __name__ == "__main__":
    asyncio.run(test_repro())
