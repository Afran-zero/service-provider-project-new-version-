"""Proxy Pattern for access control and route gating.

AccessProxy centralizes logic deciding whether a user can access certain public
pages (e.g., home landing) based on role and contextual ownership state.

Using a proxy instead of scattering conditional checks across routes provides:
- Single responsibility for access decisions
- Easier extension (add more rules: subscription tiers, feature flags, etc.)
- Clear separation between presentation and access enforcement

Pattern Participants:
- Subject (original route handler): The underlying function generating content
- Proxy (AccessProxy): Intercepts call, performs role/security checks, may redirect

Current Rules Implemented:
- Business owners are redirected away from public home pages to their dashboard
  or business creation flow depending on whether they have a business.
"""
from flask import redirect, url_for
from flask_login import current_user
from models.business import Business

class AccessProxy:
    def __init__(self, user):
        self.user = user

    def can_access_public_home(self) -> bool:
        """Business owners should not view generic marketing homepage.
        Regular customers and anonymous visitors may.
        """
        if not getattr(self.user, 'is_authenticated', False):
            return True
        role = getattr(self.user, 'role', None)
        return role != 'business_owner'

    def destination_for_owner(self):
        """Determine where to send a business owner when blocking home access."""
        if not getattr(self.user, 'is_authenticated', False):
            return url_for('home.index')
        # Does owner have a business? If yes go to dashboard; else create business.
        business = Business.objects(owner_id=self.user.user_id).first()
        if business:
            return url_for('owner_business.dashboard')
        return url_for('owner_business.create_business')

    def render_or_redirect_home(self, original_handler):
        """Invoke original home handler or redirect based on access policy."""
        if self.can_access_public_home():
            return original_handler()
        return redirect(self.destination_for_owner())
