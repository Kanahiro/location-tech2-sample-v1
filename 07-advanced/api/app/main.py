import psycopg2
import psycopg2.pool
from fastapi import Depends, FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

from app.model import PointCreate, PointUpdate

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
    conn = pool.getconn()
    yield conn
    pool.putconn(conn)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/points")
def get_points(bbox: str, conn=Depends(get_connection)):
    """
    pointsテーブルの地物をGeoJSONとして返す。GeoJSON-FeatureCollectionはSQLで生成
    """

    # クエリパラメータbboxの値をチェック
    _bbox = bbox.split(",")
    if len(_bbox) != 4:
        raise ValueError(
            "bboxの値が不正です。minx,miny,maxx,maxyの順で指定してください。"
        )
    minx, miny, maxx, maxy = list(map(float, _bbox))

    with conn.cursor() as cur:
        cur.execute(
            """SELECT json_build_object(
                'type', 'FeatureCollection',
                'features', COALESCE(json_agg(ST_AsGeoJSON(points.*)::json), '[]'::json)
            )
            FROM points 
            WHERE geom && ST_MakeEnvelope(%(minx)s, %(miny)s, %(maxx)s, %(maxy)s, 4326)
            LIMIT 1000""",
            {
                "minx": minx,
                "miny": miny,
                "maxx": maxx,
                "maxy": maxy,
            },
        )
        res = cur.fetchall()
    return res[0][0]


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


@app.patch("/points/{id}")
def update_point(id: int, data: PointUpdate, conn=Depends(get_connection)):
    """
    pointsテーブルの地物を更新
    """
    with conn.cursor() as cur:
        # 更新対象の地物が存在するか確認
        cur.execute("SELECT id FROM points WHERE id = %s", (id,))
        if not cur.fetchone():
            return Response(status_code=404)

        # 更新
        cur.execute(
            """UPDATE points SET
                geom = ST_SetSRID(ST_MakePoint(COALESCE(%s, ST_X(geom)), COALESCE(%s, ST_Y(geom))), 4326)
                WHERE id = %s""",
            (data.longitude, data.latitude, id),
        )
        conn.commit()

        # 更新した地物の情報を取得
        cur.execute(
            "SELECT id, ST_X(geom) as longitude, ST_Y(geom) as latitude FROM points WHERE id = %s",
            (id,),
        )
        _id, longitude, latitude = cur.fetchone()

    # 更新した地物をGeoJSONとして返す
    return {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [longitude, latitude],
        },
        "properties": {
            "id": _id,
        },
    }


@app.get("/points/tiles/{z}/{x}/{y}.pbf")
def get_points_tiles(z: int, x: int, y: int, conn=Depends(get_connection)):
    """
    pointsテーブルの地物をMVTとして返す
    """
    with conn.cursor() as cur:
        cur.execute(
            """WITH mvtgeom AS (
                SELECT ST_AsMVTGeom(ST_Transform(geom, 3857), ST_TileEnvelope(%(z)s, %(x)s, %(y)s)) AS geom, id
                FROM points
                WHERE ST_Transform(geom, 3857) && ST_TileEnvelope(%(z)s, %(x)s, %(y)s)
            )
            SELECT ST_AsMVT(mvtgeom.*, 'points', 4096, 'geom')
            FROM mvtgeom;""",
            {"z": z, "x": x, "y": y},
        )
        val = cur.fetchone()[0]
    # MapboxVectorTileファイルとしてレスポンス
    return Response(
        content=val.tobytes(), media_type="application/vnd.mapbox-vector-tile"
    )


@app.get("/search")
def search_image(point_id: int, conn=Depends(get_connection)):
    """
    DBに登録された地点を指定して、その地点を含む衛星画像を検索
    """
    # pointsテーブルから指定したIDのデータを取得
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, ST_X(geom) as longitude, ST_Y(geom) as latitude FROM points WHERE id = %s",
            (point_id,),
        )
        res = cur.fetchone()

    # データが存在しない場合は404を返す
    if not res:
        return Response(status_code=404)

    _id, longitude, latitude = res

    # TODO: STAChを使って衛星画像を検索する処理を追加

    dataset = {"files": []}
    return {"datasets": []}
