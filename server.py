from fastmcp import FastMCP, Context
import requests
from bs4 import BeautifulSoup
import os
from pydantic import BaseModel
import subprocess
import re
import json
import asyncio
import logging
from typing import Dict, Any

# Configure logging for detailed output
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Server configuration defined as a Pydantic model
class ServerConfig(BaseModel):
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    MCP_PATH: str = "/mcp"
    TIMEOUT: int = 60  # Increased timeout
    MAX_WORKERS: int = 4
    # Add other necessary configuration options here

# Read MCP path from environment variable or use default "/mcp"
mcp_path = os.environ.get("MCP_PATH", "/mcp")

# Create FastMCP object
mcp = FastMCP(
    "Dreamhack MCP",
    path="/mcp",
    lazy_load=True,  # Enable lazy loading for tool list lookup
    session_management=True  # Enable session management
)

# Global session management (kept for consistency, but not used in this minimal version)
session = None
session_id = None

# Decorator for tool registration (kept as is)
def register_tool(func):
    @mcp.tool()
    async def wrapper(*args, **kwargs):
        logger.debug(f"Calling tool wrapper: {func.__name__}")
        return await asyncio.to_thread(func, *args, **kwargs)
    return wrapper

# -------------------- TOOLS --------------------

# ONLY THE 'connect' tool is enabled for testing purposes.
# All other tools are commented out to isolate the issue.

# @register_tool
# def dreamhack_login(email: str, password: str) -> dict:
#     """Dreamhack 로그인"""
#     # ... (commented out) ...
#     pass

# @register_tool
# def fetch_problems() -> dict:
#     """문제 전체 목록 가져오기"""
#     # ... (commented out) ...
#     pass

# @register_tool
# def fetch_problems_by_difficulty(difficulty: str = "all") -> dict:
#     """난이도별 문제 목록 가져오기"""
#     # ... (commented out) ...
#     pass

# @register_tool
# def download_challenge(url: str, title: str) -> dict:
#     """문제 파일 다운로드 및 압축 해제"""
#     # ... (commented out) ...
#     pass

# @register_tool
# def deploy_challenge(challenge_dir: str) -> dict:
#     """문제 디렉토리에서 Docker 또는 app.py로 배포"""
#     # ... (commented out) ...
#     pass

# @register_tool
# def stop_challenge(deployment_type: str, image_name: str = None, process_id: int = None) -> dict:
#     """배포된 문제 서버 중지"""
#     # ... (commented out) ...
#     pass

# @register_tool
# def submit_flag(url: str, flag: str) -> dict:
#     """문제의 flag 제출"""
#     # ... (commented out) ...
#     pass

@mcp.tool()
def connect() -> dict:
    """Connect to the server"""
    logger.info("Connect tool called.")
    return {"message": "No configuration needed. Connect to run tools."}

# -------------------- PROMPTS --------------------

# All prompts are commented out for this test.

# @mcp.prompt()
# def login_prompt(email: str) -> str:
#     # ... (commented out) ...
#     pass

# @mcp.prompt()
# def problem_summary_prompt(title: str, category: str, difficulty: str) -> str:
#     # ... (commented out) ...
#     pass

# @mcp.prompt()
# def deploy_prompt(title: str) -> str:
#     # ... (commented out) ...
#     pass

# @mcp.prompt()
# def submit_flag_prompt(url: str) -> str:
#     # ... (commented out) ...
#     pass

# -------------------- RESOURCES --------------------

# All resources are commented out for this test.

# @mcp.resource("problems://all")
# def all_problems_resource():
#     # ... (commented out) ...
#     pass

# @mcp.resource("problems://{difficulty}")
# def problems_by_difficulty_resource(difficulty: str):
#     # ... (commented out) ...
#     pass

# @mcp.resource("challenge://{title}/files")
# def challenge_files_resource(title: str):
#     # ... (commented out) ...
#     pass

if __name__ == "__main__":
    logger.info("Starting FastMCP server with minimal configuration (connect tool only)...")
    # Smithery.ai uses process.env.PORT
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"  # Listen on all interfaces

    # Run FastMCP server
    mcp.run(
        transport="streamable-http",
        host=host,
        port=port,
        lazy_load=True,  # Enable lazy loading for tool list lookup
        session_management=True,  # Enable session management
        stream_resumable=True,  # Support stream resumption
        error_handling=True  # Enable error handling
    )
    logger.info("FastMCP server started.")
