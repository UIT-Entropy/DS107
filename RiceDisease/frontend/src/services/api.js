export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000"

async function readJson(response) {
  const data = await response.json().catch(() => ({}))

  if (!response.ok || data.success === false) {
    throw new Error(data.error || `Server error ${response.status}`)
  }

  return data
}

export async function askAdvisor({ question, sessionId, mode, models }) {
  const response = await fetch(`${API_BASE_URL}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      question,
      session_id: sessionId,
      mode,
      models,
    }),
  })

  return readJson(response)
}

export async function predictImages(files) {
  const formData = new FormData()
  files.forEach((file) => formData.append("files", file))

  const response = await fetch(`${API_BASE_URL}/predict-multiple`, {
    method: "POST",
    body: formData,
  })

  return readJson(response)
}
