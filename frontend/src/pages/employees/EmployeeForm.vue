<template>
	<div class="flex w-full flex-col gap-4">
		<EmployeesHeader
			:title="isEdit ? __('تعديل موظف') : __('موظف جديد')"
			:subtitle="isEdit ? form.employee_name : __('الحقول المطلوبة: الاسم وتاريخ بدء العمل وطريقة الأجر')"
			:show-company="!isEdit"
		>
			<template #actions>
				<button type="button" class="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 hover:bg-slate-50" @click="goBack">
					{{ __("إلغاء") }}
				</button>
				<Button variant="solid" :loading="saving" @click="save">{{ __("حفظ") }}</Button>
			</template>
		</EmployeesHeader>

		<div v-if="loading" class="py-12 text-center text-sm text-slate-400">{{ __("جاري التحميل...") }}</div>

		<template v-else>
			<!-- Personal -->
			<FormSection :title="__('معلومات الموظف')" open>
				<div class="flex flex-col gap-4 sm:flex-row">
					<div class="flex flex-col items-center gap-2">
						<img v-if="form.image" :src="form.image" class="h-20 w-20 rounded-full object-cover ring-2 ring-slate-100" />
						<div v-else class="flex h-20 w-20 items-center justify-center rounded-full bg-indigo-50 text-xl font-bold text-indigo-600">
							{{ initials(form.employee_name) }}
						</div>
						<label class="cursor-pointer text-xs font-medium text-blue-600 hover:underline">
							{{ uploading ? __("جاري الرفع...") : __("تغيير الصورة") }}
							<input type="file" accept="image/*" class="hidden" @change="onImage" />
						</label>
					</div>
					<div class="grid flex-1 grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
						<Field :label="__('الاسم')" required><input v-model="form.employee_name" class="input" /></Field>
						<Field :label="__('رقم الموظف')" :help="isEdit ? form.name : __('يُولَّد تلقائيًا إن تُرك فارغًا')">
							<input v-model="form.employee_number" class="input" />
						</Field>
						<Field :label="__('رقم الهاتف')"><input v-model="form.cell_number" class="input" dir="ltr" /></Field>
						<Field :label="__('رقم الهوية')"><input v-model="form.bs_national_id" class="input" dir="ltr" /></Field>
						<Field :label="__('تاريخ الميلاد')"><input v-model="form.date_of_birth" type="date" class="input" /></Field>
						<Field :label="__('الجنس')">
							<select v-model="form.gender" class="input">
								<option value="">—</option>
								<option v-for="g in lookups.genders" :key="g" :value="g">{{ GENDERS[g] || g }}</option>
							</select>
						</Field>
						<Field :label="__('العنوان')" class="sm:col-span-2 lg:col-span-3"><input v-model="form.current_address" class="input" /></Field>
					</div>
				</div>
			</FormSection>

			<!-- Work -->
			<FormSection :title="__('معلومات العمل')" open>
				<div class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
					<Field :label="__('تاريخ بدء العمل')" required><input v-model="form.date_of_joining" type="date" class="input" /></Field>
					<Field :label="__('الوظيفة')">
						<input v-model="form.designation" list="bs-designations" class="input" />
						<datalist id="bs-designations"><option v-for="d in lookups.designations" :key="d" :value="d" /></datalist>
					</Field>
					<Field :label="__('القسم')">
						<select v-model="form.department" class="input">
							<option value="">—</option>
							<option v-for="d in lookups.departments" :key="d" :value="d">{{ d }}</option>
						</select>
					</Field>
					<Field :label="__('الفرع')">
						<select v-model="form.branch" class="input">
							<option value="">—</option>
							<option v-for="b in lookups.branches" :key="b" :value="b">{{ b }}</option>
						</select>
					</Field>
					<Field :label="__('المدير المباشر')">
						<select v-model="form.reports_to" class="input">
							<option value="">—</option>
							<option v-for="m in managers" :key="m.name" :value="m.name">{{ m.employee_name }}</option>
						</select>
					</Field>
					<Field :label="__('نوع الموظف')">
						<select v-model="form.bs_employee_type" class="input">
							<option v-for="(label, key) in EMPLOYEE_TYPES" :key="key" :value="key">{{ __(label) }}</option>
						</select>
					</Field>
				</div>
			</FormSection>

			<!-- Pay -->
			<FormSection :title="__('طريقة احتساب الأجر')" open>
				<div class="mb-3 grid grid-cols-3 gap-2 sm:max-w-md">
					<button
						v-for="(label, key) in PAY_TYPES"
						:key="key"
						type="button"
						class="rounded-lg border px-3 py-2 text-sm font-semibold transition-colors"
						:class="form.bs_pay_type === key ? 'border-blue-500 bg-blue-50 text-blue-700' : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-50'"
						@click="form.bs_pay_type = key"
					>
						{{ __(label) }}
					</button>
				</div>
				<div class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
					<Field v-if="form.bs_pay_type === 'Monthly'" :label="__('الراتب الشهري')" required>
						<input v-model.number="form.bs_monthly_salary" type="number" min="0" step="0.01" class="input" dir="ltr" />
					</Field>
					<Field v-if="form.bs_pay_type === 'Hourly'" :label="__('سعر الساعة')" required>
						<input v-model.number="form.bs_hourly_rate" type="number" min="0" step="0.01" class="input" dir="ltr" />
					</Field>
					<Field v-if="form.bs_pay_type === 'Daily'" :label="__('أجر اليوم')" required>
						<input v-model.number="form.bs_daily_rate" type="number" min="0" step="0.01" class="input" dir="ltr" />
					</Field>
					<Field :label="__('عدد ساعات اليوم الطبيعية')">
						<input v-model.number="form.bs_daily_hours" type="number" min="1" max="24" step="0.5" class="input" dir="ltr" />
					</Field>
				</div>
			</FormSection>

			<!-- Schedule -->
			<FormSection :title="__('إعدادات الدوام')" :open="!isEdit">
				<p class="mb-3 text-xs text-slate-500">{{ __("اتركها فارغة لاستخدام الدوام الافتراضي من إعدادات الموظفين") }}</p>
				<Field :label="__('أيام العمل')">
					<div class="flex flex-wrap gap-2">
						<button
							v-for="d in WEEK_DAYS"
							:key="d.code"
							type="button"
							class="rounded-lg border px-3 py-1.5 text-xs font-semibold transition-colors"
							:class="workDays.includes(d.code) ? 'border-blue-500 bg-blue-50 text-blue-700' : 'border-slate-200 bg-white text-slate-500 hover:bg-slate-50'"
							@click="toggleDay(d.code)"
						>
							{{ __(d.label) }}
						</button>
					</div>
				</Field>
				<div class="mt-3 grid grid-cols-2 gap-3 lg:grid-cols-5">
					<Field :label="__('ساعة البداية')"><input v-model="form.bs_shift_start" type="time" class="input" dir="ltr" /></Field>
					<Field :label="__('ساعة النهاية')"><input v-model="form.bs_shift_end" type="time" class="input" dir="ltr" /></Field>
					<Field :label="__('فترة السماح للتأخير (دقيقة)')"><input v-model.number="form.bs_grace_minutes" type="number" min="0" class="input" dir="ltr" /></Field>
					<Field :label="__('أيام الإجازة السنوية')"><input v-model.number="form.bs_annual_leave_days" type="number" min="0" class="input" dir="ltr" /></Field>
					<Field :label="__('قائمة العطل')">
						<select v-model="form.holiday_list" class="input">
							<option value="">{{ __("افتراضي الشركة") }}</option>
							<option v-for="h in lookups.holiday_lists" :key="h" :value="h">{{ h }}</option>
						</select>
					</Field>
				</div>
				<div class="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
					<Field
						:label="__('رمز تسجيل الدخول (PIN)')"
						:help="hasPin ? __('محدد — اتركه فارغًا للإبقاء عليه') : __('4–8 أرقام، يُستخدم في شاشة تسجيل الدخول إن كان مطلوبًا')"
					>
						<div class="flex items-center gap-2">
							<input
								v-model="form.bs_attendance_pin"
								type="password"
								inputmode="numeric"
								maxlength="8"
								autocomplete="new-password"
								class="input"
								dir="ltr"
								:placeholder="hasPin ? '••••' : ''"
							/>
							<button
								v-if="hasPin"
								type="button"
								class="whitespace-nowrap text-xs font-semibold"
								:class="clearPin ? 'text-rose-600' : 'text-slate-500 hover:text-rose-600'"
								@click="clearPin = !clearPin"
							>
								{{ clearPin ? __("سيُحذف ✓") : __("حذف الرمز") }}
							</button>
						</div>
					</Field>
				</div>
			</FormSection>

			<!-- Finance -->
			<FormSection :title="__('إعدادات مالية')">
				<div class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
					<Field :label="__('طريقة الدفع')">
						<select v-model="form.salary_mode" class="input">
							<option value="">—</option>
							<option v-for="(label, key) in SALARY_MODES" :key="key" :value="key">{{ __(label) }}</option>
						</select>
					</Field>
					<Field v-if="form.salary_mode === 'Bank'" :label="__('البنك')"><input v-model="form.bank_name" class="input" /></Field>
					<Field v-if="form.salary_mode === 'Bank'" :label="__('رقم الحساب')"><input v-model="form.bank_ac_no" class="input" dir="ltr" /></Field>
					<Field :label="__('مركز التكلفة')" :help="__('افتراضي الشركة إن تُرك فارغًا')">
						<select v-model="form.bs_cost_center" class="input">
							<option value="">—</option>
							<option v-for="c in lookups.cost_centers" :key="c" :value="c">{{ c }}</option>
						</select>
					</Field>
					<Field :label="__('حساب مصاريف الرواتب')" :help="__('افتراضي الإعدادات إن تُرك فارغًا')">
						<select v-model="form.bs_salary_expense_account" class="input">
							<option value="">—</option>
							<option v-for="a in lookups.expense_accounts" :key="a" :value="a">{{ a }}</option>
						</select>
					</Field>
				</div>
			</FormSection>

			<!-- Status -->
			<FormSection :title="__('حالة الموظف')" :open="isEdit">
				<div class="grid grid-cols-1 gap-3 sm:grid-cols-3">
					<Field :label="__('الحالة')">
						<select v-model="form.status" class="input">
							<option value="Active">{{ __("فعال") }}</option>
							<option value="Suspended">{{ __("موقوف مؤقتًا") }}</option>
							<option value="Left">{{ __("أنهى العمل") }}</option>
						</select>
					</Field>
					<template v-if="form.status === 'Left'">
						<Field :label="__('تاريخ انتهاء العمل')" required><input v-model="form.relieving_date" type="date" class="input" /></Field>
						<Field :label="__('سبب انتهاء العمل')"><input v-model="form.reason_for_leaving" class="input" /></Field>
					</template>
				</div>
				<p class="mt-2 text-xs text-slate-400">{{ __("حالة «في إجازة» تظهر تلقائيًا من الإجازات المعتمدة") }}</p>
			</FormSection>
		</template>
	</div>
