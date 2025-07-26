"""
Database configuration utilities for Geriatric Administration System.
"""

import os
import logging
from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings

logger = logging.getLogger(__name__)


def get_database_info():
    """Get current database connection information."""
    db_settings = settings.DATABASES['default']
    return {
        'engine': db_settings['ENGINE'],
        'name': db_settings['NAME'],
        'user': db_settings['USER'],
        'host': db_settings['HOST'],
        'port': db_settings['PORT'],
    }


def test_database_connection():
    """Test database connection and return status."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            if result and result[0] == 1:
                logger.info("Database connection successful")
                return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False
    return False


def get_database_version():
    """Get PostgreSQL version information."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            logger.info(f"Database version: {version}")
            return version
    except Exception as e:
        logger.error(f"Failed to get database version: {e}")
        return None


def check_database_extensions():
    """Check if required PostgreSQL extensions are installed."""
    required_extensions = [
        'uuid-ossp',  # For UUID generation
        'pg_trgm',    # For full-text search
        'unaccent',   # For accent-insensitive search
    ]
    
    installed_extensions = []
    missing_extensions = []
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT extname FROM pg_extension 
                WHERE extname = ANY(%s)
            """, [required_extensions])
            
            installed = [row[0] for row in cursor.fetchall()]
            installed_extensions = installed
            missing_extensions = [ext for ext in required_extensions if ext not in installed]
            
            if missing_extensions:
                logger.warning(f"Missing database extensions: {missing_extensions}")
            else:
                logger.info("All required database extensions are installed")
                
    except Exception as e:
        logger.error(f"Failed to check database extensions: {e}")
    
    return {
        'installed': installed_extensions,
        'missing': missing_extensions
    }


def optimize_database_settings():
    """Get recommended PostgreSQL configuration settings."""
    recommendations = {
        'shared_buffers': '256MB',
        'effective_cache_size': '1GB',
        'maintenance_work_mem': '64MB',
        'checkpoint_completion_target': '0.9',
        'wal_buffers': '16MB',
        'default_statistics_target': '100',
        'random_page_cost': '1.1',
        'effective_io_concurrency': '200',
        'work_mem': '4MB',
        'min_wal_size': '1GB',
        'max_wal_size': '4GB',
    }
    
    logger.info("Recommended PostgreSQL settings for optimal performance:")
    for setting, value in recommendations.items():
        logger.info(f"  {setting} = {value}")
    
    return recommendations


def create_database_indexes():
    """Create additional database indexes for performance."""
    indexes = [
        # Add custom indexes here based on query patterns
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp);",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_user ON audit_log(user_id);",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_center ON audit_log(center_id);",
    ]
    
    try:
        with connection.cursor() as cursor:
            for index_sql in indexes:
                try:
                    cursor.execute(index_sql)
                    logger.info(f"Created index: {index_sql}")
                except Exception as e:
                    logger.warning(f"Failed to create index: {e}")
    except Exception as e:
        logger.error(f"Failed to create database indexes: {e}")


def get_database_size():
    """Get database size information."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    pg_size_pretty(pg_database_size(current_database())) as database_size,
                    pg_size_pretty(pg_total_relation_size('django_session')) as session_table_size
            """)
            result = cursor.fetchone()
            
            size_info = {
                'database_size': result[0],
                'session_table_size': result[1]
            }
            
            logger.info(f"Database size: {size_info['database_size']}")
            logger.info(f"Session table size: {size_info['session_table_size']}")
            
            return size_info
    except Exception as e:
        logger.error(f"Failed to get database size: {e}")
        return None


def cleanup_old_sessions():
    """Clean up expired sessions from the database."""
    try:
        from django.contrib.sessions.models import Session
        from django.utils import timezone
        
        expired_sessions = Session.objects.filter(expire_date__lt=timezone.now())
        count = expired_sessions.count()
        expired_sessions.delete()
        
        logger.info(f"Cleaned up {count} expired sessions")
        return count
    except Exception as e:
        logger.error(f"Failed to cleanup sessions: {e}")
        return 0