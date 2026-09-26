"use client";

import { useAuth } from "@/lib/auth";

export function AuthBar() {
  const { user, logout } = useAuth();
  if (!user) return null;

  return (
    <div className="auth-bar">
      <span className="auth-bar__username">{user.username}</span>
      <button type="button" className="auth-bar__logout" onClick={() => logout()}>
        Sign out
      </button>
    </div>
  );
}
