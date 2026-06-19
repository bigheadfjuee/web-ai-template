import { createApp } from 'vue'
import App from './App.vue'
import { initKeycloak } from './auth'

initKeycloak()
  .then((authenticated) => {
    if (!authenticated) {
      document.getElementById('app')!.textContent = 'Authentication failed: not authenticated.'
      return
    }
    createApp(App).mount('#app')
  })
  .catch(() => {
    document.getElementById('app')!.textContent = 'Authentication failed: could not reach Keycloak.'
  })
