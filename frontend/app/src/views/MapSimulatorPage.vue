<template>
  <div class="flex flex-col h-screen bg-white">
    <!-- Header Section -->
    <header class="flex items-center justify-between bg-white p-4 shadow-md">
      <router-link to="/mapselection" class="flex items-center text-red-600 hover:text-red-700 font-semibold text-lg">
        ← back
      </router-link>
      <p class="text-lg font-medium text-gray-800">
        Map Simulator
      </p>
      <div class="w-6"></div>
    </header>

    <!-- Main Content Section -->
    <main class="flex-grow overflow-hidden">
      <div :class="[
        'transition-all duration-300 ease-in-out h-full',
        showChat ? 'scale-95 opacity-50' : 'scale-100 opacity-100'
      ]">
        <SimulatedMap
          @landmark-selected="handleLandmarkSelect"
          :class="{ 'pointer-events-none': showChat }"
        />
      </div>

      <!-- Display Chat Only if Landmark is Selected -->
      <MapSimulatorChat
        v-if="selectedLandmark && showChat"
        :selectedLandmark="selectedLandmark"
        :show-chat="showChat"
        @close="handleChatClose"
        @show-directions="handleShowDirections"
      />
    </main>
  </div>
</template>

<script>
import SimulatedMap from '../components/SimulatedMap.vue'
import MapSimulatorChat from '../components/MapSimulatorChat.vue'

export default {
  name: 'MapSimulatorPage',
  components: {
    SimulatedMap,
    MapSimulatorChat
  },
  data() {
    return {
      selectedLandmark: null,
      showChat: false
    }
  },
  methods: {
    handleLandmarkSelect(landmark) {
      console.log('Landmark selected:', landmark)
      // Ensure all required properties are present
      this.selectedLandmark = {
        name: landmark.name || 'Unnamed Location',
        image: landmark.image || '/placeholder-image.jpg',
        location: landmark.location || { lat: 0, lng: 0 },
        description: landmark.description || ''
      };
      this.showChat = true;
    },
    handleChatClose() {
      this.showChat = false;
      this.selectedLandmark = null;
    },
    handleShowDirections(location) {
      console.log('Showing directions to:', location);
      this.showChat = false;
      // Implement your directions logic here
    }
  }
}
</script>

<style scoped>
/* Add any custom styles for your components here */
</style>
