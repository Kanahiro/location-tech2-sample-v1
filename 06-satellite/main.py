import asyncio

from fastapi import FastAPI, Response
from fastapi.staticfiles import StaticFiles
from rio_tiler.io import Reader
from rio_tiler.profiles import img_profiles

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/rgbnir.png")
async def make_image():
    with Reader("static/rgbnir.tif", options={"unscale": 0.1}) as image:
        imgdata = image.read([1, 2, 3])
    png = imgdata.render(img_format="PNG", **img_profiles.get("png"))
    return Response(png, media_type="image/png")


@app.get("/rgbnir_cog.png")
async def make_image_cog(scale_min: float, scale_max: float):
    with Reader("static/rgbnir_cog.tif") as image:
        imgdata = image.preview([1, 2, 3])  # band-1, 2, 3
        imgdata.rescale(((scale_min, scale_max),))
        png = imgdata.render(img_format="PNG", **img_profiles.get("png"))
    return Response(png, media_type="image/png")


@app.get("/ndvi.png")
async def make_image_ndvi():
    with Reader("static/rgbnir_cog.tif") as image:
        imgdata = image.preview(expression="(b4-b1)/(b4+b1)")  # 2バンドを利用した計算式
        imgdata.rescale(((0, 1),))  # 0-1を0-255に変換
        png = imgdata.render(img_format="PNG", **img_profiles.get("png"))
    return Response(png, media_type="image/png")


@app.get("/rgbnir_remote_cog.png")
async def make_image_remote_cog(scale_min: float, scale_max: float):
    with Reader("http://fileserver/rgbnir_cog.tif") as image:
        imgdata = image.preview([1, 2, 3])  # band-1, 2, 3
        imgdata.rescale(((scale_min, scale_max),))
        png = imgdata.render(img_format="PNG", **img_profiles.get("png"))
    return Response(png, media_type="image/png")


@app.get("/rgbnir_remote_cog_part.png")
async def make_image_remote_cog_part(
    minx: float,
    miny: float,
    maxx: float,
    maxy: float,
    max_size: int = 256,
    scale_min: float = 0,
    scale_max: float = 2000,
):
    with Reader("http://fileserver/rgbnir_cog.tif") as image:
        imgdata = image.part(
            bbox=(minx, miny, maxx, maxy),
            indexes=(1, 2, 3),
            dst_crs="EPSG:32654",  # オリジナルデータのCRS
            max_size=max_size,  # 1辺の最大解像度
        )
        imgdata.rescale(((scale_min, scale_max),))
        png = imgdata.render(img_format="PNG", **img_profiles.get("png"))
    return Response(png, media_type="image/png")


def get_tile(
    url: str,
    z: int,
    x: int,
    y: int,
    indexes: tuple[int, ...] | None,
    scale_min: float,
    scale_max: float,
):
    """
    COGからデータを取得・タイル画像を生成する関数
    """
    with Reader(url) as image:
        if not image.tile_exists(x, y, z):
            return None
        imgdata = image.tile(x, y, z, indexes=indexes, resampling_method="bilinear")
        imgdata.rescale(((scale_min, scale_max),))
        png = imgdata.render(img_format="PNG", **img_profiles.get("png"))
        return png


@app.get("/tiles/{z}/{x}/{y}.png")
async def make_image_remote_cog_tile(
    z: int,
    x: int,
    y: int,
    scale_min: float = 0,
    scale_max: float = 2000,
):
    if z < 6:
        # ズームレベル6以下は404を返す
        return Response(status_code=404)

    loop = asyncio.get_event_loop()
    png = await loop.run_in_executor(
        None,
        get_tile,
        "http://fileserver/rgbnir_cog.tif",
        z,
        x,
        y,
        (1, 2, 3),
        scale_min,
        scale_max,
    )

    return Response(png, media_type="image/png")


@app.get("/tiles/B02/{z}/{x}/{y}.png")
async def make_image_remote_b02_tile(
    z: int,
    x: int,
    y: int,
    scale_min: float = 0,
    scale_max: float = 2000,
):
    if z < 6:
        # ズームレベル6以下は404を返す
        return Response(status_code=404)

    loop = asyncio.get_event_loop()
    png = await loop.run_in_executor(
        None,
        get_tile,
        "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/54/T/WN/2023/11/S2B_54TWN_20231118_1_L2A/B02.tif",
        z,
        x,
        y,
        None,
        scale_min,
        scale_max,
    )

    return Response(png, media_type="image/png")


app.mount("/", StaticFiles(directory="static"), name="static")
