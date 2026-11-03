import json
from pathlib import Path

import uvicorn
from starlette.applications import Starlette
from starlette.concurrency import run_in_threadpool
from starlette.requests import Request
from starlette.responses import JSONResponse, Response, StreamingResponse
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from agent_sdk import run_case
from misc.pdf_report import markdown_to_pdf

DIST = Path(__file__).parent / "frontend" / "dist"

async def api_run_case(request: Request):
    body = await request.json()

    async def events():
        # One JSON object per line, so the page can show searches and text as they arrive
        try:
            async for kind, value in run_case(
                body["company"], 
                body.get("user_input", ""),
                bool(body.get("website")), 
                bool(body.get("kvk")),
                ):
                yield json.dumps({"type": kind, "value": value}) + "\n"
        except Exception as e:
            yield json.dumps({"type": "error", "value": str(e)}) + "\n"

    return StreamingResponse(events(), media_type="application/x-ndjson")

async def api_pdf(request: Request):
    body = await request.json()
    try:
        # PDF generation is blocking work, keep it off the event loop
        pdf = await run_in_threadpool(markdown_to_pdf, body["markdown"])
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    # The frontend chooses the file name; this one is only a fallback
    return Response(pdf, media_type="application/pdf", headers={"Content-Disposition": 'attachment; filename="werkingssfeeronderzoek.pdf"'})


if not (DIST / "index.html").exists():
    raise SystemExit("Frontend not built. Run: cd frontend && npm install && npm run build")

app = Starlette(routes=[
    Route("/api/run_case", api_run_case, methods=["POST"]),
    Route("/api/pdf", api_pdf, methods=["POST"]),
    # Built React app
    Mount("/", StaticFiles(directory=DIST, html=True)),
])

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)
