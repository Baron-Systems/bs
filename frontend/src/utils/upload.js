import { ensureCSRFToken } from "@/utils/csrf"

// Upload a file through Frappe's upload_file endpoint; resolves to the stored file_url.
export async function uploadFile(file, { isPrivate = false, folder = "Home/Attachments" } = {}) {
	await ensureCSRFToken()
	const form = new FormData()
	form.append("file", file, file.name)
	form.append("is_private", isPrivate ? "1" : "0")
	form.append("folder", folder)
	const res = await fetch("/api/method/upload_file", {
		method: "POST",
		body: form,
		headers: { "X-Frappe-CSRF-Token": window.csrf_token || "" },
		credentials: "same-origin",
	})
	const data = await res.json().catch(() => ({}))
	if (!res.ok || !data.message?.file_url) {
		throw new Error(data._error_message || data.exception || __("فشل رفع الملف"))
	}
	return data.message.file_url
}
