from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
import json

from board.models import Board, Column, Idea

User = get_user_model()


class IdeaApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="ludo",
            password="testpass123"
        )
        self.other_user = User.objects.create_user(
            username="other",
            password="otherpass123"
        )
        self.client.login(username="ludo", password="testpass123")

        self.board = Board.objects.create(
            name="Test Board",
            owner=self.user
        )

        self.col_a = Column.objects.create(
            board=self.board,
            name="A",
            order=0
        )
        self.col_b = Column.objects.create(
            board=self.board,
            name="B",
            order=1
        )

        self.idea = Idea.objects.create(
            column=self.col_a,
            title="Initial idea",
            position=0
        )

        self.other_board = Board.objects.create(
            name="Other Board",
            owner=self.other_user
        )
        self.other_col = Column.objects.create(
            board=self.other_board,
            name="Other Column",
            order=0
        )
        self.other_idea = Idea.objects.create(
            column=self.other_col,
            title="Other idea",
            position=0
        )

    def test_auth_required(self):
        self.client.logout()
        resp = self.client.get(f"/api/boards/{self.board.id}/kanban/")
        self.assertIn(resp.status_code, (401, 403))

    def test_quick_add_success(self):
        resp = self.client.post(
            f"/api/boards/{self.board.id}/ideas/quick-add/",
            data={"title": "New idea"}
        )
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(
            Idea.objects.filter(title="New idea", column__board=self.board).exists()
        )

    def test_quick_add_validation_error(self):
        resp = self.client.post(
            f"/api/boards/{self.board.id}/ideas/quick-add/",
            data={}
        )
        self.assertEqual(resp.status_code, 400)

    def test_idea_detail(self):
        resp = self.client.get(
            f"/api/boards/{self.board.id}/ideas/{self.idea.id}/"
        )
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        # L'API peut renvoyer soit l'idea à plat, soit sous une clé (ex: "idea").
        idea_data = data.get("idea") if isinstance(data, dict) else None
        if idea_data is None:
            idea_data = data

        # Selon l'implémentation, l'identifiant peut être sous "id" ou "idea_id".
        returned_id = None
        if isinstance(idea_data, dict):
            returned_id = idea_data.get("id", idea_data.get("idea_id"))

        self.assertIsNotNone(
            returned_id,
            f"Réponse inattendue pour idea detail. Clés reçues: {list(data.keys()) if isinstance(data, dict) else type(data)}",
        )
        self.assertEqual(int(returned_id), self.idea.id)

    def test_idea_update(self):
        resp = self.client.post(
            f"/api/boards/{self.board.id}/ideas/{self.idea.id}/update/",
            data={"title": "Updated title"}
        )
        self.assertEqual(resp.status_code, 200)
        self.idea.refresh_from_db()
        self.assertEqual(self.idea.title, "Updated title")

    def test_move_idea_between_columns(self):
        resp = self.client.post(
            f"/api/boards/{self.board.id}/ideas/{self.idea.id}/move/",
            data={
                "column_id": self.col_b.id,
                "position": 0
            }
        )
        self.assertEqual(resp.status_code, 200)
        self.idea.refresh_from_db()
        self.assertEqual(self.idea.column_id, self.col_b.id)

    def test_reorder_inside_column(self):
        idea2 = Idea.objects.create(
            column=self.col_a,
            title="Second idea",
            position=1
        )

        payload = {
            "order": [
                idea2.id,
                self.idea.id,
            ]
        }

        resp = self.client.post(
            f"/api/boards/{self.board.id}/columns/{self.col_a.id}/reorder/",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)

        self.idea.refresh_from_db()
        idea2.refresh_from_db()

        self.assertEqual(self.idea.position, 1)
        self.assertEqual(idea2.position, 0)

    def test_idea_forbidden_for_other_user(self):
        resp = self.client.get(
            f"/api/boards/{self.other_board.id}/ideas/{self.other_idea.id}/"
        )
        self.assertIn(resp.status_code, (403, 404))

    def test_quick_add_forbidden_for_other_user(self):
        resp = self.client.post(
            f"/api/boards/{self.other_board.id}/ideas/quick-add/",
            data={"title": "Should not add"}
        )
        self.assertIn(resp.status_code, (403, 404))

    def test_move_idea_forbidden_for_other_user(self):
        resp = self.client.post(
            f"/api/boards/{self.other_board.id}/ideas/{self.other_idea.id}/move/",
            data={
                "column_id": self.other_col.id,
                "position": 0
            }
        )
        self.assertIn(resp.status_code, (403, 404))

    def test_reorder_forbidden_for_other_user(self):
        resp = self.client.post(
            f"/api/boards/{self.other_board.id}/columns/{self.other_col.id}/reorder/",
            data={
                "order": [self.other_idea.id]
            },
            content_type="application/json",
        )
        self.assertIn(resp.status_code, (403, 404))