<template>
  <div class="flex flex-col h-screen bg-white">
    <header class="flex flex-col items-center justify-between bg-white p-4 shadow-md">
      <div class="flex items-center justify-between w-full">
        <router-link to="/selection" class="flex items-center text-red-600 hover:text-red-700 font-semibold text-lg">
          ← back
        </router-link>
        <p class="text-lg font-medium text-gray-800">
          <span v-if="loading">Simulator</span>
          <span v-else>Simulator Completed</span>
        </p>
        <div v-if="loading" class="flex items-center justify-center">
          <div class="animate-spin w-6 h-6 border-4 border-red-600 border-t-transparent rounded-full"></div>
        </div>
      </div>
      <div class="mt-2 text-center text-sm text-gray-600">
        (Content generated curated via AI and other techniques)
      </div>
    </header>

    <main class="flex-grow overflow-y-auto p-6 space-y-6">
      <div v-for="(message, index) in messages" :key="index" class="animate-fade-in-up">
        <div :class="[
          'rounded-xl max-w-4/5 shadow-lg p-4',
          message.isUser ? 'bg-gray-100 text-gray-800 ml-auto' : 'bg-red-50 text-gray-800',
        ]">
          <span v-if="message.text" class="block break-words">{{ message.text }}</span>
          <img v-if="message.image" :src="message.image" class="max-w-full rounded-lg" alt="User shared image" />
          <AudioPlayer 
            v-if="!message.isUser" 
            :text="message.text || ''" 
            :autoplay="message.isEnding"
          />
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { onMounted, ref, onBeforeUnmount } from "vue";
import { useAppStore } from "../store";
import AudioPlayer from "../components/AudioPlayer.vue";
import imageCompression from "browser-image-compression";
import lauPaSatImage from "../assets/laupasat.jpg";

const store = useAppStore();
const messages = ref([]);
const loading = ref(false);
const visitedPlaces = ref([]);

const locations = [
  "1.282542, 103.845410",
  "1.281293, 103.844640",
];

let simulatorRunning = false;

const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

const sendMessage = async (payload) => {
  const response = await fetch("https://ggdotcom.onrender.com/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return await response.json();
};

const convertImageToBase64 = async (imagePath) => {
  try {
    const response = await fetch(imagePath);
    const blob = await response.blob();

    const options = {
      maxSizeMB: 0.75,
      maxWidthOrHeight: 1024,
      useWebWorker: true,
    };

    const compressedFile = await imageCompression(blob, options);

    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => resolve(e.target.result);
      reader.onerror = reject;
      reader.readAsDataURL(compressedFile);
    });
  } catch (error) {
    console.error("Error converting image:", error);
    throw error;
  }
};

const getImageDescription = async (imageDataUrl, location) => {
  try {
    const payload = {
      image: imageDataUrl,
      location: location,
      visitedPlaces: visitedPlaces.value,
    };

    const response = await fetch("https://ggdotcom.onrender.com/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error("Error sending image to backend");
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error("Error during image description fetch:", error);
    return { response: "Error processing image" };
  }
};

const startSimulator = async () => {
  simulatorRunning = true;
  loading.value = true;
  try {
    for (let i = 0; i < locations.length; i++) {
      if (!simulatorRunning) break;

      const loc = locations[i];
      const [latitude, longitude] = loc.split(",");

      const payload = {
        location: `${latitude},${longitude}`,
        visitedPlaces: visitedPlaces.value,
      };

      const data = await sendMessage(payload);
      visitedPlaces.value.push(data.visitedPlace);
      messages.value.push({ text: data.response, isUser: false });

      if (i === 0) {
        await delay(70000);
        const historicalQuestion = "What is the historical significance of this place I am in?";
        messages.value.push({ text: historicalQuestion, isUser: true });
      }

      if (i === 1) {
        await delay(73000);
        try {
          const imageDataUrl = await convertImageToBase64(lauPaSatImage);

          messages.value.push({
            text: "Image captured",
            image: imageDataUrl,
            isUser: true,
          });

          const imageResponse = await getImageDescription(
            imageDataUrl,
            `1.2805288120280371, 103.85038526703941`
          );
          messages.value.push({ text: imageResponse.response, isUser: false });

          // Add delay to simulate processing
          await delay(10000);
        } catch (error) {
          console.error("Error processing image:", error);
          messages.value.push({
            text: "Error processing image.",
            isUser: false,
          });
        }
      }

      if (i < locations.length - 1) {
        await delay(10000);
      }
    }

    // Ensure ending message is added only after all tasks are done
    // messages.value.push({
    //   text: "Simulator ended. Hope you enjoyed your trip to Chinatown!",
    //   isUser: false,
    //   isEnding: true, // Use this flag if special handling is needed (e.g., autoplay audio)
    // });

    simulatorRunning = false;
  } catch (error) {
    console.error("Simulation error:", error);
    messages.value.push({ text: "Error in simulation.", isUser: false });
  } finally {
    loading.value = false;
  }
};


onBeforeUnmount(() => {
  simulatorRunning = false;
  loading.value = false;
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