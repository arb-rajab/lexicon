"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";

// lexicon has no login flow — the backend trusts whatever X-User-Id a caller
// sends it (backend/src/lexicon/api/auth.py: a real deployment terminates
// that header at a trusted reverse-proxy before traffic reaches the app).
// This demo frontend plays that role's client side: the visitor picks an
// identity string, it's kept in localStorage, and every API call sends it
// as X-User-Id. Corpus ownership (and therefore what you can see) is scoped
// to this value.
const STORAGE_KEY = "lexicon:user-id";
const DEFAULT_USER_ID = "demo-user";

interface IdentityContextValue {
  userId: string;
  setUserId: (id: string) => void;
}

const IdentityContext = createContext<IdentityContextValue | null>(null);

export function IdentityProvider({ children }: { children: React.ReactNode }) {
  const [userId, setUserIdState] = useState(DEFAULT_USER_ID);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    try {
      const stored = window.localStorage.getItem(STORAGE_KEY);
      if (stored && stored.trim()) setUserIdState(stored);
    } catch {
      // localStorage unavailable (private browsing, etc.) — fall back to default.
    }
    setHydrated(true);
  }, []);

  const setUserId = (id: string) => {
    const trimmed = id.trim();
    if (!trimmed) return;
    setUserIdState(trimmed);
    try {
      window.localStorage.setItem(STORAGE_KEY, trimmed);
    } catch {
      // Best effort only — an in-memory identity for this tab still works.
    }
  };

  const value = useMemo(() => ({ userId, setUserId }), [userId]);

  // Avoid a hydration flash where the server-rendered default briefly shows
  // before localStorage's real value is read.
  if (!hydrated) return null;

  return <IdentityContext.Provider value={value}>{children}</IdentityContext.Provider>;
}

export function useIdentity(): IdentityContextValue {
  const ctx = useContext(IdentityContext);
  if (!ctx) throw new Error("useIdentity must be used within an IdentityProvider");
  return ctx;
}
