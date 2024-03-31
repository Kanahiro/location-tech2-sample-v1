from fastapi import FastAPI, Response
from fastapi.staticfiles import StaticFiles
from aiopmtiles import Reader

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/vector/{z}/{x}/{y}.pbf")
async def vectortile(z: int, x: int, y: int):
    async with Reader("http://fileserver/vector.pmtiles") as pmtiles:
        tile_data = await pmtiles.get_tile(z, x, y)

    if tile_data is None:
        return Response(status_code=404)

    return Response(
        content=tile_data,
        media_type="application/vnd.mapbox-vector-tile",
        headers={"content-encoding": "gzip"},
    )


@app.get("/raster/{z}/{x}/{y}.png")
async def rastertile(z: int, x: int, y: int):
    async with Reader("http://fileserver/raster.pmtiles") as pmtiles:
        tile_data = await pmtiles.get_tile(z, x, y)
    if tile_data is None:
        return Response(status_code=404)
    return Response(content=tile_data, media_type="image/png")


app.mount("/", StaticFiles(directory="static"), name="static")
