<template>
	<div class="min-h-screen flex flex-col bg-gradient-to-br from-slate-50 via-emerald-50 to-cyan-50" dir="rtl">
		<!-- Header -->
		<header class="bg-white/80 backdrop-blur-md border-b border-slate-200 sticky top-0 z-30 shadow-sm">
			<div class="max-w-7xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between gap-3">
				<div class="flex items-center gap-3 min-w-0">
					<div class="w-10 h-10 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-xl flex items-center justify-center flex-shrink-0 shadow-lg shadow-emerald-500/30">
						<svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h2m-2 4h2m-2-8h2M5 7h14a2 2 0 012 2v10a2 2 0 01-2 2H5a2 2 0 01-2-2V9a2 2 0 012-2z" />
						</svg>
					</div>
					<div class="min-w-0">
						<h1 class="text-base sm:text-lg font-bold text-slate-900 truncate">
							{{ __("فاتورة شراء سريعة") }}
						</h1>
						<p class="text-xs text-slate-500 truncate">
							{{ __("إنشاء فاتورة شراء كمسودة") }}
						</p>
					</div>
				</div>
				<div class="flex items-center gap-2 flex-shrink-0">
					<div class="hidden sm:flex items-center gap-2 bg-slate-100 rounded-full px-3 py-1.5">
						<div class="w-7 h-7 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-full flex items-center justify-center text-white text-xs font-bold">
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
			<!-- Settings Bar (Collapsible) -->
			<section class="bg-white rounded-lg border border-gray-200 shadow-sm">
				<!-- Toggle Header -->
				<button
					@click="settingsOpen = !settingsOpen"
					class="w-full px-4 py-3 flex items-center justify-between text-start hover:bg-gray-50 transition-colors rounded-lg"
				>
					<div class="flex items-center gap-2">
						<svg
							class="w-4 h-4 text-gray-500 transition-transform"
							:class="{ 'rotate-90': settingsOpen }"
							fill="none" stroke="currentColor" viewBox="0 0 24 24"
						>
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
						</svg>
						<span class="text-sm font-semibold text-gray-900">{{ __("إعدادات الفاتورة") }}</span>
					</div>
					<div class="text-xs text-gray-500 truncate">
						<span v-if="selectedCompany">{{ selectedCompany }}</span>
						<span v-if="selectedWarehouse"> / {{ selectedWarehouse }}</span>
						<span v-if="selectedSupplier"> / {{ selectedSupplierName || selectedSupplier }}</span>
						<span v-if="!selectedCompany || !selectedSupplier">{{ __("اضغط للإعداد") }}</span>
					</div>
				</button>

				<!-- Collapsible Content -->
				<div v-show="settingsOpen" class="px-4 pb-4 pt-2 border-t border-gray-100">
					<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
						<!-- Company -->
						<div class="flex flex-col gap-1">
							<label class="text-xs font-medium text-gray-700">{{ __("الشركة") }}</label>
							<select
								v-model="selectedCompany"
								class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 bg-white"
								:disabled="loadingCompanies"
								@change="onCompanyChange"
							>
								<option value="" disabled>{{ loadingCompanies ? __("جاري التحميل...") : __("اختر الشركة") }}</option>
								<option v-for="c in companies" :key="c.name" :value="c.name">
									{{ c.name }}
								</option>
							</select>
						</div>

						<!-- Warehouse -->
						<div class="flex flex-col gap-1">
							<label class="text-xs font-medium text-gray-700">{{ __("المستودع") }}</label>
							<select
								v-model="selectedWarehouse"
								class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 bg-white"
								:disabled="!selectedCompany || loadingWarehouses"
							>
								<option value="" disabled>{{ loadingWarehouses ? __("جاري التحميل...") : __("اختر المستودع") }}</option>
								<option v-for="w in warehouses" :key="w.name" :value="w.name">
									{{ w.warehouse_name || w.name }}
								</option>
							</select>
						</div>

						<!-- Supplier -->
						<div class="flex flex-col gap-1 relative">
							<label class="text-xs font-medium text-gray-700">{{ __("المورد") }}</label>
							<div class="relative">
								<input
									ref="supplierSearchRef"
									v-model="supplierSearch"
									type="text"
									:placeholder="selectedSupplier ? '' : __('ابحث عن مورد...')"
									class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
									@input="onSupplierSearchInput"
									@focus="openSupplierResults"
								/>
								<div v-if="selectedSupplier" class="absolute inset-y-0 start-3 flex items-center pointer-events-none">
									<span class="text-sm text-gray-900 truncate">{{ selectedSupplierName || selectedSupplier }}</span>
								</div>
								<button
									v-if="selectedSupplier"
									@click="clearSupplier"
									class="absolute inset-y-0 end-0 px-2 flex items-center text-gray-400 hover:text-red-600"
								>
									<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
									</svg>
								</button>
							</div>

							<!-- Supplier Results Dropdown -->
							<div
								v-if="showSupplierResults && supplierResults.length > 0"
								class="absolute z-30 mt-1 w-full top-full"
							>
								<div class="bg-white border border-gray-200 rounded-lg shadow-2xl max-h-60 overflow-y-auto">
									<button
										v-for="s in supplierResults"
										:key="s.name"
										@click="selectSupplier(s)"
										class="w-full text-start px-4 py-3 border-b border-gray-100 last:border-0 hover:bg-gray-50 transition-colors"
									>
										<p class="text-sm font-medium text-gray-900">{{ s.supplier_name || s.name }}</p>
										<p v-if="s.mobile_no || s.email_id" class="text-xs text-gray-500">
											{{ [s.mobile_no, s.email_id].filter(Boolean).join(' - ') }}
										</p>
									</button>
								</div>
							</div>
						</div>

						<!-- Posting Date -->
						<div class="flex flex-col gap-1">
							<label class="text-xs font-medium text-gray-700">{{ __("تاريخ الترحيل") }}</label>
							<input
								v-model="postingDate"
								type="date"
								class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
							/>
						</div>

						<!-- Due Date -->
						<div class="flex flex-col gap-1">
							<label class="text-xs font-medium text-gray-700">{{ __("تاريخ الاستحقاق") }}</label>
							<input
								v-model="dueDate"
								type="date"
								class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
							/>
						</div>

						<!-- Checkboxes -->
						<div class="flex flex-col gap-2 justify-center sm:col-span-2 lg:col-span-3">
							<label class="flex items-center gap-2 cursor-pointer select-none">
								<input
									v-model="updateStock"
									type="checkbox"
									class="w-4 h-4 text-emerald-600 border-gray-300 rounded focus:ring-emerald-500"
								/>
								<span class="text-sm text-gray-700">{{ __("تحديث المخزون عند الحفظ") }}</span>
							</label>
							<label class="flex items-center gap-2 cursor-pointer select-none">
								<input
									v-model="updatePurchasePrice"
									type="checkbox"
									class="w-4 h-4 text-emerald-600 border-gray-300 rounded focus:ring-emerald-500"
								/>
								<span class="text-sm text-gray-700">{{ __("تغيير سعر الشراء بناءً على الأسعار المدخلة الجديدة") }}</span>
							</label>
							<div class="flex flex-col sm:flex-row gap-2 sm:items-center">
								<label class="flex items-center gap-2 cursor-pointer select-none">
									<input
										v-model="isPaid"
										type="checkbox"
										class="w-4 h-4 text-emerald-600 border-gray-300 rounded focus:ring-emerald-500"
									/>
									<span class="text-sm text-gray-700">{{ __("فاتورة مدفوعة") }}</span>
								</label>
								<select
									v-if="isPaid"
									v-model="modeOfPayment"
									class="border border-gray-300 rounded-lg px-2 py-1 text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 bg-white"
									:disabled="loadingModesOfPayment"
								>
									<option v-for="m in modesOfPayment" :key="m.name" :value="m.name">{{ m.name }}</option>
								</select>
							</div>
						</div>
					</div>
				</div>
			</section>

			<!-- Not configured hint -->
			<section v-if="!selectedCompany || !selectedWarehouse || !selectedSupplier" class="bg-emerald-50 border border-emerald-200 rounded-lg p-4 text-sm text-emerald-700">
				{{ __("اختر شركة ومستودع ومورد للبدء") }}
			</section>

			<!-- Work Area -->
			<section
				v-if="selectedCompany && selectedWarehouse && selectedSupplier"
				class="bg-white rounded-lg border border-gray-200 shadow-sm flex flex-col flex-1 min-h-[400px]"
				@click="refocusSearch($event)"
			>
				<!-- Sticky Search Bar -->
				<div class="p-4 border-b border-gray-200 sticky top-0 bg-white z-20 rounded-t-lg">
					<div class="relative">
						<div class="absolute inset-y-0 start-0 ps-3 flex items-center pointer-events-none">
							<svg v-if="!searching" class="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
							</svg>
							<div v-else class="animate-spin rounded-full h-4 w-4 border-b-2 border-emerald-500"></div>
						</div>
						<input
							ref="searchInputRef"
							v-model="searchQuery"
							type="text"
							:placeholder="__('ابحث عن صنف بالاسم أو الكود أو امسح الباركود...')"
							class="w-full ps-10 pe-10 py-2.5 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
							@input="onSearchInput"
							@keydown.enter.prevent="selectFirstResult"
							@keydown.down.prevent="navigateResults(1)"
							@keydown.up.prevent="navigateResults(-1)"
							@keydown.escape="clearSearch"
							autocomplete="off"
						/>
						<button
							v-if="searchQuery"
							@click="clearSearch"
							class="absolute inset-y-0 end-0 pe-3 flex items-center"
							:aria-label="__('مسح')"
						>
							<svg class="h-5 w-5 text-gray-400 hover:text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
							</svg>
						</button>
					</div>

					<!-- Search Results Dropdown -->
					<div
						v-if="showResults && (searchResults.length > 0 || (searchQuery.length >= 1 && !searching))"
						class="relative z-10 mt-2"
					>
						<div class="bg-white border border-gray-200 rounded-lg shadow-2xl max-h-80 overflow-y-auto">
							<div v-if="searchResults.length > 0">
								<button
									v-for="(item, index) in searchResults"
									:key="item.item_code"
									@click="addItem(item)"
									@mouseenter="selectedResultIndex = index"
									:class="[
										'w-full text-start px-4 py-3 flex items-center gap-3 border-b border-gray-100 last:border-0 transition-colors',
										selectedResultIndex === index ? 'bg-emerald-50' : 'hover:bg-gray-50'
									]"
								>
									<div class="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center overflow-hidden flex-shrink-0">
										<img v-if="item.image" :src="item.image" :alt="item.item_name" class="w-full h-full object-cover" />
										<svg v-else class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
										</svg>
									</div>
									<div class="flex-1 min-w-0">
										<p class="text-sm font-medium text-gray-900 truncate">{{ item.item_name }}</p>
										<p class="text-xs text-gray-500 truncate">{{ item.item_code }}</p>
									</div>
									<div class="text-end flex-shrink-0 flex flex-col items-end gap-0.5">
										<span :class="[
											'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium',
											(item.actual_qty || 0) > 0 ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
										]">
											{{ formatQty(item.actual_qty) }} {{ item.stock_uom }}
										</span>
										<span v-if="item.last_purchase_rate > 0" class="text-[10px] text-emerald-600">
											{{ formatMoney(item.last_purchase_rate) }}
										</span>
									</div>
								</button>
							</div>
							<div v-else class="px-4 py-6 text-center text-sm text-gray-500">
								{{ __("لا توجد نتائج") }}
							</div>
						</div>
					</div>
				</div>

				<!-- Cart Header -->
				<div class="px-4 py-2 border-b border-gray-200 flex items-center justify-between bg-gray-50">
					<h2 class="text-sm font-semibold text-gray-900">
						{{ __("أصناف الفاتورة") }}
						<span v-if="cart.length > 0" class="ms-2 text-xs font-normal text-gray-500">
							{{ __("{0} / {1} صنف", [cart.length, MAX_ITEMS]) }}
						</span>
					</h2>
					<button
						v-if="cart.length > 0"
						@click="clearCart"
						class="text-xs text-red-600 hover:text-red-800 hover:bg-red-50 px-2 py-1 rounded transition-colors"
					>
						{{ __("مسح الكل") }}
					</button>
				</div>

				<!-- Scrollable Cart -->
				<div class="flex-1 overflow-y-auto">
					<!-- Empty State -->
					<div v-if="cart.length === 0" class="flex items-center justify-center p-12">
						<div class="text-center">
							<svg class="mx-auto h-12 w-12 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
							</svg>
							<p class="mt-2 text-sm text-gray-500">{{ __("ابحث وأضف أصنافاً لإنشاء الفاتورة") }}</p>
						</div>
					</div>

					<!-- Cart Table -->
					<table v-else class="w-full text-sm">
						<thead class="bg-gray-50 text-xs text-gray-600 uppercase sticky top-0 z-10">
							<tr>
								<th class="px-3 py-2 text-start font-medium">{{ __("الصنف") }}</th>
								<th class="px-3 py-2 text-end font-medium w-28">{{ __("الرصيد") }}</th>
								<th class="px-3 py-2 text-end font-medium w-28">{{ __("الكمية") }}</th>
								<th class="px-3 py-2 text-end font-medium w-36">{{ __("سعر الشراء") }}</th>
								<th class="px-3 py-2 text-end font-medium w-28">{{ __("الإجمالي") }}</th>
								<th class="px-3 py-2 w-12"></th>
							</tr>
						</thead>
						<tbody class="divide-y divide-gray-100">
							<tr v-for="(row, idx) in cart" :key="row.item_code" class="hover:bg-gray-50">
								<td class="px-3 py-2 text-start">
									<div class="flex items-center gap-2">
										<div class="w-8 h-8 bg-gray-100 rounded flex items-center justify-center overflow-hidden flex-shrink-0">
											<img v-if="row.image" :src="row.image" :alt="row.item_name" class="w-full h-full object-cover" />
											<svg v-else class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
											</svg>
										</div>
										<div class="min-w-0">
											<p class="font-medium text-gray-900 truncate">{{ row.item_name }}</p>
											<p class="text-xs text-gray-500 truncate">{{ row.item_code }}</p>
										</div>
									</div>
								</td>
								<td class="px-3 py-2 text-end text-gray-600">
									{{ formatQty(row.actual_qty) }}
									<span class="text-xs text-gray-400">{{ row.stock_uom }}</span>
								</td>
								<td class="px-3 py-2 text-end">
									<input
										v-model.number="row.qty"
										type="number"
										min="0"
										step="any"
										class="w-24 text-end border border-gray-300 rounded px-2 py-1 text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
										@focus="($event.target).select()"
										@click="($event.target).select()"
										@keydown.enter.prevent="focusSearch"
									/>
								</td>
								<td class="px-3 py-2 text-end">
									<input
										v-model.number="row.rate"
										type="number"
										min="0"
										step="any"
										:class="[
											'w-28 text-end border rounded px-2 py-1 text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
											(row.rate || 0) > 0 ? 'border-gray-300' : 'border-red-300 bg-red-50'
										]"
										@focus="($event.target).select()"
										@click="($event.target).select()"
										@keydown.enter.prevent="focusSearch"
									/>
									<div class="text-[10px] text-gray-500 mt-0.5">
										<template v-if="row.rate_source === 'buying_price_list'">{{ __('قائمة أسعار الشراء') }}</template>
										<template v-else-if="row.rate_source === 'last_purchase_rate'">{{ __('آخر سعر شراء') }}</template>
										<template v-else>{{ __('يدوي') }}</template>
									</div>
								</td>
								<td class="px-3 py-2 text-end font-medium text-gray-900">
									{{ formatMoney(row.qty * row.rate) }}
								</td>
								<td class="px-3 py-2 text-center">
									<button
										@click="removeItem(idx)"
										class="p-1 rounded text-gray-400 hover:text-red-600 hover:bg-red-50 transition-colors"
										:aria-label="__('حذف')"
									>
										<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6M1 7h22M9 7V4a1 1 0 011-1h4a1 1 0 011 1v3" />
										</svg>
									</button>
								</td>
							</tr>
						</tbody>
						<tfoot v-if="cart.length > 0" class="bg-gray-50 font-semibold text-sm sticky bottom-0">
							<tr>
								<td colspan="4" class="px-3 py-2 text-end">{{ __("إجمالي الفاتورة") }}</td>
								<td class="px-3 py-2 text-end text-emerald-700">{{ formatMoney(cartTotal) }}</td>
								<td></td>
							</tr>
						</tfoot>
					</table>
				</div>

				<!-- Footer / Actions -->
				<div v-if="cart.length > 0" class="px-4 py-3 border-t border-gray-200 flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-white">
					<div class="text-xs text-gray-500">
						<p v-if="itemsWithoutPrice > 0" class="text-red-600">
							{{ __("{0} صنف بدون سعر شراء", [itemsWithoutPrice]) }}
						</p>
						<p v-else-if="cart.length >= MAX_ITEMS" class="text-amber-600">
							{{ __("بلغت الحد الأقصى ({0} صنف) - احفظ ثم ابدأ فاتورة جديدة", [MAX_ITEMS]) }}
						</p>
						<p v-else>{{ __("جميع الأصناف لها سعر شراء") }}</p>
					</div>
					<div class="flex items-center gap-2">
						<Button
							variant="subtle"
							@click="clearCart"
						>
							{{ __("مسح") }}
						</Button>
						<Button
							variant="solid"
							theme="green"
							:loading="submitting"
							:disabled="!canSubmit"
							@click="() => handleSubmit(false)"
						>
							{{ __("حفظ كمسودة") }}
						</Button>
						<Button
							variant="solid"
							theme="emerald"
							:loading="submitting"
							:disabled="!canSubmit"
							@click="() => handleSubmit(true)"
						>
							{{ __("حفظ وترحيل") }}
						</Button>
					</div>
				</div>
			</section>
		</main>

		<!-- Success Dialog -->
		<Dialog v-model="showSuccessDialog" :options="{ title: __('تم الحفظ'), size: 'sm' }">
			<template #body-content>
				<div class="flex flex-col items-center text-center py-4 gap-3">
					<div class="w-14 h-14 bg-green-100 rounded-full flex items-center justify-center">
						<svg class="w-7 h-7 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
						</svg>
					</div>
					<p class="text-sm text-gray-700">
						{{ lastSubmitted ? __("تم حفظ وترحيل فاتورة الشراء بنجاح") : __("تم إنشاء فاتورة الشراء كمسودة بنجاح") }}
					</p>
					<p class="text-xs text-gray-500">{{ __("رقم الفاتورة: {0}", [lastCreatedName]) }}</p>
				</div>
			</template>
			<template #actions>
				<div class="flex gap-2 w-full">
					<Button class="flex-1" variant="subtle" @click="showSuccessDialog = false">
						{{ __("البقاء هنا") }}
					</Button>
					<a
						:href="lastCreatedUrl"
						target="_blank"
						class="flex-1 inline-flex items-center justify-center px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm hover:bg-emerald-700 transition-colors"
					>
						{{ __("فتح في Desk") }}
					</a>
					<Button class="flex-1" variant="solid" theme="green" @click="resetAfterSave">
						{{ __("فاتورة جديدة") }}
					</Button>
				</div>
			</template>
		</Dialog>
	</div>
