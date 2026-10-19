<template>
	<div ref="root" class="flex flex-col gap-4" :class="fullscreen ? 'min-h-screen overflow-auto bg-slate-50 p-4 sm:p-6' : ''">
		<!-- Clock -->
		<section class="bs-card flex flex-wrap items-center justify-between gap-4 p-4 sm:p-5">
			<div>
				<p class="text-4xl font-extrabold tabular-nums tracking-tight text-slate-900 sm:text-5xl" dir="ltr">{{ clock }}</p>
				<p class="mt-1 text-sm text-slate-500">{{ formatLongDate(board.date) }}</p>
			</div>
			<div class="flex flex-wrap items-center gap-2">
				<span class="bs-badge bs-badge-green">{{ __("داخل الآن: {0}", [countIn]) }}</span>
				<span class="bs-badge bs-badge-neutral">{{ __("لم يسجلوا: {0}", [countNone]) }}</span>
				<button type="button" class="bs-btn bs-btn-secondary bs-btn-sm" @click="toggleFullscreen">
					{{ fullscreen ? __("خروج من ملء الشاشة") : __("وضع الجهاز (ملء الشاشة)") }}
				</button>
			</div>
		</section>

		<!-- Error banner (inline so it is visible in fullscreen, where toasts are hidden) -->
		<section v-if="errorMsg" class="rounded-2xl bg-rose-600 p-4 text-center text-base font-bold text-white shadow-lg">
			{{ errorMsg }}
		</section>

		<!-- Result banner -->
		<transition name="fade">
			<section
				v-if="result"
				class="rounded-2xl p-5 text-center text-white shadow-lg"
				:class="result.log_type === 'IN' ? 'bg-emerald-600' : 'bg-blue-600'"
			>
				<p class="text-2xl font-extrabold">
					{{ result.log_type === "IN" ? __("تم تسجيل الدخول") : __("تم تسجيل الخروج") }} — {{ result.employee_name }}
				</p>
				<p class="mt-1 text-lg tabular-nums" dir="ltr">{{ result.time }}</p>
				<p v-if="result.log_type === 'IN' && result.late_minutes" class="mt-1 text-sm font-semibold text-amber-100">
					{{ __("متأخر {0} دقيقة", [result.late_minutes]) }}
				</p>
				<p v-if="result.log_type === 'OUT'" class="mt-1 text-sm text-blue-100">
					{{ __("ساعات العمل: {0}", [formatHours(result.working_hours)]) }}
					<span v-if="result.overtime_hours"> — {{ __("إضافي: {0}", [formatHours(result.overtime_hours)]) }}</span>
				</p>
			</section>
		</transition>

		<div class="grid grid-cols-1 gap-4 lg:grid-cols-3">
			<!-- Employees -->
			<section class="bs-card p-4 lg:col-span-2">
				<input
					ref="searchInput"
					v-model="search"
					type="text"
					class="bs-input mb-3 !py-3 !text-base"
					:placeholder="__('ابحث باسمك أو رقمك الوظيفي...')"
					@keydown.enter.prevent="filtered.length === 1 && select(filtered[0])"
				/>
				<div v-if="loading && !board.rows.length" class="bs-empty">{{ __("جاري التحميل...") }}</div>
				<div v-else-if="!filtered.length" class="bs-empty">{{ __("لا يوجد موظفون") }}</div>
				<div v-else class="grid grid-cols-1 gap-2 sm:grid-cols-2 xl:grid-cols-3">
					<button
						v-for="row in filtered"
						:key="row.employee"
						type="button"
						class="flex items-center gap-3 rounded-xl border p-3 text-start transition"
						:class="selected?.employee === row.employee ? 'border-blue-500 bg-blue-50 ring-4 ring-blue-500/10' : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50'"
						@click="select(row)"
					>
						<span class="h-2.5 w-2.5 flex-shrink-0 rounded-full" :class="STATE[row.state].dot"></span>
						<div class="min-w-0 flex-1">
							<p class="truncate font-semibold text-slate-900">{{ row.employee_name }}</p>
							<p class="truncate text-[11px] text-slate-500">{{ stateText(row) }}</p>
						</div>
					</button>
				</div>
			</section>

			<!-- Punch panel + log -->
			<div class="flex flex-col gap-4">
				<section class="bs-card p-4">
					<div v-if="!selected" class="bs-empty !py-8">{{ __("اختر موظفًا لتسجيل الدخول أو الخروج") }}</div>
					<template v-else>
						<p class="text-lg font-bold text-slate-900">{{ selected.employee_name }}</p>
						<p class="text-xs text-slate-500">{{ selected.designation || selected.employee }}</p>
						<dl class="mt-3 space-y-1.5 text-sm">
							<div class="flex justify-between">
								<dt class="text-slate-500">{{ __("الدوام") }}</dt>
								<dd class="tabular-nums" dir="ltr">{{ selected.shift_start || "—" }} → {{ selected.shift_end || "—" }}</dd>
							</div>
							<div v-if="selected.check_in" class="flex justify-between">
								<dt class="text-slate-500">{{ __("الدخول") }}</dt>
								<dd class="tabular-nums" dir="ltr">{{ selected.check_in }}</dd>
							</div>
							<div v-if="selected.check_out" class="flex justify-between">
								<dt class="text-slate-500">{{ __("الخروج") }}</dt>
								<dd class="tabular-nums" dir="ltr">{{ selected.check_out }}</dd>
							</div>
						</dl>

						<p v-if="selected.state === 'leave'" class="mt-4 rounded-xl bg-sky-50 p-3 text-center text-sm font-semibold text-sky-700">
							{{ __("في إجازة اليوم") }}
						</p>
						<p v-else-if="selected.state === 'done'" class="mt-4 rounded-xl bg-slate-100 p-3 text-center text-sm font-semibold text-slate-600">
							{{ __("أنهى دوام اليوم") }}
						</p>
						<template v-else>
							<p v-if="!selected.is_work_day && selected.state === 'out_none'" class="mt-3 rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-700">
								{{ __("اليوم ليس يوم عمل لهذا الموظف — الساعات تُحسب إضافية إن سُمح بالتسجيل") }}
							</p>
							<div v-if="board.require_pin" class="mt-4">
								<label class="bs-label">{{ __("رمز الدخول") }}</label>
								<input
									ref="pinInput"
									v-model="pin"
									type="password"
									inputmode="numeric"
									maxlength="8"
									autocomplete="off"
									class="bs-input text-center !text-xl tracking-[0.5em]"
									dir="ltr"
									@keydown.enter.prevent="doPunch"
								/>
							</div>
							<button
								type="button"
								class="bs-btn mt-4 w-full !py-4 !text-lg"
								:class="selected.state === 'in' ? 'bs-btn-primary' : 'bs-btn-success'"
								:disabled="punching"
								@click="doPunch"
							>
								{{ punching ? __("جاري التسجيل...") : selected.state === "in" ? __("تسجيل خروج") : __("تسجيل دخول") }}
							</button>
						</template>
					</template>
				</section>

				<section class="bs-card p-4">
					<p class="bs-card-title mb-2">{{ __("سجل اليوم") }}</p>
					<div v-if="!board.logs.length" class="py-4 text-center text-xs text-slate-400">{{ __("لا توجد حركات بعد") }}</div>
					<ul v-else class="divide-y divide-slate-100 text-sm">
						<li v-for="(log, i) in board.logs" :key="i" class="flex items-center justify-between gap-2 py-1.5">
							<span class="truncate">{{ log.employee_name }}</span>
							<span class="flex items-center gap-2">
								<span class="bs-badge" :class="log.log_type === 'IN' ? 'bs-badge-green' : 'bs-badge-blue'">
									{{ log.log_type === "IN" ? __("دخول") : __("خروج") }}
								</span>
								<span class="tabular-nums text-slate-500" dir="ltr">{{ String(log.log_time).slice(11, 16) }}</span>
							</span>
						</li>
					</ul>
				</section>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue"
