<template>
  <div class="flex flex-col items-center space-y-4">
    <!-- Play button -->
    <button 
      @click="generateAudio" 
      class="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 disabled:bg-red-300 flex items-center gap-2"
      :disabled="isLoading"
    >
      <span v-if="isLoading">Generating Audio...</span>
      <span v-else>Generate Audio</span>
    </button>

    <!-- Audio player -->
    <audio 
      v-if="audioUrl" 
      controls 
      class="w-full max-w-md"
      :src="audioUrl"
    />
  </div>
</template>

<script setup>
import { ref, onUnmounted } from 'vue'

const props = defineProps({
  text: {
    type: String,
    required: true
  }
})

const audioUrl = ref(null)
const isLoading = ref(false)

const generateAudio = async () => {
  try {
    isLoading.value = true
    
    const response = await fetch('https://ggdotcom.onrender.com/audio', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        text: props.text
      })
    })

    if (!response.ok) {
      throw new Error('Failed to generate audio')
    }

    // Get the audio blob
    const audioBlob = await response.blob()
    
    // Clean up old audio URL if it exists
    if (audioUrl.value) {
      URL.revokeObjectURL(audioUrl.value)
    }
    
    // Create new blob URL
    audioUrl.value = URL.createObjectURL(audioBlob)

  } catch (error) {
    console.error('Error:', error)
  } finally {
    isLoading.value = false
  }
}

// Clean up URLs when component is unmounted
onUnmounted(() => {
  if (audioUrl.value) {
    URL.revokeObjectURL(audioUrl.value)
  }
})
</script>