</template>

<script setup>
import { computed, defineComponent, h, onMounted, ref } from "vue"
import { useRoute, useRouter } from "vue-router"
import { Button } from "frappe-ui"
import EmployeesHeader from "@/components/employees/EmployeesHeader.vue"
import { useEmployeeCompany } from "@/composables/useEmployeeCompany"
import { useToast } from "@/composables/useToast"
import { call } from "@/utils/apiWrapper"
import { uploadFile } from "@/utils/upload"
import { API, EMPLOYEE_TYPES, PAY_TYPES, SALARY_MODES, WEEK_DAYS, initials, todayISO } from "@/utils/employees"

const GENDERS = { Male: "ذكر", Female: "أنثى" }

// Small presentational helpers kept local to this form.
const Field = defineComponent({
	props: { label: String, help: String, required: Boolean },
	setup(props, { slots }) {
		return () => h("div", { class: "flex flex-col gap-1" }, [
			h("label", { class: "text-xs font-medium text-slate-700" }, [
				props.label,
				props.required ? h("span", { class: "text-red-500" }, " *") : null,
			]),
			slots.default?.(),
			props.help ? h("p", { class: "text-[11px] text-slate-400" }, props.help) : null,
		])
	},
})

const FormSection = defineComponent({
	props: { title: String, open: Boolean },
	setup(props, { slots }) {
		const expanded = ref(props.open)
		return () => h("section", { class: "rounded-2xl border border-slate-200 bg-white shadow-sm" }, [
			h("button", {
				type: "button",
				class: "flex w-full items-center justify-between px-4 py-3 text-start",
				onClick: () => { expanded.value = !expanded.value },
			}, [
				h("span", { class: "text-sm font-bold text-slate-800" }, props.title),
				h("svg", { class: ["h-4 w-4 text-slate-400 transition-transform", expanded.value ? "rotate-180" : ""], fill: "none", stroke: "currentColor", viewBox: "0 0 24 24" },
					[h("path", { "stroke-linecap": "round", "stroke-linejoin": "round", "stroke-width": "2", d: "M19 9l-7 7-7-7" })]),
			]),
			expanded.value ? h("div", { class: "border-t border-slate-100 px-4 pb-4 pt-3" }, slots.default?.()) : null,
		])
	},
})

