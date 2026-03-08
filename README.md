# Service Provider Project (New Version)

## Overview
This platform connects customers with local service providers (cleaning, plumbing, electrical, etc.), allowing business owners to register, manage services, and accept bookings. Customers can browse, book, and review services. The platform includes a comprehensive admin dashboard for managing users, businesses, bookings, and service categories.

## Architecture
- **Backend:** Flask + MongoEngine (MongoDB)
- **Frontend:** Jinja2 templates rendered by Flask (Bootstrap-based UI)
- **Images:** Cloudinary (Adapter pattern)
- **Auth:** Flask-Login with role-based access control; registration via email/phone verification; login with captcha
- **Security:** Session invalidation on restart, double-slash path normalization, business owner access gating via Proxy pattern, HttpOnly/SameSite cookies
- **Patterns:** Factory, Command, Observer, Adapter, Decorator, Proxy, Repository

## File Structure

**backend/** – Python Flask backend
	- `app.py`: Main Flask app, registers blueprints, sets up login and DB, session restart enforcement, path canonicalization
	- `config.py`: Singleton config loader (env vars, secrets)
	- `.env`: Environment variables (MongoDB, Cloudinary, secret keys)
	- `requirements.txt`: Python dependencies
	- `controllers/`: Business logic for users, bookings, businesses
	- `models/`: MongoEngine models for User, Business, Booking, Category (new), Service
	- `database/`: DB connection (singleton pattern)
	- `patterns/`: Design patterns (Factory, Command, Observer, Adapter, Decorator, Proxy, Repository)
	- `views/`: Flask blueprints for routing (home, auth, booking, admin, owner_business, business)
	- `utils.py`: Utility functions (Cloudinary uploads, email/SMS, validators)

**frontend/** – HTML templates (Bootstrap, Jinja2)
	- `base.html`: Main layout, navbar, styles
	- `home.html`, `dashboard.html`, `profile.html`, `services.html`, `category_list.html`: Main pages
	- `Auth/`, `admin/`, `business/`, `owner/`, `Home/`: Subfolders for role-based pages

## Backend Architecture
- **Flask** app with modular blueprints for each feature
- **MongoDB** via MongoEngine ODM
- **Entities:**
	- `User`: Customer, business owner, admin (role-based)
	- `Business`: Service provider, can have owner (user or external), profile, gallery, category
	- `Booking`: Connects customer, business, service; tracks status, timestamps
	- `Service`: Embedded in Business (name, duration, price, is_active)
- **API Endpoints:**
	The app uses server-rendered pages with form posts. Core routes include:
	- Auth:
		- `GET /login` → Login page with captcha
		- `POST /login` → Login via identifier (email/phone) + password; includes "Login as" (Customer or Business Owner) to choose destination
		- `GET|POST /register` → Register user; supports roles and email/phone verification (no captcha)
		- `GET|POST /verify_register` → Verify code (email/phone)
		- `GET|POST /forgot` → Request password reset code
		- `GET|POST /reset` → Reset password with code
		- `GET /logout` → Logout
	- Home:
		- `GET /` and `GET /home` → Landing page with categories and featured businesses
		- `GET /services` → Browse services with filters (`category`, `city`, `q`)
		- `GET /category/<category>` → Businesses by category
		- `GET /my-bookings` (auth) → Active and completed bookings
		- `GET /dashboard` (auth) → User dashboard
		- `GET /profile` (auth) → Profile view (lazy-loaded images)
	- Business:
		- `GET|POST /business/create` (owner) → Create business with profile/gallery images
		- `GET /business/<id>` → Business details + services
		- `GET|POST /business/<id>/update` (owner) → Update business
		- `POST /business/<id>/deactivate` (owner) → Deactivate business
		- `POST /business/<id>/gallery/delete` (owner) → Delete gallery image
		- `GET /business/<id>/services` → List services
		- `GET|POST /business/<id>/services/create` (owner) → Create service
	- Booking:
		- Controller functions handle `create`, `accept`, `reject`, `cancel`, `complete` via Command pattern; routes typically in `views/booking.py`.
		- `/admin/bookings` → List all bookings with customer and owner names (enriched)
		- `/admin/bookings/<booking_id>` → Booking details with status update (admin-only)
		- `/admin/bookings/<booking_id>/update-status` (POST) → Update booking (Completed or Cancelled only)
	- Admin Management:
		- `/admin/login` → Hardcoded admin login (admin/admin123)
		- `/admin/dashboard` → Statistics: users, businesses, bookings; recent bookings with names
		- `/admin/users` → List users with search; shows roles and status badges
		- `/admin/users/<user_id>` → User details, bookings, businesses owned
		- `/admin/businesses` → List businesses with owner names; filter by category
		- `/admin/businesses/<id>` → Business details and bookings
		- `/admin/bookings` → All bookings (filtered by status) with customer and owner enrichment
		- `/admin/bookings/<id>` → Booking details; admin can set status (Completed/Cancelled only)
		- `/admin/categories` → Manage service categories (create, edit, delete DB-backed; built-ins not editable)
		- `/admin/categories/create` (POST) → Create new category
		- `/admin/categories/<name>/edit` (POST) → Update category metadata (display_name, icon, description, tags)
		- `/admin/categories/<name>/delete` (POST) → Delete category (if unused)

- **Patterns:**
	- **Factory:** CategoryFactory merges DB-backed and built-in categories; used for category dropdowns, home carousel, services filter.
	- **Repository:** CategoryModel (MongoDB) persists admin-created categories; CategoryFactory reads from both DB and built-ins.
	- **Proxy:** AccessProxy gates business owners away from public home; early role check in app.before_request.
	- **Command:** Encapsulates booking actions (create, accept, reject, cancel, complete); supports queue and retry.
	- **Observer:** Notifies users on booking status changes (email/SMS).
	- **Adapter:** Cloudinary integration for image uploads; CloudinaryAdapter provides get_url, upload, delete, get_thumbnail_url.
	- **Decorator:** Role-based route protection (@admin_required, @owner_required, etc.) and auth guards.

## Frontend Structure
- **Templates:** Bootstrap 5-based, responsive, Jinja2 for dynamic content, lazy-loading images with Cloudinary transforms
- **Pages:** 
	- Landing: home.html (public), category carousel with infinite auto-scroll
	- Services: services.html (filters by category, city, business name)
	- Categories: category_list.html (businesses per category with progressive lazy images)
	- Business: business_detail.html, business/gallery.html
	- Auth: Auth/login.html, Auth/register.html, Auth/verify.html, Auth/forgot.html, Auth/reset.html
	- Dashboard: dashboard.html (role-specific content), my_bookings.html
	- Profile: profile.html (role-aware nav; owner sees Dashboard/My Business; customer sees Home)
	- Admin: admin/*.html (dashboard, users, user_detail, businesses, bookings, booking_detail, categories)
	- Owner: owner/*.html (dashboard, create_business, update_business, gallery, bookings, services)
- **Role-based views:** Auth (login/register), admin (full control), business_owner (business/gallery/services), customer (browse/book)

## Environment & Configuration
- `.env` stores secrets, DB URI, Cloudinary keys
- `config.py` loads and validates env vars (singleton)
- `requirements.txt` pins all dependencies for reproducible setup

### Required Environment Variables
- `SECRET_KEY`: Flask session/signing key (required)
- `MONGO_URI`: MongoDB connection string
- `DB_NAME`: Mongo database name
- `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`: Image storage
- `DEBUG`: Optional toggle for dev

## Design Patterns
- See `DESIGN_PATTERNS_GUIDE.md` for details on Factory, Command, Observer, Adapter implementations

### Pattern Implementations
- **Factory:** `backend/patterns/factory_business.py` creates typed businesses with defaults; `factory_category.py` manages categories (8 built-in + DB-backed); `factory_service.py` generates service templates.
- **Repository:** `backend/models/category.py` (CategoryModel) persists categories; CategoryFactory consumes it via `_db_categories_map()`.
- **Proxy:** `backend/patterns/proxy_access.py` (AccessProxy) gates business owners from public home; used in `views/home.py` and `app.before_request`.
- **Command:** `backend/patterns/command_booking.py` wraps booking flows; supports undo/logging.
- **Observer:** `backend/patterns/observer_booking.py` sends notifications on status change.
- **Adapter:** `backend/patterns/cloudinary_adapter.py` normalizes Cloudinary operations; used by `utils.py`.
- **Decorator:** `backend/patterns/decorator_auth.py` for route-level role checks and messages.

## How to Run
1. Install Python 3.10+ and MongoDB
2. Copy `.env` and set secrets/keys
3. `pip install -r backend/requirements.txt`
4. Run backend: `python backend/app.py`
5. Access frontend via Flask (templates served from `frontend/`)

### Windows quickstart (PowerShell)
```powershell
cd x:\ServiceProvider
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
$env:FLASK_APP="backend/app.py"; python backend/app.py
```

### Development Notes
- Use `Flask-Login` for auth (`current_user`, `login_user`, `logout_user`).
- Registration codes are fixed to `12345` for both email and phone; codes are printed to the server console for testing.
- Login requires solving a simple captcha; registration does not use captcha.
- **Session restart behavior:** In `DEBUG` mode, the app appends a random suffix to SECRET_KEY on each startup, and stores a boot ID in the session. When the server restarts, the old boot ID is detected and sessions are cleared, forcing users to re-authenticate.
- **Path canonicalization:** `app.before_request` normalizes double slashes (`//` → `/`) and gates business owners away from public home (`/`, `/home` → dashboard or create business flow).
- MongoEngine models are in `backend/models`; queries via `.objects`.
- Images upload via Cloudinary; URLs stored on Business and transformed (lazy, full, thumbnail) via Cloudinary URLs.
- Server-side rendered templates live in `frontend/` and are referenced in views.
- **Admin policies:** Admin cannot create businesses (UI and route blocked); can only set bookings to Completed or Cancelled; can create/edit/delete service categories (DB-backed only).

## Data Model Cheatsheet
- **User:** `user_id`, `name`, `email`, `phone`, `role` (customer, business_owner, admin), `is_verified`, address fields, `profile_pic_url`, `is_active`, `created_at`.
- **Business:** `business_id`, `owner_id`, `owner_name` (fallback), `category`, `name`, `description`, `gallery_urls`, `profile_pic_url`, `is_active`, `created_at`, `services` (embedded list).
- **Booking:** `booking_id`, `business_id`, `service_id`, `customer_id`, `staff_id`, `status` (pending, accepted, rejected, completed, cancelled), `booking_time`, `created_at`, `updated_at`, `price`, `duration_minutes`, `notes`.
- **Service:** Embedded in Business; fields: `service_id`, `name`, `price`, `duration_minutes`, `is_active`.
- **Category (new):** `name` (unique slug), `display_name`, `description`, `icon` (emoji or Bootstrap suffix), `tags` (search list).

## Typical Flows
- Registration → email/phone verification (enter code `12345`) → login (captcha) → dashboard/home.
- Business owner creates business → uploads profile + gallery → adds services.
- Customer browses services → filters by category/city → views business → makes booking.
- Booking status changes trigger observer notifications.

## Role-Based Navigation
- **Customer:** After login, redirected to `home.index` (landing page); profile nav shows Home; can browse, search, and book services.
- **Business Owner:** After login, redirected to `owner_business.dashboard` (`/owner/dashboard`) when selecting "Login as: Business Owner"; if the account isn't a business owner, the app warns and redirects to home. Cannot access public home (`/`, `/home`) — automatically redirected to dashboard or create business. Profile nav shows Dashboard and My Business links.
- **Admin:** Separate login at `/admin/login` (hardcoded: admin/admin123); once logged in, redirected to `admin.dashboard`. Access to `/admin/*` routes for user, business, booking, and category management.

### Security Features
- **Session invalidation on restart:** Boot ID mechanism clears sessions when dev server restarts.
- **Path normalization:** Double slashes (`//`) are normalized to single slashes; no path traversal.
- **Role-based access gating:** Business owners blocked from public home via Proxy; early interception in `app.before_request` and route handlers.
- **Cookie hardening:** HttpOnly, SameSite=Lax (or Strict if needed), Secure in production.
- **Admin restrictions:** Cannot create businesses; can only set bookings to Completed/Cancelled; categories are create/edit/delete (DB-backed only).

### Admin Categories Management
- **Create:** Use the form at `/admin/categories` to add new categories (emoji or Bootstrap icons supported).
- **Edit:** DB-backed categories show an inline Edit form to update display_name, icon, description, tags.
- **Delete:** DB-backed categories can be deleted via Delete button if unused by any business.
- **Built-ins:** Core built-in categories (cleaning, plumbing, electrical, etc.) are not stored in DB and cannot be edited/deleted; they show a "Built-in category (not editable)" note.

## Contributing
See business owner guides and implementation docs for details on extending features and patterns.
