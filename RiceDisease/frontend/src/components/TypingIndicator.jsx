export default function TypingIndicator({ label = "Đang xử lý" }) {
  return (
    <div className="text-sm text-[var(--text-secondary)]">
      {label}...
    </div>
  )
}
