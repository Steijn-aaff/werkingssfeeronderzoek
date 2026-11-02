import json
from pathlib import Path

import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import StreamingResponse
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from agent_sdk import ask

DIST = Path(__file__).parent / "frontend" / "dist"

async def api_ask(request: Request):
    body = await request.json()

    async def events():
        # One JSON object per line, so the page can show searches and text as they arrive
        try:
            async for kind, value in ask(body["company"], bool(body.get("website")), bool(body.get("kvk"))):
                yield json.dumps({"type": kind, "value": value}) + "\n"
        except Exception as e:
            yield json.dumps({"type": "error", "value": str(e)}) + "\n"

    return StreamingResponse(events(), media_type="application/x-ndjson")


if not (DIST / "index.html").exists():
    raise SystemExit("Frontend not built. Run: cd frontend && npm install && npm run build")

app = Starlette(routes=[
    Route("/api/ask", api_ask, methods=["POST"]),
    # Built React app
    Mount("/", StaticFiles(directory=DIST, html=True)),
])

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)
