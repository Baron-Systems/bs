<template>
	<div class="w-full">
		<main class="flex flex-col gap-5">
			<PageHeader :title="__('فاتورة شراء سريعة')" :subtitle="__('إنشاء فاتورة شراء كمسودة')" />

			<!-- Settings (collapsible) -->
			<section class="bs-card">
				<button
					type="button"
					class="flex w-full items-center justify-between gap-3 px-4 py-3 text-start sm:px-5"
					@click="settingsOpen = !settingsOpen"
				>
					<span class="flex items-center gap-2">
						<svg class="h-4 w-4 text-slate-400 transition-transform" :class="{ 'rotate-90': settingsOpen }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
						</svg>
						<span class="bs-card-title">{{ __("إعدادات الفاتورة") }}</span>
					</span>
					<span class="truncate text-xs text-slate-500">
						<template v-if="selectedCompany">{{ selectedCompany }}</template>
						<template v-if="selectedWarehouse"> / {{ selectedWarehouse }}</template>
						<template v-if="selectedSupplier"> / {{ selectedSupplierName || selectedSupplier }}</template>
						<template v-if="!selectedCompany || !selectedSupplier"> {{ __("اضغط للإعداد") }}</template>
					</span>
				</button>

				<div v-show="settingsOpen" class="border-t border-slate-100 px-4 pb-4 pt-3 sm:px-5">
					<div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
						<div>
							<label class="bs-label">{{ __("الشركة") }}</label>
							<select v-model="selectedCompany" class="bs-input" :disabled="loadingCompanies" @change="onCompanyChange">
								<option value="" disabled>{{ loadingCompanies ? __("جاري التحميل...") : __("اختر الشركة") }}</option>
								<option v-for="c in companies" :key="c.name" :value="c.name">{{ c.name }}</option>
							</select>
						</div>
						<div>
							<label class="bs-label">{{ __("المستودع") }}</label>
							<select v-model="selectedWarehouse" class="bs-input" :disabled="!selectedCompany || loadingWarehouses">
								<option value="" disabled>{{ loadingWarehouses ? __("جاري التحميل...") : __("اختر المستودع") }}</option>
								<option v-for="w in warehouses" :key="w.name" :value="w.name">{{ w.warehouse_name || w.name }}</option>
							</select>
						</div>
						<div class="relative">
							<label class="bs-label">{{ __("المورد") }}</label>
							<div class="relative">
								<input
									ref="supplierSearchRef"
									v-model="supplierSearch"
									type="text"
									:placeholder="selectedSupplier ? '' : __('ابحث عن مورد...')"
									class="bs-input !pe-9"
									@input="onSupplierSearchInput"
									@focus="openSupplierResults"
								/>
								<div v-if="selectedSupplier" class="pointer-events-none absolute inset-y-0 start-3 flex items-center">
									<span class="truncate text-sm font-semibold text-slate-900">{{ selectedSupplierName || selectedSupplier }}</span>
								</div>
								<button
									v-if="selectedSupplier"
									type="button"
									class="absolute inset-y-0 end-0 flex items-center px-3 text-slate-400 hover:text-rose-600"
									:aria-label="__('مسح')"
									@click="clearSupplier"
								>
									<svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
									</svg>
								</button>
							</div>
							<div v-if="showSupplierResults && supplierResults.length > 0" class="absolute top-full z-30 mt-1 w-full">
								<div class="bs-popover max-h-60 overflow-y-auto">
									<button
										v-for="s in supplierResults"
										:key="s.name"
										type="button"
										class="w-full border-b border-slate-100 px-4 py-2.5 text-start transition-colors last:border-0 hover:bg-slate-50"
										@click="selectSupplier(s)"
									>
										<p class="text-sm font-semibold text-slate-900">{{ s.supplier_name || s.name }}</p>
										<p v-if="s.mobile_no || s.email_id" class="text-[11px] text-slate-400">{{ [s.mobile_no, s.email_id].filter(Boolean).join(" - ") }}</p>
									</button>
								</div>
							</div>
						</div>
						<div>
							<label class="bs-label">{{ __("تاريخ الترحيل") }}</label>
							<input v-model="postingDate" type="date" class="bs-input" />
						</div>
						<div>
							<label class="bs-label">{{ __("تاريخ الاستحقاق") }}</label>
							<input v-model="dueDate" type="date" class="bs-input" />
						</div>
						<div>
							<label class="bs-label">{{ __("الدفع") }}</label>
							<div class="flex items-center gap-2">
								<label class="flex flex-shrink-0 cursor-pointer select-none items-center gap-2 text-sm text-slate-700">
									<input v-model="isPaid" type="checkbox" class="h-4 w-4 rounded border-slate-300 text-emerald-600 focus:ring-emerald-500" />
									{{ __("فاتورة مدفوعة") }}
								</label>
								<select v-if="isPaid" v-model="modeOfPayment" class="bs-input" :disabled="loadingModesOfPayment">
									<option v-for="m in modesOfPayment" :key="m.name" :value="m.name">{{ m.name }}</option>
								</select>
							</div>
						</div>
						<div class="flex flex-col gap-2 sm:col-span-2 lg:col-span-3">
							<label class="flex cursor-pointer select-none items-center gap-2 text-sm text-slate-700">
								<input v-model="updateStock" type="checkbox" class="h-4 w-4 rounded border-slate-300 text-emerald-600 focus:ring-emerald-500" />
								{{ __("تحديث المخزون عند الحفظ") }}
							</label>
							<label class="flex cursor-pointer select-none items-center gap-2 text-sm text-slate-700">
								<input v-model="updatePurchasePrice" type="checkbox" class="h-4 w-4 rounded border-slate-300 text-emerald-600 focus:ring-emerald-500" />
								{{ __("تغيير سعر الشراء بناءً على الأسعار المدخلة الجديدة") }}
							</label>
						</div>
					</div>
				</div>
			</section>

			<!-- Not configured hint -->
			<section v-if="!selectedCompany || !selectedWarehouse || !selectedSupplier" class="rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-700">
				{{ __("اختر شركة ومستودع ومورد للبدء") }}
			</section>

			<!-- Work area -->
			<section
				v-if="selectedCompany && selectedWarehouse && selectedSupplier"
				class="bs-card flex min-h-[400px] flex-1 flex-col"
				@click="refocusSearch($event)"
			>
				<!-- Search -->
				<div class="sticky top-14 z-20 rounded-t-2xl border-b border-slate-100 bg-white p-4 sm:px-5">
					<div class="flex items-stretch gap-2">
						<div class="relative flex-1">
							<div class="pointer-events-none absolute inset-y-0 start-0 flex items-center ps-3">
								<svg v-if="!searching" class="h-5 w-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
								</svg>
								<div v-else class="h-4 w-4 animate-spin rounded-full border-b-2 border-emerald-500"></div>
							</div>
							<input
								ref="searchInputRef"
								v-model="searchQuery"
								type="text"
								:placeholder="__('ابحث عن صنف بالاسم أو الكود أو امسح الباركود...')"
								class="bs-input !pe-10 !ps-10"
								autocomplete="off"
								@input="onSearchInput"
								@keydown.enter.prevent="selectFirstResult"
								@keydown.down.prevent="navigateResults(1)"
								@keydown.up.prevent="navigateResults(-1)"
								@keydown.escape="clearSearch"
							/>
							<button v-if="searchQuery" type="button" class="absolute inset-y-0 end-0 flex items-center pe-3" :aria-label="__('مسح')" @click="clearSearch">
								<svg class="h-5 w-5 text-slate-400 hover:text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
								</svg>
							</button>
						</div>
						<button type="button" class="bs-btn bs-btn-secondary flex-shrink-0" :title="__('أصناف سبق شراؤها من هذا المورد')" @click="openSupplierItems">
							<svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
							</svg>
							<span class="hidden sm:inline">{{ __("مشتريات المورد") }}</span>
						</button>
						<button type="button" class="bs-btn bs-btn-secondary flex-shrink-0" :title="__('إضافة صنف جديد')" @click="openNewItem">
							<svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
							</svg>
							<span class="hidden sm:inline">{{ __("صنف جديد") }}</span>
						</button>
					</div>

					<!-- Results -->
					<div v-if="showResults && (searchResults.length > 0 || (searchQuery.length >= 1 && !searching))" class="relative z-10 mt-2">
						<div class="bs-popover max-h-80 overflow-y-auto">
							<template v-if="searchResults.length > 0">
								<button
									v-for="(item, index) in searchResults"
									:key="item.item_code"
									type="button"
									class="flex w-full items-center gap-3 border-b border-slate-100 px-4 py-2.5 text-start transition-colors last:border-0"
									:class="selectedResultIndex === index ? 'bg-emerald-50' : 'hover:bg-slate-50'"
									@click="addItem(item)"
									@mouseenter="selectedResultIndex = index"
								>
									<div class="flex h-9 w-9 flex-shrink-0 items-center justify-center overflow-hidden rounded-lg bg-slate-100">
										<img v-if="item.image" :src="item.image" :alt="item.item_name" class="h-full w-full object-cover" />
										<svg v-else class="h-4 w-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="BOX_ICON" />
										</svg>
									</div>
									<div class="min-w-0 flex-1">
										<p class="truncate text-sm font-semibold text-slate-900">{{ item.item_name }}</p>
										<p class="truncate text-[11px] text-slate-400">{{ item.item_code }}</p>
									</div>
									<div class="flex flex-shrink-0 flex-col items-end gap-0.5">
										<span class="bs-badge" :class="(item.actual_qty || 0) > 0 ? 'bs-badge-green' : 'bs-badge-red'">
											{{ formatQty(item.actual_qty) }} {{ item.stock_uom }}
										</span>
										<span v-if="item.last_purchase_rate > 0" class="text-[10px] text-emerald-600">{{ formatMoney(item.last_purchase_rate) }}</span>
									</div>
								</button>
							</template>
							<div v-else class="px-4 py-6 text-center text-sm text-slate-500">{{ __("لا توجد نتائج") }}</div>
						</div>
					</div>
				</div>

				<!-- List header -->
				<div class="flex items-center justify-between border-b border-slate-100 px-4 py-2.5 sm:px-5">
					<h2 class="bs-card-title">
						{{ __("أصناف الفاتورة") }}
						<span v-if="cart.length > 0" class="ms-2 text-xs font-normal text-slate-400">{{ __("{0} / {1} صنف", [cart.length, MAX_ITEMS]) }}</span>
					</h2>
					<button v-if="cart.length > 0" type="button" class="bs-btn bs-btn-ghost bs-btn-sm !text-rose-600" @click="clearCart">
						{{ __("مسح الكل") }}
					</button>
				</div>

				<!-- Items -->
				<div class="flex-1 overflow-x-auto">
					<div v-if="cart.length === 0" class="bs-empty">
						<svg class="h-12 w-12 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
						</svg>
						<p>{{ __("ابحث وأضف أصنافاً لإنشاء الفاتورة") }}</p>
					</div>

					<table v-else class="bs-table w-full min-w-[820px] table-fixed">
						<colgroup>
							<col class="w-10" />
							<col />
							<col class="w-24" />
							<col class="w-24" />
							<col class="w-32" />
							<col class="w-40" />
							<col class="w-32" />
							<col class="w-12" />
						</colgroup>
						<thead class="sticky top-0 z-10">
							<tr>
								<th class="text-center">#</th>
								<th class="text-start">{{ __("الصنف") }}</th>
								<th class="text-center">{{ __("الرصيد") }}</th>
								<th class="text-center">{{ __("الوحدة") }}</th>
								<th class="text-center">{{ __("الكمية") }}</th>
								<th class="text-center">{{ __("سعر الشراء") }}</th>
								<th class="text-center">{{ __("الإجمالي") }}</th>
								<th></th>
							</tr>
						</thead>
						<tbody>
							<tr v-for="(row, idx) in cart" :key="row.item_code">
								<td class="text-center text-xs tabular-nums text-slate-400">{{ cart.length - idx }}</td>
								<td>
									<div class="flex items-center gap-2.5">
										<div class="flex h-9 w-9 flex-shrink-0 items-center justify-center overflow-hidden rounded-lg bg-slate-100">
											<img v-if="row.image" :src="row.image" :alt="row.item_name" class="h-full w-full object-cover" />
											<svg v-else class="h-4 w-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="BOX_ICON" />
											</svg>
										</div>
										<div class="min-w-0 flex-1">
											<div v-if="editingCode === row.item_code" class="flex items-center gap-1">
												<input
													ref="nameInputRef"
													v-model="editingName"
													type="text"
													maxlength="140"
													class="bs-input bs-input-sm"
													@keydown.enter.prevent="saveName(row)"
													@keydown.escape.prevent="cancelEditName"
												/>
												<button type="button" class="bs-icon-btn !h-8 !w-8 !text-emerald-600 hover:!bg-emerald-50" :title="__('حفظ')" :disabled="savingName" @click="saveName(row)">
													<svg v-if="!savingName" class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7" /></svg>
													<span v-else class="h-3.5 w-3.5 animate-spin rounded-full border-2 border-emerald-500 border-t-transparent"></span>
												</button>
												<button type="button" class="bs-icon-btn !h-8 !w-8" :title="__('إلغاء')" :disabled="savingName" @click="cancelEditName">
													<svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
												</button>
											</div>
											<div v-else class="flex min-w-0 items-center gap-1">
												<p class="truncate font-semibold text-slate-900" :title="row.item_name">{{ row.item_name }}</p>
												<button
													type="button"
													class="flex-shrink-0 rounded-md p-1 text-slate-400 transition hover:bg-blue-50 hover:text-blue-600"
													:title="__('تعديل اسم الصنف')"
													:aria-label="__('تعديل اسم الصنف')"
													@click="startEditName(row)"
												>
													<svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
														<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
													</svg>
												</button>
											</div>
											<p class="truncate text-[11px] text-slate-400">{{ row.item_code }}</p>
										</div>
									</div>
								</td>
								<td class="text-center tabular-nums" :class="(row.actual_qty || 0) > 0 ? 'text-slate-700' : 'text-slate-400'">
									{{ formatQty(row.actual_qty) }}
								</td>
								<td class="text-center">
									<span class="bs-badge bs-badge-neutral">{{ row.stock_uom || "—" }}</span>
								</td>
								<td class="text-center">
									<input
										v-model.number="row.qty"
										type="number"
										min="0"
										step="any"
										class="bs-input bs-input-sm text-center tabular-nums"
										:class="Number(row.qty) > 0 ? '' : '!border-rose-300 !bg-rose-50'"
										@focus="$event.target.select()"
										@click="$event.target.select()"
										@keydown.enter.prevent="focusSearch"
									/>
								</td>
								<td class="text-center">
									<input
										v-model.number="row.rate"
										type="number"
										min="0"
										step="any"
										class="bs-input bs-input-sm text-center tabular-nums"
										:class="(row.rate || 0) > 0 ? '' : '!border-rose-300 !bg-rose-50'"
										@focus="$event.target.select()"
										@click="$event.target.select()"
										@keydown.enter.prevent="focusSearch"
									/>
									<p class="mt-0.5 text-[10px] text-slate-400">{{ rateSourceLabel(row) }}</p>
								</td>
								<td class="text-center font-semibold tabular-nums text-slate-900">{{ formatMoney(row.qty * row.rate) }}</td>
								<td class="text-center">
									<button type="button" class="rounded-md p-1.5 text-slate-400 transition hover:bg-rose-50 hover:text-rose-600" :aria-label="__('حذف')" @click="removeItem(idx)">
										<svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6M1 7h22M9 7V4a1 1 0 011-1h4a1 1 0 011 1v3" />
										</svg>
									</button>
								</td>
							</tr>
						</tbody>
						<tfoot>
							<tr class="border-t border-slate-200 bg-slate-50">
								<td colspan="6" class="px-3 py-2.5 text-end text-sm font-bold text-slate-700">{{ __("إجمالي الفاتورة") }}</td>
								<td class="px-3 py-2.5 text-center text-sm font-extrabold tabular-nums text-emerald-700">{{ formatMoney(cartTotal) }}</td>
								<td></td>
							</tr>
						</tfoot>
					</table>
				</div>

				<!-- Footer -->
				<div v-if="cart.length > 0" class="flex flex-col items-stretch justify-between gap-3 rounded-b-2xl border-t border-slate-100 px-4 py-3 sm:flex-row sm:items-center sm:px-5">
					<div class="text-xs">
						<p v-if="itemsWithoutPrice > 0" class="text-rose-600">{{ __("{0} صنف بدون سعر شراء", [itemsWithoutPrice]) }}</p>
						<p v-else-if="cart.length >= MAX_ITEMS" class="text-amber-600">{{ __("بلغت الحد الأقصى ({0} صنف) - احفظ ثم ابدأ فاتورة جديدة", [MAX_ITEMS]) }}</p>
						<p v-else class="text-slate-500">{{ __("جميع الأصناف لها سعر شراء") }}</p>
					</div>
					<div class="flex flex-wrap items-center gap-2">
						<button type="button" class="bs-btn bs-btn-secondary" @click="clearCart">{{ __("مسح") }}</button>
						<button type="button" class="bs-btn bs-btn-secondary" :disabled="!canSubmit" @click="handleSubmit(false)">
							<span v-if="submitting && !submittingFinal" class="h-4 w-4 animate-spin rounded-full border-2 border-slate-400 border-t-transparent"></span>
							{{ __("حفظ كمسودة") }}
						</button>
						<button type="button" class="bs-btn bs-btn-success" :disabled="!canSubmit" @click="handleSubmit(true)">
							<span v-if="submitting && submittingFinal" class="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"></span>
							{{ __("حفظ وترحيل") }}
						</button>
					</div>
				</div>
			</section>
		</main>

		<!-- Supplier purchase history -->
		<Dialog v-model="supplierItemsOpen" :options="{ title: __('مشتريات سابقة من {0}', [selectedSupplierName || selectedSupplier]), size: '4xl' }">
			<template #body-content>
				<div class="flex flex-col gap-3">
					<div class="flex flex-wrap items-center gap-2">
						<input v-model="supplierItemsFilter" type="text" class="bs-input bs-input-sm max-w-xs" :placeholder="__('تصفية الأصناف...')" />
						<span class="text-xs text-slate-500">{{ __("{0} صنف", [filteredSupplierItems.length]) }}</span>
						<button
							v-if="selectableSupplierItems.length"
							type="button"
							class="bs-btn bs-btn-ghost bs-btn-sm ms-auto"
							@click="toggleAllSupplierItems"
						>
							{{ allSupplierItemsSelected ? __("إلغاء تحديد الكل") : __("تحديد الكل") }}
						</button>
					</div>

					<div v-if="loadingSupplierItems" class="bs-empty">{{ __("جاري التحميل...") }}</div>
					<div v-else-if="!supplierItems.length" class="bs-empty">{{ __("لا توجد مشتريات مرحّلة سابقة من هذا المورد") }}</div>
					<div v-else class="bs-table-wrap max-h-[55vh]">
						<table class="bs-table w-full">
							<thead class="sticky top-0 z-10">
								<tr>
									<th class="w-10"></th>
									<th class="text-start">{{ __("الصنف") }}</th>
									<th class="text-center">{{ __("آخر شراء") }}</th>
									<th class="text-center">{{ __("آخر سعر") }}</th>
									<th class="text-center">{{ __("مرات الشراء") }}</th>
									<th class="text-center">{{ __("الرصيد") }}</th>
									<th class="text-center">{{ __("الوحدة") }}</th>
								</tr>
							</thead>
							<tbody>
								<tr
									v-for="item in filteredSupplierItems"
									:key="item.item_code"
									class="cursor-pointer"
									:class="inCart(item.item_code) ? 'opacity-50' : ''"
									@click="toggleSupplierItem(item)"
								>
									<td class="text-center">
										<span v-if="inCart(item.item_code)" class="bs-badge bs-badge-green">{{ __("مضاف") }}</span>
										<input
											v-else
											type="checkbox"
											class="h-4 w-4 rounded border-slate-300 text-emerald-600 focus:ring-emerald-500"
											:checked="selectedSupplierItems.has(item.item_code)"
											@click.stop="toggleSupplierItem(item)"
										/>
									</td>
									<td>
										<p class="font-semibold text-slate-900">{{ item.item_name }}</p>
										<p class="text-[11px] text-slate-400">{{ item.item_code }}</p>
									</td>
									<td class="text-center tabular-nums text-slate-600">{{ formatDate(item.last_supplier_date) }}</td>
									<td class="text-center font-semibold tabular-nums">{{ formatMoney(item.last_supplier_rate) }}</td>
									<td class="text-center tabular-nums text-slate-600">{{ item.invoice_count }}</td>
									<td class="text-center tabular-nums" :class="(item.actual_qty || 0) > 0 ? 'text-slate-700' : 'text-slate-400'">{{ formatQty(item.actual_qty) }}</td>
									<td class="text-center"><span class="bs-badge bs-badge-neutral">{{ item.stock_uom }}</span></td>
								</tr>
							</tbody>
						</table>
					</div>
				</div>
			</template>
			<template #actions>
				<div class="flex w-full items-center justify-between gap-2">
					<p class="text-xs text-slate-500">{{ __("تُضاف الأصناف بآخر سعر شراء من هذا المورد") }}</p>
					<div class="flex gap-2">
						<button type="button" class="bs-btn bs-btn-secondary" @click="supplierItemsOpen = false">{{ __("إغلاق") }}</button>
						<button type="button" class="bs-btn bs-btn-success" :disabled="!selectedSupplierItems.size" @click="addSelectedSupplierItems">
							{{ __("إضافة ({0}) إلى الفاتورة", [selectedSupplierItems.size]) }}
						</button>
					</div>
				</div>
			</template>
		</Dialog>

		<!-- New item -->
		<Dialog v-model="newItemOpen" :options="{ title: __('صنف جديد'), size: 'lg' }">
			<template #body-content>
				<form class="grid grid-cols-1 gap-4 sm:grid-cols-2" @submit.prevent="createNewItem">
					<div class="sm:col-span-2">
						<label class="bs-label">{{ __("اسم الصنف") }} <span class="text-rose-500">*</span></label>
						<input ref="newItemNameRef" v-model="newItem.item_name" type="text" maxlength="140" class="bs-input" />
					</div>
					<div>
						<label class="bs-label">{{ __("الكود") }}</label>
						<input v-model="newItem.item_code" type="text" class="bs-input" dir="ltr" :placeholder="newItemOptions.suggested_code" />
						<p class="mt-1 text-[11px] text-slate-400">{{ __("يُولَّد تلقائيًا ({0}) إن تُرك فارغًا", [newItemOptions.suggested_code || "—"]) }}</p>
					</div>
					<div>
						<label class="bs-label">{{ __("الباركود") }}</label>
						<input v-model="newItem.barcode" type="text" class="bs-input" dir="ltr" :placeholder="__('امسح أو اكتب الباركود')" />
					</div>
					<div>
						<label class="bs-label">{{ __("المجموعة") }} <span class="text-rose-500">*</span></label>
						<select v-model="newItem.item_group" class="bs-input">
							<option value="" disabled>{{ __("اختر المجموعة") }}</option>
							<option v-for="g in newItemOptions.item_groups" :key="g" :value="g">{{ g }}</option>
						</select>
					</div>
					<div>
						<label class="bs-label">{{ __("الوحدة") }} <span class="text-rose-500">*</span></label>
						<select v-model="newItem.stock_uom" class="bs-input">
							<option v-for="u in newItemOptions.uoms" :key="u" :value="u">{{ u }}</option>
						</select>
					</div>
					<div>
						<label class="bs-label">{{ __("سعر الشراء") }}</label>
						<input v-model.number="newItem.buying_rate" type="number" min="0" step="any" class="bs-input tabular-nums" dir="ltr" />
						<p class="mt-1 text-[11px] text-slate-400">{{ newItemOptions.buying_price_list ? __("يُحفظ في {0} ويُستخدم في الفاتورة", [newItemOptions.buying_price_list]) : __("يُستخدم في الفاتورة") }}</p>
					</div>
					<div>
						<label class="bs-label">{{ __("سعر البيع") }}</label>
						<input v-model.number="newItem.selling_rate" type="number" min="0" step="any" class="bs-input tabular-nums" dir="ltr" />
						<p v-if="newItemOptions.selling_price_list" class="mt-1 text-[11px] text-slate-400">{{ __("يُحفظ في {0}", [newItemOptions.selling_price_list]) }}</p>
					</div>
					<button type="submit" class="hidden"></button>
				</form>
			</template>
			<template #actions>
				<div class="flex w-full justify-end gap-2">
					<button type="button" class="bs-btn bs-btn-secondary" @click="newItemOpen = false">{{ __("إلغاء") }}</button>
					<button type="button" class="bs-btn bs-btn-success" :disabled="creatingItem" @click="createNewItem">
						<span v-if="creatingItem" class="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"></span>
						{{ __("إنشاء وإضافة للفاتورة") }}
					</button>
				</div>
			</template>
		</Dialog>

		<!-- Success Dialog -->
		<Dialog v-model="showSuccessDialog" :options="{ title: __('تم الحفظ'), size: 'sm' }">
			<template #body-content>
				<div class="flex flex-col items-center gap-3 py-4 text-center">
					<div class="flex h-14 w-14 items-center justify-center rounded-full bg-emerald-100">
						<svg class="h-7 w-7 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
						</svg>
					</div>
					<p class="text-sm text-slate-700">
						{{ lastSubmitted ? __("تم حفظ وترحيل فاتورة الشراء بنجاح") : __("تم إنشاء فاتورة الشراء كمسودة بنجاح") }}
					</p>
					<p class="text-xs text-slate-500">{{ __("رقم الفاتورة: {0}", [lastCreatedName]) }}</p>
				</div>
			</template>
			<template #actions>
				<div class="flex w-full gap-2">
					<button type="button" class="bs-btn bs-btn-secondary flex-1" @click="showSuccessDialog = false">{{ __("البقاء هنا") }}</button>
					<a :href="lastCreatedUrl" target="_blank" class="bs-btn bs-btn-primary flex-1">{{ __("فتح في Desk") }}</a>
					<button type="button" class="bs-btn bs-btn-success flex-1" @click="resetAfterSave">{{ __("فاتورة جديدة") }}</button>
				</div>
			</template>
		</Dialog>
	</div>
