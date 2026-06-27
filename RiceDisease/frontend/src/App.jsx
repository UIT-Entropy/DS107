import { useCallback, useEffect, useMemo, useState } from "react"
import Sidebar from "./components/Sidebar"
import ChatWindow from "./components/ChatWindow"
import { askAdvisor, predictImages } from "./services/api"

const STORAGE_KEY = "ricecare-ai.sessions.v3"
const ACTIVE_KEY = "ricecare-ai.active-session"
const THEME_KEY = "ricecare-ai.theme"
const MODE_KEY = "ricecare-ai.answer-mode"
const DEFAULT_TITLE = "New diagnosis"

const ANSWER_MODES = [
  {
    id: "fast",
    label: "Fast",
    detail: "Quick answer with the required damage and action points.",
  },
  {
    id: "standard",
    label: "Standard",
    detail: "Full demo answer with diagnosis, damage, IPM actions, and notes.",
  },
  {
    id: "deep",
    label: "Deep",
    detail: "More retrieved chunks and a longer field-advisory answer.",
  },
  {
    id: "compare",
    label: "Compare",
    detail: "Runs two configured Gemini models when available.",
  },
]

function nowIso() {
  return new Date().toISOString()
}

function createId(prefix) {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return `${prefix}-${crypto.randomUUID()}`
  }
  return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2)}`
}

function createSession(title = DEFAULT_TITLE) {
  const id = createId("chat")
  const createdAt = nowIso()
  return {
    id,
    backendSessionId: id,
    title,
    pinned: false,
    messages: [],
    createdAt,
    updatedAt: createdAt,
  }
}

function createMessage({ role, content, files = [], status = "done" }) {
  return {
    id: createId("msg"),
    role,
    content,
    files,
    status,
    createdAt: nowIso(),
  }
}

function normalizeSession(session, index) {
  const id = session?.id || createId("chat")
  const createdAt = session?.createdAt || nowIso()
  return {
    id,
    backendSessionId: session?.backendSessionId || id,
    title: session?.title || (index === 0 ? DEFAULT_TITLE : `Conversation ${index + 1}`),
    pinned: Boolean(session?.pinned),
    messages: Array.isArray(session?.messages) ? session.messages : [],
    createdAt,
    updatedAt: session?.updatedAt || createdAt,
  }
}

function getInitialState() {
  if (typeof window === "undefined") {
    const session = createSession()
    return { sessions: [session], activeSessionId: session.id }
  }

  try {
    const stored = JSON.parse(window.localStorage.getItem(STORAGE_KEY) || "[]")
    const sessions = Array.isArray(stored)
      ? stored.map(normalizeSession).filter((session) => session.id)
      : []

    if (sessions.length > 0) {
      const savedActiveId = window.localStorage.getItem(ACTIVE_KEY)
      const activeSessionId = sessions.some((session) => session.id === savedActiveId)
        ? savedActiveId
        : sessions[0].id
      return { sessions, activeSessionId }
    }
  } catch {
    window.localStorage.removeItem(STORAGE_KEY)
  }

  const session = createSession()
  return { sessions: [session], activeSessionId: session.id }
}

function getInitialTheme() {
  if (typeof window === "undefined") return "dark"
  return window.localStorage.getItem(THEME_KEY) === "light" ? "light" : "dark"
}

function getInitialMode() {
  if (typeof window === "undefined") return "standard"
  const stored = window.localStorage.getItem(MODE_KEY)
  return ANSWER_MODES.some((mode) => mode.id === stored) ? stored : "standard"
}

function compactTitle(text) {
  const value = text.replace(/\s+/g, " ").trim()
  if (!value) return ""
  return value.length > 42 ? `${value.slice(0, 42)}...` : value
}

function formatConfidence(value) {
  return typeof value === "number" ? `${(value * 100).toFixed(1)}%` : "unknown"
}

function formatPredictionMessage(results) {
  if (!results.length) {
    return "YOLO did not return any prediction for this image."
  }

  return results
    .map((result, index) => {
      if (result.success === false) {
        return [
          `### Image ${index + 1}`,
          `Could not process this image: **${result.error || "unknown error"}**`,
        ].join("\n\n")
      }

      const disease = result.disease || "No clear detection"
      const confidence = formatConfidence(result.confidence)
      const countLine = Number.isFinite(result.count)
        ? `\n- Detection count: **${result.count}**`
        : ""
      const classLine = result.class_id ? `\n- YOLO class id: \`${result.class_id}\`` : ""
      const image = result.image_url ? `\n\n![YOLO image ${index + 1}](${result.image_url})` : ""

      return [
        `### Image ${index + 1}`,
        `- Prediction: **${disease}**`,
        `- Confidence: **${confidence}**${countLine}${classLine}`,
        image,
      ].join("\n")
    })
    .join("\n\n---\n\n")
}

