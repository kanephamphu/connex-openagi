
import time
from typing import List, Dict, Any, Optional
from agi.memory.engine import MemoryEngine
from agi.config import AGIConfig

class MemoryManager:
    """
    Coordinates Short-Term (Cache) and Long-Term (SQLite) Memory.
    """
    
    def __init__(self, config: AGIConfig, brain: Any = None):
        self.config = config
        self.brain = brain # Instance of GenAIBrain
        
        # Long-Term Storage
        db_path = getattr(config, 'memory_db_path', "agi_memory.db")
        self.long_term = MemoryEngine(db_path)
        
        # Short-Term Cache (Volatile, per instance/session)
        self.short_term: List[Dict[str, Any]] = []
        self.max_short_term = 10 # Keep last 10 interactions in hot cache
        
    def add_to_short_term(self, goal: str, result: str):
        """Add a recent interaction to context cache."""
        self.short_term.append({
            "goal": goal,
            "result": result,
            "timestamp": time.time()
        })
        if len(self.short_term) > self.max_short_term:
            self.short_term.pop(0)
            
    async def recall(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for relevant memories across tiers.
        """
        # 1. Get embedding for query
        if not self.brain:
             return []
             
        query_vec = await self.brain.get_embedding(query)
        
        # 2. Search LT memory
        lt_memories = self.long_term.search(query_vec, limit=limit)
        
        # 3. Combine with ST cache if relevant? 
        # (Usually ST is small enough to just include as context directly)
        return lt_memories

    async def summarize_and_persist(self, history_manager: Any):
        """
        Summarize the day's interactions and move to Long-Term Memory.
        This follows the user request to "summary information in one days".
        """
        if not self.brain:
            return
            
        # Get history from the last 24 hours
        now = time.time()
        one_day_ago = now - (24 * 3600)
        
        history = history_manager._load()
        relevant_history = [h for h in history if h['timestamp'] > one_day_ago]
        
        if not relevant_history:
            return
            
        print(f"[Memory] Summarizing {len(relevant_history)} interactions from the last 24h...")
        
        # 1. Prepare history text for LLM
        history_text = "\n".join([
            f"Goal: {h['goal']}\nStatus: {h['status']}" 
            for h in relevant_history
        ])
        
        # 2. Ask Brain to summarize
        prompt = f"""Summarize the following AGI interactions into a concise "Experience Note" for long-term memory. 
        Focus on key findings, successful strategies, and failures to avoid.
        
        Interactions:
        {history_text}
        
        Respond with a structured summary.
        """
        
        # Use simple chat/fast model for summarization
        # Since use case is background, we can await
        provider, model = self.brain.select_model("fast")
        client = self.brain.get_client(provider)
        
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            summary = response.choices[0].message.content.strip()
            
            # 3. Embed and Save to LT
            vec = await self.brain.get_embedding(summary)
            self.long_term.add_memory(
                content=summary,
                embedding=vec,
                metadata={"type": "daily_summary", "date": time.strftime("%Y-%m-%d")}
            )
            print(f"[Memory] Daily summary persisted to Long-Term Memory.")
            
        except Exception as e:
            print(f"[Memory] Failed to generate daily summary: {e}")

    def get_context_window(self) -> str:
        """Return short-term cache as a formatted string for prompting."""
        if not self.short_term:
            return "No recent interactions."
            
        lines = ["Recent Context:"]
        for st in self.short_term:
            lines.append(f"- G: {st['goal']} -> R: {st['result'][:100]}...")
        return "\n".join(lines)
