"""
Management command to check database and Redis configuration.
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from config.database import (
    test_database_connection, get_database_info, get_database_version,
    check_database_extensions, get_database_size
)
from config.redis_config import (
    test_redis_connection, get_redis_info, get_redis_info_detailed,
    get_cache_stats, monitor_redis_memory
)


class Command(BaseCommand):
    help = 'Check database and Redis configuration and connectivity'

    def add_arguments(self, parser):
        parser.add_argument(
            '--database-only',
            action='store_true',
            help='Check only database configuration',
        )
        parser.add_argument(
            '--redis-only',
            action='store_true',
            help='Check only Redis configuration',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed information',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('=== Geriatric Admin System Configuration Check ===\n')
        )

        check_database = not options['redis_only']
        check_redis = not options['database_only']
        verbose = options['verbose']

        # Check database configuration
        if check_database:
            self.check_database_config(verbose)

        # Check Redis configuration
        if check_redis:
            self.check_redis_config(verbose)

        self.stdout.write(
            self.style.SUCCESS('\n=== Configuration Check Complete ===')
        )

    def check_database_config(self, verbose=False):
        """Check database configuration and connectivity."""
        self.stdout.write(self.style.HTTP_INFO('\n--- Database Configuration ---'))
        
        # Get database info
        db_info = get_database_info()
        self.stdout.write(f"Engine: {db_info['engine']}")
        self.stdout.write(f"Database: {db_info['name']}")
        self.stdout.write(f"Host: {db_info['host']}:{db_info['port']}")
        self.stdout.write(f"User: {db_info['user']}")

        # Test connection
        self.stdout.write("\nTesting database connection...")
        if test_database_connection():
            self.stdout.write(self.style.SUCCESS("✓ Database connection successful"))
        else:
            self.stdout.write(self.style.ERROR("✗ Database connection failed"))
            return

        if verbose:
            # Get version
            version = get_database_version()
            if version:
                self.stdout.write(f"Version: {version}")

            # Check extensions
            extensions = check_database_extensions()
            if extensions['installed']:
                self.stdout.write(f"Installed extensions: {', '.join(extensions['installed'])}")
            if extensions['missing']:
                self.stdout.write(
                    self.style.WARNING(f"Missing extensions: {', '.join(extensions['missing'])}")
                )

            # Get database size
            size_info = get_database_size()
            if size_info:
                self.stdout.write(f"Database size: {size_info['database_size']}")
                self.stdout.write(f"Session table size: {size_info['session_table_size']}")

    def check_redis_config(self, verbose=False):
        """Check Redis configuration and connectivity."""
        self.stdout.write(self.style.HTTP_INFO('\n--- Redis Configuration ---'))
        
        # Get Redis info
        redis_info = get_redis_info()
        self.stdout.write(f"Backend: {redis_info['backend']}")
        self.stdout.write(f"Location: {redis_info['location']}")

        # Test connection
        self.stdout.write("\nTesting Redis connection...")
        if test_redis_connection():
            self.stdout.write(self.style.SUCCESS("✓ Redis connection successful"))
        else:
            self.stdout.write(self.style.WARNING("⚠ Redis connection failed (using fallback cache)"))
            return

        if verbose:
            # Get detailed info
            detailed_info = get_redis_info_detailed()
            if detailed_info:
                self.stdout.write(f"Version: {detailed_info['version']}")
                self.stdout.write(f"Mode: {detailed_info['mode']}")
                self.stdout.write(f"Memory used: {detailed_info['used_memory']}")
                self.stdout.write(f"Connected clients: {detailed_info['connected_clients']}")
                self.stdout.write(f"Uptime: {detailed_info['uptime_in_seconds']} seconds")

            # Get cache stats
            stats = get_cache_stats()
            if stats:
                self.stdout.write(f"Cache hit rate: {stats['hit_rate_percentage']}%")
                self.stdout.write(f"Total requests: {stats['total_requests']}")

            # Monitor memory
            memory_info = monitor_redis_memory()
            if memory_info:
                self.stdout.write(f"Peak memory: {memory_info['used_memory_peak_human']}")
                if memory_info['maxmemory_human']:
                    self.stdout.write(f"Max memory: {memory_info['maxmemory_human']}")