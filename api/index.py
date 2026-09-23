from fastapi import FastAPI, Request

app = FastAPI()

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
def echo_path(path: str, request: Request):
    return {
        "received_param_path": path,
        "scope_path": request.scope.get("path"),
        "raw_url": str(request.url)
    }





