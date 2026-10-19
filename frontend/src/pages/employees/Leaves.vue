<template>
	<div class="flex w-full flex-col gap-4">
		<EmployeesHeader
			:title="__('الإجازات')"
			:subtitle="__('الطلبات والموافقات — الإجازة المعتمدة تظهر في الدوام والاستحقاق تلقائيًا')"
			icon="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
			gradient="from-sky-500 to-blue-600 shadow-sky-500/30"
			@company-change="load"
		>
			<template #actions>
				<Button variant="solid" @click="openDialog()">{{ __("+ طلب إجازة") }}</Button>
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
			<LeavesTable :rows="filtered" :loading="loading" @edit="openDialog" @changed="load" />
		</section>

		<LeaveDialog v-model="dialogOpen" :record="dialogRecord" :employees="employees" @saved="load" />
	</div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from "vue"
import { Button } from "frappe-ui"
import EmployeesHeader from "@/components/employees/EmployeesHeader.vue"
import LeaveDialog from "@/components/employees/LeaveDialog.vue"
import LeavesTable from "@/components/employees/LeavesTable.vue"
import SummaryTiles from "@/components/employees/SummaryTiles.vue"
import { useEmployeeCompany } from "@/composables/useEmployeeCompany"
import { useToast } from "@/composables/useToast"
import { call } from "@/utils/apiWrapper"
import { API } from "@/utils/employees"

const STATUS_FILTERS = [
	{ key: "", label: "الكل" },
	{ key: "Pending", label: "بانتظار الموافقة" },
	{ key: "Approved", label: "مقبولة" },
	{ key: "Rejected", label: "مرفوضة" },
	{ key: "Cancelled", label: "ملغاة" },
]

const { showError } = useToast()
const { company, loadCompanies } = useEmployeeCompany()

const rows = ref([])
const summary = ref({})
const employees = ref([])
let employeesCompany = ""
const loading = ref(false)
const statusFilter = ref("")
const search = ref("")
const dialogOpen = ref(false)
const dialogRecord = ref(null)

const tiles = computed(() => [
	{ label: __("طلبات اليوم"), value: summary.value.today_requests || 0 },
	{ label: __("بانتظار الموافقة"), value: summary.value.pending || 0, tone: "amber", onClick: () => { statusFilter.value = "Pending" }, active: statusFilter.value === "Pending" },
	{ label: __("في إجازة الآن"), value: summary.value.on_leave_now || 0, tone: "sky" },
])

const filtered = computed(() => {
	const q = search.value.trim().toLowerCase()
	if (!q) return rows.value
	return rows.value.filter((r) => (r.employee_name || "").toLowerCase().includes(q))
})

function openDialog(row = null) {
	dialogRecord.value = row
	dialogOpen.value = true
}

async function load() {
	if (!company.value) return
	loading.value = true
	try {
		const [res, emps] = await Promise.all([
			call(`${API}.leaves.get_leaves`, { company: company.value, status: statusFilter.value || null }),
			employeesCompany === company.value ? null : call(`${API}.employees.get_employees`, { company: company.value }),
		])
		rows.value = res.rows || []
		summary.value = res.summary || {}
		if (emps) {
			employees.value = (emps.rows || []).filter((e) => e.status !== "Left")
			employeesCompany = company.value
		}
	} catch (e) {
		showError(e?.message || __("فشل تحميل الإجازات"))
	} finally {
		loading.value = false
	}
}

watch(statusFilter, load)

onMounted(async () => {
	try {
		await loadCompanies()
	} catch (e) {
		showError(e?.message || __("فشل تحميل الشركات"))
	}
	load()
})
</script>
