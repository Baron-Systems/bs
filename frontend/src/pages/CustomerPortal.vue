<template>
<div class="min-h-screen flex flex-col bg-slate-900 text-slate-200" dir="rtl">
<!-- Header -->
<header class="bg-slate-900/80 backdrop-blur-md border-b border-slate-800 sticky top-0 z-30 shadow-lg">
<div class="max-w-5xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between gap-3">
				<div class="flex items-center gap-3 min-w-0">
					<img v-if="logo && !logoFailed" :src="logo" alt="" class="w-11 h-11 flex-shrink-0 object-contain" draggable="false" @error="logoFailed = true" />
					<div v-else class="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 bg-white/10 border border-white/10">
<svg class="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
</svg>
</div>
<div class="min-w-0">
<h1 class="text-base sm:text-lg font-bold text-white truncate">
{{ customerName || __("بوابة العميل") }}
</h1>
<p class="text-xs text-blue-200/80 truncate">
{{ __("كشف حساب العميل - دفتر الأستاذ العام") }}
</p>
</div>
</div>
<button
@click="logout"
class="px-3 py-1.5 rounded-lg text-sm text-slate-300 hover:bg-rose-500/15 hover:text-rose-300 hover:border-rose-500/40 border border-slate-700 transition-all"
>
{{ __("خروج") }}
</button>
</div>
</header>

<main class="flex-1 max-w-5xl w-full mx-auto px-4 sm:px-6 py-6 sm:py-8">
<!-- Loading -->
<div v-if="loading" class="flex items-center justify-center py-20">
<div class="flex flex-col items-center gap-3">
<svg class="animate-spin h-10 w-10 text-blue-400" fill="none" viewBox="0 0 24 24">
<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
</svg>
<p class="text-slate-400 text-sm">{{ __("جاري تحميل البيانات...") }}</p>
</div>
</div>

<section v-else class="bg-slate-800/80 backdrop-blur-md border border-slate-700 rounded-2xl shadow-2xl p-4 sm:p-5">
<div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mb-3">
<h4 class="text-sm font-bold text-white flex items-center gap-2">
<svg class="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
</svg>
{{ __("كشف حساب العميل - دفتر الأستاذ العام") }}
</h4>
<div class="flex items-center gap-2 flex-wrap">
<div class="flex items-center gap-1">
<label class="text-[10px] text-slate-400 font-medium">{{ __("من تاريخ") }}</label>
<input
type="date"
v-model="fromDate"
@change="loadLedger"
class="bg-slate-900/60 border border-slate-600 rounded-lg px-2 py-1 text-xs text-white [color-scheme:dark] focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
/>
</div>
<div class="flex items-center gap-1">
<label class="text-[10px] text-slate-400 font-medium">{{ __("إلى تاريخ") }}</label>
<input
type="date"
v-model="toDate"
@change="loadLedger"
class="bg-slate-900/60 border border-slate-600 rounded-lg px-2 py-1 text-xs text-white [color-scheme:dark] focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
/>
</div>
<button
v-if="showLastMonth"
@click="showLastMonth = false"
class="px-3 py-1.5 rounded-lg text-xs font-semibold text-white transition-all bg-blue-600 hover:bg-blue-500 shadow-sm"
>{{ __("إظهار الكل") }}</button>
<button
v-else
@click="showLastMonth = true"
class="px-3 py-1.5 rounded-lg text-xs font-semibold border border-slate-600 text-slate-200 hover:bg-slate-700 transition-all"
>{{ __("آخر شهر") }}</button>
<button
@click="printReport"
class="px-3 py-1.5 rounded-lg text-xs font-semibold border border-slate-600 text-slate-200 hover:bg-slate-700 transition-all flex items-center gap-1.5"
>
<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
</svg>
{{ __("طباعة") }}
</button>
</div>
</div>

