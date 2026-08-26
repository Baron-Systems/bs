<template>
	<div dir="rtl" class="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900 py-12 px-4 sm:px-6 lg:px-8 relative overflow-hidden">
		<!-- Decorative background blobs -->
		<div class="absolute top-0 -left-20 w-96 h-96 bg-blue-500/20 rounded-full blur-3xl"></div>
		<div class="absolute bottom-0 -right-20 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl"></div>
		<div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-indigo-500/10 rounded-full blur-3xl"></div>

		<div class="max-w-md w-full space-y-8 relative z-10">
			<!-- Logo & Title -->
			<div class="text-center">
				<div class="mx-auto w-16 h-16 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl flex items-center justify-center shadow-2xl shadow-blue-500/40 mb-4">
					<svg class="w-9 h-9 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M13 10V3L4 14h7v7l9-11h-7z" />
					</svg>
				</div>
				<h2 class="text-3xl font-extrabold text-white tracking-tight">
					{{ __("تسجيل الدخول") }}
				</h2>
				<p class="mt-2 text-sm text-blue-200">
					{{ __("الدخول إلى خدمات Baron") }}
				</p>
			</div>

			<!-- Login Card -->
			<div class="bg-white/95 backdrop-blur-xl py-8 px-6 sm:px-8 shadow-2xl rounded-2xl border border-white/20">
				<form class="space-y-5" @submit.prevent="submit">
					<!-- Error -->
					<div v-if="session.login.error" class="rounded-xl bg-red-50 border border-red-200 p-4">
						<div class="flex">
							<div class="flex-shrink-0">
								<svg class="h-5 w-5 text-red-500" viewBox="0 0 20 20" fill="currentColor">
									<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
								</svg>
							</div>
							<div class="ms-3">
								<h3 class="text-sm font-semibold text-red-800">
									{{ __("فشل تسجيل الدخول") }}
								</h3>
								<div class="mt-1 text-sm text-red-700">
									<p>{{ errorMessage }}</p>
								</div>
							</div>
						</div>
					</div>

					<!-- Email -->
					<div>
						<label class="block mb-1.5">
							<span class="block text-sm font-medium text-slate-700">{{ __("المستخدم / البريد") }}</span>
						</label>
						<div class="relative">
							<div class="absolute inset-y-0 start-0 flex items-center ps-3 pointer-events-none">
								<svg class="w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
								</svg>
							</div>
							<input
								v-model="loginForm.email"
								required
								name="email"
								type="text"
								:placeholder="__('اسم المستخدم أو البريد الإلكتروني')"
								:disabled="session.login.loading"
								class="block w-full border border-slate-300 rounded-xl ps-10 pe-3 py-2.5 text-sm text-slate-900 placeholder-slate-400 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all disabled:bg-slate-100"
							/>
						</div>
					</div>

					<!-- Password -->
					<div>
						<label class="block">
							<span class="mb-1.5 block text-sm font-medium text-slate-700">{{ __("كلمة المرور") }}</span>
							<div class="relative">
								<div class="absolute inset-y-0 start-0 flex items-center ps-3 pointer-events-none">
									<svg class="w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
									</svg>
								</div>
								<input
									v-model="loginForm.password"
									required
									name="password"
									:type="showPassword ? 'text' : 'password'"
									:placeholder="__('أدخل كلمة المرور')"
									:disabled="session.login.loading"
									class="block w-full border border-slate-300 rounded-xl ps-10 pe-10 py-2.5 text-sm text-slate-900 placeholder-slate-400 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all disabled:bg-slate-100"
								/>
								<button
									type="button"
									@click="showPassword = !showPassword"
									class="absolute inset-y-0 end-0 flex items-center pe-3 text-slate-500 hover:text-slate-700 transition-colors focus:outline-none"
									:disabled="session.login.loading"
									tabindex="-1"
									:aria-label="showPassword ? __('إخفاء كلمة المرور') : __('إظهار كلمة المرور')"
								>
									<FeatherIcon
										:name="showPassword ? 'eye-off' : 'eye'"
										class="h-5 w-5"
										:stroke-width="2"
									/>
								</button>
							</div>
						</label>
					</div>

					<!-- Submit -->
					<div>
						<button
							:disabled="session.login.loading"
							type="submit"
							class="w-full flex justify-center items-center gap-2 py-3 px-4 border border-transparent rounded-xl shadow-lg shadow-blue-500/30 text-sm font-semibold text-white bg-gradient-to-l from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-60 disabled:cursor-not-allowed disabled:hover:scale-100"
						>
							<svg v-if="session.login.loading" class="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
								<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
								<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
							</svg>
							{{ session.login.loading ? __("جاري الدخول...") : __("دخول") }}
						</button>
					</div>
				</form>
			</div>

			<!-- Footer -->
			<div class="text-center text-xs text-blue-200/70">
				{{ __("AL Baron Systems") }} &copy; {{ new Date().getFullYear() }}
			</div>
		</div>
	</div>
</template>

<script setup>
import { FeatherIcon } from "frappe-ui"
import { computed, onMounted, reactive, ref, watch } from "vue"
import { session } from "@/data/session"

const loginForm = reactive({
	email: "",
	password: "",
})

const showPassword = ref(false)

const errorMessage = computed(() => {
	const err = session.login.error
	if (!err) return ""
	if (Array.isArray(err.messages) && err.messages.length) {
		return err.messages.join("\n")
	}
	return err.message || __("بيانات الدخول غير صحيحة")
})

onMounted(() => {
	loginForm.email = ""
	loginForm.password = ""
	showPassword.value = false
	if (session.login.error) {
		session.login.reset()
	}
})

function submit() {
	if (!loginForm.email || !loginForm.password) {
		return
	}
	session.login.submit({
		email: loginForm.email.trim(),
		password: loginForm.password,
	})
}

watch([() => loginForm.email, () => loginForm.password], () => {
	if (session.login.error) {
		session.login.reset()
	}
})
</script>
