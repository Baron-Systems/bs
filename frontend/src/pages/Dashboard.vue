<template>
	<div class="min-h-screen flex flex-col bg-gradient-to-br from-slate-50 via-indigo-50 to-purple-50" dir="rtl">
		<!-- Header -->
		<header class="bg-white/80 backdrop-blur-md border-b border-slate-200 sticky top-0 z-30 shadow-sm">
			<div class="max-w-7xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between gap-3">
				<div class="flex items-center gap-3 min-w-0">
					<button
						@click="goBack"
						class="p-2 rounded-xl text-slate-600 hover:bg-slate-100 transition-all hover:scale-105 active:scale-95 flex-shrink-0"
						:aria-label="__('رجوع')"
					>
						<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
						</svg>
					</button>
					<div class="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-700 rounded-xl flex items-center justify-center flex-shrink-0 shadow-lg shadow-indigo-500/30">
						<svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h16M4 18h16" />
						</svg>
					</div>
					<div class="min-w-0">
						<h1 class="text-base sm:text-lg font-bold text-slate-900 truncate">
							{{ __("لوحة المعلومات") }}
						</h1>
						<p class="text-xs text-slate-500 truncate">
							{{ __("ملخص شامل للمحل - المبيعات والمشتريات والتدفقات") }}
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
		<main class="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-4 sm:py-6 flex flex-col gap-4">
			<!-- Filters Bar -->
			<section class="bg-white rounded-2xl border border-slate-200 shadow-md p-4">
				<div class="flex flex-col sm:flex-row gap-3 items-end">
					<div class="flex-1 w-full">
						<label class="block text-xs font-semibold text-slate-700 mb-1.5">{{ __("الشركة") }}</label>
						<select
							v-model="selectedCompany"
							class="w-full border border-slate-300 rounded-xl px-3 py-2.5 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 bg-white transition-all"
							:disabled="loadingCompanies"
							@change="loadData"
						>
							<option value="" disabled>{{ loadingCompanies ? __("جاري التحميل...") : __("اختر الشركة") }}</option>
							<option v-for="c in companies" :key="c.name" :value="c.name">{{ c.name }}</option>
						</select>
					</div>
					<div class="w-full sm:w-44">
						<label class="block text-xs font-semibold text-slate-700 mb-1.5">{{ __("من تاريخ") }}</label>
						<input
							v-model="fromDate"
							type="date"
							class="w-full border border-slate-300 rounded-xl px-3 py-2.5 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 bg-white transition-all"
							@change="loadData"
						/>
					</div>
					<div class="w-full sm:w-44">
						<label class="block text-xs font-semibold text-slate-700 mb-1.5">{{ __("إلى تاريخ") }}</label>
						<input
							v-model="toDate"
							type="date"
							class="w-full border border-slate-300 rounded-xl px-3 py-2.5 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 bg-white transition-all"
							@change="loadData"
						/>
					</div>
					<div class="flex gap-2">
						<button @click="setPeriod(30)" class="px-3 py-2 rounded-lg text-xs font-semibold border border-slate-300 text-slate-700 hover:bg-slate-50 transition-all whitespace-nowrap">{{ __("30 يوم") }}</button>
						<button @click="setPeriod(90)" class="px-3 py-2 rounded-lg text-xs font-semibold border border-slate-300 text-slate-700 hover:bg-slate-50 transition-all whitespace-nowrap">{{ __("90 يوم") }}</button>
						<button @click="setPeriod(180)" class="px-3 py-2 rounded-lg text-xs font-semibold border border-slate-300 text-slate-700 hover:bg-slate-50 transition-all whitespace-nowrap">{{ __("6 أشهر") }}</button>
					</div>
				</div>
			</section>

			<!-- Loading State -->
			<div v-if="loading" class="flex items-center justify-center py-20">
				<div class="flex flex-col items-center gap-3">
					<svg class="animate-spin h-10 w-10 text-indigo-600" fill="none" viewBox="0 0 24 24">
						<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
						<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
					</svg>
					<p class="text-sm text-slate-500">{{ __("جاري تحميل البيانات...") }}</p>
				</div>
			</div>

			<template v-else-if="data">
				<!-- KPI Cards -->
				<div class="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
					<!-- Total Sales -->
					<div class="bg-gradient-to-br from-blue-500 to-blue-700 rounded-2xl p-4 sm:p-5 shadow-lg shadow-blue-500/30 text-white">
						<div class="flex items-center justify-between mb-2">
							<div class="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center">
								<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3v18h18M7 14l4-4 4 4 5-5" />
								</svg>
							</div>
						</div>
						<p class="text-xs font-medium text-blue-100">{{ __("إجمالي المبيعات") }}</p>
						<p class="text-xl sm:text-2xl font-extrabold mt-1 truncate">{{ formatCurrency(data.summary.total_sales) }}</p>
					</div>

					<!-- Total Purchases -->
					<div class="bg-gradient-to-br from-purple-500 to-fuchsia-700 rounded-2xl p-4 sm:p-5 shadow-lg shadow-purple-500/30 text-white">
						<div class="flex items-center justify-between mb-2">
							<div class="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center">
								<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3v18h18M17 10l-4 4-4-4-5 5" />
								</svg>
							</div>
						</div>
						<p class="text-xs font-medium text-purple-100">{{ __("إجمالي المشتريات") }}</p>
						<p class="text-xl sm:text-2xl font-extrabold mt-1 truncate">{{ formatCurrency(data.summary.total_purchases) }}</p>
					</div>

					<!-- Net Cash -->
					<div class="bg-gradient-to-br from-emerald-500 to-green-700 rounded-2xl p-4 sm:p-5 shadow-lg shadow-emerald-500/30 text-white">
						<div class="flex items-center justify-between mb-2">
							<div class="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center">
								<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
								</svg>
							</div>
						</div>
						<p class="text-xs font-medium text-emerald-100">{{ __("صافي التدفق النقدي") }}</p>
						<p class="text-xl sm:text-2xl font-extrabold mt-1 truncate">{{ formatCurrency(data.summary.net_cash) }}</p>
					</div>

					<!-- Gross Profit -->
					<div class="bg-gradient-to-br from-amber-500 to-orange-600 rounded-2xl p-4 sm:p-5 shadow-lg shadow-amber-500/30 text-white">
						<div class="flex items-center justify-between mb-2">
							<div class="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center">
								<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
								</svg>
							</div>
						</div>
						<p class="text-xs font-medium text-amber-100">{{ __("إجمالي الربح") }}</p>
						<p class="text-xl sm:text-2xl font-extrabold mt-1 truncate">{{ formatCurrency(data.summary.gross_profit) }}</p>
					</div>
				</div>

				<!-- Secondary KPIs -->
				<div class="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
					<div class="bg-white rounded-2xl border border-slate-200 shadow-md p-4">
						<div class="flex items-center gap-2 mb-1">
							<div class="w-8 h-8 bg-emerald-100 rounded-lg flex items-center justify-center">
								<svg class="w-5 h-5 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 11l5-5m0 0l5 5m-5-5v12" />
								</svg>
							</div>
							<p class="text-xs font-semibold text-slate-600">{{ __("مدفوعات واردة") }}</p>
						</div>
						<p class="text-lg font-bold text-emerald-700">{{ formatCurrency(data.summary.total_payments_in) }}</p>
					</div>
					<div class="bg-white rounded-2xl border border-slate-200 shadow-md p-4">
						<div class="flex items-center gap-2 mb-1">
							<div class="w-8 h-8 bg-rose-100 rounded-lg flex items-center justify-center">
								<svg class="w-5 h-5 text-rose-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 13l-5 5m0 0l-5-5m5 5V6" />
								</svg>
							</div>
							<p class="text-xs font-semibold text-slate-600">{{ __("مدفوعات صادرة") }}</p>
						</div>
						<p class="text-lg font-bold text-rose-700">{{ formatCurrency(data.summary.total_payments_out) }}</p>
					</div>
					<div class="bg-white rounded-2xl border border-slate-200 shadow-md p-4">
						<div class="flex items-center gap-2 mb-1">
							<div class="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
								<svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
								</svg>
							</div>
							<p class="text-xs font-semibold text-slate-600">{{ __("مستحقات العملاء") }}</p>
						</div>
						<p class="text-lg font-bold text-blue-700">{{ formatCurrency(data.summary.outstanding_receivable) }}</p>
					</div>
					<div class="bg-white rounded-2xl border border-slate-200 shadow-md p-4">
						<div class="flex items-center gap-2 mb-1">
							<div class="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">
								<svg class="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
								</svg>
							</div>
							<p class="text-xs font-semibold text-slate-600">{{ __("مستحقات للموردين") }}</p>
						</div>
						<p class="text-lg font-bold text-purple-700">{{ formatCurrency(data.summary.outstanding_payable) }}</p>
					</div>
				</div>

				<!-- Charts Row -->
				<div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
					<!-- Sales vs Purchases Trend -->
					<div class="lg:col-span-2 bg-white rounded-2xl border border-slate-200 shadow-md p-4 sm:p-5">
						<h3 class="text-sm font-bold text-slate-800 mb-4 flex items-center gap-2">
							<svg class="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
							</svg>
							{{ __("المبيعات مقابل المشتريات (شهري)") }}
						</h3>
						<div style="height: 300px;" dir="ltr">
							<Line v-if="data.sales_by_month.length" :data="salesChartConfig" :options="lineChartOptions" />
							<div v-else class="flex items-center justify-center h-full text-sm text-slate-400">{{ __("لا توجد بيانات") }}</div>
						</div>
					</div>

					<!-- Payments by Mode -->
					<div class="bg-white rounded-2xl border border-slate-200 shadow-md p-4 sm:p-5">
						<h3 class="text-sm font-bold text-slate-800 mb-4 flex items-center gap-2">
							<svg class="w-5 h-5 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 3.055A5.001 5.001 0 005.055 9H11V3.055zM13 3.055V9h5.945A5.001 5.001 0 0013 3.055zM11 11H5.055A5.001 5.001 0 0011 14.945V11zM13 11v3.945A5.001 5.001 0 0018.945 11H13z" />
							</svg>
							{{ __("المدفوعات حسب الطريقة") }}
						</h3>
						<div style="height: 300px;" dir="ltr">
							<Doughnut v-if="data.payments_by_mode.length" :data="paymentsChartConfig" :options="doughnutOptions" />
							<div v-else class="flex items-center justify-center h-full text-sm text-slate-400">{{ __("لا توجد بيانات") }}</div>
						</div>
					</div>
				</div>

				<!-- Top Items & Top Customers -->
				<div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
					<!-- Top Items -->
					<div class="bg-white rounded-2xl border border-slate-200 shadow-md p-4 sm:p-5">
						<h3 class="text-sm font-bold text-slate-800 mb-4 flex items-center gap-2">
							<svg class="w-5 h-5 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
							</svg>
							{{ __("أفضل الأصناف مبيعاً") }}
						</h3>
						<div class="space-y-2">
							<div v-for="(item, idx) in data.top_items" :key="item.item_code" class="flex items-center gap-3 p-2 rounded-xl hover:bg-slate-50 transition-colors">
								<div class="w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold flex-shrink-0"
									:class="idx === 0 ? 'bg-amber-100 text-amber-700' : idx === 1 ? 'bg-slate-200 text-slate-700' : idx === 2 ? 'bg-orange-100 text-orange-700' : 'bg-slate-100 text-slate-500'">
									{{ idx + 1 }}
								</div>
								<div class="flex-1 min-w-0">
									<p class="text-sm font-semibold text-slate-900 truncate">{{ item.item_name || item.item_code }}</p>
									<p class="text-xs text-slate-500">{{ __("الكمية") }}: {{ item.qty }}</p>
								</div>
								<p class="text-sm font-bold text-emerald-700 flex-shrink-0">{{ formatCurrency(item.amount) }}</p>
							</div>
							<div v-if="!data.top_items.length" class="text-center py-6 text-sm text-slate-400">{{ __("لا توجد بيانات") }}</div>
						</div>
					</div>

					<!-- Top Customers -->
					<div class="bg-white rounded-2xl border border-slate-200 shadow-md p-4 sm:p-5">
						<h3 class="text-sm font-bold text-slate-800 mb-4 flex items-center gap-2">
							<svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
							</svg>
							{{ __("أفضل العملاء") }}
						</h3>
						<div class="space-y-2">
							<div v-for="(cust, idx) in data.top_customers" :key="cust.customer" class="flex items-center gap-3 p-2 rounded-xl hover:bg-slate-50 transition-colors">
								<div class="w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold flex-shrink-0"
									:class="idx === 0 ? 'bg-blue-100 text-blue-700' : idx === 1 ? 'bg-slate-200 text-slate-700' : idx === 2 ? 'bg-indigo-100 text-indigo-700' : 'bg-slate-100 text-slate-500'">
									{{ idx + 1 }}
								</div>
								<div class="flex-1 min-w-0">
									<p class="text-sm font-semibold text-slate-900 truncate">{{ cust.customer }}</p>
									<p class="text-xs text-slate-500">{{ __("عدد الفواتير") }}: {{ cust.invoices }}</p>
								</div>
								<p class="text-sm font-bold text-blue-700 flex-shrink-0">{{ formatCurrency(cust.total) }}</p>
							</div>
							<div v-if="!data.top_customers.length" class="text-center py-6 text-sm text-slate-400">{{ __("لا توجد بيانات") }}</div>
						</div>
					</div>
				</div>

				<!-- Bottom Items & Low Stock -->
				<div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
					<!-- Least Selling Items -->
					<div class="bg-white rounded-2xl border border-slate-200 shadow-md p-4 sm:p-5">
						<h3 class="text-sm font-bold text-slate-800 mb-4 flex items-center gap-2">
							<svg class="w-5 h-5 text-rose-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 17h8m0 0V9m0 8l-8-8-4 4-2-2" />
							</svg>
							{{ __("أقل الأصناف مبيعاً") }}
						</h3>
						<div class="space-y-2">
							<div v-for="(item, idx) in data.bottom_items" :key="item.item_code" class="flex items-center gap-3 p-2 rounded-xl hover:bg-rose-50 transition-colors">
								<div class="w-8 h-8 bg-rose-100 rounded-lg flex items-center justify-center text-xs font-bold text-rose-700 flex-shrink-0">
									{{ idx + 1 }}
								</div>
								<div class="flex-1 min-w-0">
									<p class="text-sm font-semibold text-slate-900 truncate">{{ item.item_name || item.item_code }}</p>
									<p class="text-xs text-slate-500">{{ __("الكمية") }}: {{ item.qty }}</p>
								</div>
								<p class="text-sm font-bold text-rose-700 flex-shrink-0">{{ formatCurrency(item.amount) }}</p>
							</div>
							<div v-if="!data.bottom_items.length" class="text-center py-6 text-sm text-slate-400">{{ __("لا توجد بيانات") }}</div>
						</div>
					</div>

					<!-- Low Stock Items -->
					<div class="bg-white rounded-2xl border border-slate-200 shadow-md p-4 sm:p-5">
						<h3 class="text-sm font-bold text-slate-800 mb-4 flex items-center gap-2">
							<svg class="w-5 h-5 text-rose-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
							</svg>
							{{ __("أصناف منخفضة المخزون") }}
						</h3>
						<div class="space-y-2">
							<div v-for="item in data.low_stock_items" :key="item.item_code" class="flex items-center gap-3 p-2 rounded-xl hover:bg-rose-50 transition-colors border border-rose-100">
								<div class="w-8 h-8 bg-rose-100 rounded-lg flex items-center justify-center flex-shrink-0">
									<svg class="w-5 h-5 text-rose-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
									</svg>
								</div>
								<div class="flex-1 min-w-0">
									<p class="text-sm font-semibold text-slate-900 truncate">{{ item.item_name || item.item_code }}</p>
									<p class="text-xs text-slate-500">{{ item.stock_uom }}</p>
								</div>
								<p class="text-sm font-bold flex-shrink-0" :class="item.actual_qty <= 0 ? 'text-rose-600' : 'text-amber-600'">
									{{ item.actual_qty }}
								</p>
							</div>
							<div v-if="!data.low_stock_items.length" class="text-center py-6 text-sm text-slate-400">
								<svg class="w-8 h-8 mx-auto mb-2 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
								</svg>
								{{ __("المخزون بحالة جيدة") }}
							</div>
						</div>
					</div>
				</div>
			</template>
		</main>
	</div>
