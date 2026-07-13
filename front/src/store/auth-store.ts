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

type AuthState = {
  user: AuthUser | null;
  isLoggedIn: boolean;
  savedBuilds: SavedBuild[];
  authModalOpen: boolean;
  authModalTab: "login" | "register";
  savedBuildsOpen: boolean;
  // Actions
  login: (email: string, password: string) => Promise<{ success: boolean; error?: string }>;
  register: (
    email: string,
    displayName: string,
    password: string
  ) => Promise<{ success: boolean; error?: string }>;
  logout: () => void;
  saveBuild: (build: Build, name: string) => void;
  removeSavedBuild: (id: string) => void;
  openAuthModal: (tab?: "login" | "register") => void;
  closeAuthModal: () => void;
  openSavedBuilds: () => void;
  closeSavedBuilds: () => void;
};

const AUTH_USERS_KEY = "auth_users";

function getStoredUsers(): StoredUser[] {
  try {
    const raw = localStorage.getItem(AUTH_USERS_KEY);
    return raw ? (JSON.parse(raw) as StoredUser[]) : [];
  } catch {
    return [];
  }
}

function saveStoredUsers(users: StoredUser[]): void {
  localStorage.setItem(AUTH_USERS_KEY, JSON.stringify(users));
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isLoggedIn: false,
      savedBuilds: [],
      authModalOpen: false,
      authModalTab: "login",
      savedBuildsOpen: false,

      login: async (email, password) => {
        await new Promise((resolve) => setTimeout(resolve, 500));

        const users = getStoredUsers();
        const match = users.find(
          (u) => u.email.toLowerCase() === email.toLowerCase() && u.password === password
        );

        if (!match) {
          return { success: false, error: "Invalid email or password." };
        }

        const authUser: AuthUser = {
          id: match.id,
          email: match.email,
          displayName: match.displayName,
          createdAt: match.createdAt,
        };

        set({ user: authUser, isLoggedIn: true, authModalOpen: false });
        return { success: true };
      },

      register: async (email, displayName, password) => {
        await new Promise((resolve) => setTimeout(resolve, 500));

        const users = getStoredUsers();
        const exists = users.some((u) => u.email.toLowerCase() === email.toLowerCase());

        if (exists) {
          return { success: false, error: "An account with this email already exists." };
        }

        const newUser: StoredUser = {
          id: crypto.randomUUID(),
          email,
          displayName,
          password,
          createdAt: new Date().toISOString(),
        };

        saveStoredUsers([...users, newUser]);

        const authUser: AuthUser = {
          id: newUser.id,
          email: newUser.email,
          displayName: newUser.displayName,
          createdAt: newUser.createdAt,
        };

        set({ user: authUser, isLoggedIn: true, authModalOpen: false });
        return { success: true };
      },

      logout: () => set({ user: null, isLoggedIn: false }),

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
