<template>
	<div class="flex w-full flex-col gap-4">
		<div v-if="loading && !entry" class="py-12 text-center text-sm text-slate-400">{{ __("جاري التحميل...") }}</div>

		<template v-else-if="entry">
			<!-- Header -->
			<section class="bs-card flex flex-wrap items-center justify-between gap-3 p-4">
				<div class="min-w-0">
					<RouterLink :to="{ name: 'EmployeePayroll', query: { period: entry.period_label } }" class="text-xs text-blue-600 hover:underline">
						← {{ __("استحقاقات {0}", [formatPeriod(entry.period_label)]) }}
					</RouterLink>
					<div class="mt-1 flex flex-wrap items-center gap-2">
						<RouterLink :to="{ name: 'EmployeeDetail', params: { id: entry.employee } }" class="truncate text-lg font-bold text-slate-900 hover:text-blue-700">
							{{ entry.employee_name }}
						</RouterLink>
						<StatusBadge :status="entry.status" :map="PAYROLL_STATUS" />
					</div>
					<p class="text-sm text-slate-500">{{ formatPeriod(entry.period_label) }}</p>
				</div>
				<div class="flex flex-wrap gap-2">
					<template v-if="isDraft">
						<Button variant="subtle" theme="red" :loading="busy === 'delete'" @click="remove">{{ __("حذف") }}</Button>
						<Button variant="subtle" :loading="busy === 'recalc'" @click="run('recalc', 'recalculate')">{{ __("إعادة حساب") }}</Button>
						<Button variant="solid" :loading="busy === 'approve'" @click="approve">{{ __("اعتماد") }}</Button>
					</template>
					<template v-else-if="entry.status === 'Approved'">
						<Button variant="subtle" :loading="busy === 'revert'" @click="revert">{{ __("إرجاع لمسودة") }}</Button>
						<Button variant="solid" theme="green" @click="payOpen = true">{{ __("تسجيل كمدفوع") }}</Button>
					</template>
					<Button v-else variant="subtle" :loading="busy === 'unpay'" @click="unpay">{{ __("إلغاء الدفع") }}</Button>
				</div>
			</section>

			<div class="grid grid-cols-1 gap-4 lg:grid-cols-3">
				<!-- Left column: breakdown -->
				<div class="flex flex-col gap-4 lg:col-span-2">
					<!-- Base -->
					<section class="bs-card p-4">
						<div class="flex items-center justify-between">
							<h2 class="text-sm font-bold text-slate-800">{{ __("الأساسي") }}</h2>
							<p class="text-lg font-bold tabular-nums">{{ formatMoney(entry.base_amount, entry.currency) }}</p>
						</div>
						<p class="mt-1 text-xs text-slate-500" dir="rtl">{{ baseFormula }}</p>
					</section>

					<LinesCard
						:title="__('الإضافات')"
						tone="green"
						sign="+"
						:lines="earnings"
						:total="entry.total_earnings"
						:editable="isDraft"
						:add-label="__('+ إضافة استحقاق')"
						@add="openLine('Earning')"
						@remove="removeLine"
					/>
					<LinesCard
						:title="__('الخصومات')"
						tone="red"
						sign="-"
						:lines="deductions"
						:total="entry.total_deductions"
						:editable="isDraft"
						:add-label="__('+ إضافة خصم')"
						@add="openLine('Deduction')"
						@remove="removeLine"
					/>
					<LinesCard
						:title="__('السلف')"
						tone="amber"
						sign="-"
						:lines="advances"
						:total="entry.total_advances"
						:empty-text="__('لا توجد أقساط سلف مستحقة هذا الشهر')"
					/>

					<!-- Result -->
					<section class="rounded-2xl border-2 border-slate-900 bg-white p-4 shadow-sm">
						<dl class="space-y-1.5 text-sm tabular-nums">
							<div class="flex justify-between"><dt class="text-slate-600">{{ __("الأساسي") }}</dt><dd>{{ formatMoney(entry.base_amount) }}</dd></div>
							<div class="flex justify-between"><dt class="text-slate-600">{{ __("الإضافات") }}</dt><dd class="text-emerald-600">+{{ formatMoney(entry.total_earnings) }}</dd></div>
							<div class="flex justify-between"><dt class="text-slate-600">{{ __("الخصومات") }}</dt><dd class="text-red-600">-{{ formatMoney(entry.total_deductions) }}</dd></div>
							<div class="flex justify-between"><dt class="text-slate-600">{{ __("السلف") }}</dt><dd class="text-amber-600">-{{ formatMoney(entry.total_advances) }}</dd></div>
						</dl>
						<div class="mt-3 flex items-center justify-between border-t border-slate-200 pt-3">
							<span class="text-base font-bold text-slate-900">{{ __("صافي الاستحقاق") }}</span>
							<span class="text-2xl font-bold tabular-nums text-slate-900">{{ formatMoney(entry.net_amount, entry.currency) }}</span>
						</div>
					</section>
				</div>

				<!-- Right column: context -->
				<div class="flex flex-col gap-4">
					<section class="bs-card p-4">
						<h2 class="mb-2 text-sm font-bold text-slate-800">{{ __("معلومات الحساب") }}</h2>
						<dl class="divide-y divide-slate-100 text-sm">
							<Row :label="__('طريقة الأجر')" :value="__(PAY_TYPES[entry.pay_type])" />
							<Row v-if="entry.pay_type === 'Monthly'" :label="__('الراتب الشهري')" :value="formatMoney(entry.monthly_salary, entry.currency)" />
							<Row v-if="entry.pay_type === 'Hourly'" :label="__('سعر الساعة')" :value="formatMoney(entry.hourly_rate, entry.currency)" />
							<Row v-if="entry.pay_type === 'Daily'" :label="__('أجر اليوم')" :value="formatMoney(entry.daily_rate, entry.currency)" />
							<Row :label="__('أجر اليوم المحسوب')" :value="formatMoney(entry.day_rate)" />
							<Row :label="__('أجر الساعة المحسوب')" :value="formatMoney(entry.hour_rate)" />
						</dl>
					</section>
					<section class="bs-card p-4">
						<div class="mb-2 flex items-center justify-between">
							<h2 class="text-sm font-bold text-slate-800">{{ __("بيانات الدوام") }}</h2>
							<RouterLink
								:to="{ name: 'EmployeeDetail', params: { id: entry.employee }, query: { tab: 'attendance', period: entry.period_label } }"
								class="text-xs text-blue-600 hover:underline"
							>{{ __("عرض الأيام") }}</RouterLink>
						</div>
						<dl class="divide-y divide-slate-100 text-sm">
							<Row :label="__('أيام العمل المطلوبة')" :value="entry.required_days" />
							<Row :label="__('أيام الحضور')" :value="entry.present_days" />
							<Row :label="__('غياب')" :value="entry.absent_days" :tone="entry.absent_days ? 'text-red-600' : ''" />
							<Row :label="__('إجازة مدفوعة')" :value="entry.paid_leave_days" />
							<Row :label="__('إجازة بدون راتب')" :value="entry.unpaid_leave_days" :tone="entry.unpaid_leave_days ? 'text-amber-600' : ''" />
							<Row :label="__('تأخير')" :value="__('{0} دقيقة', [entry.late_minutes])" />
							<Row :label="__('ساعات العمل')" :value="formatNumber(entry.worked_hours)" />
							<Row :label="__('ساعات إضافية')" :value="formatNumber(entry.overtime_hours)" />
						</dl>
						<p v-if="isDraft" class="mt-2 text-[11px] text-slate-400">{{ __("عدّلت الدوام؟ اضغط «إعادة حساب» لتحديث الأرقام") }}</p>
					</section>
					<section v-if="entry.accrual_journal_entry || entry.payment_journal_entry" class="bs-card p-4">
						<h2 class="mb-2 text-sm font-bold text-slate-800">{{ __("القيود المحاسبية") }}</h2>
						<dl class="divide-y divide-slate-100 text-sm">
							<div v-if="entry.accrual_journal_entry" class="flex justify-between py-2">
								<dt class="text-slate-500">{{ __("قيد الاستحقاق") }}</dt>
								<dd><a :href="`/app/journal-entry/${entry.accrual_journal_entry}`" target="_blank" class="text-blue-600 hover:underline">{{ entry.accrual_journal_entry }}</a></dd>
							</div>
							<div v-if="entry.payment_journal_entry" class="flex justify-between py-2">
								<dt class="text-slate-500">{{ __("قيد الدفع") }}</dt>
								<dd><a :href="`/app/journal-entry/${entry.payment_journal_entry}`" target="_blank" class="text-blue-600 hover:underline">{{ entry.payment_journal_entry }}</a></dd>
							</div>
							<Row v-if="entry.paid_date" :label="__('تاريخ الدفع')" :value="`${formatDate(entry.paid_date)} — ${entry.mode_of_payment || ''}`" />
						</dl>
					</section>
				</div>
			</div>
		</template>

		<!-- Add line -->
		<Dialog v-model="lineOpen" :options="{ title: lineForm.line_type === 'Earning' ? __('إضافة استحقاق') : __('إضافة خصم'), size: 'sm' }">
			<template #body-content>
				<div class="flex flex-col gap-3">
					<div class="flex flex-col gap-1">
						<label class="text-xs font-medium text-slate-700">{{ __("النوع") }}</label>
						<select v-model="lineForm.component" class="input">
							<option v-for="c in lineComponents" :key="c" :value="c">{{ __(COMPONENT_LABELS[c]) }}</option>
						</select>
					</div>
					<div class="flex flex-col gap-1">
						<label class="text-xs font-medium text-slate-700">{{ __("القيمة") }} <span class="text-red-500">*</span></label>
						<input v-model.number="lineForm.amount" type="number" min="0" step="0.01" class="input" dir="ltr" />
					</div>
					<div class="flex flex-col gap-1">
						<label class="text-xs font-medium text-slate-700">{{ __("ملاحظة") }}</label>
						<input v-model="lineForm.note" class="input" />
					</div>
				</div>
			</template>
			<template #actions>
				<div class="flex w-full justify-end gap-2">
					<Button variant="subtle" @click="lineOpen = false">{{ __("إلغاء") }}</Button>
					<Button variant="solid" :loading="busy === 'line'" @click="addLine">{{ __("إضافة") }}</Button>
				</div>
			</template>
		</Dialog>

		<!-- Pay -->
		<Dialog v-model="payOpen" :options="{ title: __('تسجيل كمدفوع'), size: 'sm' }">
			<template #body-content>
				<div v-if="entry" class="flex flex-col gap-3">
					<p class="rounded-lg bg-slate-50 p-3 text-center">
						<span class="block text-xs text-slate-500">{{ __("المبلغ") }}</span>
						<span class="text-xl font-bold tabular-nums">{{ formatMoney(entry.net_amount, entry.currency) }}</span>
					</p>
					<div class="flex flex-col gap-1">
						<label class="text-xs font-medium text-slate-700">{{ __("طريقة الدفع") }}</label>
						<select v-model="payForm.mode_of_payment" class="input">
							<option v-for="m in entry.modes_of_payment" :key="m" :value="m">{{ m }}</option>
						</select>
					</div>
					<div class="flex flex-col gap-1">
						<label class="text-xs font-medium text-slate-700">{{ __("تاريخ الدفع") }}</label>
						<input v-model="payForm.posting_date" type="date" class="input" />
					</div>
				</div>
			</template>
			<template #actions>
				<div class="flex w-full justify-end gap-2">
					<Button variant="subtle" @click="payOpen = false">{{ __("إلغاء") }}</Button>
					<Button variant="solid" theme="green" :loading="busy === 'pay'" @click="pay">{{ __("تأكيد الدفع") }}</Button>
				</div>
			</template>
		</Dialog>
	</div>
