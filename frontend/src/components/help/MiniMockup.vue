<template>
  <div class="rounded-xl border border-slate-200 bg-slate-50/70 overflow-hidden">
    <div class="flex items-center gap-1.5 px-3 py-2 border-b border-slate-200 bg-white">
      <span class="h-2 w-2 rounded-full bg-rose-300" />
      <span class="h-2 w-2 rounded-full bg-amber-300" />
      <span class="h-2 w-2 rounded-full bg-emerald-300" />
      <span class="flex-1 mx-3 h-4 rounded-md bg-slate-100 text-[9px] text-slate-400 flex items-center justify-center truncate">
        {{ url }}
      </span>
    </div>
    <div class="p-3 space-y-1.5" dir="rtl">
      <div
        v-for="(zone, i) in zones"
        :key="i"
        class="flex items-center gap-2 rounded-lg border border-dashed px-2.5 py-1.5"
        :class="zone.tone === 'accent' ? 'border-indigo-300 bg-indigo-50/60' : 'border-slate-300 bg-white/80'"
      >
        <span
          class="flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full text-[10px] font-bold text-white"
          :class="zone.tone === 'accent' ? 'bg-indigo-500' : 'bg-slate-400'"
        >{{ i + 1 }}</span>
        <span class="flex-1 text-[11px] font-medium text-slate-600 truncate">{{ zone.label }}</span>
        <span class="h-1.5 w-10 rounded-full" :class="zone.tone === 'accent' ? 'bg-indigo-200' : 'bg-slate-200'" />
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  zones: { type: Array, required: true }, // [{label, tone?: 'accent'}]
  url: { type: String, default: '/bs/decision-center' },
})
</script>
