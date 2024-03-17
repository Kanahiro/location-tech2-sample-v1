from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
import psycopg2


from app.model import PoiCreate

app = FastAPI()


def get_connection():
    dsn = "postgresql://postgres:postgres@postgis:5432/postgres"
    return psycopg2.connect(dsn)


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
    if len(_bbox) != 4 or not all(map(lambda x: x.replace(".", "").isdigit(), _bbox)):
        raise ValueError(
            "bboxの値が不正です。minx,miny,maxx,maxyの順で指定してください。"
        )
    minx, miny, maxx, maxy = list(map(float, _bbox))  # float型に変換

    with conn.cursor() as cur:
        # As Geojson
        cur.execute(
            "SELECT json_build_object(\
                'type', 'FeatureCollection',\
                'features', COALESCE(json_agg(ST_AsGeoJSON(poi.*)::json), '[]')\
            )\
            FROM poi \
            WHERE geom && ST_MakeEnvelope(%(minx)s, %(miny)s, %(maxx)s, %(maxy)s, 4326)\
            LIMIT 1000",
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


app.mount("/", StaticFiles(directory="static"), name="static")
