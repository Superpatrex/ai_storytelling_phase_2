"use client";

import {
  useEffect,
  useRef,
  useState,
  useCallback,
  KeyboardEvent,
} from "react";
import { useRouter } from "next/navigation";
import { WS_URL, type ServerMessage } from "@/lib/ws";

// All possible output categories that the server or client can assign to a line of text
type Category =
  | "narrative" | "system" | "location" | "warning" | "win" | "error" | "player"
  | "room_name" | "room_desc" | "exits" | "objects_present" | "npcs_present" | "inventory_line" | "separator";

// A single line of text in the terminal output, tagged with a category for styling
interface Line {
  id: number;
  text: string;
  category: Category;
}

// Monotonically increasing ID so React can key list items without using array index
let lineId = 0;
function mkLine(text: string, category: Category): Line {
  return { id: lineId++, text, category };
}

// Categories that belong in the story panel — pure narrative only, no location/world-state lines
const STORY_CATS = new Set<Category>([
  "narrative", "warning", "win", "player",
]);

// Categories that are used for spacing/structure but should not appear as visible lines
const HIDDEN_CATS = new Set<Category>(["separator"]);

// Returns inline styles for a line in the terminal output based on its category
function categoryStyle(cat: Category): React.CSSProperties {
  switch (cat) {
    case "player":
      return { color: "var(--player)", fontWeight: 500 };
    case "room_name":
      return { color: "var(--room-name)", fontWeight: 500, marginTop: "1.1rem", letterSpacing: "0.04em" };
    case "room_desc":
      return { color: "var(--room-desc)" };
    case "exits":
      return { color: "var(--exits)", fontSize: "13px", marginTop: "0.3rem" };
    case "objects_present":
      return { color: "var(--items)", fontSize: "13px" };
    case "npcs_present":
      return { color: "var(--people)", fontSize: "13px" };
    case "inventory_line":
      return { color: "var(--carrying)", fontSize: "13px" };
    case "location":
      return { color: "var(--location)" };
    case "warning":
      return { color: "var(--warning)" };
    case "win":
      return { color: "var(--win)", fontWeight: 500 };
    case "error":
      return { color: "var(--error)" };
    case "system":
      return { color: "var(--system)", fontStyle: "italic" };
    default:
      return { color: "var(--text)" };
  }
}

// Returns inline styles for a line in the story panel
function storyLineStyle(line: Line): React.CSSProperties {
  switch (line.category) {
    case "player":
      return { color: "var(--player)", fontWeight: 500, marginTop: "1.4rem" };
    case "warning":
      return { color: "var(--warning)", fontStyle: "italic", marginTop: "0.6rem" };
    case "win":
      return { color: "var(--win)", fontWeight: 500, marginTop: "1rem" };
    default:
      return { color: "var(--text)", lineHeight: "1.85", marginTop: "0.5rem" };
  }
}

