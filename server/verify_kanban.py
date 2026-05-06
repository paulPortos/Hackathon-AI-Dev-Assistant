import requests
import json

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_kanban():
    # 1. Create a Board
    print("Creating Board...")
    resp = requests.post(f"{BASE_URL}/boards/", json={"name": "Test Board", "description": "A test board"})
    print(resp.status_code, resp.json())
    board_id = resp.json()['id']

    # 2. Create a Column
    print("\nCreating Column...")
    resp = requests.post(f"{BASE_URL}/boards/{board_id}/columns/", json={"name": "To Do", "position": 1})
    print(resp.status_code, resp.json())
    column_id = resp.json()['id']

    # 3. Create a Card
    print("\nCreating Card...")
    resp = requests.post(f"{BASE_URL}/columns/{column_id}/cards/", json={"title": "Test Card", "description": "A test card", "priority": "high"})
    print(resp.status_code, resp.json())
    card_id = resp.json()['id']

    # 4. Create a Label
    print("\nCreating Label...")
    resp = requests.post(f"{BASE_URL}/boards/{board_id}/labels/", json={"name": "Urgent", "color": "#FF0000"})
    print(resp.status_code, resp.json())
    label_id = resp.json()['id']

    # 5. Attach Label to Card
    print("\nAttaching Label...")
    resp = requests.post(f"{BASE_URL}/cards/{card_id}/labels/", json={"label_id": label_id})
    print(resp.status_code, resp.json())

    # 6. Move Card
    print("\nMoving Card...")
    # Create another column first
    resp = requests.post(f"{BASE_URL}/boards/{board_id}/columns/", json={"name": "In Progress", "position": 2})
    new_column_id = resp.json()['id']
    resp = requests.patch(f"{BASE_URL}/cards/{card_id}/move/", json={"column_id": new_column_id, "position": 1})
    print(resp.status_code, resp.json())

    # 7. Add Comment
    print("\nAdding Comment...")
    resp = requests.post(f"{BASE_URL}/cards/{card_id}/comments/", json={"body": "This is a test comment"})
    print(resp.status_code, resp.json())

    # 8. List Cards with Filter
    print("\nListing Cards with filter (priority=high)...")
    resp = requests.get(f"{BASE_URL}/columns/{new_column_id}/cards/?priority=high")
    print(resp.status_code, resp.json())

if __name__ == "__main__":
    try:
        test_kanban()
    except Exception as e:
        print(f"Error: {e}")
