<template>
    <div id="map-container" class="relative">
      <div id="mapdiv" style="height: 100vh;"></div>
      <button 
        @click="startWalking"
        :disabled="isWalking"
        class="absolute bottom-40 right-20 bg-white p-3 rounded-full shadow-lg hover:bg-gray-50 z-[1000] disabled:bg-gray-100 disabled:cursor-not-allowed"
        title="Walk to next landmark"
      >
        <svg 
          xmlns="http://www.w3.org/2000/svg" 
          class="h-6 w-6"
          :class="isWalking ? 'text-gray-400' : 'text-red-600'"
          fill="none" 
          viewBox="0 0 24 24" 
          stroke="currentColor"
        >
          <path 
            strokeLinecap="round" 
            strokeLinejoin="round" 
            strokeWidth={2} 
            d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
          />
          <path 
            strokeLinecap="round" 
            strokeLinejoin="round" 
            strokeWidth={2} 
            d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
          />
        </svg>
      </button>
      <div v-if="isWalking" class="absolute bottom-20 right-6 bg-white p-2 rounded-lg shadow-lg z-[1000]">
        Walking to {{ nextLandmarkName }}...
      </div>
    </div>
</template>

<script>
import { onMounted, ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

export default {
  name: 'SimulatedMap',
  emits: ['landmark-selected'],
  setup(props, { emit }) {
    const router = useRouter();
    const map = ref(null);
    const markers = ref([]);
    const userMarker = ref(null);
    const currentLocationIndex = ref(0);
    const isWalking = ref(false);
    const walkingPath = ref(null);

    // Updated landmarks structure
    const landmarks = ref([
      {
        name: "Lau Pa Sat",
        coordinates: { lat: 1.2805323020001182, lng: 103.85038194843708 },
        image: "../assets/laupasat.jpg",
        description: "Historic Victorian-style hawker centre"
      },
      {
        name: "Thian Hock Keng Temple",
        coordinates: { lat: 1.2810300237327374, lng: 103.847684566293 },
        image: "../assets/thian-hock-kheng-temple.jpg",
        description: "Oldest Chinese temple in Singapore"
      },
      {
        name: "Sri Mariamman Temple",
        coordinates: { lat: 1.282748539420265, lng: 103.84511988503064 },
        image: "/images/sri-mariamman.jpg",
        description: "Oldest Hindu temple in Singapore"
      }
    ]);

    const nextLandmarkName = computed(() => {
      const nextIndex = (currentLocationIndex.value + 1) % landmarks.value.length;
      return landmarks.value[nextIndex].name;
    });

    const moveMarker = (newPosition) => {
      try {
        if (!userMarker.value) {
          console.error('User marker not initialized');
          return false;
        }
        userMarker.value.setLatLng(newPosition);
        return true;
      } catch (error) {
        console.error('Error moving marker:', error);
        return false;
      }
    };

    const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

    const animateWalk = async (start, end) => {
      console.log('Starting walk animation:', start, end);
      const steps = 100;
      const duration = 5000;
      const delay = duration / steps;
      
      for (let i = 0; i <= steps; i++) {
        if (!isWalking.value) {
          console.log('Walking cancelled');
          return false;
        }

        const progress = i / steps;
        const currentPosition = {
          lat: start.lat + (end.lat - start.lat) * progress,
          lng: start.lng + (end.lng - start.lng) * progress
        };

        const moved = moveMarker([currentPosition.lat, currentPosition.lng]);
        if (!moved) {
          console.error('Failed to move marker');
          return false;
        }

        if (walkingPath.value) {
          const currentPath = walkingPath.value.getLatLngs();
          currentPath.push([currentPosition.lat, currentPosition.lng]);
          walkingPath.value.setLatLngs(currentPath);
        }

        await sleep(delay);
      }

      return true;
    };

    const startWalking = async () => {
      if (isWalking.value) {
        console.log('Already walking');
        return;
      }

      console.log('Starting walk simulation');
      isWalking.value = true;

      try {
        // Get current and next positions
        const currentPosition = landmarks.value[currentLocationIndex.value].coordinates;
        const nextIndex = (currentLocationIndex.value + 1) % landmarks.value.length;
        const nextPosition = landmarks.value[nextIndex].coordinates;

        console.log('Walking from', currentPosition, 'to', nextPosition);

        // Create new path
        if (walkingPath.value) {
          walkingPath.value.remove();
        }

        walkingPath.value = L.polyline([[currentPosition.lat, currentPosition.lng]], {
          color: '#3B82F6',
          weight: 3,
          opacity: 0.6,
          dashArray: '10, 10'
        }).addTo(map.value);

        const success = await animateWalk(currentPosition, nextPosition);

        if (success) {
          currentLocationIndex.value = nextIndex;
          console.log('Walk completed, new index:', currentLocationIndex.value);
        } else {
          console.error('Walk animation failed');
        }

      } catch (error) {
        console.error('Error during walk:', error);
      } finally {
        isWalking.value = false;
        if (walkingPath.value) {
          walkingPath.value.remove();
          walkingPath.value = null;
        }
      }
    };

    const initializeUserPosition = () => {
      console.log('Initializing user position');
      const startPosition = landmarks.value[0].coordinates;
      
      if (userMarker.value) {
        userMarker.value.remove();
      }

      try {
        userMarker.value = L.marker([startPosition.lat, startPosition.lng], {
          zIndexOffset: 1000,
          icon: L.divIcon({
            className: 'user-marker',
            html: '<div class="w-4 h-4 bg-blue-500 rounded-full border-2 border-white shadow-lg"></div>'
          })
        });

        userMarker.value.addTo(map.value);
        userMarker.value.bindPopup('You are here!');
        console.log('User marker initialized successfully');
        return true;
      } catch (error) {
        console.error('Error initializing user marker:', error);
        return false;
      }
    };

    const initializeMap = () => {
      console.log('Initializing map');
      try {
        map.value = L.map('mapdiv', {
          center: [1.2805323020001182, 103.85038194843708],
          zoom: 16,
          maxBounds: [[-90, -180], [90, 180]],
          maxZoom: 19,
          minZoom: 2
        });

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
          attribution: '© OpenStreetMap contributors',
          maxZoom: 19
        }).addTo(map.value);

        const markersLayer = L.layerGroup().addTo(map.value);
        addLocationMarkers(markersLayer);
        
        // Initialize user position after map is ready
        setTimeout(() => {
          const success = initializeUserPosition();
          if (!success) {
            console.error('Failed to initialize user position');
          }
        }, 100);

        console.log('Map initialized successfully');
      } catch (error) {
        console.error('Error initializing map:', error);
      }
    };

    const addLocationMarkers = (markersLayer) => {
      markers.value.forEach(marker => marker.remove());
      markers.value = [];
      markersLayer.clearLayers();

      landmarks.value.forEach((landmark) => {
        const marker = L.marker([landmark.coordinates.lat, landmark.coordinates.lng])
          .bindPopup(() => createPopupContent(landmark))
          .addTo(markersLayer);
        markers.value.push(marker);
      });
    };

    const createPopupContent = (landmark) => {
      const container = document.createElement('div');
      container.innerHTML = `
        <div class="custom-popup">
          <p class="text-gray-800 font-medium mb-2">${landmark.name}</p>
          <button class="see-more-btn bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700 w-full">
            See More
          </button>
        </div>
      `;
      
      container.querySelector('.see-more-btn').addEventListener('click', () => {
        emit('landmark-selected', {
          name: landmark.name,
          image: landmark.image,
          location: landmark.coordinates,
          description: landmark.description
        });
      });
      
      return container;
    };

    onMounted(() => {
      initializeMap();
    });

    return {
      startWalking,
      isWalking,
      nextLandmarkName,
      currentLocationIndex
    };
  },
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

:deep(.user-marker) {
  background: transparent;
  border: none;
}

button:hover:not(:disabled) svg {
  transform: scale(1.1);
  transition: transform 0.2s ease-in-out;
}
</style>