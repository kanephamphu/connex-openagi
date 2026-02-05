# Connex AGI Technical Architecture

This document provides a deep dive into the 8-tier architecture of Connex AGI.

## High-Level Cognitive Architecture

Connex AGI is designed to mimic a biological brain, separating fast reactions from deep reasoning and ensuring long-term self-improvement.

![architecture software design](../docs/assets/architecture_software_design.png)

```mermaid
graph TD
    User([User Intent]) --> Perception
    User --> Reflex
    
    subgraph Senses["Tier Peer Layer (Senses & Reactions)"]
        Perception[Perception Layer]
        Reflex[Reflex Layer]
    end
    
    subgraph Accelerator["Parallel Engine (Tier 8)"]
        SubBrain{{Sub-Brain System}}
    end
    
    Perception <--> SubBrain
    Orchestrator <--> SubBrain

    Perception --> Planner
    Reflex --> Orchestrator
    
    subgraph Core["Core Reasoning (Tier 1 & 2)"]
        Planner[Planner / Tier 1]
        Orchestrator[Orchestrator / Tier 2]
        Corrector[Self-Correction / Immune System]
    end
    
    Planner -- Action DAG --> Orchestrator
    Orchestrator -- Error Feedback --> Corrector
    Corrector -- Patch --> Orchestrator
    
    subgraph Execution["Workers (Tier 3)"]
        SkillDock[SkillDock]
    end
    
    Orchestrator -- Call --> SkillDock
    SkillDock -- Result --> Orchestrator
    
    subgraph Evolution["Self-Evolution (Tier 4)"]
        Motivation[Motivation System]
        Memory[Memory System]
    end
    
    Orchestrator -- Logs/Trace --> Motivation
    Orchestrator -- Conversation --> Memory
    Motivation -- Proposal --> Planner
    Memory -- Recall --> Planner
    Motivation -- Skill Acquisition --> SkillDock
    
    style SubBrain fill:#f9f,stroke:#333,stroke-width:2px
```

## Layer Descriptions

### 1. Perception Layer (Tier Peer)
- **Role**: Senses.
- **Mechanism**: Connects to the environment via MCP or specific sensors.
- **Foundational Modules**: 
    - `WorkloadPerception` (Telemetry)
    - `IntentDriftPerception` (Goal monitoring)
    - `VoicePerception` (Listening)
    - `CapabilityPerception` (Self-Awareness/Skill Registry)

### 2. Reflex Layer (Tier Peer)
- **Role**: Immediate Reaction.
- **Mechanism**: Listeners triggered by webhooks or signals.
- **Foundational Modules**: 
    - `SafetyPolicyReflex` (Compliance)
    - `ResourceGovernorReflex` (Throttling)
    - `VoiceCommandReflex` (Spoken Orders)
    - `SelfRepairReflex` (Error Recovery)
- **Function**: Bypasses the Planner for known automation recipes.

### 3. Planner (Tier 1)
- **Role**: The Architect.
- **Model**: High-reasoning LLMs.
- **Function**: Decomposes goals into structured **Action DAGs**. It considers both Perception context and Memory recall.

### 4. Orchestrator (Tier 2)
- **Role**: The Manager.
- **Function**: Executes the Action DAG, manages state, and handles I/O mapping between steps.
- **Corrector**: When an action fails, the Orchestrator uses the Corrector to generate immediate fixes.

### 5. SkillDock (Tier 3)
- **Role**: The Workers.
- **Function**: A registry of modular tools (Python classes) that perform specific tasks.

### 6. Motivation System (New)
- **Role**: Self-Reflection & Evaluation.
- **Mechanism**: Reads logs/traces post-execution.
- **Function**: Reviews performance quality and triggers **Skill Acquisition** to improve the AGI's future power.

### 7. Memory System
- **Role**: Experience Storage.
- **Mechanism**: SQLite-backed Vector DB.
- **Function**: Provides semantic recall of past interactions and daily experience summarization.

### 8. Sub-Brain System (Tier 8)
- **Role**: Local Acceleration & Parallelization.
- **Mechanism**: Distributed local LLM hosts (e.g., SmolLM-135M-Instruct).
- **Function**: Offloads intensive but straightforward tasks like emotion detection, formatting, or intent classification from the main Brain, allowing for faster response times and improved privacy.
