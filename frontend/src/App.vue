<script setup lang="ts">
import { ref } from 'vue'
import HealthCheck from './components/HealthCheck.vue'
import UsersView from './views/UsersView.vue'

const activeTab = ref<'health' | 'users'>('health')
</script>

<template>
  <main>
    <h1>Web AI Template</h1>

    <nav class="tabs">
      <button :class="{ active: activeTab === 'health' }" @click="activeTab = 'health'">
        Health
      </button>
      <button :class="{ active: activeTab === 'users' }" @click="activeTab = 'users'">
        Users
      </button>
    </nav>

    <HealthCheck v-if="activeTab === 'health'" />
    <UsersView v-else-if="activeTab === 'users'" />
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
  max-width: 50rem;
  margin: 0 auto;
}
</style>

<style scoped>
.tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
}
.tabs button {
  padding: 0.4rem 1.2rem;
  border: 1px solid #d0d4dc;
  border-radius: 0.3rem;
  background: white;
  cursor: pointer;
  font-size: 0.95rem;
  color: #555;
}
.tabs button.active {
  background: #1a1a1a;
  color: white;
  border-color: #1a1a1a;
}
</style>
