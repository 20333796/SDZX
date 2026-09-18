<script setup lang="ts">
import { Info, LockKeyhole } from '@lucide/vue'

// The honest "this column is not open to anonymous visitors yet" notice, shared so that every
// not-yet-open column explains the same thing the same way instead of each inventing a variant.
defineProps<{
  title: string
  /** `auth` = needs the campus single sign-on, `note` = still being built. */
  tone?: 'note' | 'auth'
}>()
</script>

<template>
  <div class="destination-note" :class="`is-${tone ?? 'note'}`">
    <LockKeyhole v-if="tone === 'auth'" :size="18" />
    <Info v-else :size="18" />
    <div>
      <strong>{{ title }}</strong>
      <p><slot /></p>
    </div>
  </div>
</template>

<style scoped>
.destination-note { display: flex; align-items: flex-start; gap: 12px; padding: 16px 18px; color: #33566b; background: #f2f7fb; border-left: 3px solid #8fb4cc; }
.destination-note.is-auth { background: #f4f6fb; border-left-color: #0870bc; }
.destination-note svg { flex: 0 0 auto; margin-top: 2px; color: #0870bc; }
.destination-note div { display: grid; gap: 5px; }
.destination-note strong { color: #17384d; font-size: 15px; }
.destination-note p { margin: 0; color: #5f7487; font-size: 14px; line-height: 1.8; }
</style>
