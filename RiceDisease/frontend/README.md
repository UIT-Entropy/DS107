# RiceCare AI Frontend

React + Vite frontend for the DS107 RiceCare web app.

For the complete backend + frontend demo flow, see `../README.md`.

The UI supports:

- Uploading one or more rice pest images.
- Displaying YOLO prediction results and annotated images.
- Reusing the backend-created advisor session for follow-up questions.
- Showing RAG answer sources returned by the backend.

## Setup

```powershell
npm install
```

## Development

Start the backend first:

```powershell
cd ..\backend
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Then start the frontend:

```powershell
npm run dev
```

Recommended explicit demo command:

```powershell
$env:VITE_API_BASE_URL="http://127.0.0.1:8000"
npm run dev -- --host 127.0.0.1 --port 5173
```

Open:

```text
http://127.0.0.1:5173
```

Default backend URL used by `src/services/api.js`:

```text
http://localhost:8000
```

Override it before starting Vite when the backend uses another host or port:

```powershell
$env:VITE_API_BASE_URL="http://localhost:8000"
npm run dev
```

## Build

```powershell
npm run build
```

If PowerShell blocks `npm.ps1`, use:

```powershell
npm.cmd run build
```

## Demo Notes

The expected live demo flow is:

1. Upload one or more rice pest images.
2. Show the YOLO prediction result and annotated image.
3. Ask a follow-up question in the same chat.
4. Show the RAG answer and returned sources.

Generated folders such as `node_modules/` and `dist/` should not be submitted.
