import { createApp } from 'vue'
import { createPinia } from 'pinia'
import AppShell from './AppShell.vue'
import { router } from './router'
import { session } from './session'
import './styles.css'

void session.restoreGeoChatSession()

createApp(AppShell).use(createPinia()).use(router).mount('#app')
