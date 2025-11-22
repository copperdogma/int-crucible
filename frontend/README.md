# Int Crucible Frontend

This is the Next.js frontend for Int Crucible, a general multi-agent reasoning system.

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Backend API running on http://127.0.0.1:8000 (or configure `NEXT_PUBLIC_API_URL`)

### Installation

```bash
# Install dependencies
npm install
```

### Configuration

Create a `.env.local` file (or use `.env.example` as a template):

```bash
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

### Development

```bash
# Start the development server
npm run dev
```

Open [http://localhost:3001](http://localhost:3001) in your browser.

### Build

```bash
# Build for production
npm run build

# Start production server
npm start
```

## Features

- **Project Management**: Create and select projects
- **Chat Interface**: Interactive chat with ProblemSpec/Architect agent
- **Live Spec Panel**: View and monitor ProblemSpec and WorldModel in real-time
- **Run Configuration**: Configure and start pipeline runs
- **Results View**: View ranked candidates with scores (P, R, I) and constraint flags

## Architecture

- **Framework**: Next.js 16 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State Management**: React Query (@tanstack/react-query) for server state
- **API Client**: Typed API client in `lib/api.ts`

## Project Structure

```
frontend/
├── app/              # Next.js app directory
│   ├── layout.tsx     # Root layout with providers
│   ├── page.tsx      # Main app page
│   └── providers.tsx # React Query provider
├── components/       # React components
│   ├── ProjectSelector.tsx
│   ├── ChatInterface.tsx
│   ├── SpecPanel.tsx
│   ├── RunConfigPanel.tsx
│   └── ResultsView.tsx
└── lib/             # Utilities
    └── api.ts       # API client
```
