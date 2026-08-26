const CSRF_COOKIE = "csrf_token"
const CSRF_PLACEHOLDER = "{{ csrf_token }}"
const CSRF_TOKEN_ENDPOINT = "/api/method/bs.baron_servies.api.utilities.get_csrf_token"

let refreshPromise = null
let lastKnownToken = null
let tokenRefreshCallbacks = []

function readCookie(name) {
	const value = `; ${document.cookie}`
	const parts = value.split(`; ${name}=`)
	if (parts.length === 2) {
		return parts.pop().split(";").shift() || null
	}
	return null
}

function normalizeToken(token) {
	if (typeof token !== "string" || token === CSRF_PLACEHOLDER || !token) {
		return null
	}
	return token
}

function setGlobalToken(token, source) {
	if (!token) {
		return null
	}

	window.csrf_token = token

	if (token !== lastKnownToken) {
		const prefix = token.substring(0, 10)
		const context = source === "response" ? "initialized" : "loaded"
		if (import.meta.env.DEV) {
			console.log(`CSRF token ${context}: ${prefix}...`)
		}
		lastKnownToken = token

		tokenRefreshCallbacks.forEach(callback => {
			try {
				callback(token)
			} catch (error) {
				console.error("Error in CSRF token refresh callback:", error)
			}
		})
	}

	return token
}

export function onCSRFTokenRefresh(callback) {
	if (typeof callback === 'function') {
		tokenRefreshCallbacks.push(callback)
	}
}

export function getCSRFTokenFromCookie() {
	const token = normalizeToken(readCookie(CSRF_COOKIE))
	if (token) {
		setGlobalToken(token, "cookie")
	}
	return token
}

async function fetchCSRFToken() {
	const response = await fetch(CSRF_TOKEN_ENDPOINT, {
		method: "GET",
		credentials: "include",
		cache: "no-store",
		headers: {
			Accept: "application/json",
			"X-Frappe-Site-Name": window.location.hostname,
		},
	})

	let data = null
	const contentType = response.headers.get("content-type") || ""
	if (contentType.includes("application/json")) {
		try {
			data = await response.json()
		} catch (error) {
			console.warn("Could not parse CSRF refresh response as JSON")
		}
	}

	return { response, data }
}

function extractTokenFromResponse(data) {
	return normalizeToken(data?.message?.csrf_token)
}

export async function ensureCSRFToken({
	forceRefresh = false,
	silent = false,
} = {}) {
	if (!forceRefresh) {
		if (
			window.csrf_token &&
			typeof window.csrf_token === "string" &&
			window.csrf_token !== CSRF_PLACEHOLDER
		) {
			return true
		}

		const existingToken = getCSRFTokenFromCookie()
		if (existingToken) {
			return true
		}
	}

	if (refreshPromise) {
		return refreshPromise
	}

	refreshPromise = (async () => {
		try {
			if (forceRefresh) {
				window.csrf_token = null
				lastKnownToken = null
			}

			const { response, data } = await fetchCSRFToken()

			if (response.status === 401 || response.status === 403) {
				if (!silent && import.meta.env.DEV) {
					console.log("User not authenticated, skipping CSRF token refresh")
				}
				return false
			}

			if (!response.ok) {
				if (!silent) {
					console.warn("Failed to refresh CSRF token, status:", response.status)
				}
				return false
			}

			const tokenFromCookie = getCSRFTokenFromCookie()
			if (tokenFromCookie) {
				return true
			}

			const tokenFromResponse = extractTokenFromResponse(data)
			if (tokenFromResponse) {
				setGlobalToken(tokenFromResponse, "response")
				return true
			}

			if (!silent) {
				console.warn("CSRF token not found after refresh attempt")
			}
			return false
		} catch (error) {
			if (!silent) {
				console.error("Failed to refresh CSRF token:", error)
			}
			return false
		} finally {
			refreshPromise = null
		}
	})()

	return refreshPromise
}

export async function forceRefreshCSRFToken(options = {}) {
	return ensureCSRFToken({ ...options, forceRefresh: true })
}

export function isCSRFApiError(error) {
	if (!error) {
		return false
	}

	if (error.exc_type === "CSRFTokenError") {
		return true
	}

	if (
		typeof error.message === "string" &&
		error.message.toLowerCase().includes("csrf")
	) {
		return true
	}

	if (Array.isArray(error.messages)) {
		return error.messages.some(
			(message) =>
				typeof message === "string" && message.toLowerCase().includes("csrf"),
		)
	}

	return false
}
