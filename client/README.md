# Helios AI - React Frontend

This directory will contain the React + TypeScript frontend built with Loveable.

## Backend API

The backend API contract is documented in `/server/API_CONTRACT.md`.

## Development Setup

**Prerequisites:**
- Node.js 18+ installed
- Backend running on `http://localhost:5000`

**Environment Variables:**

Create `.env.development`:
```bash
VITE_API_URL=http://localhost:5000
```

Create `.env.production`:
```bash
VITE_API_URL=http://YOUR_VULTR_IP:8080
```

## Running the Frontend

```bash
npm install
npm run dev
```

The app will run on `http://localhost:5173` (or `http://localhost:3000` depending on the setup).

## API Integration

All API endpoints and WebSocket events are documented in:
- `/server/API_CONTRACT.md`

The backend supports CORS for local development on ports 3000 and 5173.

## Build for Production

```bash
npm run build
npm install -g serve
serve -s dist -l 80
```

---

**Status:** Ready for Loveable development
