# Admin Interface — Overview

This document describes how the Admin interface works in this project: routes and pages, roles and permissions, access controls, and the design patterns used to implement admin functionality.

---

## 1. Summary

- The Admin interface is a separate Flask Blueprint mounted at `/admin` and uses its own login flow (default/hardcoded credentials: `admin` / `admin123`).
- Admin pages are rendered from `frontend/admin/*.html` and include dashboard, users, businesses, bookings, and categories management.
- Admin actions are guarded by route-level checks (session-based and role-based decorators).

## 2. Key Admin Routes & Pages

- `/admin/login` — Admin login page and POST handler.
- `/admin/logout` — Clear admin session and redirect to login.
- `/admin/dashboard` — Admin statistics and recent records view.
- `/admin/users` and `/admin/users/<user_id>` — List and detail user views. Toggle user active status.
- `/admin/businesses` and `/admin/businesses/<id>` — Business list and detail (view owner, toggle status).
- `/admin/bookings` and `/admin/bookings/<id>` — Booking list and detail with limited status updates (Completed/Cancelled).
- `/admin/categories` — Create / edit / delete DB-backed categories.

(See templates in `frontend/admin/` for the exact UI and form actions.)

## 3. Roles & Permissions

Roles used in the app (user model `role` field):
- `admin` — Full administrative access to manage users, businesses, bookings, categories (with some product rules).
- `business_owner` — Owner-specific access for managing their business and services.
- `customer` — End-user who can browse and create bookings.

Admin specifics and policies:
- Admin session is tracked separately via `session['admin_logged_in']` for the admin blueprint.
- Admins cannot create businesses via the admin UI (intentionally blocked by policy/UI).
- Admins can set booking status only to `Completed` or `Cancelled` (limited update surface).
- Categories created by admin are DB-backed and manageable from the admin UI.

## 4. Access Control Implementation

- Admin blueprint provides a lightweight admin authentication using `session['admin_logged_in']` and an `admin_required` decorator for its routes.
- Application-level role-based decorators live in `backend/patterns/decorator_auth.py` and enforce role checks via `flask_login.current_user.role` for regular user routes.
- Some routes and templates also check `current_user.role` inline to conditionally allow views/actions for admins.

Security notes:
- The current admin login uses hardcoded credentials (convenience for dev). Replace with a proper admin user stored in the DB and hashed password for production.
- Role checks depend on `current_user.role` and the presence of `current_user.is_authenticated`. Ensure the `User` model and login flow always populate these fields correctly.

## 5. Design Patterns Initialized / Used

- Decorator Pattern
  - Used for route guards and authorization checks (`admin_required`, `business_owner_required`, `customer_required`) in `backend/patterns/decorator_auth.py`.

- Proxy Pattern
  - Implemented as `AccessProxy` in `backend/patterns/proxy_access.py` to centralize page-access decisions (e.g., redirecting business owners away from the public landing page).

- Strategy Pattern
  - Authentication/verification strategies live in `backend/patterns/auth_strategy.py` (email vs phone verification, captcha login strategies). This separates verification logic from callers.

- Singleton Pattern
  - Database connection uses a Singleton (`backend/database/singleton_db.py`) so the app shares a single MongoDB connection across modules.

- Factory / Builder / Observer (Project patterns)
  - The repository also includes factories and builders for domain objects (e.g., business/category factories) and observer patterns used in auth/booking flows. These patterns help separate construction and cross-cutting responsibilities.

## 6. Implementation Notes & References

- Admin blueprint implementation: [backend/views/admin.py](backend/views/admin.py#L13)
- Role-based decorators: [backend/patterns/decorator_auth.py](backend/patterns/decorator_auth.py#L1)
- Access proxy: [backend/patterns/proxy_access.py](backend/patterns/proxy_access.py#L1)
- Auth/verification strategies: [backend/patterns/auth_strategy.py](backend/patterns/auth_strategy.py#L1)
- Database singleton: [backend/database/singleton_db.py](backend/database/singleton_db.py#L1)
- Admin templates: [frontend/admin/dashboard.html](frontend/admin/dashboard.html#L6) (see other files in that folder for users/bookings/categories UIs)

## 7. Suggested Improvements

- Replace hardcoded admin credentials with a secure admin account stored in the database and use hashed passwords (bcrypt/argon2).
- Move admin login to the same auth system or implement an `Admin` model with roles/permissions and audited actions.
- Add CSRF protection for admin POST endpoints (Flask-WTF or `flask_wtf.csrf.CSRFProtect`).
- Tighten access checks by combining session checks with `current_user.role` where appropriate to avoid bypasses.
- Add audit logging for admin actions (category deletes, booking status changes, user toggles).

---

If you'd like, I can:
- Replace the hardcoded admin login with DB-backed admin user flow, or
- Add CSRF + audit logging scaffolding for admin actions.

