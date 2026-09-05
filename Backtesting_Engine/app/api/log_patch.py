from fastapi import Request
from fastapi.responses import JSONResponse
import traceback

def add_exception_handler(app):
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        with open("crash_log.txt", "a") as f:
            f.write(f"CRASH on {request.url}\n")
            traceback.print_exc(file=f)
        return JSONResponse(status_code=500, content={"message": "Internal Server Error", "details": str(exc)})
