"""
Tests for geofencing and IP geolocation service.
"""

import pytest
from app.core.geo_service import (
    haversine_distance,
    is_geofence_violation,
    _is_private_ip,
)


class TestHaversineDistance:
    """Test the Haversine distance calculation."""

    def test_same_point_zero_distance(self):
        """Distance from a point to itself should be 0."""
        dist = haversine_distance(40.7128, -74.0060, 40.7128, -74.0060)
        assert dist == pytest.approx(0.0, abs=0.001)

    def test_ny_to_london(self):
        """Distance from New York to London should be ~5570 km."""
        # NYC: 40.7128° N, 74.0060° W
        # London: 51.5074° N, 0.1278° W
        dist = haversine_distance(40.7128, -74.0060, 51.5074, -0.1278)
        assert dist == pytest.approx(5570, abs=50)

    def test_buenos_aires_to_madrid(self):
        """Distance from Buenos Aires to Madrid should be ~10050 km."""
        dist = haversine_distance(-34.6037, -58.3816, 40.4168, -3.7038)
        assert dist == pytest.approx(10050, abs=100)

    def test_short_distance(self):
        """Two points close together should have a small distance."""
        dist = haversine_distance(40.71, -74.01, 40.72, -74.00)
        assert dist == pytest.approx(1.4, abs=0.5)


class TestIsGeofenceViolation:
    """Test geofence violation detection."""

    def test_within_limit_no_violation(self):
        """Login 10km away from last with 500km limit should not violate."""
        violation, distance = is_geofence_violation(
            -34.60, -58.38, -34.61, -58.39, 500.0
        )
        assert violation is False
        assert distance > 0

    def test_exceeds_limit_violation(self):
        """Login 600km away from last with 500km limit should violate."""
        # Buenos Aires to Cordoba is ~700km
        violation, distance = is_geofence_violation(
            -34.60, -58.38, -31.42, -64.18, 500.0
        )
        assert violation is True
        assert distance > 500

    def test_zero_limit_disabled(self):
        """Zero or negative max_distance means geofencing is disabled."""
        violation, distance = is_geofence_violation(
            -34.60, -58.38, 51.50, -0.13, 0.0
        )
        assert violation is False
        assert distance > 0

    def test_none_coordinates_no_violation(self):
        """Missing coordinates should not trigger violation."""
        violation, distance = is_geofence_violation(
            None, -58.38, -34.60, -58.38, 500.0
        )
        assert violation is False
        assert distance == 0.0

    def test_negative_limit_disabled(self):
        """Negative max_distance means disabled."""
        violation, distance = is_geofence_violation(
            -34.60, -58.38, 51.50, -0.13, -100.0
        )
        assert violation is False


class TestPrivateIPDetection:
    """Test detection of private/unroutable IPs."""

    @pytest.mark.parametrize("ip", [
        "127.0.0.1",
        "::1",
        "0:0:0:0:0:0:0:1",
        "localhost",
        "10.0.0.1",
        "10.255.255.255",
        "172.16.0.1",
        "172.31.255.255",
        "192.168.1.1",
        "192.168.255.255",
    ])
    def test_private_ips(self, ip):
        assert _is_private_ip(ip) is True

    @pytest.mark.parametrize("ip", [
        "8.8.8.8",
        "1.1.1.1",
        "2001:4860:4860::8888",
        "190.20.30.40",
    ])
    def test_public_ips(self, ip):
        assert _is_private_ip(ip) is False

    def test_empty_ip(self):
        assert _is_private_ip("") is True
        assert _is_private_ip(None) is True