<!-- GL Summary Cards -->
<div class="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-3">
<div class="bg-slate-900/60 rounded-lg p-2 border border-slate-700">
<p class="text-[10px] text-slate-400 font-medium">{{ __("رصيد افتتاحي") }}</p>
<p class="text-sm font-bold text-white">{{ formatCurrency(ledger.opening_balance) }}</p>
</div>
<div class="bg-blue-500/10 rounded-lg p-2 border border-blue-500/30">
<p class="text-[10px] text-blue-300 font-medium">{{ __("إجمالي مدين") }}</p>
<p class="text-sm font-bold text-blue-300">{{ formatCurrency(ledger.total_debit) }}</p>
</div>
<div class="bg-emerald-500/10 rounded-lg p-2 border border-emerald-500/30">
<p class="text-[10px] text-emerald-300 font-medium">{{ __("إجمالي دائن") }}</p>
<p class="text-sm font-bold text-emerald-300">{{ formatCurrency(ledger.total_credit) }}</p>
</div>
<div class="bg-amber-500/10 rounded-lg p-2 border border-amber-500/30">
<p class="text-[10px] text-amber-300 font-medium">{{ __("رصيد ختامي") }}</p>
<p class="text-sm font-bold text-amber-300">{{ formatCurrency(ledger.closing_balance) }}</p>
</div>
</div>

<div class="overflow-auto max-h-[500px] rounded-xl border border-slate-700">
<table v-if="filteredEntries.length" class="min-w-full text-xs">
<thead class="sticky top-0 bg-slate-900">
<tr>
<th class="px-1 py-2.5 text-center font-bold text-slate-300 w-8"></th>
<th class="px-2 py-2.5 text-start font-bold text-slate-300">{{ __("التاريخ") }}</th>
<th class="px-2 py-2.5 text-start font-bold text-slate-300">{{ __("نوع السند") }}</th>
<th class="px-2 py-2.5 text-start font-bold text-slate-300">{{ __("رقم السند") }}</th>
<th class="px-2 py-2.5 text-end font-bold text-slate-300">{{ __("مدين") }}</th>
<th class="px-2 py-2.5 text-end font-bold text-slate-300">{{ __("دائن") }}</th>
<th class="px-2 py-2.5 text-end font-bold text-slate-300">{{ __("الرصيد") }}</th>
</tr>
</thead>
<tbody class="divide-y divide-slate-700/70">
<tr class="bg-slate-900/40 font-semibold">
<td colspan="4" class="px-2 py-2 text-slate-300">{{ __("رصيد افتتاحي") }}</td>
<td colspan="2" class="px-2 py-2"></td>
<td class="px-2 py-2 text-end font-bold text-white">{{ formatCurrency(ledger.opening_balance) }}</td>
</tr>
<template v-for="e in filteredEntries" :key="e.gl_entry">
<tr class="hover:bg-slate-700/40 transition-colors">
<td class="px-1 py-2 text-center">
<button
v-if="isInvoice(e.voucher_type)"
@click="toggleExpand(e)"
class="p-1 rounded-md hover:bg-slate-700 transition-all"
aria-label="تفاصيل"
>
<svg class="w-3.5 h-3.5 text-slate-400 transition-transform" :class="expandedRows[e.voucher_no] ? 'rotate-90' : ''" fill="none" stroke="currentColor" viewBox="0 0 24 24">
<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 5l7 7-7 7" />
</svg>
</button>
</td>
<td class="px-2 py-2 text-slate-400 whitespace-nowrap">{{ formatDate(e.posting_date) }}</td>
<td class="px-2 py-2 text-slate-300">{{ formatVoucherType(e.voucher_type, e.voucher_subtype) }}</td>
<td class="px-2 py-2 font-semibold">
<a :href="glDocUrl(e)" target="_blank" class="text-blue-400 hover:text-blue-300 hover:underline">{{ e.voucher_no }}</a>
</td>
<td class="px-2 py-2 text-end font-semibold text-blue-300">{{ e.debit ? formatCurrency(e.debit) : "" }}</td>
<td class="px-2 py-2 text-end font-semibold text-emerald-300">{{ e.credit ? formatCurrency(e.credit) : "" }}</td>
<td class="px-2 py-2 text-end font-bold" :class="e.balance >= 0 ? 'text-white' : 'text-rose-400'">{{ formatCurrency(e.balance) }}</td>
</tr>
<tr v-if="expandedRows[e.voucher_no]">
<td colspan="7" class="px-2 pb-3 pt-1 bg-slate-900/40">
<div v-if="rowItemsLoading[e.voucher_no]" class="text-center py-3 text-xs text-slate-500">{{ __("جاري تحميل التفاصيل...") }}</div>
<div v-else-if="rowItems[e.voucher_no] && rowItems[e.voucher_no].length" class="bg-slate-900/70 border border-slate-700 rounded-lg p-2">
<table class="min-w-full text-[11px]">
<thead>
<tr class="text-slate-400 border-b border-slate-700">
<th class="px-2 py-1 text-start font-semibold">{{ __("الصنف") }}</th>
<th class="px-2 py-1 text-end font-semibold">{{ __("الكمية") }}</th>
<th class="px-2 py-1 text-end font-semibold">{{ __("السعر") }}</th>
<th class="px-2 py-1 text-end font-semibold">{{ __("المبلغ") }}</th>
</tr>
</thead>
<tbody class="divide-y divide-slate-800">
<tr v-for="item in rowItems[e.voucher_no]" :key="item.name">
<td class="px-2 py-1 text-start text-slate-300">{{ item.item_name || item.item_code }}</td>
<td class="px-2 py-1 text-end text-slate-300">{{ item.qty }} {{ item.uom || "" }}</td>
<td class="px-2 py-1 text-end text-slate-300">{{ formatCurrency(item.rate) }}</td>
<td class="px-2 py-1 text-end font-semibold text-white">{{ formatCurrency(item.amount) }}</td>
</tr>
</tbody>
</table>
</div>
<div v-else class="text-center py-3 text-xs text-slate-500">{{ __("لا توجد أصناف") }}</div>
</td>
</tr>
</template>
<tr class="bg-slate-900 font-bold border-t-2 border-slate-600">
<td colspan="4" class="px-2 py-2 text-white">{{ __("الإجمالي") }}</td>
<td class="px-2 py-2 text-end text-blue-300">{{ formatCurrency(ledger.total_debit) }}</td>
<td class="px-2 py-2 text-end text-emerald-300">{{ formatCurrency(ledger.total_credit) }}</td>
<td class="px-2 py-2 text-end text-white">{{ formatCurrency(ledger.closing_balance) }}</td>
</tr>
</tbody>
</table>
<div v-else class="text-center py-8 text-sm text-slate-500">
<svg class="w-10 h-10 mx-auto mb-2 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
</svg>
{{ __("لا توجد حركات") }}
</div>
</div>
</section>
</main>
</div>
</template>

