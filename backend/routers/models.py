"""Models routes — list available AI models from configuration."""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter
from pydantic import BaseModel


router = APIRouter(prefix="/api/models", tags=["models"])


class ModelInfo(BaseModel):
    """Information about an available AI model."""
    id: str
    name: str
    provider: str
    description: Optional[str] = None


def _load_available_models() -> List[ModelInfo]:
    """Load available models from environment and configuration.
    
    Returns a list of models that can be used with the agent system.
    This includes the default model from environment variables and
    any additional models that might be configured.
    """
    models = []
    
    # Get default model from environment
    default_model = os.getenv("AGENT_MODEL", "llama3.1")
    base_url = os.getenv("AGENT_OPENAI_BASE_URL", "http://localhost:11434/v1")
    
    # Add common models based on the base URL
    if "ollama" in base_url.lower() or "localhost:11434" in base_url:
        # Ollama models
        ollama_models = [
            ("llama3.1", "Llama 3.1", "Meta", "Meta's latest Llama model"),
            ("llama3", "Llama 3", "Meta", "Meta's Llama 3 model"),
            ("mistral", "Mistral", "Mistral AI", "Mistral's flagship model"),
            ("codellama", "Code Llama", "Meta", "Specialized for code generation"),
            ("phi3", "Phi-3", "Microsoft", "Microsoft's small but capable model"),
            ("gemma2", "Gemma 2", "Google", "Google's open-source model"),
        ]
        for model_id, name, provider, desc in ollama_models:
            models.append(ModelInfo(
                id=model_id,
                name=name,
                provider=provider,
                description=desc
            ))
    else:
        # OpenAI-compatible models (for other providers)
        openai_models = [
            ("gpt-4o", "GPT-4o", "OpenAI", "OpenAI's multimodal model"),
            ("gpt-4o-mini", "GPT-4o Mini", "OpenAI", "Fast and cost-effective"),
            ("gpt-4-turbo", "GPT-4 Turbo", "OpenAI", "Previous generation flagship"),
            ("claude-3-5-sonnet", "Claude 3.5 Sonnet", "Anthropic", "Anthropic's latest model"),
        ]
        for model_id, name, provider, desc in openai_models:
            models.append(ModelInfo(
                id=model_id,
                name=name,
                provider=provider,
                description=desc
            ))
    
    # Ensure the default model is in the list
    if not any(m.id == default_model for m in models):
        models.insert(0, ModelInfo(
            id=default_model,
            name=default_model,
            provider="Custom",
            description="Current default model"
        ))
    
    return models


@router.get("", response_model=List[ModelInfo])
async def list_models() -> List[ModelInfo]:
    """List all available AI models."""
    return _load_available_models()


@router.get("/current")
async def get_current_model() -> dict:
    """Get the currently configured default model."""
    default_model = os.getenv("AGENT_MODEL", "llama3.1")
    return {
        "id": default_model,
        "name": default_model,
        "provider": "Default"
    }