</template>

<script setup>
import { Line, Doughnut } from "vue-chartjs"
import {
	Chart as ChartJS,
	CategoryScale,
	LinearScale,
	PointElement,
	LineElement,
	ArcElement,
	Title,
	Tooltip,
	Legend,
	Filler,
} from "chart.js"
import { call } from "@/utils/apiWrapper"
import { useUserData } from "@/data/user"
import { session } from "@/data/session"
import { useToast } from "@/composables/useToast"
import router from "@/router"
import { computed, onMounted, ref } from "vue"

ChartJS.register(
	CategoryScale,
	LinearScale,
	PointElement,
	LineElement,
	ArcElement,
	Title,
	Tooltip,
	Legend,
	Filler
)

const { userName } = useUserData()
const { showError } = useToast()

const userInitial = computed(() => {
	const name = userName.value || "User"
	const parts = String(name).split(" ").filter(Boolean)
	return parts.length >= 2 ? (parts[0][0] + parts[1][0]).toUpperCase() : name.substring(0, 2).toUpperCase()
})

// State
const companies = ref([])
const selectedCompany = ref("")
const loadingCompanies = ref(false)
const loading = ref(false)
const data = ref(null)
const fromDate = ref("")
const toDate = ref("")

// Chart colors
const chartColors = {
	blue: "rgba(59, 130, 246, 0.8)",
	purple: "rgba(168, 85, 247, 0.8)",
	emerald: "rgba(16, 185, 129, 0.8)",
	amber: "rgba(245, 158, 11, 0.8)",
	rose: "rgba(244, 63, 94, 0.8)",
	indigo: "rgba(99, 102, 241, 0.8)",
	cyan: "rgba(6, 182, 212, 0.8)",
}