</template>

<script setup>
import PageHeader from "@/components/ui/PageHeader.vue"
import { Dialog } from "frappe-ui"
import { call } from "@/utils/apiWrapper"
import { useToast } from "@/composables/useToast"
import { session } from "@/data/session"
import router from "@/router"
import { computed, nextTick, onMounted, ref, watch } from "vue"

const { showSuccess, showError } = useToast()


const MAX_ITEMS = 50
const BOX_ICON = "M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"

const RATE_SOURCES = {
	buying_price_list: "قائمة أسعار الشراء",
	last_purchase_rate: "آخر سعر شراء",
	supplier_last_rate: "آخر سعر من المورد",
}

function rateSourceLabel(row) {
	return __(RATE_SOURCES[row.rate_source] || "يدوي")
}

// Inline item-name editing (pencil next to the name)
const editingCode = ref("")
const editingName = ref("")
const savingName = ref(false)
const nameInputRef = ref(null)

async function startEditName(row) {
	editingCode.value = row.item_code
	editingName.value = row.item_name
	await nextTick()
	const el = Array.isArray(nameInputRef.value) ? nameInputRef.value[0] : nameInputRef.value
	el?.focus()
	el?.select()
}

function cancelEditName() {
	editingCode.value = ""
	editingName.value = ""
	focusSearch()
}

