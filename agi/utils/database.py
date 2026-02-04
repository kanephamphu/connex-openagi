
import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

class DatabaseManager:
    """
    Manages the local SQLite database for AGI memory and metadata.
    """
    
    def __init__(self, db_path: str = "agi_memory.db"):
        self.db_path = db_path
        self._init_db()
        
    def _get_connection(self):
        return sqlite3.connect(self.db_path)
        
    def _init_db(self):
        """Initialize core tables."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Perceptions Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS perceptions (
                name TEXT PRIMARY KEY,
                description TEXT,
                category TEXT,
                sub_category TEXT,
                type TEXT,
                version TEXT,
                enabled BOOLEAN DEFAULT 1,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                embedding BLOB
            )
        """)
        
        # System Config Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_config (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Check if embedding column exists (migration)
        cursor.execute("PRAGMA table_info(perceptions)")
        columns = [info[1] for info in cursor.fetchall()]
        if "embedding" not in columns:
            cursor.execute("ALTER TABLE perceptions ADD COLUMN embedding BLOB")
        if "category" not in columns:
            cursor.execute("ALTER TABLE perceptions ADD COLUMN category TEXT")
        if "sub_category" not in columns:
            cursor.execute("ALTER TABLE perceptions ADD COLUMN sub_category TEXT")
            
        conn.commit()
        conn.close()

    # ... [Existing Perception Methods] ...
    
    # --- System Config Methods ---

    def set_config(self, key: str, value: Any):
        """Set a configuration value."""
        import json
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Store as JSON string to preserve types (simple types)
        val_str = json.dumps(value)
        
        cursor.execute("""
            INSERT INTO system_config (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(key) DO UPDATE SET
                value=excluded.value,
                updated_at=CURRENT_TIMESTAMP
        """, (key, val_str))
        
        conn.commit()
        conn.close()

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        import json
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM system_config WHERE key=?", (key,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            try:
                return json.loads(row[0])
            except:
                return row[0]
        return default

    def get_all_config(self) -> Dict[str, Any]:
        """Get all configuration values."""
        import json
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM system_config")
        rows = cursor.fetchall()
        conn.close()
        
        config = {}
        for key, val_str in rows:
            try:
                config[key] = json.loads(val_str)
            except:
                config[key] = val_str
        return config
        
    def register_perception(self, name: str, description: str, type: str, version: str, category: str = "general", sub_category: str = "general", embedding: Optional[List[float]] = None):
        """Upsert a perception module."""
        import json
        conn = self._get_connection()
        cursor = conn.cursor()
        
        emb_json = json.dumps(embedding) if embedding else None
        
        cursor.execute("""
            INSERT INTO perceptions (name, description, category, sub_category, type, version, last_updated, embedding)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
            ON CONFLICT(name) DO UPDATE SET
                description=excluded.description,
                category=excluded.category,
                sub_category=excluded.sub_category,
                type=excluded.type,
                version=excluded.version,
                last_updated=CURRENT_TIMESTAMP,
                embedding=COALESCE(excluded.embedding, perceptions.embedding)
        """, (name, description, category, sub_category, type, version, emb_json))
        
        conn.commit()
        conn.close()
        
    def get_perception_embedding(self, name: str) -> Optional[List[float]]:
        import json
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT embedding FROM perceptions WHERE name=?", (name,))
        row = cursor.fetchone()
        conn.close()
        
        if row and row[0]:
            return json.loads(row[0])
        return None

    def find_similar_perceptions(self, query_vec: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        """
        Find perceptions with similar embeddings using Cosine Similarity.
        """
        import json
        import math
        
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        # Fetch all enabled perceptions that have embeddings
        cursor.execute("SELECT * FROM perceptions WHERE enabled=1 AND embedding IS NOT NULL")
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        
        # Dot product of query vector
        query_mag = math.sqrt(sum(a*a for a in query_vec))
        if query_mag == 0:
            return []
            
        for row in rows:
            try:
                vec = json.loads(row['embedding'])
                if not vec or len(vec) != len(query_vec):
                    continue
                    
                dot_product = sum(a*b for a, b in zip(query_vec, vec))
                vec_mag = math.sqrt(sum(a*a for a in vec))
                
                if vec_mag == 0:
                    similarity = 0
                else:
                    similarity = dot_product / (query_mag * vec_mag)
                
                data = dict(row)
                data['similarity'] = similarity
                results.append((similarity, data))
            except:
                continue
                
        # Sort by similarity desc
        results.sort(key=lambda x: x[0], reverse=True)
        
        # Return top N
        return [item[1] for item in results[:limit]]

    def search_perceptions(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for perceptions matching a keyword/query in their name or description.
        Simple LIKE matching for now.
        """
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Simple keyword match
        # If query is generic, we might want to return all?
        # For now, let's just do a broad LIKE search
        
        sql_query = f"%{query}%"
        cursor.execute("""
            SELECT * FROM perceptions 
            WHERE enabled=1 AND (description LIKE ? OR name LIKE ?)
        """, (sql_query, sql_query))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]

    def get_all_perceptions(self) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM perceptions WHERE enabled=1")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
