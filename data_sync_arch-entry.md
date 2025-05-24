# PDF Invoice Generator - Data Synchronization Architecture

## 1. Data Synchronization Strategy

### Architecture Overview
The system implements a **hybrid online/offline architecture** with the following components:

- **Local Storage Layer**: SQLite database for offline transactions and settings
- **Sync Queue Manager**: Handles queuing and transmission of pending operations
- **Redis Cache**: Provides fast access to frequently used data
- **PostgreSQL Database**: Central source of truth for all transaction data

### Offline Data Storage Design

```sql
# Local SQLite Schema
CREATE TABLE transactions (
    id TEXT PRIMARY KEY,  -- UUID4 for global uniqueness
    invoice_number TEXT,
    client_data TEXT,     -- JSON blob
    line_items TEXT,      -- JSON blob
    total_amount DECIMAL(10,2),
    created_at TIMESTAMP,
    modified_at TIMESTAMP,
    sync_status TEXT DEFAULT 'pending',  -- pending, synced, conflict
    checksum TEXT,        -- SHA256 hash for integrity
    version INTEGER DEFAULT 1
);

CREATE TABLE sync_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id TEXT,
    operation TEXT,       -- insert, update, delete
    payload TEXT,         -- JSON data
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP,
    FOREIGN KEY (transaction_id) REFERENCES transactions(id)
);

CREATE TABLE app_settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    sync_required BOOLEAN DEFAULT 0
);
```

### Synchronization Flow

1. **Online Operations**: Direct write to PostgreSQL + Redis cache update
2. **Offline Operations**: Write to local SQLite + add to sync queue
3. **Connection Recovery**: Process sync queue in chronological order

## 2. Conflict Resolution

### Timestamping and Versioning Strategy

```python
import uuid
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional

class ConflictResolver:
    def __init__(self):
        self.resolution_strategies = {
            'last_write_wins': self._last_write_wins,
            'merge_fields': self._merge_fields,
            'user_prompt': self._user_prompt
        }
    
    def resolve_conflict(self, local_record: Dict, remote_record: Dict, 
                        strategy: str = 'last_write_wins') -> Dict:
        """
        Resolve conflicts between local and remote records
        """
        if strategy in self.resolution_strategies:
            return self.resolution_strategies[strategy](local_record, remote_record)
        
        raise ValueError(f"Unknown conflict resolution strategy: {strategy}")
    
    def _last_write_wins(self, local: Dict, remote: Dict) -> Dict:
        """Use the record with the most recent modification timestamp"""
        local_time = datetime.fromisoformat(local['modified_at'])
        remote_time = datetime.fromisoformat(remote['modified_at'])
        
        winner = local if local_time > remote_time else remote
        winner['version'] = max(local['version'], remote['version']) + 1
        return winner
    
    def _merge_fields(self, local: Dict, remote: Dict) -> Dict:
        """Merge non-conflicting fields, use timestamps for conflicts"""
        merged = remote.copy()
        
        # Define fields that can be safely merged
        mergeable_fields = ['line_items', 'client_data']
        
        for field in mergeable_fields:
            if field in local and field in remote:
                # Custom merge logic per field type
                if field == 'line_items':
                    merged[field] = self._merge_line_items(
                        local[field], remote[field]
                    )
        
        merged['version'] = max(local['version'], remote['version']) + 1
        merged['modified_at'] = datetime.utcnow().isoformat()
        return merged
```

### Optimistic Concurrency Control

```python
class OptimisticConcurrencyManager:
    def __init__(self, db_connection):
        self.db = db_connection
    
    def update_with_version_check(self, transaction_id: str, 
                                 updated_data: Dict, 
                                 expected_version: int) -> bool:
        """
        Update record only if version matches expected value
        Returns True if successful, False if version conflict
        """
        query = """
        UPDATE transactions 
        SET invoice_number = ?, client_data = ?, line_items = ?, 
            total_amount = ?, modified_at = ?, version = version + 1,
            checksum = ?
        WHERE id = ? AND version = ?
        """
        
        checksum = self._calculate_checksum(updated_data)
        
        cursor = self.db.execute(query, (
            updated_data['invoice_number'],
            updated_data['client_data'],
            updated_data['line_items'],
            updated_data['total_amount'],
            datetime.utcnow().isoformat(),
            checksum,
            transaction_id,
            expected_version
        ))
        
        return cursor.rowcount > 0
```

## 3. Data Integrity and Duplication Prevention

