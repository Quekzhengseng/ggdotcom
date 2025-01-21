<template>
  <div class="flex flex-col h-screen bg-white">
    <!-- Header with Back Button and Location Info -->
    <header class="flex flex-col items-center justify-between bg-white p-4 shadow-md">
      <div class="flex items-center justify-between w-full">
        <router-link to="/mappage" class="flex items-center text-red-600 hover:text-red-700 font-semibold text-lg">
          ← back to map
        </router-link>
        <p class="text-lg font-medium text-gray-800">Chat</p>
        <div class="w-6"></div>
      </div>
      
  <!-- Location Data Display -->
  <div v-if="locationData" class="mt-2 w-full px-4">
    <div class="bg-gray-50 p-3 rounded-lg">
      <h2 class="text-md text-center font-bold text-gray-800">{{ locationData.name }}</h2>
      <div class="text-sm text-gray-600 mt-1">
        <div v-if="locationData.base64Image" class="flex justify-center">
          <img :src="'data:image/jpeg;base64,' + locationData.base64Image" alt="Location Image" class="rounded-lg w-20 h-auto"/>
        </div>
        <p v-if="!locationData.base64Image">No image available</p>
      </div>
    </div>


    <!-- Action Buttons -->
    <div class="flex justify-between mt-4 px-4">
      <button @click="talkAboutPlace" class="bg-red-600 hover:bg-red-700 text-white py-2 px-4 rounded-full">
        Talk about this place
      </button>
      <button @click="takeMeThere" class="bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-full">
        Take me there
      </button>
    </div>
</div>

    </header>

    <!-- Main Chat Area -->
    <main class="flex-grow overflow-y-auto p-6 space-y-6">
      <div v-for="(message, index) in messages" :key="index" class="animate-fade-in-up">
        <div :class="[
          'rounded-xl max-w-4/5 shadow-lg',
          message.isUser ? 'bg-gray-100 text-gray-800 ml-auto' : 'bg-red-50 text-gray-800',
        ]">
          <div class="p-4">
            <span class="block break-words">{{ message.text }}</span>
            <div v-if="!message.isUser" class="mt-3 pt-3 border-t border-gray-200">
              <AudioPlayer :text="message.text" />
            </div>
          </div>
        </div>
        
        <img
          v-if="message.image"
          :src="message.image"
          alt="Captured image"
          class="mt-3 max-w-full h-auto rounded-xl shadow-md"
        />
      </div>
    </main>

    <!-- Footer with Input Controls -->
    <footer class="bg-white border-t border-gray-300 p-6 rounded-t-3xl">
      <div class="flex items-center justify-between mb-4">
        <!-- Voice Recording Button -->
        <button @click="toggleRecording" class="relative group">
          <div :class="[
            'p-3 rounded-full transition-all duration-300 ease-in-out',
            recording ? 'bg-red-600 hover:bg-red-700' : 'bg-gray-200 hover:bg-gray-300',
            'relative z-10'
          ]">
            <svg 
              xmlns="http://www.w3.org/2000/svg" 
              :class="[
                'h-7 w-7 transition-colors duration-300',
                recording ? 'text-white' : 'text-gray-700'
              ]" 
              fill="none" 
              viewBox="0 0 24 24" 
              stroke="currentColor"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
            </svg>
          </div>
          <div v-if="recording" class="absolute -inset-1 bg-red-100 rounded-full animate-pulse z-0"></div>
        </button>

        <!-- Camera Button -->
        <button
          @click="captureImage"
          class="bg-red-600 hover:bg-red-700 text-white font-bold p-3 rounded-full transition-all duration-300 ease-in-out"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-7 w-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        </button>
      </div>

      <!-- Text Input and Send Button -->
      <div class="flex">
        <input
          v-model="userInput"
          @keyup.enter="sendMessage"
          type="text"
          placeholder="Type your message..."
          class="flex-grow border-2 border-transparent rounded-full px-6 py-3 focus:outline-none focus:ring-2 focus:ring-red-600 bg-gray-100 text-gray-800 placeholder-gray-500"
        />
        <button
          @click="sendMessage"
          class="bg-red-600 hover:bg-red-700 text-white font-bold py-3 px-6 rounded-full ml-3 transition-all duration-300 ease-in-out"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-7 w-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
          </svg>
        </button>
      </div>
    </footer>

    <!-- Hidden file input for image capture -->
    <input
      type="file"
      accept="image/*"
      capture="environment"
      ref="fileInput"
      class="hidden"
      @change="onImageCapture"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { useRoute } from 'vue-router';
import { useAppStore } from '../store';
import { useGeolocation } from '@vueuse/core';
import imageCompression from 'browser-image-compression';
import AudioPlayer from '../components/AudioPlayer.vue';

// Store and Route setup
const store = useAppStore();
const route = useRoute();

// Refs
const userInput = ref('');
const fileInput = ref(null);
const recording = ref(false);
const recognition = ref(null);
const isRecognitionSupported = ref(false);
const locationData = ref(null);
const { messages } = store;
const { coords } = useGeolocation();

