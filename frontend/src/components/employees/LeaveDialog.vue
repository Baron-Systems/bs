<template>
	<Dialog v-model="show" :options="{ title: form.name ? __('تعديل طلب إجازة') : __('طلب إجازة'), size: 'md' }">
		<template #body-content>
			<div class="flex flex-col gap-3">
				<div class="flex flex-col gap-1">
					<label class="text-xs font-medium text-slate-700">{{ __("الموظف") }} <span class="text-red-500">*</span></label>
					<EmployeePicker v-model="form.employee" :employees="employees" :disabled="lockEmployee" />
				</div>
				<div class="flex flex-col gap-1">
					<label class="text-xs font-medium text-slate-700">{{ __("نوع الإجازة") }} <span class="text-red-500">*</span></label>
					<div class="grid grid-cols-3 gap-2 sm:grid-cols-5">
						<button
							v-for="(label, key) in LEAVE_TYPES"
							:key="key"
							type="button"
							class="rounded-lg border px-2 py-1.5 text-xs font-semibold"
							:class="form.leave_type === key ? 'border-blue-500 bg-blue-50 text-blue-700' : 'border-slate-200 text-slate-600 hover:bg-slate-50'"
							@click="form.leave_type = key"
						>
							{{ __(label) }}
						</button>
					</div>
				</div>
				<div class="grid grid-cols-2 gap-3">
					<div class="flex flex-col gap-1">
						<label class="text-xs font-medium text-slate-700">{{ __("من تاريخ") }} <span class="text-red-500">*</span></label>
						<input v-model="form.from_date" type="date" class="input" />
					</div>
					<div class="flex flex-col gap-1">
						<label class="text-xs font-medium text-slate-700">{{ __("إلى تاريخ") }} <span class="text-red-500">*</span></label>
						<input v-model="form.to_date" type="date" class="input" :min="form.from_date" />
					</div>
				</div>
				<div class="flex flex-wrap items-center gap-x-4 gap-y-1 rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-600">
					<span>{{ __("عدد الأيام") }}: <b class="tabular-nums">{{ days }}</b> <span class="text-slate-400">{{ __("(أيام عمل فقط)") }}</span></span>
					<span v-if="form.leave_type === 'Annual' && balance">
						{{ __("رصيد السنوية المتبقي") }}: <b class="tabular-nums" :class="days > balance.remaining ? 'text-red-600' : 'text-emerald-600'">{{ balance.remaining }}</b>
					</span>
					<span v-if="form.leave_type === 'Unpaid'" class="text-amber-600">{{ __("تُخصم من الاستحقاق") }}</span>
				</div>
				<div class="flex flex-col gap-1">
					<label class="text-xs font-medium text-slate-700">{{ __("السبب") }}</label>
					<textarea v-model="form.reason" rows="2" class="input" />
				</div>
				<div class="flex items-center gap-3">
					<label class="cursor-pointer text-xs font-medium text-blue-600 hover:underline">
						{{ uploading ? __("جاري الرفع...") : form.attachment ? __("تغيير المرفق") : __("+ إرفاق ملف") }}
						<input type="file" class="hidden" @change="onFile" />
					</label>
					<a v-if="form.attachment" :href="form.attachment" target="_blank" class="truncate text-xs text-slate-500 underline">{{ form.attachment.split("/").pop() }}</a>
				</div>
				<label v-if="!form.name" class="flex items-center gap-2 text-sm text-slate-700">
					<input v-model="form.approve_now" type="checkbox" class="rounded border-slate-200" />
					{{ __("اعتماد مباشرة") }}
				</label>
			</div>
		</template>
		<template #actions>
			<div class="flex w-full justify-end gap-2">
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
import { uploadFile } from "@/utils/upload"
import { API, LEAVE_TYPES, todayISO } from "@/utils/employees"

const props = defineProps({
	modelValue: { type: Boolean, default: false },
	record: { type: Object, default: null },
	employees: { type: Array, default: () => [] },
	lockEmployee: { type: Boolean, default: false },
})
const emit = defineEmits(["update:modelValue", "saved"])
const { showSuccess, showError } = useToast()

const show = computed({
	get: () => props.modelValue,
	set: (v) => emit("update:modelValue", v),
})

const blank = () => ({ name: "", employee: "", leave_type: "Annual", from_date: todayISO(), to_date: todayISO(), reason: "", attachment: "", approve_now: false })
const form = ref(blank())
const days = ref(0)
const balance = ref(null)
const saving = ref(false)
const uploading = ref(false)

watch(() => props.modelValue, (open) => {
	if (!open) return
	const r = props.record || {}
	form.value = { ...blank(), ...Object.fromEntries(Object.entries(r).filter(([k, v]) => k in blank() && v != null)) }
})

let countTimer = null
watch(() => [form.value.employee, form.value.from_date, form.value.to_date], () => {
	clearTimeout(countTimer)
	countTimer = setTimeout(refreshCounts, 250)
})

async function refreshCounts() {
	const { employee, from_date, to_date } = form.value
	if (!employee || !from_date || !to_date) {
		days.value = 0
		return
	}
	try {
		const [c, b] = await Promise.all([
			call(`${API}.leaves.count_days`, { employee, from_date, to_date }),
			call(`${API}.leaves.get_leave_balance`, { employee, year: from_date.slice(0, 4) }),
		])
		days.value = c.days
		balance.value = b
	} catch {
		days.value = 0
	}
}

async function onFile(e) {
	const file = e.target.files?.[0]
	if (!file) return
	uploading.value = true
	try {
		form.value.attachment = await uploadFile(file, { isPrivate: true })
	} catch (err) {
		showError(err?.message || __("فشل رفع الملف"))
	} finally {
		uploading.value = false
		e.target.value = ""
	}
}

async function save() {
	const f = form.value
	if (!f.employee || !f.leave_type || !f.from_date || !f.to_date) return showError(__("يرجى تعبئة الحقول المطلوبة"))
	saving.value = true
	try {
		await call(`${API}.leaves.save_leave`, { data: JSON.stringify(f) })
		showSuccess(__("تم حفظ طلب الإجازة"))
		show.value = false
		emit("saved")
	} catch (e) {
		showError(e?.message || __("فشل حفظ الإجازة"))
	} finally {
		saving.value = false
	}
}
</script>

<style scoped>
.input {
	@apply w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500;
}
</style>
