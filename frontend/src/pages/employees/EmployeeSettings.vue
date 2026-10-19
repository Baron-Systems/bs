<template>
	<div class="flex w-full flex-col gap-4">
		<EmployeesHeader
			:title="__('إعدادات الموظفين')"
			:subtitle="__('قواعد احتساب الأجر والدوام الافتراضي والحسابات المحاسبية')"
			icon="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
			gradient="from-slate-500 to-slate-700 shadow-slate-500/30"
			@company-change="loadAccountOptions"
		>
			<template #actions>
				<Button variant="solid" :loading="saving" :disabled="loading" @click="save">{{ __("حفظ") }}</Button>
			</template>
		</EmployeesHeader>

		<div v-if="loading" class="py-12 text-center text-sm text-slate-400">{{ __("جاري التحميل...") }}</div>

		<template v-else>
			<section class="bs-card p-4">
				<h2 class="mb-1 text-sm font-bold text-slate-800">{{ __("قواعد الحساب") }}</h2>
				<p class="mb-3 text-xs text-slate-500">{{ __("تُستخدم في إنشاء الاستحقاقات تلقائيًا") }}</p>
				<div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
					<div class="flex flex-col gap-1">
						<label class="text-xs font-medium text-slate-700">{{ __("أساس احتساب أجر اليوم للموظف الشهري") }}</label>
						<select v-model="settings.day_rate_basis" class="input">
							<option value="Working Days">{{ __("الراتب ÷ أيام العمل الفعلية في الشهر") }}</option>
							<option value="30 Days">{{ __("الراتب ÷ 30") }}</option>
						</select>
					</div>
					<SettingField v-model="settings.overtime_multiplier" :label="__('معامل الساعة الإضافية')" :help="__('مثال: 1.25 تعني الساعة الإضافية = 125% من أجر الساعة')" type="number" :min="1" :step="0.05" />
					<label class="flex items-start gap-2 text-sm text-slate-700">
						<input v-model="settings.late_deduction_enabled" type="checkbox" class="mt-0.5 rounded border-slate-200" />
						<span>
							{{ __("خصم دقائق التأخير") }}
							<span class="block text-xs text-slate-400">{{ __("بعد فترة السماح، بقيمة أجر الدقيقة") }}</span>
						</span>
					</label>
					<label class="flex items-start gap-2 text-sm text-slate-700">
						<input v-model="settings.treat_missing_as_absent" type="checkbox" class="mt-0.5 rounded border-slate-200" />
						<span>
							{{ __("اعتبار يوم العمل بلا تسجيل غيابًا") }}
							<span class="block text-xs text-slate-400">{{ __("إن عُطّل، الغياب يُسجّل يدويًا فقط") }}</span>
						</span>
					</label>
				</div>
			</section>

			<section class="bs-card p-4">
				<h2 class="mb-1 text-sm font-bold text-slate-800">{{ __("الدوام الافتراضي") }}</h2>
				<p class="mb-3 text-xs text-slate-500">{{ __("يُطبَّق على كل موظف لم تُحدَّد له إعدادات دوام خاصة") }}</p>
				<div class="mb-4 flex flex-wrap gap-2">
					<button
						v-for="d in WEEK_DAYS"
						:key="d.code"
						type="button"
						class="rounded-lg border px-3 py-1.5 text-xs font-semibold"
						:class="workDays.includes(d.code) ? 'border-blue-500 bg-blue-50 text-blue-700' : 'border-slate-200 text-slate-500 hover:bg-slate-50'"
						@click="toggleDay(d.code)"
					>
						{{ __(d.label) }}
					</button>
				</div>
				<div class="grid grid-cols-2 gap-4 lg:grid-cols-5">
					<div class="flex flex-col gap-1">
						<label class="text-xs font-medium text-slate-700">{{ __("ساعة البداية") }}</label>
						<input v-model="settings.default_shift_start" type="time" class="input" dir="ltr" />
					</div>
					<div class="flex flex-col gap-1">
						<label class="text-xs font-medium text-slate-700">{{ __("ساعة النهاية") }}</label>
						<input v-model="settings.default_shift_end" type="time" class="input" dir="ltr" />
					</div>
					<SettingField v-model="settings.default_grace_minutes" :label="__('فترة السماح')" :suffix="__('دقيقة')" type="number" :min="0" />
					<SettingField v-model="settings.default_daily_hours" :label="__('ساعات اليوم')" type="number" :min="1" :max="24" :step="0.5" />
					<SettingField v-model="settings.default_annual_leave_days" :label="__('الإجازة السنوية')" :suffix="__('يوم')" type="number" :min="0" />
				</div>
			</section>

			<section class="bs-card p-4">
				<h2 class="mb-1 text-sm font-bold text-slate-800">{{ __("شاشة تسجيل الدخول والخروج") }}</h2>
				<p class="mb-3 text-xs text-slate-500">{{ __("الوقت يؤخذ من الخادم دائمًا وليس من جهاز المستخدم") }}</p>
				<div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
					<SettingField v-model="settings.punch_min_interval_minutes" :label="__('أقل مدة بين الدخول والخروج')" :suffix="__('دقيقة')" :help="__('يمنع التسجيل المكرر بالخطأ')" type="number" :min="0" />
					<SettingField v-model="settings.punch_early_window_minutes" :label="__('أقصى مدة للدخول قبل بداية الدوام')" :suffix="__('دقيقة')" :help="__('0 = بدون حد')" type="number" :min="0" />
					<label class="flex items-start gap-2 text-sm text-slate-700">
						<input v-model="settings.punch_require_pin" type="checkbox" class="mt-0.5 rounded border-slate-200" />
						<span>
							{{ __("طلب رمز (PIN) من الموظف") }}
							<span class="block text-xs text-slate-400">{{ __("يُحدَّد الرمز من ملف كل موظف") }}</span>
						</span>
					</label>
					<label class="flex items-start gap-2 text-sm text-slate-700">
						<input v-model="settings.punch_allow_day_off" type="checkbox" class="mt-0.5 rounded border-slate-200" />
						<span>
							{{ __("السماح بالتسجيل في يوم الراحة والعطل") }}
							<span class="block text-xs text-slate-400">{{ __("ساعات يوم الراحة تُحسب كلها إضافية") }}</span>
						</span>
					</label>
					<label class="flex items-start gap-2 text-sm text-slate-700">
						<input v-model="settings.count_early_arrival_as_overtime" type="checkbox" class="mt-0.5 rounded border-slate-200" />
						<span>
							{{ __("احتساب الحضور المبكر كساعات إضافية") }}
							<span class="block text-xs text-slate-400">{{ __("إن عُطّل، تبدأ الساعات من بداية الدوام") }}</span>
						</span>
					</label>
				</div>
			</section>

			<section class="bs-card p-4">
				<h2 class="mb-1 text-sm font-bold text-slate-800">{{ __("الحسابات المحاسبية — {0}", [company]) }}</h2>
				<div class="mb-3 flex flex-wrap items-center justify-between gap-2">
					<p class="text-xs text-slate-500">{{ __("تُستخدم في قيود الاستحقاقات والسلف") }}</p>
					<Button v-if="missingAccounts" variant="subtle" :loading="creatingAccounts" @click="createAccounts">
						{{ __("إنشاء الحسابات الافتراضية") }}
					</Button>
				</div>
				<div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
					<AccountSelect v-model="accountRow.salary_expense_account" :label="__('حساب مصاريف الرواتب')" :options="accountOptions.expense" />
					<AccountSelect v-model="accountRow.payroll_payable_account" :label="__('حساب رواتب مستحقة')" :options="accountOptions.liability" />
					<AccountSelect v-model="accountRow.employee_advance_account" :label="__('حساب سلف الموظفين')" :options="accountOptions.asset" />
					<AccountSelect v-model="accountRow.cost_center" :label="__('مركز التكلفة الافتراضي')" :options="accountOptions.cost_centers" />
					<AccountSelect v-model="accountRow.default_mode_of_payment" :label="__('طريقة الدفع الافتراضية')" :options="accountOptions.modes_of_payment" />
				</div>
			</section>
		</template>
	</div>