const route = useRoute()
const router = useRouter()
const { showSuccess, showError } = useToast()
const { company, loadCompanies } = useEmployeeCompany()

const isEdit = computed(() => !!route.params.id)
const hasPin = ref(false)
const clearPin = ref(false)
const loading = ref(false)
const saving = ref(false)
const uploading = ref(false)
const lookups = ref({ genders: [], designations: [], departments: [], branches: [], managers: [], holiday_lists: [], cost_centers: [], expense_accounts: [] })

const form = ref({
	employee_name: "",
	employee_number: "",
	cell_number: "",
	bs_national_id: "",
	date_of_birth: "",
	gender: "",
	current_address: "",
	image: "",
	date_of_joining: todayISO(),
	designation: "",
	department: "",
	branch: "",
	reports_to: "",
	bs_employee_type: "Full Time",
	bs_pay_type: "Monthly",
	bs_monthly_salary: null,
	bs_hourly_rate: null,
	bs_daily_rate: null,
	bs_daily_hours: 8,
	bs_work_days: "",
	bs_shift_start: "",
	bs_shift_end: "",
	bs_grace_minutes: null,
	bs_annual_leave_days: null,
	bs_attendance_pin: "",
	holiday_list: "",
	bs_cost_center: "",
	bs_salary_expense_account: "",
	salary_mode: "Cash",
	bank_name: "",
	bank_ac_no: "",
	status: "Active",
	relieving_date: "",
	reason_for_leaving: "",
})

