<template>
  <div id="map-container" class="relative">
    <div id="mapdiv" style="height: 100vh;"></div>
    <!-- Add location button -->
    <button 
      @click="centerOnUser"
      class="absolute bottom-6 right-6 bg-white p-3 rounded-full shadow-lg hover:bg-gray-50 z-[1000]"
      title="Go to my location"
    >
      <svg 
        xmlns="http://www.w3.org/2000/svg" 
        class="h-6 w-6 text-red-600" 
        fill="none" 
        viewBox="0 0 24 24" 
        stroke="currentColor"
      >
        <path 
          strokeLinecap="round" 
          strokeLinejoin="round" 
          strokeWidth="2" 
          d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
        />
        <path 
          strokeLinecap="round" 
          strokeLinejoin="round" 
          strokeWidth="2" 
          d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
        />
      </svg>
    </button>
  </div>
</template>

<script>
import { onMounted, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Import marker images for Leaflet
import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';
import userIconImage from '../assets/human.webp';
import redIcon from '../assets/red.png';
import orangeIcon from '../assets/orange.png';
import greenIcon from '../assets/green.png';
import purpleIcon from '../assets/purple.png'

// Define custom icons for landmarks
const RedIcon = L.icon({
  iconUrl: redIcon,
  iconSize: [100, 50],      
  iconAnchor: [12, 41],    
  popupAnchor: [40, -34],   
  shadowSize: [41, 41]
});

const OrangeIcon = L.icon({
  iconUrl: orangeIcon,
  iconSize: [100, 50],      
  iconAnchor: [12, 41],    
  popupAnchor: [40, -34],   
  shadowSize: [41, 41]
});

const GreenIcon = L.icon({
  iconUrl: greenIcon,
  iconSize: [100, 50],      
  iconAnchor: [12, 41],    
  popupAnchor: [40, -34],   
  shadowSize: [41, 41]
});

const PurpleIcon = L.icon({
  iconUrl: purpleIcon,
  iconSize: [100, 50],      
  iconAnchor: [12, 41],    
  popupAnchor: [40, -34],   
  shadowSize: [41, 41]
});

const UserIcon = L.icon({
  iconUrl: userIconImage,
  shadowUrl: markerShadow, 
  iconSize: [40, 41],      
  iconAnchor: [12, 41],    
  popupAnchor: [40, -34],   
  shadowSize: [41, 41]
});


// Fix default icon paths for Leaflet
const DefaultIcon = L.icon({
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});
L.Marker.prototype.options.icon = DefaultIcon;

export default {
  name: 'Map',
  props: {
    locations: {
      type: Array,
      required: true
    }
  },
  setup(props) {
    const router = useRouter(); 
    const map = ref(null);
    const userLocation = ref(null);
    const markers = ref([]);
    const userMarker = ref(null);

    // Function to initialize the map
    const initializeMap = () => {
      map.value = L.map('mapdiv', {
        center: [1.2868108, 103.8545349],
        zoom: 16,
        maxBounds: [
          [-90, -180],
          [90, 180]
        ],
        maxZoom: 19,
        minZoom: 2,
        updateWhenZooming: false,
        updateWhenIdle: true,
        preferCanvas: true,
        renderer: L.canvas()
      });

      // Add tile layers
      const basemap = L.tileLayer(
        'https://www.onemap.gov.sg/maps/tiles/Default/{z}/{x}/{y}.png',
        {
          attribution:
            '<img src="https://www.onemap.gov.sg/web-assets/images/logo/om_logo.png" style="height:20px;width:20px;"/>&nbsp;<a href="https://www.onemap.gov.sg/" target="_blank" rel="noopener noreferrer">OneMap</a>&nbsp;&copy;&nbsp;contributors&nbsp;&#124;&nbsp;<a href="https://www.sla.gov.sg/" target="_blank" rel="noopener noreferrer">Singapore Land Authority</a>',
          maxZoom: 19,
          minZoom: 11
        }
      );
      const osmLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19
      });

      basemap.addTo(map.value);
      osmLayer.addTo(map.value);

      const markersLayer = L.layerGroup().addTo(map.value);
      addLocationMarkers(markersLayer);
    };

    // Function to add location markers to the map
    const addLocationMarkers = (markersLayer) => {
  // Clear existing markers
  markers.value.forEach((marker) => {
    marker.remove();
  });
  markers.value = [];
  markersLayer.clearLayers();

  // Check if we are filtering by prominence (is_distance is false)
  if (props.locations.length > 0 && !props.locations[0].is_distance) {
    // Split locations into three groups (one-third each)
    const sortedLocations = [...props.locations];
    const totalLocations = sortedLocations.length;
    const third = Math.floor(totalLocations / 3);

    // Assign icon colors based on prominence
    sortedLocations.forEach((location, index) => {
      let icon;
      if (index < third) {
        icon = RedIcon;  // First third (highest prominence)
      } else if (index < 2 * third) {
        icon = OrangeIcon;  // Second third
      } else {
        icon = PurpleIcon;  // Last third (lowest prominence)
      }

      // Create marker with the appropriate color
      if (location.lat && location.lng && location.name) {
        const marker = L.marker([location.lat, location.lng], {
          riseOnHover: true,
          riseOffset: 250,
          icon: icon
        });

        const popup = L.popup({
          closeButton: true,
          closeOnClick: false, // Prevent map from centering when clicked
          autoClose: false,
          className: 'custom-popup-container',
          autoPan: true,
          autoPanPadding: [50, 50],
          keepInView: true
        }).setContent(createPopupContent(location));

        marker.bindPopup(popup);
        markers.value.push(marker);
        marker.addTo(markersLayer);
      } else {
        console.warn('Invalid location data:', location);
      }
    });
  } else {
    // If filtering by distance (is_distance is true), use the default behavior
    props.locations.forEach((location) => {
      if (location.lat && location.lng && location.name) {
        const marker = L.marker([location.lat, location.lng], {
          riseOnHover: true,
          riseOffset: 250
        });

        const popup = L.popup({
          closeButton: true,
          closeOnClick: false, // Prevent map from centering when clicked
          autoClose: false,
          className: 'custom-popup-container',
          autoPan: true,
          autoPanPadding: [50, 50],
          keepInView: true
        }).setContent(createPopupContent(location));

        marker.bindPopup(popup);
        markers.value.push(marker);
        marker.addTo(markersLayer);
      } else {
        console.warn('Invalid location data:', location);
      }
    });
  }
};


    // Function to create popup content
    const createPopupContent = (location) => {
      const container = document.createElement('div');
      container.innerHTML = `
        <div class="custom-popup">
          <p class="text-gray-800 font-medium mb-2">${location.name}</p>
          <button class="see-more-btn bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700 w-full">
            See More
          </button>
        </div>
      `;
      
      container.querySelector('.see-more-btn').addEventListener('click', () => {
        handleSeeMore(location);
      });

      return container;
    };

    const handleSeeMore = (location) => {
      console.log('See more clicked for location:', location);
      // Pass the entire location object as a query parameter
      router.push({ 
        name: 'MapChat', 
        query: { 
          locationData: encodeURIComponent(JSON.stringify(location))
        } 
      });
    };

    // Watch for changes in locations prop to update markers
    watch(
      () => props.locations,
      (newLocations) => {
        if (map.value) {
          const markersLayer = L.layerGroup().addTo(map.value);
          addLocationMarkers(markersLayer);
        }
      },
      { immediate: true }
    );

    // Function to get user's location
    const locateUser = () => {
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude } = position.coords;
        userLocation.value = L.latLng(latitude, longitude);

        if (userMarker.value) {
          userMarker.value.remove();
        }

        userMarker.value = L.marker(userLocation.value, {
          icon: UserIcon, // Use the custom user icon
          zIndexOffset: 1000
        }).addTo(map.value)
          .bindPopup('You are here!')
          .openPopup();

        map.value.setView(userLocation.value, 16); // Center map on user's location
      },
      (error) => {
        console.error('Error retrieving location:', error);
        alert('Unable to retrieve your location.');
      }
    );
  } else {
    alert('Geolocation is not supported by your browser.');
  }
};


    const centerOnUser = () => {
      console.log('Centering on user');
      if (userLocation.value && map.value) {
        map.value.setView(userLocation.value, 16, {
          animate: true,
          duration: 1
        });
        if (userMarker.value) {
          userMarker.value.openPopup();
        }
      } else {
        locateUser();
      }
    };

    onMounted(() => {
      initializeMap();
      locateUser(); 
    });

    return {
      map,
      userLocation,
      centerOnUser
    };
  }
};
</script>

<style scoped>
#map-container {
  position: relative;
}

#mapdiv {
  height: 100%;
  width: 100%;
}

:deep(.custom-popup-container) {
  .leaflet-popup-content {
    margin: 10px;
    min-width: 200px;
  }

  .custom-popup {
    text-align: center;
  }

  .leaflet-popup {
    position: absolute;
    z-index: 1000;
  }
}

:deep(.leaflet-tile-container) {
  will-change: transform;
  transform-style: preserve-3d;
}

button:hover svg {
  transform: scale(1.1);
  transition: transform 0.2s ease-in-out;
}
</style>
