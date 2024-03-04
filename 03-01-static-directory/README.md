## データ出典

- [国土数値情報](http://nlftp.mlit.go.jp/ksj/index.html) - 学校データ
- [Natural Earth](http://www.naturalearthdata.com/) - 1:10m Natural Earth II

## サーバーの起動

NginxでWebサーバーを起動します。

```sh
$ docker run --rm -d -p 8080:80 -v $(pwd):/usr/share/nginx/html nginx
```