// Main game page — manages the WebSocket connection, terminal output, and player input
export default function GamePage() {
  const router = useRouter();
  const ws = useRef<WebSocket | null>(null);
  const terminalBottomRef = useRef<HTMLDivElement>(null);
  const storyBottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Terminal lines (all output) and story lines (narrative-only subset for the story panel)
  const [lines, setLines] = useState<Line[]>([]);
  const [storyLines, setStoryLines] = useState<Line[]>([]);
  const [showStory, setShowStory] = useState(false);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [connected, setConnected] = useState(false);
  const [gameStarted, setGameStarted] = useState(false);
  const [gameComplete, setGameComplete] = useState(false);
  const [protagonist, setProtagonist] = useState("");
  // Input history for ArrowUp/ArrowDown navigation, capped at 50 entries
  const [history, setHistory] = useState<string[]>([]);
  const [, setHistoryIdx] = useState(-1);

  // Appends a line to the terminal and, if it's narrative content, to the story panel as well
  const push = useCallback((text: string, category: Category) => {
    const line = mkLine(text, category);
    if (!HIDDEN_CATS.has(category)) {
      setLines((prev) => [...prev, line]);
    }
    if (STORY_CATS.has(category) && text.trim() !== "") {
      setStoryLines((prev) => [...prev, line]);
    }
  }, []);

  // Auto-scroll the terminal to the bottom whenever new lines are added
  useEffect(() => {
    terminalBottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [lines]);

  // Auto-scroll the story panel to the bottom when it is open and new story lines arrive
  useEffect(() => {
    if (showStory) {
      storyBottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [storyLines, showStory]);

  // Open the WebSocket on mount, start the game session, and handle all incoming server messages
  useEffect(() => {
    const socket = new WebSocket(WS_URL);
    ws.current = socket;

    socket.onopen = () => {
      setConnected(true);
      socket.send(JSON.stringify({ type: "start_game" }));
      setBusy(true);
    };

    socket.onmessage = (e) => {
      const msg: ServerMessage = JSON.parse(e.data);

      // Display the protagonist and goal at game start
      if (msg.type === "game_start") {
        setProtagonist(msg.protagonist);
        setGameStarted(true);
        push(`You are ${msg.protagonist}.`, "system");
        push(`Goal: ${msg.goal}`, "system");
        push("", "system");
      } else if (msg.type === "game_output") {
        if (msg.text.trim() || msg.category !== "system") {
          push(msg.text, msg.category as Category);
        }
      } else if (msg.type === "action_complete") {
        // Re-enable the input and check if the mystery has been solved
        setBusy(false);
        if (msg.game_complete) setGameComplete(true);
        setTimeout(() => inputRef.current?.focus(), 50);
      } else if (msg.type === "error") {
        push(`Error: ${msg.message}`, "error");
        setBusy(false);
      }
    };

    socket.onerror = () => {
      setBusy(false);
    };

    socket.onclose = () => setConnected(false);

    return () => socket.close();
  }, [push]);

  // Sends a player action over the WebSocket and echoes it to the terminal
  const sendAction = useCallback(
    (raw: string) => {
      const trimmed = raw.trim();
      if (!trimmed || busy || !connected) return;

      push(`> ${trimmed}`, "player");
      push("", "system");

      // Prepend to history and reset the history cursor
      setHistory((h) => [trimmed, ...h.slice(0, 49)]);
      setHistoryIdx(-1);
      setInput("");
      setBusy(true);

      ws.current?.send(JSON.stringify({ type: "player_action", input: trimmed }));
    },
    [busy, connected, push]
  );

  // Handles Enter to submit and ArrowUp/Down to navigate input history
  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLInputElement>) => {
      if (e.key === "Enter") {
        sendAction(input);
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setHistoryIdx((idx) => {
          const next = Math.min(idx + 1, history.length - 1);
          setInput(history[next] ?? "");
          return next;
        });
      } else if (e.key === "ArrowDown") {
        e.preventDefault();
        setHistoryIdx((idx) => {
          const next = Math.max(idx - 1, -1);
          setInput(next === -1 ? "" : (history[next] ?? ""));
          return next;
        });
      }
    },
    [input, sendAction, history]
  );

  return (
    <div
      style={{ height: "100vh", display: "flex", flexDirection: "column", overflow: "hidden" }}
      onClick={() => inputRef.current?.focus()}
    >
      {/* Header */}
      <div
        style={{
          flexShrink: 0,
          padding: "0.6rem 1.25rem",
          borderBottom: "1px solid var(--border)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          background: "var(--surface)",
        }}
      >
        <span style={{ color: "var(--dim)", fontSize: "11px", letterSpacing: "0.2em" }}>
          MYSTERY ENGINE
          {protagonist && (
            <span style={{ color: "var(--dim)", marginLeft: "1.5rem" }}>
              {protagonist.toUpperCase()}
            </span>
          )}
        </span>

        <div style={{ display: "flex", gap: "1.25rem", alignItems: "center" }}>
          {/* Story toggle */}
          <button
            onClick={(e) => {
              e.stopPropagation();
              setShowStory((s) => !s);
            }}
            style={{
              background: "transparent",
              border: "none",
              color: showStory ? "var(--player)" : "var(--dim)",
              fontFamily: "inherit",
              fontSize: "11px",
              cursor: "pointer",
              letterSpacing: "0.12em",
              padding: 0,
              transition: "color 0.15s",
            }}
          >
            ◧ STORY
          </button>

          <span
            style={{
              width: "6px",
              height: "6px",
              borderRadius: "50%",
              background: connected ? "var(--win)" : "var(--error)",
              display: "inline-block",
              flexShrink: 0,
            }}
          />

          <button
            onClick={(e) => {
              e.stopPropagation();
              router.push("/");
            }}
            style={{
              background: "transparent",
              border: "none",
              color: "var(--dim)",
              fontFamily: "inherit",
              fontSize: "11px",
              cursor: "pointer",
              letterSpacing: "0.1em",
              padding: 0,
            }}
          >
            ← exit
          </button>
        </div>
      </div>

      {/* Body: terminal + optional story panel */}
      <div style={{ flex: 1, display: "flex", overflow: "hidden" }}>

        {/* Terminal column */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
          {/* Output */}
          <div
            style={{
              flex: 1,
              overflowY: "auto",
              padding: "1.25rem 1.5rem",
              display: "flex",
              flexDirection: "column",
            }}
          >
            {!connected && !gameStarted && (
              <p style={{ color: "var(--dim)" }}>
                connecting<span className="blink">_</span>
              </p>
            )}

            {lines.map((line) => (
              <div
                key={line.id}
                style={{
                  ...categoryStyle(line.category),
                  whiteSpace: "pre-wrap",
                  wordBreak: "break-word",
                  minHeight: line.text === "" ? "0.8rem" : undefined,
                  fontSize: "14px",
                  lineHeight: 1.65,
                }}
              >
                {line.text}
              </div>
            ))}

            {busy && (
              <div style={{ color: "var(--dim)", fontStyle: "italic", fontSize: "13px" }}>
                <span className="blink">_</span>
              </div>
            )}

            <div ref={terminalBottomRef} />
          </div>

          {/* Input bar */}
          <div
            style={{
              flexShrink: 0,
              borderTop: "1px solid var(--border)",
              padding: "0.75rem 1.5rem",
              display: "flex",
              alignItems: "center",
              gap: "0.6rem",
              background: "var(--surface)",
            }}
          >
            <span
              style={{
                color: gameComplete ? "var(--win)" : busy ? "var(--dim)" : "var(--player)",
                fontSize: "14px",
                flexShrink: 0,
                transition: "color 0.2s",
              }}
            >
              &gt;
            </span>
            <input
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={busy || gameComplete || !connected}
              placeholder={
                gameComplete
                  ? "mystery solved"
                  : busy
                    ? ""
                    : "what do you do?"
              }
              style={{
                flex: 1,
                background: "transparent",
                border: "none",
                outline: "none",
                color: "var(--player)",
                fontFamily: "inherit",
                fontSize: "14px",
                caretColor: "var(--cursor)",
              }}
              autoFocus
              spellCheck={false}
              autoComplete="off"
              autoCorrect="off"
            />
            {gameComplete && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  router.push("/");
                }}
                style={{
                  background: "transparent",
                  border: "1px solid var(--win)",
                  color: "var(--win)",
                  fontFamily: "inherit",
                  fontSize: "11px",
                  padding: "0.25rem 0.75rem",
                  cursor: "pointer",
                  letterSpacing: "0.1em",
                }}
              >
                DONE
              </button>
            )}
          </div>
        </div>

        {/* Story panel */}
        {showStory && (
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              width: "420px",
              flexShrink: 0,
              borderLeft: "1px solid var(--border)",
              background: "var(--surface)",
              display: "flex",
              flexDirection: "column",
              overflow: "hidden",
            }}
          >
            {/* Panel header */}
            <div
              style={{
                flexShrink: 0,
                padding: "0.6rem 1.25rem",
                borderBottom: "1px solid var(--border)",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
              }}
            >
              <span style={{ color: "var(--dim)", fontSize: "10px", letterSpacing: "0.25em" }}>
                STORY SO FAR
              </span>
              <span style={{ color: "var(--dim)", fontSize: "10px" }}>
                {storyLines.length > 0 ? `${storyLines.length} entries` : "nothing yet"}
              </span>
            </div>

            {/* Story content */}
            <div
              style={{
                flex: 1,
                overflowY: "auto",
                padding: "1.25rem 1.5rem",
              }}
            >
              {storyLines.length === 0 && (
                <p style={{ color: "var(--dim)", fontSize: "12px" }}>
                  Your story will appear here as you play.
                </p>
              )}

              {storyLines.map((line) => (
                <div
                  key={line.id}
                  style={{
                    ...storyLineStyle(line),
                    whiteSpace: "pre-wrap",
                    wordBreak: "break-word",
                    fontSize: "13px",
                  }}
                >
                  {line.category === "player"
                    ? `→ ${line.text.replace(/^>\s*/, "")}`
                    : line.text}
                </div>
              ))}

              <div ref={storyBottomRef} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
