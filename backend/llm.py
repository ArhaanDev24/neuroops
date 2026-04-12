import os
import json
import requests
from typing import Dict, Any, Optional
from retry import retry

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
MODEL_NAME = os.getenv("MODEL_NAME", "qwen2.5:latest") # Ensure this model is pulled in Ollama

class LLMError(Exception):
    pass

def _call_ollama(prompt: str, system_prompt: str = "You are a helpful AI assistant.") -> str:
    """Raw call to Ollama API."""
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "system": system_prompt,
        "stream": False,
        "options": {"temperature": 0.7}
    }
    
    try:
        response = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=60)
        response.raise_for_status()
        return response.json().get("response", "")
    except requests.exceptions.RequestException as e:
        raise LLMError(f"Failed to connect to Ollama: {e}")

@retry(tries=3, delay=2, backoff=2)
def generate_response(prompt: str, system_prompt: str = "You are a helpful AI assistant.") -> str:
    """Generates a text response with retry logic."""
    return _call_ollama(prompt, system_prompt).strip()

@retry(tries=3, delay=2, backoff=2)
def structured_output(prompt: str, schema_description: str) -> Dict[str, Any]:
    """
    Forces the LLM to return valid JSON based on a schema description.
    Includes parsing and validation retry logic.
    """
    full_prompt = f"""
    You must output ONLY valid JSON. Do not include markdown formatting like ```json.
    Schema Requirement: {schema_description}
    
    Task: {prompt}
    
    Output:
    """
    
    raw_text = _call_ollama(full_prompt, "You are a strict JSON generator. Output only raw JSON.")
    
    # Clean up common LLM artifacts
    clean_text = raw_text.strip()
    if clean_text.startswith("```json"):
        clean_text = clean_text[7:]
    if clean_text.startswith("```"):
        clean_text = clean_text[3:]
    if clean_text.endswith("```"):
        clean_text = clean_text[:-3]
    clean_text = clean_text.strip()

    try:
        data = json.loads(clean_text)
        return data
    except json.JSONDecodeError as e:
        raise LLMError(f"Invalid JSON received from LLM: {e}\nRaw: {clean_text}")