async function saveName(row) {
	const name = editingName.value.trim()
	if (!name) return showError(__("اسم الصنف مطلوب"))
	if (name === row.item_name) return cancelEditName()
	savingName.value = true
	try {
		const res = await call("bs.baron_servies.api.stock_reconciliation.update_item_name", {
			item_code: row.item_code,
			item_name: name,
		})
		row.item_name = res.item_name
		showSuccess(__("تم تعديل اسم الصنف"))
		cancelEditName()
	} catch (e) {
		showError(e?.message || __("فشل تعديل اسم الصنف"))
	} finally {
		savingName.value = false
	}
}

// Supplier purchase history dialog
const supplierItemsOpen = ref(false)
const supplierItems = ref([])
const supplierItemsFor = ref("")
const loadingSupplierItems = ref(false)
const supplierItemsFilter = ref("")
const selectedSupplierItems = ref(new Set())

const inCart = (code) => cart.value.some((r) => r.item_code === code)

const filteredSupplierItems = computed(() => {
	const q = supplierItemsFilter.value.trim().toLowerCase()
	if (!q) return supplierItems.value
	return supplierItems.value.filter((it) =>
		(it.item_name || "").toLowerCase().includes(q) || (it.item_code || "").toLowerCase().includes(q)
	)
})
const selectableSupplierItems = computed(() => filteredSupplierItems.value.filter((it) => !inCart(it.item_code)))
const allSupplierItemsSelected = computed(() =>
	selectableSupplierItems.value.length > 0 && selectableSupplierItems.value.every((it) => selectedSupplierItems.value.has(it.item_code))
)

