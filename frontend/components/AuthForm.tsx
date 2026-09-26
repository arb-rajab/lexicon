"use client";

import { useState } from "react";

import { AuthError, useAuth } from "@/lib/auth";

const FRIENDLY_MESSAGE: Record<string, string> = {
  invalid_credentials: "Invalid username or password.",
  username_taken: "That username is already registered.",
  rate_limited: "Too many attempts — slow down and try again shortly.",
  validation_error: "Check your username and password and try again.",
};

export function AuthForm() {
  const { login, register } = useAuth();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      if (mode === "login") {
        await login(username, password);
      } else {
        await register(username, password);
      }
    } catch (err) {
      if (err instanceof AuthError) {
        setError(FRIENDLY_MESSAGE[err.code] ?? err.message);
      } else {
        setError("Something went wrong.");
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="auth-page">
      <h1>lexicon</h1>
      <p className="muted">Grounded document Q&amp;A — every answer is citation-backed or refused.</p>

      <form onSubmit={handleSubmit} className="auth-form">
        <h2>{mode === "login" ? "Sign in" : "Create an account"}</h2>

        <label htmlFor="auth-username">Username</label>
        <input
          id="auth-username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          autoComplete="username"
          disabled={submitting}
        />

        <label htmlFor="auth-password">Password</label>
        <input
          id="auth-password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete={mode === "login" ? "current-password" : "new-password"}
          disabled={submitting}
        />

        {error ? (
          <p role="alert" className="error-banner">
            {error}
          </p>
        ) : null}

        <button type="submit" disabled={submitting || !username.trim() || !password}>
          {submitting ? "Please wait…" : mode === "login" ? "Sign in" : "Create account"}
        </button>

        <button
          type="button"
          className="auth-form__switch"
          onClick={() => {
            setMode(mode === "login" ? "register" : "login");
            setError(null);
          }}
          disabled={submitting}
        >
          {mode === "login" ? "Need an account? Register" : "Already have an account? Sign in"}
        </button>
      </form>
    </main>
  );
}
