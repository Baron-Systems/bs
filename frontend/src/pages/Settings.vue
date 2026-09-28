<template>
<div class="min-h-screen flex flex-col bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50" dir="rtl">
<!-- Header -->
<header class="bg-white/80 backdrop-blur-md border-b border-slate-200 sticky top-0 z-30 shadow-sm">
<div class="max-w-5xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between gap-3">
<div class="flex items-center gap-3 min-w-0">
<button
@click="goBack"
class="p-2 rounded-xl text-slate-600 hover:bg-slate-100 transition-all hover:scale-105 active:scale-95 flex-shrink-0"
aria-label="رجوع"
>
<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
</svg>
</button>
<div class="w-10 h-10 bg-gradient-to-br from-slate-600 to-slate-800 rounded-xl flex items-center justify-center flex-shrink-0 shadow-lg shadow-slate-500/30">
<svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
</svg>
</div>
<div class="min-w-0">
<h1 class="text-base sm:text-lg font-bold text-slate-900 truncate">{{ __("إعدادات الصفحة الرئيسية") }}</h1>
<p class="text-xs text-slate-500 truncate">{{ __("تفعيل البطاقات وتحديد المستخدمين - مسموح للمدير فقط") }}</p>
</div>
</div>
</div>
</header>

<main class="flex-1 max-w-5xl w-full mx-auto px-4 sm:px-6 py-6 sm:py-8">
<!-- Unauthorized -->
<div v-if="!isAdmin" class="bg-rose-50 border border-rose-200 rounded-2xl p-6 text-center">
<p class="text-rose-700 font-semibold">{{ __("غير مصرح") }}</p>
<p class="text-sm text-rose-600 mt-1">{{ __("هذه الصفحة مخصصة لحساب Administrator فقط") }}</p>
</div>

<template v-else>
<!-- Loading -->
<div v-if="loading" class="flex items-center justify-center py-20">
<div class="flex flex-col items-center gap-3">
<svg class="animate-spin h-10 w-10 text-blue-600" fill="none" viewBox="0 0 24 24">
<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
</svg>
<p class="text-slate-500 text-sm">{{ __("جاري التحميل...") }}</p>
</div>
</div>

<template v-else>
<div class="bg-white border border-slate-200 rounded-2xl shadow-md overflow-hidden mb-4">
<div class="px-5 py-4 border-b border-slate-100 flex items-center justify-between flex-wrap gap-2">
<h2 class="font-bold text-slate-800">{{ __("البطاقات المتاحة") }}</h2>
<div class="flex items-center gap-2">
<button
@click="enableAll"
class="px-3 py-1.5 rounded-lg text-xs font-semibold border border-slate-300 text-slate-700 hover:bg-slate-50 transition-all"
>{{ __("تفعيل الكل") }}</button>
<button
@click="disableAll"
class="px-3 py-1.5 rounded-lg text-xs font-semibold border border-slate-300 text-slate-700 hover:bg-slate-50 transition-all"
>{{ __("إخفاء الكل") }}</button>
</div>
</div>
<div class="divide-y divide-slate-100">
<div
v-for="card in cards"
:key="card.id"
class="px-5 py-4 hover:bg-slate-50 transition-colors"
>
<div class="flex items-center justify-between gap-3">
<div class="flex items-center gap-3 min-w-0">
<div class="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0" :class="cardColors[card.id]?.bg || 'bg-slate-100'">
<svg class="w-5 h-5" :class="cardColors[card.id]?.icon || 'text-slate-500'" fill="none" stroke="currentColor" viewBox="0 0 24 24">
<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="cardColors[card.id]?.path || cardIcons[card.id] || 'M4 6h16M4 12h16M4 18h16'" />
</svg>
</div>
<div class="min-w-0">
<p class="font-semibold text-slate-800 text-sm">{{ card.label }}</p>
<p class="text-xs text-slate-500 truncate">{{ card.route }}</p>
</div>
</div>
<label class="relative inline-flex items-center cursor-pointer flex-shrink-0">
<input type="checkbox" v-model="card.enabled" class="sr-only peer" />
<div class="w-11 h-6 bg-slate-200 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:right-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
</label>
</div>

