<template>
	<Dialog v-model="show" :options="{ title: record?.name ? __('تعديل دوام') : __('تسجيل دوام'), size: 'md' }">
		<template #body-content>
			<div class="flex flex-col gap-3">
				<div class="flex flex-col gap-1">
					<label class="text-xs font-medium text-slate-700">{{ __("الموظف") }} <span class="text-red-500">*</span></label>
					<EmployeePicker v-model="form.employee" :employees="employees" :disabled="lockEmployee" />
				</div>
				<div class="flex flex-col gap-1">
					<label class="text-xs font-medium text-slate-700">{{ __("التاريخ") }} <span class="text-red-500">*</span></label>
					<input v-model="form.attendance_date" type="date" class="input" :disabled="lockEmployee" />
				</div>
				<div class="flex flex-col gap-1">
					<label class="text-xs font-medium text-slate-700">{{ __("الحالة") }}</label>
					<div class="grid grid-cols-2 gap-2 sm:grid-cols-4">
						<button
							v-for="s in STATUSES"
							:key="s"
							type="button"
							class="rounded-lg border px-2 py-1.5 text-xs font-semibold"
							:class="form.status === s ? 'border-blue-500 bg-blue-50 text-blue-700' : 'border-slate-200 text-slate-600 hover:bg-slate-50'"
							@click="form.status = s"
						>
							{{ __(ATTENDANCE_STATUS[s].label) }}
						</button>
					</div>
					<p class="text-[11px] text-slate-400">{{ __("الإجازات تُسجّل من قسم الإجازات وتظهر هنا تلقائيًا") }}</p>
				</div>
				<div v-if="hasTimes" class="grid grid-cols-2 gap-3">
					<div class="flex flex-col gap-1">
						<label class="text-xs font-medium text-slate-700">{{ __("وقت الدخول") }}</label>
						<input v-model="form.check_in" type="time" class="input" dir="ltr" />
					</div>
					<div class="flex flex-col gap-1">
						<label class="text-xs font-medium text-slate-700">{{ __("وقت الخروج") }}</label>
						<input v-model="form.check_out" type="time" class="input" dir="ltr" />
					</div>
				</div>
				<p v-if="hasTimes && previewHours" class="rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-600">
					{{ __("ساعات العمل") }}: <b class="tabular-nums">{{ previewHours }}</b>
					<span class="text-slate-400"> — {{ __("التأخير والإضافي يُحسبان حسب دوام الموظف عند الحفظ") }}</span>
				</p>
				<div class="flex flex-col gap-1">
					<label class="text-xs font-medium text-slate-700">{{ __("ملاحظة") }}</label>
					<input v-model="form.note" class="input" />
				</div>
			</div>
		</template>
		<template #actions>
			<div class="flex w-full items-center gap-2">
				<Button v-if="record?.name" variant="subtle" theme="red" :loading="deleting" @click="remove">{{ __("حذف") }}</Button>
				<div class="flex-1" />
				<Button variant="subtle" @click="show = false">{{ __("إلغاء") }}</Button>
				<Button variant="solid" :loading="saving" @click="save">{{ __("حفظ") }}</Button>
			</div>
		</template>
	</Dialog>
</template>

<script setup>
import { computed, ref, watch } from "vue"
import { Button, Dialog } from "frappe-ui"
import EmployeePicker from "@/components/employees/EmployeePicker.vue"
import { useToast } from "@/composables/useToast"
import { call } from "@/utils/apiWrapper"
import { API, ATTENDANCE_STATUS, formatHours, todayISO } from "@/utils/employees"

const STATUSES = ["Present", "Absent", "Work Mission", "Day Off"]

const props = defineProps({
	modelValue: { type: Boolean, default: false },
	record: { type: Object, default: null }, // {name?, employee, attendance_date, status, check_in, check_out, note}
	employees: { type: Array, default: () => [] },
	lockEmployee: { type: Boolean, default: false },
})
const emit = defineEmits(["update:modelValue", "saved"])
const { showSuccess, showError } = useToast()

const show = computed({
	get: () => props.modelValue,
	set: (v) => emit("update:modelValue", v),
})

const blank = () => ({ name: "", employee: "", attendance_date: todayISO(), status: "Present", check_in: "", check_out: "", note: "" })
const form = ref(blank())
const saving = ref(false)
const deleting = ref(false)

watch(() => props.modelValue, (open) => {
	if (!open) return
	const r = props.record || {}
	form.value = {
		...blank(),
		...Object.fromEntries(Object.entries(r).filter(([k, v]) => k in blank() && v !== null && v !== undefined)),
	}
	if (!STATUSES.includes(form.value.status)) form.value.status = "Present"
	// Rows from the daily board already carry the shift; otherwise it is fetched below.
	if (r.shift_start && !form.value.check_in && !form.value.check_out) {
		form.value.check_in = r.shift_start
		form.value.check_out = r.shift_end || ""
	} else {
		fillShift()
	}
})

// New entries start with the employee's own shift (or the default schedule).
let shiftRequest = 0
async function fillShift() {
	const f = form.value
	if (!f.employee || !hasTimes.value || f.check_in || f.check_out) return
	const request = ++shiftRequest
	try {
		const shift = await call(`${API}.attendance.get_shift`, { employee: f.employee })
		// ignore late answers and anything the user typed meanwhile
		if (request !== shiftRequest || form.value.employee !== f.employee || form.value.check_in || form.value.check_out) return
		form.value.check_in = shift.shift_start || ""
		form.value.check_out = shift.shift_end || ""
	} catch {
		// times stay empty; the user can type them
	}
}

watch(() => form.value.employee, (emp, prev) => {
	if (!props.modelValue || !emp || emp === prev || form.value.name) return
	form.value.check_in = ""
	form.value.check_out = ""
	fillShift()
})
watch(() => form.value.status, () => {
	if (props.modelValue) fillShift()
})

const hasTimes = computed(() => ["Present", "Work Mission"].includes(form.value.status))

const previewHours = computed(() => {
	const toMin = (t) => {
		if (!t) return null
		const [h, m] = t.split(":").map(Number)
		return h * 60 + m
	}
	const a = toMin(form.value.check_in)
	let b = toMin(form.value.check_out)
	if (a === null || b === null) return ""
	if (b < a) b += 24 * 60
	return formatHours((b - a) / 60)
})

async function save() {
	if (!form.value.employee || !form.value.attendance_date) return showError(__("الموظف والتاريخ مطلوبان"))
	saving.value = true
	try {
		await call(`${API}.attendance.save_attendance`, { data: JSON.stringify(form.value) })
		showSuccess(__("تم حفظ الدوام"))
		show.value = false
		emit("saved")
	} catch (e) {
		showError(e?.message || __("فشل حفظ الدوام"))
	} finally {
		saving.value = false
	}
}

async function remove() {
	if (!confirm(__("حذف سجل الدوام؟"))) return
	deleting.value = true
	try {
		await call(`${API}.attendance.delete_attendance`, { name: props.record.name })
		show.value = false
		emit("saved")
	} catch (e) {
		showError(e?.message || __("فشل الحذف"))
	} finally {
		deleting.value = false
	}
}
</script>

<style scoped>
.input {
	@apply w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-slate-50;
}
</style>