<script setup>
import { call } from "@/utils/apiWrapper"
import { useToast } from "@/composables/useToast"
import router from "@/router"
import { computed, onMounted, ref } from "vue"

const { showError } = useToast()

const customerName = ref("")
const customerId = ref("")
const logo = ref("")
const logoFailed = ref(false)

const loading = ref(true)
const ledger = ref({ opening_balance: 0, closing_balance: 0, total_debit: 0, total_credit: 0, entries: [], currency: "" })
const fromDate = ref("")
const toDate = ref("")
const showLastMonth = ref(true)
const expandedRows = ref({})
const rowItems = ref({})
const rowItemsLoading = ref({})

const filteredEntries = computed(() => {
if (!showLastMonth.value) return ledger.value.entries || []
const cutoff = new Date()
cutoff.setDate(cutoff.getDate() - 30)
cutoff.setHours(0, 0, 0, 0)
return (ledger.value.entries || []).filter((e) => e.posting_date && new Date(e.posting_date) >= cutoff)
})

function getToken() {
return localStorage.getItem("bs_customer_token")
}

onMounted(async () => {
if (!getToken()) {
router.replace({ name: "CustomerPortalLogin" })
return
}
customerName.value = localStorage.getItem("bs_customer_name") || ""
customerId.value = localStorage.getItem("bs_customer_id") || ""
loadBranding()
await loadLedger()
})

