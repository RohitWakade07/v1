# Secure Academic Grading Platform - Student Portal

React + TypeScript student portal for Phase 1 backend APIs.

## Requirements
- Node.js 20+
- npm 9+

## Setup
1. Install dependencies:
   ```bash
   npm install
   ```
2. Configure environment variables (optional):
   - `VITE_API_BASE_URL` (default: `/api/v1`)

Create a `.env` file in the project root if needed:
```
VITE_API_BASE_URL=/api/v1
```

## Development
```bash
npm run dev
```

## Build
```bash
npm run build
```

## Preview
```bash
npm run preview
```

## Notes
- The frontend is presentation-only. All verification and scoring remain server-side.
- Certificate download is disabled until Phase 2 backend support is available.
