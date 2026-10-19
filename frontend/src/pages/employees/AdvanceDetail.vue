<template>
	<div class="flex w-full flex-col gap-4">
		<div v-if="loading && !adv" class="py-12 text-center text-sm text-slate-400">{{ __("جاري التحميل...") }}</div>

		<template v-else-if="adv">
			<section class="bs-card flex flex-wrap items-center justify-between gap-3 p-4">
				<div class="min-w-0">
					<RouterLink :to="{ name: 'EmployeeAdvances' }" class="text-xs text-blue-600 hover:underline">← {{ __("السلف") }}</RouterLink>
					<div class="mt-1 flex flex-wrap items-center gap-2">
						<RouterLink :to="{ name: 'EmployeeDetail', params: { id: adv.employee }, query: { tab: 'advances' } }" class="truncate text-lg font-bold text-slate-900 hover:text-blue-700">
							{{ adv.employee_name }}
						</RouterLink>
						<StatusBadge :status="adv.status" :map="ADVANCE_STATUS" />
					</div>
					<p class="text-sm text-slate-500">{{ __("سلفة بتاريخ {0}", [formatDate(adv.posting_date)]) }} — {{ __(RECOVERY_METHODS[adv.recovery_method]) }}</p>
				</div>
				<div v-if="isOpen" class="flex flex-wrap gap-2">
					<Button variant="subtle" :loading="busy === 'pause'" @click="togglePause">
						{{ adv.status === "Paused" ? __("استئناف الخصم") : __("إيقاف الخصم مؤقتًا") }}
					</Button>
					<Button variant="subtle" @click="openInstallment">{{ __("تعديل القسط") }}</Button>
					<Button variant="subtle" @click="openPayment">{{ __("تسجيل دفعة") }}</Button>
					<Button variant="subtle" theme="red" :loading="busy === 'close'" @click="closeAdvance">{{ __("إغلاق السلفة") }}</Button>
				</div>
				<Button v-if="!adv.repayments?.length" variant="subtle" theme="red" :loading="busy === 'cancel'" @click="cancelAdvance">{{ __("إلغاء السلفة") }}</Button>
			</section>

			<div class="grid grid-cols-1 gap-4 lg:grid-cols-3">
				<section class="bs-card p-4">
					<dl class="space-y-2 text-sm tabular-nums">
						<div class="flex justify-between"><dt class="text-slate-500">{{ __("السلفة الأصلية") }}</dt><dd class="font-semibold">{{ formatMoney(adv.amount, adv.currency) }}</dd></div>
						<div class="flex justify-between"><dt class="text-slate-500">{{ __("تم الاسترداد") }}</dt><dd class="font-semibold text-emerald-600">{{ formatMoney(adv.recovered_amount) }}</dd></div>
						<div class="flex justify-between border-t border-slate-100 pt-2"><dt class="font-bold text-slate-800">{{ __("المتبقي") }}</dt><dd class="text-lg font-bold text-amber-600">{{ formatMoney(adv.remaining_amount, adv.currency) }}</dd></div>
						<div v-if="adv.recovery_method === 'Installments'" class="flex justify-between"><dt class="text-slate-500">{{ __("القسط الشهري") }}</dt><dd class="font-semibold">{{ formatMoney(adv.installment_amount) }}</dd></div>
					</dl>
					<div class="mt-3 h-2 overflow-hidden rounded-full bg-slate-100">
						<div class="h-full rounded-full bg-emerald-500" :style="{ width: progress + '%' }"></div>
					</div>
					<div class="mt-4 space-y-1 text-xs text-slate-500">
						<p v-if="adv.mode_of_payment">{{ __("صُرفت من") }}: {{ adv.mode_of_payment }}</p>
						<p v-if="adv.journal_entry">
							{{ __("قيد الصرف") }}:
							<a :href="`/app/journal-entry/${adv.journal_entry}`" target="_blank" class="text-blue-600 hover:underline">{{ adv.journal_entry }}</a>
						</p>
						<p v-if="adv.note">{{ adv.note }}</p>
					</div>
				</section>

				<section class="bs-card lg:col-span-2">
					<h2 class="border-b border-slate-100 px-4 py-3 text-sm font-bold text-slate-800">{{ __("جدول الاسترداد") }}</h2>
					<div v-if="!adv.schedule.length" class="py-8 text-center text-xs text-slate-400">{{ __("لا توجد أقساط") }}</div>
					<table v-else class="w-full text-sm">
						<thead>
							<tr class="bg-slate-50 text-xs text-slate-600">
								<th class="px-3 py-2 text-start font-semibold">{{ __("الشهر") }}</th>
								<th class="px-3 py-2 text-start font-semibold">{{ __("المصدر") }}</th>
								<th class="px-3 py-2 text-end font-semibold">{{ __("الخصم") }}</th>
								<th class="px-3 py-2 text-start font-semibold">{{ __("الحالة") }}</th>
							</tr>
						</thead>
						<tbody class="divide-y divide-slate-100">
							<tr v-for="(row, i) in adv.schedule" :key="i">
								<td class="px-3 py-2">{{ formatPeriod(row.period) }}</td>
								<td class="px-3 py-2 text-xs text-slate-500">
									<RouterLink v-if="row.payroll_entry" :to="{ name: 'EmployeePayrollEntry', params: { id: row.payroll_entry } }" class="text-blue-600 hover:underline">
										{{ __(REPAYMENT_SOURCES[row.source]) }}
									</RouterLink>
									<span v-else>{{ __(REPAYMENT_SOURCES[row.source]) }}</span>
								</td>
								<td class="px-3 py-2 text-end font-semibold tabular-nums">{{ formatMoney(row.amount) }}</td>
								<td class="px-3 py-2"><StatusBadge :status="row.status" :map="INSTALLMENT_STATUS" /></td>
							</tr>
						</tbody>
					</table>
				</section>
			</div>
		</template>

		<!-- Edit installment -->
		<Dialog v-model="installmentOpen" :options="{ title: __('تعديل القسط'), size: 'sm' }">
			<template #body-content>
				<div class="flex flex-col gap-3">
					<p class="text-xs text-slate-500">{{ __("ينطبق على المتبقي: {0}", [formatMoney(adv?.remaining_amount)]) }}</p>
					<div class="flex flex-col gap-1">
						<label class="text-xs font-medium text-slate-700">{{ __("طريقة الاسترداد") }}</label>
						<select v-model="installmentForm.recovery_method" class="input">
							<option v-for="(label, key) in RECOVERY_METHODS" :key="key" :value="key">{{ __(label) }}</option>
						</select>
					</div>
					<div v-if="installmentForm.recovery_method === 'Installments'" class="grid grid-cols-2 gap-3">
						<div class="flex flex-col gap-1">
							<label class="text-xs font-medium text-slate-700">{{ __("قيمة القسط") }}</label>
							<input v-model.number="installmentForm.installment_amount" type="number" min="0" step="0.01" class="input" dir="ltr" @input="installmentForm.installments_count = null" />
						</div>
						<div class="flex flex-col gap-1">
							<label class="text-xs font-medium text-slate-700">{{ __("أو عدد الأقساط المتبقية") }}</label>
							<input v-model.number="installmentForm.installments_count" type="number" min="1" class="input" dir="ltr" />
						</div>
					</div>
				</div>
			</template>
			<template #actions>
				<div class="flex w-full justify-end gap-2">
					<Button variant="subtle" @click="installmentOpen = false">{{ __("إلغاء") }}</Button>
					<Button variant="solid" :loading="busy === 'installment'" @click="saveInstallment">{{ __("حفظ") }}</Button>
				</div>
			</template>
		</Dialog>

		<!-- Manual payment -->
		<Dialog v-model="paymentOpen" :options="{ title: __('تسجيل دفعة'), size: 'sm' }">
			<template #body-content>
				<div class="flex flex-col gap-3">
					<p class="text-xs text-slate-500">{{ __("الموظف يسدد مباشرة نقدًا أو تحويلًا") }}</p>
					<div class="flex flex-col gap-1">
						<label class="text-xs font-medium text-slate-700">{{ __("المبلغ") }}</label>
						<input v-model.number="paymentForm.amount" type="number" min="0" :max="adv?.remaining_amount" step="0.01" class="input" dir="ltr" />
					</div>
					<div class="flex flex-col gap-1">
						<label class="text-xs font-medium text-slate-700">{{ __("استُلمت في") }}</label>
						<select v-model="paymentForm.mode_of_payment" class="input">
							<option v-for="m in adv?.modes_of_payment || []" :key="m" :value="m">{{ m }}</option>
						</select>
					</div>
					<div class="flex flex-col gap-1">
						<label class="text-xs font-medium text-slate-700">{{ __("التاريخ") }}</label>
						<input v-model="paymentForm.posting_date" type="date" class="input" />
					</div>
				</div>
			</template>
			<template #actions>
				<div class="flex w-full justify-end gap-2">
					<Button variant="subtle" @click="paymentOpen = false">{{ __("إلغاء") }}</Button>
					<Button variant="solid" :loading="busy === 'payment'" @click="savePayment">{{ __("تسجيل") }}</Button>
				</div>
			</template>
		</Dialog>
	</div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue"
