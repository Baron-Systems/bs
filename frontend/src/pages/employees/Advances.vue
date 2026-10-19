<template>
	<div class="flex w-full flex-col gap-4">
		<EmployeesHeader
			:title="__('السلف')"
			:subtitle="__('صرف السلف واستردادها من الاستحقاقات تلقائيًا')"
			icon="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
			gradient="from-amber-500 to-orange-600 shadow-amber-500/30"
			@company-change="load"
		>
			<template #actions>
				<Button variant="solid" @click="dialogOpen = true">{{ __("+ سلفة جديدة") }}</Button>
			</template>
		</EmployeesHeader>

		<SummaryTiles :tiles="tiles" :cols="3" />

		<section class="bs-card">
			<div class="flex flex-wrap items-center gap-2 border-b border-slate-100 p-3">
				<button
					v-for="s in STATUS_FILTERS"
					:key="s.key"
					type="button"
					class="rounded-full px-3 py-1 text-xs font-semibold"
					:class="statusFilter === s.key ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'"
					@click="statusFilter = s.key"
				>
					{{ __(s.label) }}
				</button>
				<input
					v-model="search"
					type="text"
					:placeholder="__('بحث...')"
					class="ms-auto w-44 rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs focus:bg-white focus:outline-none"
				/>
			</div>
			<AdvancesTable :rows="filtered" :loading="loading" />
		</section>

		<AdvanceDialog v-model="dialogOpen" :employees="employees" :company="company" @saved="onSaved" />
	</div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue"
import { useRouter } from "vue-router"
import { Button } from "frappe-ui"
import AdvanceDialog from "@/components/employees/AdvanceDialog.vue"
import AdvancesTable from "@/components/employees/AdvancesTable.vue"
import EmployeesHeader from "@/components/employees/EmployeesHeader.vue"
import SummaryTiles from "@/components/employees/SummaryTiles.vue"
import { useEmployeeCompany } from "@/composables/useEmployeeCompany"
import { useToast } from "@/composables/useToast"
import { call } from "@/utils/apiWrapper"
import { API, formatMoney } from "@/utils/employees"

const STATUS_FILTERS = [
	{ key: "open", label: "المفتوحة" },
	{ key: "", label: "الكل" },
	{ key: "Completed", label: "مكتملة" },
	{ key: "Closed", label: "مغلقة" },
]

const router = useRouter()
const { showError } = useToast()
const { company, loadCompanies } = useEmployeeCompany()

const rows = ref([])
const summary = ref({})
const currency = ref("")
const employees = ref([])
const loading = ref(false)
const statusFilter = ref("open")
const search = ref("")
const dialogOpen = ref(false)

const tiles = computed(() => [
	{ label: __("إجمالي السلف المفتوحة"), value: formatMoney(summary.value.open_total, currency.value), hint: __("{0} سلفة", [summary.value.open_count || 0]) },
	{ label: __("المخصوم هذا الشهر"), value: formatMoney(summary.value.deducted_this_month, currency.value), tone: "green" },
	{ label: __("متبقي السلف"), value: formatMoney(summary.value.remaining, currency.value), tone: "amber" },
])

const filtered = computed(() => {
	const q = search.value.trim().toLowerCase()
	return rows.value.filter((r) => {
		if (statusFilter.value === "open" && !["Active", "Paused"].includes(r.status)) return false
		if (statusFilter.value && statusFilter.value !== "open" && r.status !== statusFilter.value) return false
		return !q || (r.employee_name || "").toLowerCase().includes(q)
	})
})

async function load() {
	if (!company.value) return
	loading.value = true
	try {
		const [res, emps] = await Promise.all([
			call(`${API}.advances.get_advances`, { company: company.value }),
			call(`${API}.employees.get_employees`, { company: company.value }),
		])
		rows.value = res.rows || []
		summary.value = res.summary || {}
		currency.value = res.currency
		employees.value = (emps.rows || []).filter((e) => e.status !== "Left")
	} catch (e) {
		showError(e?.message || __("فشل تحميل السلف"))
	} finally {
		loading.value = false
	}
}

function onSaved(name) {
	router.push({ name: "EmployeeAdvanceDetail", params: { id: name } })
}

onMounted(async () => {
	try {
		await loadCompanies()
	} catch (e) {
		showError(e?.message || __("فشل تحميل الشركات"))
	}
	load()
})
</script>
