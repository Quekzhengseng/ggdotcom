<template>
  <div class="flex flex-col h-screen bg-white">
    <header class="flex flex-col items-center justify-between bg-white p-4 shadow-md">
      <div class="flex items-center justify-between w-full">
        <router-link to="/" class="flex items-center text-red-600 hover:text-red-700 font-semibold text-lg">
          ← back
        </router-link>
        <p class="text-lg font-medium text-gray-800">Simulator</p>
        <div v-if="loading" class="flex items-center justify-center">
          <div class="animate-spin w-6 h-6 border-4 border-red-600 border-t-transparent rounded-full"></div>
        </div>
      </div>
      <div class="mt-2 text-center text-sm text-gray-600">
        (Content generated curated via AI and other techniques)
      </div>
    </header>

    <main class="flex-grow overflow-y-auto p-6 space-y-6">
      <div class="text-center text-gray-800 space-y-4"></div>

      <div v-for="(message, index) in messages" :key="index" class="animate-fade-in-up">
        <div
          :class="[
            'rounded-xl max-w-4/5 shadow-lg p-4',
            message.isUser ? 'bg-gray-100 text-gray-800 ml-auto' : 'bg-red-50 text-gray-800',
          ]"
        >
          <span class="block break-words">{{ message.text }}</span>
          <AudioPlayer v-if="!message.isUser" :text="message.text" />
        </div>
      </div>
    </main>
    
  </div>
</template>

<script setup>
import { onMounted, ref, onBeforeUnmount } from 'vue';
import { useAppStore } from '../store';
import AudioPlayer from '../components/AudioPlayer.vue';

const store = useAppStore();
const messages = ref([]);
const loading = ref(false);
const visitedPlaces = ref([]);


const locations = [
'1.282542, 103.845410',
'1.281293, 103.844640',
'1.280921, 103.846269',
'1.281072, 103.847809',
'1.280181, 103.850140',
];

// Flag to manage simulator state
let simulatorRunning = false;

const startSimulator = async () => {
  simulatorRunning = true;
  loading.value = true;
  try {
    for (const loc of locations) {
      if (!simulatorRunning) break; // Stop if simulator is no longer running

      const [latitude, longitude] = loc.split(",");
      
      const payload = {
      location: `${latitude},${longitude},`,
      visitedPlaces: visitedPlaces.value, 
    };

      console.log(`Sending location: ${loc}`);

      const response = await fetch('https://ggdotcom.onrender.com/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const data = await response.json();
      console.log(`Response for ${loc}:`, data);
      visitedPlaces.value.push(data.visitedPlace);
      console.log(`visited places are ${visitedPlaces.value}`);

      messages.value.push({ text: data.response, isUser: false });
      await new Promise(resolve => setTimeout(resolve, 150000)); // Simulate delay
    }

    // Show "Simulator ended" message after all locations are sent
    simulatorRunning = false
    messages.value.push({ text: "Simulator ended. Hope you enjoyed your trip to Chinatown!", isUser: false });

  } catch (error) {
    console.error("Simulation error:", error);
    messages.value.push({ text: "Error in simulation.", isUser: false });
  } finally {
    loading.value = false;
  }
};

// Stop the simulation when the component is unmounted or when the user navigates away
onBeforeUnmount(() => {
  simulatorRunning = false;
  loading.value = false;  // Stop loading animation if still running
});

onMounted(() => {
  startSimulator();
});
</script>

<style scoped>
.animate-fade-in-up {
  animation: fadeInUp 0.5s ease-out;
}
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
