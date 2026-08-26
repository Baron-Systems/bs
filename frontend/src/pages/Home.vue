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

			<!-- Services Grid -->
			<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5 sm:gap-6">
				<!-- Service 0: Dashboard -->
				<button
					@click="goTo('Dashboard')"
					class="group relative overflow-hidden bg-white rounded-2xl border border-slate-200 shadow-md p-6 text-start hover:shadow-xl hover:border-indigo-400 transition-all duration-300 hover:-translate-y-1"
				>
					<div class="absolute -top-8 -left-8 w-32 h-32 bg-indigo-500/10 rounded-full blur-2xl group-hover:bg-indigo-500/20 transition-colors"></div>
					<div class="relative">
						<div class="flex items-start justify-between mb-4">
							<div class="w-14 h-14 bg-gradient-to-br from-indigo-500 to-purple-700 rounded-2xl flex items-center justify-center shadow-lg shadow-indigo-500/40 group-hover:scale-110 transition-transform">
								<svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h16M4 18h16" />
								</svg>
							</div>
							<svg class="w-5 h-5 text-slate-300 group-hover:text-indigo-600 group-hover:-translate-x-1 transition-all" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 19l-7-7 7-7" />
							</svg>
						</div>
						<h3 class="text-lg font-bold text-slate-900 mb-1.5">{{ __("لوحة المعلومات") }}</h3>
						<p class="text-sm text-slate-600 leading-relaxed">{{ __("ملخص شامل للمحل: المبيعات، المشتريات، التدفقات النقدية، أفضل الأصناف والعملاء") }}</p>
					</div>
				</button>

				<!-- Service 1: Quick Inventory -->
				<button
					@click="goTo('QuickInventory')"
					class="group relative overflow-hidden bg-white rounded-2xl border border-slate-200 shadow-md p-6 text-start hover:shadow-xl hover:border-blue-400 transition-all duration-300 hover:-translate-y-1"
				>
					<div class="absolute -top-8 -left-8 w-32 h-32 bg-blue-500/10 rounded-full blur-2xl group-hover:bg-blue-500/20 transition-colors"></div>
					<div class="relative">
						<div class="flex items-start justify-between mb-4">
							<div class="w-14 h-14 bg-gradient-to-br from-blue-500 to-blue-700 rounded-2xl flex items-center justify-center shadow-lg shadow-blue-500/40 group-hover:scale-110 transition-transform">
								<svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
								</svg>
							</div>
							<svg class="w-5 h-5 text-slate-300 group-hover:text-blue-600 group-hover:-translate-x-1 transition-all" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 19l-7-7 7-7" />
							</svg>
						</div>
						<h3 class="text-lg font-bold text-slate-900 mb-1.5">{{ __("جرد سريع") }}</h3>
						<p class="text-sm text-slate-600 leading-relaxed">{{ __("إنشاء سجل جرد مخزون أول المدة كمسودة بسرعة وسهولة") }}</p>
					</div>
				</button>

				<!-- Service 2: Customer Report -->
				<button
					@click="goTo('CustomerReport')"
					class="group relative overflow-hidden bg-white rounded-2xl border border-slate-200 shadow-md p-6 text-start hover:shadow-xl hover:border-emerald-400 transition-all duration-300 hover:-translate-y-1"
				>
					<div class="absolute -top-8 -left-8 w-32 h-32 bg-emerald-500/10 rounded-full blur-2xl group-hover:bg-emerald-500/20 transition-colors"></div>
					<div class="relative">
						<div class="flex items-start justify-between mb-4">
							<div class="w-14 h-14 bg-gradient-to-br from-emerald-500 to-green-700 rounded-2xl flex items-center justify-center shadow-lg shadow-emerald-500/40 group-hover:scale-110 transition-transform">
								<svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
								</svg>
							</div>
							<svg class="w-5 h-5 text-slate-300 group-hover:text-emerald-600 group-hover:-translate-x-1 transition-all" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 19l-7-7 7-7" />
							</svg>
						</div>
						<h3 class="text-lg font-bold text-slate-900 mb-1.5">{{ __("تقرير العميل مفصل") }}</h3>
						<p class="text-sm text-slate-600 leading-relaxed">{{ __("عرض شامل لبيانات العميل: المبيعات، الفواتير، المدفوعات والمستحقات") }}</p>
					</div>
				</button>

				<!-- Service 3: Customer Payment -->
				<button
					@click="goTo('CustomerPayment')"
					class="group relative overflow-hidden bg-white rounded-2xl border border-slate-200 shadow-md p-6 text-start hover:shadow-xl hover:border-amber-400 transition-all duration-300 hover:-translate-y-1"
				>
					<div class="absolute -top-8 -left-8 w-32 h-32 bg-amber-500/10 rounded-full blur-2xl group-hover:bg-amber-500/20 transition-colors"></div>
					<div class="relative">
						<div class="flex items-start justify-between mb-4">
							<div class="w-14 h-14 bg-gradient-to-br from-amber-500 to-orange-600 rounded-2xl flex items-center justify-center shadow-lg shadow-amber-500/40 group-hover:scale-110 transition-transform">
								<svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
								</svg>
							</div>
							<svg class="w-5 h-5 text-slate-300 group-hover:text-amber-600 group-hover:-translate-x-1 transition-all" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 19l-7-7 7-7" />
							</svg>
						</div>
						<h3 class="text-lg font-bold text-slate-900 mb-1.5">{{ __("دفع العميل") }}</h3>
						<p class="text-sm text-slate-600 leading-relaxed">{{ __("قبض من العميل أو الدفع له مع كشف حساب مفصل") }}</p>
					</div>
				</button>

				<!-- Service 4: Supplier Payment -->
				<button
					@click="goTo('SupplierPayment')"
					class="group relative overflow-hidden bg-white rounded-2xl border border-slate-200 shadow-md p-6 text-start hover:shadow-xl hover:border-purple-400 transition-all duration-300 hover:-translate-y-1"
				>
					<div class="absolute -top-8 -left-8 w-32 h-32 bg-purple-500/10 rounded-full blur-2xl group-hover:bg-purple-500/20 transition-colors"></div>
					<div class="relative">
						<div class="flex items-start justify-between mb-4">
							<div class="w-14 h-14 bg-gradient-to-br from-purple-500 to-fuchsia-700 rounded-2xl flex items-center justify-center shadow-lg shadow-purple-500/40 group-hover:scale-110 transition-transform">
								<svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
								</svg>
							</div>
							<svg class="w-5 h-5 text-slate-300 group-hover:text-purple-600 group-hover:-translate-x-1 transition-all" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 19l-7-7 7-7" />
							</svg>
						</div>
						<h3 class="text-lg font-bold text-slate-900 mb-1.5">{{ __("دفع المورد") }}</h3>
						<p class="text-sm text-slate-600 leading-relaxed">{{ __("الدفع للمورد أو القبض منه مع كشف حساب مفصل") }}</p>
					</div>
				</button>

				<!-- Service 5: Store Management -->
				<button
					@click="goTo('StoreManage')"
					class="group relative overflow-hidden bg-white rounded-2xl border border-slate-200 shadow-md p-6 text-start hover:shadow-xl hover:border-cyan-400 transition-all duration-300 hover:-translate-y-1"
				>
					<div class="absolute -top-8 -left-8 w-32 h-32 bg-cyan-500/10 rounded-full blur-2xl group-hover:bg-cyan-500/20 transition-colors"></div>
					<div class="relative">
						<div class="flex items-start justify-between mb-4">
							<div class="w-14 h-14 bg-gradient-to-br from-cyan-500 to-blue-700 rounded-2xl flex items-center justify-center shadow-lg shadow-cyan-500/40 group-hover:scale-110 transition-transform">
								<svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
								</svg>
							</div>
							<svg class="w-5 h-5 text-slate-300 group-hover:text-cyan-600 group-hover:-translate-x-1 transition-all" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 19l-7-7 7-7" />
							</svg>
						</div>
						<h3 class="text-lg font-bold text-slate-900 mb-1.5">{{ __("\u0625\u062f\u0627\u0631\u0629 \u0627\u0644\u0645\u062a\u062c\u0631") }}</h3>
						<p class="text-sm text-slate-600 leading-relaxed">{{ __("\u062a\u062d\u062f\u064a\u062f \u0623\u0635\u0646\u0627\u0641 \u0627\u0644\u0645\u062a\u062c\u0631\u060c \u0631\u0641\u0639 \u0627\u0644\u0628\u0646\u0631\u060c \u062a\u0641\u0639\u064a\u0644/\u062a\u0639\u0637\u064a\u0644\u060c \u0645\u0646\u0627\u0637\u0642 \u0648\u0623\u0633\u0639\u0627\u0631 \u0627\u0644\u062a\u0648\u0635\u064a\u0644") }}</p>
					</div>
				</button>

				<!-- Service 6: Storefront (Public) -->
				<a
					href="/bs/store"
					class="group relative overflow-hidden bg-white rounded-2xl border border-slate-200 shadow-md p-6 text-start hover:shadow-xl hover:border-emerald-400 transition-all duration-300 hover:-translate-y-1"
				>
					<div class="absolute -top-8 -left-8 w-32 h-32 bg-emerald-500/10 rounded-full blur-2xl group-hover:bg-emerald-500/20 transition-colors"></div>
					<div class="relative">
						<div class="flex items-start justify-between mb-4">
							<div class="w-14 h-14 bg-gradient-to-br from-emerald-500 to-green-700 rounded-2xl flex items-center justify-center shadow-lg shadow-emerald-500/40 group-hover:scale-110 transition-transform">
								<svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
								</svg>
							</div>
							<svg class="w-5 h-5 text-slate-300 group-hover:text-emerald-600 group-hover:-translate-x-1 transition-all" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 19l-7-7 7-7" />
							</svg>
						</div>
						<h3 class="text-lg font-bold text-slate-900 mb-1.5">{{ __("\u0627\u0644\u0645\u062a\u062c\u0631") }}</h3>
						<p class="text-sm text-slate-600 leading-relaxed">{{ __("\u062a\u0635\u0641\u062d \u0627\u0644\u0645\u0646\u062a\u062c\u0627\u062a\u060c \u0627\u0644\u0628\u062d\u062b\u060c \u0627\u0644\u0633\u0644\u0629\u060c \u0625\u0646\u0634\u0627\u0621 \u0637\u0644\u0628 \u2014 \u0645\u062a\u0627\u062d \u0644\u0644\u0639\u0645\u0644\u0627\u0621 \u0628\u062f\u0648\u0646 \u062a\u0633\u062c\u064a\u0644 \u062f\u062e\u0648\u0644") }}</p>
					</div>
				</a>
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
import router from "@/router"
import { computed, onMounted } from "vue"

const { userName } = useUserData()

const userInitial = computed(() => {
	const name = userName.value || "User"
	const parts = String(name).split(" ").filter(Boolean)
	return parts.length >= 2 ? (parts[0][0] + parts[1][0]).toUpperCase() : name.substring(0, 2).toUpperCase()
})

onMounted(() => {
	if (!session.isLoggedIn) {
		router.replace({ name: "Login" })
	}
})

function goTo(name) {
	router.push({ name })
}

async function logout() {
	await session.logout.submit()
}
</script>
