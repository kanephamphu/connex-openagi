"""
FastAPI Server for Connex AGI.
Provides a streaming API for interacting with the AGI planner and orchestrator.
"""
import sys
import os
from pathlib import Path

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from typing import Dict, Any, Optional
import json
import asyncio
from pathlib import Path

from agi import AGI
from agi.config import AGIConfig

app = FastAPI(title="Connex AGI Server", version="1.0.0")

# CORS - Allow local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize AGI
agi_instance = None
system_config = None

@app.on_event("startup")
async def startup():
    global agi_instance, system_config
    try:
        # Load config first (from env + db)
        system_config = AGIConfig.from_env()
        print("[Server] Configuration loaded.")
        
        # Then try to init AGI
        agi_instance = AGI(system_config)
        await agi_instance.initialize()
        print("AGI Initialized Successfully")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Failed to initialize AGI: {e}")
        # Don't crash startup, but subsequent requests might fail
        # Requests to /api/config will use system_config

@app.get("/health")
def health_check():
    ear_active = False
    if agi_instance and hasattr(agi_instance, "ear") and agi_instance.ear:
        ear_active = agi_instance.ear.running
        
    return {
        "status": "ok", 
        "agi_initialized": agi_instance is not None,
        "ear_active": ear_active
    }

@app.post("/api/sensors/ear/toggle")
async def toggle_ear(enabled: bool):
    if not agi_instance or not hasattr(agi_instance, "ear") or not agi_instance.ear:
        raise HTTPException(status_code=503, detail="Ear sensor not available")
    
    if enabled:
        agi_instance.ear.start()
    else:
        agi_instance.ear.stop()
        
    return {"success": True, "active": agi_instance.ear.running}


from typing import Dict, Any, Optional
import json

