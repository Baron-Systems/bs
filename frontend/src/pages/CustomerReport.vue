<template>
	<div class="min-h-screen flex flex-col bg-gradient-to-br from-slate-50 via-emerald-50 to-green-50" dir="rtl">
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
					<div class="w-10 h-10 bg-gradient-to-br from-emerald-500 to-green-700 rounded-xl flex items-center justify-center flex-shrink-0 shadow-lg shadow-emerald-500/30">
						<svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
						</svg>
					</div>
					<div class="min-w-0">
						<h1 class="text-base sm:text-lg font-bold text-slate-900 truncate">
							{{ __("تقرير العميل مفصل") }}
						</h1>
						<p class="text-xs text-slate-500 truncate">
							{{ __("عرض شامل لبيانات العميل") }}
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
		<main class="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-4 flex flex-col gap-4">
			<!-- Search & Filters -->
			<section class="bg-white rounded-lg border border-gray-200 shadow-sm p-4">
				<div class="flex flex-col sm:flex-row gap-3">
					<!-- Customer Search -->
					<div class="flex-1 relative">
						<label class="block text-xs font-medium text-gray-700 mb-1">{{ __("بحث عن عميل") }}</label>
						<div class="relative">
							<input
								ref="searchInputRef"
								v-model="searchQuery"
								type="text"
								:placeholder="__('اسم العميل، الجوال، البريد، الرقم الضريبي...')"
								class="w-full border border-gray-300 rounded-lg ps-10 pe-3 py-2 text-sm focus:ring-2 focus:ring-green-500 focus:border-green-500"
								@input="onSearchInput"
								@keydown.enter.prevent="selectFirstCustomer"
								@keydown.arrow-down.prevent="navigateCustomers(1)"
								@keydown.arrow-up.prevent="navigateCustomers(-1)"
							/>
							<svg class="absolute inset-y-0 start-3 my-auto w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
							</svg>
						</div>
						<!-- Results Dropdown -->
						<div
							v-if="showResults && searchResults.length > 0"
							class="absolute z-20 mt-1 w-full bg-white border border-gray-200 rounded-lg shadow-lg max-h-72 overflow-auto"
						>
							<button
								v-for="(c, idx) in searchResults"
								:key="c.name"
								@click="selectCustomer(c)"
								@mouseenter="selectedResultIndex = idx"
								:class="[
									'w-full text-start px-3 py-2 text-sm hover:bg-gray-50 transition-colors border-b border-gray-100 last:border-0',
									idx === selectedResultIndex ? 'bg-green-50' : ''
								]"
							>
								<div class="flex items-center justify-between gap-2">
									<div class="min-w-0">
										<p class="font-medium text-gray-900 truncate">{{ c.customer_name }}</p>
										<p class="text-xs text-gray-500 truncate">{{ c.name }}</p>
									</div>
									<div class="text-xs text-gray-400 flex-shrink-0 text-end">
										<span v-if="c.mobile_no">{{ c.mobile_no }}</span>
										<span v-if="c.customer_group" class="block">{{ c.customer_group }}</span>
									</div>
								</div>
							</button>
						</div>
						<div
							v-else-if="showResults && searchQuery.trim() && !searching && searchResults.length === 0"
							class="absolute z-20 mt-1 w-full bg-white border border-gray-200 rounded-lg shadow-lg p-3 text-sm text-gray-500"
						>
							{{ __("لا توجد نتائج") }}
						</div>
					</div>

					<!-- Date Range -->
					<div class="flex gap-2">
						<div class="flex flex-col gap-1">
							<label class="text-xs font-medium text-gray-700">{{ __("من تاريخ") }}</label>
							<input
								v-model="fromDate"
								type="date"
								class="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-green-500 focus:border-green-500"
							/>
						</div>
						<div class="flex flex-col gap-1">
							<label class="text-xs font-medium text-gray-700">{{ __("إلى تاريخ") }}</label>
							<input
								v-model="toDate"
								type="date"
								class="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-green-500 focus:border-green-500"
							/>
						</div>
					</div>

					<!-- Load Report Button -->
					<div class="flex items-end">
						<Button
							variant="solid"
							theme="green"
							:loading="loadingReport"
							:disabled="!selectedCustomer"
							@click="loadReport"
						>
							{{ __("عرض التقرير") }}
						</Button>
					</div>
				</div>
			</section>

			<!-- Loading State -->
			<div v-if="loadingReport" class="bg-white rounded-lg border border-gray-200 shadow-sm p-12 flex flex-col items-center justify-center gap-3">
				<svg class="animate-spin w-8 h-8 text-green-600" fill="none" viewBox="0 0 24 24">
					<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
					<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
				</svg>
				<p class="text-sm text-gray-500">{{ __("جاري تحميل التقرير...") }}</p>
			</div>

			<!-- Empty State -->
			<div v-else-if="!report" class="bg-white rounded-lg border border-gray-200 shadow-sm p-12 flex flex-col items-center justify-center gap-3">
				<svg class="w-12 h-12 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
				</svg>
				<p class="text-sm text-gray-500 text-center">{{ __("اختر عميلاً واضغط \"عرض التقرير\" لعرض البيانات") }}</p>
			</div>

			<!-- Report Content -->
			<template v-else>
				<!-- Customer Profile Card -->
				<section class="bg-white rounded-lg border border-gray-200 shadow-sm p-4">
					<div class="flex items-start gap-4">
						<div class="w-14 h-14 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0">
							<span class="text-lg font-bold text-green-700">{{ customerInitials }}</span>
						</div>
						<div class="flex-1 min-w-0">
							<h2 class="text-lg font-bold text-gray-900 truncate">{{ report.profile.customer_name }}</h2>
							<p class="text-xs text-gray-500 truncate">{{ report.profile.name }}</p>
							<div class="flex flex-wrap gap-2 mt-2">
								<span v-if="report.profile.customer_group" class="inline-flex items-center px-2 py-0.5 rounded text-xs bg-blue-50 text-blue-700">
									{{ report.profile.customer_group }}
								</span>
								<span v-if="report.profile.territory" class="inline-flex items-center px-2 py-0.5 rounded text-xs bg-purple-50 text-purple-700">
									{{ report.profile.territory }}
								</span>
								<span v-if="report.profile.customer_type" class="inline-flex items-center px-2 py-0.5 rounded text-xs bg-gray-100 text-gray-700">
									{{ report.profile.customer_type }}
								</span>
							</div>
						</div>
					</div>

					<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mt-4 pt-4 border-t border-gray-100">
						<div v-if="report.profile.mobile_no" class="flex items-center gap-2 text-sm">
							<svg class="w-4 h-4 text-gray-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
							</svg>
							<span class="text-gray-700 truncate">{{ report.profile.mobile_no }}</span>
						</div>
						<div v-if="report.profile.email_id" class="flex items-center gap-2 text-sm">
							<svg class="w-4 h-4 text-gray-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
							</svg>
							<span class="text-gray-700 truncate">{{ report.profile.email_id }}</span>
						</div>
						<div v-if="report.profile.tax_id" class="flex items-center gap-2 text-sm">
							<svg class="w-4 h-4 text-gray-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
							</svg>
							<span class="text-gray-700 truncate">{{ __("الرقم الضريبي:") }} {{ report.profile.tax_id }}</span>
						</div>
						<div v-if="report.profile.address" class="flex items-center gap-2 text-sm">
							<svg class="w-4 h-4 text-gray-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
							</svg>
							<span class="text-gray-700 truncate">
								{{ report.profile.address.address_line1 }}{{ report.profile.address.city ? ', ' + report.profile.address.city : '' }}
							</span>
						</div>
					</div>
				</section>

				<!-- Summary Cards -->
				<section class="grid grid-cols-2 lg:grid-cols-4 gap-3">
					<div class="bg-white rounded-lg border border-gray-200 shadow-sm p-4">
						<p class="text-xs text-gray-500 mb-1">{{ __("إجمالي المبيعات") }}</p>
						<p class="text-lg font-bold text-gray-900">{{ formatCurrency(report.summary.total_sales) }}</p>
						<p class="text-xs text-gray-400 mt-1">{{ report.summary.total_invoices }} {{ __("فاتورة") }}</p>
					</div>
					<div class="bg-white rounded-lg border border-gray-200 shadow-sm p-4">
						<p class="text-xs text-gray-500 mb-1">{{ __("صافي المبيعات") }}</p>
						<p class="text-lg font-bold text-green-700">{{ formatCurrency(report.summary.net_sales) }}</p>
						<p class="text-xs text-gray-400 mt-1">{{ __("بعد المرتجعات") }}</p>
					</div>
					<div class="bg-white rounded-lg border border-gray-200 shadow-sm p-4">
						<p class="text-xs text-gray-500 mb-1">{{ __("متوسط الفاتورة") }}</p>
						<p class="text-lg font-bold text-blue-700">{{ formatCurrency(report.summary.avg_invoice) }}</p>
						<p class="text-xs text-gray-400 mt-1">{{ report.summary.total_qty }} {{ __("وحدة") }}</p>
					</div>
					<div class="bg-white rounded-lg border border-gray-200 shadow-sm p-4">
						<p class="text-xs text-gray-500 mb-1">{{ __("المستحقات") }}</p>
						<p class="text-lg font-bold" :class="report.outstanding.total_outstanding > 0 ? 'text-red-600' : 'text-gray-900'">
							{{ formatCurrency(report.outstanding.total_outstanding) }}
						</p>
						<p class="text-xs mt-1" :class="report.outstanding.overdue_amount > 0 ? 'text-red-500' : 'text-gray-400'">
							{{ __("المتأخر:") }} {{ formatCurrency(report.outstanding.overdue_amount) }}
						</p>
					</div>
				</section>

				<!-- Monthly Trend (simple bar chart) -->
				<section v-if="report.monthly_trend.length > 0" class="bg-white rounded-lg border border-gray-200 shadow-sm p-4">
					<h3 class="text-sm font-semibold text-gray-900 mb-3">{{ __("الاتجاه الشهري للمبيعات") }}</h3>
					<div class="flex items-end gap-2 h-32 overflow-x-auto">
						<div
							v-for="m in report.monthly_trend"
							:key="m.month"
							class="flex flex-col items-center gap-1 flex-1 min-w-[40px]"
						>
							<div class="text-[10px] text-gray-500">{{ formatCurrencyShort(m.net) }}</div>
							<div
								class="w-full bg-green-500 rounded-t transition-all hover:bg-green-600"
								:style="{ height: trendBarHeight(m.net) + '%' }"
								:title="m.month + ': ' + formatCurrency(m.net)"
							></div>
							<div class="text-[10px] text-gray-400 whitespace-nowrap">{{ m.month.split('-')[1] }}</div>
						</div>
					</div>
				</section>

				<!-- Two columns: Top Items + Recent Invoices -->
				<div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
					<!-- Top Items -->
					<section class="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
						<div class="px-4 py-3 border-b border-gray-100">
							<h3 class="text-sm font-semibold text-gray-900">{{ __("أكثر الأصناف مبيعاً") }}</h3>
						</div>
						<div v-if="report.top_items.length === 0" class="p-6 text-center text-sm text-gray-500">
							{{ __("لا توجد بيانات") }}
						</div>
						<div v-else class="overflow-x-auto">
							<table class="w-full text-sm">
								<thead class="bg-gray-50 text-xs text-gray-500">
									<tr>
										<th class="px-3 py-2 text-start font-medium">{{ __("الصنف") }}</th>
										<th class="px-3 py-2 text-end font-medium">{{ __("الكمية") }}</th>
										<th class="px-3 py-2 text-end font-medium">{{ __("القيمة") }}</th>
									</tr>
								</thead>
								<tbody class="divide-y divide-gray-100">
									<tr v-for="it in report.top_items" :key="it.item_code" class="hover:bg-gray-50">
										<td class="px-3 py-2">
											<p class="font-medium text-gray-900 truncate max-w-[180px]">{{ it.item_name }}</p>
											<p class="text-xs text-gray-400 truncate">{{ it.item_code }}</p>
										</td>
										<td class="px-3 py-2 text-end text-gray-700">{{ formatQty(it.total_qty) }} <span class="text-xs text-gray-400">{{ it.uom }}</span></td>
										<td class="px-3 py-2 text-end font-medium text-gray-900">{{ formatCurrency(it.total_amount) }}</td>
									</tr>
								</tbody>
							</table>
						</div>
					</section>

					<!-- Recent Invoices -->
					<section class="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
						<div class="px-4 py-3 border-b border-gray-100">
							<h3 class="text-sm font-semibold text-gray-900">{{ __("أحدث الفواتير") }}</h3>
						</div>
						<div v-if="report.recent_invoices.length === 0" class="p-6 text-center text-sm text-gray-500">
							{{ __("لا توجد فواتير") }}
						</div>
						<div v-else class="overflow-x-auto">
							<table class="w-full text-sm">
								<thead class="bg-gray-50 text-xs text-gray-500">
									<tr>
										<th class="px-3 py-2 text-start font-medium">{{ __("رقم") }}</th>
										<th class="px-3 py-2 text-start font-medium">{{ __("التاريخ") }}</th>
										<th class="px-3 py-2 text-end font-medium">{{ __("الإجمالي") }}</th>
										<th class="px-3 py-2 text-center font-medium">{{ __("الحالة") }}</th>
									</tr>
								</thead>
								<tbody class="divide-y divide-gray-100">
									<tr v-for="inv in report.recent_invoices" :key="inv.name" class="hover:bg-gray-50">
										<td class="px-3 py-2">
											<a :href="invoiceUrl(inv.name)" target="_blank" class="text-blue-600 hover:underline truncate block max-w-[140px]">
												{{ inv.name }}
											</a>
											<span v-if="inv.is_return" class="text-[10px] text-red-500">{{ __("مرتجع") }}</span>
										</td>
										<td class="px-3 py-2 text-gray-600 whitespace-nowrap">{{ formatDate(inv.posting_date) }}</td>
										<td class="px-3 py-2 text-end font-medium text-gray-900">{{ formatCurrency(inv.grand_total) }}</td>
										<td class="px-3 py-2 text-center">
											<span
												:class="[
													'inline-block px-2 py-0.5 rounded text-xs',
													inv.status === 'Paid' ? 'bg-green-50 text-green-700' : '',
													inv.status === 'Unpaid' ? 'bg-red-50 text-red-700' : '',
													inv.status === 'Partly Paid' ? 'bg-amber-50 text-amber-700' : '',
													!['Paid','Unpaid','Partly Paid'].includes(inv.status) ? 'bg-gray-100 text-gray-600' : ''
												]"
											>{{ inv.status }}</span>
										</td>
									</tr>
								</tbody>
							</table>
						</div>
					</section>
				</div>

				<!-- Outstanding Invoices -->
				<section v-if="report.outstanding.open_invoices.length > 0" class="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
					<div class="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
						<h3 class="text-sm font-semibold text-gray-900">{{ __("الفواتير المستحقة") }}</h3>
						<span class="text-xs text-gray-500">{{ report.outstanding.open_invoices_count }} {{ __("فاتورة") }}</span>
					</div>
					<div class="overflow-x-auto">
						<table class="w-full text-sm">
							<thead class="bg-gray-50 text-xs text-gray-500">
								<tr>
									<th class="px-3 py-2 text-start font-medium">{{ __("رقم") }}</th>
									<th class="px-3 py-2 text-start font-medium">{{ __("تاريخ الفاتورة") }}</th>
									<th class="px-3 py-2 text-start font-medium">{{ __("تاريخ الاستحقاق") }}</th>
									<th class="px-3 py-2 text-end font-medium">{{ __("الإجمالي") }}</th>
									<th class="px-3 py-2 text-end font-medium">{{ __("المدفوع") }}</th>
									<th class="px-3 py-2 text-end font-medium">{{ __("المتبقي") }}</th>
								</tr>
							</thead>
							<tbody class="divide-y divide-gray-100">
								<tr v-for="inv in report.outstanding.open_invoices" :key="inv.name" class="hover:bg-gray-50">
									<td class="px-3 py-2">
										<a :href="invoiceUrl(inv.name)" target="_blank" class="text-blue-600 hover:underline">{{ inv.name }}</a>
									</td>
									<td class="px-3 py-2 text-gray-600 whitespace-nowrap">{{ formatDate(inv.posting_date) }}</td>
									<td class="px-3 py-2 whitespace-nowrap" :class="isOverdue(inv.due_date) ? 'text-red-600 font-medium' : 'text-gray-600'">
										{{ formatDate(inv.due_date) }}
										<span v-if="isOverdue(inv.due_date)" class="text-[10px] block">{{ __("متأخرة") }}</span>
									</td>
									<td class="px-3 py-2 text-end text-gray-700">{{ formatCurrency(inv.grand_total) }}</td>
									<td class="px-3 py-2 text-end text-green-700">{{ formatCurrency(inv.paid_amount) }}</td>
									<td class="px-3 py-2 text-end font-medium text-red-600">{{ formatCurrency(inv.outstanding_amount) }}</td>
								</tr>
							</tbody>
							<tfoot class="bg-gray-50 font-semibold">
								<tr>
									<td colspan="5" class="px-3 py-2 text-end text-gray-700">{{ __("الإجمالي المستحق:") }}</td>
									<td class="px-3 py-2 text-end text-red-700">{{ formatCurrency(report.outstanding.total_outstanding) }}</td>
								</tr>
							</tfoot>
						</table>
					</div>
				</section>

				<!-- Payment History -->
				<section v-if="report.payments.length > 0" class="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
					<div class="px-4 py-3 border-b border-gray-100">
						<h3 class="text-sm font-semibold text-gray-900">{{ __("سجل المدفوعات") }}</h3>
					</div>
					<div class="overflow-x-auto">
						<table class="w-full text-sm">
							<thead class="bg-gray-50 text-xs text-gray-500">
								<tr>
									<th class="px-3 py-2 text-start font-medium">{{ __("رقم") }}</th>
									<th class="px-3 py-2 text-start font-medium">{{ __("التاريخ") }}</th>
									<th class="px-3 py-2 text-start font-medium">{{ __("طريقة الدفع") }}</th>
									<th class="px-3 py-2 text-start font-medium">{{ __("المرجع") }}</th>
									<th class="px-3 py-2 text-end font-medium">{{ __("المبلغ") }}</th>
								</tr>
							</thead>
							<tbody class="divide-y divide-gray-100">
								<tr v-for="p in report.payments" :key="p.name" class="hover:bg-gray-50">
									<td class="px-3 py-2">
										<a :href="paymentUrl(p.name)" target="_blank" class="text-blue-600 hover:underline">{{ p.name }}</a>
									</td>
									<td class="px-3 py-2 text-gray-600 whitespace-nowrap">{{ formatDate(p.posting_date) }}</td>
									<td class="px-3 py-2 text-gray-700">{{ p.mode_of_payment || '-' }}</td>
									<td class="px-3 py-2 text-gray-500">{{ p.reference_no || '-' }}</td>
									<td class="px-3 py-2 text-end font-medium text-green-700">{{ formatCurrency(p.paid_amount) }}</td>
								</tr>
							</tbody>
						</table>
					</div>
				</section>
			</template>
		</main>
	</div>
