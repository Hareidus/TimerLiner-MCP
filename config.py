"""MCP Server configuration."""

import os

BACKEND_BASE_URL = os.getenv("TIMELINER_BACKEND_URL", "http://localhost:8080/api")
REQUEST_TIMEOUT = float(os.getenv("TIMELINER_REQUEST_TIMEOUT", "30"))

# 连接时自动登录的凭据（通过 env 传入）
AUTH_USERNAME = os.getenv("TIMELINER_USERNAME", "")
AUTH_PASSWORD = os.getenv("TIMELINER_PASSWORD", "")
