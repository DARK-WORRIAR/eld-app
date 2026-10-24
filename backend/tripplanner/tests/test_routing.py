"""
Unit tests for routing calculations and spatial interpolation algorithms.
"""

from django.test import SimpleTestCase
from tripplanner.services.routing import haversine_distance_miles, point_at_distance


class RoutingAlgorithmTests(SimpleTestCase):
    """
    Validates spherical distance and polyline marker projection calculations.
    """

    def test_haversine_known_distance(self):
        """Distance between NYC (40.7128, -74.0060) and Philly (39.9526, -75.1652) is ~80 miles."""
        dist = haversine_distance_miles(40.7128, -74.0060, 39.9526, -75.1652)
        self.assertAlmostEqual(dist, 80.5, delta=5.0)

    def test_point_at_distance_exact_boundaries(self):
        """Point at distance 0 should return first coordinate, and at max should return last."""
        coords = [
            [32.7767, -96.7970],  # Dallas
            [35.4676, -97.5164],  # OKC
            [41.8781, -87.6298],  # Chicago
        ]
        start_pt = point_at_distance(coords, total_route_miles=900.0, target_miles=0.0)
        self.assertEqual(start_pt, coords[0])

        end_pt = point_at_distance(coords, total_route_miles=900.0, target_miles=900.0)
        self.assertEqual(end_pt, coords[-1])

    def test_point_at_distance_interpolation(self):
        """Point along simple straight segment should interpolate linearly."""
        coords = [
            [0.0, 0.0],
            [10.0, 0.0],
        ]
        mid = point_at_distance(coords, total_route_miles=690.0, target_miles=345.0)
        self.assertAlmostEqual(mid[0], 5.0, delta=0.5)
        self.assertAlmostEqual(mid[1], 0.0, delta=0.1)

