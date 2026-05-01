"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { WS_URL, type ServerMessage } from "@/lib/ws";

const PHASES = [
  { id: "01_initialize", label: "Initializing story" },
  { id: "02_loop", label: "Writing story beats" },
  { id: "03_fixer", label: "Fixing plot holes" },
  { id: "04_plot_point_annotator", label: "Annotating plot points" },
  { id: "05_dependency_analyzer", label: "Analyzing dependencies" },
  { id: "06_world_graph_builder", label: "Building world map" },
  { id: "07_object_npc_placer", label: "Placing objects & characters" },
];

type PhaseStatus = "pending" | "starting" | "running" | "complete" | "error";

// ── Minigame ──────────────────────────────────────────────────────────────────

const WORDS = [
  // Core mystery
  "ALIBI", "CULPRIT", "MOTIVE", "CIPHER", "SUSPECT",
  "CLUE", "EVIDENCE", "WITNESS", "MYSTERY", "DETECTIVE",
  "FORENSIC", "INSPECTOR", "VERDICT", "INQUIRY", "SLEUTH",
  "POISON", "DAGGER", "CORONER", "RANSOM", "DECRYPT",
  "MAGNIFY", "DEDUCE", "CONCEAL", "MISDIRECT", "ACCOMPLICE",

  // Crimes & acts
  "MURDER", "THEFT", "FORGERY", "EXTORTION", "SABOTAGE",
  "TRESPASS", "CONSPIRE", "BLACKMAIL", "AMBUSH", "SMUGGLE",
  "KIDNAP", "ARSON", "BRIBERY", "PERJURY", "EMBEZZLE",
  "ABSCOND", "LARCENY", "TREACHERY", "COERCE", "BETRAY",
  "ASSAULT", "FRAUD", "STALKING", "ESPIONAGE", "TREASON",
  "VANDALISM", "DEFAME", "COUNTERFEIT", "INTERCEPT", "PLUNDER",
  "PIRACY", "DEFRAUD", "ABDUCT", "POISON", "RANSACK",
  "INTIMIDATE", "SUFFOCATE", "STRANGLE", "ENTRAP", "IMPERSONATE",

  // Investigation
  "AUTOPSY", "BALLISTIC", "DOSSIER", "FINGERPRINT", "TOXICOLOGY",
  "SPECIMEN", "ANALYSIS", "DEDUCTION", "HYPOTHESIS", "PROFILE",
  "TIMELINE", "PERPETRATOR", "TESTIMONY", "CONFESSION",
  "WARRANT", "SUBPOENA", "HANDWRITING", "SURVEILLANCE", "INFORMANT",
  "CASEFILE", "EVIDENCE", "BLOODSTAIN", "FIBRES", "MOTIVE",
  "ALIBI", "CROSSCHECK", "DATABASE", "POLYGRAPH", "PATHOLOGY",
  "TRAJECTORY", "RESIDUE", "LIGATURE", "LACERATION", "CONTUSION",
  "INFERENCE", "COMPOSITE", "CHRONICLE", "FORENSICS", "EXHUMATION",
  "TRANSCRIPT", "STATEMENT", "DEBRIEF", "SEQUENCE", "DISCLOSURE",

  // People & roles
  "CONSTABLE", "MAGISTRATE", "PROSECUTOR", "SOLICITOR",
  "FUGITIVE", "INFORMER", "UNDERCOVER", "PROFILER",
  "PATHOLOGIST", "JOURNALIST", "BYSTANDER", "LIEUTENANT",
  "COMMISSIONER", "DETECTIVE", "SERGEANT", "WARDEN", "DEPUTY",
  "BARONESS", "CONFIDANT", "ACCOMPLICE", "RINGLEADER", "OPERATIVE",
  "LIAISON", "HANDLER", "ANALYST", "ARCHIVIST", "WHISTLEBLOWER",
  "ANTAGONIST", "PROTAGONIST", "CONSPIRATOR", "MASTERMIND", "ENFORCER",
  "TURNCOAT", "DOUBLE", "HANDLER", "LACKEY", "LOOKOUT",

  // Places & objects
  "CORRIDOR", "CELLAR", "LABORATORY", "OBSERVATORY", "BALLROOM",
  "REVOLVER", "SCALPEL", "BRIEFCASE", "LOCKBOX", "TELEGRAM",
  "LEDGER", "MANUSCRIPT", "BLUEPRINT", "LOCKET", "DECANTER",
  "FIREPLACE", "LANTERN", "COMPASS", "PHOTOGRAPH", "ENVELOPE",
  "ATTIC", "BASEMENT", "LIBRARY", "CONSERVATORY", "DUNGEON",
  "ARCHIVE", "VAULT", "CHAMBER", "GATEHOUSE", "TURRET",
  "CATACOMBS", "PASSAGE", "CRYPT", "ANTECHAMBER", "GALLERY",
  "SYRINGE", "VIAL", "CAPSULE", "CANISTER", "CONTAINER",
  "LOCKPICK", "SKELETON", "CROWBAR", "GARROTE", "WRENCH",
  "PISTOL", "BAYONET", "STILETTO", "CROSSBOW", "BLOWPIPE",
  "TYPEWRITER", "MONOCLE", "POCKETWATCH", "SIGNET", "INKWELL",
  "CANDLESTICK", "MIRROR", "KEYCHAIN", "BRIEFING", "LEDGER",

  // Atmosphere & narrative
  "CRYPTIC", "SINISTER", "ELUSIVE", "DEVIOUS", "CLANDESTINE",
  "CONCEALED", "OBSCURED", "SHADOWED", "PHANTOM", "ENIGMATIC",
  "DESOLATE", "PARANOID", "RUTHLESS", "CUNNING", "INCOGNITO",
  "LURKING", "HAUNTED", "OMINOUS", "MACABRE", "NOTORIOUS",
  "FOREBODING", "TREACHEROUS", "DECEPTIVE", "MENACING", "LABYRINTHINE",
  "NEFARIOUS", "MALEVOLENT", "INSIDIOUS", "DUPLICITOUS", "FURTIVE",
  "BROODING", "UNSETTLING", "DESPERATE", "FRANTIC", "CALCULATED",
  "METHODICAL", "BRAZEN", "STEALTHY", "EERIE", "SUSPICIOUS",
  "PERPLEXING", "BAFFLING", "INEXPLICABLE", "BEWILDERING", "HAUNTING",
  "TORMENTED", "RELENTLESS", "OBSESSIVE", "VINDICTIVE", "PREDATORY",

  // Actions & methods
  "SCRUTINIZE", "INTERROGATE", "INVESTIGATE", "IMPLICATE",
  "ELIMINATE", "EXONERATE", "CORROBORATE", "FABRICATE", "ORCHESTRATE",
  "DISAPPEAR", "DISGUISE", "INFILTRATE", "RECONSTRUCT",
  "IDENTIFY", "CLASSIFY", "DOCUMENT", "EXAMINE", "UNRAVEL",
  "SURVEIL", "CATALOGUE", "TRIANGULATE", "ISOLATE", "CORRELATE",
  "AUTHENTICATE", "VALIDATE", "CONTRADICT", "DISPROVE", "ESTABLISH",
  "GATHER", "PURSUE", "SHADOW", "FOLLOW", "APPREHEND",
  "ARREST", "DETAIN", "RELEASE", "ACQUIT", "CONVICT",
  "PROSECUTE", "APPEAL", "OVERTURN", "SENTENCE", "PARDON",
  "EXTRACT", "ENCODE", "TRANSMIT", "INTERCEPT", "DECIPHER",
  "SEARCH", "RETRIEVE", "ANALYSE", "COMPARE", "CONCLUDE",
  "EXPOSE", "REVEAL", "UNCOVER", "DISCLOSE", "CONFIRM",

  // Literary & genre
  "WHODUNIT", "THRILLER", "SUSPENSE", "INTRIGUE", "CONSPIRACY",
  "SCANDAL", "REVELATION", "DENOUEMENT", "RESOLUTION", "CLIMAX",
  "SUBPLOT", "FLASHBACK", "FORESHADOW", "NARRATIVE", "CHRONICLE",
  "PROTAGONIST", "ANTAGONIST", "UNRELIABLE", "TWIST", "EPILOGUE",
  "CHAPTER", "PROLOGUE", "MONOLOGUE", "DIALOGUE", "WITNESS",
];

