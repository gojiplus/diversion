export default function ({ data, parentElement }) {
  const container = parentElement.querySelector('#map');
  const status = parentElement.querySelector('#status');
  let disposed = false;
  let map;
  const overlays = [];
  status.textContent = 'Loading Google Maps…';
  const showUnavailable = () => {
    if (!disposed) status.textContent = 'Map unavailable. Use the itinerary and Open walk in Google Maps link below.';
  };
  window.addEventListener('diversion-map-auth-failure', showUnavailable);
  function loadMaps(key) {
    if (window.google?.maps?.Map) return Promise.resolve();
    if (!window.diversionMapsLoader) {
      window.diversionMapsLoader = new Promise((resolve, reject) => {
        const script = document.createElement('script');
        window.diversionMapsReady = () => {
          delete window.diversionMapsReady;
          resolve();
        };
        window.gm_authFailure = () => {
          window.dispatchEvent(new Event('diversion-map-auth-failure'));
          reject(new Error('Map authorization failed.'));
        };
        script.onerror = () => {
          script.remove();
          delete window.diversionMapsLoader;
          reject(new Error('Map could not load.'));
        };
        const params = new URLSearchParams({ key, v: 'weekly', loading: 'async', callback: 'diversionMapsReady' });
        script.src = 'https://maps.googleapis.com/maps/api/js?' + params.toString();
        script.async = true;
        document.head.appendChild(script);
      });
    }
    return window.diversionMapsLoader;
  }
  loadMaps(data.key).then(() => {
    if (disposed) return;
    if (!data.points.length) throw new Error('No route geometry.');
    map = new google.maps.Map(container, {
      center: data.points[0], zoom: 14, mapTypeControl: false, streetViewControl: false,
    });
    const bounds = new google.maps.LatLngBounds();
    data.points.forEach(point => bounds.extend(point));
    overlays.push(new google.maps.Polyline({
      path: data.points, strokeColor: '#176b52', strokeWeight: 5, map,
    }));
    const markers = [
      { name: 'Start', position: data.points[0] },
      ...data.stops.map((stop, i) => ({ ...stop, name: `${i + 1}. ${stop.name}` })),
      { name: 'Finish', position: data.points.at(-1) },
    ];
    markers.forEach(stop => {
      const circle = new google.maps.Circle({
        map, center: stop.position, radius: 18, fillColor: '#176b52',
        fillOpacity: 1, strokeColor: '#fff', strokeWeight: 2,
      });
      const label = document.createElement('div');
      label.textContent = stop.name;
      const info = new google.maps.InfoWindow({ content: label, position: stop.position });
      circle.addListener('click', () => info.open({ map }));
      overlays.push(circle, info);
      bounds.extend(stop.position);
    });
    map.fitBounds(bounds, 36);
    status.textContent = 'Selected walk. Stops are listed below the map.';
  }).catch(showUnavailable);
  return () => {
    disposed = true;
    window.removeEventListener('diversion-map-auth-failure', showUnavailable);
    overlays.forEach(overlay => {
      google.maps.event.clearInstanceListeners(overlay);
      if (overlay.setMap) overlay.setMap(null);
      if (overlay.close) overlay.close();
    });
    if (map) google.maps.event.clearInstanceListeners(map);
  };
}