<!-- Users assignment -->
<div v-if="card.enabled" class="mt-3 pr-0 sm:pr-14">
<p class="text-xs font-medium text-slate-600 mb-2">
{{ __("المستخدمون المسموح لهم") }}
<span class="text-slate-400 font-normal">{{ __("(إذا فارغة تظهر للجميع)") }}</span>
</p>
<div class="flex flex-wrap gap-2 mb-2">
<span
v-for="u in card.users || []"
:key="u"
class="inline-flex items-center gap-1 px-2 py-1 rounded-lg bg-blue-50 border border-blue-100 text-xs text-slate-700"
>
{{ u }}
<button
@click="removeUser(card, u)"
class="text-slate-400 hover:text-rose-600 transition-colors"
aria-label="إزالة"
>
<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
</svg>
</button>
</span>
<span v-if="!(card.users || []).length" class="text-xs text-slate-400">{{ __("جميع المستخدمين") }}</span>
</div>
<div class="relative">
<input
type="text"
v-model="userSearch[card.id]"
@input="onUserSearchInput(card)"
@focus="onUserSearchInput(card)"
:placeholder="__('ابحث باسم المستخدم أو البريد')"
class="w-full sm:w-80 border border-slate-300 rounded-lg px-3 py-2 text-xs focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white transition-all"
/>
<div
v-if="(userResults[card.id] || []).length && userSearchFocused[card.id]"
class="absolute z-10 mt-1 w-full sm:w-80 bg-white border border-slate-200 rounded-lg shadow-lg max-h-48 overflow-auto"
>
<button
v-for="u in userResults[card.id]"
:key="u.name"
@click="addUser(card, u)"
class="w-full text-start px-3 py-2 text-xs hover:bg-blue-50 transition-colors border-b border-slate-50 last:border-0"
:disabled="(card.users || []).includes(u.name)"
:class="(card.users || []).includes(u.name) ? 'opacity-50 cursor-not-allowed' : ''"
>
<p class="font-medium text-slate-800">{{ u.name }}</p>
<p class="text-slate-500">{{ u.full_name }} · {{ u.email }}</p>
</button>
</div>
<div v-else-if="userSearchLoading[card.id]" class="absolute z-10 mt-1 w-full sm:w-80 bg-white border border-slate-200 rounded-lg shadow-lg p-3 text-xs text-slate-500">
{{ __("جاري البحث...") }}
</div>
</div>
</div>
</div>
</div>
</div>

<div class="flex justify-end">
<button
@click="saveSettings"
:disabled="saving"
class="px-6 py-2.5 rounded-xl text-sm font-bold text-white bg-gradient-to-l from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 shadow-lg shadow-blue-500/30 transition-all disabled:opacity-60 disabled:cursor-not-allowed flex items-center gap-2"
>
<svg v-if="saving" class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
</svg>
{{ saving ? __("جاري الحفظ...") : __("حفظ الإعدادات") }}
</button>
</div>
</template>
</template>
</main>
</div>
</template>

<script setup>
import { call } from "@/utils/apiWrapper"
import { useToast } from "@/composables/useToast"
import router from "@/router"
import { session } from "@/data/session"
import { onMounted, onBeforeUnmount, ref } from "vue"

const { showSuccess, showError } = useToast()

const isAdmin = ref(false)
const loading = ref(true)
const saving = ref(false)
const cards = ref([])

const userSearch = ref({})
const userResults = ref({})
const userSearchLoading = ref({})
const userSearchFocused = ref({})
const userSearchDebounce = ref({})

