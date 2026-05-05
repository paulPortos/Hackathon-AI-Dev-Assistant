import asyncio
import websockets
import json

async def test_real_server():
    uri = "ws://localhost:8000/ws/scrum-live/"

    print(f"Connecting to {uri}...")
    try:
        async with websockets.connect(uri) as websocket:


            print("Connected to Server!")
            msg = {"type": "text", "text": "Hello Gemini, real server test."}
            await websocket.send(json.dumps(msg))
            print(f"Sent: {msg['text']}")
            
            while True:
                response = await websocket.recv()
                data = json.loads(response)
                print(f"Received: {data}")
                if data.get("type") == "transcription" and data.get("source") == "gemini":
                    print("SUCCESS!")
                    break
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_real_server())