### Transaction Idempotency

```python
import json
from hashlib import sha256

class TransactionManager:
    def __init__(self, local_db, remote_db, redis_client):
        self.local_db = local_db
        self.remote_db = remote_db
        self.redis = redis_client
    
    def create_transaction(self, transaction_data: Dict) -> str:
        """Create idempotent transaction with unique ID"""
        transaction_id = str(uuid.uuid4())
        transaction_data['id'] = transaction_id
        transaction_data['created_at'] = datetime.utcnow().isoformat()
        transaction_data['modified_at'] = transaction_data['created_at']
        transaction_data['checksum'] = self._calculate_checksum(transaction_data)
        
        # Store locally first
        self._store_local_transaction(transaction_data)
        
        # Try to sync immediately if online
        if self._is_online():
            self._sync_transaction(transaction_id)
        
        return transaction_id
    
    def _calculate_checksum(self, data: Dict) -> str:
        """Generate SHA256 checksum for data integrity verification"""
        # Create a deterministic string representation
        relevant_fields = ['invoice_number', 'client_data', 'line_items', 'total_amount']
        checksum_data = {k: data.get(k) for k in relevant_fields}
        
        json_str = json.dumps(checksum_data, sort_keys=True, separators=(',', ':'))
        return sha256(json_str.encode()).hexdigest()
    
    def _verify_integrity(self, transaction_data: Dict) -> bool:
        """Verify transaction data integrity using checksum"""
        stored_checksum = transaction_data.pop('checksum', '')
        calculated_checksum = self._calculate_checksum(transaction_data)
        transaction_data['checksum'] = stored_checksum
        
        return stored_checksum == calculated_checksum
```

### Duplicate Detection and Merging

```python
class DuplicateDetector:
    def __init__(self):
        self.similarity_threshold = 0.85
    
    def detect_duplicates(self, new_transaction: Dict, 
                         existing_transactions: list) -> Optional[Dict]:
        """
        Detect potential duplicates using multiple criteria
        """
        for existing in existing_transactions:
            similarity_score = self._calculate_similarity(new_transaction, existing)
            
            if similarity_score > self.similarity_threshold:
                return {
                    'duplicate_of': existing['id'],
                    'similarity_score': similarity_score,
                    'suggested_action': 'merge' if similarity_score < 0.95 else 'skip'
                }
        
        return None
    
    def _calculate_similarity(self, trans1: Dict, trans2: Dict) -> float:
        """Calculate similarity score between two transactions"""
        # Compare key fields
        score = 0.0
        weights = {
            'invoice_number': 0.3,
            'total_amount': 0.25,
            'client_data': 0.25,
            'created_at': 0.2
        }
        
        for field, weight in weights.items():
            if field in trans1 and field in trans2:
                field_similarity = self._field_similarity(trans1[field], trans2[field], field)
                score += field_similarity * weight
        
        return score
```

## 4. Local Data Storage

### SQLite vs JSON Comparison

| Aspect | SQLite | JSON Files |
|--------|--------|------------|
| **Query Performance** | Excellent (SQL queries) | Poor (full file reads) |
| **Data Integrity** | Built-in ACID properties | Manual validation required |
| **Concurrent Access** | Good (built-in locking) | Poor (file locking issues) |
| **Storage Efficiency** | Excellent (binary format) | Good (text compression) |
| **Backup/Recovery** | Excellent (atomic operations) | Fair (file-level operations) |
| **Learning Curve** | Moderate (SQL knowledge) | Low (simple file operations) |

**Recommendation**: Use **SQLite** for its superior query performance, data integrity, and concurrent access handling.

### SQLite Implementation

```python
import sqlite3
from contextlib import contextmanager
from typing import Generator

class LocalDataStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize SQLite database with required tables"""
        with self.get_connection() as conn:
            conn.executescript('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id TEXT PRIMARY KEY,
                    invoice_number TEXT,
                    client_data TEXT,
                    line_items TEXT,
                    total_amount DECIMAL(10,2),
                    created_at TIMESTAMP,
                    modified_at TIMESTAMP,
                    sync_status TEXT DEFAULT 'pending',
                    checksum TEXT,
                    version INTEGER DEFAULT 1
                );
                
                CREATE INDEX IF NOT EXISTS idx_sync_status ON transactions(sync_status);
                CREATE INDEX IF NOT EXISTS idx_created_at ON transactions(created_at);
                
                CREATE TABLE IF NOT EXISTS app_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    sync_required BOOLEAN DEFAULT 0
                );
            ''')
    
    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
```

