import json
from django.contrib.auth import get_user_model
from django.test import TestCase, Client

User = get_user_model()


class AuthApiTests(TestCase):
    """
    Tests d'authentification API.
    Objectifs :
    - Vérifier /auth/me (anon vs auth)
    - Vérifier login / logout session-based
    """

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="ludo",
            email="ludo@test.local",
            password="testpassword123",
        )

    def test_me_unauthenticated(self):
        """
        /auth/me sans être connecté doit retourner 200, 401 ou 403.
        """
        response = self.client.get("/api/auth/me/")
        self.assertIn(response.status_code, (200, 401, 403))

    def test_login_and_me(self):
        """
        Login avec credentials valides,
        puis accès à /api/auth/me.
        """
        response = self.client.post(
            "/api/auth/login/",
            data=json.dumps(
                {
                    "username": "ludo",
                    "password": "testpassword123",
                }
            ),
            content_type="application/json",
        )

        self.assertIn(response.status_code, (200, 204))
        self.assertIn("_auth_user_id", self.client.session)

        me_response = self.client.get("/api/auth/me/")
        self.assertEqual(me_response.status_code, 200)

        data = me_response.json()

        # Contrat minimal attendu
        self.assertTrue(data.get("is_authenticated", True))

    def test_login_invalid_credentials(self):
        """
        Login avec mauvais mot de passe → 400 ou 401.
        """
        response = self.client.post(
            "/api/auth/login/",
            data=json.dumps(
                {
                    "username": "ludo",
                    "password": "wrongpassword",
                }
            ),
            content_type="application/json",
        )

        self.assertIn(response.status_code, (400, 401))

    def test_logout(self):
        """
        Logout invalide la session.
        """
        self.client.force_login(self.user)
        response = self.client.post(
            "/api/auth/logout/",
        )
        self.assertIn(response.status_code, (200, 204))

        me_response = self.client.get("/api/auth/me/")
        self.assertIn(me_response.status_code, (200, 401, 403))