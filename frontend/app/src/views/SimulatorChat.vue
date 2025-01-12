<template>
    <div class="flex flex-col h-screen bg-white">
      <header class="flex items-center justify-between bg-white p-4 shadow-md">
        <router-link to="/" class="flex items-center text-red-600 hover:text-red-700 font-semibold text-lg">
          ← back
        </router-link>
        <p class="text-lg font-medium text-gray-800">Simulator</p>
  
        <div v-if="loading" class="flex items-center justify-center">
          <div class="animate-spin w-6 h-6 border-4 border-red-600 border-t-transparent rounded-full"></div>
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
          </div>
        </div>
      </main>
    </div>
  </template>
  
  <script setup>
  import { onMounted, ref } from 'vue';
  import { useAppStore } from '../store';
  
  const store = useAppStore();
  const messages = ref([]);
  const loading = ref(false);
  
  const locations = [
    "1.2831,103.8431", // Chinatown Point
    "1.2828,103.8442", // Maxwell Food Centre
    "1.2823,103.8435", // Sago Street
    "1.2798,103.8412", // Ann Siang Hill
  ];
  
  const startSimulator = async () => {
    loading.value = true;
    try {
      for (const loc of locations) {
        const [latitude, longitude] = loc.split(",");
        const payload = { location: `${latitude},${longitude}` };
  
        console.log(`Sending location: ${loc}`);
  
        const response = await fetch('https://ggdotcom.onrender.com/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
  
        const data = await response.json();
        console.log(`Response for ${loc}:`, data);
  
        messages.value.push({ text: data.response, isUser: false });
        await new Promise(resolve => setTimeout(resolve, 5000)); // Simulate delay
      }
  
      // Show "Simulator ended" message after all locations are sent
      messages.value.push({ text: "Simulator ended. Hope you enjoyed your trip to Chinatown!", isUser: false });
  
    } catch (error) {
      console.error("Simulation error:", error);
      messages.value.push({ text: "Error in simulation.", isUser: false });
    } finally {
      loading.value = false;
    }
  };
  
  // Automatically start simulation when the view loads
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
  