## 5. Technical Implementation

### Core Synchronization Engine

```python
import asyncio
import aiohttp
import json
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum

class SyncStatus(Enum):
    PENDING = "pending"
    SYNCING = "syncing"
    SYNCED = "synced"
    CONFLICT = "conflict"
    ERROR = "error"

@dataclass
class SyncResult:
    success: bool
    transaction_id: str
    status: SyncStatus
    error_message: Optional[str] = None
    conflict_data: Optional[Dict] = None

class SynchronizationEngine:
    def __init__(self, local_store: LocalDataStore, 
                 api_base_url: str, auth_token: str):
        self.local_store = local_store
        self.api_base_url = api_base_url
        self.auth_token = auth_token
        self.max_retries = 3
        self.batch_size = 10
    
    async def sync_pending_transactions(self) -> List[SyncResult]:
        """Synchronize all pending transactions with remote database"""
        pending_transactions = self._get_pending_transactions()
        results = []
        
        # Process transactions in batches
        for i in range(0, len(pending_transactions), self.batch_size):
            batch = pending_transactions[i:i + self.batch_size]
            batch_results = await self._sync_batch(batch)
            results.extend(batch_results)
        
        return results
    
    async def _sync_batch(self, transactions: List[Dict]) -> List[SyncResult]:
        """Synchronize a batch of transactions"""
        tasks = []
        
        for transaction in transactions:
            task = asyncio.create_task(
                self._sync_single_transaction(transaction)
            )
            tasks.append(task)
        
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _sync_single_transaction(self, transaction: Dict) -> SyncResult:
        """Synchronize a single transaction with retry logic"""
        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    headers = {
                        'Authorization': f'Bearer {self.auth_token}',
                        'Content-Type': 'application/json'
                    }
                    
                    # Check if transaction exists remotely
                    remote_transaction = await self._fetch_remote_transaction(
                        session, transaction['id']
                    )
                    
                    if remote_transaction:
                        # Handle potential conflict
                        return await self._handle_conflict(
                            transaction, remote_transaction
                        )
                    else:
                        # Create new transaction remotely
                        return await self._create_remote_transaction(
                            session, transaction, headers
                        )
                        
            except Exception as e:
                if attempt == self.max_retries - 1:
                    return SyncResult(
                        success=False,
                        transaction_id=transaction['id'],
                        status=SyncStatus.ERROR,
                        error_message=str(e)
                    )
                
                # Exponential backoff
                await asyncio.sleep(2 ** attempt)
        
        return SyncResult(
            success=False,
            transaction_id=transaction['id'],
            status=SyncStatus.ERROR,
            error_message="Max retries exceeded"
        )
    
    def _get_pending_transactions(self) -> List[Dict]:
        """Retrieve all pending transactions from local storage"""
        with self.local_store.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM transactions WHERE sync_status = ?",
                (SyncStatus.PENDING.value,)
            )
            return [dict(row) for row in cursor.fetchall()]
```

### Settings Management

```python
class SettingsManager:
    def __init__(self, local_store: LocalDataStore, redis_client):
        self.local_store = local_store
        self.redis = redis_client
        self.cache_ttl = 3600  # 1 hour
    
    def get_setting(self, key: str, default=None):
        """Retrieve setting with Redis caching"""
        # Try Redis cache first
        cached_value = self.redis.get(f"setting:{key}")
        if cached_value:
            return json.loads(cached_value)
        
        # Fall back to local storage
        with self.local_store.get_connection() as conn:
            cursor = conn.execute(
                "SELECT value FROM app_settings WHERE key = ?", (key,)
            )
            row = cursor.fetchone()
            
            if row:
                value = json.loads(row['value'])
                # Cache for future use
                self.redis.setex(
                    f"setting:{key}", 
                    self.cache_ttl, 
                    json.dumps(value)
                )
                return value
        
        return default
    
    def set_setting(self, key: str, value, sync_required: bool = True):
        """Store setting locally and mark for sync if needed"""
        json_value = json.dumps(value)
        
        with self.local_store.get_connection() as conn:
            conn.execute('''
                INSERT OR REPLACE INTO app_settings (key, value, sync_required)
                VALUES (?, ?, ?)
            ''', (key, json_value, sync_required))
        
        # Update cache
        self.redis.setex(
            f"setting:{key}", 
            self.cache_ttl, 
            json_value
        )
        
        if sync_required and self._is_online():
            asyncio.create_task(self._sync_setting(key, value))
```

