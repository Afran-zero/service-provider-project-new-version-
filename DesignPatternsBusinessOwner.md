# Design Patterns in Service Provider System

This document summarizes the key design patterns used across the Service Provider project, with where they are applied, the intent, and how they support maintainability and extensibility.

## Factory Pattern
- Purpose: Create different business categories/services through a unified interface without exposing instantiation logic to callers.
- Where: Business/service creation flows in `backend/controllers/business_controller.py` (e.g., creating `Service` entries per business). The category field and service creation act as a simple factory for constructing services with different parameters.
- Why: Decouples creation from usage, making it easier to add new service types/categories.

## Command Pattern
- Purpose: Encapsulate booking operations (create, update, cancel) as commands that can be executed, queued, or rolled back.
- Where: Booking flows in `backend/controllers/booking_controller.py` (e.g., create booking, update status). Each operation is invoked via controller functions acting as commands.
- Why: Standardizes booking actions, enabling future features like undo, batching, or audit trails.

## Observer Pattern
- Purpose: Notify interested components (e.g., user or owner notifications) when domain events occur, such as booking created or status changed.
- Where: App initialization in `backend/app.py` wires observers; booking controller triggers notifications on state changes.
- Why: Decouples event producers from consumers, enabling easy addition of new notification channels.

## Adapter Pattern (Cloudinary)
- Purpose: Provide a uniform interface for image operations regardless of Cloudinary’s API, hiding vendor-specific details.
- Where: `backend/utils.py` exposes helpers (`upload_image_to_cloudinary`, `get_cloudinary_url`, `get_cloudinary_thumbnail_url`), used by `backend/controllers/business_controller.py` and `backend/controllers/user_controller.py`.
- Why: Centralizes image upload/transformation logic, easing provider changes or configuration updates.

## Decorator Pattern (Role Guards)
- Purpose: Enforce access rules (owner-only routes) around view functions without changing their core logic.
- Where: Flask route guards (e.g., `@login_required`) and role checks inside views under `backend/views/owner_business.py` and `backend/views/business.py`. Public business view blocks booking when the viewer is the owner (`is_owner_viewing`).
- Why: Keeps authorization logic orthogonal to business logic and reusable across endpoints.

## Strategy Pattern (Image URL selection)
- Purpose: Select between multiple strategies for profile image resolution (business image vs. owner’s user image) and transformation (lazy vs. full).
- Where: `backend/controllers/business_controller.py#get_business_details` chooses source and transformations. When `Business.profile_pic_url` is missing, it falls back to the owner `User.profile_pic_url`. Generates `profile_pic_lazy` and `profile_pic_full` for progressive loading.
- Why: Cleanly switches behavior based on context while keeping a consistent output contract.

## Template/View Pattern
- Purpose: Separate presentation from logic using Jinja2 templates fed by view controllers.
- Where: `frontend/` templates with Flask views in `backend/views/*`. Owner public view (`frontend/business_detail.html`) hides booking UI when owner is viewing; owner business view (`frontend/owner/view_business.html`) uses progressive lazy loading for profile image.
- Why: Improves maintainability by decoupling UI from server-side logic.

## Context Processor
- Purpose: Inject global context (e.g., `owner_primary_business_id`) to templates like the navbar.
- Where: `backend/app.py` context processor.
- Why: Reduces duplication and ensures consistent navigation for business owners.

---

## Pattern-to-Code Map
- Factory: `backend/controllers/business_controller.py#create_service` builds `Service` domain objects.
- Command: `backend/controllers/booking_controller.py` methods for booking lifecycle.
- Observer: Event hooks in `backend/app.py` and booking events triggering notifications.
- Adapter: Cloudinary helpers in `backend/utils.py`, used by user/business controllers.
- Decorator: `@login_required` and role checks guarding `owner_business` and `business` routes; booking disabled for owners in public view.
- Strategy: Image selection/transforms in `get_business_details`.
- Template/View: Jinja templates under `frontend/` paired with Flask views under `backend/views/`.
- Context Processor: `inject_owner_business` in `backend/app.py`.

## UX/Navigation Rules (Owner-specific)
- Services Back button: returns to `owner_business.view_business` for the current business.
- Create Service Cancel: returns to `owner_business.view_business`.
- Navbar: hide `Home` for business owners; footer hides `Home` link for business owners.
- Public View: business owners cannot book their own services; UI shows owner message with link back to owner dashboard.

## Notes
- These patterns are applied pragmatically to match the project’s scale.
- As features grow (e.g., complex pricing or scheduling), Strategy and Factory can expand to dedicated classes.
- Observer can evolve into a message bus (e.g., via signals or an event queue) for scalability.