</template>

<script setup>
import { computed, defineComponent, h, onMounted, ref } from "vue"
import { Button } from "frappe-ui"
import EmployeesHeader from "@/components/employees/EmployeesHeader.vue"
import SettingField from "@/components/SettingField.vue"
import { useEmployeeCompany } from "@/composables/useEmployeeCompany"
import { useToast } from "@/composables/useToast"
import { call } from "@/utils/apiWrapper"
import { API, WEEK_DAYS } from "@/utils/employees"

const AccountSelect = defineComponent({
	props: { modelValue: String, label: String, options: Array },
	emits: ["update:modelValue"],
	setup(props, { emit }) {
		return () => h("div", { class: "flex flex-col gap-1" }, [
			h("label", { class: "text-xs font-medium text-slate-700" }, props.label),
			h("select", {
				class: "w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500",
				value: props.modelValue || "",
				onChange: (e) => emit("update:modelValue", e.target.value),
			}, [h("option", { value: "" }, "—"), ...(props.options || []).map((o) => h("option", { value: o }, o))]),
		])
	},
})

const { showSuccess, showError } = useToast()
const { company, loadCompanies } = useEmployeeCompany()

const loading = ref(false)
const saving = ref(false)
const settings = ref({ company_accounts: [] })
const accountOptions = ref({ expense: [], liability: [], asset: [], cost_centers: [], modes_of_payment: [] })

