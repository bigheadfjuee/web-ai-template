<script setup lang="ts">
import { onMounted, ref } from 'vue'

const statusText = ref<string>('Backend status: loading...')

onMounted(async () => {
  try {
    const res = await fetch('/api/health')
    if (!res.ok) {
      statusText.value = 'Backend status: unreachable'
      return
    }
    const body = (await res.json()) as { status?: string }
    statusText.value = `Backend status: ${body.status ?? 'unknown'}`
  } catch {
    statusText.value = 'Backend status: unreachable'
  }
})
</script>

<template>
  <section class="health-check">
    <p>{{ statusText }}</p>
  </section>
</template>

<style scoped>
.health-check {
  margin-top: 1rem;
  padding: 1rem;
  border: 1px solid #d0d4dc;
  border-radius: 0.5rem;
  background: white;
}
</style>
