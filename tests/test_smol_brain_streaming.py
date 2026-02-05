
import httpx
import json
import asyncio

async def test_streaming():
    url = "http://localhost:11434/v1/chat/completions"
    payload = {
        "model": "SmolLM-135M-Instruct",
        "messages": [
            {"role": "user", "content": "Tell me a short story about an AI."}
        ],
        "temperature": 0.7,
        "max_tokens": 50,
        "stream": True
    }
    
    print(f"[*] Testing streaming with payload: {json.dumps(payload, indent=2)}")
    print("[*] Connecting to server...")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", url, json=payload) as response:
                if response.status_code != 200:
                    print(f"[ERROR] Failed to connect: {response.status_code}")
                    return

                print("\n=== Stream Start ===")
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            print("\n=== Stream End ===")
                            break
                        
                        try:
                            chunk = json.loads(data)
                            content = chunk["choices"][0]["delta"].get("content", "")
                            print(content, end="", flush=True)
                        except json.JSONDecodeError:
                            print(f"\n[ERROR] Parse error: {data}")
    except Exception as e:
        print(f"\n[ERROR] Request failed: {e}")
        print("\nTip: Make sure the SmolLM server is running with run_smol_brain.bat")

if __name__ == "__main__":
    asyncio.run(test_streaming())
