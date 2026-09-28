import { call as frappeCall } from "frappe-ui"

import { forceRefreshCSRFToken, isCSRFApiError } from "./csrf"

// Wrapped call function with CSRF auto-refresh
export async function call(method, params, options) {
	try {
		return await frappeCall(method, params, options)
	} catch (error) {
		if (isCSRFApiError(error)) {
			console.warn(
				"CSRF token error in call(), refreshing token and retrying...",
			)
			const refreshed = await forceRefreshCSRFToken()

			if (refreshed) {
				console.log("Retrying call after CSRF refresh...")
				return await frappeCall(method, params, options)
			}

			console.warn(
				"Could not refresh CSRF token. Server may have ignore_csrf enabled.",
			)
		}

		throw error
	}
}
