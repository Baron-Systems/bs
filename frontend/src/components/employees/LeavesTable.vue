<template>
	<div>
		<div v-if="loading" class="py-12 text-center text-sm text-slate-400">{{ __("جاري التحميل...") }}</div>
		<div v-else-if="!rows.length" class="py-12 text-center text-sm text-slate-400">{{ __("لا توجد طلبات إجازة") }}</div>
		<div v-else class="overflow-x-auto">
			<table class="w-full text-sm">
				<thead>
					<tr class="bg-slate-50 text-xs text-slate-600">
						<th v-if="showEmployee" class="px-3 py-2 text-start font-semibold">{{ __("الموظف") }}</th>
						<th class="px-3 py-2 text-start font-semibold">{{ __("النوع") }}</th>
						<th class="px-3 py-2 text-center font-semibold">{{ __("من") }}</th>
						<th class="px-3 py-2 text-center font-semibold">{{ __("إلى") }}</th>
						<th class="px-3 py-2 text-center font-semibold">{{ __("الأيام") }}</th>
						<th class="px-3 py-2 text-start font-semibold">{{ __("الحالة") }}</th>
						<th class="px-3 py-2 text-end font-semibold"></th>
					</tr>
				</thead>
				<tbody class="divide-y divide-slate-100">
					<tr v-for="row in rows" :key="row.name" class="hover:bg-slate-50">
						<td v-if="showEmployee" class="px-3 py-2">
							<RouterLink :to="{ name: 'EmployeeDetail', params: { id: row.employee }, query: { tab: 'leaves' } }" class="font-semibold text-slate-900 hover:text-blue-600">
								{{ row.employee_name }}
							</RouterLink>
							<p v-if="row.reason" class="max-w-[16rem] truncate text-[11px] text-slate-400">{{ row.reason }}</p>
						</td>
						<td class="px-3 py-2 text-slate-700">
							{{ __(LEAVE_TYPES[row.leave_type] || row.leave_type) }}
							<a v-if="row.attachment" :href="row.attachment" target="_blank" class="ms-1 text-xs text-blue-600" :title="__('مرفق')">📎</a>
						</td>
						<td class="px-3 py-2 text-center tabular-nums">{{ formatShortDate(row.from_date) }}</td>
						<td class="px-3 py-2 text-center tabular-nums">{{ formatShortDate(row.to_date) }}</td>
						<td class="px-3 py-2 text-center tabular-nums">{{ formatNumber(row.total_days) }}</td>
						<td class="px-3 py-2"><StatusBadge :status="row.status" :map="LEAVE_STATUS" /></td>
						<td class="whitespace-nowrap px-3 py-2 text-end">
							<template v-if="row.status === 'Pending'">
								<button type="button" class="act text-emerald-700 hover:bg-emerald-50" @click="setStatus(row, 'Approved')">{{ __("قبول") }}</button>
								<button type="button" class="act text-red-700 hover:bg-red-50" @click="setStatus(row, 'Rejected')">{{ __("رفض") }}</button>
								<button type="button" class="act text-slate-600 hover:bg-slate-100" @click="$emit('edit', row)">{{ __("تعديل") }}</button>
							</template>
							<button v-else-if="row.status === 'Approved'" type="button" class="act text-slate-600 hover:bg-slate-100" @click="setStatus(row, 'Cancelled')">{{ __("إلغاء") }}</button>
							<button v-else type="button" class="act text-slate-600 hover:bg-slate-100" @click="setStatus(row, 'Pending')">{{ __("إعادة فتح") }}</button>
						</td>
					</tr>
				</tbody>
			</table>
		</div>
	</div>
</template>

<script setup>
import StatusBadge from "@/components/employees/StatusBadge.vue"
import { useToast } from "@/composables/useToast"
import { call } from "@/utils/apiWrapper"
import { API, LEAVE_STATUS, LEAVE_TYPES, formatNumber, formatShortDate } from "@/utils/employees"

defineProps({
	rows: { type: Array, default: () => [] },
	loading: { type: Boolean, default: false },
	showEmployee: { type: Boolean, default: true },
})
const emit = defineEmits(["edit", "changed"])
const { showSuccess, showError } = useToast()

const CONFIRM = {
	Approved: "قبول طلب الإجازة؟ سيظهر في الدوام تلقائيًا",
	Rejected: "رفض طلب الإجازة؟",
	Cancelled: "إلغاء الإجازة المعتمدة؟ ستُزال من الدوام",
	Pending: "إعادة فتح الطلب؟",
}

async function setStatus(row, status) {
	if (!confirm(__(CONFIRM[status]))) return
	try {
		await call(`${API}.leaves.set_leave_status`, { name: row.name, status })
		showSuccess(__("تم تحديث الطلب"))
		emit("changed")
	} catch (e) {
		showError(e?.message || __("فشل تحديث الطلب"))
	}
}
</script>

<style scoped>
.act {
	@apply rounded-md px-2 py-1 text-xs font-semibold;
}
</style>
