<template>
	<div class="flex w-full flex-col gap-4">
		<EmployeesHeader
			:title="__('استحقاقات الموظفين')"
			:subtitle="__('تُحسب تلقائيًا من الدوام والإجازات والسلف')"
			icon="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z"
			gradient="from-blue-500 to-indigo-600 shadow-blue-500/30"
			@company-change="load"
		>
			<template #actions>
				<input v-model="period" type="month" class="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm" />
			</template>
		</EmployeesHeader>

		<!-- Generate banner -->
		<section
			v-if="!loading && data.missing.length"
			class="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-blue-200 bg-blue-50 p-4"
		>
			<div>
				<p class="text-sm font-bold text-blue-900">
					{{ data.rows.length ? __("{0} موظف بدون استحقاق لهذا الشهر", [data.missing.length]) : __("لم تُنشأ استحقاقات {0} بعد", [formatPeriod(period)]) }}
				</p>
				<p class="text-xs text-blue-700">{{ __("سيُنشأ استحقاق مسودة لكل موظف من دوامه وإجازاته وسلفه") }}</p>
			</div>
			<Button variant="solid" :loading="generating" @click="generate">{{ __("إنشاء استحقاقات الشهر") }}</Button>
		</section>

		<SummaryTiles v-if="data.rows.length" :tiles="tiles" :cols="6" />

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
					{{ __(s.label) }}<span v-if="s.key" class="ms-1 opacity-70">{{ data.summary.by_status?.[s.key] || 0 }}</span>
				</button>
				<div class="ms-auto flex gap-2">
					<Button v-if="draftCount" variant="subtle" :loading="recalculating" @click="recalcAll">{{ __("إعادة حساب المسودات") }}</Button>
					<Button v-if="draftCount" variant="solid" theme="green" :loading="approving" @click="approveAll">{{ __("اعتماد الكل ({0})", [draftCount]) }}</Button>
				</div>
			</div>

			<div v-if="loading" class="py-12 text-center text-sm text-slate-400">{{ __("جاري التحميل...") }}</div>
			<div v-else-if="!filtered.length" class="py-12 text-center text-sm text-slate-400">{{ __("لا توجد استحقاقات") }}</div>
			<div v-else class="overflow-x-auto">
				<table class="w-full text-sm">
					<thead>
						<tr class="bg-slate-50 text-xs text-slate-600">
							<th class="px-3 py-2 text-start font-semibold">{{ __("الموظف") }}</th>
							<th class="px-3 py-2 text-end font-semibold">{{ __("الأساسي") }}</th>
							<th class="hidden px-3 py-2 text-end font-semibold sm:table-cell">{{ __("إضافات") }}</th>
							<th class="hidden px-3 py-2 text-end font-semibold sm:table-cell">{{ __("خصومات") }}</th>
							<th class="hidden px-3 py-2 text-end font-semibold md:table-cell">{{ __("سلف") }}</th>
							<th class="px-3 py-2 text-end font-semibold">{{ __("الصافي") }}</th>
							<th class="px-3 py-2 text-start font-semibold">{{ __("الحالة") }}</th>
						</tr>
					</thead>
					<tbody class="divide-y divide-slate-100">
						<tr
							v-for="row in filtered"
							:key="row.name"
							class="cursor-pointer hover:bg-slate-50"
							@click="router.push({ name: 'EmployeePayrollEntry', params: { id: row.name } })"
						>
							<td class="px-3 py-2">
								<p class="font-semibold text-slate-900">{{ row.employee_name }}</p>
								<p class="text-[11px] text-slate-400">{{ __(PAY_TYPES_SHORT[row.pay_type] || "") }}</p>
							</td>
							<td class="px-3 py-2 text-end tabular-nums">{{ formatMoney(row.base_amount) }}</td>
							<td class="hidden px-3 py-2 text-end tabular-nums text-emerald-600 sm:table-cell">{{ row.total_earnings ? "+" + formatMoney(row.total_earnings) : "—" }}</td>
							<td class="hidden px-3 py-2 text-end tabular-nums text-red-600 sm:table-cell">{{ row.total_deductions ? "-" + formatMoney(row.total_deductions) : "—" }}</td>
							<td class="hidden px-3 py-2 text-end tabular-nums text-amber-600 md:table-cell">{{ row.total_advances ? "-" + formatMoney(row.total_advances) : "—" }}</td>
							<td class="px-3 py-2 text-end font-bold tabular-nums text-slate-900">{{ formatMoney(row.net_amount) }}</td>
							<td class="px-3 py-2"><StatusBadge :status="row.status" :map="PAYROLL_STATUS" /></td>
						</tr>
					</tbody>
					<tfoot>
						<tr class="bg-slate-50 text-sm font-bold">
							<td class="px-3 py-2">{{ __("الإجمالي") }}</td>
							<td class="px-3 py-2 text-end tabular-nums">{{ formatMoney(sum("base_amount")) }}</td>
							<td class="hidden px-3 py-2 text-end tabular-nums text-emerald-600 sm:table-cell">{{ formatMoney(sum("total_earnings")) }}</td>
							<td class="hidden px-3 py-2 text-end tabular-nums text-red-600 sm:table-cell">{{ formatMoney(sum("total_deductions")) }}</td>
							<td class="hidden px-3 py-2 text-end tabular-nums text-amber-600 md:table-cell">{{ formatMoney(sum("total_advances")) }}</td>
							<td class="px-3 py-2 text-end tabular-nums">{{ formatMoney(sum("net_amount"), data.currency) }}</td>
							<td></td>
						</tr>
					</tfoot>
				</table>
			</div>
		</section>
	</div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from "vue"
