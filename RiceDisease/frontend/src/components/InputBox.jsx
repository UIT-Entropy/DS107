import { useState } from "react"

export default function InputBox({ onSend }) {
  const [text, setText] = useState("")

  const send = () => {
    if (!text.trim()) return
    onSend(text)
    setText("")
  }

  return (
    <div className="border-t border-white/10 bg-[#0b0f14] p-4">
      <div className="flex items-end gap-2">
        <textarea
          className="flex-1 resize-none rounded-xl bg-[#111827] p-3 text-sm outline-none"
          onChange={(event) => setText(event.target.value)}
          placeholder="Message..."
          rows={1}
          value={text}
        />

        <button
          className="rounded-xl bg-green-600 px-4 py-2 hover:bg-green-500"
          onClick={send}
          type="button"
        >
          Send
        </button>
      </div>
    </div>
  )
}
