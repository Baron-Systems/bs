import { ref, computed, watch, nextTick } from "vue"
import { useRoute, useRouter } from "vue-router"
import { call } from "@/utils/apiWrapper"

// ── Shared reactive state ──────────────────────────────────────────
const company = ref("")
const period = ref("last_30_days")
const customFrom = ref("")
const customTo = ref("")
const currency = ref("")
const companies = ref([])
const loadingCompanies = ref(false)

// Tab data cache — keyed by tab name, invalidated on context change
const tabData = ref({})
const tabLoading = ref({})
const tabError = ref({})

// Context fingerprint — used to detect stale data
const _contextKey = computed(() => `${company.value}|${period.value}|${customFrom.value}|${customTo.value}`)

// Suppress route sync during programmatic updates
let _suppressRouteSync = false

export function useDecisionCenter() {
	const route = useRoute()
	const router = useRouter()

	// ── Init from route query ──
	function initFromQuery() {
		_suppressRouteSync = true
		if (route.query.company) company.value = route.query.company
		if (route.query.period) period.value = route.query.period
		if (route.query.from_date) customFrom.value = route.query.from_date
		if (route.query.to_date) customTo.value = route.query.to_date
		nextTick(() => { _suppressRouteSync = false })
	}

	// ── Sync state → URL ──
	function syncToUrl() {
		if (_suppressRouteSync) return
		const q = {}
		if (company.value) q.company = company.value
		if (period.value && period.value !== "last_30_days") q.period = period.value
		if (period.value === "custom" && customFrom.value) q.from_date = customFrom.value
		if (period.value === "custom" && customTo.value) q.to_date = customTo.value

		// Equality guard — avoid unnecessary replace
		const cur = route.query
		const same = Object.keys(q).length === Object.keys(cur).length &&
			Object.keys(q).every((k) => String(q[k]) === String(cur[k] || ""))
		if (same) return

		_suppressRouteSync = true
		router.replace({ query: q }).finally(() => {
			nextTick(() => { _suppressRouteSync = false })
		})
	}

	// ── Watch route query → state (Back/Forward) ──
	watch(
		() => route.query,
		(q) => {
			if (_suppressRouteSync) return
			_suppressRouteSync = true
			if (q.company && q.company !== company.value) company.value = q.company
			if (q.period && q.period !== period.value) period.value = q.period
			else if (!q.period && period.value !== "last_30_days") period.value = "last_30_days"
			if (q.from_date !== customFrom.value) customFrom.value = q.from_date || ""
			if (q.to_date !== customTo.value) customTo.value = q.to_date || ""
			nextTick(() => { _suppressRouteSync = false })
		},
		{ deep: true }
	)

	// ── Watch context changes → invalidate cache + sync URL ──
	watch(_contextKey, () => {
		tabData.value = {}
		tabError.value = {}
		syncToUrl()
	})

	// ── Build API params ──
	function apiParams(extra = {}) {
		const p = { company: company.value, period: period.value }
		if (period.value === "custom") {
			if (customFrom.value) p.from_date = customFrom.value
			if (customTo.value) p.to_date = customTo.value
		}
		return { ...p, ...extra }
	}

	// ── Build query params for RouterLink ──
	function queryParams() {
		const q = {}
		if (company.value) q.company = company.value
		if (period.value && period.value !== "last_30_days") q.period = period.value
		if (period.value === "custom" && customFrom.value) q.from_date = customFrom.value
		if (period.value === "custom" && customTo.value) q.to_date = customTo.value
		return q
	}

	// ── Load tab data (lazy, cached) ──
	async function loadTab(tabName, apiMethod, extraParams = {}) {
		// Already loaded for this context?
		if (tabData.value[tabName] && !tabError.value[tabName]) return
		tabLoading.value = { ...tabLoading.value, [tabName]: true }
		tabError.value = { ...tabError.value, [tabName]: "" }
		try {
			const result = await call(apiMethod, apiParams(extraParams))
			if (result?.currency) currency.value = result.currency
			tabData.value = { ...tabData.value, [tabName]: result }
		} catch (e) {
			tabError.value = { ...tabError.value, [tabName]: e?.message || __("فشل تحميل البيانات") }
		} finally {
			tabLoading.value = { ...tabLoading.value, [tabName]: false }
		}
	}

	// ── Force reload current tab ──
	async function reloadTab(tabName, apiMethod, extraParams = {}) {
		tabData.value = { ...tabData.value, [tabName]: null }
		await loadTab(tabName, apiMethod, extraParams)
	}

	// ── Load companies ──
	async function loadCompanies() {
		if (companies.value.length) return
		loadingCompanies.value = true
		try {
			companies.value = await call("bs.baron_servies.api.utilities.get_companies") || []
			if (companies.value.length && !company.value) {
				company.value = companies.value[0].name
			}
		} catch (e) {
			// silent
		} finally {
			loadingCompanies.value = false
		}
	}

	// ── Format helpers ──
	function formatCurrency(value) {
		const n = Number(value || 0)
		const cur = currency.value
		if (cur) {
			try {
				return new Intl.NumberFormat("en-US", {
					style: "currency",
					currency: cur,
					minimumFractionDigits: 0,
					maximumFractionDigits: 2,
				}).format(n)
			} catch (e) {
				// fallback if currency code invalid
			}
		}
		return n.toLocaleString("en-US", { minimumFractionDigits: 0, maximumFractionDigits: 2 })
	}

	function formatPct(value) {
		if (value === null || value === undefined || value === "") return "\u2014"
		const n = Number(value)
		if (isNaN(n)) return "\u2014"
		const sign = n > 0 ? "+" : ""
		return `${sign}${n.toFixed(1)}%`
	}

	function formatNumber(value) {
		const n = Number(value || 0)
		return n.toLocaleString("en-US", { maximumFractionDigits: 2 })
	}

	return {
		company,
		period,
		customFrom,
		customTo,
		currency,
		companies,
		loadingCompanies,
		tabData,
		tabLoading,
		tabError,
		initFromQuery,
		syncToUrl,
		apiParams,
		queryParams,
		loadTab,
		reloadTab,
		loadCompanies,
		formatCurrency,
		formatPct,
		formatNumber,
	}
}
