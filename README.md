# Connex AGI - Three-Tier Agentic Planning System

> **Building the base of AGI**: A system where every user interaction is converted into a structured sequence of executable actions.

Connex AGI implements a sophisticated three-tier architecture that transforms nebulous goals into executable "programs" — making it a compiler for human intent.

## 🎯 Architecture Overview

Connex AGI mimics biological cognitive systems by integrating **Deliberative Reasoning** (Planner/Orchestrator) with **Perception** (Senses) and **Reflexes** (Automatic Responses).


![Connex AGI Architecture](docs/assets/architecture_v2.png)


### 1. Perception Layer (Senses) 👁️
**"The Eyes and Ears of the AGI"**

The Perception Layer connects the AGI to the real world using the **Model Context Protocol (MCP)**.
- **Purpose**: Gathers real-time environmental data *before* or *during* planning.
- **Mechanism**: Connects to external sensors, databases, or live feeds.
- **Integration**: The Brain checks if it needs "eyes" (Perception) to understand the user's request accurately.
- **Examples**: 
    - Reading live logs
    - Checking server status
    - Analyzing a video stream

### 2. Reflex Layer (Unconditional Reflex) ⚡
**"The Nervous System"**

Reflexes are pre-programmed, automatic responses to specific triggers. They bypass the slow, expensive reasoning of the Planner for known, critical events.
- **Purpose**: Instant reaction to external signals (Webhooks, Signals).
- **Mechanism**: Event Listener -> Condition Check -> Static/Dynamic Plan.
- **Integration**: Feeds executable plans directly to the Orchestrator.
- **Example**: 
    - *Trigger*: `github_webhook` (Push Event)
    - *Reflex Plan*: `[git_pull, run_tests, notify_slack]`

### 3. Tier 1: The Planner (Architect) 🧠
The high-reasoning component that decomposes goals into action sequences.
- **Model**: DeepSeek-R1, GPT-o1, or Claude
- **Input**: Natural language goal + Perception Context
- **Output**: Directed Acyclic Graph (DAG) of actions
- **Logic**: Chain-of-thought reasoning to identify inputs/outputs

### 4. Tier 2: The Orchestrator (Manager) ⚙️
The state management and routing layer.
- **State Management**: Tracks completed, pending, and failed actions
- **Input/Output Mapping**: Ensures outputs from Step A become inputs for Step B
- **Self-Correction**: Re-plans if a step fails

### 5. Tier 3: The SkillDock (Workers) 🔧
Modular skills that perform actual work.
- **Built-in Skills**: Web search, HTTP client, code execution
- **Custom Skills**: Easy to create and install from Registry

---

## 🚀 Quick Start

### 1. Installation

```bash
cd connex/agi
pip install -e .
```

### 2. Configuration

Copy the environment template and add your API keys:

```bash
cp .env.example .env
# Edit .env and add your keys
```

### 3. Basic Usage (Python)

```python
from agi import AGI
import asyncio

async def main():
    agi = AGI()
    await agi.initialize()
    
    # Standard Goal Execution
    result = await agi.execute(
        goal="Check the server logs and summarize the last error",
        context={"server_id": "prod-1"}
    )
    
    # Perception Query (Direct)
    data = await agi.perception.perceive("server_logs_mcp", query="last 5 mins")
```

### 4. API Usage (Server)

Start the server:
```bash
python server.py
```

**Trigger a Reflex (Webhook):**
```bash
curl -X POST http://localhost:8001/api/reflex/webhook/github \
     -H "Content-Type: application/json" \
     -d '{"event": "push", "repo": "connex"}'
```

---

## 📚 Core Concepts

### Hub Interface
Both Perception and Reflex modules are treated as **installable capabilities**, similar to Skills.
- **Perception Hub**: Install new sensors/data sources.
- **Reflex Hub**: Install new automation recipes.

### The Brain's Inner Monologue
With Perception integrated, the AGI's thought process evolves:

1. **Core Objective**: What does the user want?
2. **Perception Check**: Do I need to "see" something first? (e.g. Query MCP)
3. **Capability Check**: Which skills do I have?
4. **Strategic Plan**: Build the Action DAG.

## 🛠️ Extensibility

### Creating a Perception Module

```python
from agi.perception import PerceptionModule

class MySensor(PerceptionModule):
    @property
    def perception_type(self):
        return "visual"

    async def perceive(self, query=None, **kwargs):
        # Connect to MCP or Hardware
        return {"temperature": 72, "status": "nominal"}
```

### Creating a Reflex

```python
from agi.reflex import ReflexModule

class DeployReflex(ReflexModule):
    async def evaluate(self, event):
        return event.get("type") == "release_published"
        
    async def get_plan(self):
        return [
            {"skill": "ssh_client", "args": {"cmd": "deploy.sh"}},
            {"skill": "email", "args": {"to": "admin", "body": "Deployed!"}}
        ]
```

## 📜 License
MIT License - Part of the Connex Platform
