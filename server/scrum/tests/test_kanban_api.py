from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from scrum.models import Board, Column, Card, Label, Comment

class KanbanAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.version = "v1"
        self.base_url = f"/api/{self.version}"

    def test_kanban_flow(self):
        # 1. Create Board
        response = self.client.post(f"{self.base_url}/boards/", {"name": "Test Board"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        board_id = response.data['id']

        # 2. Create Column
        response = self.client.post(f"{self.base_url}/boards/{board_id}/columns/", {"name": "To Do", "position": 1})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        column_id = response.data['id']

        # 3. Create Card
        response = self.client.post(f"{self.base_url}/columns/{column_id}/cards/", {"title": "Test Card", "priority": "high"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        card_id = response.data['id']

        # 4. Create Label
        response = self.client.post(f"{self.base_url}/boards/{board_id}/labels/", {"name": "Urgent", "color": "#FF0000"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        label_id = response.data['id']

        # 5. Attach Label
        response = self.client.post(f"{self.base_url}/cards/{card_id}/labels/", {"label_id": label_id})
        if response.status_code != status.HTTP_200_OK:
            print(response.content)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(any(l['id'] == label_id for l in response.data['labels']))

        # 6. Move Card
        response = self.client.post(f"{self.base_url}/boards/{board_id}/columns/", {"name": "In Progress", "position": 2})
        new_column_id = response.data['id']
        response = self.client.patch(f"{self.base_url}/cards/{card_id}/move/", {"column_id": new_column_id, "position": 5})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['column'], new_column_id)
        self.assertEqual(response.data['position'], 5)

        # 7. Add Comment
        response = self.client.post(f"{self.base_url}/cards/{card_id}/comments/", {"body": "Test comment"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 8. Filter
        response = self.client.get(f"{self.base_url}/columns/{new_column_id}/cards/?priority=high")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

        response = self.client.get(f"{self.base_url}/columns/{new_column_id}/cards/?priority=low")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)
