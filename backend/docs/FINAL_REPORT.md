**Final Project Report**

**Project:** Service Provider Platform

**Team:** One from each group — final submission

---

**1. Proposed and Completed Functional Requirements**
- **Proposed:**
  - Admin panel (login, dashboard, user/business/booking/category management).
  - User registration/login (email/phone verification), business owner flows, booking creation.
  - Public service listing and search UI.
- **Completed:**
  - Admin blueprint and pages: dashboard, users, businesses, bookings, categories (see UI in `frontend/admin/*`).
  - Role-based routing and guards for customers and business owners.
  - Email/phone verification strategies for registration.

**Examples**
- UI reference: `frontend/admin/dashboard.html` (admin dashboard and sidebar).
- Route/controller reference: `backend/views/admin.py` ([backend/views/admin.py](backend/views/admin.py#L13)).

**Snippet (admin route decorator)**
```python
# backend/patterns/decorator_auth.py (excerpt)
from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user

def admin_required(f):
    @wraps(f)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please log in first.", "warning")
            return redirect(url_for('auth.login'))
        if not hasattr(current_user, 'role') or current_user.role != 'admin':
            flash("Access denied. Only administrators can access this page.", "danger")
            return redirect(url_for('home.index'))
        return f(*args, **kwargs)
    return decorated_view
```

---

**2. Proposed and Completed Non-Functional Requirements**
- **Proposed:**
  - Single shared DB connection for efficiency; protect admin endpoints; reasonable page load times.
  - Session-based auth and CSRF protection (recommended).
- **Completed:**
  - Singleton DB connection implemented to avoid repeated connections.
  - Basic session-based admin login (dev mode: hardcoded admin credentials).
  - Role-based in-template checks to reduce accidental UI exposure.

**Examples**
- DB Singleton: `backend/database/singleton_db.py` ([backend/database/singleton_db.py](backend/database/singleton_db.py#L1))

**Snippet (DB singleton)**
```python
# backend/database/singleton_db.py (excerpt)
class SingletonDB:
    _instance = None
    _lock = threading.Lock()
    _initialized = False
    _connection = None

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(SingletonDB, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if SingletonDB._initialized:
            return
        # connect to MongoDB and mark initialized
```

**Notes on non-functional gaps**
- Admin uses hardcoded credentials (`backend/views/admin.py`) — replace with DB-backed hashed password for production.
- CSRF protection and audit logging are recommended improvements.

**Expanded Non-Functional Requirements**

- **Security**
  - Proposed: Use strong password hashing (bcrypt/argon2), HTTPS-only cookies, CSRF protection, input validation and output encoding, rate limiting on authentication endpoints, and encryption at rest for sensitive data.
  - Completed: Session-based auth present; recommend upgrading to DB-backed admin users and add `flask_wtf.CSRFProtect` and password hashing.

  Snippet (bcrypt usage recommendation):
  ```python
  from werkzeug.security import generate_password_hash, check_password_hash

  # storing a password
  hashed = generate_password_hash(plain_password, method='pbkdf2:sha256', salt_length=16)

  # checking a password
  check_password_hash(hashed, candidate_password)
  ```

- **Performance & Scalability**
  - Proposed: Keep average response times < 300ms for common endpoints under expected load; add caching (Redis) for hot read endpoints (category lists, business listings); enable database connection pooling and indexes on frequently queried fields.
  - Completed: Singleton DB reduces connection churn; recommended: add query indexes and introduce a caching layer for lists.

- **Reliability & Availability**
  - Proposed: Regular backups for the database, health-check endpoints, monitoring and alerts (Prometheus/Grafana), and graceful degradation for non-critical features (e.g., queue notifications when mail service is down).
  - Completed: Basic app runs; recommend adding health endpoints and scheduled DB backups.

- **Maintainability & Observability**
  - Proposed: Structured logging (JSON logs), request/response tracing (correlation IDs), comprehensive unit and integration tests, and clear module boundaries (patterns already help).
  - Completed: Patterns (Decorator, Strategy, Proxy, Singleton) organize code; recommend adding centralized logging and automated tests.

  Snippet (Flask CSRF protection):
  ```python
  # app.py
  from flask_wtf import CSRFProtect
  csrf = CSRFProtect()
  csrf.init_app(app)
  ```

- **Deployability & Config**
  - Proposed: Use environment-based configuration, 12-factor app practices, containerize (Docker) for consistent deployments, and provide a minimal `docker-compose` for dev and production manifests.
  - Completed: Config patterns present (`backend/config.py`); recommend creating Docker manifests and CI/CD pipelines.

- **Privacy & Data Retention**
  - Proposed: Define retention policies for user data, anonymize or delete test data, and implement export/delete endpoints for GDPR/CCPA compliance if needed.

- **Accessibility & Internationalization**
  - Proposed: Ensure UI templates follow WCAG basics, provide i18n support for strings, and test with screen readers for critical admin pages.

These expanded non-functional requirements should be tracked and prioritized for production readiness; I can help implement specific items (CSRF, password hashing, Dockerization, caching, or monitoring) on request.

---

**3. Design Patterns Implemented**
- **Decorator Pattern** — route guards and authorization checks.
  - Location: `backend/patterns/decorator_auth.py` ([backend/patterns/decorator_auth.py](backend/patterns/decorator_auth.py#L1)).
  - Snippet: see `admin_required` above.

- **Proxy Pattern** — centralized access decisions (redirect business owners from public home).
  - Location: `backend/patterns/proxy_access.py` ([backend/patterns/proxy_access.py](backend/patterns/proxy_access.py#L1)).
  - Snippet (core idea):
```python
class AccessProxy:
    def __init__(self, user):
        self.user = user
    def can_access_public_home(self):
        if not getattr(self.user, 'is_authenticated', False):
            return True
        return getattr(self.user, 'role', None) != 'business_owner'
```

- **Strategy Pattern** — verification/login strategies (email vs phone, captcha)
  - Location: `backend/patterns/auth_strategy.py` ([backend/patterns/auth_strategy.py](backend/patterns/auth_strategy.py#L1)).
  - Snippet:
```python
class VerificationStrategy(ABC):
    def send_verification(self, contact, user_data=None):
        pass

class EmailVerificationStrategy(VerificationStrategy):
    def send_verification(self, contact, user_data=None):
        code = generate_verification_code()
        send_verification_email(contact, code)
        session['reg_code'] = code
        return code
```

- **Singleton Pattern** — DB connection (see snippet above).

- **Factory / Observer / Builder** — present in `backend/patterns/*` to build domain objects and decouple creation; used in business/category factories and booking observers for notification flows.

---

**4. Class & Sequence Diagram Mapping**
- **Class Diagram (conceptual mapping)**
  - `User` (models/user.py) — attributes: `user_id`, `name`, `email`, `phone`, `role`, `is_active`.
  - `Business` (models/business.py) — attributes: `business_id`, `owner_id`, services list, active flag.
  - `Booking` (models/booking.py) — `booking_id`, `customer_id`, `business_id`, `status`.

**Snippet (`User` model example)**
```python
# backend/models/user.py (excerpt)
class User(Document):
    user_id = StringField(required=True)
    name = StringField()
    email = EmailField()
    phone = StringField()
    role = StringField(choices=['customer','business_owner','admin'])
```

- **Sequence Diagram (booking flow → implemented)**
  - Actor: Customer
  - Steps implemented:
    1. Customer selects service (frontend UI `frontend/business/services.html`).
    2. Booking POST → controller/view `backend/views/booking.py` or `backend/controllers/booking_controller.py` creates `Booking` record and triggers observers (notifications).
    3. Booking stored in DB (uses `SingletonDB` connection).
    4. Business owner and customer receive notifications (observer pattern).

**If diagram differs from code**
- The implemented code uses observer pattern for booking notifications; if original diagram showed synchronous email sends, we changed to observer notifications to decouple responsibilities.
- The admin auth was originally planned as DB-backed; currently a dev-mode admin login was used — update diagram to show `AdminSession` backed by `session['admin_logged_in']` until DB-based admin is implemented.

---

**References (key files)**
- Admin views: [backend/views/admin.py](backend/views/admin.py#L13)
- Decorators: [backend/patterns/decorator_auth.py](backend/patterns/decorator_auth.py#L1)
- Strategy: [backend/patterns/auth_strategy.py](backend/patterns/auth_strategy.py#L1)
- Proxy: [backend/patterns/proxy_access.py](backend/patterns/proxy_access.py#L1)
- Singleton DB: [backend/database/singleton_db.py](backend/database/singleton_db.py#L1)
- Models: [backend/models/user.py](backend/models/user.py#L1), [backend/models/business.py](backend/models/business.py#L1), [backend/models/booking.py](backend/models/booking.py#L1)

---

**Next steps / Improvements (suggested for final delivery)**
- Replace hardcoded admin login with DB-backed admin user and hashed password.
- Add CSRF protection for admin POST endpoints and enable HTTPS.
- Add an `audit_log` model and log admin actions (category deletes, booking status changes).
- Produce formal UML diagrams (class + sequence) and attach PNG/SVG in `docs/`.

---

If you want, I can:
- Generate the UML class and sequence diagrams (PlantUML) and add them to `backend/docs/`, or
- Replace the admin hardcoded login with a DB-backed implementation now.

