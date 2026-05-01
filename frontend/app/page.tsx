"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { API_URL } from "@/lib/ws";

interface Status {
  has_state: boolean;
  story_name: string | null;
  protagonist_name: string | null;
}

export default function Home() {
  const router = useRouter();
  const [status, setStatus] = useState<Status | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_URL}/api/status`)
      .then((r) => r.json())
      .then(setStatus)
      .catch(() => setStatus({ has_state: false, story_name: null, protagonist_name: null }))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div
      style={{
        height: "100vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: "2rem",
        padding: "2rem",
      }}
    >
      <div style={{ textAlign: "center" }}>
        <p style={{ color: "var(--dim)", fontSize: "11px", letterSpacing: "0.3em", marginBottom: "1rem" }}>
          MYSTERY ENGINE
        </p>
        {loading ? (
          <p style={{ color: "var(--dim)" }}>
            connecting<span className="blink">_</span>
          </p>
        ) : status?.has_state ? (
          <>
            <h1
              style={{
                color: "var(--text)",
                fontSize: "22px",
                fontWeight: 500,
                marginBottom: "0.4rem",
                letterSpacing: "0.05em",
              }}
            >
              {status.story_name ?? "UNTITLED MYSTERY"}
            </h1>
            {status.protagonist_name && (
              <p style={{ color: "var(--dim)", fontSize: "12px" }}>
                playing as {status.protagonist_name}
              </p>
            )}
          </>
        ) : (
          <h1 style={{ color: "var(--text)", fontSize: "22px", fontWeight: 500, letterSpacing: "0.05em" }}>
            NO STORY LOADED
          </h1>
        )}
      </div>

      {!loading && (
        <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem", alignItems: "center" }}>
          {status?.has_state && (
            <button
              onClick={() => router.push("/game")}
              style={{
                background: "transparent",
                border: "1px solid var(--player)",
                color: "var(--player)",
                padding: "0.6rem 2rem",
                cursor: "pointer",
                fontFamily: "inherit",
                fontSize: "13px",
                letterSpacing: "0.12em",
                width: "220px",
              }}
            >
              &gt; CONTINUE
            </button>
          )}
          <button
            onClick={() => router.push("/generate")}
            style={{
              background: "transparent",
              border: "1px solid var(--border)",
              color: "var(--dim)",
              padding: "0.6rem 2rem",
              cursor: "pointer",
              fontFamily: "inherit",
              fontSize: "13px",
              letterSpacing: "0.12em",
              width: "220px",
            }}
            onMouseEnter={(e) => {
              (e.target as HTMLButtonElement).style.borderColor = "var(--text)";
              (e.target as HTMLButtonElement).style.color = "var(--text)";
            }}
            onMouseLeave={(e) => {
              (e.target as HTMLButtonElement).style.borderColor = "var(--border)";
              (e.target as HTMLButtonElement).style.color = "var(--dim)";
            }}
          >
            &gt; NEW GAME
          </button>
        </div>
      )}

    </div>
  );
}
