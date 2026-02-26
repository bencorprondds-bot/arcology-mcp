FROM python:3.12-slim

WORKDIR /app

# Install dependencies directly (no wheel build needed)
RUN pip install --no-cache-dir "fastmcp>=2.0.0" "httpx>=0.27.0" "pydantic>=2.0.0"

# Copy application code
COPY *.py .

# Default to SSE transport for production
ENV MCP_TRANSPORT=sse
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=8000

EXPOSE 8000

CMD ["python", "server.py"]
