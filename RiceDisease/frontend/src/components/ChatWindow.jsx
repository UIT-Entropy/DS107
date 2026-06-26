import { useEffect, useMemo, useRef, useState } from "react"
import Message from "./Message"

export default function ChatWindow({
  answerMode,
  answerModes,
  isBusy,
  onAnswerModeChange,
  onSubmit,
  onThemeChange,
  session,
  theme,
}) {
  const [text, setText] = useState("")
  const [files, setFiles] = useState([])
  const bottomRef = useRef(null)
  const fileInputRef = useRef(null)

  const messages = useMemo(() => session?.messages || [], [session?.messages])
  const activeMode = answerModes.find((mode) => mode.id === answerMode) || answerModes[0]
  const canSend = Boolean(text.trim() || files.length)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" })
  }, [messages])

  const removeFile = (index) => {
    setFiles((currentFiles) => currentFiles.filter((_, fileIndex) => fileIndex !== index))
  }

  const submit = async () => {
    if (!canSend || isBusy) return
    const payload = { text, files, mode: activeMode.id }
    setText("")
    setFiles([])
    if (fileInputRef.current) fileInputRef.current.value = ""
    await onSubmit(payload)
  }

  return (
    <div className="flex h-full min-w-0 flex-col bg-[var(--page-bg)] text-[var(--text-primary)]">
      <header className="flex min-h-16 shrink-0 items-center justify-between border-b border-[var(--border)] px-4 md:px-6">
        <div className="min-w-0">
          <div className="truncate text-sm font-semibold">{session?.title || "RiceCare AI"}</div>
          <div className="truncate text-xs text-[var(--text-muted)]">
            YOLO pest detection / DS107 RAG advisor
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            className="rounded-md border border-[var(--border)] px-3 py-1.5 text-xs text-[var(--text-secondary)] hover:bg-[var(--button-hover)]"
            onClick={() => onThemeChange(theme === "dark" ? "light" : "dark")}
            type="button"
          >
            {theme === "dark" ? "Light" : "Dark"}
          </button>
          <div className="rounded-md border border-[var(--border)] px-3 py-1.5 text-xs text-[var(--text-secondary)]">
            {isBusy ? "Working" : "Ready"}
          </div>
        </div>
      </header>

      <section className="flex-1 overflow-y-auto">
        {messages.length === 0 ? (
          <div className="mx-auto flex h-full max-w-3xl flex-col items-center justify-center px-6 text-center">
            <h1 className="text-2xl font-semibold">RiceCare AI</h1>
            <p className="mt-2 max-w-md text-sm leading-6 text-[var(--text-secondary)]">
              Upload a rice pest image for YOLO detection, then ask follow-up advisory questions
              in the same session.
            </p>
          </div>
        ) : (
          <div className="py-4">
            {messages.map((message) => (
              <Message key={message.id} msg={message} />
            ))}
            <div ref={bottomRef} />
          </div>
        )}
      </section>

      <footer className="shrink-0 px-3 pb-4 pt-2 md:px-6">
        <div className="mx-auto max-w-3xl">
          {files.length > 0 && (
            <div className="mb-2 flex flex-wrap gap-2">
              {files.map((file, index) => (
                <div
                  className="flex max-w-full items-center gap-2 rounded-md border border-[var(--border)] bg-[var(--panel-bg)] px-2 py-1 text-xs text-[var(--text-secondary)]"
                  key={`${file.name}-${file.lastModified}-${index}`}
                >
                  <span className="max-w-48 truncate">{file.name}</span>
                  <button
                    className="rounded px-1.5 py-0.5 hover:bg-[var(--button-hover)]"
                    onClick={() => removeFile(index)}
                    type="button"
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>
          )}

          <div className="rounded-xl border border-[var(--border)] bg-[var(--composer-bg)] shadow-[0_18px_55px_rgba(0,0,0,0.16)]">
            <div className="flex items-center justify-between border-b border-[var(--border)] px-3 py-2">
              <label className="flex items-center gap-2 text-xs text-[var(--text-muted)]">
                Mode
                <select
                  className="rounded-md border border-[var(--border)] bg-[var(--panel-bg)] px-2 py-1 text-sm text-[var(--text-primary)] outline-none"
                  disabled={isBusy}
                  onChange={(event) => onAnswerModeChange(event.target.value)}
                  value={activeMode.id}
                >
                  {answerModes.map((mode) => (
                    <option key={mode.id} value={mode.id}>
                      {mode.label}
                    </option>
                  ))}
                </select>
              </label>
              <span className="hidden text-xs text-[var(--text-muted)] sm:block">
                {activeMode.detail}
              </span>
            </div>

            <textarea
              className="max-h-40 min-h-12 w-full resize-none bg-transparent px-5 pt-4 text-[15px] leading-6 outline-none placeholder:text-[var(--text-muted)]"
              disabled={isBusy}
              onChange={(event) => setText(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault()
                  submit()
                }
              }}
              placeholder="Ask a question or upload rice pest images..."
              rows={1}
              value={text}
            />

            <div className="flex items-center justify-between px-3 pb-3">
              <div>
                <button
                  className="rounded-md px-3 py-2 text-sm text-[var(--text-secondary)] hover:bg-[var(--button-hover)] disabled:opacity-50"
                  disabled={isBusy}
                  onClick={() => fileInputRef.current?.click()}
                  type="button"
                >
                  Add images
                </button>
                <input
                  accept="image/*"
                  className="hidden"
                  multiple
                  onChange={(event) => setFiles(Array.from(event.target.files || []))}
                  ref={fileInputRef}
                  type="file"
                />
              </div>

              <button
                className="rounded-md bg-[var(--send-bg)] px-4 py-2 text-sm font-medium text-[var(--send-text)] disabled:bg-[var(--disabled-bg)] disabled:text-[var(--text-muted)]"
                disabled={!canSend || isBusy}
                onClick={submit}
                type="button"
              >
                Send
              </button>
            </div>
          </div>

          <div className="pt-2 text-center text-xs text-[var(--text-muted)]">
            YOLO and RAG outputs are decision support only. Confirm field conditions before action.
          </div>
        </div>
      </footer>
    </div>
  )
}
