import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import TypingIndicator from "./TypingIndicator"

const markdownComponents = {
  a(props) {
    return (
      <a
        {...props}
        className="text-[var(--link)] underline decoration-[var(--link)]/40 underline-offset-4 hover:decoration-[var(--link)]"
        target="_blank"
        rel="noreferrer"
      />
    )
  },
  img(props) {
    return (
      <img
        {...props}
        className="mt-3 max-h-[460px] w-full rounded-lg border border-[var(--border)] object-contain"
        loading="lazy"
      />
    )
  },
}

export default function Message({ msg }) {
  const isUser = msg.role === "user"
  const isLoading = msg.status === "loading"
  const isError = msg.status === "error"

  if (isUser) {
    return (
      <div className="mx-auto flex w-full max-w-3xl justify-end px-4 py-3">
        <div className="max-w-[82%] rounded-xl bg-[var(--user-bubble)] px-4 py-3 text-sm leading-6 text-[var(--user-text)] md:max-w-[72%]">
          <div className="markdown markdown-user">
            <ReactMarkdown components={markdownComponents} remarkPlugins={[remarkGfm]}>
              {msg.content}
            </ReactMarkdown>
          </div>

          {msg.files?.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-2">
              {msg.files.map((fileName) => (
                <div
                  className="max-w-full truncate rounded-md bg-[var(--file-chip)] px-2 py-1 text-xs text-[var(--text-secondary)]"
                  key={fileName}
                >
                  {fileName}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="mx-auto flex w-full max-w-3xl px-4 py-5">
      <div
        className={`min-w-0 flex-1 text-sm leading-7 ${
          isError ? "text-[var(--error-text)]" : "text-[var(--text-primary)]"
        }`}
      >
        {isLoading ? (
          <TypingIndicator label={msg.content} />
        ) : (
          <div className="markdown">
            <ReactMarkdown components={markdownComponents} remarkPlugins={[remarkGfm]}>
              {msg.content}
            </ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  )
}