</template>

<script setup>
import { Button, Dialog } from "frappe-ui"
import { call } from "@/utils/apiWrapper"
import { useToast } from "@/composables/useToast"
import { useUserData } from "@/data/user"
import { session } from "@/data/session"
import router from "@/router"
import { computed, onMounted, ref, watch } from "vue"

const { showSuccess, showError } = useToast()
const { userName } = useUserData()

const userInitial = computed(() => {
	const name = userName.value || "User"
	const parts = String(name).split(" ").filter(Boolean)
	return parts.length >= 2 ? (parts[0][0] + parts[1][0]).toUpperCase() : name.substring(0, 2).toUpperCase()
})

const MAX_ITEMS = 50

// State
const companies = ref([])
const warehouses = ref([])
const selectedCompany = ref("")
const selectedWarehouse = ref("")
const postingDate = ref(new Date().toISOString().split("T")[0])
const dueDate = ref("")
const updateStock = ref(false)
const updatePurchasePrice = ref(false)
const isPaid = ref(false)
const modeOfPayment = ref("Cash")
const modesOfPayment = ref([])
const loadingModesOfPayment = ref(false)
const settingsOpen = ref(false)

const loadingCompanies = ref(false)
const loadingWarehouses = ref(false)

// Supplier search
const supplierSearch = ref("")
const supplierResults = ref([])
const showSupplierResults = ref(false)
const selectedSupplier = ref("")
const selectedSupplierName = ref("")
const supplierSearchRef = ref(null)
let supplierSearchDebounce = null