import { call } from "@/utils/apiWrapper"
import { API, formatHours, formatLongDate } from "@/utils/employees"

const props = defineProps({
	company: { type: String, default: "" },
})
const emit = defineEmits(["punched"])

const STATE = {
	out_none: { dot: "bg-slate-300" },
	in: { dot: "bg-emerald-500" },
	done: { dot: "bg-blue-500" },
	leave: { dot: "bg-sky-400" },
}

const root = ref(null)
const searchInput = ref(null)
const pinInput = ref(null)
const board = ref({ rows: [], logs: [], date: "", require_pin: 0, server_time: "" })
const loading = ref(false)
const search = ref("")
const selectedId = ref("")
const pin = ref("")
const punching = ref(false)
const result = ref(null)
const fullscreen = ref(false)
const offsetMs = ref(0) // server − browser, so the clock shows server time
const nowMs = ref(Date.now())

let tickTimer = null
let refreshTimer = null
let resultTimer = null
let errorTimer = null
const errorMsg = ref("")

function setError(message) {
	errorMsg.value = message
	clearTimeout(errorTimer)
	errorTimer = setTimeout(() => { errorMsg.value = "" }, 6000)
}

const selected = computed(() => board.value.rows.find((r) => r.employee === selectedId.value) || null)
const countIn = computed(() => board.value.rows.filter((r) => r.state === "in").length)
const countNone = computed(() => board.value.rows.filter((r) => r.state === "out_none" && r.is_work_day).length)