</template>

<script setup>
import { computed, defineComponent, h, onMounted, ref, watch } from "vue"
import { useRoute, useRouter } from "vue-router"
import { Button, Dialog } from "frappe-ui"
import StatusBadge from "@/components/employees/StatusBadge.vue"
import { useToast } from "@/composables/useToast"
import { call } from "@/utils/apiWrapper"
import {
	API, COMPONENT_LABELS, MANUAL_DEDUCTIONS, MANUAL_EARNINGS, PAYROLL_STATUS, PAY_TYPES,
	formatDate, formatMoney, formatNumber, formatPeriod, todayISO,
} from "@/utils/employees"

const Row = defineComponent({
	props: { label: String, value: [String, Number], tone: String },
	setup(props) {
		return () => h("div", { class: "flex items-center justify-between py-1.5" }, [
			h("dt", { class: "text-slate-500" }, props.label),
			h("dd", { class: ["font-medium tabular-nums text-slate-900", props.tone] }, props.value ?? "—"),
		])
	},
})

const LinesCard = defineComponent({
	props: { title: String, tone: String, sign: String, lines: Array, total: Number, editable: Boolean, addLabel: String, emptyText: String },
	emits: ["add", "remove"],
	setup(props, { emit }) {
		const toneCls = { green: "text-emerald-600", red: "text-red-600", amber: "text-amber-600" }
		return () => h("section", { class: "rounded-2xl border border-slate-200 bg-white shadow-sm" }, [
			h("div", { class: "flex items-center justify-between border-b border-slate-100 px-4 py-3" }, [
				h("h2", { class: "text-sm font-bold text-slate-800" }, props.title),
				h("span", { class: ["text-sm font-bold tabular-nums", toneCls[props.tone]] }, `${props.total ? props.sign : ""}${formatMoney(props.total)}`),
			]),
			props.lines.length
				? h("ul", { class: "divide-y divide-slate-100" }, props.lines.map((l) =>
					h("li", { class: "flex items-center gap-3 px-4 py-2 text-sm" }, [
						h("div", { class: "min-w-0 flex-1" }, [
							h("p", { class: "font-medium text-slate-800" }, [
								__(COMPONENT_LABELS[l.component] || l.component),
								l.is_auto ? h("span", { class: "ms-2 rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-semibold text-slate-500" }, __("تلقائي")) : null,
							]),
							lineHint(l) ? h("p", { class: "truncate text-[11px] text-slate-400" }, lineHint(l)) : null,
						]),
						h("span", { class: ["tabular-nums font-semibold", toneCls[props.tone]] }, `${props.sign}${formatMoney(l.amount)}`),
						props.editable && !l.is_auto
							? h("button", { type: "button", class: "rounded p-1 text-slate-400 hover:bg-red-50 hover:text-red-600", title: __("حذف"), onClick: () => emit("remove", l) }, "✕")
							: h("span", { class: "w-6" }),
					])
				))
				: h("p", { class: "px-4 py-4 text-center text-xs text-slate-400" }, props.emptyText || __("لا يوجد")),
			props.editable && props.addLabel
				? h("div", { class: "border-t border-slate-100 px-4 py-2" }, [
					h("button", { type: "button", class: "text-xs font-semibold text-blue-600 hover:underline", onClick: () => emit("add") }, props.addLabel),
				])
				: null,
		])
	},
})

