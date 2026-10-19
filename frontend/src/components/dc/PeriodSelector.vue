<template>
<div class="flex flex-col sm:flex-row gap-2 items-end">
	<div class="w-full sm:w-auto">
		<label class="block text-xs font-semibold text-slate-700 mb-1">{{ __("الفترة") }}</label>
		<select
			:value="modelValue"
			@change="onPeriodChange($event.target.value)"
			class="w-full sm:w-44 border border-slate-300 rounded-xl px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white transition-all"
		>
			<option v-for="p in periods" :key="p.value" :value="p.value">{{ p.label }}</option>
		</select>
	</div>
	<template v-if="modelValue === 'custom'">
		<div class="w-full sm:w-36">
			<label class="block text-xs font-semibold text-slate-700 mb-1">{{ __("من") }}</label>
			<input
				type="date"
				:value="fromDate"
				@change="$emit('update:fromDate', $event.target.value)"
				class="w-full border border-slate-300 rounded-xl px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white transition-all"
			/>
		</div>
		<div class="w-full sm:w-36">
			<label class="block text-xs font-semibold text-slate-700 mb-1">{{ __("إلى") }}</label>
			<input
				type="date"
				:value="toDate"
				@change="$emit('update:toDate', $event.target.value)"
				class="w-full border border-slate-300 rounded-xl px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white transition-all"
			/>
		</div>
	</template>
</div>
</template>

<script setup>
defineProps({
	modelValue: { type: String, default: "last_30_days" },
	fromDate: { type: String, default: "" },
	toDate: { type: String, default: "" },
})

const emit = defineEmits(["update:modelValue", "update:fromDate", "update:toDate"])

const periods = [
	{ value: "today", label: __("اليوم") },
	{ value: "last_7_days", label: __("آخر 7 أيام") },
	{ value: "last_30_days", label: __("آخر 30 يومًا") },
	{ value: "this_month", label: __("هذا الشهر") },
	{ value: "last_month", label: __("الشهر السابق") },
	{ value: "this_quarter", label: __("هذا الربع") },
	{ value: "this_year", label: __("هذه السنة") },
	{ value: "custom", label: __("فترة مخصصة") },
]

function onPeriodChange(val) {
	emit("update:modelValue", val)
}
</script>