async function loadBranding() {
try {
const branding = await call("bs.baron_servies.api.customer_portal.get_customer_portal_branding")
if (branding?.logo) logo.value = branding.logo
} catch (e) {
// keep the default icon
}
}

async function loadLedger() {
loading.value = true
try {
const params = {}
if (fromDate.value) params.from_date = fromDate.value
if (toDate.value) params.to_date = toDate.value
const result = await call("bs.baron_servies.api.customer_portal.get_customer_portal_ledger", params, {
headers: { "X-Customer-Token": getToken() },
})
if (result && result.success) {
ledger.value = result.ledger || { opening_balance: 0, closing_balance: 0, total_debit: 0, total_credit: 0, entries: [], currency: "" }
expandAllInvoices()
} else {
throw new Error(result?.message || "فشل تحميل كشف الحساب")
}
} catch (e) {
showError(e?.message || "فشل تحميل كشف الحساب")
} finally {
loading.value = false
}
}

function isInvoice(voucher_type) {
return voucher_type === "Sales Invoice" || voucher_type === "Purchase Invoice"
}

// Invoice details are shown by default: open every invoice row and load all items in one call.
async function expandAllInvoices() {
const invoices = []
const seen = new Set()
for (const e of ledger.value.entries || []) {
if (isInvoice(e.voucher_type) && e.voucher_no && !seen.has(e.voucher_no)) {
seen.add(e.voucher_no)
invoices.push({ voucher_type: e.voucher_type, voucher_no: e.voucher_no })
}
}
const expanded = {}
invoices.forEach((v) => { expanded[v.voucher_no] = true })
expandedRows.value = expanded

const missing = invoices.filter((v) => !rowItems.value[v.voucher_no])
if (!missing.length) return
const loadingMap = { ...rowItemsLoading.value }
missing.forEach((v) => { loadingMap[v.voucher_no] = true })
rowItemsLoading.value = loadingMap
try {
const result = await call("bs.baron_servies.api.customer_portal.get_customer_portal_vouchers_items", {
vouchers: JSON.stringify(missing),
}, {
headers: { "X-Customer-Token": getToken() },
})
if (!result?.success) throw new Error(result?.message)
const byVoucher = result.items || {}
const items = { ...rowItems.value }
missing.forEach((v) => { items[v.voucher_no] = byVoucher[v.voucher_no] || [] })
rowItems.value = items
} catch (err) {
// rows stay expandable one by one through toggleExpand
const expandedNow = { ...expandedRows.value }
missing.forEach((v) => { delete expandedNow[v.voucher_no] })
expandedRows.value = expandedNow
} finally {
const done = { ...rowItemsLoading.value }
missing.forEach((v) => { done[v.voucher_no] = false })
rowItemsLoading.value = done
}
}

async function toggleExpand(e) {
const no = e.voucher_no
if (!no) return
if (expandedRows.value[no]) {
expandedRows.value = { ...expandedRows.value, [no]: false }
return
}
expandedRows.value = { ...expandedRows.value, [no]: true }
if (rowItems.value[no]) return
rowItemsLoading.value = { ...rowItemsLoading.value, [no]: true }
try {
const result = await call("bs.baron_servies.api.customer_portal.get_customer_portal_voucher_items", {
voucher_type: e.voucher_type,
voucher_no: no,
}, {
headers: { "X-Customer-Token": getToken() },
})
rowItems.value = { ...rowItems.value, [no]: Array.isArray(result?.items) ? result.items : [] }
} catch (err) {
rowItems.value = { ...rowItems.value, [no]: [] }
} finally {
rowItemsLoading.value = { ...rowItemsLoading.value, [no]: false }
}
}

function formatCurrency(value) {
const n = Number(value || 0)
const cur = ledger.value.currency || ""
return n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + (cur ? " " + cur : "")
}

function formatDate(date) {
if (!date) return "-"
return new Date(date).toLocaleDateString("en-GB")
}

