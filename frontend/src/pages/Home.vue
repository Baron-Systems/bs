<template>
<div class="min-h-screen flex flex-col bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50" dir="rtl">
<!-- Header -->
<header class="bg-white/80 backdrop-blur-md border-b border-slate-200 sticky top-0 z-30 shadow-sm">
<div class="max-w-7xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between gap-3">
<div class="flex items-center gap-3 min-w-0">
<div class="w-11 h-11 bg-gradient-to-br from-blue-600 to-indigo-700 rounded-xl flex items-center justify-center flex-shrink-0 shadow-lg shadow-blue-500/30">
<svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M13 10V3L4 14h7v7l9-11h-7z" />
</svg>
</div>
<div class="min-w-0">
<h1 class="text-base sm:text-lg font-bold text-slate-900 truncate">
{{ __("خدمات Baron") }}
</h1>
<p class="text-xs text-slate-500 truncate">
{{ __("اختر الخدمة للبدء") }}
</p>
</div>
</div>
<div class="flex items-center gap-2 flex-shrink-0">
<div class="hidden sm:flex items-center gap-2 bg-slate-100 rounded-full px-3 py-1.5">
<div class="w-7 h-7 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center text-white text-xs font-bold">
{{ userInitial }}
</div>
<span class="text-xs font-medium text-slate-700">{{ userName }}</span>
</div>
<button
@click="logout"
class="p-2 rounded-xl text-slate-600 hover:bg-red-50 hover:text-red-600 transition-all hover:scale-105 active:scale-95"
:aria-label="__('تسجيل الخروج')"
:title="__('تسجيل الخروج')"
>
<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
</svg>
</button>
</div>
</div>
</header>

<!-- Main Content -->
<main class="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-8 sm:py-12">
<!-- Title Section -->
<div class="mb-8 text-center sm:text-start">
<h2 class="text-2xl sm:text-3xl font-extrabold bg-gradient-to-l from-blue-700 via-indigo-700 to-purple-700 bg-clip-text text-transparent">
{{ __("الخدمات المتاحة") }}
</h2>
<p class="text-sm sm:text-base text-slate-600 mt-2">{{ __("اختر الخدمة التي تريد استخدامها") }}</p>
</div>

<!-- Loading -->
<div v-if="loading" class="flex items-center justify-center py-20">
<div class="flex flex-col items-center gap-3">
<svg class="animate-spin h-10 w-10 text-blue-600" fill="none" viewBox="0 0 24 24">
<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
</svg>
<p class="text-slate-500 text-sm">{{ __("جاري تحميل الخدمات...") }}</p>
</div>
</div>

<!-- Empty state -->
<div v-else-if="!enabledCards.length && !isAdmin" class="text-center py-20 bg-white rounded-2xl border border-slate-200 shadow-sm">
<svg class="w-16 h-16 text-slate-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
</svg>
<p class="text-slate-600 font-medium">{{ __("لا توجد خدمات متاحة لك حالياً") }}</p>
</div>

<!-- Services Grid -->
<div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5 sm:gap-6">
<component
:is="card.type === 'link' ? 'a' : 'button'"
v-for="card in enabledCards"
:key="card.id"
:href="card.type === 'link' ? card.route : undefined"
@click="card.type === 'route' ? goTo(card.route) : undefined"
class="group relative overflow-hidden bg-white rounded-2xl border border-slate-200 shadow-md p-6 text-start hover:shadow-xl transition-all duration-300 hover:-translate-y-1"
:class="cardMeta[card.id]?.borderHover || 'hover:border-blue-400'"
>
<div class="absolute -top-8 -left-8 w-32 h-32 rounded-full blur-2xl transition-colors" :class="cardMeta[card.id]?.blur || 'bg-slate-500/10 group-hover:bg-slate-500/20'"></div>
<div class="relative">
<div class="flex items-start justify-between mb-4">
<div class="w-14 h-14 rounded-2xl flex items-center justify-center shadow-lg transition-transform group-hover:scale-110" :class="cardMeta[card.id]?.iconBg || 'bg-gradient-to-br from-slate-500 to-slate-700'">
<svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="cardMeta[card.id]?.path || 'M4 6h16M4 12h16M4 18h16'" />
</svg>
</div>
<svg class="w-5 h-5 text-slate-300 transition-all" :class="cardMeta[card.id]?.arrowHover || 'group-hover:text-slate-600 group-hover:-translate-x-1'" fill="none" stroke="currentColor" viewBox="0 0 24 24">
<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 19l-7-7 7-7" />
</svg>
</div>
<h3 class="text-lg font-bold text-slate-900 mb-1.5">{{ card.label }}</h3>
<p class="text-sm text-slate-600 leading-relaxed">{{ cardMeta[card.id]?.description || '' }}</p>
</div>
</component>

