"""
Management command to sync Statbotics data for active events
Usage: python manage.py sync_statbotics [--event-id EVENT_ID] [--all]
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from events.models import Event
from analytics.statbotics_api import sync_event_statbotics_data


class Command(BaseCommand):
    help = 'Sync Statbotics data for active events'

    def add_arguments(self, parser):
        parser.add_argument(
            '--event-id',
            type=int,
            help='Specific event ID to sync',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Sync all events (not just active ones)',
        )

    def handle(self, *args, **options):
        event_id = options.get('event_id')
        sync_all = options.get('all')

        if event_id:
            # Sync specific event
            try:
                event = Event.objects.get(id=event_id)
                self.stdout.write(f'Syncing Statbotics data for event: {event.name}')
                updated_count = sync_event_statbotics_data(event)
                self.stdout.write(self.style.SUCCESS(
                    f'Successfully synced data for {updated_count} teams'
                ))
            except Event.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Event with ID {event_id} not found'))
        else:
            # Sync active or all events
            if sync_all:
                events = Event.objects.all()
                self.stdout.write('Syncing all events...')
            else:
                # Active events: within 7 days of start_date or between start and end date
                today = timezone.now().date()
                events = Event.objects.filter(
                    start_date__gte=today - timedelta(days=7),
                    end_date__gte=today
                )
                self.stdout.write(f'Syncing {events.count()} active events...')

            total_updated = 0
            for event in events:
                self.stdout.write(f'Processing: {event.name}')
                try:
                    updated_count = sync_event_statbotics_data(event)
                    total_updated += updated_count
                    self.stdout.write(f'  → Synced {updated_count} teams')
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'  → Error: {str(e)}'))

            self.stdout.write(self.style.SUCCESS(
                f'Successfully synced data for {total_updated} teams across {events.count()} events'
            ))
