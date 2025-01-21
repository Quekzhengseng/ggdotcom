<template>
  <div class="flex flex-col h-screen bg-white">
    <!-- Header section -->
    <header class="flex flex-col items-center justify-between bg-white p-4 shadow-md">
      <div class="flex items-center justify-between w-full">
        <router-link
          to="/mapselection"
          class="flex items-center text-red-600 hover:text-red-700 font-semibold text-lg"
        >
          ← back
        </router-link>
        <p class="text-lg font-medium text-gray-800">Map</p>
        <div class="w-6">
          <!-- Placeholder div to maintain header layout -->
        </div>
      </div>
    </header>

    <!-- Controls Section -->
    <div class="flex items-center justify-between px-4 py-2">
      <button
        @click="scanLandmarks"
        class="px-4 py-2 bg-red-600 text-white font-semibold rounded hover:bg-red-700"
      >
        Scan surrounding for landmarks!
      </button>

      <select
        v-model="filter"
        class="p-2 bg-white border border-gray-300 rounded"
      >
        <option value="distance">Filter by Distance</option>
        <option value="prominence">Filter by Prominence</option>
      </select>
    </div>

    <!-- Main content area containing the Map component -->
    <main class="flex-grow overflow-hidden">
      <Map :locations="locations" class="w-full h-full" />
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import axios from 'axios';
import Map from '../components/Map.vue';

const filter = ref('distance'); // Default to "Distance"
const locations = ref([]); 


// Function to get user's current location
const getUserLocation = () => {
  return new Promise((resolve, reject) => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const { latitude, longitude } = position.coords;
          resolve(`${latitude},${longitude}`); // Return as a string
        },
        (error) => {
          reject(new Error('Unable to retrieve location: ' + error.message));
        }
      );
    } else {
      reject(new Error('Geolocation is not supported by this browser.'));
    }
  });
};

// Function to scan landmarks
const scanLandmarks = async () => {
  try {
    const location = await getUserLocation(); 
    const is_distance = filter.value === 'distance';

    const payload = {
      content: "text/html; charset=utf-8",
      location: location,
      is_distance: is_distance,
    };
    console.log(payload)

    const response = await fetch('https://ggdotcom.onrender.com/scan', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error('Failed to get response from backend');
    }

    const data = await response.json();
    console.log(data.locations)
    locations.value = data.locations.map((loc) => ({
      name: loc[0], 
      lat: loc[1].lat,
      lng: loc[1].lng,
      photoReference: loc[2], 
    }));

  } catch (error) {
    console.error('Error scanning landmarks:', error.message);
  }
};


</script>
