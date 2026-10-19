<template>
	<div class="flex w-full flex-col gap-4">
		<EmployeesHeader :title="__('الموظفون')" :subtitle="__('بيانات الموظفين وطريقة احتساب الأجر')" @company-change="load">
			<template #actions>
				<RouterLink
					:to="{ name: 'EmployeeNew' }"
					class="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-700"
				>
					<svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" /></svg>
					{{ __("موظف جديد") }}
				</RouterLink>
			</template>
		</EmployeesHeader>

		<SummaryTiles :tiles="statusTiles" :cols="5" />

		<section class="bs-card">
			<div class="border-b border-slate-100 p-3">
				<input
					v-model="search"
					type="text"
					:placeholder="__('بحث عن موظف بالاسم أو الرقم أو الوظيفة...')"
					class="bs-input bs-input-sm w-full bg-slate-50 px-3 py-2 focus:bg-white focus:ring-1"
				/>
			</div>

			<div v-if="loading" class="py-12 text-center text-sm text-slate-400">{{ __("جاري التحميل...") }}</div>
			<div v-else-if="!filtered.length" class="py-12 text-center text-sm text-slate-400">
				{{ rows.length ? __("لا توجد نتائج مطابقة") : __("لا يوجد موظفون بعد — أضف أول موظف") }}
			</div>
			<div v-else class="overflow-x-auto">
				<table class="w-full text-sm">
					<thead>
						<tr class="bg-slate-50 text-xs text-slate-600">
							<th class="px-3 py-2 text-start font-semibold">{{ __("الموظف") }}</th>
							<th class="px-3 py-2 text-start font-semibold">{{ __("الوظيفة") }}</th>
							<th class="hidden px-3 py-2 text-start font-semibold sm:table-cell">{{ __("القسم") }}</th>
							<th class="hidden px-3 py-2 text-start font-semibold md:table-cell">{{ __("طريقة الأجر") }}</th>
							<th class="px-3 py-2 text-end font-semibold">{{ __("الأجر") }}</th>
							<th class="px-3 py-2 text-start font-semibold">{{ __("الحالة") }}</th>
						</tr>
					</thead>
					<tbody class="divide-y divide-slate-100">
						<tr
							v-for="row in filtered"
							:key="row.name"
							class="cursor-pointer hover:bg-slate-50"
							@click="router.push({ name: 'EmployeeDetail', params: { id: row.name } })"
						>
							<td class="px-3 py-2">
								<div class="flex items-center gap-2">
									<img v-if="row.image" :src="row.image" class="h-8 w-8 flex-shrink-0 rounded-full object-cover" />
									<div v-else class="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-indigo-50 text-xs font-bold text-indigo-600">
										{{ initials(row.employee_name) }}
									</div>
									<div class="min-w-0">
										<p class="truncate font-semibold text-slate-900">{{ row.employee_name }}</p>
										<p class="truncate text-[11px] text-slate-400">{{ row.name }}</p>
									</div>
								</div>
							</td>
							<td class="px-3 py-2 text-slate-600">{{ row.designation || "—" }}</td>
							<td class="hidden px-3 py-2 text-slate-600 sm:table-cell">{{ row.department || "—" }}</td>
							<td class="hidden px-3 py-2 text-slate-600 md:table-cell">{{ __(PAY_TYPES_SHORT[row.bs_pay_type || "Monthly"]) }}</td>
							<td class="whitespace-nowrap px-3 py-2 text-end font-semibold tabular-nums text-slate-900">
								{{ formatMoney(row.pay_amount) }}<span class="text-xs font-normal text-slate-500">{{ __(PAY_UNITS[row.pay_unit]) }}</span>
							</td>
							<td class="px-3 py-2"><StatusBadge :status="row.display_status" :map="EMPLOYEE_STATUS" /></td>
						</tr>
					</tbody>
				</table>
			</div>
		</section>
	</div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue"
import { useRouter } from "vue-router"
import EmployeesHeader from "@/components/employees/EmployeesHeader.vue"
import StatusBadge from "@/components/employees/StatusBadge.vue"
import SummaryTiles from "@/components/employees/SummaryTiles.vue"
import { useEmployeeCompany } from "@/composables/useEmployeeCompany"
import { useToast } from "@/composables/useToast"
import { call } from "@/utils/apiWrapper"
import { API, EMPLOYEE_STATUS, PAY_TYPES_SHORT, PAY_UNITS, formatMoney, initials } from "@/utils/employees"

const router = useRouter()
const { showError } = useToast()
const { company, loadCompanies } = useEmployeeCompany()

const rows = ref([])
const counts = ref({})
const loading = ref(false)
const search = ref("")
const statusFilter = ref("all")

const STATUS_TABS = [
	{ key: "all", label: "الكل" },
	{ key: "Active", label: "فعال", tone: "green" },
	{ key: "On Leave", label: "إجازة", tone: "sky" },
	{ key: "Suspended", label: "موقوف", tone: "amber" },
	{ key: "Left", label: "أنهى العمل", tone: "slate" },
]

const statusTiles = computed(() =>
	STATUS_TABS.map((t) => ({
		key: t.key,
		label: __(t.label),
		value: counts.value[t.key] || 0,
		tone: t.tone,
		active: statusFilter.value === t.key,
		onClick: () => { statusFilter.value = t.key },
	}))
)

const filtered = computed(() => {
	const q = search.value.trim().toLowerCase()
	return rows.value.filter((r) => {
		if (statusFilter.value !== "all" && r.display_status !== statusFilter.value) return false
		if (!q) return true
		return [r.employee_name, r.name, r.designation, r.department, r.cell_number]
			.some((v) => String(v || "").toLowerCase().includes(q))
	})
})

async function load() {
	if (!company.value) return
	loading.value = true
	try {
		const res = await call(`${API}.employees.get_employees`, { company: company.value })
		rows.value = res.rows || []
		counts.value = res.counts || {}
	} catch (e) {
		showError(e?.message || __("فشل تحميل الموظفين"))
	} finally {
		loading.value = false
	}
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
