# Business Owner Implementation - Deployment Checklist

## Pre-Deployment Tasks

### Database Migration

- [ ] Backup existing MongoDB database
- [ ] Add role field to all existing users:
  ```javascript
  db.users.updateMany(
    { role: { $exists: false } },
    { $set: { role: "customer" } }
  );
  ```
- [ ] Verify role field is set for all users:
  ```javascript
  db.users.countDocuments({ role: { $exists: false } });
  // Should return 0
  ```

### Code Deployment

- [ ] Pull latest code
- [ ] Install/verify dependencies: `pip install -r requirements.txt`
- [ ] Run Python syntax check on modified files
- [ ] Test imports: `python -c "from views.owner_business import owner_business_bp"`

### Frontend Assets

- [ ] Verify Bootstrap 5 is available (for new templates)
- [ ] Verify Bootstrap Icons are available
- [ ] Test responsive design on mobile browsers

---

## Files to Review Before Deployment

| File                                     | Type       | Changes                   | Review                    |
| ---------------------------------------- | ---------- | ------------------------- | ------------------------- |
| `backend/models/user.py`                 | Model      | Added role field          | ✓ Check role choices      |
| `backend/patterns/decorator_auth.py`     | Pattern    | New decorators            | ✓ Check access control    |
| `backend/patterns/command_booking.py`    | Pattern    | Ownership verification    | ✓ Check authorization     |
| `backend/controllers/user_controller.py` | Controller | Role parameter            | ✓ Check default value     |
| `backend/views/auth.py`                  | View       | Role selection + redirect | ✓ Check redirection logic |
| `backend/views/owner_business.py`        | View       | New routes (NEW)          | ✓ Check all routes        |
| `backend/app.py`                         | Core       | Blueprint registration    | ✓ Check import            |
| `frontend/owner/dashboard.html`          | Template   | New (NEW)                 | ✓ Check paths             |
| `frontend/owner/bookings.html`           | Template   | New (NEW)                 | ✓ Check paths             |
| `frontend/owner/booking_detail.html`     | Template   | New (NEW)                 | ✓ Check paths             |
| `frontend/owner/create_business.html`    | Template   | New (NEW)                 | ✓ Check paths             |
| `frontend/owner/view_business.html`      | Template   | New (NEW)                 | ✓ Check paths             |
| `BUSINESS_OWNER_IMPLEMENTATION.md`       | Doc        | New (NEW)                 | ✓ Review docs             |

---

## Testing Checklist

### Unit Tests

- [ ] Test business owner registration with role='business_owner'
- [ ] Test default role='customer' for regular registration
- [ ] Test @business_owner_required decorator with valid user
- [ ] Test @business_owner_required decorator with customer (should deny)
- [ ] Test AcceptBookingCommand with correct owner (should succeed)
- [ ] Test AcceptBookingCommand with wrong owner (should fail)
- [ ] Test RejectBookingCommand with optional reason

### Integration Tests

- [ ] Business owner registration → login → dashboard flow
- [ ] Create business → view business → list bookings flow
- [ ] Accept booking → check status update → check timestamps
- [ ] Reject booking with reason → check notification
- [ ] Unauthorized access attempts → verify redirects

### Manual Testing

- [ ] Register new business owner account
- [ ] Login and verify redirect to /owner/dashboard
- [ ] Create business with profile picture and gallery
- [ ] View list of bookings with different statuses
- [ ] View booking detail page
- [ ] Accept booking and verify status change
- [ ] Reject booking with reason and verify notification
- [ ] Test mobile responsiveness on all new templates

### Security Testing

- [ ] Try accessing /owner/dashboard without login (should redirect to login)
- [ ] Try accessing /owner/dashboard as customer (should deny)
- [ ] Try accepting booking for business you don't own (should fail)
- [ ] Try rejecting booking with malicious reason input (should sanitize)
- [ ] Verify all sensitive operations are logged

---

## Performance Testing

- [ ] Dashboard loads within 2 seconds (even with 100+ bookings)
- [ ] Bookings list loads and filters efficiently
- [ ] Booking detail page loads within 1 second
- [ ] Accept/reject operations complete within 500ms
- [ ] No N+1 queries in booking list

---

## Monitoring Setup

### Logs to Monitor

```bash
# Watch for business owner activity
tail -f app.log | grep "owner_business"

# Watch for command execution
tail -f app.log | grep "Command"

# Watch for authorization failures
tail -f app.log | grep "Unauthorized"
```

### Key Metrics

- [ ] Number of business owners registered
- [ ] Average response time for dashboard
- [ ] Booking acceptance rate
- [ ] Number of rejected bookings with reasons
- [ ] Command execution success rate

---

## Rollback Plan

If issues occur after deployment:

1. **Check Logs:**

   ```bash
   tail -f app.log | grep "ERROR"
   ```

