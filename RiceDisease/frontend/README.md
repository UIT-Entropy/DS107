# RiceCare AI Frontend

React + Vite frontend for the DS107 RiceCare web app.

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

```powershell
npm run dev
```

Default backend URL:

```text
http://localhost:8000
```

Override with:

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
