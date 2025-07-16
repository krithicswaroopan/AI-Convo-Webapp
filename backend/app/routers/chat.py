"""Chat API router for LLM interactions."""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from app.services.llm_service import llm_service
from app.models.chat import ChatRequest, ChatResponse, ConversationHistory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat & LLM"])


@router.post("/generate", response_model=ChatResponse)
async def generate_response(request: ChatRequest):
    """
    Generate a response using the specified LLM model.
    
    Args:
        request: ChatRequest containing user message and parameters
        
    Returns:
        ChatResponse with generated text and metadata
    """
    try:
        logger.info(f"Generating response for message: {request.message[:50]}...")
        
        # Validate model if specified
        if request.model and not llm_service.validate_model(request.model):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid model: {request.model}"
            )
        
        # Generate response
        response = await llm_service.generate_response(request)
        
        if not response.success:
            raise HTTPException(
                status_code=500,
                detail=f"LLM generation failed: {response.error}"
            )
        
        logger.info(f"Response generated successfully: {len(response.message)} characters")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat generation error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error during chat generation"
        )


@router.post("/stream")
async def generate_streaming_response(request: ChatRequest):
    """
    Generate a streaming response using the specified LLM model.
    
    Args:
        request: ChatRequest containing user message and parameters
        
    Yields:
        Streaming response chunks
    """
    try:
        logger.info(f"Generating streaming response for message: {request.message[:50]}...")
        
        # Validate model if specified
        if request.model and not llm_service.validate_model(request.model):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid model: {request.model}"
            )
        
        # Generate streaming response
        async for chunk in llm_service.generate_streaming_response(request):
            yield f"data: {chunk}\n\n"
        
        yield "data: [DONE]\n\n"
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Streaming chat generation error: {str(e)}", exc_info=True)
        yield f"data: Error: {str(e)}\n\n"


@router.get("/models")
async def get_available_models():
    """
    Get list of available LLM models.
    
    Returns:
        Dictionary of available models
    """
    try:
        models = llm_service.get_available_models()
        return {
            "models": models,
            "default_model": llm_service.default_model,
            "total_models": len(models)
        }
    except Exception as e:
        logger.error(f"Error getting available models: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve available models"
        )


@router.post("/conversation", response_model=ConversationHistory)
async def create_conversation():
    """
    Create a new conversation.
    
    Returns:
        New conversation with ID
    """
    try:
        import uuid
        from datetime import datetime
        
        conversation = ConversationHistory(
            conversation_id=str(uuid.uuid4()),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        logger.info(f"Created new conversation: {conversation.conversation_id}")
        return conversation
        
    except Exception as e:
        logger.error(f"Error creating conversation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create conversation"
        )


@router.get("/conversation/{conversation_id}", response_model=ConversationHistory)
async def get_conversation(conversation_id: str):
    """
    Get conversation by ID.
    
    Args:
        conversation_id: Unique conversation identifier
        
    Returns:
        Conversation history
    """
    try:
        # This would typically fetch from database
        # For now, return a placeholder
        from datetime import datetime
        
        conversation = ConversationHistory(
            conversation_id=conversation_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        return conversation
        
    except Exception as e:
        logger.error(f"Error getting conversation {conversation_id}: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )


@router.post("/conversation/{conversation_id}/rate")
async def rate_response(
    conversation_id: str,
    message_id: str,
    rating: int
):
    """
    Rate an assistant response.
    
    Args:
        conversation_id: Conversation identifier
        message_id: Message identifier
        rating: Rating (1-5 stars)
        
    Returns:
        Confirmation of rating
    """
    try:
        if not 1 <= rating <= 5:
            raise HTTPException(
                status_code=400,
                detail="Rating must be between 1 and 5"
            )
        
        # This would typically store in database
        logger.info(f"Rating {rating} received for message {message_id} in conversation {conversation_id}")
        
        return {
            "success": True,
            "message": "Rating received successfully",
            "conversation_id": conversation_id,
            "message_id": message_id,
            "rating": rating
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rating response: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to save rating"
        )


@router.get("/health")
async def chat_health_check():
    """
    Health check for chat service.
    
    Returns:
        Health status of the chat service
    """
    try:
        return {
            "status": "healthy",
            "service": "chat",
            "default_model": llm_service.default_model,
            "available_models": len(llm_service.get_available_models()),
            "available": True
        }
    except Exception as e:
        logger.error(f"Chat health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "service": "chat",
            "error": str(e),
            "available": False
        } 