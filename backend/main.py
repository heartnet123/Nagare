from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from routers import evaluations, agents, datasets, monitoring, logs, chat, mcp, memory, agent_config, sessions, history
from middleware.error_handler import (
    http_error_handler,
    validation_error_handler,
    general_error_handler
)
from services.session_manager import SessionManager

app = FastAPI(
    title="NAGARE OS API",
    description="API for NAGARE OS - AI Operating System for RAG pipelines",
    version="0.1.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Nuxt dev server
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# Error handlers
app.add_exception_handler(StarletteHTTPException, http_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(Exception, general_error_handler)

session_manager = SessionManager()
sessions._register(session_manager)
history._register(session_manager)
chat._register(session_manager)

# Mount routers
app.include_router(evaluations.router)
app.include_router(agents.router)
app.include_router(datasets.router)
app.include_router(monitoring.router)
app.include_router(logs.router)
app.include_router(chat.router)
app.include_router(mcp.router)
app.include_router(memory.router)
app.include_router(agent_config.router)
app.include_router(sessions.router)
app.include_router(history.router)



@app.get("/")
async def root():
    return {
        "name": "NAGARE OS API",
        "version": "0.1.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