function scramble(word: string): string {
  const arr = word.split("");
  let result: string;
  do {
    for (let i = arr.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [arr[i], arr[j]] = [arr[j], arr[i]];
    }
    result = arr.join("");
  } while (result === word && word.length > 1);
  return result;
}

function pickWord(): string {
  return WORDS[Math.floor(Math.random() * WORDS.length)];
}

function Minigame() {
  const [word, setWord] = useState(() => pickWord());
  const [scrambled, setScrambled] = useState(() => "");
  const [input, setInput] = useState("");
  const [feedback, setFeedback] = useState<"correct" | "wrong" | null>(null);
  const [score, setScore] = useState({ correct: 0, total: 0 });
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setScrambled(scramble(word));
  }, [word]);

  const next = useCallback(() => {
    const w = pickWord();
    setWord(w);
    setInput("");
    setFeedback(null);
    setTimeout(() => inputRef.current?.focus(), 50);
  }, []);

  const submit = useCallback(() => {
    if (!input.trim()) return;
    const correct = input.trim().toUpperCase() === word;
    setFeedback(correct ? "correct" : "wrong");
    setScore((s) => ({ correct: s.correct + (correct ? 1 : 0), total: s.total + 1 }));
    setTimeout(next, 900);
  }, [input, word, next]);

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: "1.5rem",
        padding: "2rem",
        borderLeft: "1px solid var(--border)",
        height: "100%",
        justifyContent: "center",
      }}
    >
      <p style={{ color: "var(--dim)", fontSize: "10px", letterSpacing: "0.3em" }}>
        DECIPHER WHILE YOU WAIT
      </p>

      <div
        style={{
          fontSize: "28px",
          letterSpacing: "0.35em",
          color: "var(--player)",
          minHeight: "2.5rem",
          textAlign: "center",
        }}
      >
        {scrambled}
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
        <span style={{ color: "var(--dim)" }}>&gt;</span>
        <input
          ref={inputRef}
          value={input}
          onChange={(e) => setInput(e.target.value.toUpperCase())}
          onKeyDown={(e) => e.key === "Enter" && submit()}
          placeholder="type your answer"
          autoFocus
          disabled={feedback !== null}
          style={{
            background: "transparent",
            border: "none",
            borderBottom: "1px solid var(--border)",
            color: "var(--text)",
            fontFamily: "inherit",
            fontSize: "16px",
            outline: "none",
            width: "200px",
            textAlign: "center",
            letterSpacing: "0.15em",
            padding: "0.25rem 0",
          }}
        />
      </div>

      <div style={{ minHeight: "1.4rem", textAlign: "center" }}>
        {feedback === "correct" && (
          <span style={{ color: "var(--win)", fontSize: "12px", letterSpacing: "0.1em" }}>
            ✓ CORRECT
          </span>
        )}
        {feedback === "wrong" && (
          <span style={{ color: "var(--error)", fontSize: "12px", letterSpacing: "0.1em" }}>
            ✗ {word}
          </span>
        )}
      </div>

      <p style={{ color: "var(--dim)", fontSize: "11px" }}>
        {score.correct} / {score.total}
      </p>
    </div>
  );
}

