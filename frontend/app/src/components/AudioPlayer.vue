<template>
  <div class="flex flex-col items-center space-y-4">
    <!-- Loading State -->
    <div v-if="isLoading" class="text-red-600 flex items-center gap-2">
      <div class="animate-spin h-5 w-5 border-2 border-red-600 border-t-transparent rounded-full"></div>
      <span>Generating audio...</span>
    </div>

    <!-- Audio Player -->
    <div v-if="audioUrl" class="w-full flex items-center gap-3">
      <audio 
        ref="audioPlayer"
        :src="audioUrl" 
        class="flex-grow"
        controls
      />
      
      <!-- Download Button -->
      <button
        @click="downloadAudio"
        class="p-2 text-red-600 hover:text-red-700 rounded-full hover:bg-red-50 transition-colors"
        title="Download audio"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
        </svg>
      </button>
    </div>

    <!-- Error State -->
    <div v-if="error" class="text-red-600">
      Failed to load audio. Click here to try again.
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  text: {
    type: String,
    required: true
  }
})

const audioUrl = ref(null)
const audioPlayer = ref(null)
const isLoading = ref(false)
const error = ref(null)

const generateAudio = async () => {
  try {
    isLoading.value = true
    error.value = null
    
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

    const audioBlob = await response.blob()
    
    // Clean up old audio URL if it exists
    if (audioUrl.value) {
      URL.revokeObjectURL(audioUrl.value)
    }
    
    // Create new blob URL
    audioUrl.value = URL.createObjectURL(audioBlob)

    setTimeout(() => {
      if (audioPlayer.value) {
        audioPlayer.value.play()
          .catch(err => console.warn('Auto-play failed:', err))
      }
    }, 100)

  } catch (err) {
    console.error('Error:', err)
    error.value = err.message
  } finally {
    isLoading.value = false
  }
}

const downloadAudio = async () => {
  if (!audioUrl.value) return
  
  const link = document.createElement('a')
  link.href = audioUrl.value
  link.download = `audio-${Date.now()}.mp3` // Or whatever extension your audio uses
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

// Generate audio as soon as the component mounts
onMounted(() => {
  generateAudio()
})

// Clean up URLs when component is unmounted
onUnmounted(() => {
  if (audioUrl.value) {
    URL.revokeObjectURL(audioUrl.value)
  }
})
</script>