function lineHint(l) {
	const qty = Number(l.quantity || 0)
	const parts = []
	if (qty) {
		if (l.component === "Overtime") parts.push(__("{0} ساعة", [formatNumber(qty)]))
		else if (["Absence", "Unpaid Leave"].includes(l.component)) parts.push(__("{0} يوم", [formatNumber(qty)]))
		else if (l.component === "Late") parts.push(__("{0} دقيقة", [formatNumber(qty)]))
	}
	if (l.note) parts.push(l.note)
	return parts.join(" — ")
}

const route = useRoute()
const router = useRouter()
const { showSuccess, showError } = useToast()

const entry = ref(null)
const loading = ref(false)
const busy = ref("")
const lineOpen = ref(false)
const lineForm = ref({ line_type: "Earning", component: "Bonus", amount: null, note: "" })
const payOpen = ref(false)
const payForm = ref({ mode_of_payment: "", posting_date: todayISO() })

const isDraft = computed(() => entry.value?.status === "Draft")
const earnings = computed(() => (entry.value?.lines || []).filter((l) => l.line_type === "Earning"))
const deductions = computed(() => (entry.value?.lines || []).filter((l) => l.line_type === "Deduction"))
const advances = computed(() => (entry.value?.lines || []).filter((l) => l.line_type === "Advance"))
const lineComponents = computed(() => (lineForm.value.line_type === "Earning" ? MANUAL_EARNINGS : MANUAL_DEDUCTIONS))