// Item search
const searchQuery = ref("")
const searchResults = ref([])
const showResults = ref(false)
const searching = ref(false)
const selectedResultIndex = ref(-1)
const searchInputRef = ref(null)

const cart = ref([])
const submitting = ref(false)

const showSuccessDialog = ref(false)
const lastCreatedName = ref("")
const lastCreatedUrl = ref("")
const lastSubmitted = ref(false)

let searchDebounce = null

// Computed
const itemsWithoutPrice = computed(() =>
	cart.value.filter(r => !r.rate || Number(r.rate) <= 0).length
)

const cartTotal = computed(() =>
	cart.value.reduce((sum, r) => sum + (Number(r.qty) || 0) * (Number(r.rate) || 0), 0)
)

const canSubmit = computed(() =>
	!submitting.value &&
	cart.value.length > 0 &&
	itemsWithoutPrice.value === 0 &&
	cart.value.every(r => Number(r.qty) > 0) &&
	selectedCompany.value &&
	selectedWarehouse.value &&
	selectedSupplier.value &&
	postingDate.value
)

// Lifecycle
onMounted(async () => {
	if (!session.isLoggedIn) {
		router.replace({ name: "Login" })
		return
	}
	await Promise.all([loadCompanies(), loadModesOfPayment()])
})

