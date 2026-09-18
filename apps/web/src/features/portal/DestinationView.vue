<script setup lang="ts">
// Shared furniture for the columns that do not have a feature component of their own yet: a white work
// area carrying that column's own heading, in the same visual language as the built columns
// (ResourceCatalog / LearningTasks / WellLogLab: eyebrow + h2 + intro, then the content).
defineProps<{ eyebrow: string; title: string; intro: string }>()
</script>

<template>
  <section class="destination-view">
    <header class="destination-heading">
      <p class="eyebrow">{{ eyebrow }}</p>
      <h2>{{ title }}</h2>
      <span>{{ intro }}</span>
    </header>
    <slot />
  </section>
</template>

<style scoped>
.destination-view { display: grid; gap: 26px; padding: 40px 42px; background: #fff; border: 1px solid #d9e5ef; border-top: 3px solid #d5e5ed; }
.destination-heading { display: grid; gap: 8px; max-width: 760px; }
.destination-heading h2 { margin: 0; color: #17384d; font-family: "Alibaba PuHuiTi", "Microsoft YaHei", sans-serif; font-size: clamp(22px, 2.1vw, 30px); font-weight: 800; }
.destination-heading span { color: #5f7487; line-height: 1.85; }
@media (max-width: 760px) { .destination-view { padding: 26px 20px; } }
</style>