const ACCOUNT_KEYS = ["salary_expense_account", "payroll_payable_account", "employee_advance_account", "cost_center", "default_mode_of_payment"]

const EMPTY_ROW = Object.fromEntries(ACCOUNT_KEYS.map((k) => [k, ""]))
const accountRow = computed(() => settings.value.company_accounts.find((r) => r.company === company.value) || { ...EMPTY_ROW })

function ensureRow() {
	if (company.value && !settings.value.company_accounts.some((r) => r.company === company.value)) {
		settings.value.company_accounts.push({ company: company.value, ...EMPTY_ROW })
	}
}

const workDays = computed(() => (settings.value.default_work_days || "").split(",").map((d) => d.trim()).filter(Boolean))

function toggleDay(code) {
	const set = new Set(workDays.value)
	set.has(code) ? set.delete(code) : set.add(code)
	settings.value.default_work_days = WEEK_DAYS.map((d) => d.code).filter((c) => set.has(c)).join(",")
}

async function loadAccountOptions() {
	if (!company.value) return
	ensureRow()
	try {
		accountOptions.value = await call(`${API}.settings.get_account_options`, { company: company.value })
	} catch (e) {
		showError(e?.message || __("فشل تحميل الحسابات"))
	}
}

const creatingAccounts = ref(false)
const missingAccounts = computed(() => ["salary_expense_account", "payroll_payable_account", "employee_advance_account"].some((k) => !accountRow.value[k]))

async function createAccounts() {
	if (!confirm(__("إنشاء حسابات: رواتب وأجور، رواتب مستحقة الدفع، سلف الموظفين في دليل الحسابات لشركة {0}؟", [company.value]))) return
	creatingAccounts.value = true
	try {
		await call(`${API}.settings.create_default_accounts`, { company: company.value })
		const data = await call(`${API}.settings.get_employee_settings`)
		settings.value.company_accounts = data.company_accounts || []
		await loadAccountOptions()
		showSuccess(__("تم إنشاء الحسابات وربطها"))
	} catch (e) {
		showError(e?.message || __("فشل إنشاء الحسابات"))
	} finally {
		creatingAccounts.value = false
	}
}

async function save() {
	saving.value = true
	try {
		const data = {
			...settings.value,
			late_deduction_enabled: settings.value.late_deduction_enabled ? 1 : 0,
			treat_missing_as_absent: settings.value.treat_missing_as_absent ? 1 : 0,
			count_early_arrival_as_overtime: settings.value.count_early_arrival_as_overtime ? 1 : 0,
			punch_allow_day_off: settings.value.punch_allow_day_off ? 1 : 0,
			punch_require_pin: settings.value.punch_require_pin ? 1 : 0,
			company_accounts: settings.value.company_accounts.filter((r) => ACCOUNT_KEYS.some((k) => r[k])),
		}
		await call(`${API}.settings.save_employee_settings`, { data: JSON.stringify(data) })
		showSuccess(__("تم حفظ الإعدادات"))
	} catch (e) {
		showError(e?.message || __("فشل حفظ الإعدادات"))
	} finally {
		saving.value = false
	}
}

onMounted(async () => {
	loading.value = true
	try {
		await loadCompanies()
		const data = await call(`${API}.settings.get_employee_settings`)
		data.late_deduction_enabled = !!data.late_deduction_enabled
		data.treat_missing_as_absent = !!data.treat_missing_as_absent
		data.count_early_arrival_as_overtime = !!data.count_early_arrival_as_overtime
		data.punch_allow_day_off = !!data.punch_allow_day_off
		data.punch_require_pin = !!data.punch_require_pin
		data.company_accounts = data.company_accounts || []
		settings.value = data
		await loadAccountOptions()
	} catch (e) {
		showError(e?.message || __("فشل تحميل الإعدادات"))
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