// Watch posting date to default due date
watch(postingDate, (newDate) => {
	if (!dueDate.value && newDate) {
		try {
			const d = new Date(newDate)
			d.setDate(d.getDate() + 30)
			dueDate.value = d.toISOString().split("T")[0]
		} catch (e) {
			dueDate.value = ""
		}
	}
})

// Methods
async function loadCompanies() {
	loadingCompanies.value = true
	try {
		companies.value = await call("bs.baron_servies.api.utilities.get_companies") || []
		if (companies.value.length === 1) {
			selectedCompany.value = companies.value[0].name
			await onCompanyChange()
		} else if (companies.value.length > 1) {
			settingsOpen.value = true
		}
	} catch (e) {
		showError(e?.message || __("فشل تحميل الشركات"))
	} finally {
		loadingCompanies.value = false
	}
}

async function loadModesOfPayment() {
	loadingModesOfPayment.value = true
	try {
		modesOfPayment.value = await call("bs.baron_servies.api.purchase_invoice.get_modes_of_payment") || []
		if (modesOfPayment.value.length > 0 && !modesOfPayment.value.some(m => m.name === modeOfPayment.value)) {
			modeOfPayment.value = modesOfPayment.value[0].name
		}
	} catch (e) {
		showError(e?.message || __("فشل تحميل طرق الدفع"))
		modesOfPayment.value = []
	} finally {
		loadingModesOfPayment.value = false
	}
}