const palette = [
	chartColors.emerald,
	chartColors.blue,
	chartColors.purple,
	chartColors.amber,
	chartColors.rose,
	chartColors.indigo,
	chartColors.cyan,
	"rgba(236, 72, 153, 0.8)",
	"rgba(14, 165, 233, 0.8)",
	"rgba(132, 204, 22, 0.8)",
]

// Lifecycle
onMounted(async () => {
	if (!session.isLoggedIn) {
		router.replace({ name: "Login" })
		return
	}
	setPeriod(180)
	await loadCompanies()
	await loadData()
})

// Methods
async function loadCompanies() {
	loadingCompanies.value = true
	try {
		companies.value = await call("bs.baron_servies.api.utilities.get_companies") || []
		if (companies.value.length && !selectedCompany.value) {
			selectedCompany.value = companies.value[0].name
		}
	} catch (e) {
		showError(e?.message || __("فشل تحميل الشركات"))
	} finally {
		loadingCompanies.value = false
	}
}

async function loadData() {
	loading.value = true
	try {
		data.value = await call("bs.baron_servies.api.dashboard.get_dashboard_data", {
			company: selectedCompany.value || undefined,
			from_date: fromDate.value || undefined,
			to_date: toDate.value || undefined,
		})
	} catch (e) {
		showError(e?.message || __("فشل تحميل البيانات"))
	} finally {
		loading.value = false
	}
}

