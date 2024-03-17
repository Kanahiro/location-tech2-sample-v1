CREATE TABLE IF NOT EXISTS poi (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  geom GEOMETRY(POINT, 4326) NOT NULL
);

CREATE INDEX poi_geom_idx ON poi USING GIST (geom);

DELETE ROWS FROM poi WHERE name LIKE '平面直角座標系%'; -- 既存のデータを削除
INSERT INTO poi (name, geom) VALUES
  ('平面直角座標系: 1系原点', ST_GeomFromText('POINT(127.5 26)', 4326)),
  ('平面直角座標系: 2系原点', ST_GeomFromText('POINT(131.0 33)', 4326)),
  ('平面直角座標系: 3系原点', ST_GeomFromText('POINT(132.1666666 36)', 4326)),
  ('平面直角座標系: 4系原点', ST_GeomFromText('POINT(133.5 33)', 4326)),
  ('平面直角座標系: 5系原点', ST_GeomFromText('POINT(134.3333333 36)', 4326)),
  ('平面直角座標系: 6系原点', ST_GeomFromText('POINT(136.0 36)', 4326)),
  ('平面直角座標系: 7系原点', ST_GeomFromText('POINT(137.1666666 36)', 4326)),
  ('平面直角座標系: 8系原点', ST_GeomFromText('POINT(138.5 36)', 4326)),
  ('平面直角座標系: 9系原点', ST_GeomFromText('POINT(139.8333333 36)', 4326)),
  ('平面直角座標系: 10系原点', ST_GeomFromText('POINT(140.8333333 40)', 4326)),
  ('平面直角座標系: 11系原点', ST_GeomFromText('POINT(140.25 44)', 4326)),
  ('平面直角座標系: 12系原点', ST_GeomFromText('POINT(142.25 44)', 4326)),
  ('平面直角座標系: 13系原点', ST_GeomFromText('POINT(144.25 44)', 4326)),
  ('平面直角座標系: 14系原点', ST_GeomFromText('POINT(142.0 26)', 4326)),
  ('平面直角座標系: 15系原点', ST_GeomFromText('POINT(127.5 26)', 4326)),
  ('平面直角座標系: 16系原点', ST_GeomFromText('POINT(124.0 26)', 4326)),
  ('平面直角座標系: 17系原点', ST_GeomFromText('POINT(131.0 26)', 4326)),
  ('平面直角座標系: 18系原点', ST_GeomFromText('POINT(136.0 20)', 4326)),
  ('平面直角座標系: 19系原点', ST_GeomFromText('POINT(154.0 26)', 4326));