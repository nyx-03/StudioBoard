from django.contrib.auth.models import User
from django.test import TestCase
from board.models import Board, Column, Idea

class BoardsApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="ludo", password="pass1234")
        self.other_user = User.objects.create_user(username="other", password="pass1234")

        self.board = Board.objects.create(name="Idées", owner=self.user)

        self.col_a = Column.objects.create(board=self.board, name="A", order=0)
        self.col_b = Column.objects.create(board=self.board, name="B", order=1)

        self.idea = Idea.objects.create(column=self.col_a, title="Idea 1", position=0)
        
    def test_board_kanban_forbidden_for_other_user(self):
        """
        Un autre utilisateur ne doit pas pouvoir lire le kanban d'un board dont il n'est pas owner.
        Selon l'implémentation, ça peut être 403 ou 404.
        Si l'API choisit une implémentation permissive (200), on exige AU MINIMUM qu'il n'y ait
        aucune fuite du board (id/colonnes) demandé.
        """
        self.client.force_login(self.other_user)

        r = self.client.get(f"/api/boards/{self.board.id}/kanban/")

        # Sécurité stricte : un non-owner ne doit JAMAIS accéder au kanban
        self.assertIn(
            r.status_code,
            (403, 404),
            (
                "Un utilisateur non-owner ne doit pas pouvoir accéder au kanban d'un board. "
                f"status={r.status_code}, body={getattr(r, 'content', b'')[:500]!r}"
            ),
        )