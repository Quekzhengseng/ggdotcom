<template>
  <div class="fixed bottom-0 left-0 right-0 bg-white shadow-lg rounded-t-lg z-50">
    <div class="flex items-center justify-between p-4 border-b">
      <p class="font-semibold text-gray-800">{{ selectedLandmark.name }}</p>
      <button @click="handleCloseChat" class="text-gray-500 hover:text-gray-700">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M15.621 4.379a1 1 0 00-1.414 1.414L14.207 6H6a1 1 0 100 2h8.207l-.707.707a1 1 0 001.414 1.414l2.828-2.828a1 1 0 000-1.414l-2.828-2.828z" clip-rule="evenodd"/>
        </svg>
      </button>
    </div>
    
    <div class="p-4">
      <img :src="selectedLandmark.image" alt="Landmark Image" class="w-full rounded-lg mb-4" />
      <p class="text-gray-700 mb-4">{{ selectedLandmark.description }}</p>
      
      <div class="flex justify-between">
        <button @click="handleShowDirections" class="px-4 py-2 bg-blue-600 text-white rounded-full hover:bg-blue-700">
          Show Directions
        </button>
        <button @click="handleCloseChat" class="px-4 py-2 bg-gray-300 text-gray-800 rounded-full hover:bg-gray-400">
          Close
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'MapSimulatorChat',
  props: {
    selectedLandmark: Object,
    showChat: Boolean
  },
  methods: {
    handleCloseChat() {
      this.$emit('close');
    },
    handleShowDirections() {
      this.$emit('show-directions', this.selectedLandmark.location);
    }
  }
}
</script>

<style scoped>
/* Chat window styles */
.fixed {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
}
</style>