// voucher_subtype (Receive / Pay / Credit Note …) tells a receipt from a payment and returns from invoices.
function formatVoucherType(voucher_type, voucher_subtype) {
const bySubtype = {
"Payment Entry|Receive": __("قبض"),
"Payment Entry|Pay": __("دفع"),
"Payment Entry|Internal Transfer": __("تحويل داخلي"),
"Sales Invoice|Credit Note": __("مرتجع مبيعات"),
"Purchase Invoice|Debit Note": __("مرتجع مشتريات"),
}
const map = {
"Sales Invoice": __("فاتورة مبيعات"),
"Purchase Invoice": __("فاتورة مشتريات"),
"Payment Entry": __("دفعة"),
"Journal Entry": __("قيد يومية"),
}
return bySubtype[`${voucher_type}|${voucher_subtype}`] || map[voucher_type] || voucher_type || ""
}

function glDocUrl(e) {
const t = e.voucher_type
const n = encodeURIComponent(e.voucher_no || "")
if (t === "Sales Invoice") return `/app/sales-invoice/${n}`
if (t === "Purchase Invoice") return `/app/purchase-invoice/${n}`
if (t === "Payment Entry") return `/app/payment-entry/${n}`
if (t === "Journal Entry") return `/app/journal-entry/${n}`
return `/app/${n}`
}

async function logout() {
try {
await call("bs.baron_servies.api.customer_portal.customer_portal_logout", {}, {
headers: { "X-Customer-Token": getToken() },
})
} catch (e) {
console.error(e)
}
localStorage.removeItem("bs_customer_token")
localStorage.removeItem("bs_customer_name")
localStorage.removeItem("bs_customer_id")
router.replace({ name: "CustomerPortalLogin" })
}

// Printed statements include the invoice items that are expanded on screen.
function escapeHtml(value) {
	return String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]))
}

function printItemsRow(e) {
	if (!isInvoice(e.voucher_type) || !expandedRows.value[e.voucher_no]) return ""
	const items = rowItems.value[e.voucher_no] || []
	if (!items.length) return ""
	const rows = items.map((it) =>
		"<tr>" +
			"<td>" + escapeHtml(it.item_name || it.item_code) + "</td>" +
			'<td class="num">' + escapeHtml(it.qty) + " " + escapeHtml(it.uom || "") + "</td>" +
			'<td class="num">' + formatCurrency(it.rate) + "</td>" +
			'<td class="num">' + formatCurrency(it.amount) + "</td>" +
		"</tr>"
	).join("")
	return '<tr class="items"><td colspan="6"><table class="sub"><thead><tr>' +
		"<th>" + __("الصنف") + '</th><th class="num">' + __("الكمية") + '</th><th class="num">' + __("السعر") + '</th><th class="num">' + __("المبلغ") + "</th>" +
		"</tr></thead><tbody>" + rows + "</tbody></table></td></tr>"
}

