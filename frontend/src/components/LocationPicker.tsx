import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, useMapEvents } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';

// Configure default icon
L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
});

// Create a custom icon instance (ensures proper sizing)
const defaultMarkerIcon = new L.Icon({
  iconUrl: markerIcon,
  iconRetinaUrl: markerIcon2x,
  shadowUrl: markerShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  tooltipAnchor: [16, -28],
});

interface LocationPickerProps {
  initialPosition: { lat: number; lng: number };
  onLocationSelect: (lat: number, lng: number) => void;
  // Optional bounds to restrict map view (e.g., Tehran area)
  bounds?: [[number, number], [number, number]];
}

export const LocationPicker: React.FC<LocationPickerProps> = ({ initialPosition, onLocationSelect, bounds }) => {
  const [position, setPosition] = useState(initialPosition);

  // Sync map view when position changes externally
  const MapUpdater = () => {
    const map = useMapEvents({});
    useEffect(() => {
      map.setView([position.lat, position.lng], map.getZoom(), { animate: true });
    }, [position, map]);
    return null;
  };

  // Handle clicks on the map
  const ClickHandler = () => {
    useMapEvents({
      click(e) {
        const { lat, lng } = e.latlng;
        setPosition({ lat, lng });
        onLocationSelect(lat, lng);
      },
    });
    return null;
  };

  return (
    <div className="rounded-xl overflow-hidden shadow-lg border border-emerald-100">
      <MapContainer
        center={[initialPosition.lat, initialPosition.lng]}
        zoom={13}
        className="h-64 w-full"
        style={{ height: '300px' }}
        // Performance tweaks
        preferCanvas={true}
        scrollWheelZoom={true}
        maxZoom={18}
        minZoom={10}
        // Optional bounds to keep user inside a region
        {...(bounds ? { maxBounds: bounds, maxBoundsViscosity: 1.0 } : {})}
      >
        <TileLayer
          attribution='&copy; <a href="https://osm.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <Marker position={[position.lat, position.lng]} icon={defaultMarkerIcon} />
        <MapUpdater />
        <ClickHandler />
      </MapContainer>
      <div className="p-2 text-xs text-slate-500 text-center bg-emerald-50">
        موقعیت فعلی: Latitude {position.lat.toFixed(4)}, Longitude {position.lng.toFixed(4)}
      </div>
    </div>
  );
};
