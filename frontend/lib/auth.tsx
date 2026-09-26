"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

// ADR-0005 — real sign-in. Before this, lexicon had no login flow at all:
// the backend trusted whatever X-User-Id a caller sent it, and this
// frontend played along by letting the visitor type any identity string
// into a localStorage-backed switcher (see the removed lib/identity.tsx).
// That was a correct reflection of the backend's then-actual (and, it
// turned out, fully spoofable) auth model — not a frontend bug. Now that
// the backend verifies a real, signed session token, this provider talks to
// the real register/login/logout/me endpoints (app/api/auth/*) instead.
// The token itself is never held here, or anywhere in page JavaScript — it
// lives only in an httpOnly cookie those route handlers set and read
// server-side (lib/session-cookie.ts).

export class AuthError extends Error {
  readonly status: number;
  readonly code: string;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.name = "AuthError";
    this.status = status;
    this.code = code;
  }
}

interface AuthUser {
  username: string;
}

interface AuthContextValue {
  user: AuthUser | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

async function parseErrorBody(response: Response): Promise<AuthError> {
  try {
    const body = await response.json();
    return new AuthError(
      response.status,
      body?.error?.code ?? "unknown_error",
      body?.error?.message ?? response.statusText,
    );
  } catch {
    return new AuthError(response.status, "unknown_error", response.statusText);
  }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const res = await fetch("/api/auth/me");
      if (res.ok) {
        const body = await res.json();
        setUser({ username: body.username });
      } else {
        setUser(null);
      }
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const submitCredentials = useCallback(
    async (path: "login" | "register", username: string, password: string) => {
      const res = await fetch(`/api/auth/${path}`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      if (!res.ok) throw await parseErrorBody(res);
      const body = await res.json();
      setUser({ username: body.username });
    },
    [],
  );

  const login = useCallback(
    (username: string, password: string) => submitCredentials("login", username, password),
    [submitCredentials],
  );
  const register = useCallback(
    (username: string, password: string) => submitCredentials("register", username, password),
    [submitCredentials],
  );

  const logout = useCallback(async () => {
    await fetch("/api/auth/logout", { method: "POST" });
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({ user, loading, login, register, logout }),
    [user, loading, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
