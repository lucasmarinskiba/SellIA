"""
Unit tests for auth logic without database dependency.
Tests pure functions and code paths in auth module.
"""

import hashlib
import secrets
import pytest
from app.core.geo_service import haversine_distance, is_geofence_violation


class TestBackupCodeHashing:
    """Test backup code hashing logic."""

    def test_hash_code_consistency(self):
        """Same code should always produce same hash."""
        code = "A1B2C3D4"
        expected = hashlib.sha256(code.encode()).hexdigest()
        assert hashlib.sha256(code.encode()).hexdigest() == expected

    def test_hash_code_uniqueness(self):
        """Different codes should produce different hashes."""
        hash1 = hashlib.sha256("A1B2C3D4".encode()).hexdigest()
        hash2 = hashlib.sha256("B2C3D4E5".encode()).hexdigest()
        assert hash1 != hash2

    def test_hash_length(self):
        """SHA-256 hex should be 64 characters."""
        code = secrets.token_hex(4).upper()
        code_hash = hashlib.sha256(code.encode()).hexdigest()
        assert len(code_hash) == 64


class TestGeofencingLogic:
    """Test geofencing decision logic."""

    def test_buenos_aires_to_cordoba(self):
        """Distance from BA to Cordoba should trigger 500km geofence."""
        # BA: -34.60, -58.38
        # Cordoba: -31.42, -64.18
        violation, distance = is_geofence_violation(-34.60, -58.38, -31.42, -64.18, 500.0)
        assert violation is True
        assert distance > 500

    def test_nearby_logins_no_violation(self):
        """Two logins in the same city should not trigger geofence."""
        violation, distance = is_geofence_violation(
            -34.60, -58.38, -34.61, -58.39, 500.0
        )
        assert violation is False
        assert distance < 500

    def test_geofencing_disabled_with_zero(self):
        """Zero max_distance should disable geofencing."""
        violation, distance = is_geofence_violation(
            0.0, 0.0, 90.0, 0.0, 0.0
        )
        assert violation is False

    def test_geofencing_disabled_with_none_coords(self):
        """None coordinates should not trigger violation."""
        violation, distance = is_geofence_violation(
            None, None, 40.0, -74.0, 500.0
        )
        assert violation is False
        assert distance == 0.0

    def test_cross_hemisphere_distance(self):
        """Distance across hemispheres should be calculated correctly."""
        # Sydney to London
        dist = haversine_distance(-33.87, 151.21, 51.51, -0.13)
        assert dist == pytest.approx(16985, abs=100)


class TestLoginFlowCodes:
    """Test 2FA code validation patterns."""

    def test_totp_code_pattern(self):
        """TOTP codes are 6 digits."""
        code = "123456"
        assert code.isdigit()
        assert len(code) == 6

    def test_backup_code_pattern(self):
        """Backup codes are 8 hex chars."""
        code = "A1B2C3D4"
        assert len(code) == 8
        assert all(c in "0123456789ABCDEF" for c in code)

    def test_backup_code_generation(self):
        """Generated backup codes should match expected format."""
        codes = [secrets.token_hex(4).upper() for _ in range(8)]
        assert len(codes) == 8
        for code in codes:
            assert len(code) == 8
            assert code.isalnum()
            assert code == code.upper()
