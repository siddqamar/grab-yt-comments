import argparse

import uvicorn

from api import app as fastapi_app


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Desktop FastAPI sidecar for GrabComments.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    uvicorn.run(fastapi_app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