async function onCompanyChange() {
	selectedWarehouse.value = ""
	warehouses.value = []
	selectedSupplier.value = ""
	selectedSupplierName.value = ""
	supplierSearch.value = ""
	cart.value = []
	clearSearch()
	if (!selectedCompany.value) return

	loadingWarehouses.value = true
	try {
		warehouses.value = await call("bs.baron_servies.api.stock_reconciliation.get_warehouses", {
			company: selectedCompany.value,
		}) || []
		if (warehouses.value.length === 1) {
			selectedWarehouse.value = warehouses.value[0].name
		}
		if (warehouses.value.length >= 1 && selectedSupplier.value) {
			settingsOpen.value = false
			focusSearch()
		} else {
			settingsOpen.value = true
		}
	} catch (e) {
		showError(e?.message || __("فشل تحميل المستودعات"))
	} finally {
		loadingWarehouses.value = false
	}
}

// Supplier search
function onSupplierSearchInput() {
	clearTimeout(supplierSearchDebounce)
	selectedSupplier.value = ""
	selectedSupplierName.value = ""
	showSupplierResults.value = true
	if (!supplierSearch.value.trim()) {
		supplierResults.value = []
		showSupplierResults.value = false
		return
	}
	supplierSearchDebounce = setTimeout(() => doSupplierSearch(), 300)
}