</template>

<script setup>
import { Button } from "frappe-ui"
import { call } from "@/utils/apiWrapper"
import { useUserData } from "@/data/user"
import { session } from "@/data/session"
import { useToast } from "@/composables/useToast"
import router from "@/router"
import { computed, onMounted, ref } from "vue"

const { userName } = useUserData()
const { showError } = useToast()

const userInitial = computed(() => {
	const name = userName.value || "User"
	const parts = String(name).split(" ").filter(Boolean)
	return parts.length >= 2 ? (parts[0][0] + parts[1][0]).toUpperCase() : name.substring(0, 2).toUpperCase()
})

// State
const searchQuery = ref("")
const searchResults = ref([])
const showResults = ref(false)
const searching = ref(false)
const selectedResultIndex = ref(-1)
const searchInputRef = ref(null)

const selectedCustomer = ref("")
const selectedCustomerName = ref("")

const fromDate = ref(new Date(new Date().setFullYear(new Date().getFullYear() - 1)).toISOString().split("T")[0])
const toDate = ref(new Date().toISOString().split("T")[0])

const report = ref(null)
const loadingReport = ref(false)

let searchDebounce = null

// Computed
const customerInitials = computed(() => {
	const name = report.value?.profile?.customer_name || ""
	const parts = name.split(" ").filter(Boolean)
	return parts.length >= 2 ? (parts[0][0] + parts[1][0]).toUpperCase() : name.substring(0, 2).toUpperCase()
})