import { useRoute, useRouter } from "vue-router"
import { Button, Dialog } from "frappe-ui"
import StatusBadge from "@/components/employees/StatusBadge.vue"
import { useToast } from "@/composables/useToast"
import { call } from "@/utils/apiWrapper"
import {
	ADVANCE_STATUS, API, INSTALLMENT_STATUS, RECOVERY_METHODS, REPAYMENT_SOURCES,
	formatDate, formatMoney, formatPeriod, todayISO,
} from "@/utils/employees"

const route = useRoute()
const router = useRouter()
const { showSuccess, showError } = useToast()

const adv = ref(null)
const loading = ref(false)
const busy = ref("")
const installmentOpen = ref(false)
const installmentForm = ref({})
const paymentOpen = ref(false)
const paymentForm = ref({})

const isOpen = computed(() => ["Active", "Paused"].includes(adv.value?.status))
const progress = computed(() => {
	const a = adv.value
	if (!a || !Number(a.amount)) return 0
	return Math.min(100, Math.round((Number(a.recovered_amount) / Number(a.amount)) * 100))
})

async function load() {
	loading.value = true
	try {
		adv.value = await call(`${API}.advances.get_advance`, { name: route.params.id })
	} catch (e) {
		showError(e?.message || __("فشل تحميل السلفة"))
	} finally {
		loading.value = false
	}
}