async function openSupplierItems() {
	supplierItemsOpen.value = true
	supplierItemsFilter.value = ""
	selectedSupplierItems.value = new Set()
	const key = `${selectedSupplier.value}|${selectedCompany.value}|${selectedWarehouse.value}`
	if (supplierItemsFor.value === key) return
	loadingSupplierItems.value = true
	try {
		supplierItems.value = await call("bs.baron_servies.api.purchase_invoice.get_supplier_purchased_items", {
			supplier: selectedSupplier.value,
			company: selectedCompany.value,
			warehouse: selectedWarehouse.value,
		}) || []
		supplierItemsFor.value = key
	} catch (e) {
		supplierItems.value = []
		showError(e?.message || __("فشل تحميل مشتريات المورد"))
	} finally {
		loadingSupplierItems.value = false
	}
}

function toggleSupplierItem(item) {
	if (inCart(item.item_code)) return
	const next = new Set(selectedSupplierItems.value)
	next.has(item.item_code) ? next.delete(item.item_code) : next.add(item.item_code)
	selectedSupplierItems.value = next
}

function toggleAllSupplierItems() {
	const next = new Set(selectedSupplierItems.value)
	if (allSupplierItemsSelected.value) selectableSupplierItems.value.forEach((it) => next.delete(it.item_code))
	else selectableSupplierItems.value.forEach((it) => next.add(it.item_code))
	selectedSupplierItems.value = next
}

