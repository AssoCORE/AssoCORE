# ROADMAP

Feature milestones from the Beta Test Plan. Each feature maps to a test ID (F1–F24).

---

## Step 1 — Foundation

| ID | Feature | Backend | Frontend | Status |
|----|---------|---------|----------|--------|
| F1 | **Auth & RBAC** | ✅ JWT login, bcrypt, full user/notification/reminder CRUD, `get_current_user` dep | Login page, token storage, protected routes | In progress |
| F2 | **Cloud Storage** | Nextcloud admin routes functional; per-user proxy stubs | File explorer UI | In progress |
| F3 | **Event Management** | Models & schemas defined; route handlers stubbed | Calendar UI | Not started |
| F4 | **Attendance** | — | — | Not started |

## Step 2 — Communication

| ID | Feature | Notes |
|----|---------|-------|
| F5 | **Newsletter** | Bulk email engine (SMTP integration) |
| F6 | **Messaging** | Real-time chat — will require WebSocket support |
| F7 | **File Viewer** | In-app .xlsx / .pdf preview via Nextcloud proxy |
| F8 | **Polls** | Create & vote; live updates via WebSocket |
| F9 | **Activity Feed** | Post feed on the main dashboard |

## Step 3 — Finance

| ID | Feature | Notes |
|----|---------|-------|
| F10 | **Invoicing** | Automated PDF generation |
| F11 | **Stripe Payments** | Checkout for member dues |
| F12 | **Expense Tracker** | Log and categorize organizational spending |
| F13 | **Inventory** | Stock management with low-stock alerts |

## Step 4 — Advanced Tools

| ID | Feature | Notes |
|----|---------|-------|
| F14 | **Site Vitrine** | Public landing page, no login required |
| F15 | **Meeting Minutes** | Archived notes, searchable by date |
| F16 | **Personal Notes** | Private per-user scratchpad |
| F17 | **Kanban Board** | Drag & drop, persistent state |
| F18 | **Org Chart** | Visual member hierarchy |
| F19 | **KPI Dashboard** | Financial and growth charts |
| F20 | **Themes** | Dark / Light mode toggle |

## Step 5 — Mobile & International

| ID | Feature | Notes |
|----|---------|-------|
| F21 | **Mobile App** | Flutter + PWA responsive layout |
| F22 | **Localization** | FR / EN toggle across all UI strings |
| F23 | **Room Booking** | Reservation system, collision prevention |
| F24 | **Privacy Controls** | Per-user visibility settings |
