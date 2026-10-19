<template>
	<div class="flex w-full flex-col gap-4">
		<EmployeesHeader
			:title="__('الدوام')"
			:subtitle="__('من حضر، كم ساعة اشتغل، وهل عنده نقص أو إضافي')"
			icon="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
			gradient="from-emerald-500 to-teal-600 shadow-emerald-500/30"
			@company-change="reload"
		>
			<template #actions>
				<div class="flex rounded-lg border border-slate-200 bg-white p-0.5 text-sm">
					<button
						v-for="m in MODES"
						:key="m.key"
						type="button"
						class="rounded-md px-3 py-1.5 font-semibold"
						:class="mode === m.key ? 'bg-slate-900 text-white' : 'text-slate-600 hover:bg-slate-50'"
						@click="setMode(m.key)"
					>
						{{ __(m.label) }}
					</button>
				</div>
				<Button v-if="mode === 'daily'" variant="solid" @click="openDialog()">{{ __("+ تسجيل دوام") }}</Button>
			</template>
		</EmployeesHeader>

		<!-- Daily -->
		<template v-if="mode === 'daily'">
			<section class="bs-card flex flex-wrap items-center justify-between gap-3 p-3">
				<div class="flex items-center gap-1">
					<button type="button" class="nav-btn" @click="shiftDay(-1)">{{ __("أمس") }}</button>
					<button type="button" class="nav-btn" :class="{ 'bg-slate-100': date === todayISO() }" @click="date = todayISO()">{{ __("اليوم") }}</button>
					<button type="button" class="nav-btn" @click="shiftDay(1)">{{ __("غدًا") }}</button>
				</div>
				<p class="text-sm font-bold text-slate-800">{{ formatLongDate(date) }}</p>
				<input v-model="date" type="date" class="rounded-lg border border-slate-200 px-3 py-1.5 text-sm" />
			</section>

			<SummaryTiles :tiles="dailyTiles" :cols="5" />

			<section class="bs-card">
				<div class="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 p-3">
					<input
						v-model="search"
						type="text"
						:placeholder="__('بحث...')"
						class="w-48 rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs focus:bg-white focus:outline-none"
					/>
					<Button v-if="unmarkedCount" variant="subtle" :loading="bulkLoading" @click="markAllPresent">
						{{ __("تسجيل حضور للبقية ({0})", [unmarkedCount]) }}
					</Button>
				</div>
				<div v-if="loading" class="py-12 text-center text-sm text-slate-400">{{ __("جاري التحميل...") }}</div>
				<div v-else-if="!dailyRows.length" class="py-12 text-center text-sm text-slate-400">{{ __("لا يوجد موظفون") }}</div>
				<div v-else class="overflow-x-auto">
					<table class="w-full text-sm">
						<thead>
							<tr class="bg-slate-50 text-xs text-slate-600">
								<th class="px-3 py-2 text-start font-semibold">{{ __("الموظف") }}</th>
								<th class="px-3 py-2 text-center font-semibold">{{ __("الدخول") }}</th>
								<th class="px-3 py-2 text-center font-semibold">{{ __("الخروج") }}</th>
								<th class="px-3 py-2 text-center font-semibold">{{ __("الساعات") }}</th>
								<th class="hidden px-3 py-2 text-center font-semibold sm:table-cell">{{ __("تأخير") }}</th>
								<th class="hidden px-3 py-2 text-center font-semibold sm:table-cell">{{ __("إضافي") }}</th>
								<th class="px-3 py-2 text-start font-semibold">{{ __("الحالة") }}</th>
							</tr>
						</thead>
						<tbody class="divide-y divide-slate-100">
							<tr v-for="row in dailyRows" :key="row.employee" class="cursor-pointer hover:bg-slate-50" @click="openDialog(row)">
								<td class="px-3 py-2">
									<p class="font-semibold text-slate-900">{{ row.employee_name }}</p>
									<p class="text-[11px] text-slate-400">{{ row.designation || row.employee }}</p>
								</td>
								<template v-if="isQuick(row) && quick[row.employee]">
									<td class="px-2 py-1.5 text-center" @click.stop>
										<input v-model="quick[row.employee].in" type="time" class="bs-input bs-input-sm !w-[6.5rem] text-center" dir="ltr" />
									</td>
									<td class="px-2 py-1.5 text-center" @click.stop>
										<input v-model="quick[row.employee].out" type="time" class="bs-input bs-input-sm !w-[6.5rem] text-center" dir="ltr" />
									</td>
									<td class="px-3 py-2 text-center tabular-nums text-slate-400" dir="ltr">{{ quickHours(row) }}</td>
								</template>
								<template v-else>
									<td class="px-3 py-2 text-center tabular-nums" dir="ltr">{{ row.check_in || "—" }}</td>
									<td class="px-3 py-2 text-center tabular-nums" dir="ltr">
										<template v-if="row.check_out">{{ row.check_out }}</template>
										<span v-else-if="row.check_in" class="text-[11px] font-semibold text-emerald-600" dir="rtl">{{ __("داخل الآن") }}</span>
										<template v-else>—</template>
									</td>
									<td class="px-3 py-2 text-center tabular-nums" dir="ltr">{{ formatHours(row.working_hours) }}</td>
								</template>
								<td class="hidden px-3 py-2 text-center tabular-nums text-amber-600 sm:table-cell">{{ row.late_minutes ? __("{0} د", [row.late_minutes]) : "—" }}</td>
								<td class="hidden px-3 py-2 text-center tabular-nums text-emerald-600 sm:table-cell" dir="ltr">{{ formatHours(row.overtime_hours) }}</td>
								<td class="px-3 py-2" @click="isQuick(row) && $event.stopPropagation()">
									<div v-if="isQuick(row)" class="flex items-center gap-1.5">
										<button
											type="button"
											class="bs-btn bs-btn-success bs-btn-sm"
											:disabled="savingRow === row.employee"
											@click="quickPresent(row)"
										>
											{{ savingRow === row.employee ? "..." : __("حاضر") }}
										</button>
										<button
											type="button"
											class="bs-btn bs-btn-ghost bs-btn-sm !text-rose-600"
											:disabled="savingRow === row.employee"
											@click="quickAbsent(row)"
										>
											{{ __("غائب") }}
										</button>
									</div>
									<template v-else>
										<StatusBadge :status="attendanceKey(row)" :map="ATTENDANCE_STATUS" />
										<span v-if="row.status === 'On Leave' && row.leave_type" class="ms-1 text-[11px] text-slate-400">{{ __(LEAVE_TYPES[row.leave_type]) }}</span>
										<span v-if="row.source === 'Punch'" class="ms-1 text-[10px] text-slate-400" :title="__('مسجّل من شاشة الدخول')">⏱</span>
									</template>
								</td>
							</tr>
						</tbody>
					</table>
				</div>
			</section>
		</template>

		<!-- Check in / out (time clock) -->
		<PunchClock v-else-if="mode === 'punch'" :company="company" />

		<!-- Monthly -->
		<template v-else>
			<section class="bs-card flex flex-wrap items-center justify-between gap-3 p-3">
				<p class="text-sm font-bold text-slate-800">{{ formatPeriod(period) }}</p>
				<input v-model="period" type="month" class="rounded-lg border border-slate-200 px-3 py-1.5 text-sm" />
			</section>
			<section class="bs-card">
				<div v-if="loading" class="py-12 text-center text-sm text-slate-400">{{ __("جاري التحميل...") }}</div>
				<div v-else-if="!monthlyRows.length" class="py-12 text-center text-sm text-slate-400">{{ __("لا توجد بيانات") }}</div>
				<div v-else class="overflow-x-auto">
					<table class="w-full text-sm">
						<thead>
							<tr class="bg-slate-50 text-xs text-slate-600">
								<th class="px-3 py-2 text-start font-semibold">{{ __("الموظف") }}</th>
								<th class="px-3 py-2 text-center font-semibold">{{ __("حضور") }}</th>
								<th class="px-3 py-2 text-center font-semibold">{{ __("غياب") }}</th>
								<th class="px-3 py-2 text-center font-semibold">{{ __("إجازات") }}</th>
								<th class="hidden px-3 py-2 text-center font-semibold sm:table-cell">{{ __("تأخير") }}</th>
								<th class="px-3 py-2 text-center font-semibold">{{ __("ساعات") }}</th>
								<th class="px-3 py-2 text-center font-semibold">{{ __("إضافي") }}</th>
							</tr>
						</thead>
						<tbody class="divide-y divide-slate-100">
							<tr
								v-for="row in monthlyRows"
								:key="row.employee"
								class="cursor-pointer hover:bg-slate-50"
								@click="router.push({ name: 'EmployeeDetail', params: { id: row.employee }, query: { tab: 'attendance', period } })"
							>
								<td class="px-3 py-2">
									<p class="font-semibold text-slate-900">{{ row.employee_name }}</p>
									<p class="text-[11px] text-slate-400">{{ row.designation || row.employee }}</p>
								</td>
								<td class="px-3 py-2 text-center tabular-nums">
									{{ row.present_days }}<span class="text-[11px] text-slate-400"> / {{ row.required_days }}</span>
								</td>
								<td class="px-3 py-2 text-center tabular-nums" :class="row.absent_days ? 'font-semibold text-red-600' : ''">{{ row.absent_days }}</td>
								<td class="px-3 py-2 text-center tabular-nums">{{ row.paid_leave_days + row.unpaid_leave_days }}</td>
								<td class="hidden px-3 py-2 text-center tabular-nums text-amber-600 sm:table-cell">{{ row.late_minutes ? __("{0} د", [row.late_minutes]) : "—" }}</td>
								<td class="px-3 py-2 text-center tabular-nums" dir="ltr">{{ formatNumber(row.worked_hours) }}</td>
								<td class="px-3 py-2 text-center tabular-nums text-emerald-600" dir="ltr">{{ formatNumber(row.overtime_hours) }}</td>
							</tr>
						</tbody>
					</table>
				</div>
			</section>
		</template>

		<AttendanceDialog v-model="dialogOpen" :record="dialogRecord" :employees="employeeOptions" :lock-employee="!!dialogRecord?.employee" @saved="loadDaily" />
	</div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from "vue"