function openSupplierResults() {
	if (supplierSearch.value.trim()) {
		showSupplierResults.value = true
	}
}

async function doSupplierSearch() {
	if (!supplierSearch.value.trim()) return
	try {
		supplierResults.value = await call("bs.baron_servies.api.purchase_invoice.get_suppliers_for_purchase_invoice", {
			search_term: supplierSearch.value.trim(),
			limit: 20,
		}) || []
		showSupplierResults.value = supplierResults.value.length > 0
	} catch (e) {
		showError(e?.message || __("فشل البحث عن المورد"))
		supplierResults.value = []
	}
}

function selectSupplier(supplier) {
	selectedSupplier.value = supplier.name
	selectedSupplierName.value = supplier.supplier_name || supplier.name
	supplierSearch.value = ""
	supplierResults.value = []
	showSupplierResults.value = false
	if (selectedWarehouse.value) {
		settingsOpen.value = false
		focusSearch()
	}
}

function clearSupplier() {
	selectedSupplier.value = ""
	selectedSupplierName.value = ""
	supplierSearch.value = ""
	supplierResults.value = []
	showSupplierResults.value = false
}

// Item search
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
	if (!searchQuery.value.trim() || !selectedCompany.value || !selectedWarehouse.value) return
	searching.value = true
	try {
		searchResults.value = await call("bs.baron_servies.api.purchase_invoice.search_items_for_purchase_invoice", {
			search_term: searchQuery.value.trim(),
			company: selectedCompany.value,
			warehouse: selectedWarehouse.value,
			limit: 20,
		}) || []
		if (searchResults.value.length === 1) {
			const term = searchQuery.value.trim()
			const item = searchResults.value[0]
			if (term === item.item_code || (!term.includes(" ") && term.length <= 32)) {
				addItem(item)
				return
			}
		}
		selectedResultIndex.value = searchResults.value.length > 0 ? 0 : -1
	} catch (e) {
		showError(e?.message || __("فشل البحث"))
		searchResults.value = []
	} finally {
		searching.value = false
	}
}

