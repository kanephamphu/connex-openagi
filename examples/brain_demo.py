"""
Demo of the GenAI Brain's provider switching capabilities.
"""

import os
from agi import AGI, AGIConfig

def main():
    print("=" * 60)
    print("GenAI Brain - Multi-Provider Demo")
    print("=" * 60)
    
    # Initialize AGI
    # Note: In a real run, this needs valid API keys in .env
    config = AGIConfig.from_env()
    
    # Only verify configuration if keys are present (mocks for demo output)
    if not any([config.openai_api_key, config.deepseek_api_key, config.anthropic_api_key]):
        print("\n[WARN] No API keys found in .env. Showing logic trace only.\n")
        
        # Mock keys for demonstration logic
        config.deepseek_api_key = "mock_key"
        config.openai_api_key = "mock_key"
        config.anthropic_api_key = "mock_key"
        config.groq_api_key = "mock_key"
    
    agi = AGI(config)
    brain = agi.brain
    
    # 1. Planning Task (DeepSeek-R1)
    print("\n[Scenario 1] Complex Planning Task")
    print("Task: 'Decompose a marketing strategy for a new SaaS product'")
    provider, model = brain.select_model("planning")
    print(f"-> Brain selected: {provider.upper()} ({model})")
    print(f"  Reason: Best reasoning capabilities for decomposition")
    
    # 2. Coding Task (Claude 3.5 Sonnet / GPT-4o)
    print("\n[Scenario 2] Heavy Coding Task")
    print("Task: 'Write a Python FastAPI server with auth middleware'")
    provider, model = brain.select_model("coding")
    print(f"-> Brain selected: {provider.upper()} ({model})")
    print(f"  Reason: High precision and context window for code")
    
    # 3. Fast Task (Groq)
    print("\n[Scenario 3] Real-time Response")
    print("Task: 'Chatbot response to user greeting'")
    provider, model = brain.select_model("fast")
    print(f"-> Brain selected: {provider.upper()} ({model})")
    print(f"  Reason: Lowest latency for interactive tasks")
    
    # 4. Creative Task (GPT-4o / Opus)
    print("\n[Scenario 4] Creative Writing")
    print("Task: 'Write a poem about AI agents'")
    provider, model = brain.select_model("creative")
    print(f"-> Brain selected: {provider.upper()} ({model})")
    print(f"  Reason: Strong creative writing capabilities")

if __name__ == "__main__":
    main()
