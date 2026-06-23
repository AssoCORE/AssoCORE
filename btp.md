# BETA TEST PLAN: ALL-IN-ONE MANAGEMENT PLATFORM

## 1. Project Context

This platform is an integrated management solution designed to centralize administrative tasks, professional communication, and productivity tools. It facilitates organization management through cloud storage, event planning, financial tracking (Stripe), and collaborative tools like Kanbans and messaging, accessible via both web and mobile interfaces.

---

## 2. User Roles

The following roles are involved in the beta testing process:

| Role Name | Description |
| :--- | :--- |
| **Admin** | Manages organization settings, billing, member privileges, events, and global inventory. |
| **Member** | Regular user with access to messaging, personal cloud storage, and collaborative tools. |
| **Guest** | Public user with read-only access to the "Site Vitrine" (Showcase site). |

---

## 3. Feature Table

All listed features are mapped to their respective development milestones.

| Feature ID | Milestone | User Role | Feature Name | Short Functional Description |
| :--- | :--- | :--- | :--- | :--- |
| **F1** | Step 1 | Everyone | **Auth & RBAC** | Login/Logout with role-based permission management. |
| **F2** | Step 1 | Everyone | **Cloud Storage** | Upload, download, and manage files in a cloud explorer. |
| **F3** | Step 1 | Admin | **Event Management** | Create and manage calendar events with categories. |
| **F4** | Step 1 | Admin | **Attendance** | Track member presence and "check-ins" for events. |
| **F5** | Step 2 | Admin | **Newsletter** | Bulk email engine for organizational announcements. |
| **F6** | Step 2 | Member | **Messaging** | Real-time chat (direct & group) between members. |
| **F7** | Step 2 | Everyone | **File Viewer** | In-app preview for spreadsheets (Tableur) and PDFs. |
| **F8** | Step 2 | Everyone | **Polls/Sondages** | Create and vote in polls with live result updates. |
| **F9** | Step 2 | Everyone | **Activity Feed** | Social-style post feed on the main dashboard. |
| **F10** | Step 3 | Admin | **Invoicing** | Automated PDF invoice generation for member dues. |
| **F11** | Step 3 | Member | **Stripe Payment** | Secure online checkout for invoices and services. |
| **F12** | Step 3 | Admin | **Expense Tracker** | Log and categorize organizational spending/outgoings. |
| **F13** | Step 3 | Admin | **Inventory** | Manage physical/digital stock levels and alerts. |
| **F14** | Step 4 | Guest | **Site Vitrine** | Public-facing landing page for external visitors. |
| **F15** | Step 4 | Member | **Meeting Minutes** | Create and archive "Compte rendu" meeting notes. |
| **F16** | Step 4 | Member | **Personal Notes** | Private scratchpad/note system for individual users. |
| **F17** | Step 4 | Everyone | **Kanban Board** | Visual task management with Drag & Drop columns. |
| **F18** | Step 4 | Admin | **Org Chart** | Visual hierarchy (Organigramme) of all members. |
| **F19** | Step 4 | Admin | **KPI Dashboard** | Data visualization (graphs) for financial/growth health. |
| **F20** | Step 4 | Everyone | **Themes & UI** | Toggle between Dark/Light modes and system accents. |
| **F21** | Step 5 | Everyone | **Mobile App** | Access via PWA/Mobile port with responsive layout. |
| **F22** | Step 5 | Everyone | **Localization** | Multi-language support (FR/EN) across the UI. |
| **F23** | Step 5 | Member | **Room Booking** | Reservation system for physical rooms or equipment. |
| **F24** | Step 5 | Member | **Privacy Control** | Toggle visibility of personal info to other members. |

---

## 4. Success Criteria

The following metrics define a successful beta test for each module.

| Feature ID | Milestone | Key Success Criteria | Indicator/Metric | Result |
| :--- | :--- | :--- | :--- | :--- |
| **F1** | Step 1 | Secure login with role-based access control (Admin/Member). | 50 logins; 0 unauthorized access to Admin panels. | **TBD** |
| **F2** | Step 1 | Cloud storage allows upload/download without data corruption. | 20 files (up to 100MB); 100% data integrity. | **TBD** |
| **F3** | Step 1 | Event creation and calendar synchronization. | 10 events created; visible to all targeted members. | **TBD** |
| **F4** | Step 1 | Presence manager accurately logs member check-ins. | 20 "check-ins" recorded; 0 data loss in DB. | **TBD** |
| **F5** | Step 2 | Newsletter/Email dispatch reaches external inboxes. | 100 emails sent; < 5% bounce rate. | **TBD** |
| **F6** | Step 2 | Messaging (Chat) delivers messages in real-time. | Average latency < 800ms over 50 test messages. | **TBD** |
| **F7** | Step 2 | Spreadsheet/Viewer opens standard .xlsx and .pdf files. | 10 different files; 0 rendering crashes. | **TBD** |
| **F8** | Step 2 | Poll results update instantly for all participants. | 10 votes cast; UI updates via sockets without refresh. | **TBD** |
| **F9** | Step 2 | Activity feed posts appear for all members instantly. | 15 posts; 100% visibility for logged-in users. | **TBD** |
| **F10** | Step 3 | Automated PDF invoice generation with correct data. | 15 invoices; 0 calculation errors vs. user dues. | **TBD** |
| **F11** | Step 3 | Stripe payment session completes and updates DB status. | 20 test payments; 20 "Paid" status updates in-app. | **TBD** |
| **F12** | Step 3 | Expense tracking accurately reflects organization budget. | 10 expenses logged; total balance matches manual calc. | **TBD** |
| **F13** | Step 3 | Inventory stock levels decrease by exactly 1 per action. | 30 "withdrawals"; stock count matches exactly. | **TBD** |
| **F14** | Step 4 | Site Vitrine is accessible to guests without login. | 5 external URL pings; 100% uptime; 0 login prompts. | **TBD** |
| **F15** | Step 4 | Meeting minutes are stored and searchable by date. | 10 documents created; 100% retrieval success. | **TBD** |
| **F16** | Step 4 | Personal notes remain private to the specific user. | 5 "Note" checks; 0 cross-user visibility leaks. | **TBD** |
| **F17** | Step 4 | Kanban cards persist their state after page refresh. | 50 drag-and-drops; 0 "reset" to original column. | **TBD** |
| **F18** | Step 4 | Org Chart displays correct hierarchy of current members. | 20 members; 100% accuracy in visual tree. | **TBD** |
| **F19** | Step 4 | KPI graphs reflect real-time database values. | 5 chart types; 100% match with manual DB counts. | **TBD** |
| **F20** | Step 4 | Theme system (Dark/Light) applies to all sub-pages. | 10 pages tested; 0 "white flashes" in dark mode. | **TBD** |
| **F21** | Step 5 | Mobile portage maintains full functionality (PWA). | 10 core tasks on iOS/Android; 0 UI blockers. | **TBD** |
| **F22** | Step 5 | Language toggle updates 100% of hardcoded strings. | 3 languages tested; 0 untranslated fragments. | **TBD** |
| **F23** | Step 5 | Room booking prevents double-booking the same slot. | 5 collision attempts; 5 successful rejections. | **TBD** |
| **F24** | Step 5 | Privacy settings mask personal data from non-admins. | 5 "Hidden" profiles; 0 unauthorized data visibility. | **TBD** |