function clearSearch() {
	searchQuery.value = ""
	searchResults.value = []
	showResults.value = false
	selectedResultIndex.value = -1
}

function navigateResults(delta) {
	if (searchResults.value.length === 0) return
	let next = selectedResultIndex.value + delta
	if (next < 0) next = searchResults.value.length - 1
	if (next >= searchResults.value.length) next = 0
	selectedResultIndex.value = next
}

async function selectFirstResult() {
	if (searchResults.value.length === 0 && searchQuery.value.trim()) {
		clearTimeout(searchDebounce)
		await doSearch()
		if (searchResults.value.length === 0) return
	}
	if (searchResults.value.length === 0) return
	const idx = selectedResultIndex.value >= 0 ? selectedResultIndex.value : 0
	addItem(searchResults.value[idx])
}

function addItem(item) {
	if (!item) return
	if (cart.value.length >= MAX_ITEMS) {
		showError(__("بلغت الحد الأقصى ({0} صنف). احفظ الفاتورة الحالية ثم ابدأ فاتورة جديدة.", [MAX_ITEMS]))
		return
	}
	if (cart.value.some(r => r.item_code === item.item_code)) {
		showError(__("الصنف موجود مسبقاً في الفاتورة"))
		return
	}

	const buyingRate = flt(item.buying_price_list_rate) > 0 ? flt(item.buying_price_list_rate) : 0
	const lastRate = flt(item.last_purchase_rate) > 0 ? flt(item.last_purchase_rate) : 0
	const rate = buyingRate || lastRate || 0
	const rateSource = buyingRate > 0 ? "buying_price_list" : (lastRate > 0 ? "last_purchase_rate" : "manual")
	cart.value.unshift({
		item_code: item.item_code,
		item_name: item.item_name,
		stock_uom: item.stock_uom,
		image: item.image,
		actual_qty: item.actual_qty || 0,
		last_purchase_rate: lastRate,
		buying_price_list_rate: buyingRate,
		rate: rate,
		rate_source: rateSource,
		qty: 1,
	})
	clearSearch()
	focusSearch()
}

