"""Run the patent search API server."""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8766,
        log_level="info",
    )