function addSelectedSupplierItems() {
	const room = MAX_ITEMS - cart.value.length
	const picked = supplierItems.value.filter((it) => selectedSupplierItems.value.has(it.item_code) && !inCart(it.item_code))
	if (picked.length > room) {
		showError(__("يمكن إضافة {0} صنف فقط (الحد الأقصى {1})", [room, MAX_ITEMS]))
		return
	}
	// keep the dialog's order (most recently bought first) at the top of the invoice
	for (const it of [...picked].reverse()) {
		const supplierRate = flt(it.last_supplier_rate)
		cart.value.unshift({
			item_code: it.item_code,
			item_name: it.item_name,
			stock_uom: it.stock_uom,
			image: it.image,
			actual_qty: it.actual_qty || 0,
			last_purchase_rate: flt(it.last_purchase_rate),
			buying_price_list_rate: flt(it.buying_price_list_rate),
			rate: supplierRate || flt(it.buying_price_list_rate) || flt(it.last_purchase_rate),
			rate_source: supplierRate ? "supplier_last_rate" : flt(it.buying_price_list_rate) ? "buying_price_list" : flt(it.last_purchase_rate) ? "last_purchase_rate" : "manual",
			qty: 1,
		})
	}
	showSuccess(__("تمت إضافة {0} صنف", [picked.length]))
	supplierItemsOpen.value = false
	focusSearch()
}

