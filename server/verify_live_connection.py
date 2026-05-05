import asyncio
import json
import os
import sys
import django
from channels.testing import WebsocketCommunicator

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from scrum.consumers import ScrumLiveConsumer

async def test_text_interaction():
    print("Starting Live API Text Interaction Test...")
    
    # Initialize communicator
    communicator = WebsocketCommunicator(ScrumLiveConsumer.as_asgi(), "/ws/scrum-live/")
    connected, subprotocol = await communicator.connect()
    
    if not connected:
        print("Failed to connect to ScrumLiveConsumer")
        return

    print("Connected to ScrumLiveConsumer")

    # Send a text message
    test_msg = {"type": "text", "text": "Hello Gemini, this is a test from the Scrum app scaffold. Please reply with 'Scrum scaffold verified' if you can hear me."}
    await communicator.send_json_to(test_msg)
    print(f"Sent: {test_msg['text']}")

    # Wait for response (transcription)
    # Gemini Live usually sends 'inputTranscription' then 'outputTranscription' and 'audio'
    print("Waiting for Gemini response (this may take a few seconds)...")
    
    received_output = False
    for _ in range(20): # Polling for a bit
        try:
            response = await communicator.receive_json_from(timeout=5)
            if response.get("type") == "transcription":
                print(f"[{response['source'].upper()}]: {response['text']}")
                if response['source'] == "gemini":
                    received_output = True
                    break
            elif response.get("type") == "error":
                print(f"ERROR: {response['message']}")
                break
        except asyncio.TimeoutError:
            continue

    if received_output:
        print("\nSUCCESS: Received text output from Gemini Live!")
    else:
        print("\nFAILURE: Did not receive a text response from Gemini Live.")

    await communicator.disconnect()

if __name__ == "__main__":
    asyncio.run(test_text_interaction())