<!-- Settings card (admin only) -->
<button
v-if="isAdmin"
@click="goTo('Settings')"
class="group relative overflow-hidden bg-white rounded-2xl border border-slate-200 shadow-md p-6 text-start hover:shadow-xl hover:border-slate-400 transition-all duration-300 hover:-translate-y-1"
>
<div class="absolute -top-8 -left-8 w-32 h-32 bg-slate-500/10 rounded-full blur-2xl group-hover:bg-slate-500/20 transition-colors"></div>
<div class="relative">
<div class="flex items-start justify-between mb-4">
<div class="w-14 h-14 bg-gradient-to-br from-slate-500 to-slate-700 rounded-2xl flex items-center justify-center shadow-lg shadow-slate-500/40 group-hover:scale-110 transition-transform">
<svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
</svg>
</div>
<svg class="w-5 h-5 text-slate-300 group-hover:text-slate-600 group-hover:-translate-x-1 transition-all" fill="none" stroke="currentColor" viewBox="0 0 24 24">
<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 19l-7-7 7-7" />
</svg>
</div>
<h3 class="text-lg font-bold text-slate-900 mb-1.5">{{ __("إعدادات الصفحة الرئيسية") }}</h3>
<p class="text-sm text-slate-600 leading-relaxed">{{ __("تفعيل/إخفاء البطاقات وتحديد المستخدمين المسموح لهم") }}</p>
</div>
</button>
</div>
</main>

<!-- Footer -->
<footer class="border-t border-slate-200 py-4 bg-white/50">
<div class="max-w-7xl mx-auto px-4 sm:px-6 text-center text-xs text-slate-500 font-medium">
{{ __("AL Baron Systems") }} &copy; {{ new Date().getFullYear() }}
</div>
</footer>
</div>
</template>

<script setup>
import { useUserData } from "@/data/user"
import { session } from "@/data/session"
import { call } from "@/utils/apiWrapper"
import { useToast } from "@/composables/useToast"
import router from "@/router"
import { computed, onMounted, ref } from "vue"

const { userName } = useUserData()
const { showError } = useToast()

const loading = ref(true)
const cards = ref([])

const isAdmin = computed(() => session.user === "Administrator")

const userInitial = computed(() => {
const name = userName.value || "User"
const parts = String(name).split(" ").filter(Boolean)
return parts.length >= 2 ? (parts[0][0] + parts[1][0]).toUpperCase() : name.substring(0, 2).toUpperCase()
})