import { useRoute, useRouter } from "vue-router"
import { Button } from "frappe-ui"
import EmployeesHeader from "@/components/employees/EmployeesHeader.vue"
import StatusBadge from "@/components/employees/StatusBadge.vue"
import SummaryTiles from "@/components/employees/SummaryTiles.vue"
import { useEmployeeCompany } from "@/composables/useEmployeeCompany"
import { useToast } from "@/composables/useToast"
import { call } from "@/utils/apiWrapper"
import { API, PAYROLL_STATUS, PAY_TYPES_SHORT, currentPeriod, formatMoney, formatPeriod } from "@/utils/employees"

const STATUS_FILTERS = [
	{ key: "", label: "الكل" },
	{ key: "Draft", label: "مسودة" },
	{ key: "Approved", label: "معتمد" },
	{ key: "Paid", label: "مدفوع" },
]

const route = useRoute()
const router = useRouter()
const { showSuccess, showError, showWarning } = useToast()
const { company, loadCompanies } = useEmployeeCompany()

const period = ref(route.query.period || currentPeriod())
const data = ref({ rows: [], summary: {}, missing: [], currency: "" })
const loading = ref(false)
const generating = ref(false)
const approving = ref(false)
const recalculating = ref(false)
const statusFilter = ref("")

const filtered = computed(() => data.value.rows.filter((r) => !statusFilter.value || r.status === statusFilter.value))
const draftCount = computed(() => data.value.summary.by_status?.Draft || 0)

const tiles = computed(() => {
	const s = data.value.summary
	const c = data.value.currency
	return [
		{ label: __("الموظفون"), value: s.employees || 0 },
		{ label: __("الأساسي"), value: formatMoney(s.base, c) },
		{ label: __("الإضافات"), value: formatMoney(s.earnings, c), tone: "green" },
		{ label: __("الخصومات"), value: formatMoney(s.deductions, c), tone: "red" },
		{ label: __("السلف"), value: formatMoney(s.advances, c), tone: "amber" },
		{ label: __("صافي الاستحقاقات"), value: formatMoney(s.net, c), tone: "blue" },
	]
})

function sum(key) {
	return filtered.value.reduce((t, r) => t + Number(r[key] || 0), 0)
}

function reportErrors(errors) {
	if (!errors?.length) return
	showWarning(errors.map((e) => `${e.employee}: ${e.error}`).join(" — "))
}

async function load() {
	if (!company.value) return
	loading.value = true
	try {
		data.value = await call(`${API}.payroll.get_period`, { company: company.value, period: period.value })
	} catch (e) {
		showError(e?.message || __("فشل تحميل الاستحقاقات"))
	} finally {
		loading.value = false
	}
}

async function generate() {
	generating.value = true
	try {
		const res = await call(`${API}.payroll.generate_period`, { company: company.value, period: period.value })
		showSuccess(__("تم إنشاء {0} استحقاق", [res.created]))
		reportErrors(res.errors)
		await load()
	} catch (e) {
		showError(e?.message || __("فشل إنشاء الاستحقاقات"))
	} finally {
		generating.value = false
	}
}

async function recalcAll() {
	recalculating.value = true
	try {
		const res = await call(`${API}.payroll.recalculate_period`, { company: company.value, period: period.value })
		showSuccess(__("تمت إعادة حساب {0} استحقاق", [res.updated]))
		await load()
	} catch (e) {
		showError(e?.message || __("فشلت إعادة الحساب"))
	} finally {
		recalculating.value = false
	}
}

async function approveAll() {
	if (!confirm(__("اعتماد {0} استحقاق؟ سيتم إنشاء القيود المحاسبية وخصم أقساط السلف", [draftCount.value]))) return
	approving.value = true
	try {
		const res = await call(`${API}.payroll.approve_period`, { company: company.value, period: period.value })
		showSuccess(__("تم اعتماد {0} استحقاق", [res.approved]))
		reportErrors(res.errors)
		await load()
	} catch (e) {
		showError(e?.message || __("فشل الاعتماد"))
	} finally {
		approving.value = false
	}
}

watch(period, () => {
	router.replace({ query: { period: period.value } })
	load()
})

onMounted(async () => {
	try {
		await loadCompanies()
	} catch (e) {
		showError(e?.message || __("فشل تحميل الشركات"))
	}
	load()
})
</script>
