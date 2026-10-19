<template>
  <section :id="anchorId" class="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 scroll-mt-24">
    <header v-if="title" class="flex items-center gap-3 mb-3">
      <div
        v-if="icon"
        class="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-xl text-white shadow-sm"
        :class="accentClass"
      >
        <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="icon" />
        </svg>
      </div>
      <div class="min-w-0 flex-1">
        <h3 class="text-sm font-bold text-slate-900">{{ title }}</h3>
        <p v-if="subtitle" class="text-[11px] text-slate-500">{{ subtitle }}</p>
      </div>
      <slot name="actions" />
    </header>
    <slot />
  </section>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  title: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  icon: { type: String, default: '' },
  accent: { type: String, default: 'indigo' },
  anchor: { type: String, default: '' },
})

const anchorId = computed(() => (props.anchor ? `help-section-${props.anchor}` : undefined))

const ACCENTS = {
  indigo: 'bg-gradient-to-br from-indigo-500 to-indigo-700',
  blue: 'bg-gradient-to-br from-blue-500 to-blue-700',
  emerald: 'bg-gradient-to-br from-emerald-500 to-emerald-700',
  amber: 'bg-gradient-to-br from-amber-500 to-amber-600',
  rose: 'bg-gradient-to-br from-rose-500 to-rose-700',
  slate: 'bg-gradient-to-br from-slate-500 to-slate-700',
}

const accentClass = computed(() => ACCENTS[props.accent] || ACCENTS.indigo)
</script>
