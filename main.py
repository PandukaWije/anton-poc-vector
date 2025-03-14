from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import asyncio
import json
import uuid
from datetime import datetime

# Import our ProductRAG class
from product_rag import ProductRAG

app = FastAPI(title="Product RAG API")

# Configure CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for chats and messages
# In a real application, you would use a database
chats = {}

# Load product data once at startup
with open("product_catalog.md", "r", encoding="utf-8") as f:
    product_data = f.read()

# Create a single instance of ProductRAG
rag = ProductRAG(markdown_content=product_data)

# Models
class Message(BaseModel):
    id: str
    role: str
    content: str
    created_at: str

class Chat(BaseModel):
    id: str
    title: str
    messages: List[Message]
    created_at: str

class MessageRequest(BaseModel):
    chat_id: Optional[str] = None
    content: str

class ChatResponse(BaseModel):
    id: str
    title: str
    created_at: str

# Routes
@app.get("/api/chats", response_model=List[ChatResponse])
async def get_chats():
    return [
        ChatResponse(id=chat_id, title=chat["title"], created_at=chat["created_at"])
        for chat_id, chat in chats.items()
    ]

@app.post("/api/chats", response_model=ChatResponse)
async def create_chat():
    chat_id = str(uuid.uuid4())
    created_at = datetime.now().isoformat()
    chats[chat_id] = {
        "id": chat_id,
        "title": "New Chat",
        "messages": [],
        "created_at": created_at
    }
    return ChatResponse(id=chat_id, title="New Chat", created_at=created_at)

@app.get("/api/chats/{chat_id}", response_model=Chat)
async def get_chat(chat_id: str):
    if chat_id not in chats:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chats[chat_id]

@app.post("/api/chats/{chat_id}/title")
async def update_chat_title(chat_id: str, title: str):
    if chat_id not in chats:
        raise HTTPException(status_code=404, detail="Chat not found")
    chats[chat_id]["title"] = title
    return {"success": True}

@app.post("/api/messages")
async def create_message(message_request: MessageRequest):
    # Create a new chat if chat_id is not provided
    chat_id = message_request.chat_id
    if not chat_id or chat_id not in chats:
        chat_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()
        chats[chat_id] = {
            "id": chat_id,
            "title": "New Chat",
            "messages": [],
            "created_at": created_at
        }
    
    # Add user message to chat
    user_message_id = str(uuid.uuid4())
    user_message = {
        "id": user_message_id,
        "role": "user",
        "content": message_request.content,
        "created_at": datetime.now().isoformat()
    }
    chats[chat_id]["messages"].append(user_message)
    
    # Update chat title if it's the first message
    if chats[chat_id]["title"] == "New Chat" and len(chats[chat_id]["messages"]) == 1:
        title = message_request.content
        if len(title) > 30:
            title = title[:27] + "..."
        chats[chat_id]["title"] = title
    
    # Add assistant message placeholder
    assistant_message_id = str(uuid.uuid4())
    assistant_message = {
        "id": assistant_message_id,
        "role": "assistant",
        "content": "",
        "created_at": datetime.now().isoformat()
    }
    chats[chat_id]["messages"].append(assistant_message)
    
    return {
        "chat_id": chat_id,
        "message_id": assistant_message_id
    }

@app.get("/api/messages/{message_id}/stream")
async def stream_message(message_id: str, chat_id: str):
    # Find the chat and message
    if chat_id not in chats:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Find the message with the given ID
    for i, message in enumerate(chats[chat_id]["messages"]):
        if message["id"] == message_id and message["role"] == "assistant":
            # Get the previous user message
            if i > 0 and chats[chat_id]["messages"][i-1]["role"] == "user":
                user_message = chats[chat_id]["messages"][i-1]["content"]
                break
    else:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Stream the response
    async def event_generator():
        full_response = ""
        async for chunk in rag.stream_query(user_message):
            full_response += chunk
            yield f"data: {json.dumps({'content': chunk})}\n\n"
        
        # Update the message in our storage with the full response
        for message in chats[chat_id]["messages"]:
            if message["id"] == message_id:
                message["content"] = full_response
                break
                
        yield f"data: [DONE]\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )

@app.delete("/api/chats/{chat_id}")
async def delete_chat(chat_id: str):
    if chat_id not in chats:
        raise HTTPException(status_code=404, detail="Chat not found")
    del chats[chat_id]
    return {"success": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)