const cardMeta = {
dashboard: {
borderHover: "hover:border-indigo-400",
blur: "bg-indigo-500/10 group-hover:bg-indigo-500/20",
iconBg: "bg-gradient-to-br from-indigo-500 to-purple-700 shadow-indigo-500/40",
arrowHover: "group-hover:text-indigo-600 group-hover:-translate-x-1",
path: "M4 6h16M4 10h16M4 14h16M4 18h16",
description: __("ملخص شامل للمحل: المبيعات، المشتريات، التدفقات النقدية، أفضل الأصناف والعملاء"),
},
quick_inventory: {
borderHover: "hover:border-blue-400",
blur: "bg-blue-500/10 group-hover:bg-blue-500/20",
iconBg: "bg-gradient-to-br from-blue-500 to-blue-700 shadow-blue-500/40",
arrowHover: "group-hover:text-blue-600 group-hover:-translate-x-1",
path: "M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4",
description: __("إنشاء سجل جرد مخزون أول المدة كمسودة بسرعة وسهولة"),
},
quick_purchase_invoice: {
borderHover: "hover:border-emerald-400",
blur: "bg-emerald-500/10 group-hover:bg-emerald-500/20",
iconBg: "bg-gradient-to-br from-emerald-500 to-teal-700 shadow-emerald-500/40",
arrowHover: "group-hover:text-emerald-600 group-hover:-translate-x-1",
path: "M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h2m-2 4h2m-2-8h2M5 7h14a2 2 0 012 2v10a2 2 0 01-2 2H5a2 2 0 01-2-2V9a2 2 0 012-2z",
description: __("إنشاء فاتورة شراء كمسودة مع إمكانية تحديث سعر الشراء"),
},
customer_report: {
borderHover: "hover:border-emerald-400",
blur: "bg-emerald-500/10 group-hover:bg-emerald-500/20",
iconBg: "bg-gradient-to-br from-emerald-500 to-green-700 shadow-emerald-500/40",
arrowHover: "group-hover:text-emerald-600 group-hover:-translate-x-1",
path: "M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z",
description: __("عرض شامل لبيانات العميل: المبيعات، الفواتير، المدفوعات والمستحقات"),
},
customer_payment: {
borderHover: "hover:border-amber-400",
blur: "bg-amber-500/10 group-hover:bg-amber-500/20",
iconBg: "bg-gradient-to-br from-amber-500 to-orange-600 shadow-amber-500/40",
arrowHover: "group-hover:text-amber-600 group-hover:-translate-x-1",
path: "M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z",
description: __("قبض من العميل أو الدفع له مع كشف حساب مفصل"),
},
supplier_payment: {
borderHover: "hover:border-purple-400",
blur: "bg-purple-500/10 group-hover:bg-purple-500/20",
iconBg: "bg-gradient-to-br from-purple-500 to-fuchsia-700 shadow-purple-500/40",
arrowHover: "group-hover:text-purple-600 group-hover:-translate-x-1",
path: "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z",
description: __("الدفع للمورد أو القبض منه مع كشف حساب مفصل"),
},
store_manage: {
borderHover: "hover:border-cyan-400",
blur: "bg-cyan-500/10 group-hover:bg-cyan-500/20",
iconBg: "bg-gradient-to-br from-cyan-500 to-blue-700 shadow-cyan-500/40",
arrowHover: "group-hover:text-cyan-600 group-hover:-translate-x-1",
path: "M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z",
description: __("تحديد أصناف المتجر، رفع البنر، تفعيل/تعطيل، مناطق وأسعار التوصيل"),
},
customer_portal: {
borderHover: "hover:border-blue-400",
blur: "bg-blue-500/10 group-hover:bg-blue-500/20",
iconBg: "bg-gradient-to-br from-blue-500 to-indigo-700 shadow-blue-500/40",
arrowHover: "group-hover:text-blue-600 group-hover:-translate-x-1",
path: "M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z",
description: __("دخول العملاء لعرض كشف الحساب والرصيد"),
},
storefront: {
borderHover: "hover:border-emerald-400",
blur: "bg-emerald-500/10 group-hover:bg-emerald-500/20",
iconBg: "bg-gradient-to-br from-emerald-500 to-green-700 shadow-emerald-500/40",
arrowHover: "group-hover:text-emerald-600 group-hover:-translate-x-1",
path: "M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z",
description: __("تصفح المنتجات، البحث، السلة، إنشاء طلب — متاح للعملاء بدون تسجيل دخول"),
},
}

const enabledCards = computed(() => {
const user = session.user
const admin = user === "Administrator"
return (cards.value || []).filter((c) => {
if (!c.enabled || !cardMeta[c.id]) return false
if (admin) return true
const allowed = Array.isArray(c.users) ? c.users : []
if (allowed.length) return allowed.includes(user)
return true
})
})

onMounted(async () => {
if (!session.isLoggedIn) {
router.replace({ name: "Login" })
return
}
await loadSettings()
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
showError(e?.message || __("فشل تحميل الإعدادات"))
} finally {
loading.value = false
}
}

function goTo(name) {
router.push({ name })
}

async function logout() {
await session.logout.submit()
}
</script>
