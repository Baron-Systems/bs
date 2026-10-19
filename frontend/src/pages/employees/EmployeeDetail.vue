<template>
	<div class="flex w-full flex-col gap-4">
		<div v-if="loading && !emp" class="py-12 text-center text-sm text-slate-400">{{ __("جاري التحميل...") }}</div>

		<template v-else-if="emp">
			<!-- Header card -->
			<section class="bs-card p-4">
				<div class="flex flex-wrap items-start justify-between gap-4">
					<div class="flex min-w-0 items-center gap-3">
						<img v-if="emp.image" :src="emp.image" class="h-14 w-14 flex-shrink-0 rounded-full object-cover ring-2 ring-slate-100" />
						<div v-else class="flex h-14 w-14 flex-shrink-0 items-center justify-center rounded-full bg-indigo-50 text-lg font-bold text-indigo-600">
							{{ initials(emp.employee_name) }}
						</div>
						<div class="min-w-0">
							<div class="flex flex-wrap items-center gap-2">
								<h1 class="truncate text-lg font-bold text-slate-900">{{ emp.employee_name }}</h1>
								<StatusBadge :status="displayStatus" :map="EMPLOYEE_STATUS" />
							</div>
							<p class="truncate text-sm text-slate-500">
								{{ [emp.designation, emp.department && __("قسم {0}", [emp.department])].filter(Boolean).join(" — ") || emp.name }}
							</p>
						</div>
					</div>
					<div class="flex items-center gap-4">
						<div class="text-end">
							<p class="text-xs text-slate-500">{{ __(PAY_TYPES[emp.bs_pay_type || "Monthly"]) }}</p>
							<p class="text-lg font-bold tabular-nums text-slate-900">
								{{ formatMoney(emp.pay_amount, currency) }}<span class="text-xs font-normal text-slate-500">{{ __(PAY_UNITS[emp.pay_unit]) }}</span>
							</p>
						</div>
						<RouterLink
							:to="{ name: 'EmployeeEdit', params: { id: emp.name } }"
							class="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
						>
							{{ __("تعديل") }}
						</RouterLink>
					</div>
				</div>
			</section>

			<!-- This month -->
			<section v-if="summary" class="bs-card p-4">
				<div class="mb-3 flex items-center justify-between">
					<h2 class="text-sm font-bold text-slate-800">{{ __("هذا الشهر") }} — {{ formatPeriod(summary.period) }}</h2>
				</div>
				<SummaryTiles :tiles="summaryTiles" :cols="4" />
			</section>

			<!-- Tabs -->
			<div class="flex gap-1 overflow-x-auto border-b border-slate-200">
				<button
					v-for="t in TABS"
					:key="t.key"
					type="button"
					class="whitespace-nowrap border-b-2 px-4 py-2 text-sm font-semibold transition-colors"
					:class="tab === t.key ? 'border-blue-600 text-blue-700' : 'border-transparent text-slate-500 hover:text-slate-800'"
					@click="tab = t.key"
				>
					{{ __(t.label) }}
				</button>
			</div>

			<!-- Data -->
			<section v-if="tab === 'data'" class="grid grid-cols-1 gap-4 lg:grid-cols-2">
				<InfoCard :title="__('معلومات الموظف')" :rows="[
					[__('رقم الموظف'), emp.employee_number || emp.name],
					[__('رقم الهاتف'), emp.cell_number],
					[__('رقم الهوية'), emp.bs_national_id],
					[__('تاريخ الميلاد'), emp.date_of_birth && formatDate(emp.date_of_birth)],
					[__('العنوان'), emp.current_address],
				]" />
				<InfoCard :title="__('معلومات العمل')" :rows="[
					[__('تاريخ بدء العمل'), formatDate(emp.date_of_joining)],
					[__('الفرع'), emp.branch],
					[__('المدير المباشر'), emp.reports_to],
					[__('نوع الموظف'), emp.bs_employee_type && __(EMPLOYEE_TYPES[emp.bs_employee_type])],
					[__('طريقة الدفع'), emp.salary_mode && __(SALARY_MODES[emp.salary_mode])],
				]" />
				<InfoCard :title="__('الدوام')" :rows="[
					[__('أيام العمل'), workDaysLabel],
					[__('الدوام'), emp.bs_shift_start && emp.bs_shift_end ? `${emp.bs_shift_start} → ${emp.bs_shift_end}` : __('افتراضي')],
					[__('فترة السماح'), emp.bs_grace_minutes != null ? __('{0} دقيقة', [emp.bs_grace_minutes]) : __('افتراضي')],
					[__('ساعات اليوم'), emp.bs_daily_hours],
				]" />
				<InfoCard v-if="summary" :title="__('الإجازة السنوية') + ' ' + summary.leave_balance.year" :rows="[
					[__('الرصيد الأولي'), __('{0} يوم', [summary.leave_balance.allowance])],
					[__('المستخدم'), __('{0} يوم', [summary.leave_balance.used])],
					[__('المتبقي'), __('{0} يوم', [summary.leave_balance.remaining])],
				]" />
			</section>

			<!-- Attendance -->
			<section v-else-if="tab === 'attendance'" class="bs-card">
				<div class="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 p-3">
					<p class="text-sm font-bold text-slate-800">{{ formatPeriod(period) }}</p>
					<div class="flex items-center gap-2">
						<input v-model="period" type="month" class="rounded-lg border border-slate-200 px-3 py-1.5 text-sm" />
						<Button variant="solid" @click="openAttendance()">{{ __("+ تسجيل دوام") }}</Button>
					</div>
				</div>
				<div v-if="month" class="border-b border-slate-100 p-3">
					<SummaryTiles :tiles="monthTiles" :cols="6" />
				</div>
				<div v-if="monthLoading" class="py-12 text-center text-sm text-slate-400">{{ __("جاري التحميل...") }}</div>
				<ul v-else-if="month" class="divide-y divide-slate-100">
					<li
						v-for="day in visibleDays"
						:key="day.date"
						class="flex cursor-pointer items-center gap-3 px-4 py-2.5 hover:bg-slate-50"
						:class="!day.is_work_day ? 'bg-slate-50/60' : ''"
						@click="openAttendance(day)"
					>
						<div class="w-24 flex-shrink-0">
							<p class="text-sm font-semibold text-slate-800">{{ __(weekdayName(day.date)) }}</p>
							<p class="text-[11px] tabular-nums text-slate-400">{{ formatShortDate(day.date) }}</p>
						</div>
						<div class="flex-1 text-sm tabular-nums text-slate-700" dir="ltr">
							<template v-if="day.check_in || day.check_out">{{ day.check_in || "—" }} → {{ day.check_out || "—" }}</template>
						</div>
						<div class="hidden w-20 text-center text-sm tabular-nums text-slate-600 sm:block" dir="ltr">
							{{ day.working_hours ? formatHours(day.working_hours) : "" }}
						</div>
						<div class="w-32 text-end">
							<StatusBadge v-if="day.status" :status="attendanceKey(day)" :map="ATTENDANCE_STATUS" />
							<p v-if="day.status === 'On Leave' && day.leave_type" class="text-[11px] text-slate-400">{{ __(LEAVE_TYPES[day.leave_type]) }}</p>
							<p v-else-if="day.late_minutes" class="text-[11px] text-amber-600">{{ __("تأخير {0} د", [day.late_minutes]) }}</p>
							<p v-else-if="day.overtime_hours" class="text-[11px] text-emerald-600">{{ __("إضافي {0}", [formatHours(day.overtime_hours)]) }}</p>
						</div>
					</li>
				</ul>
			</section>

			<!-- Leaves -->
			<section v-else-if="tab === 'leaves'" class="bs-card">
				<div class="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 p-3">
					<p v-if="summary" class="text-sm text-slate-600">
						{{ __("رصيد السنوية") }}:
						<b class="tabular-nums text-slate-900">{{ summary.leave_balance.remaining }}</b>
						<span class="text-slate-400"> / {{ summary.leave_balance.allowance }}</span>
					</p>
					<Button variant="solid" @click="openLeave()">{{ __("+ طلب إجازة") }}</Button>
				</div>
				<LeavesTable :rows="leaves" :loading="leavesLoading" :show-employee="false" @edit="openLeave" @changed="onLeaveChanged" />
			</section>

			<!-- Advances -->
			<section v-else-if="tab === 'advances'" class="bs-card">
				<div class="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 p-3">
					<p class="text-sm text-slate-600">
						{{ __("السلف المتبقية") }}: <b class="tabular-nums text-amber-600">{{ formatMoney(summary?.advances_remaining, currency) }}</b>
					</p>
					<Button variant="solid" @click="advanceOpen = true">{{ __("+ سلفة جديدة") }}</Button>
				</div>
				<AdvancesTable :rows="advancesRows" :loading="advancesLoading" :show-employee="false" />
			</section>

			<!-- Payroll -->
			<section v-else-if="tab === 'payroll'" class="bs-card">
				<div v-if="payrollLoading" class="py-12 text-center text-sm text-slate-400">{{ __("جاري التحميل...") }}</div>
				<div v-else-if="!payrollRows.length" class="py-12 text-center text-sm text-slate-400">{{ __("لا توجد استحقاقات بعد") }}</div>
				<table v-else class="w-full text-sm">
					<thead>
						<tr class="bg-slate-50 text-xs text-slate-600">
							<th class="px-3 py-2 text-start font-semibold">{{ __("الشهر") }}</th>
							<th class="px-3 py-2 text-end font-semibold">{{ __("الأساسي") }}</th>
							<th class="hidden px-3 py-2 text-end font-semibold sm:table-cell">{{ __("إضافات") }}</th>
							<th class="hidden px-3 py-2 text-end font-semibold sm:table-cell">{{ __("خصومات") }}</th>
							<th class="hidden px-3 py-2 text-end font-semibold sm:table-cell">{{ __("سلف") }}</th>
							<th class="px-3 py-2 text-end font-semibold">{{ __("الصافي") }}</th>
							<th class="px-3 py-2 text-start font-semibold">{{ __("الحالة") }}</th>
						</tr>
					</thead>
					<tbody class="divide-y divide-slate-100">
						<tr
							v-for="row in payrollRows"
							:key="row.name"
							class="cursor-pointer hover:bg-slate-50"
							@click="router.push({ name: 'EmployeePayrollEntry', params: { id: row.name } })"
						>
							<td class="px-3 py-2 font-semibold">{{ formatPeriod(String(row.period).slice(0, 7)) }}</td>
							<td class="px-3 py-2 text-end tabular-nums">{{ formatMoney(row.base_amount) }}</td>
							<td class="hidden px-3 py-2 text-end tabular-nums text-emerald-600 sm:table-cell">{{ formatMoney(row.total_earnings) }}</td>
							<td class="hidden px-3 py-2 text-end tabular-nums text-red-600 sm:table-cell">{{ formatMoney(row.total_deductions) }}</td>
							<td class="hidden px-3 py-2 text-end tabular-nums text-amber-600 sm:table-cell">{{ formatMoney(row.total_advances) }}</td>
							<td class="px-3 py-2 text-end font-bold tabular-nums">{{ formatMoney(row.net_amount) }}</td>
							<td class="px-3 py-2"><StatusBadge :status="row.status" :map="PAYROLL_STATUS" /></td>
						</tr>
					</tbody>
				</table>
			</section>
		</template>

		<AdvanceDialog v-model="advanceOpen" :employee="employeeId" :employees="selfOption" :company="emp?.company" lock-employee @saved="onAdvanceSaved" />
		<AttendanceDialog v-model="attendanceOpen" :record="attendanceRecord" :employees="selfOption" lock-employee @saved="onAttendanceSaved" />
		<LeaveDialog v-model="leaveOpen" :record="leaveRecord" :employees="selfOption" lock-employee @saved="onLeaveChanged" />
	</div>