async function run(key, method, params = {}, successMsg = "") {
	busy.value = key
	try {
		adv.value = await call(`${API}.advances.${method}`, { name: adv.value.name, ...params })
		if (successMsg) showSuccess(successMsg)
		return true
	} catch (e) {
		showError(e?.message || __("فشلت العملية"))
		return false
	} finally {
		busy.value = ""
	}
}

function togglePause() {
	const pause = adv.value.status !== "Paused"
	run("pause", "set_paused", { paused: pause ? 1 : 0 }, pause ? __("تم إيقاف الخصم") : __("تم استئناف الخصم"))
}

function openInstallment() {
	installmentForm.value = { recovery_method: adv.value.recovery_method, installment_amount: adv.value.installment_amount, installments_count: null }
	installmentOpen.value = true
}

async function saveInstallment() {
	if (await run("installment", "update_installment", installmentForm.value, __("تم تعديل القسط"))) installmentOpen.value = false
}

function openPayment() {
	paymentForm.value = {
		amount: adv.value.remaining_amount,
		mode_of_payment: adv.value.default_mode_of_payment || adv.value.modes_of_payment?.[0] || "",
		posting_date: todayISO(),
	}
	paymentOpen.value = true
}

async function savePayment() {
	if (!(Number(paymentForm.value.amount) > 0)) return showError(__("يرجى إدخال المبلغ"))
	if (await run("payment", "record_payment", paymentForm.value, __("تم تسجيل الدفعة"))) paymentOpen.value = false
}

function closeAdvance() {
	const remaining = Number(adv.value.remaining_amount)
	const msg = remaining > 0
		? __("إغلاق السلفة؟ المتبقي {0} سيُشطب كمصروف رواتب ولن يُخصم", [formatMoney(remaining)])
		: __("إغلاق السلفة؟")
	if (!confirm(msg)) return
	run("close", "close_advance", {}, __("تم إغلاق السلفة"))
}

async function cancelAdvance() {
	if (!confirm(__("إلغاء السلفة نهائيًا؟ سيُلغى قيد الصرف"))) return
	busy.value = "cancel"
	try {
		await call(`${API}.advances.cancel_advance`, { name: adv.value.name })
		showSuccess(__("تم إلغاء السلفة"))
		router.replace({ name: "EmployeeAdvances" })
	} catch (e) {
		showError(e?.message || __("فشل الإلغاء"))
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