// New item dialog
const GROUP_KEY = "bs_qpi_last_item_group"
const newItemOpen = ref(false)
const creatingItem = ref(false)
const newItemNameRef = ref(null)
const newItemOptions = ref({ item_groups: [], uoms: [], suggested_code: "" })
const newItem = ref({})

function readLastGroup() {
	try { return localStorage.getItem(GROUP_KEY) || "" } catch { return "" }
}

async function openNewItem() {
	if (cart.value.length >= MAX_ITEMS) {
		showError(__("بلغت الحد الأقصى ({0} صنف). احفظ الفاتورة الحالية ثم ابدأ فاتورة جديدة.", [MAX_ITEMS]))
		return
	}
	// a search that found nothing becomes the new item's name (or barcode if it looks like one)
	const term = searchQuery.value.trim()
	const looksLikeBarcode = /^\d{6,}$/.test(term)
	newItem.value = {
		item_name: looksLikeBarcode ? "" : term,
		item_code: "",
		barcode: looksLikeBarcode ? term : "",
		item_group: "",
		stock_uom: "",
		buying_rate: null,
		selling_rate: null,
	}
	newItemOpen.value = true
	try {
		newItemOptions.value = await call("bs.baron_servies.api.purchase_invoice.get_new_item_options", { company: selectedCompany.value })
		const groups = newItemOptions.value.item_groups || []
		const last = readLastGroup()
		newItem.value.item_group = groups.includes(last) ? last : (newItemOptions.value.default_item_group || (groups.length === 1 ? groups[0] : ""))
		newItem.value.stock_uom = newItemOptions.value.default_uom || newItemOptions.value.uoms?.[0] || ""
	} catch (e) {
		showError(e?.message || __("فشل تحميل خيارات الصنف"))
		newItemOpen.value = false
		return
	}
	await nextTick()
	newItemNameRef.value?.focus()
}

