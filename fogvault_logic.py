"""
FogVault Logic Module
Handles encryption, fog node operations, MongoDB, AWS S3
"""

import os
import hashlib
import boto3
from pymongo import MongoClient
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from werkzeug.security import generate_password_hash, check_password_hash
from flask import send_file
from datetime import datetime
from bson.objectid import ObjectId
import io

class FogVaultLogic:
    def __init__(self):
        # MongoDB connection
        mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
        self.db = MongoClient(mongo_uri)['fogvault']
        self.users     = self.db['users']
        self.files     = self.db['files']
        self.audit_log = self.db['audit_log']
        self.cache     = {}  # Fog node local cache

        # AWS S3
        self.s3 = boto3.client(
            's3',
            aws_access_key_id     = os.getenv('AWS_ACCESS_KEY'),
            aws_secret_access_key = os.getenv('AWS_SECRET_KEY'),
            region_name           = os.getenv('AWS_REGION', 'us-east-1')
        )
        self.bucket = os.getenv('S3_BUCKET', 'fogvault-bucket')

    # ─────────────────────────────────────────
    # ENCRYPTION (AES-256)
    # ─────────────────────────────────────────
    def encrypt_file(self, data: bytes) -> tuple:
        """Encrypt file data using AES-256 CBC"""
        key = os.urandom(32)   # 256-bit key
        iv  = os.urandom(16)   # 128-bit IV
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        # Pad data to 16-byte boundary
        pad_len = 16 - (len(data) % 16)
        data += bytes([pad_len] * pad_len)
        encrypted = encryptor.update(data) + encryptor.finalize()
        return encrypted, key, iv

    def decrypt_file(self, encrypted_data: bytes, key: bytes, iv: bytes) -> bytes:
        """Decrypt file data using AES-256 CBC"""
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        data = decryptor.update(encrypted_data) + decryptor.finalize()
        pad_len = data[-1]
        return data[:-pad_len]

    def compute_hash(self, data: bytes) -> str:
        """Compute MD5 hash for integrity verification"""
        return hashlib.md5(data).hexdigest()

    # ─────────────────────────────────────────
    # USER MANAGEMENT
    # ─────────────────────────────────────────
    def register_user(self, username, password, email):
        if self.users.find_one({'username': username}):
            return {'success': False, 'message': 'Username already exists'}
        self.users.insert_one({
            'username': username,
            'password': generate_password_hash(password),
            'email': email,
            'role': 'user',
            'created_at': datetime.utcnow()
        })
        return {'success': True}

    def authenticate_user(self, username, password):
        user = self.users.find_one({'username': username})
        if user and check_password_hash(user['password'], password):
            return {'success': True, 'user_id': str(user['_id'])}
        return {'success': False}

    # ─────────────────────────────────────────
    # FILE OPERATIONS
    # ─────────────────────────────────────────
    def upload_file(self, user_id, filename, file_data):
        try:
            # Step 1: Compute hash for integrity
            file_hash = self.compute_hash(file_data)

            # Step 2: Encrypt at fog node (AES-256)
            encrypted_data, key, iv = self.encrypt_file(file_data)

            # Step 3: Cache at fog node
            cache_key = f"{user_id}_{filename}"
            self.cache[cache_key] = {'data': file_data, 'hash': file_hash}

            # Step 4: Upload encrypted file to AWS S3
            s3_key = f"{user_id}/{filename}"
            self.s3.put_object(
                Bucket=self.bucket,
                Key=s3_key,
                Body=encrypted_data
            )

            # Step 5: Store metadata in MongoDB
            self.files.insert_one({
                'user_id': user_id,
                'filename': filename,
                's3_key': s3_key,
                'encryption_key': key.hex(),
                'iv': iv.hex(),
                'hash': file_hash,
                'size': len(file_data),
                'uploaded_at': datetime.utcnow(),
                'status': 'active'
            })
            return {'success': True}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    def download_file(self, file_id, user_id):
        try:
            file_doc = self.files.find_one({'_id': ObjectId(file_id), 'user_id': user_id})
            if not file_doc:
                return {'success': False, 'message': 'File not found or access denied'}

            # Check fog cache first
            cache_key = f"{user_id}_{file_doc['filename']}"
            if cache_key in self.cache:
                file_data = self.cache[cache_key]['data']
            else:
                # Fetch from S3 and decrypt
                s3_obj = self.s3.get_object(Bucket=self.bucket, Key=file_doc['s3_key'])
                encrypted_data = s3_obj['Body'].read()
                key = bytes.fromhex(file_doc['encryption_key'])
                iv  = bytes.fromhex(file_doc['iv'])
                file_data = self.decrypt_file(encrypted_data, key, iv)

                # Verify integrity
                if self.compute_hash(file_data) != file_doc['hash']:
                    return {'success': False, 'message': 'File integrity check failed!'}

                # Cache for future use
                self.cache[cache_key] = {'data': file_data, 'hash': file_doc['hash']}

            response = send_file(
                io.BytesIO(file_data),
                download_name=file_doc['filename'],
                as_attachment=True
            )
            return {'success': True, 'response': response, 'filename': file_doc['filename']}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    def delete_file(self, file_id, user_id):
        try:
            file_doc = self.files.find_one({'_id': ObjectId(file_id), 'user_id': user_id})
            if not file_doc:
                return {'success': False}
            self.s3.delete_object(Bucket=self.bucket, Key=file_doc['s3_key'])
            self.files.delete_one({'_id': ObjectId(file_id)})
            cache_key = f"{user_id}_{file_doc['filename']}"
            self.cache.pop(cache_key, None)
            return {'success': True}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    def get_user_files(self, user_id):
        files = list(self.files.find({'user_id': user_id, 'status': 'active'}))
        for f in files:
            f['_id'] = str(f['_id'])
            f['size_kb'] = round(f['size'] / 1024, 2)
        return files

    # ─────────────────────────────────────────
    # AUDIT LOGGING
    # ─────────────────────────────────────────
    def log_action(self, user_id, action, filename, status):
        self.audit_log.insert_one({
            'user_id': user_id,
            'action': action,
            'filename': filename,
            'status': status,
            'timestamp': datetime.utcnow()
        })

    def get_audit_logs(self, user_id):
        logs = list(self.audit_log.find({'user_id': user_id}).sort('timestamp', -1).limit(50))
        for log in logs:
            log['_id'] = str(log['_id'])
        return logs

    # ─────────────────────────────────────────
    # CLOUD STATUS CHECK
    # ─────────────────────────────────────────
    def check_cloud_status(self):
        try:
            self.s3.head_bucket(Bucket=self.bucket)
            return 'online'
        except:
            return 'offline'
