<template>
  <RouterLink
    :to="{ name: 'DecisionCenterHelp', query: { tab: target.tab, section: target.section } }"
    class="inline-flex items-center justify-center h-4.5 w-4.5 min-w-[18px] min-h-[18px] rounded-full border border-indigo-200 bg-indigo-50 text-indigo-500 hover:bg-indigo-100 hover:text-indigo-700 transition-colors align-middle"
    :title="__('شرح في مركز المساعدة')"
    @click.stop
  >
    <span class="text-[10px] font-bold leading-none">؟</span>
  </RouterLink>
</template>

<script setup>
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import { HELP_TOPICS } from '@/data/help'

const props = defineProps({
  topic: { type: String, default: '' },
  tab: { type: String, default: '' },
  section: { type: String, default: '' },
})

const target = computed(() => {
  if (props.tab) return { tab: props.tab, section: props.section }
  return HELP_TOPICS[props.topic] || { tab: 'start', section: '' }
})
</script>
