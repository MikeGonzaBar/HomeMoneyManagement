<template>
  <v-app>
    <router-view />
  </v-app>
</template>

<script lang="ts" setup>
//
</script>

<style>
/* Global Styles for Budget Buddy */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

* {
  font-family: 'Inter', sans-serif;
}

.v-application {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%) !important;
}

/* Custom scrollbar */
::-webkit-scrollbar {
  width: 8px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: #4CAF50;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #2E7D32;
}

/* Glassmorphism effect */
.glass-card {
  background: rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.18);
  box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
}

/* Modern shadows */
.shadow-soft {
  box-shadow: 0 2px 20px rgba(0, 0, 0, 0.08);
}

.shadow-medium {
  box-shadow: 0 4px 30px rgba(0, 0, 0, 0.12);
}

.shadow-strong {
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.16);
}

/* Smooth transitions */
.smooth-transition {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Hover effects */
.hover-lift:hover {
  transform: translateY(-2px);
  transition: transform 0.2s ease;
}

/* Budget Buddy specific styles */
.budget-gradient {
  background: linear-gradient(135deg, #2E7D32 0%, #4CAF50 50%, #8BC34A 100%);
}

.budget-text-gradient {
  background: linear-gradient(135deg, #2E7D32 0%, #4CAF50 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
</style>