function removeItem(idx) {
	cart.value.splice(idx, 1)
}

function clearCart() {
	cart.value = []
}

function focusSearch() {
	setTimeout(() => searchInputRef.value?.focus(), 0)
}

function refocusSearch(e) {
	const tag = e.target?.tagName?.toLowerCase()
	if (tag === "input" || tag === "select" || tag === "button" || tag === "a") return
	focusSearch()
}

function formatQty(v) {
	const n = Number(v || 0)
	return Number.isInteger(n) ? String(n) : n.toFixed(3).replace(/\.?0+$/, "")
}

function formatMoney(v) {
	const n = Number(v || 0)
	return n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function flt(v) {
	return Number(v || 0)
}

async function handleSubmit(shouldSubmit = false) {
	if (!canSubmit.value) return
	clearSearch()
	submitting.value = true
	try {
		const payload = cart.value.map(r => ({
			item_code: r.item_code,
			qty: Number(r.qty),
			rate: Number(r.rate),
		}))
		const result = await call("bs.baron_servies.api.purchase_invoice.create_quick_purchase_invoice", {
			company: selectedCompany.value,
			supplier: selectedSupplier.value,
			warehouse: selectedWarehouse.value,
			posting_date: postingDate.value,
			due_date: dueDate.value || undefined,
			update_stock: updateStock.value ? 1 : 0,
			update_purchase_price: updatePurchasePrice.value ? 1 : 0,
			is_paid: isPaid.value ? 1 : 0,
			mode_of_payment: modeOfPayment.value,
			items: payload,
			submit: shouldSubmit ? 1 : 0,
		})
		lastCreatedName.value = result.name
		lastCreatedUrl.value = result.url
		lastSubmitted.value = shouldSubmit
		showSuccessDialog.value = true
		if (shouldSubmit) {
			showSuccess(__("تم حفظ وترحيل فاتورة الشراء {0}", [result.name]))
		} else {
			showSuccess(__("تم حفظ فاتورة الشراء {0} كمسودة", [result.name]))
		}
	} catch (e) {
		const msg = e?.message || e?.toString() || __("فشل حفظ فاتورة الشراء")
		showError(msg)
	} finally {
		submitting.value = false
	}
}

function resetAfterSave() {
	showSuccessDialog.value = false
	cart.value = []
	lastCreatedName.value = ""
	lastCreatedUrl.value = ""
	lastSubmitted.value = false
	focusSearch()
}

async function logout() {
	await session.logout.submit()
}
</script>

<style scoped>
/* Hide number input spinners (up/down arrows) */
input[type="number"]::-webkit-inner-spin-button,
input[type="number"]::-webkit-outer-spin-button {
	-webkit-appearance: none;
	margin: 0;
}
input[type="number"] {
	-moz-appearance: textfield;
}
</style>