## 6. Additional Considerations

### Security Measures

#### Data Encryption
```python
from cryptography.fernet import Fernet
import base64

class DataEncryption:
    def __init__(self, encryption_key: bytes):
        self.cipher = Fernet(encryption_key)
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data for storage"""
        encrypted_data = self.cipher.encrypt(data.encode())
        return base64.b64encode(encrypted_data).decode()
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        decoded_data = base64.b64decode(encrypted_data.encode())
        return self.cipher.decrypt(decoded_data).decode()
```

#### API Authentication
```python
import jwt
from datetime import datetime, timedelta

class APIAuthenticator:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.token_expiry = 24  # hours
    
    def generate_token(self, user_id: str) -> str:
        """Generate JWT token for API authentication"""
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(hours=self.token_expiry),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def validate_token(self, token: str) -> Optional[Dict]:
        """Validate JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
```

### Performance Optimization

#### Database Indexing Strategy
```sql
-- PostgreSQL indexes for optimal performance
CREATE INDEX CONCURRENTLY idx_transactions_created_at 
ON transactions(created_at DESC);

CREATE INDEX CONCURRENTLY idx_transactions_client_id 
ON transactions(client_id) WHERE client_id IS NOT NULL;

CREATE INDEX CONCURRENTLY idx_transactions_status 
ON transactions(sync_status) WHERE sync_status != 'synced';

-- Partial index for pending synchronization
CREATE INDEX CONCURRENTLY idx_transactions_pending_sync 
ON transactions(created_at) WHERE sync_status = 'pending';
```

#### Redis Caching Strategy
```python
class CacheManager:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.cache_policies = {
            'transactions': {'ttl': 1800, 'prefix': 'txn'},
            'settings': {'ttl': 3600, 'prefix': 'set'},
            'clients': {'ttl': 7200, 'prefix': 'cli'}
        }
    
    def cache_transaction(self, transaction: Dict):
        """Cache transaction data with appropriate TTL"""
        policy = self.cache_policies['transactions']
        key = f"{policy['prefix']}:{transaction['id']}"
        
        self.redis.setex(
            key, 
            policy['ttl'], 
            json.dumps(transaction)
        )
    
    def get_cached_transaction(self, transaction_id: str) -> Optional[Dict]:
        """Retrieve cached transaction"""
        policy = self.cache_policies['transactions']
        key = f"{policy['prefix']}:{transaction_id}"
        
        cached_data = self.redis.get(key)
        return json.loads(cached_data) if cached_data else None
```

### Connection Monitoring
```python
import asyncio
import aiohttp
from typing import Callable

class ConnectionMonitor:
    def __init__(self, api_base_url: str, check_interval: int = 30):
        self.api_base_url = api_base_url
        self.check_interval = check_interval
        self.is_online = False
        self.callbacks = {'online': [], 'offline': []}
    
    def add_callback(self, event: str, callback: Callable):
        """Add callback for connection state changes"""
        if event in self.callbacks:
            self.callbacks[event].append(callback)
    
    async def start_monitoring(self):
        """Start connection monitoring loop"""
        while True:
            previous_state = self.is_online
            self.is_online = await self._check_connection()
            
            # Trigger callbacks on state change
            if previous_state != self.is_online:
                event = 'online' if self.is_online else 'offline'
                for callback in self.callbacks[event]:
                    try:
                        await callback()
                    except Exception as e:
                        print(f"Callback error: {e}")
            
            await asyncio.sleep(self.check_interval)
    
    async def _check_connection(self) -> bool:
        """Check if connection to remote server is available"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(f"{self.api_base_url}/health") as response:
                    return response.status == 200
        except:
            return False
```

## Implementation Checklist

- [ ] Set up SQLite local database with proper schema
- [ ] Implement transaction versioning and conflict resolution
- [ ] Create synchronization queue and batch processing
- [ ] Add data integrity validation with checksums
- [ ] Implement Redis caching layer
- [ ] Set up connection monitoring and offline detection
- [ ] Add encryption for sensitive data
- [ ] Create comprehensive error handling and logging
- [ ] Implement performance monitoring and optimization
- [ ] Add unit tests for critical synchronization logic

This architecture provides a robust foundation for your PDF invoice generator with reliable data synchronization, conflict resolution, and offline capabilities.