const cardIcons = {
dashboard: "M4 6h16M4 10h16M4 14h16M4 18h16",
quick_inventory: "M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4",
quick_purchase_invoice: "M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h2m-2 4h2m-2-8h2M5 7h14a2 2 0 012 2v10a2 2 0 01-2 2H5a2 2 0 01-2-2V9a2 2 0 012-2z",
customer_report: "M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z",
customer_payment: "M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z",
supplier_payment: "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z",
store_manage: "M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z",
customer_portal: "M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z",
storefront: "M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z",
}

const cardColors = {
dashboard: { bg: "bg-indigo-100", icon: "text-indigo-600", path: cardIcons.dashboard },
quick_inventory: { bg: "bg-blue-100", icon: "text-blue-600", path: cardIcons.quick_inventory },
quick_purchase_invoice: { bg: "bg-emerald-100", icon: "text-emerald-600", path: cardIcons.quick_purchase_invoice },
customer_report: { bg: "bg-emerald-100", icon: "text-emerald-600", path: cardIcons.customer_report },
customer_payment: { bg: "bg-amber-100", icon: "text-amber-600", path: cardIcons.customer_payment },
supplier_payment: { bg: "bg-purple-100", icon: "text-purple-600", path: cardIcons.supplier_payment },
store_manage: { bg: "bg-cyan-100", icon: "text-cyan-600", path: cardIcons.store_manage },
customer_portal: { bg: "bg-blue-100", icon: "text-blue-600", path: cardIcons.customer_portal },
storefront: { bg: "bg-emerald-100", icon: "text-emerald-600", path: cardIcons.storefront },
}

onMounted(async () => {
isAdmin.value = session.user === "Administrator"
if (!isAdmin.value) {
loading.value = false
return
}
await loadSettings()
document.addEventListener("click", onDocumentClick)
})

onBeforeUnmount(() => {
document.removeEventListener("click", onDocumentClick)
})

async function loadSettings() {
loading.value = true
try {
const result = await call("bs.baron_servies.api.utilities.get_bs_home_settings")
cards.value = (result?.cards || []).map((c) => ({
...c,
enabled: !!c.enabled,
users: Array.isArray(c.users) ? c.users : [],
}))
} catch (e) {
showError(e?.message || "فشل تحميل الإعدادات")
} finally {
loading.value = false
}
}

function onUserSearchInput(card) {
const id = card.id
userSearchFocused.value[id] = true
clearTimeout(userSearchDebounce.value[id])
userSearchDebounce.value[id] = setTimeout(() => doUserSearch(card), 300)
}

async function doUserSearch(card) {
const id = card.id
const term = (userSearch.value[id] || "").trim()
if (!term) {
userResults.value[id] = []
return
}
userSearchLoading.value[id] = true
try {
const result = await call("bs.baron_servies.api.utilities.search_users_for_settings", {
search_term: term,
limit: 20,
})
userResults.value[id] = Array.isArray(result?.users) ? result.users : []
} catch (e) {
userResults.value[id] = []
} finally {
userSearchLoading.value[id] = false
}
}

function addUser(card, user) {
if (!card.users) card.users = []
if (!card.users.includes(user.name)) {
card.users.push(user.name)
}
userSearch.value[card.id] = ""
userResults.value[card.id] = []
userSearchFocused.value[card.id] = false
}

function removeUser(card, userName) {
card.users = (card.users || []).filter((u) => u !== userName)
}

function onDocumentClick(e) {
for (const id in userSearchFocused.value) {
userSearchFocused.value[id] = false
}
}

function enableAll() {
cards.value.forEach((c) => (c.enabled = true))
}

function disableAll() {
cards.value.forEach((c) => (c.enabled = false))
}

async function saveSettings() {
saving.value = true
try {
const payload = JSON.stringify(cards.value, null, 2)
await call("bs.baron_servies.api.utilities.update_bs_home_settings", { cards_config: payload })
showSuccess("تم حفظ الإعدادات")
} catch (e) {
showError(e?.message || "فشل حفظ الإعدادات")
} finally {
saving.value = false
}
}

function goBack() {
router.push({ name: "Home" })
}
</script>