// ── Generate page ─────────────────────────────────────────────────────────────

export default function GeneratePage() {
  const router = useRouter();
  const ws = useRef<WebSocket | null>(null);
  const [phases, setPhases] = useState<Record<string, PhaseStatus>>({});
  const [connected, setConnected] = useState(false);
  const [done, setDone] = useState(false);

  const totalComplete = PHASES.filter((p) => phases[p.id] === "complete").length;
  const progressPct = Math.round((totalComplete / PHASES.length) * 100);

  useEffect(() => {
    const socket = new WebSocket(WS_URL);
    ws.current = socket;

    socket.onopen = () => {
      setConnected(true);
      socket.send(JSON.stringify({ type: "start_generation" }));
    };

    socket.onmessage = (e) => {
      const msg: ServerMessage = JSON.parse(e.data);

      if (msg.type === "generation_progress") {
        setPhases((prev) => ({ ...prev, [msg.phase]: msg.status }));
      } else if (msg.type === "generation_complete") {
        setDone(true);
        setTimeout(() => router.push("/game"), 1200);
      }
    };

    socket.onerror = () => {};
    socket.onclose = () => setConnected(false);

    return () => socket.close();
  }, [router]);

  return (
    <div
      style={{
        height: "100vh",
        display: "grid",
        gridTemplateColumns: "1fr 1fr",
        overflow: "hidden",
      }}
    >
      {/* Left: Phase progress */}
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          padding: "3rem 2.5rem",
          gap: "0",
          justifyContent: "center",
        }}
      >
        <p style={{ color: "var(--dim)", fontSize: "10px", letterSpacing: "0.3em", marginBottom: "2rem" }}>
          GENERATING YOUR MYSTERY
        </p>

        <div style={{ display: "flex", flexDirection: "column", gap: "0" }}>
          {PHASES.map((phase, idx) => {
            const status = phases[phase.id] ?? "pending";
            const isRunning = status === "running";
            const isComplete = status === "complete";
            const isError = status === "error";

            return (
              <div
                key={phase.id}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "0.85rem",
                  padding: "0.65rem 0",
                  borderBottom: idx < PHASES.length - 1 ? "1px solid #1a1a1a" : "none",
                  opacity: status === "pending" ? 0.35 : 1,
                  transition: "opacity 0.3s",
                }}
              >
                <span
                  style={{
                    fontSize: "13px",
                    color: isComplete
                      ? "var(--win)"
                      : isRunning
                        ? "var(--player)"
                        : isError
                          ? "var(--error)"
                          : "var(--dim)",
                    flexShrink: 0,
                    width: "16px",
                    textAlign: "center",
                  }}
                  className={isRunning ? "pulse-dot" : ""}
                >
                  {isComplete ? "✓" : isRunning ? "◉" : isError ? "✗" : "○"}
                </span>

                <span
                  style={{
                    color: isComplete
                      ? "var(--text)"
                      : isRunning
                        ? "var(--player)"
                        : "var(--dim)",
                    fontSize: "13px",
                    flex: 1,
                  }}
                >
                  {phase.label}
                </span>

                {isRunning && (
                  <span style={{ color: "var(--dim)", fontSize: "11px" }}>
                    running<span className="blink">_</span>
                  </span>
                )}
                {isComplete && (
                  <span style={{ color: "var(--dim)", fontSize: "11px" }}>done</span>
                )}
              </div>
            );
          })}
        </div>

        {/* Progress bar */}
        <div
          style={{
            marginTop: "2rem",
            height: "1px",
            background: "var(--border)",
            position: "relative",
          }}
        >
          <div
            style={{
              position: "absolute",
              left: 0,
              top: 0,
              height: "1px",
              width: `${progressPct}%`,
              background: done ? "var(--win)" : "var(--player)",
              transition: "width 0.5s ease",
            }}
          />
        </div>
        <p style={{ color: "var(--dim)", fontSize: "11px", marginTop: "0.5rem" }}>
          {done ? "complete — entering game..." : connected ? `${progressPct}%` : "connecting..."}
        </p>
      </div>

      {/* Right: Minigame */}
      <Minigame />
    </div>
  );
}
