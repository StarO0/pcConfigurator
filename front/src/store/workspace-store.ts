"use client";

import { create } from "zustand";

export type WorkspaceSection = "builder" | "catalog" | "compare" | "account" | "data";

type WorkspaceState = {
  section: WorkspaceSection;
  setSection: (section: WorkspaceSection) => void;
};

export const useWorkspaceStore = create<WorkspaceState>((set) => ({
  section: "builder",
  setSection: (section) => set({ section }),
}));