</template>

<script setup>
import { computed, defineComponent, h, onMounted, ref, watch } from "vue"
import { useRoute, useRouter } from "vue-router"
import { Button } from "frappe-ui"
import AdvanceDialog from "@/components/employees/AdvanceDialog.vue"
import AdvancesTable from "@/components/employees/AdvancesTable.vue"
import AttendanceDialog from "@/components/employees/AttendanceDialog.vue"
import LeaveDialog from "@/components/employees/LeaveDialog.vue"
import LeavesTable from "@/components/employees/LeavesTable.vue"
import StatusBadge from "@/components/employees/StatusBadge.vue"
import SummaryTiles from "@/components/employees/SummaryTiles.vue"
import { useToast } from "@/composables/useToast"
import { call } from "@/utils/apiWrapper"
import {
	API, ATTENDANCE_STATUS, EMPLOYEE_STATUS, PAYROLL_STATUS, EMPLOYEE_TYPES, LEAVE_TYPES, PAY_TYPES, PAY_UNITS, SALARY_MODES,
	WEEK_DAYS, attendanceKey, currentPeriod, formatDate, formatHours, formatMoney, formatNumber, formatPeriod,
	formatShortDate, initials, weekdayName,
} from "@/utils/employees"

const TABS = [
	{ key: "data", label: "البيانات" },
	{ key: "attendance", label: "الدوام" },
	{ key: "leaves", label: "الإجازات" },
	{ key: "advances", label: "السلف" },
	{ key: "payroll", label: "الاستحقاقات" },
]