function setPeriod(days) {
	const today = new Date()
	const past = new Date()
	past.setDate(past.getDate() - days)
	toDate.value = today.toISOString().split("T")[0]
	fromDate.value = past.toISOString().split("T")[0]
	if (data.value) loadData()
}

function goBack() {
	router.push({ name: "Home" })
}

async function logout() {
	await session.logout.submit()
}

// Chart configs
const salesChartConfig = computed(() => {
	const labels = (data.value?.sales_by_month || []).map((d) => d.label)
	const sales = (data.value?.sales_by_month || []).map((d) => d.sales)
	const purchases = (data.value?.sales_by_month || []).map((d) => d.purchases)
	return {
		labels,
		datasets: [
			{
				label: __("المبيعات"),
				data: sales,
				borderColor: chartColors.blue,
				backgroundColor: "rgba(59, 130, 246, 0.15)",
				fill: true,
				tension: 0.4,
				borderWidth: 3,
				pointRadius: 4,
				pointBackgroundColor: chartColors.blue,
			},
			{
				label: __("المشتريات"),
				data: purchases,
				borderColor: chartColors.purple,
				backgroundColor: "rgba(168, 85, 247, 0.15)",
				fill: true,
				tension: 0.4,
				borderWidth: 3,
				pointRadius: 4,
				pointBackgroundColor: chartColors.purple,
			},
		],
	}
})

