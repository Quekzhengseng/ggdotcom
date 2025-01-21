<template>
  <div class="flex flex-col items-center justify-center min-h-screen p-4">
    <h1 class="text-4xl font-bold mb-8">
      SG <span class="text-red-500">Buddy</span>
    </h1>


    <router-link to="/mapselection">
      <button class="bg-red-500 hover:bg-red-600 text-white font-bold py-3 px-6 rounded mb-4 w-64">
        Map
      </button>
    </router-link>

    <router-link to="/selection">
      <button class="bg-red-500 hover:bg-red-600 text-white font-bold py-3 px-6 rounded mb-4 w-64">
        AI Tour Guide
      </button>
    </router-link>

    <router-link to="/history">
      <button class="bg-gray-400 hover:bg-gray-500 text-white font-bold py-3 px-6 rounded w-64">
        View Travel Journal
      </button>
    </router-link>
  </div>
</template>

<script setup>

</script>
