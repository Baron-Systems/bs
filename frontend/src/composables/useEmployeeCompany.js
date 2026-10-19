import { ref } from "vue"
import { call } from "@/utils/apiWrapper"

// Company selection shared by every Employees page; remembered per browser.
const STORAGE_KEY = "bs_employees_company"

const companies = ref([])
const company = ref(readStored())
let loadPromise = null

function readStored() {
	try {
		return localStorage.getItem(STORAGE_KEY) || ""
	} catch {
		return ""
	}
}

function setCompany(value) {
	company.value = value || ""
	try {
		localStorage.setItem(STORAGE_KEY, company.value)
	} catch {
		// storage unavailable — selection just won't persist
	}
}

async function loadCompanies() {
	if (!loadPromise) {
		loadPromise = call("bs.baron_servies.api.utilities.get_companies")
			.then((rows) => {
				companies.value = rows || []
				if (!companies.value.some((c) => c.name === company.value)) {
					setCompany(companies.value[0]?.name || "")
				}
			})
			.catch((e) => {
				loadPromise = null
				throw e
			})
	}
	return loadPromise
}

export function useEmployeeCompany() {
	return { companies, company, setCompany, loadCompanies }
}