import { useRoute, useRouter } from "vue-router"
import { Button } from "frappe-ui"
import AttendanceDialog from "@/components/employees/AttendanceDialog.vue"
import PunchClock from "@/components/employees/PunchClock.vue"
import EmployeesHeader from "@/components/employees/EmployeesHeader.vue"
import StatusBadge from "@/components/employees/StatusBadge.vue"
import SummaryTiles from "@/components/employees/SummaryTiles.vue"
import { useEmployeeCompany } from "@/composables/useEmployeeCompany"
import { useToast } from "@/composables/useToast"
import { call } from "@/utils/apiWrapper"
import {
	API, ATTENDANCE_STATUS, LEAVE_TYPES, addDays, attendanceKey, currentPeriod, formatHours,
	formatLongDate, formatNumber, formatPeriod, todayISO,
} from "@/utils/employees"

const MODES = [
	{ key: "daily", label: "يومي" },
	{ key: "monthly", label: "شهري" },
	{ key: "punch", label: "تسجيل الدخول" },
]

const route = useRoute()
const router = useRouter()
const { showSuccess, showError } = useToast()
const { company, loadCompanies } = useEmployeeCompany()

const mode = ref(MODES.some((m) => m.key === route.query.view) ? route.query.view : "daily")
const date = ref(route.query.date || todayISO())
const period = ref(route.query.period || currentPeriod())
const loading = ref(false)
const bulkLoading = ref(false)
const search = ref("")
const daily = ref({ summary: {}, rows: [] })
const monthlyRows = ref([])