const paymentsChartConfig = computed(() => {
	const modes = data.value?.payments_by_mode || []
	return {
		labels: modes.map((m) => m.mode),
		datasets: [
			{
				data: modes.map((m) => m.amount),
				backgroundColor: modes.map((_, i) => palette[i % palette.length]),
				borderWidth: 2,
				borderColor: "#fff",
			},
		],
	}
})

const lineChartOptions = {
	responsive: true,
	maintainAspectRatio: false,
	plugins: {
		legend: {
			position: "top",
			labels: { font: { size: 12 }, usePointStyle: true, padding: 15 },
		},
		tooltip: {
			callbacks: {
				label: function (ctx) {
					return ctx.dataset.label + ": " + formatCurrency(ctx.parsed.y)
				},
			},
		},
	},
	scales: {
		y: {
			beginAtZero: true,
			ticks: { font: { size: 11 } },
			grid: { color: "rgba(0,0,0,0.05)" },
		},
		x: {
			ticks: { font: { size: 11 } },
			grid: { display: false },
		},
	},
}

const doughnutOptions = {
	responsive: true,
	maintainAspectRatio: false,
	plugins: {
		legend: {
			position: "bottom",
			labels: { font: { size: 11 }, usePointStyle: true, padding: 10 },
		},
		tooltip: {
			callbacks: {
				label: function (ctx) {
					return ctx.label + ": " + formatCurrency(ctx.parsed)
				},
			},
		},
	},
}

// Formatters
function formatCurrency(value) {
	const n = Number(value || 0)
	const cur = data.value?.summary?.currency || ""
	return n.toLocaleString("en-US", { minimumFractionDigits: 0, maximumFractionDigits: 2 }) + (cur ? " " + cur : "")
}

function formatDate(date) {
	if (!date) return "-"
	return new Date(date).toLocaleDateString("en-GB")
}
</script>
