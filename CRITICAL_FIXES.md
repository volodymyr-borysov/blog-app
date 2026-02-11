# Critical Security Fixes Required

This document outlines the **critical security issues** that must be fixed before merging the password reset PR.

---

## 🔴 CRITICAL FIX #1: Race Condition in Token Validation

### Issue
Multiple concurrent requests with the same token could all pass validation before any marks the token as used.

### Location
`app/users/schema/mutations.py` - `ConfirmPasswordReset.mutate()` method

### Fix
Use database-level locking with `select_for_update()` and atomic transactions:

```python
@classmethod
def mutate(cls, root, info, input):
    from django.db import transaction
    from ..models import PasswordResetToken

    try:
        # Use select_for_update to lock the row
        with transaction.atomic():
            reset_token = PasswordResetToken.objects.select_for_update().get(
                token=input.token
            )
            
            # Validate token
            if not reset_token.is_valid():
                return ConfirmPasswordReset(
                    success=False, 
                    message=None, 
                    errors=["Invalid or expired token."]
                )

            # Validate new password
            errors = []
            try:
                validate_password(input.new_password, user=reset_token.user)
            except ValidationError as e:
                errors.extend(list(e.messages))

            if errors:
                return ConfirmPasswordReset(success=False, message=None, errors=errors)

            # Set new password
            reset_token.user.set_password(input.new_password)
            reset_token.user.save()

            # Mark token as used (still within the atomic transaction)
            reset_token.mark_as_used()

            return ConfirmPasswordReset(
                success=True,
                message="Password has been reset successfully.",
                errors=None,
            )
            
    except PasswordResetToken.DoesNotExist:
        return ConfirmPasswordReset(
            success=False, 
            message=None, 
            errors=["Invalid or expired token."]
        )
```

---

## 🔴 CRITICAL FIX #2: Timing Attack Vulnerability

### Issue
The mutation returns immediately when user doesn't exist, but performs database operations and email sending when user exists. This timing difference can be used to enumerate valid email addresses.

### Location
`app/users/schema/mutations.py` - `RequestPasswordReset.mutate()` method

### Fix
Ensure similar execution paths regardless of whether the user exists:

```python
@classmethod
def mutate(cls, root, info, input):
    from django.conf import settings
    from django.core.mail import send_mail
    from ..models import PasswordResetToken
    import logging
    
    logger = logging.getLogger(__name__)

    # Validate email format first (fail fast for clearly invalid emails)
    import re
    email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(email_regex, input.email):
        # For invalid format, still return success message
        return RequestPasswordReset(
            success=True,
            message=(
                "If an account with this email exists, "
                "a password reset link has been sent."
            ),
            errors=None,
        )

    # Try to get user
    try:
        user = User.objects.get(email=input.email)
        user_exists = True
    except User.DoesNotExist:
        user = None
        user_exists = False

    # Perform operations only if user exists
    if user_exists:
        # Deactivate any existing active tokens for this user
        PasswordResetToken.objects.filter(user=user, is_active=True).update(
            is_active=False
        )

        # Create new token
        reset_token = PasswordResetToken.objects.create(user=user)

        # Prepare reset URL
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token.token}"

        # Send email
        try:
            send_mail(
                subject="Password Reset Request",
                message=(
                    f"Hello {user.get_full_name()},\n\n"
                    f"You requested a password reset. Click the link below to reset your password:\n\n"
                    f"{reset_url}\n\n"
                    f"This link will expire in 24 hours.\n\n"
                    f"If you didn't request this, please ignore this email.\n\n"
                    f"Best regards,\nThe Blog Team"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
        except Exception as e:
            logger.error(f"Failed to send password reset email to {user.email}: {str(e)}")
            return RequestPasswordReset(
                success=False,
                message=None,
                errors=[f"Failed to send email: {str(e)}"],
            )
    else:
        # User doesn't exist - do nothing but maintain similar timing
        # The database query above already consumed some time
        logger.info(f"Password reset requested for non-existent email: {input.email}")
    
    # Always return the same success message
    return RequestPasswordReset(
        success=True,
        message="If an account with this email exists, a password reset link has been sent.",
        errors=None,
    )
```

**Note:** While this reduces timing differences, determined attackers with precise timing measurements might still detect differences. For maximum security, consider:
1. Adding rate limiting (see PR_REVIEW.md)
2. Adding a small random delay
3. Implementing CAPTCHA for multiple failed attempts

---

## 📝 Testing the Fixes

### Test for Race Condition Protection

Add this test to `app/users/tests/test_password_reset.py`:

```python
import threading
from django.db import transaction

@pytest.mark.django_db
class TestPasswordResetConcurrency:
    """Test cases for concurrent password reset attempts."""

    def test_concurrent_token_usage_prevented(self, user):
        """Test that the same token cannot be used concurrently."""
        reset_token = PasswordResetToken.objects.create(user=user)
        client = Client(schema)
        
        mutation = """
            mutation ConfirmPasswordReset($input: ConfirmPasswordResetInput!) {
                confirmPasswordReset(input: $input) {
                    success
                    message
                    errors
                }
            }
        """
        
        results = []
        errors = []
        
        def reset_password():
            try:
                result = client.execute(
                    mutation,
                    variables={
                        "input": {
                            "token": reset_token.token,
                            "newPassword": "NewSecurePass123!",
                        }
                    },
                )
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        # Create two threads that try to use the same token simultaneously
        thread1 = threading.Thread(target=reset_password)
        thread2 = threading.Thread(target=reset_password)
        
        thread1.start()
        thread2.start()
        thread1.join()
        thread2.join()
        
        # Only one should succeed
        success_count = sum(
            1 for r in results 
            if r.get("data", {}).get("confirmPasswordReset", {}).get("success")
        )
        
        assert success_count == 1, "Only one concurrent request should succeed"
        
        # Verify token was marked as used
        reset_token.refresh_from_db()
        assert not reset_token.is_valid()
```

---

## 🚀 Deployment Checklist

Before deploying password reset to production:

- [ ] Apply Critical Fix #1 (Race Condition)
- [ ] Apply Critical Fix #2 (Timing Attack)
- [ ] Add the concurrency test
- [ ] Run all tests and verify they pass
- [ ] Implement rate limiting (recommended)
- [ ] Set up monitoring for failed password reset attempts
- [ ] Configure email settings properly in production
- [ ] Set up a cron job to clean up expired tokens
- [ ] Document the password reset flow for users
- [ ] Test the complete flow in a staging environment

---

## Additional Recommendations

While not critical, these should be addressed soon:

1. **Rate Limiting**: Limit password reset requests per email/IP
2. **Token Cleanup**: Schedule a task to delete expired tokens
3. **Confirmation Email**: Send email after successful password reset
4. **Audit Logging**: Log all password reset attempts with IP addresses
5. **Token Length**: Increase token field from 64 to 128 characters

See `PR_REVIEW.md` for complete details on all issues found.