const InfoCard = defineComponent({
	props: { title: String, rows: Array },
	setup(props) {
		return () => h("div", { class: "rounded-2xl border border-slate-200 bg-white p-4 shadow-sm" }, [
			h("h3", { class: "mb-2 text-sm font-bold text-slate-800" }, props.title),
			h("dl", { class: "divide-y divide-slate-100" }, props.rows.map(([label, value]) =>
				h("div", { class: "flex items-center justify-between gap-3 py-2 text-sm" }, [
					h("dt", { class: "text-slate-500" }, label),
					h("dd", { class: "truncate text-end font-medium text-slate-900" }, value || value === 0 ? String(value) : "—"),
				])
			)),
		])
	},
})

const route = useRoute()
const router = useRouter()
const { showError } = useToast()

const emp = ref(null)
const summary = ref(null)
const loading = ref(false)
const tab = ref(TABS.some((t) => t.key === route.query.tab) ? route.query.tab : "data")
const period = ref(route.query.period || currentPeriod())

const month = ref(null)
const monthLoading = ref(false)
const leaves = ref([])
const leavesLoading = ref(false)

const advancesRows = ref([])
const advancesLoading = ref(false)
const advanceOpen = ref(false)
const payrollRows = ref([])
const payrollLoading = ref(false)

