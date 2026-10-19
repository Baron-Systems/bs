<template>
	<div ref="root" class="relative">
		<input
			v-model="query"
			type="text"
			:placeholder="placeholder || __('ابحث عن موظف...')"
			:disabled="disabled"
			class="bs-input bs-input-sm w-full px-3 py-2 disabled:bg-slate-50"
			@focus="open = true"
			@input="open = true"
			@keydown.down.prevent="move(1)"
			@keydown.up.prevent="move(-1)"
			@keydown.enter.prevent="pick(filtered[highlight])"
			@keydown.esc="open = false"
		/>
		<ul
			v-if="open && filtered.length"
			class="absolute z-30 mt-1 max-h-60 w-full overflow-y-auto rounded-lg border border-slate-200 bg-white py-1 shadow-lg"
		>
			<li
				v-for="(emp, i) in filtered"
				:key="emp.name"
				class="flex cursor-pointer items-center justify-between gap-2 px-3 py-2 text-sm"
				:class="i === highlight ? 'bg-blue-50 text-blue-700' : 'hover:bg-slate-50'"
				@mousedown.prevent="pick(emp)"
			>
				<span class="truncate font-medium">{{ emp.employee_name }}</span>
				<span class="truncate text-xs text-slate-400">{{ emp.designation || emp.name }}</span>
			</li>
		</ul>
	</div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue"

const props = defineProps({
	modelValue: { type: String, default: "" },
	employees: { type: Array, default: () => [] },
	placeholder: { type: String, default: "" },
	disabled: { type: Boolean, default: false },
})
const emit = defineEmits(["update:modelValue"])

const root = ref(null)
const open = ref(false)
const query = ref("")
const highlight = ref(0)

const selected = computed(() => props.employees.find((e) => e.name === props.modelValue))

watch(selected, (emp) => { query.value = emp ? emp.employee_name : "" }, { immediate: true })

const filtered = computed(() => {
	const q = query.value.trim().toLowerCase()
	const list = selected.value && query.value === selected.value.employee_name ? props.employees : props.employees.filter(
		(e) => !q || (e.employee_name || "").toLowerCase().includes(q) || (e.name || "").toLowerCase().includes(q)
	)
	return list.slice(0, 50)
})

watch(filtered, () => { highlight.value = 0 })

function move(step) {
	if (!filtered.value.length) return
	open.value = true
	highlight.value = (highlight.value + step + filtered.value.length) % filtered.value.length
}

function pick(emp) {
	if (!emp) return
	emit("update:modelValue", emp.name)
	query.value = emp.employee_name
	open.value = false
}

function onClickOutside(e) {
	if (root.value && !root.value.contains(e.target)) {
		open.value = false
		query.value = selected.value ? selected.value.employee_name : ""
	}
}

onMounted(() => document.addEventListener("mousedown", onClickOutside))
onBeforeUnmount(() => document.removeEventListener("mousedown", onClickOutside))
</script>
