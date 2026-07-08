from __future__ import annotations

from fastapi import FastAPI


def create_app() -> FastAPI:
    application = FastAPI(
        title="LumenWatch Agent",
        version="0.1.0",
        description="Website change intelligence through REST and MCP.",
    )

    @application.get("/api/health", tags=["system"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": "lumenwatch-agent"}

    return application


app = create_app()