class ChatRequest(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None


class SkillConfigRequest(BaseModel):
    skill_name: str
    config: Dict[str, Any]


@app.post("/api/skills/config")
async def save_skill_config(request: SkillConfigRequest):
    """Save configuration for a specific skill."""
    try:
        agi_instance.skill_registry.store.set_skill_config(request.skill_name, request.config)
        # Also reload the skill to apply the new config immediately
        skill = agi_instance.skill_registry.get_skill(request.skill_name)
        skill.config.update(request.config)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    context: dict = {}

@app.get("/api/skills")
async def list_skills():
    """List all installed skills with status."""
    if not agi_instance:
        raise HTTPException(status_code=503, detail="AGI not initialized")
    
    skills_data = []
    registry = agi_instance.skill_registry
    
    for name, skill in registry._skills.items():
        data = skill.metadata.to_dict()
        
        # Add runtime status
        is_enabled = True
        if isinstance(skill.config, dict):
            is_enabled = skill.config.get("enabled", True)
        
        # Check if configured
        is_configured = True
        try:
             # We rely on check_config but catch the error
             # But check_config is async. We might not want to await here for all.
             # Let's do a lightweight check based on config keys
             if skill.metadata.config_schema:
                required = skill.metadata.config_schema.get("required", [])
                for key in required:
                    val = None
                    if isinstance(skill.config, dict):
                         val = skill.config.get(key)
                    
                    if not val and not os.getenv(key):
                        is_configured = False
                        break
        except:
            is_configured = False
            
        data["enabled"] = is_enabled
        data["is_configured"] = is_configured
        skills_data.append(data)
        
    return {"skills": skills_data}

class ToggleSkillRequest(BaseModel):
    enabled: bool

@app.post("/api/skills/{name}/toggle")
async def toggle_skill(name: str, request: ToggleSkillRequest):
    """Enable or disable a skill."""
    if not agi_instance:
        raise HTTPException(status_code=503, detail="AGI not initialized")
    
    try:
        skill = agi_instance.skill_registry.get_skill(name)
        
        # Update config in memory
        skill.config["enabled"] = request.enabled
        
        # Persist to DB
        # We need to get current config, merge, and save
        # Or just use the skill.config which is the source of truth
        agi_instance.skill_registry.store.set_skill_config(name, skill.config)
        
        action = "enabled" if request.enabled else "disabled"
        print(f"[Server] Skill {name} {action} by user.")
        return {"success": True, "enabled": request.enabled}
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Skill {name} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/reflex/webhook/{source}")
async def webhook_trigger(source: str, payload: Dict[str, Any]):
    """
    Endpoint for external webhooks to trigger Reflexes.
    """
    if not agi_instance:
        raise HTTPException(status_code=503, detail="AGI not initialized")
    
    event = {
        "source": source,
        "type": "webhook",
        "payload": payload
    }
    
    print(f"[Server] Received webhook from {source}")
    
    # Process through Reflex Layer
    triggered_plans = await agi_instance.reflex.process_event(event)
    
    results = []
    if triggered_plans:
        print(f"[Server] {len(triggered_plans)} reflexes triggered. Executing...")
        for tp in triggered_plans:
            reflex_name = tp["reflex"]
            plan = tp["plan"]
            
            # Execute plan via Orchestrator
            exec_result = await agi_instance.orchestrator.execute_plan(plan)
            results.append({
                "reflex": reflex_name,
                "success": exec_result.success,
            })
            
    return {"status": "received", "triggered": len(triggered_plans), "results": results}

@app.get("/api/perception")
async def list_perception_modules():
    """List all installed perception modules."""
    if not agi_instance:
         raise HTTPException(status_code=503, detail="AGI not initialized")
    
    modules = []
    for name, module in agi_instance.perception._modules.items():
        modules.append({
            "name": module.metadata.name,
            "description": module.metadata.description,
            "version": module.metadata.version,
            "type": "perception",
            "signals": [s.name for s in module.metadata.signals]
        })
    return {"modules": modules}

@app.get("/api/perception/{module_name}")
async def perceive(module_name: str, query: Optional[str] = None):
    """
    Directly query a perception module.
    """
    if not agi_instance:
         raise HTTPException(status_code=503, detail="AGI not initialized")
    
    try:
        data = await agi_instance.perception.perceive(module_name, query)
        return {"module": module_name, "data": data}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reflex")
async def list_reflex_modules():
    """List all installed reflex modules."""
    if not agi_instance:
         raise HTTPException(status_code=503, detail="AGI not initialized")
         
    modules = []
    # Access private _reflexes (ReflexLayer doesn't expose list method yet)
    for name, reflex in agi_instance.reflex._reflexes.items():
        modules.append({
            "name": reflex.metadata.name,
            "description": reflex.metadata.description,
            "version": reflex.metadata.version,
            "type": reflex.metadata.type,
            "active": reflex.active
        })
    return {"modules": modules}


@app.get("/api/config")
async def get_system_config():
    """Get current system configuration."""
    # Use active config or fallback to system_config
    current_config = None
    if agi_instance:
        current_config = agi_instance.config
    elif system_config:
        current_config = system_config
    else:
        # Emergency fallback
        try:
             current_config = AGIConfig.from_env()
        except:
             raise HTTPException(status_code=503, detail="Configuration unavailable")
    
    # Return everything from config object
    # Mask secrets
    from dataclasses import fields
    
    # Filter only defined dataclass fields to avoid runtime objects (managers, etc.)
    allowed_keys = {f.name for f in fields(AGIConfig)}
    
    raw_config = current_config.__dict__.copy()
    masked_config = {}
    for k, v in raw_config.items():
        # Skip runtime injections
        if k not in allowed_keys:
            continue

        # Skip internal callbacks/complex objects that are not serializable
        if callable(v) or k == "on_speak_callback":
            masked_config[k] = str(v) if v else None
            continue
            
        if "api_key" in k or "token" in k or "secret" in k:
            if v:
                masked_config[k] = f"***{str(v)[-4:]}"
            else:
                masked_config[k] = None
        else:
            masked_config[k] = v
            
    return {"config": masked_config}

class ConfigUpdateRequest(BaseModel):
    config: Dict[str, Any]

@app.post("/api/config")
async def update_system_config(request: ConfigUpdateRequest):
    """
    Update system configuration.
    If AGI is not initialized, try to re-initialize it after update.
    """
    global agi_instance, system_config
    
    try:
        from agi.utils.database import DatabaseManager
        db = DatabaseManager()
        
        # 1. Save to DB
        updated_keys = []
        for key, value in request.config.items():
             db.set_config(key, value)
             updated_keys.append(key)

        # 2. Update In-Memory Config
        target_config = agi_instance.config if agi_instance else system_config
        
        # If even system_config is gone, regenerate
        if not target_config:
             target_config = AGIConfig.from_env()
             if not system_config:
                  system_config = target_config

        for key, value in request.config.items():
            if hasattr(target_config, key):
                setattr(target_config, key, value)
        
        # 3. Attempt Re-Initialization if invalid
        if not agi_instance:
            print("[Server] Configuration updated. Attempting to initialize AGI...")
            try:
                # Re-create config from env+db to be sure
                new_config = AGIConfig.from_env()
                new_agi = AGI(new_config)
                await new_agi.initialize()
                
                # Success!
                agi_instance = new_agi
                system_config = new_config
                print("[Server] AGI Initialized/Recovered via Config Update!")
            except Exception as e:
                 print(f"[Server] Re-init failed: {e}")
                 # We still return success for the Config Update, so user knows it saved
                
        return {"success": True, "updated": updated_keys, "agi_initialized": agi_instance is not None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/memory/summarize")
async def trigger_summarization():
    """
    Trigger the daily summarization process.
    Summarizes the last 24h of history and saves to Long-Term Memory.
    """
    if not agi_instance:
         raise HTTPException(status_code=503, detail="AGI not initialized")
    
    try:
        await agi_instance.memory.summarize_and_persist(agi_instance.history)
        return {"success": True, "message": "Daily summary generated and persisted."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.get("/api/history")
async def list_history(limit: int = 20):
    """List execution history summaries."""
    if not agi_instance:
         raise HTTPException(status_code=503, detail="AGI not initialized")
    history = agi_instance.history.get_recent(limit)
    return {"history": history}

@app.get("/api/history/{entry_id}")
async def get_history_trace(entry_id: str):
    """Get full trace for a specific execution."""
    if not agi_instance:
         raise HTTPException(status_code=503, detail="AGI not initialized")
    item = agi_instance.history.get_trace(entry_id)
    if not item:
        raise HTTPException(status_code=404, detail="Trace not found")
    return item
@app.get("/api/registry/search")
async def search_registry(q: str, type: str = "skill", limit: int = 10):
    """Search for components in the registry."""
    if not agi_instance:
         raise HTTPException(status_code=503, detail="AGI not initialized")
    
    try:
        if type == "skill":
            results = await agi_instance.skill_registry.search_registry(q, limit)
        elif type == "perception":
            results = await agi_instance.perception.search_registry(q, limit)
        elif type == "reflex":
            results = await agi_instance.reflex.search_registry(q, limit)
        else:
            raise HTTPException(status_code=400, detail=f"Invalid component type: {type}")
            
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class InstallRequest(BaseModel):
    name: str
    type: str

@app.post("/api/registry/install")
async def install_component(request: InstallRequest):
    """Install a component from the registry."""
    if not agi_instance:
         raise HTTPException(status_code=503, detail="AGI not initialized")
    
    try:
        success = False
        if request.type == "skill":
            success = await agi_instance.skill_registry.install_skill(request.name)
        elif request.type == "perception":
            success = await agi_instance.perception.install_module(request.name)
        elif request.type == "reflex":
            success = await agi_instance.reflex.install_reflex(request.name)
        else:
            raise HTTPException(status_code=400, detail=f"Invalid component type: {request.type}")
            
        if not success:
            raise HTTPException(status_code=404, detail=f"Component {request.name} not found or failed to install")
            
        return {"success": True, "message": f"Successfully installed {request.name}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class PublishRequest(BaseModel):
    name: str
    type: str # skill, perception, reflex
    scoped_name: str
    private: bool = False

@app.post("/api/registry/publish")
async def publish_component(request: PublishRequest):
    """Publish a local component to the registry."""
    if not agi_instance:
         raise HTTPException(status_code=503, detail="AGI not initialized")
    
    from agi.services.publisher import ConnexPublisher
    publisher = ConnexPublisher(agi_instance.config)
    
    try:
        component = None
        if request.type == "skill":
            component = agi_instance.skill_registry.get_skill(request.name)
        elif request.type == "perception":
            component = agi_instance.perception.get_module(request.name)
        elif request.type == "reflex":
            # For reflexes, we need to find it in the list
            component = agi_instance.reflex._reflexes.get(request.name)
        
        if not component:
             raise HTTPException(status_code=404, detail=f"Component {request.name} not found locally")
             
        result = await publisher.publish_component(
            component=component,
            scoped_name=request.scoped_name,
            private=request.private
        )
        
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    if not agi_instance:
        # Check if we can lazy-init or key is missing
        if hasattr(app.state, 'init_error'):
             raise HTTPException(status_code=503, detail=f"AGI Unavailable: {app.state.init_error}")
        raise HTTPException(status_code=503, detail="AGI not initialized")
        
    async def event_generator():
        try:
            print(f"[Server] Starting event stream for message: {request.message[:50]}...")
            # Yield initial acknowledgment
            yield {
                "event": "start",
                "data": json.dumps({"status": "processing"})
            }
            
            async for update in agi_instance.execute_with_streaming(request.message, request.context):
                # print(f"[Server] Yielding update: {update.get('type')}")
                yield {
                    "event": "update",
                    "data": json.dumps(update)
                }
            
            print("[Server] Stream complete.")
            yield {
                "event": "done",
                "data": json.dumps({"status": "complete"})
            }
            
        except Exception as e:
            # Check for specific "AGI not ready" errors or DB errors
            error_msg = str(e)
            print(f"[Server] Stream error: {error_msg}")
            
            yield {
                "event": "error",
                "data": json.dumps({"error": error_msg})
            }

    return EventSourceResponse(event_generator())

@app.get("/api/repair/{entry_id}")
async def repair_history_item(entry_id: str):
    """
    Stream manual repair for a failed history item.
    Re-runs the planner with Immune System context.
    """
    if not agi_instance:
         raise HTTPException(status_code=503, detail="AGI not initialized")
    
    # 1. Get trace
    item = agi_instance.history.get_trace(entry_id)
    if not item:
        raise HTTPException(status_code=404, detail="Trace not found")
        
    async def event_generator():
        try:
           yield {"event": "start", "data": json.dumps({"status": "analyzing_failure"})}
           
           # 2. Extract failure details from trace
           # We look for the last 'action_failed' event or similar
           events = item["events"]
           failed_event = next((e for e in reversed(events) if e.get("type") == "action_failed"), None)
           
           error_msg = "Unknown error"
           failed_id = "unknown_action"
           skill_name = None
           
           if failed_event:
               failed_id = failed_event.get("action_id")
               error_msg = failed_event.get("error")
               
               # Find the start event for this action to get the skill name
               start_event = next((e for e in events if e.get("type") == "action_started" and e.get("action_id") == failed_id), None)
               if start_event:
                   skill_name = start_event.get("skill")
           
           # 3. Get skill file path
           skill_file_path = None
           if skill_name:
               import inspect
               try:
                   skill = agi_instance.skill_registry.get_skill(skill_name)
                   skill_file_path = inspect.getfile(skill.__class__)
                   print(f"Repair targets skill file: {skill_file_path}")
               except:
                   pass
            
           # 4. Get relevant skills
           skills = await agi_instance.skill_registry.get_relevant_skills(f"Fix {skill_name} error: {error_msg}")
           
           # 5. Run Planner with repair context
           from agi.planner.brain_planner import BrainPlanner
           planner = BrainPlanner(agi_instance.config)
           
           context = {
               "failed_action": failed_id,
               "error": error_msg,
               "skill_file_path": skill_file_path,
               "manual_repair": True
           }
           
           # Stream the PLAN creation
           final_plan = None
           async for update in planner.create_plan_streaming(
               goal=f"Fix failure in step '{failed_id}' ({skill_name}): {error_msg}", 
               context=context,
               skills=skills
           ):
                # Yield planning events
                yield {"event": "update", "data": json.dumps(update)}
                if update.get("type") == "plan_complete":
                     final_plan = update["plan"]

           # 5. Execute the repair plan
           if final_plan:
               async for update in agi_instance.orchestrator.execute_plan_streaming(final_plan):
                   yield {"event": "update", "data": json.dumps(update)}
                   
           yield {"event": "done", "data": json.dumps({"status": "complete"})}

        except Exception as e:
            yield {"event": "error", "data": json.dumps({"error": str(e)})}

    return EventSourceResponse(event_generator())


# Serve Static Assets manually to avoid directory/file conflicts
if os.path.exists("ui/out"):
    from fastapi.responses import FileResponse
    
    # 1. Mount Next.js assets explicitly
    app.mount("/_next", StaticFiles(directory="ui/out/_next"), name="next-assets")
    
    # 2. Explicit Routes for clean URLs
    @app.get("/")
    async def serve_root():
        return FileResponse("ui/out/index.html")

    @app.get("/skills")
    async def serve_skills():
        return FileResponse("ui/out/skills.html")

    @app.get("/history")
    async def serve_history():
        return FileResponse("ui/out/history.html")
    
    # 3. Fallback for other static files (favicon, vectors, etc.)
    # This must be the LAST route defined
    @app.get("/{path:path}")
    async def serve_static(path: str):
        # Prevent traversing up
        if ".." in path:
            raise HTTPException(status_code=404)
            
        file_path = Path("ui/out") / path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
            
        # Try appending .html for other clean urls
        html_path = file_path.with_suffix(".html")
        if html_path.exists() and html_path.is_file():
            return FileResponse(html_path)
            
        return FileResponse("ui/out/404.html", status_code=404)

if __name__ == "__main__":
    import uvicorn
    # Load .env explicitly if running directly
    from dotenv import load_dotenv
    load_dotenv()
    
    uvicorn.run(app, host="0.0.0.0", port=8001)

