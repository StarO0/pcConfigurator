"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Build } from "@/data/builds";
import { api, ApiError, type ApiUser } from "@/lib/api";

export type AuthUser = {
  id: string;
  email: string;
  displayName: string;
  createdAt: string;
  role: "user" | "admin";
};

type SavedBuild = {
  id: string;
  savedAt: string;
  build: Build;
  name: string;
};

type Result = { success: boolean; error?: string };

type AuthState = {
  user: AuthUser | null;
  accessToken: string | null;
  refreshToken: string | null;
  tokenExpiresAt: string | null;
  isLoggedIn: boolean;
  savedBuilds: SavedBuild[];
  authModalOpen: boolean;
  authModalTab: "login" | "register";
  savedBuildsOpen: boolean;
  login: (email: string, password: string) => Promise<Result>;
  register: (email: string, displayName: string, password: string) => Promise<Result>;
  ensureAccessToken: () => Promise<string | null>;
  logout: () => Promise<void>;
  saveBuild: (build: Build, name: string) => Promise<Result>;
  refreshSavedBuilds: () => Promise<void>;
  removeSavedBuild: (id: string) => Promise<Result>;
  openAuthModal: (tab?: "login" | "register") => void;
  closeAuthModal: () => void;
  openSavedBuilds: () => void;
  closeSavedBuilds: () => void;
};

function userFromApi(user: ApiUser): AuthUser {
  return {
    id: user.id,
    email: user.email,
    displayName: user.display_name,
    createdAt: user.created_at,
    role: user.role,
  };
}

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  if (error instanceof TypeError) return "Backend недоступен. Проверьте, что API запущен на порту 8000.";
  return error instanceof Error ? error.message : "Неизвестная ошибка";
}

async function authenticate(
  action: () => Promise<{ access_token: string; refresh_token: string; expires_at: string }>,
  set: (value: Partial<AuthState>) => void,
): Promise<Result> {
  try {
    const tokens = await action();
    const user = await api.me(tokens.access_token);
    set({
      user: userFromApi(user),
      accessToken: tokens.access_token,
      refreshToken: tokens.refresh_token,
      tokenExpiresAt: tokens.expires_at,
      isLoggedIn: true,
      authModalOpen: false,
    });
    return { success: true };
  } catch (error) {
    return { success: false, error: errorMessage(error) };
  }
}

let refreshInFlight: Promise<string | null> | null = null;

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      tokenExpiresAt: null,
      isLoggedIn: false,
      savedBuilds: [],
      authModalOpen: false,
      authModalTab: "login",
      savedBuildsOpen: false,

      login: (email, password) => authenticate(() => api.login(email, password), set),
      register: (email, displayName, password) =>
        authenticate(() => api.register(email, displayName, password), set),

      ensureAccessToken: async () => {
        const { accessToken, refreshToken, tokenExpiresAt } = get();
        const expiresAt = tokenExpiresAt ? Date.parse(tokenExpiresAt) : 0;
        if (accessToken && Number.isFinite(expiresAt) && expiresAt > Date.now() + 30_000) {
          return accessToken;
        }
        if (!refreshToken) {
          set({ user: null, accessToken: null, tokenExpiresAt: null, isLoggedIn: false });
          return null;
        }
        if (!refreshInFlight) {
          refreshInFlight = (async () => {
            try {
              const tokens = await api.refresh(refreshToken);
              const user = await api.me(tokens.access_token);
              set({
                user: userFromApi(user),
                accessToken: tokens.access_token,
                refreshToken: tokens.refresh_token,
                tokenExpiresAt: tokens.expires_at,
                isLoggedIn: true,
              });
              return tokens.access_token;
            } catch {
              set({
                user: null,
                accessToken: null,
                refreshToken: null,
                tokenExpiresAt: null,
                isLoggedIn: false,
                savedBuilds: [],
              });
              return null;
            } finally {
              refreshInFlight = null;
            }
          })();
        }
        return refreshInFlight;
      },

      logout: async () => {
        const accessToken = get().refreshToken ? await get().ensureAccessToken() : null;
        const refreshToken = get().refreshToken;
        if (accessToken && refreshToken) {
          await api.logout(accessToken, refreshToken).catch(() => undefined);
        }
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          tokenExpiresAt: null,
          isLoggedIn: false,
          savedBuilds: [],
        });
      },

      saveBuild: async (build, name) => {
        const token = await get().ensureAccessToken();
        if (!token) return { success: false, error: "Сначала войдите в аккаунт" };
        try {
          const saved = build.backendId ? await api.saveBuild(build, token) : build;
          set((state) => ({
            savedBuilds: [
              {
                id: saved.backendId ?? saved.id,
                savedAt: new Date().toISOString(),
                build: saved,
                name,
              },
              ...state.savedBuilds.filter((item) => item.id !== (saved.backendId ?? saved.id)),
            ],
          }));
          return { success: true };
        } catch (error) {
          return { success: false, error: errorMessage(error) };
        }
      },

      refreshSavedBuilds: async () => {
        const token = await get().ensureAccessToken();
        if (!token) return;
        try {
          const builds = await api.savedBuilds(token);
          set({
            savedBuilds: builds.map((build) => ({
              id: build.backendId ?? build.id,
              savedAt: new Date().toISOString(),
              build,
              name: build.badge.label.ru ?? build.badge.label.en,
            })),
          });
        } catch {
          // Cached saved builds remain available when the backend is temporarily offline.
        }
      },

      removeSavedBuild: async (id) => {
        const saved = get().savedBuilds.find((item) => item.id === id);
        if (!saved) return { success: true };
        if (saved.build.backendId) {
          const token = await get().ensureAccessToken();
          if (!token) return { success: false, error: "Сначала войдите в аккаунт" };
          try {
            await api.deleteBuild(saved.build.backendId, token);
          } catch (error) {
            return { success: false, error: errorMessage(error) };
          }
        }
        set((state) => ({ savedBuilds: state.savedBuilds.filter((build) => build.id !== id) }));
        return { success: true };
      },
      openAuthModal: (tab = "login") => set({ authModalOpen: true, authModalTab: tab }),
      closeAuthModal: () => set({ authModalOpen: false }),
      openSavedBuilds: () => {
        set({ savedBuildsOpen: true });
        void get().refreshSavedBuilds();
      },
      closeSavedBuilds: () => set({ savedBuildsOpen: false }),
    }),
    {
      name: "ai-pc-auth-v3",
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        tokenExpiresAt: state.tokenExpiresAt,
        isLoggedIn: state.isLoggedIn,
        savedBuilds: state.savedBuilds,
      }),
    },
  ),
);