const filtered = computed(() => {
	const q = search.value.trim().toLowerCase()
	if (!q) return board.value.rows
	return board.value.rows.filter((r) =>
		(r.employee_name || "").toLowerCase().includes(q) || (r.employee || "").toLowerCase().includes(q)
	)
})

const clock = computed(() => {
	const d = new Date(nowMs.value + offsetMs.value)
	return [d.getHours(), d.getMinutes(), d.getSeconds()].map((n) => String(n).padStart(2, "0")).join(":")
})

function stateText(row) {
	if (row.state === "leave") return __("في إجازة")
	if (row.state === "in") return __("داخل منذ {0}", [row.check_in])
	if (row.state === "done") return __("{0} → {1}", [row.check_in, row.check_out])
	if (!row.is_work_day) return __("يوم راحة")
	return __("لم يسجل — الدوام {0}", [row.shift_start || "—"])
}

function parseServerTime(value) {
	// "YYYY-MM-DD HH:MM:SS[.ffffff]" in the site's timezone → treat as local wall-clock time
	const [d, t] = String(value).split(" ")
	const [y, m, day] = d.split("-").map(Number)
	const [hh, mm, ss] = (t || "0:0:0").split(":")
	return new Date(y, m - 1, day, Number(hh), Number(mm), Math.floor(Number(ss))).getTime()
}

async function load() {
	if (!props.company) return
	loading.value = true
	try {
		const res = await call(`${API}.punch.get_board`, { company: props.company })
		board.value = res
		offsetMs.value = parseServerTime(res.server_time) - Date.now()
	} catch (e) {
		setError(e?.message || __("فشل تحميل الموظفين"))
	} finally {
		loading.value = false
	}
}

async function select(row) {
	selectedId.value = row.employee
	pin.value = ""
	await nextTick()
	pinInput.value?.focus()
}

async function doPunch() {
	if (!selected.value || punching.value) return
	if (board.value.require_pin && !pin.value) return setError(__("أدخل رمز الدخول"))
	punching.value = true
	errorMsg.value = ""
	try {
		result.value = await call(`${API}.punch.punch`, { employee: selected.value.employee, pin: pin.value || null })
		emit("punched")
		clearTimeout(resultTimer)
		resultTimer = setTimeout(() => { result.value = null }, 5000)
		// Ready for the next person
		selectedId.value = ""
		search.value = ""
		pin.value = ""
		await load()
		searchInput.value?.focus()
	} catch (e) {
		setError(e?.message || __("فشل التسجيل"))
		pin.value = ""
	} finally {
		punching.value = false
	}
}

async function toggleFullscreen() {
	try {
		if (!document.fullscreenElement) await root.value.requestFullscreen()
		else await document.exitFullscreen()
	} catch {
		setError(__("المتصفح لا يدعم ملء الشاشة"))
	}
}

function onFullscreenChange() {
	fullscreen.value = document.fullscreenElement === root.value
}

watch(() => props.company, load)

onMounted(() => {
	load()
	tickTimer = setInterval(() => { nowMs.value = Date.now() }, 1000)
	refreshTimer = setInterval(load, 60000)
	document.addEventListener("fullscreenchange", onFullscreenChange)
	searchInput.value?.focus()
})

onBeforeUnmount(() => {
	clearInterval(tickTimer)
	clearInterval(refreshTimer)
	clearTimeout(resultTimer)
	clearTimeout(errorTimer)
	document.removeEventListener("fullscreenchange", onFullscreenChange)
})
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
	transition: opacity 0.25s;
}
.fade-enter-from,
.fade-leave-to {
	opacity: 0;
}
</style>
