<template>
	<Dialog v-model="show" :options="{ title: __('سلفة جديدة'), size: 'md' }">
		<template #body-content>
			<div class="flex flex-col gap-3">
				<div class="flex flex-col gap-1">
					<label class="text-xs font-medium text-slate-700">{{ __("الموظف") }} <span class="text-red-500">*</span></label>
					<EmployeePicker v-model="form.employee" :employees="employees" :disabled="lockEmployee" />
				</div>
				<div class="grid grid-cols-2 gap-3">
					<div class="flex flex-col gap-1">
						<label class="text-xs font-medium text-slate-700">{{ __("التاريخ") }} <span class="text-red-500">*</span></label>
						<input v-model="form.posting_date" type="date" class="input" />
					</div>
					<div class="flex flex-col gap-1">
						<label class="text-xs font-medium text-slate-700">{{ __("قيمة السلفة") }} <span class="text-red-500">*</span></label>
						<input v-model.number="form.amount" type="number" min="0" step="0.01" class="input" dir="ltr" />
					</div>
				</div>
				<div class="flex flex-col gap-1">
					<label class="text-xs font-medium text-slate-700">{{ __("صُرفت من") }}</label>
					<select v-model="form.mode_of_payment" class="input">
						<option v-for="m in options.modes_of_payment" :key="m" :value="m">{{ m }}</option>
					</select>
				</div>
				<div class="flex flex-col gap-1">
					<label class="text-xs font-medium text-slate-700">{{ __("طريقة الاسترداد") }}</label>
					<div class="grid grid-cols-1 gap-2 sm:grid-cols-3">
						<button
							v-for="(label, key) in RECOVERY_METHODS"
							:key="key"
							type="button"
							class="rounded-lg border px-2 py-2 text-xs font-semibold"
							:class="form.recovery_method === key ? 'border-blue-500 bg-blue-50 text-blue-700' : 'border-slate-200 text-slate-600 hover:bg-slate-50'"
							@click="form.recovery_method = key"
						>
							{{ __(label) }}
						</button>
					</div>
				</div>
				<template v-if="form.recovery_method === 'Installments'">
					<div class="grid grid-cols-2 gap-3">
						<div class="flex flex-col gap-1">
							<label class="text-xs font-medium text-slate-700">{{ __("عدد الأقساط") }}</label>
							<input v-model.number="form.installments_count" type="number" min="1" class="input" dir="ltr" @input="byCount = true" />
						</div>
						<div class="flex flex-col gap-1">
							<label class="text-xs font-medium text-slate-700">{{ __("أو قيمة القسط") }}</label>
							<input v-model.number="form.installment_amount" type="number" min="0" step="0.01" class="input" dir="ltr" @input="byCount = false" />
						</div>
					</div>
				</template>
				<div v-if="form.recovery_method !== 'Manual'" class="flex flex-col gap-1">
					<label class="text-xs font-medium text-slate-700">{{ __("أول شهر للخصم") }}</label>
					<input v-model="form.start_period" type="month" class="input" />
				</div>
				<p v-if="preview" class="rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-600">{{ preview }}</p>
				<div class="flex flex-col gap-1">
					<label class="text-xs font-medium text-slate-700">{{ __("ملاحظة") }}</label>
					<input v-model="form.note" class="input" />
				</div>
			</div>
		</template>
		<template #actions>
			<div class="flex w-full justify-end gap-2">
				<Button variant="subtle" @click="show = false">{{ __("إلغاء") }}</Button>
				<Button variant="solid" :loading="saving" @click="save">{{ __("صرف السلفة") }}</Button>
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
import { API, RECOVERY_METHODS, currentPeriod, formatMoney, todayISO } from "@/utils/employees"

const props = defineProps({
	modelValue: { type: Boolean, default: false },
	employee: { type: String, default: "" },
	employees: { type: Array, default: () => [] },
	company: { type: String, default: "" },
	lockEmployee: { type: Boolean, default: false },
})
const emit = defineEmits(["update:modelValue", "saved"])
const { showSuccess, showError } = useToast()

const show = computed({
	get: () => props.modelValue,
	set: (v) => emit("update:modelValue", v),
})

const blank = () => ({
	employee: props.employee || "", posting_date: todayISO(), amount: null, mode_of_payment: "",
	recovery_method: "Installments", installments_count: 4, installment_amount: null, start_period: currentPeriod(), note: "",
})
const form = ref(blank())
const options = ref({ modes_of_payment: [], default_mode_of_payment: "" })
const byCount = ref(true)
const saving = ref(false)

watch(() => props.modelValue, async (open) => {
	if (!open) return
	form.value = blank()
	byCount.value = true
	try {
		options.value = await call(`${API}.advances.get_form_options`, { company: props.company || null })
		form.value.mode_of_payment = options.value.default_mode_of_payment || options.value.modes_of_payment[0] || ""
	} catch (e) {
		showError(e?.message || __("فشل تحميل الخيارات"))
	}
})

// Keep count and installment in sync with whichever the user typed last.
watch(() => [form.value.amount, form.value.installments_count, form.value.installment_amount], () => {
	const f = form.value
	const amount = Number(f.amount || 0)
	if (!amount) return
	if (byCount.value && Number(f.installments_count) > 0) {
		f.installment_amount = Math.ceil((amount * 100) / Number(f.installments_count)) / 100
	} else if (!byCount.value && Number(f.installment_amount) > 0) {
		f.installments_count = Math.ceil(amount / Number(f.installment_amount))
	}
})

const preview = computed(() => {
	const f = form.value
	if (!(Number(f.amount) > 0)) return ""
	if (f.recovery_method === "Installments" && Number(f.installment_amount) > 0) {
		return __("السلفة {0} — {1} أقساط × {2} شهريًا", [formatMoney(f.amount), f.installments_count, formatMoney(f.installment_amount)])
	}
	if (f.recovery_method === "Next Payroll") return __("تُخصم {0} كاملة من استحقاق {1}", [formatMoney(f.amount), f.start_period])
	if (f.recovery_method === "Manual") return __("لن تُخصم تلقائيًا — تُسجَّل الدفعات يدويًا")
	return ""
})

async function save() {
	const f = form.value
	if (!f.employee || !f.posting_date || !(Number(f.amount) > 0)) return showError(__("يرجى تعبئة الحقول المطلوبة"))
	if (!f.mode_of_payment) return showError(__("يرجى اختيار طريقة الدفع"))
	saving.value = true
	try {
		const payload = { ...f, start_period: f.start_period ? `${f.start_period}-01` : null }
		if (byCount.value) payload.installment_amount = null
		const res = await call(`${API}.advances.create_advance`, { data: JSON.stringify(payload) })
		showSuccess(__("تم صرف السلفة"))
		show.value = false
		emit("saved", res.name)
	} catch (e) {
		showError(e?.message || __("فشل صرف السلفة"))
	} finally {
		saving.value = false
	}
}
</script>

<style scoped>
.input {
	@apply w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-slate-50;
}
</style>