// Lifecycle
onMounted(() => {
	if (!session.isLoggedIn) {
		router.replace({ name: "Login" })
		return
	}
	setTimeout(() => searchInputRef.value?.focus(), 0)
})

// Methods
function onSearchInput() {
	clearTimeout(searchDebounce)
	showResults.value = true
	if (!searchQuery.value.trim()) {
		searchResults.value = []
		showResults.value = false
		return
	}
	searchDebounce = setTimeout(() => doSearch(), 300)
}

async function doSearch() {
	if (!searchQuery.value.trim()) return
	searching.value = true
	try {
		searchResults.value = await call("bs.baron_servies.api.customer_report.get_customers", {
			search_term: searchQuery.value.trim(),
			limit: 30,
		}) || []
		selectedResultIndex.value = searchResults.value.length > 0 ? 0 : -1
	} catch (e) {
		searchResults.value = []
	} finally {
		searching.value = false
	}
}

function navigateCustomers(delta) {
	if (searchResults.value.length === 0) return
	let next = selectedResultIndex.value + delta
	if (next < 0) next = searchResults.value.length - 1
	if (next >= searchResults.value.length) next = 0
	selectedResultIndex.value = next
}

async function selectFirstCustomer() {
	if (searchResults.value.length === 0 && searchQuery.value.trim()) {
		clearTimeout(searchDebounce)
		await doSearch()
		if (searchResults.value.length === 0) return
	}
	if (searchResults.value.length === 0) return
	const idx = selectedResultIndex.value >= 0 ? selectedResultIndex.value : 0
	selectCustomer(searchResults.value[idx])
}

