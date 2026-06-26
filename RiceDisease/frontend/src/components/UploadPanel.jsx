import { useState } from "react"
import { predictImages } from "../services/api"

export default function UploadPanel({ onReceive }) {
  const [files, setFiles] = useState([])
  const [loading, setLoading] = useState(false)

  const handleUpload = async () => {
    if (!files.length) return
    setLoading(true)

    try {
      const data = await predictImages(files)
      const results = data.results || []
      const message = results
        .map((result, index) => {
          const confidence =
            typeof result.confidence === "number"
              ? `${(result.confidence * 100).toFixed(1)}%`
              : "unknown"

          return [
            `### Image ${index + 1}`,
            `- Prediction: **${result.disease || "No clear detection"}**`,
            `- Confidence: **${confidence}**`,
            result.image_url ? `\n![YOLO image](${result.image_url})` : "",
          ].join("\n")
        })
        .join("\n\n---\n\n")

      onReceive?.(message)
      setFiles([])
    } catch (error) {
      onReceive?.(`Could not upload image: ${error.message}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="border-b border-white/10 bg-[#171717] p-3">
      <div className="flex items-center gap-2">
        <label className="cursor-pointer rounded-lg bg-[#303030] px-3 py-2 text-sm text-[#ececec] hover:bg-[#3a3a3a]">
          Choose images
          <input
            accept="image/*"
            className="hidden"
            multiple
            onChange={(event) => setFiles(Array.from(event.target.files || []))}
            type="file"
          />
        </label>

        <button
          className="rounded-lg bg-[#ececec] px-3 py-2 text-sm text-[#212121] disabled:bg-[#414141] disabled:text-[#8f8f8f]"
          disabled={!files.length || loading}
          onClick={handleUpload}
          type="button"
        >
          {loading ? "Processing" : "Upload"}
        </button>
      </div>
    </div>
  )
}