function printReport() {
const w = window.open("", "_blank", "width=1000,height=750")
if (!w) return
const cur = ledger.value.currency || ""
const opening = formatCurrency(ledger.value.opening_balance)
const closing = formatCurrency(ledger.value.closing_balance)
const totDebit = formatCurrency(ledger.value.total_debit)
const totCredit = formatCurrency(ledger.value.total_credit)

const bodyRows = filteredEntries.value.map((e) => {
return "<tr>" +
"<td>" + formatDate(e.posting_date) + "</td>" +
"<td>" + (formatVoucherType(e.voucher_type, e.voucher_subtype)) + "</td>" +
"<td>" + (e.voucher_no || "") + "</td>" +
"<td class=\"num debit\">" + (e.debit ? formatCurrency(e.debit) : "") + "</td>" +
"<td class=\"num credit\">" + (e.credit ? formatCurrency(e.credit) : "") + "</td>" +
"<td class=\"num bal\">" + formatCurrency(e.balance) + "</td>" +
"</tr>" + printItemsRow(e)
}).join("")

const html = `<!DOCTYPE html>
<html dir=rtl>
<head>
<meta charset=UTF-8>
<title>${__("كشف حساب العميل - دفتر الأستاذ العام")}</title>
<style>
  * { box-sizing: border-box; }
  body { font-family: 'Tahoma', 'Arial', sans-serif; margin: 0; padding: 24px; background: #fff; color: #333; }
  .header { text-align: center; margin-bottom: 16px; border-bottom: 2px solid #2563eb; padding-bottom: 12px; }
  .header h2 { margin: 0 0 6px; color: #1e40af; font-size: 22px; }
  .header .meta { margin: 0; color: #666; font-size: 13px; }
  .summary { display: flex; justify-content: space-around; gap: 8px; margin: 12px 0; flex-wrap: wrap; }
  .summary .box { flex: 1; min-width: 140px; border: 1px solid #e5e7eb; border-radius: 8px; padding: 8px 10px; text-align: center; }
  .summary .box .lbl { font-size: 11px; color: #6b7280; margin: 0; }
  .summary .box .val { font-size: 15px; font-weight: 700; margin: 2px 0 0; }
  table { width: 100%; border-collapse: collapse; margin-top: 8px; }
  th, td { border: 1px solid #e5e7eb; padding: 6px 8px; text-align: right; font-size: 12px; }
  th { background: #f3f4f6; color: #374151; font-weight: 600; }
  td.num, th.num { text-align: left; font-variant-numeric: tabular-nums; }
  td.debit { color: #1e40af; font-weight: 600; }
  td.credit { color: #047857; font-weight: 600; }
  td.bal { font-weight: 700; }
  tr.items > td { background: #fafafa; padding: 4px 8px 8px; }
  table.sub { width: 100%; margin: 0; border-collapse: collapse; }
  table.sub th, table.sub td { border: 1px solid #eef0f3; padding: 3px 6px; font-size: 10.5px; color: #4b5563; }
  table.sub th { background: #f3f4f6; font-weight: 600; }
  tr.items { page-break-inside: avoid; }
  tr.opening td, tr.totals td { background: #f9fafb; font-weight: 700; }
  .footer { margin-top: 24px; text-align: center; font-size: 12px; color: #9ca3af; }
</style>
</head>
<body>
<div class='header'>
  <h2>${__("كشف حساب العميل - دفتر الأستاذ العام")}</h2>
  <p class='meta'>${customerName.value} · ${new Date().toLocaleDateString('en-GB')}</p>
</div>
<div class='summary'>
  <div class='box'><p class='lbl'>${__("رصيد افتتاحي")}</p><p class='val'>${opening}</p></div>
  <div class='box'><p class='lbl'>${__("إجمالي مدين")}</p><p class='val' style='color:#1e40af'>${totDebit}</p></div>
  <div class='box'><p class='lbl'>${__("إجمالي دائن")}</p><p class='val' style='color:#047857'>${totCredit}</p></div>
  <div class='box'><p class='lbl'>${__("رصيد ختامي")}</p><p class='val'>${closing}</p></div>
</div>
<table>
  <thead>
    <tr>
      <th>${__("التاريخ")}</th>
      <th>${__("نوع السند")}</th>
      <th>${__("رقم السند")}</th>
      <th class="num">${__("مدين")}</th>
      <th class="num">${__("دائن")}</th>
      <th class="num">${__("الرصيد")}</th>
    </tr>
  </thead>
  <tbody>
    <tr class="opening"><td colspan="3">${__("رصيد افتتاحي")}</td><td colspan="2"></td><td class="num">${opening}</td></tr>
    ${bodyRows}
    <tr class="totals"><td colspan="3">${__("الإجمالي")}</td><td class="num">${totDebit}</td><td class="num">${totCredit}</td><td class="num">${closing}</td></tr>
  </tbody>
</table>
<div class='footer'>${__("كشف حساب العميل - دفتر الأستاذ العام")} · ${cur}</div>
</body>
</html>`
w.document.open()
w.document.write(html)
w.document.close()
w.print()
}
</script>
