"""
EmailBot Encryption Utilities
============================

Provides field-level encryption capabilities for sensitive model data with key management and rotation support.

This module implements:
- FieldEncryption class for model field encryption
- Key derivation and management utilities
- Batch encryption/decryption operations
- Key rotation support with migration
- Encryption metadata management
"""

import base64
import json
import time
import asyncio
import logging
from typing import Dict, List, Optional, Union, Any, Tuple
from datetime import datetime, timedelta
from cryptography.fernet import Fernet, MultiFernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import secrets

from app.core.security import SecurityManager, SecurityException, EncryptionError

logger = logging.getLogger(__name__)


class FieldEncryption:
    """
    Field-level encryption for database models with key rotation support.
    
    This class provides transparent encryption/decryption for sensitive model fields
    with support for key rotation, metadata tracking, and batch operations.
    """
    
    def __init__(self, security_manager: SecurityManager):
        """Initialize field encryption with security manager."""
        self.security_manager = security_manager
        self.key_store = {}
        self.encryption_metadata = {}
        self._init_key_management()
    
    def _init_key_management(self):
        """Initialize key management system."""
        try:
            # Initialize primary encryption key
            self.current_key_id = "primary"
            self.key_store[self.current_key_id] = {
                "fernet": self.security_manager.fernet,
                "created_at": datetime.utcnow().isoformat(),
                "active": True,
                "version": 1
            }
            
            logger.info("Field encryption key management initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize key management: {str(e)}")
            raise EncryptionError(f"Key management initialization failed: {str(e)}")
    
    def encrypt_field(self, field_name: str, field_value: Any, 
                     model_id: str = None, metadata: Dict = None) -> Dict[str, Any]:
        """
        Encrypt a model field with metadata tracking.
        
        Args:
            field_name: Name of the field being encrypted
            field_value: Value to encrypt
            model_id: Optional model instance ID for tracking
            metadata: Additional metadata to store
            
        Returns:
            Dict containing encrypted data and metadata
            
        Raises:
            EncryptionError: If encryption fails
        """
        try:
            # Convert field value to string for encryption
            if field_value is None:
                return {
                    "encrypted_value": None,
                    "encryption_metadata": None
                }
            
            # Prepare value for encryption
            if isinstance(field_value, (dict, list)):
                value_string = json.dumps(field_value, default=str)
            else:
                value_string = str(field_value)
            
            # Encrypt the value
            encrypted_value = self.security_manager.encrypt_data(value_string)
            
            # Create encryption metadata
            encryption_metadata = {
                "field_name": field_name,
                "key_id": self.current_key_id,
                "encryption_timestamp": datetime.utcnow().isoformat(),
                "data_type": type(field_value).__name__,
                "encrypted_length": len(encrypted_value),
                "original_length": len(value_string)
            }
            
            # Add custom metadata
            if metadata:
                encryption_metadata.update(metadata)
            
            # Store metadata for tracking
            metadata_key = f"{model_id}:{field_name}" if model_id else field_name
            self.encryption_metadata[metadata_key] = encryption_metadata
            
            # Log encryption event
            logger.info(f"Field '{field_name}' encrypted successfully")
            
            return {
                "encrypted_value": encrypted_value,
                "encryption_metadata": encryption_metadata
            }
            
        except Exception as e:
            logger.error(f"Field encryption failed for '{field_name}': {str(e)}")
            raise EncryptionError(f"Failed to encrypt field '{field_name}': {str(e)}")
    
    def decrypt_field(self, encrypted_data: Dict[str, Any], 
                     expected_type: type = str) -> Any:
        """
        Decrypt a model field using stored metadata.
        
        Args:
            encrypted_data: Dict containing encrypted value and metadata
            expected_type: Expected type of decrypted data
            
        Returns:
            Decrypted field value in original type
            
        Raises:
            EncryptionError: If decryption fails
        """
        try:
            if encrypted_data["encrypted_value"] is None:
                return None
            
            encrypted_value = encrypted_data["encrypted_value"]
            metadata = encrypted_data["encryption_metadata"]
            
            # Get the encryption key used
            key_id = metadata.get("key_id", self.current_key_id)
            if key_id not in self.key_store:
                raise EncryptionError(f"Encryption key '{key_id}' not found")
            
            # Decrypt using the appropriate key
            fernet = self.key_store[key_id]["fernet"]
            decrypted_value = self.security_manager.decrypt_data(encrypted_value)
            
            # Convert to expected type
            original_type = metadata.get("data_type", "str")
            
            if expected_type == dict or original_type in ["dict", "list"]:
                result = json.loads(decrypted_value)
            elif expected_type == int:
                result = int(decrypted_value)
            elif expected_type == float:
                result = float(decrypted_value)
            elif expected_type == bool:
                result = decrypted_value.lower() in ('true', '1', 'yes')
            else:
                result = decrypted_value
            
            # Log decryption event
            field_name = metadata.get("field_name", "unknown")
            logger.info(f"Field '{field_name}' decrypted successfully")
            
            return result
            
        except Exception as e:
            logger.error(f"Field decryption failed: {str(e)}")
            raise EncryptionError(f"Failed to decrypt field: {str(e)}")
    
    def encrypt_multiple_fields(self, field_data: Dict[str, Any], 
                               model_id: str = None) -> Dict[str, Dict[str, Any]]:
        """
        Encrypt multiple fields in batch.
        
        Args:
            field_data: Dict of field_name -> field_value
            model_id: Optional model instance ID
            
        Returns:
            Dict of field_name -> encrypted_data
        """
        encrypted_fields = {}
        
        for field_name, field_value in field_data.items():
            try:
                encrypted_fields[field_name] = self.encrypt_field(
                    field_name, field_value, model_id
                )
            except Exception as e:
                logger.error(f"Batch encryption failed for field '{field_name}': {str(e)}")
                encrypted_fields[field_name] = {
                    "encrypted_value": None,
                    "encryption_metadata": {"error": str(e)}
                }
        
        return encrypted_fields
    
    def decrypt_multiple_fields(self, encrypted_fields: Dict[str, Dict[str, Any]], 
                               type_map: Dict[str, type] = None) -> Dict[str, Any]:
        """
        Decrypt multiple fields in batch.
        
        Args:
            encrypted_fields: Dict of field_name -> encrypted_data
            type_map: Optional mapping of field_name -> expected_type
            
        Returns:
            Dict of field_name -> decrypted_value
        """
        decrypted_fields = {}
        type_map = type_map or {}
        
        for field_name, encrypted_data in encrypted_fields.items():
            try:
                expected_type = type_map.get(field_name, str)
                decrypted_fields[field_name] = self.decrypt_field(
                    encrypted_data, expected_type
                )
            except Exception as e:
                logger.error(f"Batch decryption failed for field '{field_name}': {str(e)}")
                decrypted_fields[field_name] = None
        
        return decrypted_fields
    
    # ===== KEY MANAGEMENT =====
    
    def rotate_encryption_key(self, new_key: str = None) -> str:
        """
        Rotate encryption key while maintaining ability to decrypt old data.
        
        Args:
            new_key: Optional new encryption key (generated if not provided)
            
        Returns:
            New key ID
        """
        try:
            # Generate new key if not provided
            if new_key is None:
                new_key = Fernet.generate_key()
            elif isinstance(new_key, str):
                new_key = new_key.encode()
            
            # Create new key version
            new_key_id = f"key_{int(time.time())}"
            self.key_store[new_key_id] = {
                "fernet": Fernet(new_key),
                "created_at": datetime.utcnow().isoformat(),
                "active": True,
                "version": len(self.key_store) + 1
            }
            
            # Mark old key as inactive
            if self.current_key_id in self.key_store:
                self.key_store[self.current_key_id]["active"] = False
            
            # Update current key
            self.current_key_id = new_key_id
            
            logger.info(f"Encryption key rotated successfully - new key ID: {new_key_id}")
            
            return new_key_id
            
        except Exception as e:
            logger.error(f"Key rotation failed: {str(e)}")
            raise EncryptionError(f"Failed to rotate encryption key: {str(e)}")
    
    def migrate_encrypted_data(self, old_encrypted_data: Dict[str, Any], 
                              target_key_id: str = None) -> Dict[str, Any]:
        """
        Migrate encrypted data to use a new encryption key.
        
        Args:
            old_encrypted_data: Existing encrypted data
            target_key_id: Target key ID (uses current if not specified)
            
        Returns:
            Re-encrypted data with new key
        """
        try:
            target_key_id = target_key_id or self.current_key_id
            
            # Decrypt with old key
            decrypted_value = self.decrypt_field(old_encrypted_data)
            
            # Get field metadata
            old_metadata = old_encrypted_data["encryption_metadata"]
            field_name = old_metadata.get("field_name", "migrated_field")
            
            # Re-encrypt with new key
            old_key_id = self.current_key_id
            self.current_key_id = target_key_id
            
            try:
                new_encrypted_data = self.encrypt_field(field_name, decrypted_value)
                
                # Add migration metadata
                new_encrypted_data["encryption_metadata"]["migration"] = {
                    "migrated_from": old_metadata.get("key_id"),
                    "migrated_at": datetime.utcnow().isoformat(),
                    "migration_reason": "key_rotation"
                }
                
                return new_encrypted_data
                
            finally:
                # Restore current key ID
                self.current_key_id = old_key_id
            
        except Exception as e:
            logger.error(f"Data migration failed: {str(e)}")
            raise EncryptionError(f"Failed to migrate encrypted data: {str(e)}")
    
    async def batch_migrate_encrypted_data(self, encrypted_data_list: List[Dict[str, Any]], 
                                          target_key_id: str = None, 
                                          batch_size: int = 100) -> List[Dict[str, Any]]:
        """
        Migrate multiple encrypted data items in batches.
        
        Args:
            encrypted_data_list: List of encrypted data to migrate
            target_key_id: Target key ID
            batch_size: Number of items to process per batch
            
        Returns:
            List of migrated encrypted data
        """
        migrated_data = []
        
        for i in range(0, len(encrypted_data_list), batch_size):
            batch = encrypted_data_list[i:i + batch_size]
            
            # Process batch
            batch_results = []
            for encrypted_data in batch:
                try:
                    migrated_item = self.migrate_encrypted_data(encrypted_data, target_key_id)
                    batch_results.append(migrated_item)
                except Exception as e:
                    logger.error(f"Batch migration failed for item: {str(e)}")
                    batch_results.append(encrypted_data)  # Keep original on failure
            
            migrated_data.extend(batch_results)
            
            # Small delay between batches to prevent overwhelming the system
            if i + batch_size < len(encrypted_data_list):
                await asyncio.sleep(0.1)
        
        logger.info(f"Batch migration completed - {len(migrated_data)} items processed")
        
        return migrated_data
    
    # ===== UTILITY METHODS =====
    
    def get_encryption_metadata(self, model_id: str = None, field_name: str = None) -> Dict[str, Any]:
        """Get encryption metadata for tracking and auditing."""
        if model_id and field_name:
            metadata_key = f"{model_id}:{field_name}"
            return self.encryption_metadata.get(metadata_key, {})
        
        # Return all metadata if no specific field requested
        return dict(self.encryption_metadata)
    
    def get_key_information(self) -> Dict[str, Any]:
        """Get information about encryption keys."""
        key_info = {
            "current_key_id": self.current_key_id,
            "total_keys": len(self.key_store),
            "keys": {}
        }
        
        for key_id, key_data in self.key_store.items():
            key_info["keys"][key_id] = {
                "created_at": key_data["created_at"],
                "active": key_data["active"],
                "version": key_data["version"]
            }
        
        return key_info
    
    def validate_encrypted_data(self, encrypted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate encrypted data structure and metadata.
        
        Args:
            encrypted_data: Encrypted data to validate
            
        Returns:
            Validation results
        """
        validation = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Check required fields
        if "encrypted_value" not in encrypted_data:
            validation["valid"] = False
            validation["errors"].append("Missing 'encrypted_value' field")
        
        if "encryption_metadata" not in encrypted_data:
            validation["valid"] = False
            validation["errors"].append("Missing 'encryption_metadata' field")
        
        if not validation["valid"]:
            return validation
        
        metadata = encrypted_data["encryption_metadata"]
        
        # Check metadata fields
        required_metadata = ["field_name", "key_id", "encryption_timestamp", "data_type"]
        for field in required_metadata:
            if field not in metadata:
                validation["errors"].append(f"Missing metadata field: {field}")
        
        # Check if key exists
        key_id = metadata.get("key_id")
        if key_id and key_id not in self.key_store:
            validation["warnings"].append(f"Encryption key '{key_id}' not found in key store")
        
        # Check timestamp validity
        timestamp = metadata.get("encryption_timestamp")
        if timestamp:
            try:
                parsed_timestamp = datetime.fromisoformat(timestamp)
                if parsed_timestamp > datetime.utcnow():
                    validation["warnings"].append("Encryption timestamp is in the future")
            except ValueError:
                validation["errors"].append("Invalid encryption timestamp format")
        
        if validation["errors"]:
            validation["valid"] = False
        
        return validation


class EncryptionKeyManager:
    """Manages encryption keys with secure storage and rotation."""
    
    def __init__(self, master_key: str):
        """Initialize key manager with master key."""
        self.master_key = master_key
        self.key_derivations = {}
        self._init_master_key()
    
    def _init_master_key(self):
        """Initialize master key for key derivation."""
        try:
            # Validate master key
            if len(self.master_key) < 32:
                raise EncryptionError("Master key must be at least 32 characters")
            
            # Create master Fernet instance
            master_key_bytes = hashlib.sha256(self.master_key.encode()).digest()
            self.master_fernet = Fernet(base64.urlsafe_b64encode(master_key_bytes))
            
            logger.info("Encryption key manager initialized")
            
        except Exception as e:
            logger.error(f"Master key initialization failed: {str(e)}")
            raise EncryptionError(f"Failed to initialize key manager: {str(e)}")
    
    def derive_key(self, purpose: str, salt: str = None) -> str:
        """
        Derive encryption key for specific purpose.
        
        Args:
            purpose: Purpose identifier (e.g., 'email_content', 'user_data')
            salt: Optional salt (generated if not provided)
            
        Returns:
            Derived encryption key
        """
        if salt is None:
            salt = secrets.token_hex(16)
        
        # Create derived key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt.encode(),
            iterations=100000,
        )
        
        derived_key = base64.urlsafe_b64encode(kdf.derive(f"{self.master_key}:{purpose}".encode()))
        
        # Store derivation info
        self.key_derivations[purpose] = {
            "salt": salt,
            "created_at": datetime.utcnow().isoformat(),
            "key": derived_key.decode()
        }
        
        return derived_key.decode()
    
    def get_derived_key(self, purpose: str) -> Optional[str]:
        """Get previously derived key for purpose."""
        derivation = self.key_derivations.get(purpose)
        return derivation["key"] if derivation else None
    
    def rotate_derived_key(self, purpose: str) -> str:
        """Rotate key for specific purpose."""
        new_salt = secrets.token_hex(16)
        return self.derive_key(purpose, new_salt)


# Utility functions
def create_field_encryption(encryption_key: str = None) -> FieldEncryption:
    """Create field encryption instance with security manager."""
    from app.core.security import create_security_manager
    
    security_manager = create_security_manager(encryption_key)
    return FieldEncryption(security_manager)


def encrypt_sensitive_fields(model_data: Dict[str, Any], 
                           sensitive_fields: List[str],
                           encryption_key: str = None) -> Dict[str, Any]:
    """
    Utility function to encrypt sensitive fields in model data.
    
    Args:
        model_data: Dictionary containing model data
        sensitive_fields: List of field names to encrypt
        encryption_key: Optional encryption key
        
    Returns:
        Model data with encrypted sensitive fields
    """
    field_encryption = create_field_encryption(encryption_key)
    
    # Extract sensitive fields for encryption
    fields_to_encrypt = {
        field: model_data[field] 
        for field in sensitive_fields 
        if field in model_data
    }
    
    # Encrypt fields
    encrypted_fields = field_encryption.encrypt_multiple_fields(fields_to_encrypt)
    
    # Replace original fields with encrypted versions
    encrypted_model_data = model_data.copy()
    for field_name, encrypted_data in encrypted_fields.items():
        encrypted_model_data[f"{field_name}_encrypted"] = encrypted_data
        # Optionally remove original field
        if field_name in encrypted_model_data:
            del encrypted_model_data[field_name]
    
    return encrypted_model_data


def decrypt_sensitive_fields(model_data: Dict[str, Any], 
                           sensitive_fields: List[str],
                           encryption_key: str = None) -> Dict[str, Any]:
    """
    Utility function to decrypt sensitive fields in model data.
    
    Args:
        model_data: Dictionary containing model data with encrypted fields
        sensitive_fields: List of field names to decrypt
        encryption_key: Optional encryption key
        
    Returns:
        Model data with decrypted sensitive fields
    """
    field_encryption = create_field_encryption(encryption_key)
    
    # Extract encrypted fields for decryption
    fields_to_decrypt = {
        field: model_data[f"{field}_encrypted"]
        for field in sensitive_fields
        if f"{field}_encrypted" in model_data
    }
    
    # Decrypt fields
    decrypted_fields = field_encryption.decrypt_multiple_fields(fields_to_decrypt)
    
    # Replace encrypted fields with decrypted versions
    decrypted_model_data = model_data.copy()
    for field_name, decrypted_value in decrypted_fields.items():
        decrypted_model_data[field_name] = decrypted_value
        # Remove encrypted field
        encrypted_field_name = f"{field_name}_encrypted"
        if encrypted_field_name in decrypted_model_data:
            del decrypted_model_data[encrypted_field_name]
    
    return decrypted_model_data 