2. **Verify Database:**

   ```javascript
   db.users.findOne({ role: "business_owner" });
   ```

3. **If Critical Issues:**

   - Revert database changes (restore from backup)
   - Revert code to previous version
   - Restart application

4. **Document Issues:**
   - Note exact error messages
   - Record when issue occurred
   - Save relevant logs

---

## Post-Deployment Tasks

### Immediately After Deployment

- [ ] Test business owner registration and login
- [ ] Verify no errors in application logs
- [ ] Check MongoDB for new role field in users
- [ ] Test booking accept/reject operations
- [ ] Verify email notifications are sent (check logs)

### First Week

- [ ] Monitor for any authorization errors
- [ ] Check user feedback for UI/UX issues
- [ ] Review database performance metrics
- [ ] Check server resource usage (CPU, memory)

### First Month

- [ ] Analyze usage patterns
- [ ] Get user feedback
- [ ] Optimize based on real usage
- [ ] Update documentation if needed

---

## Common Issues & Quick Fixes

### Issue: "role field not found" error

```python
# Quick fix - Add default to model
role = me.StringField(default='customer', choices=ROLES, required=False)

# Or migrate existing records
db.users.updateMany({}, { $set: { role: "customer" } })
```

### Issue: Decorator returning 403 instead of redirecting

```python
# Verify decorator is checking role correctly
if not hasattr(current_user, 'role') or current_user.role != 'business_owner':
    # This condition is correct
```

### Issue: Command not executing (ownership check failing)

```python
# Debug: Print IDs being compared
logger.debug(f"Business owner_id: {business.owner_id}")
logger.debug(f"Current user: {current_user.user_id}")
# Verify they match
```

### Issue: Templates not loading (404 on new routes)

```python
# Check blueprint registration in app.py
app.register_blueprint(owner_business_bp)
# Verify template folder path
template_folder='../../frontend/owner'
```

---

## Environment Variables

Ensure `.env` file contains:

```env
# Existing
SECRET_KEY=your-secret-key
MONGO_URI=mongodb://...
DB_NAME=serviceDB

# Verify these are present (if using email/SMS)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

---

## Browser Compatibility

Test on:

- [ ] Chrome 90+
- [ ] Firefox 88+
- [ ] Safari 14+
- [ ] Edge 90+
- [ ] Mobile Chrome (Android)
- [ ] Mobile Safari (iOS)

---

## Accessibility Testing

- [ ] All forms have proper labels
- [ ] Color contrast meets WCAG standards
- [ ] Keyboard navigation works on all pages
- [ ] Screen reader compatible
- [ ] Mobile touch targets are 44px+

---

## Documentation

Before going live:

- [ ] Share `BUSINESS_OWNER_IMPLEMENTATION.md` with team
- [ ] Share `BUSINESS_OWNER_SUMMARY.md` with stakeholders
- [ ] Brief team on new decorator pattern usage
- [ ] Brief team on command pattern for booking ops
- [ ] Provide test scenarios to QA team
- [ ] Update main README.md with new feature

---

## Sign-Off

- [ ] Development Lead: **********\_********** Date: **\_**
- [ ] QA Lead: **********\_********** Date: **\_**
- [ ] DevOps/Deployment: **********\_********** Date: **\_**
- [ ] Product Owner: **********\_********** Date: **\_**

---

## Post-Launch Support

### First 48 Hours

- [ ] Monitor application logs hourly
- [ ] Be available for urgent fixes
- [ ] Track user feedback/bug reports
- [ ] Monitor performance metrics

### First Week

- [ ] Daily check of application health
- [ ] Review usage analytics
- [ ] Respond to user feedback
- [ ] Plan any immediate improvements

### Ongoing

- [ ] Weekly review of metrics
- [ ] Monthly feature suggestions based on usage
- [ ] Quarterly performance optimization
- [ ] Annual security audit

---

## Success Criteria

✅ Implementation is successful if:

1. **Functionality:**

   - Business owners can register and login
   - Business owners can create and manage businesses
   - Business owners can view and accept/reject bookings
   - All commands execute without errors

2. **Security:**

   - Non-business-owners cannot access /owner/\* routes
   - Ownership checks prevent unauthorized operations
   - All sensitive operations are logged
   - No data leaks in error messages

3. **Performance:**

   - Dashboard loads within 2 seconds
   - Booking operations complete within 500ms
   - No increase in memory usage
   - Database queries are optimized

4. **User Experience:**

   - Responsive design on all devices
   - Clear navigation and CTAs
   - Helpful error messages
   - Fast page load times

5. **Documentation:**
   - Clear implementation guide exists
   - Test scenarios are documented
   - API reference is complete
   - Troubleshooting guide covers common issues

---

**Deployment Date:** ******\_\_\_******  
**Deployed By:** ******\_\_\_******  
**Notes:**

---

End of Checklist
