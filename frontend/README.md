# Amrutam Telemedicine Frontend

Modern, responsive telemedicine web application built with **React 18, Vite, Tailwind CSS, React Router, Recharts, and Lucide React**.

---

## Architectural Principles
- **Strict JavaScript / JSX**: Implemented cleanly using standard JavaScript (no TypeScript, no `.ts`/`.tsx` files).
- **Decoupled API Architecture**: Centralized Axios client (`src/api/axios.js`) with automated JWT token refresh queueing, session expiration listener, and `X-Request-ID` propagation.
- **Idempotent UI**: Client generates unique UUIDs for each booking operation, guaranteeing safe network retry without duplicate bookings.
- **Ayurvedic Clinical Design**: Amrutam-inspired herbal color palette (emerald greens, warm amber, clinical slate), accessible contrast, smooth transitions, and responsive mobile drawers.
- **Role-Based Views**: Dedicated portals for Patients (directory, booking modal, appointments, prescriptions), Doctors (clinical workspace, queue, prescription writer, schedule manager), and Administrators (telemetry, Recharts graphs, audit log inspector).

---

## Getting Started

### 1. Install Dependencies
```bash
# In frontend/ directory
npm install
```

### 2. Environment Configuration
Ensure `.env` contains:
```bash
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

### 3. Run Development Server
```bash
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

### 4. Run Automated Frontend Tests
```bash
npm test
```
Runs Vitest unit and integration tests verifying authentication form validation, doctor search controls, and error states.

### 5. Production Build
```bash
npm run build
```
Generates optimized static bundle in `dist/`.