// Initialize component
const fetchImage = async (photoReference) => {
  try {
    console.log('Fetching image with photoReference:', photoReference);

    const response = await fetch('https://ggdotcom.onrender.com/image', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ photo_reference: photoReference }),
    });

    if (!response.ok) {
      throw new Error('Failed to fetch image');
    }

    const data = await response.json();


    return data;
  } catch (error) {
    console.error('Error fetching image:', error);
    return { base64_image: null }; // Return a fallback response
  }
};


onMounted(async () => {
  try {
    // Get and decode the location data from URL
    if (route.query.locationData) {
      const decodedData = decodeURIComponent(route.query.locationData);
      locationData.value = JSON.parse(decodedData);
      console.log('Received location data:', locationData.value);

      // Fetch the image from the backend using the photoReference
      const imageResponse = await fetchImage(locationData.value.photoReference);

      // Use the correct key for the base64 image
      locationData.value.base64Image = imageResponse.base64_image; 
    }
    checkSpeechRecognitionSupport();
  } catch (error) {
    console.error('Error parsing location data:', error);
  }
});

// Speech Recognition Setup
const checkSpeechRecognitionSupport = () => {
  if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    isRecognitionSupported.value = true;
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition.value = new SpeechRecognition();
    recognition.value.continuous = true;
    recognition.value.interimResults = true;

    recognition.value.onstart = () => {
      recording.value = true;
    };

    recognition.value.onend = () => {
      recording.value = false;
    };

    recognition.value.onresult = async (event) => {
      const result = event.results[event.results.length - 1];
      if (result.isFinal) {
        const speech = result[0].transcript;
        store.addMessage({ text: speech, isUser: true });
        await sendToBackend(speech);
      }
    };

    recognition.value.onerror = (event) => {
      console.error('Speech recognition error:', event.error);
      stopRecognition();
    };
  }
};

// Voice Recording Functions
const toggleRecording = () => {
  if (!isRecognitionSupported.value) {
    alert('Speech recognition is not supported in your browser.');
    return;
  }
  recording.value ? stopRecognition() : startRecognition();
};

const startRecognition = () => {
  if (recognition.value) {
    try {
      recognition.value.start();
    } catch (error) {
      console.error('Speech recognition error:', error);
    }
  }
};

const stopRecognition = () => {
  if (recognition.value) {
    recognition.value.stop();
  }
};

// Message Handling Functions
const sendMessage = async () => {
  if (userInput.value.trim()) {
    const messageText = userInput.value.trim();
    userInput.value = '';
    store.addMessage({ text: messageText, isUser: true });
    await sendToBackend(messageText);
  }
};

const sendToBackend = async (text) => {
  try {
    const payload = {
      text,
      location: `${locationData.value.lat},${locationData.value.lng}`, 
    };
    console.log(payload)

    const response = await fetch('https://ggdotcom.onrender.com/chat2', { 
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
    store.addMessage({ text: data.response, isUser: false });
  } catch (error) {
    console.error("Error getting response:", error);
    store.addMessage({ text: "Error getting response.", isUser: false });
  }
};


const talkAboutPlace = async () => {
  try {
    // Prepare the payload with location and optional image
    const payload = {
      location: `${locationData.value.lat},${locationData.value.lng}`,
      text: 'Can you tell me about the landmark that I am at right now', // Modify as necessary or allow user input
      image: locationData.value.base64Image || null, // Send the image if available
    };

    // Send the request to the backend
    const response = await fetch('https://ggdotcom.onrender.com/chat2', {
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
    
    console.log('AI Response:', data);

    // Optionally, you can add the response to the chat as a message
    store.addMessage({ text: data.response, isUser: false });
  } catch (error) {
    console.error("Error talking about the place:", error);
    store.addMessage({ text: "Error getting response from AI.", isUser: false });
  }
};


// Image Handling Functions
const captureImage = () => {
  fileInput.value.click();
};

const onImageCapture = async (event) => {
  const file = event.target.files[0];
  if (file) {
    try {
      const options = {
        maxSizeMB: 0.75,
        maxWidthOrHeight: 1024,
        useWebWorker: true,
      };
      const compressedFile = await imageCompression(file, options);
      const reader = new FileReader();

      reader.onload = async (e) => {
        const imageDataUrl = e.target.result;
        store.addMessage({
          text: 'Image captured and compressed',
          isUser: true,
          image: imageDataUrl,
        });

        try {
          const payload = {
            image: imageDataUrl,
            location: `${locationData.value.lat},${locationData.value.lng}`,
          };

          const response = await fetch('https://ggdotcom.onrender.com/chat2', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload),
          });

          if (!response.ok) {
            throw new Error('Error sending image to backend');
          }

          const data = await response.json();
          store.addMessage({ text: data.response, isUser: false });
        } catch (error) {
          store.addMessage({ text: "Error processing image.", isUser: false });
          console.error("Image processing error:", error);
        }
      };

      reader.readAsDataURL(compressedFile);
    } catch (error) {
      console.error("Compression error:", error);
      store.addMessage({ text: "Error compressing image.", isUser: false });
    }
  }
};
</script>

<style scoped>
.animate-fade-in-up {
  animation: fadeInUp 0.5s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(15px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>