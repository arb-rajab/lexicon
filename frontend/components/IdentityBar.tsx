"use client";

import { useState } from "react";

import { useIdentity } from "@/lib/identity";

export function IdentityBar() {
  const { userId, setUserId } = useIdentity();
  const [draft, setDraft] = useState(userId);
  const [editing, setEditing] = useState(false);

  const commit = () => {
    setUserId(draft);
    setEditing(false);
  };

  return (
    <div className="identity-bar">
      <span className="identity-bar__label">Identity</span>
      {editing ? (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            commit();
          }}
          className="identity-bar__form"
        >
          <input
            aria-label="User ID"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            autoFocus
          />
          <button type="submit">Save</button>
          <button type="button" onClick={() => setEditing(false)}>
            Cancel
          </button>
        </form>
      ) : (
        <button
          type="button"
          className="identity-bar__value"
          onClick={() => {
            setDraft(userId);
            setEditing(true);
          }}
          title="Switch identity (X-User-Id sent on every request)"
        >
          {userId}
        </button>
      )}
    </div>
  );
}
