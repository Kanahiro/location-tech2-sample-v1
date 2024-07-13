# 位置情報デベロッパー養成講座　サンプルコード集

トピックごとにディレクトリが分かれています。各トピックの実装は、それぞれのディレクトリ内で完結しており、04-01を除き、`docker compose`により起動できるようになっています。

```sh
# 04-02を起動する例
cd 04-0２-static-mbtiles
docker compose up # 起動
docker compose down # 終了
```

キャッシュが悪さすることがあるかもしれませんので、適宜、ビルドキャッシュをクリアして進めてください。

```sh
docker compose build --no-cache
docker compose up
```

## 目次

- [第4章：タイルサーバーの実装 - ディレクトリ形式のタイルを配信する](./04-01-static-directory/)
- [第4章：タイルサーバーの実装 - MBTiles形式のタイルを配信する](./04-02-static-mbtiles/)
- [第4章：タイルサーバーの実装 - PMTiles形式のタイルを配信する](./04-03-static-pmtiles/)
- [第4章：タイルサーバーの実装 - 動的にタイルを作成して配信する](./04-04-dynamic-tile/)
- [第5章：ベクトルデータのCRUD処理](./05-vector-crud/)
- [第6章：衛星画像配信サーバーの構築](./06-satellite/)
- [第7章：ベクトル・ラスターを組み合わせたアプリケーション開発](./07-advanced/)
