import './index.css'

import { createApp } from 'vue'
import router from './router'
import App from './App.vue'

import { Button, setConfig, frappeRequest, resourcesPlugin } from 'frappe-ui'

// Translation helper — uses Frappe's __ if available, otherwise passthrough.
// Supports printf-style placeholders: __("Hello {0}", ["World"])
function translate(str, replacements) {
	if (typeof window.frappe?.__ === "function") {
		return window.frappe.__(str, replacements)
	}
	if (Array.isArray(replacements)) {
		return str.replace(/\{(\d+)\}/g, (_, i) => (replacements[i] != null ? replacements[i] : ""))
	}
	return str
}

// Expose globally for use in <script> and as window.__
window.__ = translate

let app = createApp(App)

// Make __ available on every component instance (templates compile to ctx.__())
app.config.globalProperties.__ = translate

setConfig('resourceFetcher', frappeRequest)

app.use(router)
app.use(resourcesPlugin)

app.component('Button', Button)
app.mount('#app')
