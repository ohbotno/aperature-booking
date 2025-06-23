# booking/backup_service.py
"""
Backup management service for the Aperture Booking.

This file is part of the Aperture Booking.
Copyright (C) 2025 Aperture Booking Contributors

This software is dual-licensed:
1. GNU General Public License v3.0 (GPL-3.0) - for open source use
2. Commercial License - for proprietary and commercial use

For GPL-3.0 license terms, see LICENSE file.
For commercial licensing, see COMMERCIAL-LICENSE.txt or visit:
https://aperture-booking.org/commercial
"""

import os
import shutil
import subprocess
import gzip
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from django.conf import settings
from django.core.management import call_command
from django.db import connection
from django.core.files.storage import default_storage
import tempfile


logger = logging.getLogger(__name__)


class BackupService:
    """
    Comprehensive backup service for database, media files, and system configuration.
    """
    
    def __init__(self):
        self.backup_dir = getattr(settings, 'BACKUP_DIR', os.path.join(settings.BASE_DIR, 'backups'))
        self.max_backup_age_days = getattr(settings, 'BACKUP_RETENTION_DAYS', 30)
        self.compression_enabled = getattr(settings, 'BACKUP_COMPRESSION', True)
        self.ensure_backup_directory()
    
    def ensure_backup_directory(self) -> None:
        """Ensure backup directory exists with proper permissions."""
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Set secure permissions (owner read/write/execute only)
        try:
            os.chmod(self.backup_dir, 0o700)
        except OSError as e:
            logger.warning(f"Could not set backup directory permissions: {e}")
    
    def create_full_backup(self, include_media: bool = True, description: str = "") -> Dict[str, Any]:
        """
        Create a complete backup including database, media files, and configuration.
        
        Args:
            include_media: Whether to include media files in backup
            description: Optional description for the backup
            
        Returns:
            Dictionary with backup information and status
        """
        backup_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"full_backup_{backup_timestamp}"
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        os.makedirs(backup_path, exist_ok=True)
        
        result = {
            'backup_name': backup_name,
            'backup_path': backup_path,
            'timestamp': datetime.now(),
            'description': description,
            'components': {},
            'success': True,
            'errors': [],
            'total_size': 0
        }
        
        try:
            # Backup database
            logger.info("Starting database backup...")
            db_result = self.backup_database(backup_path)
            result['components']['database'] = db_result
            if not db_result['success']:
                result['errors'].extend(db_result.get('errors', []))
            
            # Backup media files if requested
            if include_media:
                logger.info("Starting media files backup...")
                media_result = self.backup_media_files(backup_path)
                result['components']['media'] = media_result
                if not media_result['success']:
                    result['errors'].extend(media_result.get('errors', []))
            
            # Backup configuration
            logger.info("Starting configuration backup...")
            config_result = self.backup_configuration(backup_path)
            result['components']['configuration'] = config_result
            if not config_result['success']:
                result['errors'].extend(config_result.get('errors', []))
            
            # Calculate total backup size
            result['total_size'] = self._calculate_directory_size(backup_path)
            
            # Create backup manifest
            self._create_backup_manifest(backup_path, result)
            
            # Compress backup if enabled
            if self.compression_enabled:
                logger.info("Compressing backup...")
                compressed_path = self._compress_backup(backup_path)
                if compressed_path:
                    # Remove uncompressed directory
                    shutil.rmtree(backup_path)
                    result['backup_path'] = compressed_path
                    result['compressed'] = True
                    result['total_size'] = os.path.getsize(compressed_path)
                else:
                    result['errors'].append("Failed to compress backup")
            
            result['success'] = len(result['errors']) == 0
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            result['success'] = False
            result['errors'].append(str(e))
            
            # Cleanup failed backup
            if os.path.exists(backup_path):
                shutil.rmtree(backup_path, ignore_errors=True)
        
        return result
    
    def backup_database(self, backup_path: str) -> Dict[str, Any]:
        """Backup the database to the specified path."""
        result = {
            'success': True,
            'errors': [],
            'file_path': '',
            'size': 0
        }
        
        try:
            db_config = settings.DATABASES['default']
            engine = db_config['ENGINE']
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            if 'sqlite' in engine.lower():
                result.update(self._backup_sqlite(backup_path, db_config, timestamp))
            elif 'mysql' in engine.lower():
                result.update(self._backup_mysql(backup_path, db_config, timestamp))
            elif 'postgresql' in engine.lower():
                result.update(self._backup_postgresql(backup_path, db_config, timestamp))
            else:
                # Fallback to Django's dumpdata
                result.update(self._backup_django_dumpdata(backup_path, timestamp))
                
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            result['success'] = False
            result['errors'].append(str(e))
        
        return result
    
    def _backup_sqlite(self, backup_path: str, db_config: Dict, timestamp: str) -> Dict[str, Any]:
        """Backup SQLite database."""
        db_file = db_config['NAME']
        backup_file = os.path.join(backup_path, f'database_sqlite_{timestamp}.db')
        
        try:
            shutil.copy2(db_file, backup_file)
            
            if self.compression_enabled:
                compressed_file = f"{backup_file}.gz"
                with open(backup_file, 'rb') as f_in:
                    with gzip.open(compressed_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                os.remove(backup_file)
                backup_file = compressed_file
            
            return {
                'success': True,
                'file_path': backup_file,
                'size': os.path.getsize(backup_file),
                'errors': []
            }
            
        except Exception as e:
            return {
                'success': False,
                'file_path': '',
                'size': 0,
                'errors': [str(e)]
            }
    
    def _backup_mysql(self, backup_path: str, db_config: Dict, timestamp: str) -> Dict[str, Any]:
        """Backup MySQL database using mysqldump."""
        backup_file = os.path.join(backup_path, f'database_mysql_{timestamp}.sql')
        
        try:
            cmd = [
                'mysqldump',
                f"--host={db_config.get('HOST', 'localhost')}",
                f"--port={db_config.get('PORT', 3306)}",
                f"--user={db_config['USER']}",
                f"--password={db_config['PASSWORD']}",
                '--single-transaction',
                '--routines',
                '--triggers',
                db_config['NAME']
            ]
            
            with open(backup_file, 'w') as f:
                subprocess.run(cmd, stdout=f, check=True, stderr=subprocess.PIPE)
            
            if self.compression_enabled:
                compressed_file = f"{backup_file}.gz"
                with open(backup_file, 'rb') as f_in:
                    with gzip.open(compressed_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                os.remove(backup_file)
                backup_file = compressed_file
            
            return {
                'success': True,
                'file_path': backup_file,
                'size': os.path.getsize(backup_file),
                'errors': []
            }
            
        except subprocess.CalledProcessError as e:
            return {
                'success': False,
                'file_path': '',
                'size': 0,
                'errors': [f"mysqldump failed: {e.stderr.decode() if e.stderr else str(e)}"]
            }
        except Exception as e:
            return {
                'success': False,
                'file_path': '',
                'size': 0,
                'errors': [str(e)]
            }
    
    def _backup_postgresql(self, backup_path: str, db_config: Dict, timestamp: str) -> Dict[str, Any]:
        """Backup PostgreSQL database using pg_dump."""
        backup_file = os.path.join(backup_path, f'database_postgresql_{timestamp}.sql')
        
        try:
            env = os.environ.copy()
            env['PGPASSWORD'] = db_config['PASSWORD']
            
            cmd = [
                'pg_dump',
                f"--host={db_config.get('HOST', 'localhost')}",
                f"--port={db_config.get('PORT', 5432)}",
                f"--username={db_config['USER']}",
                '--no-password',
                '--verbose',
                '--clean',
                '--no-acl',
                '--no-owner',
                db_config['NAME']
            ]
            
            with open(backup_file, 'w') as f:
                subprocess.run(cmd, stdout=f, check=True, stderr=subprocess.PIPE, env=env)
            
            if self.compression_enabled:
                compressed_file = f"{backup_file}.gz"
                with open(backup_file, 'rb') as f_in:
                    with gzip.open(compressed_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                os.remove(backup_file)
                backup_file = compressed_file
            
            return {
                'success': True,
                'file_path': backup_file,
                'size': os.path.getsize(backup_file),
                'errors': []
            }
            
        except subprocess.CalledProcessError as e:
            return {
                'success': False,
                'file_path': '',
                'size': 0,
                'errors': [f"pg_dump failed: {e.stderr.decode() if e.stderr else str(e)}"]
            }
        except Exception as e:
            return {
                'success': False,
                'file_path': '',
                'size': 0,
                'errors': [str(e)]
            }
    
    def _backup_django_dumpdata(self, backup_path: str, timestamp: str) -> Dict[str, Any]:
        """Backup using Django's dumpdata command as fallback."""
        backup_file = os.path.join(backup_path, f'database_django_{timestamp}.json')
        
        try:
            with open(backup_file, 'w') as f:
                call_command('dumpdata', stdout=f, indent=2)
            
            if self.compression_enabled:
                compressed_file = f"{backup_file}.gz"
                with open(backup_file, 'rb') as f_in:
                    with gzip.open(compressed_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                os.remove(backup_file)
                backup_file = compressed_file
            
            return {
                'success': True,
                'file_path': backup_file,
                'size': os.path.getsize(backup_file),
                'errors': []
            }
            
        except Exception as e:
            return {
                'success': False,
                'file_path': '',
                'size': 0,
                'errors': [str(e)]
            }
    
    def backup_media_files(self, backup_path: str) -> Dict[str, Any]:
        """Backup media files."""
        result = {
            'success': True,
            'errors': [],
            'file_path': '',
            'size': 0,
            'file_count': 0
        }
        
        try:
            media_root = settings.MEDIA_ROOT
            if not os.path.exists(media_root):
                return {
                    'success': True,
                    'errors': ['No media directory found'],
                    'file_path': '',
                    'size': 0,
                    'file_count': 0
                }
            
            media_backup_path = os.path.join(backup_path, 'media')
            
            # Copy media files
            shutil.copytree(media_root, media_backup_path, dirs_exist_ok=True)
            
            # Count files and calculate size
            file_count = 0
            total_size = 0
            for root, dirs, files in os.walk(media_backup_path):
                file_count += len(files)
                for file in files:
                    total_size += os.path.getsize(os.path.join(root, file))
            
            result.update({
                'file_path': media_backup_path,
                'size': total_size,
                'file_count': file_count
            })
            
        except Exception as e:
            logger.error(f"Media files backup failed: {e}")
            result['success'] = False
            result['errors'].append(str(e))
        
        return result
    
    def backup_configuration(self, backup_path: str) -> Dict[str, Any]:
        """Backup system configuration and important files."""
        result = {
            'success': True,
            'errors': [],
            'files': [],
            'size': 0
        }
        
        try:
            config_backup_path = os.path.join(backup_path, 'configuration')
            os.makedirs(config_backup_path, exist_ok=True)
            
            # Backup requirements.txt
            requirements_path = os.path.join(settings.BASE_DIR, 'requirements.txt')
            if os.path.exists(requirements_path):
                shutil.copy2(requirements_path, config_backup_path)
                result['files'].append('requirements.txt')
            
            # Backup environment variables (sanitized)
            env_backup = self._create_sanitized_env_backup()
            env_file = os.path.join(config_backup_path, 'environment.json')
            with open(env_file, 'w') as f:
                json.dump(env_backup, f, indent=2)
            result['files'].append('environment.json')
            
            # Backup Django settings structure (sanitized)
            settings_backup = self._create_sanitized_settings_backup()
            settings_file = os.path.join(config_backup_path, 'django_settings.json')
            with open(settings_file, 'w') as f:
                json.dump(settings_backup, f, indent=2)
            result['files'].append('django_settings.json')
            
            # Calculate total size
            result['size'] = self._calculate_directory_size(config_backup_path)
            
        except Exception as e:
            logger.error(f"Configuration backup failed: {e}")
            result['success'] = False
            result['errors'].append(str(e))
        
        return result
    
    def _create_sanitized_env_backup(self) -> Dict[str, Any]:
        """Create a sanitized backup of environment variables."""
        sensitive_keys = [
            'SECRET_KEY', 'DB_PASSWORD', 'EMAIL_HOST_PASSWORD', 
            'AWS_SECRET_ACCESS_KEY', 'API_KEY', 'TOKEN'
        ]
        
        env_backup = {}
        for key, value in os.environ.items():
            if any(sensitive in key.upper() for sensitive in sensitive_keys):
                env_backup[key] = '[REDACTED]'
            elif key.startswith(('APERTURE_', 'DJANGO_')):
                env_backup[key] = value
        
        return env_backup
    
    def _create_sanitized_settings_backup(self) -> Dict[str, Any]:
        """Create a sanitized backup of Django settings."""
        sensitive_settings = [
            'SECRET_KEY', 'DATABASES', 'EMAIL_HOST_PASSWORD',
            'AWS_SECRET_ACCESS_KEY', 'API_KEYS'
        ]
        
        settings_backup = {}
        for attr in dir(settings):
            if not attr.startswith('_') and attr.isupper():
                if attr in sensitive_settings:
                    settings_backup[attr] = '[REDACTED]'
                else:
                    try:
                        value = getattr(settings, attr)
                        # Only include serializable values
                        json.dumps(value)
                        settings_backup[attr] = value
                    except (TypeError, ValueError):
                        settings_backup[attr] = str(value)
        
        return settings_backup
    
    def _compress_backup(self, backup_path: str) -> Optional[str]:
        """Compress backup directory into a tar.gz file."""
        try:
            compressed_path = f"{backup_path}.tar.gz"
            shutil.make_archive(backup_path, 'gztar', backup_path)
            return compressed_path
        except Exception as e:
            logger.error(f"Backup compression failed: {e}")
            return None
    
    def _create_backup_manifest(self, backup_path: str, backup_info: Dict[str, Any]) -> None:
        """Create a manifest file with backup information."""
        manifest = {
            'backup_name': backup_info['backup_name'],
            'timestamp': backup_info['timestamp'].isoformat(),
            'description': backup_info['description'],
            'components': backup_info['components'],
            'total_size': backup_info['total_size'],
            'django_version': getattr(settings, 'DJANGO_VERSION', 'unknown'),
            'python_version': f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
            'created_by': 'Aperture Booking Backup Service'
        }
        
        manifest_file = os.path.join(backup_path, 'backup_manifest.json')
        with open(manifest_file, 'w') as f:
            json.dump(manifest, f, indent=2, default=str)
    
    def _calculate_directory_size(self, directory: str) -> int:
        """Calculate total size of a directory in bytes."""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    total_size += os.path.getsize(filepath)
        return total_size
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """List all available backups with their information."""
        backups = []
        
        if not os.path.exists(self.backup_dir):
            return backups
        
        for item in os.listdir(self.backup_dir):
            item_path = os.path.join(self.backup_dir, item)
            backup_info = self._get_backup_info(item_path)
            if backup_info:
                backups.append(backup_info)
        
        # Sort by timestamp, newest first
        backups.sort(key=lambda x: x['timestamp'], reverse=True)
        return backups
    
    def _get_backup_info(self, backup_path: str) -> Optional[Dict[str, Any]]:
        """Get information about a backup from its manifest."""
        try:
            # Handle compressed backups
            if backup_path.endswith('.tar.gz'):
                # Extract manifest from compressed backup
                import tarfile
                with tarfile.open(backup_path, 'r:gz') as tar:
                    try:
                        manifest_member = tar.getmember('backup_manifest.json')
                        manifest_file = tar.extractfile(manifest_member)
                        if manifest_file:
                            manifest_data = json.loads(manifest_file.read().decode())
                            manifest_data['file_path'] = backup_path
                            manifest_data['size'] = os.path.getsize(backup_path)
                            manifest_data['compressed'] = True
                            return manifest_data
                    except KeyError:
                        pass
            else:
                # Handle uncompressed backups
                manifest_file = os.path.join(backup_path, 'backup_manifest.json')
                if os.path.exists(manifest_file):
                    with open(manifest_file, 'r') as f:
                        manifest_data = json.load(f)
                        manifest_data['file_path'] = backup_path
                        manifest_data['size'] = self._calculate_directory_size(backup_path)
                        manifest_data['compressed'] = False
                        return manifest_data
            
            # Fallback for backups without manifest
            stat = os.stat(backup_path)
            return {
                'backup_name': os.path.basename(backup_path),
                'timestamp': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'description': 'Legacy backup (no manifest)',
                'file_path': backup_path,
                'size': stat.st_size if os.path.isfile(backup_path) else self._calculate_directory_size(backup_path),
                'compressed': backup_path.endswith(('.tar.gz', '.zip')),
                'components': {}
            }
            
        except Exception as e:
            logger.error(f"Error getting backup info for {backup_path}: {e}")
            return None
    
    def delete_backup(self, backup_name: str) -> Dict[str, Any]:
        """Delete a specific backup."""
        result = {'success': False, 'message': ''}
        
        try:
            backup_path = os.path.join(self.backup_dir, backup_name)
            compressed_path = f"{backup_path}.tar.gz"
            
            if os.path.exists(compressed_path):
                os.remove(compressed_path)
                result['success'] = True
                result['message'] = f"Backup {backup_name} deleted successfully"
            elif os.path.exists(backup_path):
                if os.path.isdir(backup_path):
                    shutil.rmtree(backup_path)
                else:
                    os.remove(backup_path)
                result['success'] = True
                result['message'] = f"Backup {backup_name} deleted successfully"
            else:
                result['message'] = f"Backup {backup_name} not found"
                
        except Exception as e:
            logger.error(f"Error deleting backup {backup_name}: {e}")
            result['message'] = str(e)
        
        return result
    
    def cleanup_old_backups(self) -> Dict[str, Any]:
        """Remove backups older than the retention period."""
        result = {
            'success': True,
            'deleted_count': 0,
            'errors': [],
            'deleted_backups': []
        }
        
        try:
            cutoff_date = datetime.now() - timedelta(days=self.max_backup_age_days)
            backups = self.list_backups()
            
            for backup in backups:
                backup_date = datetime.fromisoformat(backup['timestamp'].replace('Z', '+00:00'))
                if backup_date < cutoff_date:
                    delete_result = self.delete_backup(backup['backup_name'])
                    if delete_result['success']:
                        result['deleted_count'] += 1
                        result['deleted_backups'].append(backup['backup_name'])
                    else:
                        result['errors'].append(f"Failed to delete {backup['backup_name']}: {delete_result['message']}")
                        
        except Exception as e:
            logger.error(f"Error during backup cleanup: {e}")
            result['success'] = False
            result['errors'].append(str(e))
        
        return result
    
    def get_backup_statistics(self) -> Dict[str, Any]:
        """Get backup statistics and information."""
        backups = self.list_backups()
        
        if not backups:
            return {
                'total_backups': 0,
                'total_size': 0,
                'oldest_backup': None,
                'newest_backup': None,
                'backup_dir': self.backup_dir,
                'retention_days': self.max_backup_age_days
            }
        
        total_size = sum(backup.get('size', 0) for backup in backups)
        
        return {
            'total_backups': len(backups),
            'total_size': total_size,
            'oldest_backup': backups[-1] if backups else None,
            'newest_backup': backups[0] if backups else None,
            'backup_dir': self.backup_dir,
            'retention_days': self.max_backup_age_days,
            'compressed_backups': sum(1 for backup in backups if backup.get('compressed', False)),
            'recent_backups': [backup for backup in backups[:5]]  # Last 5 backups
        }