"""
Memory Database Engine using SQLite for storage and vector search.
"""

import sqlite3
import json
import math
import os
import time
from typing import List, Dict, Any, Tuple

class MemoryEngine:
    def __init__(self, db_path: str = "agi_memory.db"):
        self.db_path = db_path
        self._init_db()
        
    def _init_db(self):
        """Initialize SQLite table."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        # Create memories table
        # embedding_json stores the vector as a JSON list [0.1, 0.2, ...]
        c.execute('''
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                embedding_json TEXT NOT NULL,
                metadata_json TEXT DEFAULT '{}',
                timestamp REAL
            )
        ''')
        conn.commit()
        conn.close()
        
    def add_memory(self, content: str, embedding: List[float], metadata: Dict[str, Any] = None):
        """Store a memory with its vector."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        embedding_str = json.dumps(embedding)
        metadata_str = json.dumps(metadata or {})
        timestamp = time.time()
        
        c.execute(
            'INSERT INTO memories (content, embedding_json, metadata_json, timestamp) VALUES (?, ?, ?, ?)',
            (content, embedding_str, metadata_str, timestamp)
        )
        conn.commit()
        conn.close()
        
    def search(self, query_embedding: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        """
        Semantic search using Cosine Similarity.
        
        Since SQLite doesn't have native vector functions, we fetch all (or recent) memories
        and compute similarity in Python. This is fast enough for <10,000 memories.
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Fetch all memories
        # Optimization: In production, use a vector DB or extension like sqlite-vec
        c.execute('SELECT id, content, embedding_json, metadata_json, timestamp FROM memories')
        rows = c.fetchall()
        conn.close()
        
        scored_memories = []
        
        for row in rows:
            mem_id, content, emb_json, meta_json, ts = row
            embedding = json.loads(emb_json)
            
            score = self._cosine_similarity(query_embedding, embedding)
            scored_memories.append({
                "id": mem_id,
                "content": content,
                "score": score,
                "metadata": json.loads(meta_json),
                "timestamp": ts
            })
            
        # Sort by score descending
        scored_memories.sort(key=lambda x: x["score"], reverse=True)
        
        return scored_memories[:limit]
        
    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        dot_product = sum(a * b for a, b in zip(v1, v2))
        magnitude_v1 = math.sqrt(sum(a * a for a in v1))
        magnitude_v2 = math.sqrt(sum(b * b for b in v2))
        
        if magnitude_v1 == 0 or magnitude_v2 == 0:
            return 0.0
            
        return dot_product / (magnitude_v1 * magnitude_v2)
    
    def delete_memory(self, memory_id: int):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('DELETE FROM memories WHERE id = ?', (memory_id,))
        conn.commit()
        conn.close()

    def get_all(self, limit: int = 100):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT id, content, metadata_json, timestamp FROM memories ORDER BY timestamp DESC LIMIT ?', (limit,))
        rows = c.fetchall()
        conn.close()
        return [
            {
                "id": r[0], 
                "content": r[1], 
                "metadata": json.loads(r[2]), 
                "timestamp": r[3]
            } 
            for r in rows
        ]
