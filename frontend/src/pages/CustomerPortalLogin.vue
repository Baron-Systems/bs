<template>
	<div class="min-h-screen flex flex-col bg-slate-900" dir="rtl">
		<!-- Header / Brand -->
		<div class="flex-1 flex items-center justify-center p-4 sm:p-6">
			<div class="w-full max-w-md">
				<div class="text-center mb-8">
					<div class="inline-flex items-center justify-center w-20 h-20 bg-white/10 rounded-2xl mb-4 backdrop-blur-sm border border-white/10 shadow-xl">
						<svg class="w-10 h-10 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
						</svg>
					</div>
					<h1 class="text-2xl sm:text-3xl font-bold text-white mb-2">Al Baron Systems</h1>
					<p class="text-blue-200 text-lg">بوابة العملاء الذكية</p>
				</div>

				<!-- Login Card -->
				<div class="bg-slate-800/80 backdrop-blur-md border border-slate-700 rounded-2xl shadow-2xl p-6 sm:p-8">
					<h2 class="text-xl font-bold text-white text-center mb-6">تسجيل الدخول</h2>
					<p class="text-slate-400 text-center text-sm mb-6">أدخل بياناتك للوصول إلى حسابك</p>

					<form @submit.prevent="handleLogin" class="space-y-5">
						<div>
							<label class="block text-sm font-medium text-slate-300 mb-2">الاسم</label>
							<div class="relative">
								<div class="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
									<svg class="w-5 h-5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
									</svg>
								</div>
								<input
									v-model="name"
									type="text"
									placeholder="يكفي إدخال الاسم الأول فقط"
									class="w-full bg-slate-900/60 border border-slate-600 rounded-xl pr-10 pl-4 py-3 text-white placeholder-slate-500 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
									:disabled="loading"
								/>
							</div>
							<p class="text-xs text-slate-500 mt-1.5">يكفي إدخال الاسم الأول فقط</p>
						</div>

						<div>
							<label class="block text-sm font-medium text-slate-300 mb-2">رقم العميل</label>
							<div class="relative">
								<div class="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
									<svg class="w-5 h-5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V8a2 2 0 00-2-2h-5m-4 0V5a2 2 0 114 0v1m-4 0a2 2 0 104 0m-5 8a2 2 0 100-4 2 2 0 000 4zm0 0c1.306 0 2.417.835 2.83 2M9 14a3 3 0 00-3 3m3-3a3 3 0 013 3m-3 0h6" />
									</svg>
								</div>
								<input
									v-model="idNo"
									type="text"
									inputmode="numeric"
									placeholder="أدخل رقم العميل"
									class="w-full bg-slate-900/60 border border-slate-600 rounded-xl pr-10 pl-4 py-3 text-white placeholder-slate-500 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
									:disabled="loading"
								/>
							</div>
							<p class="text-xs text-slate-500 mt-1.5">هذه طريقة الدخول</p>
						</div>

						<Button
							type="submit"
							variant="solid"
							theme="blue"
							:loading="loading"
							class="w-full justify-center py-3 text-base"
						>
							{{ loading ? "جاري التحقق..." : "دخول" }}
						</Button>
					</form>
				</div>

				<p class="text-center text-slate-500 text-sm mt-6">
					© Al Baron Systems
				</p>
			</div>
		</div>
	</div>
</template>

<script setup>
import { Button } from "frappe-ui"
import { call } from "@/utils/apiWrapper"
import { useToast } from "@/composables/useToast"
import router from "@/router"
import { ref } from "vue"

const { showError } = useToast()

const name = ref("")
const idNo = ref("")
const loading = ref(false)

async function handleLogin() {
	if (!name.value.trim() || !idNo.value.trim()) {
		showError("يرجى إدخال الاسم ورقم العميل")
		return
	}
	loading.value = true
	try {
		const result = await call("bs.baron_servies.api.customer_portal.customer_portal_login", {
			name: name.value.trim(),
			id_no: idNo.value.trim(),
		})
		if (result && result.success && result.token) {
			localStorage.setItem("bs_customer_token", result.token)
			if (result.customer) {
				localStorage.setItem("bs_customer_name", result.customer.customer_name || "")
				localStorage.setItem("bs_customer_id", result.customer.name || "")
			}
			router.replace({ name: "CustomerPortal" })
		} else {
			showError(result?.message || "فشل تسجيل الدخول")
		}
	} catch (e) {
		showError(e?.message || "الاسم أو رقم العميل غير صحيح")
	} finally {
		loading.value = false
	}
}
</script>
