import sqlite3
from datetime import datetime
from typing import Optional
from pathlib import Path
import json
import threading


class AuditLog:
    _instance: Optional["AuditLog"] = None
    _lock = threading.Lock()
    
    def __new__(cls, db_path: str = "jarvis_audit.db") -> "AuditLog":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._db_path = db_path
            cls._instance._init_db()
        return cls._instance
    
    def _init_db(self) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    user_id TEXT,
                    module TEXT NOT NULL,
                    action TEXT NOT NULL,
                    params TEXT,
                    status TEXT NOT NULL,
                    result TEXT,
                    ip_address TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    content TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    status TEXT DEFAULT 'active',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.commit()
    
    def log_action(
        self,
        module: str,
        action: str,
        status: str,
        user_id: Optional[str] = None,
        params: Optional[dict] = None,
        result: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> int:
        timestamp = datetime.now().isoformat()
        params_json = json.dumps(params) if params else None
        
        with self._lock:
            with sqlite3.connect(self._db_path) as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO audit_log 
                    (timestamp, user_id, module, action, params, status, result, ip_address)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (timestamp, user_id, module, action, params_json, status, result, ip_address)
                )
                conn.commit()
                return cursor.lastrowid
    
    def get_recent_logs(self, limit: int = 20) -> list[dict]:
        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT * FROM audit_log 
                ORDER BY timestamp DESC 
                LIMIT ?
                """,
                (limit,)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def add_note(self, content: str) -> int:
        timestamp = datetime.now().isoformat()
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO notes (timestamp, content) VALUES (?, ?)",
                (timestamp, content)
            )
            conn.commit()
            return cursor.lastrowid
    
    def get_notes(self, limit: int = 10) -> list[dict]:
        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM notes ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def create_project(self, name: str, description: Optional[str] = None) -> int:
        timestamp = datetime.now().isoformat()
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO projects (name, description, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                (name, description, timestamp, timestamp)
            )
            conn.commit()
            return cursor.lastrowid
    
    def get_projects(self, status: str = "active") -> list[dict]:
        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM projects WHERE status = ? ORDER BY updated_at DESC",
                (status,)
            )
            return [dict(row) for row in cursor.fetchall()]


audit_log = AuditLog()
