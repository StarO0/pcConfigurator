"use client";
import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Build } from "@/data/builds";

export type AuthUser = {
  id: string;
  email: string;
  displayName: string;
  createdAt: string;
};

type StoredUser = {
  id: string;
  email: string;
  displayName: string;
  password: string;
  createdAt: string;
};

type SavedBuild = {
  id: string;
  savedAt: string;
  build: Build;
  name: string;
};

import api from "@/lib/api";

type AuthState = {
  user: AuthUser | null;
  isLoggedIn: boolean;
  savedBuilds: SavedBuild[];
  authModalOpen: boolean;
  authModalTab: "login" | "register";
  savedBuildsOpen: boolean;
  isFetching: boolean;
  // Actions
  login: (email: string, password: string) => Promise<{ success: boolean; error?: string }>;
  register: (
    email: string,
    displayName: string,
    password: string
  ) => Promise<{ success: boolean; error?: string }>;
  logout: () => void;
  fetchMe: () => Promise<void>;
  saveBuild: (build: Build, name: string) => void;
  removeSavedBuild: (id: string) => void;
  openAuthModal: (tab?: "login" | "register") => void;
  closeAuthModal: () => void;
  openSavedBuilds: () => void;
  closeSavedBuilds: () => void;
};

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      isLoggedIn: false,
      savedBuilds: [],
      authModalOpen: false,
      authModalTab: "login",
      savedBuildsOpen: false,

      isFetching: false,

      fetchMe: async () => {
        const token = localStorage.getItem("access_token");
        if (!token) return;
        set({ isFetching: true });
        try {
          const res = await api.get("/auth/me");
          const userData = res.data;
          set({
            user: {
              id: userData.id,
              email: userData.email,
              displayName: userData.display_name,
              createdAt: userData.created_at,
            },
            isLoggedIn: true,
          });
        } catch (e) {
          // Token might be expired or invalid
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
          set({ user: null, isLoggedIn: false });
        } finally {
          set({ isFetching: false });
        }
      },

      login: async (email, password) => {
        try {
          const res = await api.post("/auth/login", { email, password });
          const data = res.data;
          localStorage.setItem("access_token", data.access_token);
          localStorage.setItem("refresh_token", data.refresh_token);
          
          // Get user details
          await get().fetchMe();
          set({ authModalOpen: false });
          return { success: true };
        } catch (error: any) {
          return { 
            success: false, 
            error: error.response?.data?.detail || "Invalid email or password." 
          };
        }
      },

      register: async (email, displayName, password) => {
        try {
          const res = await api.post("/auth/register", { 
            email, 
            display_name: displayName, 
            password 
          });
          const data = res.data;
          localStorage.setItem("access_token", data.access_token);
          localStorage.setItem("refresh_token", data.refresh_token);
          
          await get().fetchMe();
          set({ authModalOpen: false });
          return { success: true };
        } catch (error: any) {
          return { 
            success: false, 
            error: error.response?.data?.detail || "An error occurred during registration." 
          };
        }
      },

      logout: async () => {
        try {
          // Optional: invalidate token on server
          await api.post("/auth/logout", { all_sessions: false });
        } catch (e) {
          // Ignore
        }
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        set({ user: null, isLoggedIn: false });
      },

      saveBuild: (build, name) =>
        set((state) => ({
          savedBuilds: [
            ...state.savedBuilds,
            {
              id: crypto.randomUUID(),
              savedAt: new Date().toISOString(),
              build,
              name,
            },
          ],
        })),

      removeSavedBuild: (id) =>
        set((state) => ({
          savedBuilds: state.savedBuilds.filter((b) => b.id !== id),
        })),

      openAuthModal: (tab = "login") => set({ authModalOpen: true, authModalTab: tab }),
      closeAuthModal: () => set({ authModalOpen: false }),

      openSavedBuilds: () => set({ savedBuildsOpen: true }),
      closeSavedBuilds: () => set({ savedBuildsOpen: false }),
    }),
    {
      name: "ai-pc-auth",
      partialize: (state) => ({
        user: state.user,
        isLoggedIn: state.isLoggedIn,
        savedBuilds: state.savedBuilds,
      }),
    }
  )
);
