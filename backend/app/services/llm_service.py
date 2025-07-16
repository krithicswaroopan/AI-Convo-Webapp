"""Language Model service using OpenRouter API for open-source models."""

import logging
import json
import uuid
from typing import Optional, List, Dict, Any
import httpx
from app.config import settings
from app.models.chat import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)


class LLMService:
    """Language Model service using OpenRouter API."""
    
    def __init__(self):
        """Initialize the LLM service."""
        self.api_key = settings.openrouter_api_key
        self.base_url = settings.openrouter_base_url
        self.default_model = settings.default_llm_model
        self.client = httpx.AsyncClient(timeout=60.0)
        
        # Available open-source models via OpenRouter
        self.available_models = {
            "llama-3.1-8b": "meta-llama/llama-3.1-8b-instruct",
            "llama-3.1-70b": "meta-llama/llama-3.1-70b-instruct",
            "mistral-7b": "mistralai/mistral-7b-instruct",
            "mistral-8x7b": "mistralai/mixtral-8x7b-instruct",
            "codellama-7b": "codellama/codellama-7b-instruct",
            "phi-3": "microsoft/phi-3-mini-4k-instruct",
            "gemma-2b": "google/gemma-2b-it",
            "gemma-7b": "google/gemma-7b-it"
        }
    
    async def generate_response(
        self, 
        request: ChatRequest,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> ChatResponse:
        """
        Generate a response using the specified LLM model.
        
        Args:
            request: ChatRequest containing user message and parameters
            conversation_history: Optional conversation context
            
        Returns:
            ChatResponse with generated text and metadata
        """
        try:
            model = request.model or self.default_model
            logger.info(f"Generating response with model: {model}")
            
            # Prepare messages for the API
            messages = []
            
            # Add system prompt if provided
            if request.system_prompt:
                messages.append({
                    "role": "system",
                    "content": request.system_prompt
                })
            
            # Add conversation history if provided
            if conversation_history:
                messages.extend(conversation_history)
            
            # Add current user message
            messages.append({
                "role": "user",
                "content": request.message
            })
            
            # Prepare the request payload
            payload = {
                "model": model,
                "messages": messages,
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
                "stream": False
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://ai-assistant-webapp.com",
                "X-Title": "AI Assistant WebApp"
            }
            
            # Make request to OpenRouter API
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                choice = result["choices"][0]
                message = choice["message"]["content"]
                
                return ChatResponse(
                    success=True,
                    message=message,
                    conversation_id=request.conversation_id or str(uuid.uuid4()),
                    message_id=str(uuid.uuid4()),
                    model_used=model,
                    tokens_used=result.get("usage", {}).get("total_tokens"),
                    error=None
                )
            else:
                error_msg = f"LLM API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return ChatResponse(
                    success=False,
                    message="",
                    conversation_id=request.conversation_id or str(uuid.uuid4()),
                    message_id=str(uuid.uuid4()),
                    model_used=model,
                    error=error_msg
                )
                
        except Exception as e:
            error_msg = f"LLM generation failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return ChatResponse(
                success=False,
                message="",
                conversation_id=request.conversation_id or str(uuid.uuid4()),
                message_id=str(uuid.uuid4()),
                model_used=request.model or self.default_model,
                error=error_msg
            )
    
    async def generate_streaming_response(
        self,
        request: ChatRequest,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ):
        """
        Generate a streaming response using the specified LLM model.
        
        Args:
            request: ChatRequest containing user message and parameters
            conversation_history: Optional conversation context
            
        Yields:
            Chunks of the generated response
        """
        try:
            model = request.model or self.default_model
            logger.info(f"Generating streaming response with model: {model}")
            
            # Prepare messages for the API
            messages = []
            
            if request.system_prompt:
                messages.append({
                    "role": "system",
                    "content": request.system_prompt
                })
            
            if conversation_history:
                messages.extend(conversation_history)
            
            messages.append({
                "role": "user",
                "content": request.message
            })
            
            payload = {
                "model": model,
                "messages": messages,
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
                "stream": True
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://ai-assistant-webapp.com",
                "X-Title": "AI Assistant WebApp"
            }
            
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers
                ) as response:
                    if response.status_code == 200:
                        async for line in response.aiter_lines():
                            if line.startswith("data: "):
                                data = line[6:]  # Remove "data: " prefix
                                if data == "[DONE]":
                                    break
                                try:
                                    chunk = json.loads(data)
                                    if "choices" in chunk and chunk["choices"]:
                                        delta = chunk["choices"][0].get("delta", {})
                                        if "content" in delta:
                                            yield delta["content"]
                                except json.JSONDecodeError:
                                    continue
                    else:
                        error_msg = f"Streaming LLM API error: {response.status_code}"
                        logger.error(error_msg)
                        yield f"Error: {error_msg}"
                        
        except Exception as e:
            error_msg = f"Streaming LLM generation failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            yield f"Error: {error_msg}"
    
    def get_available_models(self) -> Dict[str, str]:
        """Get list of available models."""
        return self.available_models.copy()
    
    def validate_model(self, model: str) -> bool:
        """Validate if a model is available."""
        return model in self.available_models.values()
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


# Global LLM service instance
llm_service = LLMService() 