<template>
    <div class="flex flex-col h-screen bg-white">
      <!-- Header with Back Button -->
      <header class="flex items-center justify-start bg-white p-4 shadow-md">
        <router-link to="/" class="flex items-center text-red-600 hover:text-red-700 font-semibold text-lg">
          ← back
        </router-link>
      </header>
  
      <main class="flex-grow flex items-center justify-center p-6">
        <div class="text-center text-gray-800 space-y-6">
          <div class="flex justify-center items-center">
            <img class="w-24 h-24 object-contain" src="../assets/SGpin.png" alt="SG Pin">
          </div>
          <p class="text-2xl font-semibold">Welcome to your Map Guide!</p>
          <p class="text-xl font-semibold">Select an option to begin:</p>
  
          <div class="flex flex-col space-y-4">
            <!-- Begin Tour Button -->
            <router-link to="/mappage">
              <button 
                class="bg-red-500 hover:bg-red-600 text-white font-bold py-3 px-6 rounded w-36"
              >
                Map
              </button>
            </router-link>
            <!-- Run Simulator Button -->
            <router-link to="/mapsimulatorpage">
              <button 
                class="bg-red-500 hover:bg-red-600 text-white font-bold py-3 px-6 rounded w-48"
              >
                Map Simulator
              </button>
            </router-link>
            
          </div>
        </div>
      </main>
    </div>
  </template>
  
  <script setup>
  </script>
  
  <style scoped>
  </style>