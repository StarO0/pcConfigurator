"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Mail, Lock, User, Loader2, CheckCircle, Eye, EyeOff } from "lucide-react";
import { useAuthStore } from "@/store/auth-store";

export default function AuthModal() {
  const { authModalOpen, authModalTab, closeAuthModal, login, register, openAuthModal } =
    useAuthStore();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  const activeTab = authModalTab;

  function resetForm() {
    setEmail("");
    setPassword("");
    setDisplayName("");
    setError("");
    setSuccess(false);
    setShowPassword(false);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    try {
      if (activeTab === "login") {
        const result = await login(email, password);
        if (result.success) {
          setSuccess(true);
          setTimeout(() => {
            closeAuthModal();
            resetForm();
          }, 800);
        } else {
          setError(result.error ?? "Ошибка входа");
        }
      } else {
        if (!displayName.trim()) {
          setError("Введите имя пользователя");
          setIsLoading(false);
          return;
        }
        const result = await register(email, displayName, password);
        if (result.success) {
          setSuccess(true);
          setTimeout(() => {
            closeAuthModal();
            resetForm();
          }, 800);
        } else {
          setError(result.error ?? "Ошибка регистрации");
        }
      }
    } finally {
      setIsLoading(false);
    }
  }

  if (!authModalOpen) return null;

  return (
    <AnimatePresence>
      {authModalOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            key="backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => { closeAuthModal(); resetForm(); }}
            className="fixed inset-0 z-[60] bg-black/60 backdrop-blur-md"
          />

          {/* Modal */}
          <motion.div
            key="modal"
            initial={{ opacity: 0, scale: 0.92, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.92, y: 20 }}
            transition={{ type: "spring", stiffness: 350, damping: 30 }}
            className="fixed left-1/2 top-1/2 z-[61] w-full max-w-md -translate-x-1/2 -translate-y-1/2 px-4"
          >
            <div className="relative rounded-2xl border border-white/[0.08] bg-[#0f1520] shadow-2xl shadow-black/50 overflow-hidden">
              {/* Gradient top strip */}
              <div className="absolute top-0 inset-x-0 h-[1px] bg-gradient-to-r from-transparent via-[#06b6d4]/60 to-transparent" />

              {/* Close button */}
              <button
                onClick={() => { closeAuthModal(); resetForm(); }}
                aria-label="Close"
                className="absolute right-4 top-4 p-1.5 rounded-lg text-white/40 hover:text-white hover:bg-white/10 transition-colors z-10"
              >
                <X className="w-4 h-4" />
              </button>

              <div className="p-8">
                {/* Title */}
                <h2 className="text-xl font-bold text-white mb-1">
                  {activeTab === "login" ? "Добро пожаловать" : "Создать аккаунт"}
                </h2>
                <p className="text-sm text-zinc-500 mb-6">
                  {activeTab === "login"
                    ? "Войдите, чтобы сохранять сборки и использовать ИИ"
                    : "Зарегистрируйтесь — это бесплатно"}
                </p>

                {/* Tab switcher */}
                <div className="flex gap-1 rounded-xl border border-white/[0.06] bg-white/[0.02] p-1 mb-6">
                  {(["login", "register"] as const).map((tab) => (
                    <button
                      key={tab}
                      onClick={() => { openAuthModal(tab); setError(""); }}
                      className={`relative flex-1 rounded-lg py-2 text-sm font-medium transition-all ${
                        activeTab === tab ? "text-white" : "text-zinc-500 hover:text-zinc-300"
                      }`}
                    >
                      {activeTab === tab && (
                        <motion.div
                          layoutId="authTab"
                          className="absolute inset-0 rounded-lg bg-gradient-to-r from-[#06b6d4]/20 to-[#0ea5e9]/20 border border-[#06b6d4]/30"
                          transition={{ type: "spring", stiffness: 400, damping: 30 }}
                        />
                      )}
                      <span className="relative z-10">
                        {tab === "login" ? "Войти" : "Регистрация"}
                      </span>
                    </button>
                  ))}
                </div>

                {/* Success state */}
                <AnimatePresence>
                  {success && (
                    <motion.div
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      className="flex flex-col items-center justify-center py-8 gap-3"
                    >
                      <CheckCircle className="w-12 h-12 text-emerald-400" />
                      <p className="text-white font-semibold">
                        {activeTab === "login" ? "Вы вошли!" : "Аккаунт создан!"}
                      </p>
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Form */}
                {!success && (
                  <form onSubmit={handleSubmit} className="space-y-4">
                    {/* Display name (register only) */}
                    <AnimatePresence>
                      {activeTab === "register" && (
                        <motion.div
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: "auto" }}
                          exit={{ opacity: 0, height: 0 }}
                          className="overflow-hidden"
                        >
                          <label className="block text-xs font-medium text-zinc-400 mb-1.5">
                            Имя пользователя
                          </label>
                          <div className="relative">
                            <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
                            <input
                              type="text"
                              value={displayName}
                              onChange={(e) => setDisplayName(e.target.value)}
                              placeholder="Ваше имя"
                              required
                              className="w-full rounded-xl bg-white/[0.04] border border-white/[0.08] pl-10 pr-4 py-3 text-sm text-white placeholder-zinc-600 outline-none focus:border-[#06b6d4]/50 focus:ring-1 focus:ring-[#06b6d4]/30 transition-all"
                            />
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>

                    {/* Email */}
                    <div>
                      <label className="block text-xs font-medium text-zinc-400 mb-1.5">
                        Email
                      </label>
                      <div className="relative">
                        <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
                        <input
                          type="email"
                          value={email}
                          onChange={(e) => setEmail(e.target.value)}
                          placeholder="you@example.com"
                          required
                          className="w-full rounded-xl bg-white/[0.04] border border-white/[0.08] pl-10 pr-4 py-3 text-sm text-white placeholder-zinc-600 outline-none focus:border-[#06b6d4]/50 focus:ring-1 focus:ring-[#06b6d4]/30 transition-all"
                        />
                      </div>
                    </div>

                    {/* Password */}
                    <div>
                      <label className="block text-xs font-medium text-zinc-400 mb-1.5">
                        Пароль
                      </label>
                      <div className="relative">
                        <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
                        <input
                          type={showPassword ? "text" : "password"}
                          value={password}
                          onChange={(e) => setPassword(e.target.value)}
                              placeholder="Минимум 10 символов"
                          required
                              minLength={10}
                          className="w-full rounded-xl bg-white/[0.04] border border-white/[0.08] pl-10 pr-12 py-3 text-sm text-white placeholder-zinc-600 outline-none focus:border-[#06b6d4]/50 focus:ring-1 focus:ring-[#06b6d4]/30 transition-all"
                        />
                        <button
                          type="button"
                          onClick={() => setShowPassword(!showPassword)}
                          className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300 transition-colors"
                        >
                          {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                        </button>
                      </div>
                    </div>

                    {/* Error */}
                    <AnimatePresence>
                      {error && (
                        <motion.p
                          initial={{ opacity: 0, y: -4 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0 }}
                          className="text-sm text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2"
                        >
                          {error}
                        </motion.p>
                      )}
                    </AnimatePresence>

                    {/* Submit */}
                    <motion.button
                      type="submit"
                      disabled={isLoading}
                      whileHover={{ scale: isLoading ? 1 : 1.01 }}
                      whileTap={{ scale: isLoading ? 1 : 0.98 }}
                      className="w-full rounded-xl bg-gradient-to-r from-[#06b6d4] to-[#0ea5e9] py-3 text-sm font-semibold text-white shadow-lg shadow-cyan-500/20 transition-all hover:shadow-cyan-500/30 disabled:opacity-60 flex items-center justify-center gap-2"
                    >
                      {isLoading ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" />
                          {activeTab === "login" ? "Входим..." : "Создаём..."}
                        </>
                      ) : (
                        activeTab === "login" ? "Войти" : "Создать аккаунт"
                      )}
                    </motion.button>
                  </form>
                )}
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