const attendanceOpen = ref(false)
const attendanceRecord = ref(null)
const leaveOpen = ref(false)
const leaveRecord = ref(null)

const employeeId = computed(() => route.params.id)
const currency = computed(() => summary.value?.currency || "")
const selfOption = computed(() => (emp.value ? [{ name: emp.value.name, employee_name: emp.value.employee_name }] : []))

const displayStatus = computed(() => {
	if (!emp.value) return ""
	if (emp.value.status === "Active" && summary.value?.on_leave_today) return "On Leave"
	return emp.value.status
})

const workDaysLabel = computed(() => {
	const codes = (emp.value?.bs_work_days || "").split(",").filter(Boolean)
	if (!codes.length) return __("افتراضي")
	return WEEK_DAYS.filter((d) => codes.includes(d.code)).map((d) => __(d.label)).join("، ")
})

const summaryTiles = computed(() => {
	const s = summary.value
	if (!s) return []
	const a = s.attendance
	const tiles = [
		{ label: __("الحضور"), value: `${a.present_days} / ${a.required_days}`, tone: "green" },
		{ label: __("الغياب"), value: __("{0} يوم", [a.absent_days]), tone: a.absent_days ? "red" : "" },
		{ label: __("الإجازة"), value: __("{0} يوم", [a.paid_leave_days + a.unpaid_leave_days]), tone: "sky" },
		{ label: __("الساعات"), value: formatNumber(a.worked_hours) },
		{ label: __("الإضافي"), value: __("{0} ساعة", [formatNumber(a.overtime_hours)]), tone: "green" },
		{ label: __("رصيد الإجازات"), value: __("{0} يوم", [s.leave_balance.remaining]) },
	]
	if (s.payroll) tiles.push({ label: __("الاستحقاق"), value: formatMoney(s.payroll.net_amount, currency.value), tone: "blue" })
	if (s.advances_remaining) tiles.push({ label: __("السلف المتبقية"), value: formatMoney(s.advances_remaining, currency.value), tone: "amber" })
	return tiles
})

