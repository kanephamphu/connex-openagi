"""
SQLite persistent storage for AGI skills and vectors.
"""
import sqlite3
import json
import os
import math
from typing import List, Dict, Any, Optional, Tuple

class SkillStore:
    """
    SQLite backend for skill persistence and semantic search.
    """
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()
        
    def _init_db(self):
        """Initialize database schema."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            # Skills table: metadata and full content
            conn.execute("""
                CREATE TABLE IF NOT EXISTS skills (
                    name TEXT PRIMARY KEY,
                    description TEXT,
                    category TEXT,
                    sub_category TEXT,
                    json_data TEXT,  -- Full SkillMetadata serialization
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Embeddings table: name -> vector (blob)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS embeddings (
                    skill_name TEXT PRIMARY KEY,
                    vector BLOB,
                    FOREIGN KEY(skill_name) REFERENCES skills(name) ON DELETE CASCADE
                )
            """)

            # Configs table: name -> json_config
            conn.execute("""
                CREATE TABLE IF NOT EXISTS skill_configs (
                    skill_name TEXT PRIMARY KEY,
                    config_json TEXT,
                    FOREIGN KEY(skill_name) REFERENCES skills(name) ON DELETE CASCADE
                )
            """)
            conn.commit()
            
    def upsert_skill(self, skill_name: str, metadata: Dict[str, Any], embedding: Optional[List[float]] = None):
        """Save skill and optionally its embedding."""
        with sqlite3.connect(self.db_path) as conn:
            # 1. Save Skill
            current_time = "example-timestamp" # Let DB handle it or use python datetime? DB defaults are safer.
            # Actually standard sqlite handling:
            conn.execute("""
                INSERT OR REPLACE INTO skills (name, description, category, sub_category, json_data, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                skill_name, 
                metadata.get("description", ""), 
                metadata.get("category", "uncategorized"), 
                metadata.get("sub_category", "uncategorized"),
                json.dumps(metadata)
            ))
            
            # 2. Save Embedding if provided
            if embedding:
                import struct
                # Pack floats into bytes (f = float32 standard)
                vector_bytes = struct.pack(f'{len(embedding)}f', *embedding)
                conn.execute("""
                    INSERT OR REPLACE INTO embeddings (skill_name, vector)
                    VALUES (?, ?)
                """, (skill_name, vector_bytes))
            
            conn.commit()

    def get_skill(self, skill_name: str) -> Optional[Dict[str, Any]]:
        """Retrieve skill metadata."""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT json_data FROM skills WHERE name = ?", (skill_name,)).fetchone()
            if row:
                return json.loads(row[0])
        return None
        
    def list_skills(self) -> List[Dict[str, Any]]:
        """List all stored skills."""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("SELECT json_data FROM skills").fetchall()
            return [json.loads(row[0]) for row in rows]

    def get_embedding(self, skill_name: str) -> Optional[List[float]]:
        """Retrieve stored embedding."""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT vector FROM embeddings WHERE skill_name = ?", (skill_name,)).fetchone()
            if row:
                import struct
                vector_bytes = row[0]
                count = len(vector_bytes) // 4
                return list(struct.unpack(f'{count}f', vector_bytes))
        return None

    def find_relevant_skills(self, query_vec: List[float], limit: int = 5) -> List[Tuple[Dict[str, Any], float]]:
        """
        Find top-k skills by cosine similarity.
        Warning: This loads all embeddings into memory. For <10k skills this is fine.
        """
        import struct
        
        candidates = []
        with sqlite3.connect(self.db_path) as conn:
            # Fetch all embeddings
            # Join with skills to get data proactively? Or fetch later?
            # Fetch name and vector
            cursor = conn.execute("SELECT skill_name, vector FROM embeddings")
            for name, vector_bytes in cursor:
                count = len(vector_bytes) // 4
                vec = list(struct.unpack(f'{count}f', vector_bytes))
                score = self._cosine_similarity(query_vec, vec)
                candidates.append((name, score))
        
        # Sort
        candidates.sort(key=lambda x: x[1], reverse=True)
        top_candidates = candidates[:limit]
        
        # Hydrate
        results = []
        with sqlite3.connect(self.db_path) as conn:
            for name, score in top_candidates:
                row = conn.execute("SELECT json_data FROM skills WHERE name = ?", (name,)).fetchone()
                if row:
                    results.append((json.loads(row[0]), score))
                    
        return results

    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        dot_product = sum(a * b for a, b in zip(v1, v2))
        magnitude_v1 = math.sqrt(sum(a * a for a in v1))
        magnitude_v2 = math.sqrt(sum(b * b for b in v2))
        if magnitude_v1 == 0 or magnitude_v2 == 0:
            return 0.0
        return dot_product / (magnitude_v1 * magnitude_v2)

    def get_skill_config(self, skill_name: str) -> Optional[Dict[str, Any]]:
        """Retrieve stored config for a skill."""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT config_json FROM skill_configs WHERE skill_name = ?", (skill_name,)).fetchone()
            if row:
                return json.loads(row[0])
        return None

    def set_skill_config(self, skill_name: str, config: Dict[str, Any]):
        """Save config for a skill."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO skill_configs (skill_name, config_json)
                VALUES (?, ?)
            """, (skill_name, json.dumps(config)))
            conn.commit()
