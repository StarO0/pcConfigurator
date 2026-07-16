"use client";

import { useCallback, useEffect, useState } from "react";
import { Bell, BellRing, Check, Heart, Trash2 } from "lucide-react";
import { api, type ApiNotification, type ApiPriceAlert, type ApiProduct } from "@/lib/api";
import { useAuthStore } from "@/store/auth-store";

export default function AccountCenter() {
  const { isLoggedIn, openAuthModal, ensureAccessToken } = useAuthStore();
  const [favorites, setFavorites] = useState<ApiProduct[]>([]);
  const [alerts, setAlerts] = useState<ApiPriceAlert[]>([]);
  const [notifications, setNotifications] = useState<ApiNotification[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (!isLoggedIn) { setLoading(false); return; }
    setLoading(true);
    setError("");
    const token = await ensureAccessToken();
    if (!token) { setLoading(false); return; }
    try {
      const [favoriteData, alertData, notificationData] = await Promise.all([
        api.favoriteProducts(token), api.priceAlerts(token), api.notifications(token),
      ]);
      setFavorites(favoriteData.items);
      setAlerts(alertData);
      setNotifications(notificationData.items);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Не удалось загрузить данные");
    } finally { setLoading(false); }
  }, [ensureAccessToken, isLoggedIn]);

  useEffect(() => {
    const timeout = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timeout);
  }, [load]);

  if (!isLoggedIn) return <main className="mx-auto flex w-full max-w-4xl flex-1 flex-col items-center justify-center px-4 py-20 text-center"><BellRing className="mb-5 h-12 w-12 text-cyan-400" /><h2 className="text-3xl font-bold">Избранное, алерты и уведомления</h2><p className="mt-3 max-w-xl text-zinc-500">Войдите, чтобы хранить товары и получать локальные уведомления об изменении импортированной цены.</p><button onClick={() => openAuthModal("login")} className="mt-6 rounded-xl bg-cyan-500 px-6 py-3 font-bold text-slate-950">Войти</button></main>;

  async function removeFavorite(productId: string) {
    const token = await ensureAccessToken();
    if (!token) return;
    await api.setFavorite(productId, false, token);
    setFavorites((items) => items.filter((item) => item.id !== productId));
  }

  async function removeAlert(alertId: string) {
    const token = await ensureAccessToken();
    if (!token) return;
    await api.deletePriceAlert(alertId, token);
    setAlerts((items) => items.filter((item) => item.id !== alertId));
  }

  async function markRead(notificationId: string) {
    const token = await ensureAccessToken();
    if (!token) return;
    const updated = await api.readNotification(notificationId, token);
    setNotifications((items) => items.map((item) => item.id === notificationId ? updated : item));
  }

  return <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-8 sm:px-6 lg:px-8">
    <div className="mb-8"><p className="text-sm font-semibold uppercase tracking-[0.2em] text-cyan-400">Личный центр</p><h2 className="mt-2 text-3xl font-bold">Контроль товаров и цен</h2></div>
    {loading && <div className="shimmer h-40 rounded-2xl" />}{error && <p className="rounded-xl bg-red-500/10 p-4 text-red-300">{error}</p>}
    {!loading && <div className="grid gap-6 lg:grid-cols-3">
      <section className="glass-card p-5"><div className="mb-4 flex items-center gap-2"><Heart className="h-5 w-5 text-pink-400" /><h3 className="font-bold">Избранное · {favorites.length}</h3></div><div className="space-y-3">{favorites.length ? favorites.map((product) => <div key={product.id} className="rounded-xl bg-white/[0.03] p-3"><div className="flex justify-between gap-3"><div><p className="text-sm font-semibold">{product.name}</p><p className="mt-1 text-xs text-zinc-600">{product.brand} · {product.offers.length ? `${Math.min(...product.offers.map((offer) => Number(offer.effective_price)))} PLN` : "без цены"}</p></div><button onClick={() => void removeFavorite(product.id)} className="text-zinc-600 hover:text-red-400"><Trash2 className="h-4 w-4" /></button></div></div>) : <p className="text-sm text-zinc-600">Добавляйте товары сердцем в каталоге.</p>}</div></section>
      <section className="glass-card p-5"><div className="mb-4 flex items-center gap-2"><Bell className="h-5 w-5 text-amber-400" /><h3 className="font-bold">Ценовые алерты · {alerts.length}</h3></div><div className="space-y-3">{alerts.length ? alerts.map((alert) => { const product = favorites.find((item) => item.id === alert.product_id); return <div key={alert.id} className="rounded-xl bg-white/[0.03] p-3"><div className="flex justify-between gap-3"><div><p className="text-sm font-semibold">{product?.name ?? `Товар ${alert.product_id.slice(0, 8)}`}</p><p className="mt-1 text-xs text-amber-300">Цель: {Number(alert.target_price).toLocaleString()} {alert.currency}</p></div><button onClick={() => void removeAlert(alert.id)} className="text-zinc-600 hover:text-red-400"><Trash2 className="h-4 w-4" /></button></div></div>; }) : <p className="text-sm text-zinc-600">Создайте алерт на карточке товара.</p>}</div></section>
      <section className="glass-card p-5"><div className="mb-4 flex items-center gap-2"><BellRing className="h-5 w-5 text-cyan-400" /><h3 className="font-bold">Уведомления · {notifications.length}</h3></div><div className="space-y-3">{notifications.length ? notifications.map((item) => <button key={item.id} onClick={() => !item.read_at && void markRead(item.id)} className={`w-full rounded-xl p-3 text-left ${item.read_at ? "bg-white/[0.02] opacity-60" : "bg-cyan-500/10"}`}><div className="flex items-start justify-between gap-3"><div><p className="text-sm font-semibold">{item.title}</p><p className="mt-1 text-xs text-zinc-400">{item.body}</p></div>{item.read_at ? <Check className="h-4 w-4 text-emerald-400" /> : <span className="mt-1 h-2 w-2 rounded-full bg-cyan-400" />}</div></button>) : <p className="text-sm text-zinc-600">Пока нет уведомлений. Они появятся после проверки алертов.</p>}</div></section>
    </div>}
  </main>;
}