const monthTiles = computed(() => {
	const st = month.value?.stats
	if (!st) return []
	return [
		{ label: __("حضور"), value: st.present_days, tone: "green" },
		{ label: __("غياب"), value: st.absent_days, tone: st.absent_days ? "red" : "" },
		{ label: __("إجازات"), value: st.paid_leave_days + st.unpaid_leave_days, tone: "sky" },
		{ label: __("تأخير (د)"), value: st.late_minutes, tone: st.late_minutes ? "amber" : "" },
		{ label: __("ساعات"), value: formatNumber(st.worked_hours) },
		{ label: __("إضافي"), value: formatNumber(st.overtime_hours), tone: "green" },
	]
})

// Hide days before joining / after leaving and empty future days for a cleaner list.
const visibleDays = computed(() => (month.value?.days || []).filter((d) => d.employed))

async function loadEmployee() {
	loading.value = true
	try {
		const [e, s] = await Promise.all([
			call(`${API}.employees.get_employee`, { name: employeeId.value }),
			call(`${API}.employees.get_employee_summary`, { name: employeeId.value }),
		])
		emp.value = e
		summary.value = s
	} catch (err) {
		showError(err?.message || __("فشل تحميل الموظف"))
	} finally {
		loading.value = false
	}
}

async function refreshSummary() {
	try {
		summary.value = await call(`${API}.employees.get_employee_summary`, { name: employeeId.value })
	} catch {
		// summary refresh is best-effort
	}
}

async function loadMonth() {
	monthLoading.value = true
	try {
		month.value = await call(`${API}.attendance.get_employee_month`, { employee: employeeId.value, period: period.value })
	} catch (err) {
		showError(err?.message || __("فشل تحميل الدوام"))
	} finally {
		monthLoading.value = false
	}
}

async function loadLeaves() {
	leavesLoading.value = true
	try {
		const res = await call(`${API}.leaves.get_leaves`, { company: emp.value.company, employee: employeeId.value })
		leaves.value = res.rows || []
	} catch (err) {
		showError(err?.message || __("فشل تحميل الإجازات"))
	} finally {
		leavesLoading.value = false
	}
}

async function loadAdvances() {
	advancesLoading.value = true
	try {
		const res = await call(`${API}.advances.get_advances`, { company: emp.value.company, employee: employeeId.value })
		advancesRows.value = res.rows || []
	} catch (err) {
		showError(err?.message || __("فشل تحميل السلف"))
	} finally {
		advancesLoading.value = false
	}
}

async function loadPayroll() {
	payrollLoading.value = true
	try {
		payrollRows.value = await call(`${API}.payroll.get_employee_entries`, { employee: employeeId.value })
	} catch (err) {
		showError(err?.message || __("فشل تحميل الاستحقاقات"))
	} finally {
		payrollLoading.value = false
	}
}

function loadTab() {
	if (!emp.value) return
	if (tab.value === "attendance") loadMonth()
	else if (tab.value === "leaves") loadLeaves()
	else if (tab.value === "advances") loadAdvances()
	else if (tab.value === "payroll") loadPayroll()
}

function onAdvanceSaved() {
	loadAdvances()
	refreshSummary()
}

function openAttendance(day = null) {
	if (day?.source === "Leave") {
		showError(__("هذا اليوم مرتبط بإجازة معتمدة — عدّلها من تبويب الإجازات"))
		return
	}
	attendanceRecord.value = day
		? { ...day, employee: employeeId.value, attendance_date: day.date, name: day.derived ? "" : day.name, status: day.derived ? "Present" : day.status }
		: { employee: employeeId.value }
	attendanceOpen.value = true
}

function openLeave(row = null) {
	leaveRecord.value = row ? { ...row } : { employee: employeeId.value }
	leaveOpen.value = true
}

function onAttendanceSaved() {
	loadMonth()
	refreshSummary()
}

function onLeaveChanged() {
	loadLeaves()
	refreshSummary()
}

watch(tab, (t) => {
	router.replace({ query: { ...route.query, tab: t } })
	loadTab()
})
watch(period, () => {
	router.replace({ query: { ...route.query, period: period.value } })
	loadMonth()
})
watch(employeeId, async (id) => {
	if (!id) return
	await loadEmployee()
	loadTab()
})

onMounted(async () => {
	await loadEmployee()
	loadTab()
})
</script>
