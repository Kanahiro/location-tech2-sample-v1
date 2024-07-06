import psycopg2
import psycopg2.pool
from fastapi import Depends, FastAPI, Response
from fastapi.staticfiles import StaticFiles

from app.model import PoiCreate, PoiUpdate

app = FastAPI()
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


@app.get("/pois")
def get_pois(conn=Depends(get_connection)):
    """
    PoIテーブルの地物をGeoJSONとして返す
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, name, ST_X(geom) as longitude, ST_Y(geom) as latitude FROM poi"
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
                "name": name,
            },
        }
        for id, name, longitude, latitude in res
    ]

    # GeoJSON-FeatureCollectionとしてレスポンス
    return {
        "type": "FeatureCollection",
        "features": features,
    }


@app.get("/pois_sql")
def get_pois_sql(conn=Depends(get_connection)):
    """
    PoIテーブルの地物をGeoJSONとして返す。GeoJSON-FeatureはSQLで生成
    """
    import json

    with conn.cursor() as cur:
        # As Geojson
        cur.execute("SELECT ST_AsGeoJSON(poi.*) FROM poi")
        res = cur.fetchall()

    # res[n][0] でGeoJSON形式の文字列が得られる

    # GeoJSON-Featureの配列
    features = [json.loads(row[0]) for row in res]

    # GeoJSON-FeatureCollectionとしてレスポンス
    return {
        "type": "FeatureCollection",
        "features": features,
    }


@app.get("/pois_sql2")
def get_pois_sql2(bbox: str, conn=Depends(get_connection)):
    """
    PoIテーブルの地物をGeoJSONとして返す。GeoJSON-FeatureCollectionはSQLで生成
    """

    # クエリパラメータbboxの値をチェック
    _bbox = bbox.split(",")
    if len(_bbox) != 4:
        raise ValueError(
            "bboxの値が不正です。minx,miny,maxx,maxyの順で指定してください。"
        )
    minx, miny, maxx, maxy = list(map(float, _bbox))  # float型に変換

    with conn.cursor() as cur:
        # As Geojson
        cur.execute(
            """SELECT json_build_object(
                'type', 'FeatureCollection',
                'features', COALESCE(json_agg(ST_AsGeoJSON(poi.*)::json), '[]'::json)
            )
            FROM poi 
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
    return res[0][0]  # dict型


@app.post("/pois")
def create_poi(data: PoiCreate, conn=Depends(get_connection)):
    """
    PoIテーブルに地物を追加
    """

    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO poi (name, geom) VALUES (%s, ST_SetSRID(ST_MakePoint(%s, %s), 4326))",
            (data.name, data.longitude, data.latitude),
        )
        conn.commit()

        # 作成した地物のIDを取得
        cur.execute("SELECT lastval()")
        res = cur.fetchone()
        _id = res[0]

        # 作成した地物の情報を取得
        cur.execute(
            "SELECT id, name, ST_X(geom) as longitude, ST_Y(geom) as latitude FROM poi WHERE id = %s",
            (_id,),
        )
        id, name, longitude, latitude = cur.fetchone()

    # 作成した地物をGeoJSONとして返す
    return {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [longitude, latitude],
        },
        "properties": {
            "id": id,
            "name": name,
        },
    }


@app.delete("/pois/{id}")
def delete_poi(id: int, conn=Depends(get_connection)):
    """
    PoIテーブルの地物を削除
    """
    with conn.cursor() as cur:
        cur.execute("DELETE FROM poi WHERE id = %s", (id,))
        conn.commit()

    return Response(status_code=204)  # 204 No Contentを返す


@app.patch("/pois/{poi_id}")
def update_poi(poi_id: int, data: PoiUpdate, conn=Depends(get_connection)):
    """
    PoIテーブルの地物を更新
    """
    with conn.cursor() as cur:
        # 更新対象の地物が存在するか確認
        cur.execute("SELECT id FROM poi WHERE id = %s", (poi_id,))
        if not cur.fetchone():
            return Response(status_code=404)

        # 更新
        cur.execute(
            """UPDATE poi SET
                name = COALESCE(%s, name),
                geom = ST_SetSRID(ST_MakePoint(COALESCE(%s, ST_X(geom)), COALESCE(%s, ST_Y(geom))), 4326)
                WHERE id = %s""",
            (data.name, data.longitude, data.latitude, poi_id),
        )
        conn.commit()

        # 更新した地物の情報を取得
        cur.execute(
            "SELECT id, name, ST_X(geom) as longitude, ST_Y(geom) as latitude FROM poi WHERE id = %s",
            (poi_id,),
        )
        _id, name, longitude, latitude = cur.fetchone()

    # 更新した地物をGeoJSONとして返す
    return {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [longitude, latitude],
        },
        "properties": {
            "id": _id,
            "name": name,
        },
    }


@app.get("/pois/tiles/{z}/{x}/{y}.pbf")
def get_pois_tiles(z: int, x: int, y: int, conn=Depends(get_connection)):
    """
    PoIテーブルの地物をMVTとして返す
    """
    with conn.cursor() as cur:
        cur.execute(
            """WITH mvtgeom AS (
                SELECT ST_AsMVTGeom(ST_Transform(geom, 3857), ST_TileEnvelope(%(z)s, %(x)s, %(y)s)) AS geom, id, name
                FROM poi
                WHERE ST_Transform(geom, 3857) && ST_TileEnvelope(%(z)s, %(x)s, %(y)s)
            )
            SELECT ST_AsMVT(mvtgeom.*, 'poi', 4096, 'geom')
            FROM mvtgeom;""",
            {"z": z, "x": x, "y": y},
        )
        val = cur.fetchone()[0]
    # MapboxVectorTileファイルとしてレスポンス
    return Response(
        content=val.tobytes(), media_type="application/vnd.mapbox-vector-tile"
    )


app.mount("/", StaticFiles(directory="static"), name="static")
