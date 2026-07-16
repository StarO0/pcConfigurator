"use client";

import { useEffect } from "react";
import { useAuthStore } from "@/store/auth-store";

export default function AuthProvider({ children }: { children: React.ReactNode }) {
  const ensureAccessToken = useAuthStore((s) => s.ensureAccessToken);

  useEffect(() => {
    // Attempt to validate/refresh current user profile if we have a token
    void ensureAccessToken();
  }, [ensureAccessToken]);

  return <>{children}</>;
}
