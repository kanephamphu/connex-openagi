
import os
import torch
import uvicorn
import json
import time
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Generator
from transformers import AutoTokenizer, AutoModelForCausalLM, TextIteratorStreamer
from threading import Thread

# 1. Initialize FastAPI
app = FastAPI(title="SmolLM Sub-Brain Server")

# 2. Schemas
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.3
    max_tokens: Optional[int] = 256
    stream: Optional[bool] = False

class ChatCompletionResponseChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: str

class ChatCompletionResponse(BaseModel):
    id: str = "smollm-result"
    object: str = "chat.completion"
    created: int = int(time.time())
    model: str
    choices: List[ChatCompletionResponseChoice]

# 3. Model Configuration & Loading
MODEL_ID = "HuggingFaceTB/SmolLM2-1.7B-Instruct"

# Detect device: CUDA -> MPS -> CPU
if torch.cuda.is_available():
    DEVICE = "cuda"
elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
    DEVICE = "mps"
else:
    DEVICE = "cpu"

CACHE_DIR = os.path.join(os.getcwd(), "models", "smollm")

os.makedirs(CACHE_DIR, exist_ok=True)
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

print(f"[*] Loading model {MODEL_ID} on {DEVICE}...")
print(f"[*] Local cache: {CACHE_DIR}")

# Optional quantization (CPU/MPS usually don't support BitsAndBytes 4-bit)
quantization_config = None
if DEVICE == "cuda":
    try:
        from transformers import BitsAndBytesConfig
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True
        )
    except ImportError:
        print("[!] BitsAndBytes not found, skipping quantization.")

tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, cache_dir=CACHE_DIR)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID, 
    quantization_config=quantization_config,
    device_map="auto" if DEVICE == "cuda" else None,
    cache_dir=CACHE_DIR
).to(DEVICE)

@app.get("/api/tags")
@app.get("/api/health")
async def health_check():
    return {"status": "ok", "model": MODEL_ID}

def stream_generator(prompt: str, request: ChatCompletionRequest) -> Generator[str, None, None]:
    """Generator for OpenAI-compatible streaming responses."""
    inputs = tokenizer.encode(prompt, return_tensors="pt").to(DEVICE)
    streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)
    
    generation_kwargs = dict(
        input_ids=inputs,
        streamer=streamer,
        max_new_tokens=request.max_tokens,
        temperature=request.temperature,
        do_sample=True if request.temperature > 0 else False,
        pad_token_id=tokenizer.eos_token_id,
        eos_token_id=tokenizer.eos_token_id
    )
    
    thread = Thread(target=model.generate, kwargs=generation_kwargs)
    thread.start()
    
    for i, new_text in enumerate(streamer):
        # Truncate hallucinated turns in stream
        stop_found = False
        for stop_word in ["USER:", "ASSISTANT:", "<|im_start|>", "<|im_end|>", "User:", "Assistant:"]:
            if stop_word in new_text:
                new_text = new_text.split(stop_word)[0]
                stop_found = True
                break
        
        if not new_text and not stop_found:
            continue

        chunk = {
            "id": "smollm-stream",
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": MODEL_ID,
            "choices": [{
                "index": 0,
                "delta": {"content": new_text},
                "finish_reason": None if not stop_found else "stop"
            }]
        }
        yield f"data: {json.dumps(chunk)}\n\n"
        if stop_found:
            break
            
    yield "data: [DONE]\n\n"

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """Chat completion endpoint supporting both blocking and streaming."""
    chat = [{"role": msg.role, "content": msg.content} for msg in request.messages]
    prompt = tokenizer.apply_chat_template(chat, tokenize=False, add_generation_prompt=True)
    
    if request.stream:
        return StreamingResponse(stream_generator(prompt, request), media_type="text/event-stream")
    
    # Non-streaming implementation
    inputs = tokenizer.encode(prompt, return_tensors="pt").to(DEVICE)
    with torch.no_grad():
        outputs = model.generate(
            inputs, 
            max_new_tokens=request.max_tokens,
            temperature=request.temperature,
            do_sample=True if request.temperature > 0 else False,
            pad_token_id=tokenizer.eos_token_id,
            eos_token_id=tokenizer.eos_token_id
        )
    
    response_text = tokenizer.decode(outputs[0][len(inputs[0]):], skip_special_tokens=True).strip()

    for stop_word in ["USER:", "ASSISTANT:", "<|im_start|>", "<|im_end|>", "User:", "Assistant:"]:
        if stop_word in response_text:
            response_text = response_text.split(stop_word)[0].strip()

    return ChatCompletionResponse(
        model=MODEL_ID,
        choices=[
            ChatCompletionResponseChoice(
                index=0,
                message=ChatMessage(role="assistant", content=response_text),
                finish_reason="stop"
            )
        ]
    )

if __name__ == "__main__":
    port = int(os.getenv("SMOL_BRAIN_PORT", 11434))
    uvicorn.run(app, host="0.0.0.0", port=port)