const dialogOpen = ref(false)
const dialogRecord = ref(null)

// Quick entry: unmarked work days get editable shift times + a one-click «حاضر».
const quick = reactive({})
const savingRow = ref("")

function isQuick(row) {
	return row.is_work_day && row.source !== "Leave" && (!row.status || row.derived)
}

function syncQuick() {
	for (const row of daily.value.rows) {
		if (!isQuick(row)) continue
		const q = quick[row.employee]
		if (!q) {
			quick[row.employee] = { in: row.shift_start || "", out: row.shift_end || "" }
		} else if (!q.in && !q.out) {
			// untouched and still empty → take the employee's shift (e.g. after it was edited)
			q.in = row.shift_start || ""
			q.out = row.shift_end || ""
		}
	}
}

function quickHours(row) {
	const q = quick[row.employee]
	const toMin = (t) => {
		if (!t) return null
		const [h, m] = t.split(":").map(Number)
		return h * 60 + m
	}
	const a = toMin(q?.in)
	let b = toMin(q?.out)
	if (a === null || b === null) return "—"
	if (b < a) b += 24 * 60
	return formatHours((b - a) / 60)
}

async function saveQuick(row, payload, message) {
	savingRow.value = row.employee
	try {
		await call(`${API}.attendance.save_attendance`, {
			data: JSON.stringify({ employee: row.employee, attendance_date: date.value, ...payload }),
		})
		delete quick[row.employee]
		showSuccess(message)
		await loadDaily()
	} catch (e) {
		showError(e?.message || __("فشل التسجيل"))
	} finally {
		savingRow.value = ""
	}
}

