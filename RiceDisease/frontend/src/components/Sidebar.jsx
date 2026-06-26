import { useMemo, useState } from "react"

function formatTime(value) {
  if (!value) return ""
  try {
    return new Intl.DateTimeFormat("en", {
      hour: "2-digit",
      minute: "2-digit",
      day: "2-digit",
      month: "2-digit",
    }).format(new Date(value))
  } catch {
    return ""
  }
}

function sortSessions(a, b) {
  return new Date(b.updatedAt || b.createdAt) - new Date(a.updatedAt || a.createdAt)
}

function ActionButton({ label, onClick }) {
  return (
    <button
      className="rounded px-1.5 py-1 text-[11px] text-[var(--text-muted)] opacity-0 transition hover:bg-[var(--button-hover)] hover:text-[var(--text-primary)] focus:opacity-100 group-hover:opacity-100"
      onClick={onClick}
      type="button"
    >
      {label}
    </button>
  )
}

export default function Sidebar({
  activeSessionId,
  sessions,
  onClearSession,
  onDeleteSession,
  onNewChat,
  onRenameSession,
  onSelectSession,
  onTogglePinSession,
}) {
  const [editingId, setEditingId] = useState("")
  const [draftTitle, setDraftTitle] = useState("")

  const { pinned, recent } = useMemo(() => {
    const sorted = [...sessions].sort(sortSessions)
    return {
      pinned: sorted.filter((session) => session.pinned),
      recent: sorted.filter((session) => !session.pinned),
    }
  }, [sessions])

  const startEditing = (session) => {
    setEditingId(session.id)
    setDraftTitle(session.title)
  }

  const saveEditing = () => {
    if (editingId && draftTitle.trim()) onRenameSession(editingId, draftTitle)
    setEditingId("")
    setDraftTitle("")
  }

  const renderSession = (session) => {
    const isActive = session.id === activeSessionId
    const isEditing = editingId === session.id

    return (
      <div
        className={`group rounded-lg px-2 py-2 transition ${
          isActive ? "bg-[var(--active-bg)]" : "hover:bg-[var(--button-hover)]"
        }`}
        key={session.id}
      >
        <button
          className="w-full min-w-0 text-left"
          onClick={() => onSelectSession(session.id)}
          type="button"
        >
          {isEditing ? (
            <input
              autoFocus
              className="w-full rounded-md border border-[var(--border)] bg-[var(--page-bg)] px-2 py-1 text-sm outline-none focus:border-[var(--accent)]"
              onBlur={saveEditing}
              onChange={(event) => setDraftTitle(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") saveEditing()
                if (event.key === "Escape") {
                  setEditingId("")
                  setDraftTitle("")
                }
              }}
              value={draftTitle}
            />
          ) : (
            <>
              <div className="truncate text-sm text-[var(--text-primary)]">{session.title}</div>
              <div className="mt-0.5 truncate text-xs text-[var(--text-muted)]">
                {session.messages.length} messages / {formatTime(session.updatedAt)}
              </div>
            </>
          )}
        </button>

        {!isEditing && (
          <div className="mt-1 flex items-center gap-1">
            <ActionButton
              label={session.pinned ? "Unpin" : "Pin"}
              onClick={(event) => {
                event.stopPropagation()
                onTogglePinSession(session.id)
              }}
            />
            <ActionButton
              label="Rename"
              onClick={(event) => {
                event.stopPropagation()
                startEditing(session)
              }}
            />
            <ActionButton
              label="Clear"
              onClick={(event) => {
                event.stopPropagation()
                onClearSession(session.id)
              }}
            />
            <ActionButton
              label="Delete"
              onClick={(event) => {
                event.stopPropagation()
                onDeleteSession(session.id)
              }}
            />
          </div>
        )}
      </div>
    )
  }

  return (
    <aside className="hidden w-[300px] shrink-0 flex-col border-r border-[var(--border)] bg-[var(--sidebar-bg)] md:flex">
      <div className="p-3">
        <button
          className="flex h-11 w-full items-center rounded-lg border border-[var(--border)] px-3 text-sm font-medium text-[var(--text-primary)] transition hover:bg-[var(--button-hover)]"
          onClick={onNewChat}
          type="button"
        >
          New chat
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-2 pb-4">
        {pinned.length > 0 && (
          <div className="px-2 pb-1 pt-2 text-xs font-medium uppercase tracking-wide text-[var(--text-muted)]">
            Pinned
          </div>
        )}
        <div className="space-y-1">{pinned.map(renderSession)}</div>

        <div className="px-2 pb-1 pt-4 text-xs font-medium uppercase tracking-wide text-[var(--text-muted)]">
          Conversations
        </div>
        <div className="space-y-1">{recent.map(renderSession)}</div>
      </div>

      <div className="border-t border-[var(--border)] px-3 py-3">
        <div className="rounded-lg bg-[var(--panel-bg)] px-3 py-2 text-sm text-[var(--text-secondary)]">
          RiceCare AI
        </div>
      </div>
    </aside>
  )
}