const baseFormula = computed(() => {
	const e = entry.value
	if (!e) return ""
	if (e.base_unit === "hour") return `${formatNumber(e.base_quantity)} ${__("ساعة")} × ${formatMoney(e.hour_rate)} = ${formatMoney(e.base_amount)}`
	if (e.base_unit === "day" && e.pay_type === "Daily") return `${formatNumber(e.base_quantity)} ${__("يوم")} × ${formatMoney(e.day_rate)} = ${formatMoney(e.base_amount)}`
	if (e.base_unit === "day") return __("راتب نسبي: {0} × {1} / {2} يوم عمل", [formatMoney(e.monthly_salary), e.base_quantity, e.month_working_days])
	return __("الراتب الشهري كاملًا")
})

watch(payOpen, (open) => {
	if (open && entry.value) payForm.value = { mode_of_payment: entry.value.default_mode_of_payment || entry.value.modes_of_payment?.[0] || "", posting_date: todayISO() }
})

async function load() {
	loading.value = true
	try {
		entry.value = await call(`${API}.payroll.get_entry`, { name: route.params.id })
	} catch (e) {
		showError(e?.message || __("فشل تحميل الاستحقاق"))
	} finally {
		loading.value = false
	}
}

async function run(key, method, params = {}, successMsg = "") {
	busy.value = key
	try {
		entry.value = await call(`${API}.payroll.${method}`, { name: entry.value.name, ...params })
		if (successMsg) showSuccess(successMsg)
		return true
	} catch (e) {
		showError(e?.message || __("فشلت العملية"))
		return false
	} finally {
		busy.value = ""
	}
}