function predictionTitle(results, fallbackText) {
  const disease = results.find((result) => result?.disease)?.disease
  return compactTitle(disease || fallbackText || DEFAULT_TITLE)
}

function formatSources(sources = []) {
  if (!sources.length) {
    return "\n\n### Sources\nNo RAG sources were returned by the backend."
  }

  const rows = sources.map((source) => {
    const title = source.title || source.section || "Knowledge chunk"
    const org = source.source_org ? ` - ${source.source_org}` : ""
    const section = source.section ? `\n  Section: ${source.section}` : ""
    const url = source.source_url ? `\n  URL: ${source.source_url}` : ""
    const excerpt = source.excerpt ? `\n  Excerpt: ${source.excerpt}` : ""
    return `- [${source.label}] ${title}${org}${section}${url}${excerpt}`
  })

  return `\n\n### Sources\n${rows.join("\n")}`
}

function formatAdvisorContent(data) {
  const answers = Array.isArray(data.answers) ? data.answers : []
  const answerBody =
    answers.length > 1
      ? answers.map((item) => `## ${item.label}\n\n${item.answer}`).join("\n\n---\n\n")
      : data.answer || answers[0]?.answer || "Advisor did not return an answer."

  return `${answerBody}${formatSources(data.sources)}`
}

export default function App() {
  const [initialState] = useState(getInitialState)
  const [sessions, setSessions] = useState(initialState.sessions)
  const [activeSessionId, setActiveSessionId] = useState(initialState.activeSessionId)
  const [theme, setTheme] = useState(getInitialTheme)
  const [answerMode, setAnswerMode] = useState(getInitialMode)

  const activeSession = useMemo(
    () => sessions.find((session) => session.id === activeSessionId) || sessions[0],
    [activeSessionId, sessions],
  )
  const activeIsBusy = Boolean(
    activeSession?.messages?.some((message) => message.status === "loading"),
  )

  useEffect(() => {
    if (typeof window === "undefined") return
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions))
    if (activeSessionId) window.localStorage.setItem(ACTIVE_KEY, activeSessionId)
  }, [activeSessionId, sessions])

  useEffect(() => {
    if (typeof window === "undefined") return
    window.localStorage.setItem(THEME_KEY, theme)
    window.localStorage.setItem(MODE_KEY, answerMode)
  }, [answerMode, theme])

  const updateSession = useCallback((sessionId, updater) => {
    setSessions((currentSessions) =>
      currentSessions.map((session) => {
        if (session.id !== sessionId) return session
        const nextSession =
          typeof updater === "function" ? updater(session) : { ...session, ...updater }
        return { ...nextSession, updatedAt: nowIso() }
      }),
    )
  }, [])

  const replaceMessage = useCallback(
    (sessionId, messageId, patch) => {
      updateSession(sessionId, (session) => ({
        ...session,
        messages: session.messages.map((message) =>
          message.id === messageId ? { ...message, ...patch } : message,
        ),
      }))
    },
    [updateSession],
  )

  const appendAssistantMessage = useCallback(
    (sessionId, message) => {
      updateSession(sessionId, (session) => ({
        ...session,
        messages: [...session.messages, message],
      }))
    },
    [updateSession],
  )

  const startNewChat = useCallback(() => {
    const session = createSession()
    setSessions((currentSessions) => [session, ...currentSessions])
    setActiveSessionId(session.id)
  }, [])

  const renameSession = useCallback(
    (sessionId, title) => {
      const nextTitle = compactTitle(title)
      if (nextTitle) updateSession(sessionId, { title: nextTitle })
    },
    [updateSession],
  )

  const deleteSession = useCallback(
    (sessionId) => {
      const filtered = sessions.filter((session) => session.id !== sessionId)
      if (!filtered.length) {
        const session = createSession()
        setSessions([session])
        setActiveSessionId(session.id)
        return
      }

      setSessions(filtered)
      if (activeSessionId === sessionId) setActiveSessionId(filtered[0].id)
    },
    [activeSessionId, sessions],
  )

  const clearSession = useCallback(
    (sessionId) => {
      updateSession(sessionId, (session) => ({
        ...session,
        backendSessionId: session.id,
        messages: [],
        title: DEFAULT_TITLE,
      }))
    },
    [updateSession],
  )

  const togglePinSession = useCallback(
    (sessionId) => {
      updateSession(sessionId, (session) => ({ ...session, pinned: !session.pinned }))
    },
    [updateSession],
  )

  const enqueueTurn = useCallback(
    (sessionId, userMessage, pendingMessage, titleHint) => {
      updateSession(sessionId, (session) => ({
        ...session,
        title: session.messages.length === 0 && titleHint ? titleHint : session.title,
        messages: [...session.messages, userMessage, pendingMessage],
      }))
    },
    [updateSession],
  )

  const handleSubmit = useCallback(
    async ({ text, files, mode }) => {
      const cleanText = text.trim()
      const selectedFiles = Array.from(files || [])
      const selectedMode = ANSWER_MODES.some((item) => item.id === mode) ? mode : answerMode
      const targetSession = sessions.find((session) => session.id === activeSessionId)
      if (!targetSession || (!cleanText && !selectedFiles.length)) return

      const fileNames = selectedFiles.map((file) => file.name)
      const userMessage = createMessage({
        role: "user",
        content: cleanText || `Uploaded ${selectedFiles.length} rice image(s) for diagnosis.`,
        files: fileNames,
      })
      const pendingMessage = createMessage({
        role: "assistant",
        content: selectedFiles.length ? "Running YOLO detection..." : "Asking the RAG advisor...",
        status: "loading",
      })
      const titleHint = compactTitle(cleanText) || (selectedFiles.length ? "Rice image" : "")

      enqueueTurn(targetSession.id, userMessage, pendingMessage, titleHint)

      if (selectedFiles.length) {
        try {
          const data = await predictImages(selectedFiles)
          const results = data.results || []
          const primaryPrediction = results.find((result) => result?.session_id)
          const advisorSessionId =
            primaryPrediction?.session_id || targetSession.backendSessionId || targetSession.id

          replaceMessage(targetSession.id, pendingMessage.id, {
            content: formatPredictionMessage(results),
            predictions: results,
            status: "done",
          })

          updateSession(targetSession.id, (session) => ({
            ...session,
            backendSessionId: advisorSessionId,
            title:
              session.messages.length <= 2 ? predictionTitle(results, cleanText) : session.title,
          }))

          if (cleanText) {
            const advisorPending = createMessage({
              role: "assistant",
              content: "Writing advisory answer from YOLO context...",
              status: "loading",
            })
            appendAssistantMessage(targetSession.id, advisorPending)

            const advisorData = await askAdvisor({
              question: cleanText,
              sessionId: advisorSessionId,
              mode: selectedMode,
            })

            replaceMessage(targetSession.id, advisorPending.id, {
              content: formatAdvisorContent(advisorData),
              status: "done",
            })
          }
        } catch (error) {
          replaceMessage(targetSession.id, pendingMessage.id, {
            content: `Could not process image: ${error.message}`,
            status: "error",
          })
        }
        return
      }

      try {
        const data = await askAdvisor({
          question: cleanText,
          sessionId: targetSession.backendSessionId || targetSession.id,
          mode: selectedMode,
        })
        replaceMessage(targetSession.id, pendingMessage.id, {
          content: formatAdvisorContent(data),
          status: "done",
        })
      } catch (error) {
        replaceMessage(targetSession.id, pendingMessage.id, {
          content: `Could not call advisor: ${error.message}`,
          status: "error",
        })
      }
    },
    [
      activeSessionId,
      appendAssistantMessage,
      answerMode,
      enqueueTurn,
      replaceMessage,
      sessions,
      updateSession,
    ],
  )

  return (
    <div className={`app-shell ${theme} flex h-screen overflow-hidden`}>
      <Sidebar
        activeSessionId={activeSession?.id}
        sessions={sessions}
        onClearSession={clearSession}
        onDeleteSession={deleteSession}
        onNewChat={startNewChat}
        onRenameSession={renameSession}
        onSelectSession={setActiveSessionId}
        onTogglePinSession={togglePinSession}
      />

      <main className="flex min-w-0 flex-1 flex-col">
        <ChatWindow
          answerMode={answerMode}
          answerModes={ANSWER_MODES}
          isBusy={activeIsBusy}
          key={activeSession?.id || "empty-chat"}
          onAnswerModeChange={setAnswerMode}
          onSubmit={handleSubmit}
          onThemeChange={setTheme}
          session={activeSession}
          theme={theme}
        />
      </main>
    </div>
  )
}
