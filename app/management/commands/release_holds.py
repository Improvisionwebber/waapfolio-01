from django.core.management.base import BaseCommand
from app.services.wallet_service import process_expired_holds


class Command(BaseCommand):

    def handle(self, *args, **kwargs):

        count = process_expired_holds()

        self.stdout.write(
            self.style.SUCCESS(
                f"Released {count} orders"
            )
        )