"use client";

import { AuthBar } from "@/components/AuthBar";
import { AuthForm } from "@/components/AuthForm";
import { useAuth } from "@/lib/auth";

/** Shows the sign-in/register form until a real session exists, then the
 * app itself with a header carrying the signed-in username — replaces the
 * old always-render-the-app-with-a-spoofable-identity-switcher shape. */
export function AuthGate({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();

  if (loading) return null;
  if (!user) return <AuthForm />;

  return (
    <>
      <header className="site-header">
        <span className="site-header__brand">lexicon</span>
        <AuthBar />
      </header>
      {children}
    </>
  );
}
