"""
Backup configuration utilities for Geriatric Administration System.
"""

import os
import gzip
import shutil
import logging
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from django.conf import settings
from django.core.management import call_command
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


class BackupManager:
    """Manages database and media file backups."""
    
    def __init__(self):
        self.backup_settings = getattr(settings, 'BACKUP_SETTINGS', {})
        self.storage_path = Path(self.backup_settings.get('STORAGE_PATH', '/tmp/backups'))
        self.retention_days = self.backup_settings.get('RETENTION_DAYS', 90)
        self.compress = self.backup_settings.get('COMPRESS', True)
        self.encrypt = self.backup_settings.get('ENCRYPT', True)
        self.encryption_key = self.backup_settings.get('ENCRYPTION_KEY', '')
        
        # Ensure backup directory exists
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def create_database_backup(self):
        """Create a database backup."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"db_backup_{timestamp}.sql"
        backup_path = self.storage_path / backup_filename
        
        try:
            # Get database settings
            db_settings = settings.DATABASES['default']
            
            # Create PostgreSQL dump command
            cmd = [
                'pg_dump',
                f"--host={db_settings['HOST']}",
                f"--port={db_settings['PORT']}",
                f"--username={db_settings['USER']}",
                f"--dbname={db_settings['NAME']}",
                '--no-password',
                '--verbose',
                '--clean',
                '--no-acl',
                '--no-owner',
                f"--file={backup_path}"
            ]
            
            # Set password environment variable
            env = os.environ.copy()
            env['PGPASSWORD'] = db_settings['PASSWORD']
            
            # Execute backup command
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Database backup created: {backup_path}")
                
                # Compress if enabled
                if self.compress:
                    backup_path = self._compress_file(backup_path)
                
                # Encrypt if enabled
                if self.encrypt and self.encryption_key:
                    backup_path = self._encrypt_file(backup_path)
                
                return backup_path
            else:
                logger.error(f"Database backup failed: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"Database backup error: {e}")
            return None
    
    def create_media_backup(self):
        """Create a backup of media files."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"media_backup_{timestamp}.tar.gz"
        backup_path = self.storage_path / backup_filename
        
        try:
            media_root = Path(settings.MEDIA_ROOT)
            
            if not media_root.exists():
                logger.warning("Media directory does not exist, skipping media backup")
                return None
            
            # Create compressed archive
            shutil.make_archive(
                str(backup_path.with_suffix('')),
                'gztar',
                str(media_root.parent),
                str(media_root.name)
            )
            
            logger.info(f"Media backup created: {backup_path}")
            
            # Encrypt if enabled
            if self.encrypt and self.encryption_key:
                backup_path = self._encrypt_file(backup_path)
            
            return backup_path
            
        except Exception as e:
            logger.error(f"Media backup error: {e}")
            return None
    
    def create_full_backup(self):
        """Create a full system backup (database + media)."""
        logger.info("Starting full system backup...")
        
        backups = {}
        
        # Create database backup
        db_backup = self.create_database_backup()
        if db_backup:
            backups['database'] = db_backup
        
        # Create media backup
        media_backup = self.create_media_backup()
        if media_backup:
            backups['media'] = media_backup
        
        logger.info(f"Full backup completed. Files: {list(backups.values())}")
        return backups
    
    def restore_database_backup(self, backup_path):
        """Restore database from backup."""
        backup_path = Path(backup_path)
        
        if not backup_path.exists():
            logger.error(f"Backup file not found: {backup_path}")
            return False
        
        try:
            # Decrypt if needed
            if backup_path.suffix == '.enc':
                backup_path = self._decrypt_file(backup_path)
            
            # Decompress if needed
            if backup_path.suffix == '.gz':
                backup_path = self._decompress_file(backup_path)
            
            # Get database settings
            db_settings = settings.DATABASES['default']
            
            # Create PostgreSQL restore command
            cmd = [
                'psql',
                f"--host={db_settings['HOST']}",
                f"--port={db_settings['PORT']}",
                f"--username={db_settings['USER']}",
                f"--dbname={db_settings['NAME']}",
                '--no-password',
                f"--file={backup_path}"
            ]
            
            # Set password environment variable
            env = os.environ.copy()
            env['PGPASSWORD'] = db_settings['PASSWORD']
            
            # Execute restore command
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Database restored from: {backup_path}")
                return True
            else:
                logger.error(f"Database restore failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Database restore error: {e}")
            return False
    
    def cleanup_old_backups(self):
        """Remove backups older than retention period."""
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        removed_count = 0
        
        try:
            for backup_file in self.storage_path.glob('*_backup_*'):
                if backup_file.stat().st_mtime < cutoff_date.timestamp():
                    backup_file.unlink()
                    removed_count += 1
                    logger.info(f"Removed old backup: {backup_file}")
            
            logger.info(f"Cleaned up {removed_count} old backup files")
            return removed_count
            
        except Exception as e:
            logger.error(f"Backup cleanup error: {e}")
            return 0
    
    def list_backups(self):
        """List all available backups."""
        backups = []
        
        try:
            for backup_file in sorted(self.storage_path.glob('*_backup_*')):
                stat = backup_file.stat()
                backups.append({
                    'filename': backup_file.name,
                    'path': str(backup_file),
                    'size': stat.st_size,
                    'created': datetime.fromtimestamp(stat.st_mtime),
                    'type': 'database' if 'db_backup' in backup_file.name else 'media'
                })
        except Exception as e:
            logger.error(f"Error listing backups: {e}")
        
        return backups
    
    def _compress_file(self, file_path):
        """Compress a file using gzip."""
        file_path = Path(file_path)
        compressed_path = file_path.with_suffix(file_path.suffix + '.gz')
        
        with open(file_path, 'rb') as f_in:
            with gzip.open(compressed_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # Remove original file
        file_path.unlink()
        logger.info(f"File compressed: {compressed_path}")
        return compressed_path
    
    def _decompress_file(self, file_path):
        """Decompress a gzipped file."""
        file_path = Path(file_path)
        decompressed_path = file_path.with_suffix('')
        
        with gzip.open(file_path, 'rb') as f_in:
            with open(decompressed_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        logger.info(f"File decompressed: {decompressed_path}")
        return decompressed_path
    
    def _encrypt_file(self, file_path):
        """Encrypt a file using Fernet encryption."""
        if not self.encryption_key:
            logger.warning("No encryption key provided, skipping encryption")
            return file_path
        
        file_path = Path(file_path)
        encrypted_path = file_path.with_suffix(file_path.suffix + '.enc')
        
        try:
            # Generate key if it's a string
            if isinstance(self.encryption_key, str):
                key = self.encryption_key.encode()[:32].ljust(32, b'0')
                key = Fernet.generate_key()  # Use proper key generation
            else:
                key = self.encryption_key
            
            fernet = Fernet(key)
            
            with open(file_path, 'rb') as f_in:
                encrypted_data = fernet.encrypt(f_in.read())
            
            with open(encrypted_path, 'wb') as f_out:
                f_out.write(encrypted_data)
            
            # Remove original file
            file_path.unlink()
            logger.info(f"File encrypted: {encrypted_path}")
            return encrypted_path
            
        except Exception as e:
            logger.error(f"File encryption error: {e}")
            return file_path
    
    def _decrypt_file(self, file_path):
        """Decrypt an encrypted file."""
        if not self.encryption_key:
            logger.error("No encryption key provided for decryption")
            return file_path
        
        file_path = Path(file_path)
        decrypted_path = file_path.with_suffix('')
        
        try:
            # Generate key if it's a string
            if isinstance(self.encryption_key, str):
                key = self.encryption_key.encode()[:32].ljust(32, b'0')
                key = Fernet.generate_key()  # Use proper key generation
            else:
                key = self.encryption_key
            
            fernet = Fernet(key)
            
            with open(file_path, 'rb') as f_in:
                decrypted_data = fernet.decrypt(f_in.read())
            
            with open(decrypted_path, 'wb') as f_out:
                f_out.write(decrypted_data)
            
            logger.info(f"File decrypted: {decrypted_path}")
            return decrypted_path
            
        except Exception as e:
            logger.error(f"File decryption error: {e}")
            return file_path