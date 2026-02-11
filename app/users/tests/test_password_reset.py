"""Tests for password reset functionality."""

from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.utils import timezone

import pytest
from graphene.test import Client

from core.schema import schema
from users.models import PasswordResetToken

User = get_user_model()


@pytest.mark.django_db
class TestRequestPasswordReset:
    """Test cases for requesting password reset."""

    def test_request_password_reset_success(self, user):
        """Test successful password reset request."""
        client = Client(schema)

        mutation = """
            mutation RequestPasswordReset($input: RequestPasswordResetInput!) {
                requestPasswordReset(input: $input) {
                    success
                    message
                    errors
                }
            }
        """

        with patch("django.core.mail.send_mail") as mock_send_mail:
            mock_send_mail.return_value = 1

            result = client.execute(
                mutation,
                variables={"input": {"email": user.email}},
            )

        assert result["data"]["requestPasswordReset"]["success"] is True
        assert (
            "password reset link has been sent" in result["data"]["requestPasswordReset"]["message"]
        )
        assert result["data"]["requestPasswordReset"]["errors"] is None

        # Verify token was created
        token = PasswordResetToken.objects.filter(user=user, is_active=True).first()
        assert token is not None
        assert token.is_valid()

        # Verify email was sent
        mock_send_mail.assert_called_once()
        call_args = mock_send_mail.call_args
        assert user.email in call_args[1]["recipient_list"]
        assert "Password Reset Request" in call_args[1]["subject"]

    def test_request_password_reset_nonexistent_email(self):
        """Test password reset request with non-existent email."""
        client = Client(schema)

        mutation = """
            mutation RequestPasswordReset($input: RequestPasswordResetInput!) {
                requestPasswordReset(input: $input) {
                    success
                    message
                    errors
                }
            }
        """

        with patch("django.core.mail.send_mail") as mock_send_mail:
            result = client.execute(
                mutation,
                variables={"input": {"email": "nonexistent@example.com"}},
            )

        # Should still return success for security (don't reveal if email exists)
        assert result["data"]["requestPasswordReset"]["success"] is True
        assert (
            "password reset link has been sent" in result["data"]["requestPasswordReset"]["message"]
        )

        # Verify no email was sent
        mock_send_mail.assert_not_called()

    def test_request_password_reset_deactivates_old_tokens(self, user):
        """Test that requesting password reset deactivates old tokens."""
        # Create an old token
        old_token = PasswordResetToken.objects.create(user=user)
        assert old_token.is_active is True

        client = Client(schema)

        mutation = """
            mutation RequestPasswordReset($input: RequestPasswordResetInput!) {
                requestPasswordReset(input: $input) {
                    success
                    message
                    errors
                }
            }
        """

        with patch("django.core.mail.send_mail") as mock_send_mail:
            mock_send_mail.return_value = 1

            result = client.execute(
                mutation,
                variables={"input": {"email": user.email}},
            )

        assert result["data"]["requestPasswordReset"]["success"] is True

        # Verify old token was deactivated
        old_token.refresh_from_db()
        assert old_token.is_active is False

        # Verify new token was created
        new_token = PasswordResetToken.objects.filter(user=user, is_active=True).first()
        assert new_token is not None
        assert new_token.id != old_token.id

    def test_request_password_reset_email_failure(self, user):
        """Test password reset request when email sending fails."""
        client = Client(schema)

        mutation = """
            mutation RequestPasswordReset($input: RequestPasswordResetInput!) {
                requestPasswordReset(input: $input) {
                    success
                    message
                    errors
                }
            }
        """

        with patch("django.core.mail.send_mail") as mock_send_mail:
            mock_send_mail.side_effect = Exception("Email service unavailable")

            result = client.execute(
                mutation,
                variables={"input": {"email": user.email}},
            )

        assert result["data"]["requestPasswordReset"]["success"] is False
        assert result["data"]["requestPasswordReset"]["errors"] is not None
        assert "Failed to send email" in result["data"]["requestPasswordReset"]["errors"][0]