const managers = computed(() => lookups.value.managers.filter((m) => m.name !== route.params.id))
const workDays = computed(() => (form.value.bs_work_days || "").split(",").map((d) => d.trim()).filter(Boolean))

function toggleDay(code) {
	const set = new Set(workDays.value)
	set.has(code) ? set.delete(code) : set.add(code)
	form.value.bs_work_days = WEEK_DAYS.map((d) => d.code).filter((c) => set.has(c)).join(",")
}

async function onImage(e) {
	const file = e.target.files?.[0]
	if (!file) return
	uploading.value = true
	try {
		form.value.image = await uploadFile(file)
	} catch (err) {
		showError(err?.message || __("فشل رفع الصورة"))
	} finally {
		uploading.value = false
		e.target.value = ""
	}
}

function validate() {
	const f = form.value
	if (!f.employee_name?.trim()) return __("اسم الموظف مطلوب")
	if (!f.date_of_joining) return __("تاريخ بدء العمل مطلوب")
	const rateField = { Monthly: "bs_monthly_salary", Hourly: "bs_hourly_rate", Daily: "bs_daily_rate" }[f.bs_pay_type]
	if (!(Number(f[rateField]) > 0)) return __("يرجى إدخال قيمة الأجر")
	if (f.status === "Left" && !f.relieving_date) return __("تاريخ انتهاء العمل مطلوب")
	return ""
}

async function save() {
	const error = validate()
	if (error) return showError(error)
	saving.value = true
	try {
		const payload = { ...form.value, company: company.value, clear_attendance_pin: clearPin.value ? 1 : 0 }
		if (isEdit.value) payload.name = route.params.id
		const res = await call(`${API}.employees.save_employee`, { data: JSON.stringify(payload) })
		showSuccess(__("تم حفظ الموظف"))
		router.replace({ name: "EmployeeDetail", params: { id: res.name } })
	} catch (e) {
		showError(e?.message || __("فشل حفظ الموظف"))
	} finally {
		saving.value = false
	}
}

function goBack() {
	if (isEdit.value) router.push({ name: "EmployeeDetail", params: { id: route.params.id } })
	else router.push({ name: "EmployeesList" })
}

onMounted(async () => {
	loading.value = true
	try {
		let targetCompany
		if (isEdit.value) {
			const data = await call(`${API}.employees.get_employee`, { name: route.params.id })
			hasPin.value = !!data.has_attendance_pin
			Object.keys(form.value).forEach((k) => {
				if (data[k] !== undefined && data[k] !== null) form.value[k] = data[k]
			})
			targetCompany = data.company
		} else {
			await loadCompanies()
			targetCompany = company.value
		}
		lookups.value = await call(`${API}.employees.get_lookups`, { company: targetCompany })
	} catch (e) {
		showError(e?.message || __("فشل تحميل البيانات"))
	} finally {
		loading.value = false
	}
})
</script>

<style scoped>
.input {
	@apply w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500;
}
</style>
