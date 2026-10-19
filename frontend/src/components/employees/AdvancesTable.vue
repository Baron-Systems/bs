<template>
	<div>
		<div v-if="loading" class="py-12 text-center text-sm text-slate-400">{{ __("جاري التحميل...") }}</div>
		<div v-else-if="!rows.length" class="py-12 text-center text-sm text-slate-400">{{ __("لا توجد سلف") }}</div>
		<div v-else class="overflow-x-auto">
			<table class="w-full text-sm">
				<thead>
					<tr class="bg-slate-50 text-xs text-slate-600">
						<th v-if="showEmployee" class="px-3 py-2 text-start font-semibold">{{ __("الموظف") }}</th>
						<th class="px-3 py-2 text-center font-semibold">{{ __("التاريخ") }}</th>
						<th class="px-3 py-2 text-end font-semibold">{{ __("قيمة السلفة") }}</th>
						<th class="hidden px-3 py-2 text-end font-semibold sm:table-cell">{{ __("المسترد") }}</th>
						<th class="px-3 py-2 text-end font-semibold">{{ __("المتبقي") }}</th>
						<th class="hidden px-3 py-2 text-end font-semibold md:table-cell">{{ __("القسط") }}</th>
						<th class="px-3 py-2 text-start font-semibold">{{ __("الحالة") }}</th>
					</tr>
				</thead>
				<tbody class="divide-y divide-slate-100">
					<tr
						v-for="row in rows"
						:key="row.name"
						class="cursor-pointer hover:bg-slate-50"
						@click="router.push({ name: 'EmployeeAdvanceDetail', params: { id: row.name } })"
					>
						<td v-if="showEmployee" class="px-3 py-2 font-semibold text-slate-900">{{ row.employee_name }}</td>
						<td class="px-3 py-2 text-center tabular-nums">{{ formatDate(row.posting_date) }}</td>
						<td class="px-3 py-2 text-end tabular-nums">{{ formatMoney(row.amount) }}</td>
						<td class="hidden px-3 py-2 text-end tabular-nums text-emerald-600 sm:table-cell">{{ formatMoney(row.recovered_amount) }}</td>
						<td class="px-3 py-2 text-end font-bold tabular-nums" :class="row.remaining_amount > 0 ? 'text-amber-600' : 'text-slate-400'">{{ formatMoney(row.remaining_amount) }}</td>
						<td class="hidden px-3 py-2 text-end tabular-nums md:table-cell">
							<template v-if="row.recovery_method === 'Installments'">{{ formatMoney(row.installment_amount) }}</template>
							<span v-else class="text-xs text-slate-500">{{ __(RECOVERY_METHODS[row.recovery_method]) }}</span>
						</td>
						<td class="px-3 py-2"><StatusBadge :status="row.status" :map="ADVANCE_STATUS" /></td>
					</tr>
				</tbody>
			</table>
		</div>
	</div>
</template>

<script setup>
import { useRouter } from "vue-router"
import StatusBadge from "@/components/employees/StatusBadge.vue"
import { ADVANCE_STATUS, RECOVERY_METHODS, formatDate, formatMoney } from "@/utils/employees"

defineProps({
	rows: { type: Array, default: () => [] },
	loading: { type: Boolean, default: false },
	showEmployee: { type: Boolean, default: true },
})
const router = useRouter()
</script>
