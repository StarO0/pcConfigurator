import { create } from "zustand";
import { useConfiguratorStore } from "@/store/configurator-store";

export type ChatRole = "user" | "ai";
export type ChatPhase = "idle" | "clarifying" | "generating" | "results" | "chatting";

export type ChatMessage = {
  id: string;
  role: ChatRole;
  content: string;
  timestamp: number;
  isTyping?: boolean;
};

type ChatState = {
  messages: ChatMessage[];
  phase: ChatPhase;
  initialPrompt: string;
  // Actions
  sendMessage: (content: string) => void;
  clearChat: () => void;
  setPhase: (phase: ChatPhase) => void;
};

function makeAiMessage(content: string, isTyping = false): ChatMessage {
  return {
    id: crypto.randomUUID(),
    role: "ai",
    content,
    timestamp: Date.now(),
    isTyping,
  };
}

function makeUserMessage(content: string): ChatMessage {
  return {
    id: crypto.randomUUID(),
    role: "user",
    content,
    timestamp: Date.now(),
  };
}

/** Pick a contextual AI refinement response based on keywords in the user message. */
function getRefinementResponse(content: string): string {
  const lower = content.toLowerCase();

  if (
    lower.includes("cheaper") ||
    lower.includes("budget") ||
    lower.includes("дешевле") ||
    lower.includes("tańszy")
  ) {
    return "I'll optimize for better value — swapping components where we can cut cost without hurting real-world performance.";
  }

  if (lower.includes("gaming")) {
    return "Focusing on gaming performance — prioritising a stronger GPU and pairing it with a CPU that won't bottleneck it.";
  }

  if (
    lower.includes("quiet") ||
    lower.includes("тихий") ||
    lower.includes("cichy")
  ) {
    return "I'll prioritise quiet operation — looking at low-noise coolers and airflow-optimised cases for you.";
  }

  return "Adjusting the build based on your feedback — give me a moment to re-generate the recommendations.";
}

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  phase: "idle",
  initialPrompt: "",

  setPhase: (phase) => set({ phase }),

  sendMessage: (content) => {
    const { phase } = get();

    const userMsg = makeUserMessage(content);

    // ── IDLE: first message from user ──────────────────────────────────────────
    if (phase === "idle") {
      set((state) => ({
        messages: [...state.messages, userMsg],
        initialPrompt: content,
        phase: "clarifying",
      }));

      // Simulate AI typing then respond
      setTimeout(() => {
        const aiMsg = makeAiMessage(
          "Great! To find the best build for you, I have a couple of quick questions — what's your budget? And will you mainly use the PC for gaming, work, or a mix of both?"
        );
        set((state) => ({ messages: [...state.messages, aiMsg] }));
      }, 1500);

      return;
    }

    // ── CLARIFYING: user answered the clarifying question ─────────────────────
    if (phase === "clarifying") {
      set((state) => ({
        messages: [...state.messages, userMsg],
        phase: "generating",
      }));

      // Brief "generating" message
      setTimeout(() => {
        const generatingMsg = makeAiMessage(
          "Perfect, generating 5 builds for you — this will just take a moment…"
        );
        set((state) => ({ messages: [...state.messages, generatingMsg] }));

        // Trigger actual build generation after additional delay
        setTimeout(() => {
          const prompt = `${get().initialPrompt}. ${content}`;
          void useConfiguratorStore.getState().triggerGenerate(prompt);
          set({ phase: "chatting" });
        }, 2500);
      }, 500);

      return;
    }

    // ── CHATTING: user refines after seeing results ────────────────────────────
    if (phase === "chatting") {
      set((state) => ({
        messages: [...state.messages, userMsg],
      }));

      setTimeout(() => {
        const ackMsg = makeAiMessage("Got it! Let me adjust the build…");
        set((state) => ({ messages: [...state.messages, ackMsg] }));

        setTimeout(() => {
          const refinementResponse = getRefinementResponse(content);
          const detailMsg = makeAiMessage(refinementResponse);
          set((state) => ({ messages: [...state.messages, detailMsg] }));

          // Re-generate builds
          const prompt = `${get().initialPrompt}. ${content}`;
          void useConfiguratorStore.getState().triggerGenerate(prompt);
        }, 2000);
      }, 1500);

      return;
    }
  },

  clearChat: () =>
    set({
      messages: [],
      phase: "idle",
      initialPrompt: "",
    }),
}));
