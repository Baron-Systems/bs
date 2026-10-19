<template>
<div class="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
	<!-- Header -->
	<div class="flex items-center justify-between gap-3 p-3 border-b border-slate-100">
		<h3 class="text-sm font-bold text-slate-800 flex items-center gap-2">
			<svg v-if="icon" class="w-4 h-4 flex-shrink-0" :class="iconColor" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="icon" />
			</svg>
			{{ title }}
		</h3>
		<div v-if="searchable && data.length > 5" class="relative">
			<input
				v-model="searchQuery"
				type="text"
				:placeholder="__('بحث...')"
				class="w-36 sm:w-48 border border-slate-200 rounded-lg px-3 py-1.5 text-xs bg-slate-50 focus:bg-white focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-100 transition-all"
			/>
		</div>
	</div>

	<!-- Table -->
	<div class="overflow-x-auto">
		<table class="w-full text-sm">
			<thead>
				<tr class="bg-slate-50 text-slate-600">
					<th
						v-for="col in columns"
						:key="col.key"
						class="px-3 py-2 text-xs font-semibold text-right whitespace-nowrap"
						:class="{ 'cursor-pointer hover:text-blue-600 select-none': sortable }"
						@click="sortable && toggleSort(col.key)"
					>
						<span class="flex items-center gap-1">
							{{ col.label }}
							<template v-if="sortable && sortKey === col.key">
								<svg v-if="sortDir === 'asc'" class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 11l5-5m0 0l5 5" /></svg>
								<svg v-else class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 13l-5 5m0 0l-5-5" /></svg>
							</template>
						</span>
					</th>
				</tr>
			</thead>
			<tbody class="divide-y divide-slate-100">
				<tr v-for="(row, idx) in pagedRows" :key="idx" class="hover:bg-slate-50 transition-colors">
					<td
						v-for="col in columns"
						:key="col.key"
						class="px-3 py-2 text-right whitespace-nowrap"
						:class="col.class || ''"
					>
						<slot :name="'cell-' + col.key" :row="row" :value="row[col.key]">
							<span v-if="col.format === 'currency'" class="font-semibold">{{ formatFn(row[col.key]) }}</span>
							<span v-else-if="col.format === 'pct'" :class="pctColor(row[col.key])">{{ formatPctValue(row[col.key]) }}</span>
							<span v-else-if="col.format === 'number'" class="tabular-nums">{{ formatNum(row[col.key]) }}</span>
							<span v-else>{{ row[col.key] ?? "—" }}</span>
						</slot>
					</td>
				</tr>
			</tbody>
		</table>
	</div>

	<!-- Empty state -->
	<div v-if="!filteredRows.length" class="py-8 text-center text-xs text-slate-400">
		{{ __("لا توجد بيانات") }}
	</div>

	<!-- Pagination -->
	<div v-if="totalPages > 1" class="flex items-center justify-between px-3 py-2 border-t border-slate-100 text-xs text-slate-500">
		<span>{{ filteredRows.length }} {{ __("سجل") }}</span>
		<div class="flex items-center gap-1">
			<button
				@click="currentPage = Math.max(1, currentPage - 1)"
				:disabled="currentPage <= 1"
				class="px-2 py-1 rounded border border-slate-200 hover:bg-slate-50 disabled:opacity-40 transition-all"
			>←</button>
			<span class="px-2">{{ currentPage }} / {{ totalPages }}</span>
			<button
				@click="currentPage = Math.min(totalPages, currentPage + 1)"
				:disabled="currentPage >= totalPages"
				class="px-2 py-1 rounded border border-slate-200 hover:bg-slate-50 disabled:opacity-40 transition-all"
			>→</button>
		</div>
	</div>
</div>
</template>

<script setup>
import { ref, computed, watch } from "vue"

const props = defineProps({
	title: { type: String, default: "" },
	icon: { type: String, default: "" },
	iconColor: { type: String, default: "text-slate-500" },
	columns: { type: Array, required: true },
	data: { type: Array, default: () => [] },
	searchable: { type: Boolean, default: true },
	sortable: { type: Boolean, default: true },
	pageSize: { type: Number, default: 10 },
	formatFn: { type: Function, default: (v) => String(v ?? "—") },
})

const searchQuery = ref("")
const sortKey = ref("")
const sortDir = ref("desc")
const currentPage = ref(1)

// Reset page on search/sort change
watch([searchQuery, sortKey, sortDir], () => { currentPage.value = 1 })
watch(() => props.data, () => { currentPage.value = 1 })

function toggleSort(key) {
	if (sortKey.value === key) {
		sortDir.value = sortDir.value === "asc" ? "desc" : "asc"
	} else {
		sortKey.value = key
		sortDir.value = "desc"
	}
}

const filteredRows = computed(() => {
	let rows = [...props.data]
	const q = searchQuery.value.trim().toLowerCase()
	if (q) {
		rows = rows.filter((row) =>
			props.columns.some((col) => String(row[col.key] || "").toLowerCase().includes(q))
		)
	}
	if (sortKey.value) {
		rows.sort((a, b) => {
			const va = a[sortKey.value]
			const vb = b[sortKey.value]
			const na = Number(va)
			const nb = Number(vb)
			const cmp = (!isNaN(na) && !isNaN(nb)) ? na - nb : String(va || "").localeCompare(String(vb || ""), "ar")
			return sortDir.value === "asc" ? cmp : -cmp
		})
	}
	return rows
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredRows.value.length / props.pageSize)))
const pagedRows = computed(() => {
	const start = (currentPage.value - 1) * props.pageSize
	return filteredRows.value.slice(start, start + props.pageSize)
})

function pctColor(val) {
	const n = Number(val)
	if (n > 0) return "text-emerald-600 font-semibold"
	if (n < 0) return "text-red-600 font-semibold"
	return "text-slate-500"
}

function formatPctValue(val) {
	if (val === null || val === undefined) return "—"
	const n = Number(val)
	if (isNaN(n)) return "—"
	const sign = n > 0 ? "+" : ""
	return `${sign}${n.toFixed(1)}%`
}

function formatNum(val) {
	if (val === null || val === undefined) return "—"
	return Number(val).toLocaleString("en-US", { maximumFractionDigits: 2 })
}
</script>
