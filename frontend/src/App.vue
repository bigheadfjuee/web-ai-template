<script setup lang="ts">
import HealthCheck from './components/HealthCheck.vue'
</script>

<template>
  <main>
    <h1>Web AI Template</h1>
    <p>Vite + Vue 3 + FastAPI scaffold</p>
    <HealthCheck />
  </main>
</template>

<style>
body {
  font-family: system-ui, -apple-system, sans-serif;
  margin: 0;
  padding: 2rem;
  background: #f6f7f9;
  color: #1a1a1a;
}
main {
  max-width: 40rem;
  margin: 0 auto;
}
</style>
