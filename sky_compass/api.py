from sky_compass.types import CompassRequest, CompassResponse
from sky_compass.compass_io import deserialized_io

try:
    from fastapi import FastAPI
except ImportError:
    api_enabled = False
else:
    api_enabled = True

if api_enabled:
    app = FastAPI()

    @app.post("/")
    async def process_request(request: CompassRequest) -> CompassResponse:
        return deserialized_io(request)