function selectCustomer(c) {
	selectedCustomer.value = c.name
	selectedCustomerName.value = c.customer_name
	searchQuery.value = c.customer_name
	showResults.value = false
	loadReport()
}

async function loadReport() {
	if (!selectedCustomer.value) return
	loadingReport.value = true
	report.value = null
	try {
		report.value = await call("bs.baron_servies.api.customer_report.get_customer_report", {
			customer: selectedCustomer.value,
			from_date: fromDate.value,
			to_date: toDate.value,
		})
	} catch (e) {
		const msg = e?.message || e?.toString() || __("فشل تحميل التقرير")
		showError(msg)
	} finally {
		loadingReport.value = false
	}
}

function goBack() {
	router.push({ name: "Home" })
}

async function logout() {
	await session.logout.submit()
}

// Formatters
function formatCurrency(v) {
	const n = Number(v || 0)
	return n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function formatCurrencyShort(v) {
	const n = Number(v || 0)
	if (Math.abs(n) >= 1000) return (n / 1000).toFixed(1) + "k"
	return n.toFixed(0)
}

function formatQty(v) {
	const n = Number(v || 0)
	return Number.isInteger(n) ? String(n) : n.toFixed(3).replace(/\.?0+$/, "")
}

function formatDate(d) {
	if (!d) return "-"
	try {
		const date = new Date(d)
		return date.toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" })
	} catch {
		return d
	}
}

function isOverdue(dueDate) {
	if (!dueDate) return false
	return new Date(dueDate) < new Date()
}

function trendBarHeight(value) {
	const max = Math.max(...report.value.monthly_trend.map(m => Math.abs(Number(m.net || 0))), 1)
	return Math.max(5, (Math.abs(Number(value || 0)) / max) * 100)
}

function invoiceUrl(name) {
	return `/app/sales-invoice/${encodeURIComponent(name)}`
}

function paymentUrl(name) {
	return `/app/payment-entry/${encodeURIComponent(name)}`
}
</script>

<style scoped>
input[type="number"]::-webkit-inner-spin-button,
input[type="number"]::-webkit-outer-spin-button {
	-webkit-appearance: none;
	margin: 0;
}
</style>