function openLine(type) {
	lineForm.value = { line_type: type, component: type === "Earning" ? "Bonus" : "Administrative", amount: null, note: "" }
	lineOpen.value = true
}

async function addLine() {
	if (!(Number(lineForm.value.amount) > 0)) return showError(__("يرجى إدخال القيمة"))
	if (await run("line", "add_line", lineForm.value)) lineOpen.value = false
}

function removeLine(line) {
	if (!confirm(__("حذف هذا السطر؟"))) return
	run("line", "remove_line", { row_name: line.name })
}

function approve() {
	if (!confirm(__("اعتماد الاستحقاق؟ سيتم إنشاء قيد محاسبي وخصم أقساط السلف"))) return
	run("approve", "approve", {}, __("تم الاعتماد"))
}

function revert() {
	if (!confirm(__("إرجاع الاستحقاق لمسودة؟ سيُلغى القيد المحاسبي وأقساط السلف المرتبطة"))) return
	run("revert", "revert_to_draft", {}, __("تم الإرجاع لمسودة"))
}

async function pay() {
	if (!payForm.value.mode_of_payment) return showError(__("يرجى اختيار طريقة الدفع"))
	if (await run("pay", "mark_paid", payForm.value, __("تم تسجيل الدفع"))) payOpen.value = false
}

function unpay() {
	if (!confirm(__("إلغاء الدفع؟ سيُلغى قيد الدفع"))) return
	run("unpay", "cancel_payment", {}, __("تم إلغاء الدفع"))
}

async function remove() {
	if (!confirm(__("حذف الاستحقاق؟"))) return
	busy.value = "delete"
	try {
		const period = entry.value.period_label
		await call(`${API}.payroll.delete_entry`, { name: entry.value.name })
		router.replace({ name: "EmployeePayroll", query: { period } })
	} catch (e) {
		showError(e?.message || __("فشل الحذف"))
	} finally {
		busy.value = ""
	}
}

onMounted(load)
</script>

<style scoped>
.input {
	@apply w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500;
}
</style>
