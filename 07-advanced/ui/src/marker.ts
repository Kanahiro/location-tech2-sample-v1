import { Map, Marker, Popup } from 'maplibre-gl';
import { loadPoints } from './api';

const initMarker = (map: Map) => {
    // Marker関連の処理
    const markers: Marker[] = [];

    const loadMarkers = async () => {
        const points = await loadPoints();
        points.features.forEach((feature) => {
            const marker = new Marker()
                .setLngLat(feature.geometry.coordinates)
                .addTo(map)
                .setPopup(
                    new Popup().setHTML(
                        `<button onclick="deleteMarker('${feature.properties.id}')">削除</button>`,
                    ),
                );
            marker.getElement().addEventListener('click', () => {
                isMarkerClicked = true;
            });
            markers.push(marker);
        });
    };

    const clearMarkers = () => {
        markers.forEach((marker) => marker.remove());
    };

    return { loadMarkers, clearMarkers };
};

export { initMarker };