function quickPresent(row) {
	const q = quick[row.employee] || {}
	if (!q.in) return showError(__("أدخل وقت الدخول"))
	saveQuick(row, { status: "Present", check_in: q.in, check_out: q.out || null }, __("تم تسجيل حضور {0}", [row.employee_name]))
}

function quickAbsent(row) {
	saveQuick(row, { status: "Absent" }, __("تم تسجيل غياب {0}", [row.employee_name]))
}

const employeeOptions = computed(() => daily.value.rows.map((r) => ({ name: r.employee, employee_name: r.employee_name, designation: r.designation })))

const dailyRows = computed(() => {
	const q = search.value.trim().toLowerCase()
	if (!q) return daily.value.rows
	return daily.value.rows.filter((r) => (r.employee_name || "").toLowerCase().includes(q))
})

const unmarkedCount = computed(() => daily.value.rows.filter((r) => r.is_work_day && (!r.status || (r.derived && r.status === "Absent"))).length)

const dailyTiles = computed(() => {
	const s = daily.value.summary || {}
	return [
		{ label: __("الموظفون"), value: s.total || 0 },
		{ label: __("حاضرون"), value: s.present || 0, tone: "green" },
		{ label: __("غائبون"), value: s.absent || 0, tone: "red" },
		{ label: __("إجازة"), value: s.on_leave || 0, tone: "sky" },
		{ label: __("متأخرون"), value: s.late || 0, tone: "amber" },
	]
})

function setMode(m) {
	mode.value = m
}

function shiftDay(n) {
	date.value = addDays(date.value, n)
}

function openDialog(row = null) {
	if (row && row.source === "Leave") {
		showError(__("هذا اليوم مرتبط بإجازة معتمدة — عدّلها من قسم الإجازات"))
		return
	}
	dialogRecord.value = row
		? { ...row, name: row.derived ? "" : row.name, attendance_date: date.value, status: row.derived ? "Present" : row.status }
		: { attendance_date: date.value }
	dialogOpen.value = true
}

async function loadDaily() {
	if (!company.value) return
	loading.value = true
	try {
		daily.value = await call(`${API}.attendance.get_daily`, { company: company.value, date: date.value })
		syncQuick()
	} catch (e) {
		showError(e?.message || __("فشل تحميل الدوام"))
	} finally {
		loading.value = false
	}
}

async function loadMonthly() {
	if (!company.value) return
	loading.value = true
	try {
		const res = await call(`${API}.attendance.get_monthly`, { company: company.value, period: period.value })
		monthlyRows.value = res.rows || []
	} catch (e) {
		showError(e?.message || __("فشل تحميل الدوام"))
	} finally {
		loading.value = false
	}
}

async function markAllPresent() {
	const employees = daily.value.rows
		.filter((r) => r.is_work_day && (!r.status || (r.derived && r.status === "Absent")))
		.map((r) => r.employee)
	if (!confirm(__("تسجيل حضور بدوام كامل لـ {0} موظف؟", [employees.length]))) return
	bulkLoading.value = true
	try {
		const res = await call(`${API}.attendance.mark_present_bulk`, {
			company: company.value, date: date.value, employees: JSON.stringify(employees),
		})
		showSuccess(__("تم تسجيل حضور {0} موظف", [res.created]))
		loadDaily()
	} catch (e) {
		showError(e?.message || __("فشل التسجيل"))
	} finally {
		bulkLoading.value = false
	}
}

function reload() {
	if (mode.value === "daily") loadDaily()
	else if (mode.value === "monthly") loadMonthly()
	// the punch tab loads itself
}

watch(date, () => {
	Object.keys(quick).forEach((k) => delete quick[k])
})

watch([mode, date, period], () => {
	const extra = mode.value === "daily" ? { date: date.value } : mode.value === "monthly" ? { period: period.value } : {}
	router.replace({ query: { view: mode.value, ...extra } })
	reload()
})

onMounted(async () => {
	try {
		await loadCompanies()
	} catch (e) {
		showError(e?.message || __("فشل تحميل الشركات"))
	}
	reload()
})
</script>

<style scoped>
.nav-btn {
	@apply rounded-lg px-3 py-1.5 text-sm font-semibold text-slate-700 hover:bg-slate-100;
}
</style>