@pytest.mark.django_db
class TestConfirmPasswordReset:
    """Test cases for confirming password reset."""

    def test_confirm_password_reset_success(self, user):
        """Test successful password reset confirmation."""
        # Create a valid token
        reset_token = PasswordResetToken.objects.create(user=user)
        old_password = user.password

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

        result = client.execute(
            mutation,
            variables={
                "input": {
                    "token": reset_token.token,
                    "newPassword": "NewSecurePass123!",
                }
            },
        )

        assert result["data"]["confirmPasswordReset"]["success"] is True
        assert (
            "Password has been reset successfully"
            in result["data"]["confirmPasswordReset"]["message"]
        )
        assert result["data"]["confirmPasswordReset"]["errors"] is None

        # Verify password was changed
        user.refresh_from_db()
        assert user.password != old_password
        assert user.check_password("NewSecurePass123!")

        # Verify token was marked as used
        reset_token.refresh_from_db()
        assert reset_token.used_at is not None
        assert reset_token.is_active is False
        assert not reset_token.is_valid()

    def test_confirm_password_reset_invalid_token(self):
        """Test password reset with invalid token."""
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

        result = client.execute(
            mutation,
            variables={
                "input": {
                    "token": "invalid-token-12345",
                    "newPassword": "NewSecurePass123!",
                }
            },
        )

        assert result["data"]["confirmPasswordReset"]["success"] is False
        assert "Invalid or expired token" in result["data"]["confirmPasswordReset"]["errors"][0]

    def test_confirm_password_reset_expired_token(self, user):
        """Test password reset with expired token."""
        # Create an expired token
        reset_token = PasswordResetToken.objects.create(user=user)
        reset_token.expires_at = timezone.now() - timedelta(hours=1)
        reset_token.save()

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

        result = client.execute(
            mutation,
            variables={
                "input": {
                    "token": reset_token.token,
                    "newPassword": "NewSecurePass123!",
                }
            },
        )

        assert result["data"]["confirmPasswordReset"]["success"] is False
        assert "Invalid or expired token" in result["data"]["confirmPasswordReset"]["errors"][0]

    def test_confirm_password_reset_used_token(self, user):
        """Test password reset with already used token."""
        # Create a used token
        reset_token = PasswordResetToken.objects.create(user=user)
        reset_token.mark_as_used()

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

        result = client.execute(
            mutation,
            variables={
                "input": {
                    "token": reset_token.token,
                    "newPassword": "NewSecurePass123!",
                }
            },
        )

        assert result["data"]["confirmPasswordReset"]["success"] is False
        assert "Invalid or expired token" in result["data"]["confirmPasswordReset"]["errors"][0]

    def test_confirm_password_reset_weak_password(self, user):
        """Test password reset with weak password."""
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

        result = client.execute(
            mutation,
            variables={
                "input": {
                    "token": reset_token.token,
                    "newPassword": "weak",
                }
            },
        )

        assert result["data"]["confirmPasswordReset"]["success"] is False
        assert result["data"]["confirmPasswordReset"]["errors"] is not None
        assert len(result["data"]["confirmPasswordReset"]["errors"]) > 0

        # Verify token is still valid (not used)
        reset_token.refresh_from_db()
        assert reset_token.is_valid()

    def test_confirm_password_reset_inactive_token(self, user):
        """Test password reset with inactive token."""
        reset_token = PasswordResetToken.objects.create(user=user)
        reset_token.is_active = False
        reset_token.save()

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

        result = client.execute(
            mutation,
            variables={
                "input": {
                    "token": reset_token.token,
                    "newPassword": "NewSecurePass123!",
                }
            },
        )

        assert result["data"]["confirmPasswordReset"]["success"] is False
        assert "Invalid or expired token" in result["data"]["confirmPasswordReset"]["errors"][0]


@pytest.mark.django_db
class TestPasswordResetTokenModel:
    """Test cases for PasswordResetToken model."""

    def test_token_auto_generation(self, user):
        """Test that token is automatically generated."""
        reset_token = PasswordResetToken.objects.create(user=user)

        assert reset_token.token is not None
        assert len(reset_token.token) > 0

    def test_token_uniqueness(self, user):
        """Test that tokens are unique."""
        token1 = PasswordResetToken.objects.create(user=user)
        token2 = PasswordResetToken.objects.create(user=user)

        assert token1.token != token2.token

    def test_expiration_auto_set(self, user):
        """Test that expiration is automatically set."""
        reset_token = PasswordResetToken.objects.create(user=user)

        assert reset_token.expires_at is not None
        assert reset_token.expires_at > timezone.now()

    def test_is_valid_method(self, user):
        """Test is_valid method."""
        reset_token = PasswordResetToken.objects.create(user=user)

        # Should be valid initially
        assert reset_token.is_valid() is True

        # Should be invalid after marking as used
        reset_token.mark_as_used()
        assert reset_token.is_valid() is False

    def test_is_valid_expired(self, user):
        """Test is_valid with expired token."""
        reset_token = PasswordResetToken.objects.create(user=user)
        reset_token.expires_at = timezone.now() - timedelta(hours=1)
        reset_token.save()

        assert reset_token.is_valid() is False

    def test_mark_as_used(self, user):
        """Test mark_as_used method."""
        reset_token = PasswordResetToken.objects.create(user=user)

        assert reset_token.used_at is None
        assert reset_token.is_active is True

        reset_token.mark_as_used()

        assert reset_token.used_at is not None
        assert reset_token.is_active is False

    def test_string_representation(self, user):
        """Test string representation of token."""
        reset_token = PasswordResetToken.objects.create(user=user)

        assert str(reset_token) == f"Password reset token for {user.email}"
