import httpx
import psycopg2
import psycopg2.pool
from fastapi import Depends, FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from rio_tiler.io import Reader

from app.model import PointCreate

app = FastAPI()

# フロントエンドからのクロスオリジンリクエストを許可
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
)

pool = psycopg2.pool.SimpleConnectionPool(
    dsn="postgresql://postgres:postgres@postgis:5432/postgres", minconn=2, maxconn=4
)


def get_connection():
    try:
        conn = pool.getconn()
        yield conn
    finally:
        pool.putconn(conn)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/points")
def get_points(conn=Depends(get_connection)):
    """
    pointsテーブルの地物をGeoJSONとして返す
    """

    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, ST_X(geom) as longitude, ST_Y(geom) as latitude FROM points"
        )
        res = cur.fetchall()

    # GeoJSON-Featureの配列
    features = [
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [longitude, latitude],
            },
            "properties": {
                "id": id,
            },
        }
        for id, longitude, latitude in res
    ]

    # GeoJSON-FeatureCollectionとしてレスポンス
    return {
        "type": "FeatureCollection",
        "features": features,
    }


@app.post("/points")
def create_point(data: PointCreate, conn=Depends(get_connection)):
    """
    pointsテーブルに地物を追加
    """

    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO points (geom) VALUES (ST_SetSRID(ST_MakePoint(%s, %s), 4326))",
            (data.longitude, data.latitude),
        )
        conn.commit()

        # 作成した地物のIDを取得
        cur.execute("SELECT lastval()")
        res = cur.fetchone()
        _id = res[0]

        # 作成した地物の情報を取得
        cur.execute(
            "SELECT id, ST_X(geom) as longitude, ST_Y(geom) as latitude FROM points WHERE id = %s",
            (_id,),
        )
        id, longitude, latitude = cur.fetchone()

    # 作成した地物をGeoJSONとして返す
    return {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [longitude, latitude],
        },
        "properties": {
            "id": id,
        },
    }


@app.delete("/points/{id}")
def delete_point(id: int, conn=Depends(get_connection)):
    """
    pointsテーブルの地物を削除
    """
    with conn.cursor() as cur:
        cur.execute("DELETE FROM points WHERE id = %s", (id,))
        conn.commit()

    return Response(status_code=204)  # 204 No Contentを返す


@app.get("/points/{point_id}/satellite.jpg")
async def sattelite_preview(
    point_id: int, max_size: int = 256, conn=Depends(get_connection)
):
    """
    DBに登録された地点を指定して、その地点を含む衛星画像を検索
    """
    if max_size > 1024:
        # 1024pxを超えるサイズは許可しない
        return Response(status_code=400)

    # pointsテーブルから指定したIDのデータを取得
    with conn.cursor() as cur:
        cur.execute(
            "SELECT ST_X(geom) as longitude, ST_Y(geom) as latitude FROM points WHERE id = %s",
            (point_id,),
        )
        res = cur.fetchone()

    # データが存在しない場合は404を返す
    if not res:
        return Response(status_code=404)

    longitude, latitude = res

    # 衛星画像を検索
    # 便宜上、地点から一定距離の範囲で検索
    buffer = 0.01
    minx = longitude - buffer
    miny = latitude - buffer
    maxx = longitude + buffer
    maxy = latitude + buffer

    result = await search_dataset(minx, miny, maxx, maxy, limit=1)
    if len(result["features"]) == 0:
        return Response(status_code=404)

    feature = result["features"][0]  # 最初の1件（＝最新）を取得
    cog_url = feature["assets"]["visual"]["href"]  # 可視光データ

    with Reader(cog_url) as src:
        img = src.preview(max_size=max_size)
    jpg = img.render(img_format="JPEG")

    return Response(content=jpg, media_type="image/jpg")


async def search_dataset(
    minx: float, miny: float, maxx: float, maxy: float, limit: int = 12
):
    """
    STACを使って衛星画像を検索
    """

    url = "https://earth-search.aws.element84.com/v1/collections/sentinel-2-l2a/items"
    params = {
        "limit": limit,
        "bbox": f"{minx},{miny},{maxx},{maxy}",
    }
    headers = {
        "Accept": "application/json",
    }

    async with httpx.AsyncClient() as client:
        res = await client.get(url, params=params, headers=headers)
        res.raise_for_status()
        dataset = res.json()

    return dataset
