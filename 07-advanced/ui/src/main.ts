import 'maplibre-gl/dist/maplibre-gl.css';
import { Map, Marker, Popup } from 'maplibre-gl';

import { createPoint, loadPoints, deletePoint, satelliteImageUrl } from './api';

const map = new Map({
    container: 'app',
    maxZoom: 18,
    center: [139.767125, 35.681236],
    style: {
        version: 8,
        sources: {
            osm: {
                type: 'raster',
                tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
                tileSize: 256,
                attribution:
                    "© OpenStreetMap contributors | Copernicus Sentinel data 2024' for Sentinel data",
            },
        },
        layers: [
            {
                id: 'osm',
                type: 'raster',
                source: 'osm',
            },
        ],
    },
});

// Marker関連の処理
const markers: Marker[] = [];
let isMarkerClicked = false;

const createPopupDom = (id: string) => {
    /**
     * ポップアップ内に埋め込みたい、以下のような構造のDOMを作成して返す
     * <div style="display: flex; flex-direction: column;">
     *  <a href="satelliteImageUrl(id, 1024)">
     *   <img src="satelliteImageUrl(id)" width="256" height="256" />
     *  </a>
     *  <button onclick="deleteMarker('id')">削除</button>
     * </div>
     */

    const popupDom = document.createElement('div');
    popupDom.style.display = 'flex';
    popupDom.style.flexDirection = 'column';

    const anchor = document.createElement('a');
    anchor.href = satelliteImageUrl(id, 1024);
    anchor.innerHTML = `<img src="${satelliteImageUrl(
        id,
    )}" width="256" height="256" />`;

    const buttonDom = document.createElement('button');
    buttonDom.textContent = '削除';
    buttonDom.onclick = async () => {
        if (!confirm('地点を削除しますか？')) return;
        await deletePoint(id);
        clearMarkers();
        await loadMarkers();
    };

    popupDom.appendChild(anchor);
    popupDom.appendChild(buttonDom);
    return popupDom;
};

const loadMarkers = async () => {
    const points = await loadPoints();
    points.features.forEach((feature) => {
        const popup = new Popup().setMaxWidth('500px');
        const marker = new Marker()
            .setLngLat(feature.geometry.coordinates)
            .addTo(map)
            .setPopup(popup);
        marker.getElement().addEventListener('click', () => {
            isMarkerClicked = true;
            // ピンのクリック時に画像を読み込ませたいので、DOMを作成するタイミングをマーカーのクリック時にする
            popup.setDOMContent(createPopupDom(feature.properties.id));
        });
        markers.push(marker);
    });
};

const clearMarkers = () => {
    markers.forEach((marker) => marker.remove());
};

map.on('load', async () => {
    await loadMarkers();
});

map.on('click', async (e) => {
    if (isMarkerClicked) {
        // ピンのクリックであれば、以降の処理をしない
        isMarkerClicked = false;
        return;
    }

    if (!confirm('地点を作成しますか？')) return;

    const { lng, lat } = e.lngLat;
    await createPoint({ longitude: lng, latitude: lat });
    clearMarkers();
    await loadMarkers();
});
