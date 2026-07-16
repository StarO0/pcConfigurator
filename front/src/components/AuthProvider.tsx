"use client";

import { useEffect } from "react";
import { useAuthStore } from "@/store/auth-store";

export default function AuthProvider({ children }: { children: React.ReactNode }) {
  const fetchMe = useAuthStore((s) => s.fetchMe);

  useEffect(() => {
    // Attempt to fetch current user profile if we have a token
    fetchMe();
  }, [fetchMe]);

  return <>{children}</>;
}
