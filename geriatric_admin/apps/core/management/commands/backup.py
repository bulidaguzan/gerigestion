"""
Management command for backup operations.
"""

from django.core.management.base import BaseCommand, CommandError
from config.backup import BackupManager


class Command(BaseCommand):
    help = 'Manage database and media backups'

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=['create', 'restore', 'list', 'cleanup'],
            help='Action to perform'
        )
        parser.add_argument(
            '--type',
            choices=['database', 'media', 'full'],
            default='full',
            help='Type of backup to create (default: full)'
        )
        parser.add_argument(
            '--file',
            help='Backup file path for restore operation'
        )

    def handle(self, *args, **options):
        backup_manager = BackupManager()
        action = options['action']

        if action == 'create':
            self.create_backup(backup_manager, options['type'])
        elif action == 'restore':
            self.restore_backup(backup_manager, options['file'])
        elif action == 'list':
            self.list_backups(backup_manager)
        elif action == 'cleanup':
            self.cleanup_backups(backup_manager)

    def create_backup(self, backup_manager, backup_type):
        """Create a backup."""
        self.stdout.write(f"Creating {backup_type} backup...")

        if backup_type == 'database':
            result = backup_manager.create_database_backup()
            if result:
                self.stdout.write(
                    self.style.SUCCESS(f"Database backup created: {result}")
                )
            else:
                raise CommandError("Database backup failed")

        elif backup_type == 'media':
            result = backup_manager.create_media_backup()
            if result:
                self.stdout.write(
                    self.style.SUCCESS(f"Media backup created: {result}")
                )
            else:
                raise CommandError("Media backup failed")

        elif backup_type == 'full':
            results = backup_manager.create_full_backup()
            if results:
                self.stdout.write(self.style.SUCCESS("Full backup completed:"))
                for backup_type, path in results.items():
                    self.stdout.write(f"  {backup_type}: {path}")
            else:
                raise CommandError("Full backup failed")

    def restore_backup(self, backup_manager, backup_file):
        """Restore from backup."""
        if not backup_file:
            raise CommandError("Backup file path is required for restore")

        self.stdout.write(f"Restoring from backup: {backup_file}")
        
        # Ask for confirmation
        confirm = input("This will overwrite existing data. Continue? (yes/no): ")
        if confirm.lower() != 'yes':
            self.stdout.write("Restore cancelled")
            return

        success = backup_manager.restore_database_backup(backup_file)
        if success:
            self.stdout.write(
                self.style.SUCCESS("Database restored successfully")
            )
        else:
            raise CommandError("Database restore failed")

    def list_backups(self, backup_manager):
        """List available backups."""
        backups = backup_manager.list_backups()
        
        if not backups:
            self.stdout.write("No backups found")
            return

        self.stdout.write("Available backups:")
        self.stdout.write("-" * 80)
        self.stdout.write(f"{'Filename':<40} {'Type':<10} {'Size':<10} {'Created':<20}")
        self.stdout.write("-" * 80)

        for backup in backups:
            size_mb = backup['size'] / (1024 * 1024)
            self.stdout.write(
                f"{backup['filename']:<40} "
                f"{backup['type']:<10} "
                f"{size_mb:.1f}MB{'':<4} "
                f"{backup['created'].strftime('%Y-%m-%d %H:%M:%S')}"
            )

    def cleanup_backups(self, backup_manager):
        """Clean up old backups."""
        self.stdout.write("Cleaning up old backups...")
        
        removed_count = backup_manager.cleanup_old_backups()
        self.stdout.write(
            self.style.SUCCESS(f"Removed {removed_count} old backup files")
        )