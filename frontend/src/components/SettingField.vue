<template>
  <div class="flex flex-col gap-0.5">
    <div class="flex items-center justify-between gap-2">
      <label class="text-xs font-semibold text-slate-700">{{ label }}</label>
      <span v-if="suffix" class="text-[11px] font-medium text-slate-500">{{ suffix }}</span>
    </div>
    <input
      :type="inputType"
      :value="modelValue"
      :min="min"
      :max="max"
      :step="step"
      class="w-full border rounded-lg px-3 py-1.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
      :class="error ? 'border-rose-300 focus:ring-rose-200 focus:border-rose-500' : 'border-slate-300'"
      @input="onInput"
    />
    <p v-if="help" class="text-[11px] text-slate-500 leading-snug">
      <span class="font-medium text-slate-600">{{ __('شرح:') }}</span>
      {{ help }}
    </p>
    <p v-if="error" class="text-[11px] text-rose-600">{{ error }}</p>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: { type: [Number, String], default: null },
  label: { type: String, required: true },
  help: { type: String, default: '' },
  suffix: { type: String, default: '' },
  type: { type: String, default: 'number' },
  min: { type: Number, default: undefined },
  max: { type: Number, default: undefined },
  step: { type: [Number, String], default: undefined },
  error: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue'])

const inputType = computed(() => 'number')

function onInput(event) {
  const val = event.target.value
  if (val === '' || val === null || val === undefined) {
    emit('update:modelValue', null)
    return
  }
  const num = props.type === 'int' ? parseInt(val, 10) : parseFloat(val)
  emit('update:modelValue', Number.isNaN(num) ? null : num)
}
</script>
