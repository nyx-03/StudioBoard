from django.core.management.base import BaseCommand
from board.models import Board, Column


DEFAULT_COLUMNS = [
    "💡 Idées",
    "🔍 À creuser",
    "🧠 En réflexion",
    "✅ Validées",
    "🗄️ Archivées",
]


class Command(BaseCommand):
    help = "Crée (ou met à jour) le board 'Idées' et ses colonnes par défaut."

    def add_arguments(self, parser):
        parser.add_argument(
            "--name",
            default="Idées",
            help="Nom du board à créer (défaut: 'Idées')",
        )

    def handle(self, *args, **options):
        board_name = options["name"]

        board, created = Board.objects.get_or_create(
            name=board_name,
            defaults={"description": "Board Kanban pour capturer et trier des idées."},
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f"Board créé: {board.name}"))
        else:
            self.stdout.write(self.style.WARNING(f"Board existant: {board.name}"))

        # Crée / assure les colonnes et leur ordre
        for idx, col_name in enumerate(DEFAULT_COLUMNS):
            column, col_created = Column.objects.get_or_create(
                board=board,
                name=col_name,
                defaults={"order": idx},
            )
            # Si existant, on recale l'ordre sur la liste (utile si tu modifies DEFAULT_COLUMNS)
            if not col_created and column.order != idx:
                column.order = idx
                column.save(update_fields=["order"])

        self.stdout.write(self.style.SUCCESS("Colonnes OK."))