async function createNewItem() {
	const d = newItem.value
	if (!d.item_name?.trim()) return showError(__("اسم الصنف مطلوب"))
	if (!d.item_group) return showError(__("يرجى اختيار مجموعة الصنف"))
	if (!d.stock_uom) return showError(__("يرجى اختيار الوحدة"))
	creatingItem.value = true
	try {
		const item = await call("bs.baron_servies.api.purchase_invoice.create_quick_item", {
			data: JSON.stringify(d),
			company: selectedCompany.value,
			warehouse: selectedWarehouse.value,
		})
		try { localStorage.setItem(GROUP_KEY, d.item_group) } catch { /* not persisted */ }
		const rate = Number(d.buying_rate) || 0
		cart.value.unshift({
			item_code: item.item_code,
			item_name: item.item_name,
			stock_uom: item.stock_uom,
			image: item.image,
			actual_qty: item.actual_qty || 0,
			last_purchase_rate: 0,
			buying_price_list_rate: rate,
			rate,
			rate_source: rate ? "buying_price_list" : "manual",
			qty: 1,
		})
		supplierItemsFor.value = ""
		showSuccess(__("تم إنشاء الصنف {0} ({1}) وإضافته للفاتورة", [item.item_name, item.item_code]))
		newItemOpen.value = false
		clearSearch()
		focusSearch()
	} catch (e) {
		showError(e?.message || __("فشل إنشاء الصنف"))
	} finally {
		creatingItem.value = false
	}
}

function formatDate(v) {
	if (!v) return "—"
	const [y, m, d] = String(v).slice(0, 10).split("-")
	return `${d}/${m}/${y}`
}

// State
const companies = ref([])
const warehouses = ref([])
const selectedCompany = ref("")
const selectedWarehouse = ref("")
const postingDate = ref(new Date().toISOString().split("T")[0])
const dueDate = ref("")
// On by default: purchases are not received through Purchase Receipts, so the invoice must move stock
const updateStock = ref(true)
const updatePurchasePrice = ref(true)
const isPaid = ref(true)
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
const submittingFinal = ref(false)

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
	// clicks inside controls (incl. icons inside buttons) keep their own focus
	if (editingCode.value || supplierItemsOpen.value || newItemOpen.value || e.target?.closest?.("input, select, textarea, button, a")) return
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
	submittingFinal.value = shouldSubmit
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
	supplierItemsFor.value = "" // history changed — reload next time
	cart.value = []
	lastCreatedName.value = ""
	lastCreatedUrl.value = ""
	lastSubmitted.value = false
	focusSearch()
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
