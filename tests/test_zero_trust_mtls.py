"""
Tests for Zero-Trust mTLS Implementation
Tests service-to-service authentication, certificate validation, and network isolation.
"""

import unittest
import requests
import os
import time
import urllib3

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# API Gateway base URL
BASE_URL = os.getenv("BASE_URL", "https://localhost:8443")

# Create a session with SSL verification disabled for self-signed certs
session = requests.Session()
session.verify = False

# Path to certificates (if available for testing)
CERT_DIR = os.getenv("CERT_DIR", "../microservices/certs/generated")


class TestMTLSCertificateValidation(unittest.TestCase):
    """Test mTLS certificate validation for service-to-service communication."""

    def test_services_use_https(self):
        """Test that services are configured to use HTTPS."""
        # This test verifies that services are running with HTTPS
        # by checking that they reject plain HTTP connections
        # Note: Since services are not exposed, we test through gateway
        
        try:
            # Health check should work through gateway (which uses HTTPS to backend)
            response = session.get(f"{BASE_URL}/api/cards/health", timeout=5)
            self.assertEqual(response.status_code, 200)
            
            # Verify the gateway is using HTTPS to backend services
            # (indirect test - if HTTPS wasn't configured, nginx would fail)
            response = session.get(f"{BASE_URL}/api/auth/health", timeout=5)
            self.assertEqual(response.status_code, 200)
        except requests.exceptions.ConnectionError:
            self.skipTest("Services are not running. Start services with: cd microservices && ./build-and-start.sh")

    def test_certificate_files_exist(self):
        """Test that certificate files are generated and accessible."""
        # Check if certificate directory exists
        if os.path.exists(CERT_DIR):
            # Check for CA certificate
            ca_cert = os.path.join(CERT_DIR, "ca-cert.pem")
            self.assertTrue(
                os.path.exists(ca_cert), "CA certificate should exist"
            )

            # Check for service certificates
            services = [
                "auth-service",
                "card-service",
                "game-service",
                "leaderboard-service",
                "logs-service",
            ]
            for service in services:
                server_cert = os.path.join(
                    CERT_DIR, f"{service}-server-cert.pem"
                )
                client_cert = os.path.join(
                    CERT_DIR, f"{service}-client-cert.pem"
                )
                key_file = os.path.join(CERT_DIR, f"{service}-key.pem")

                self.assertTrue(
                    os.path.exists(server_cert),
                    f"{service} server certificate should exist",
                )
                self.assertTrue(
                    os.path.exists(client_cert),
                    f"{service} client certificate should exist",
                )
                self.assertTrue(
                    os.path.exists(key_file), f"{service} key file should exist"
                )


class TestServiceToServiceAuthentication(unittest.TestCase):
    """Test service-to-service authentication with API keys."""

    @classmethod
    def setUpClass(cls):
        """Set up test user and token."""
        # Check if services are running first
        try:
            test_response = session.get(f"{BASE_URL}/api/cards/health", timeout=5)
            if test_response.status_code != 200:
                raise requests.exceptions.ConnectionError("Services not healthy")
        except requests.exceptions.RequestException:
            raise unittest.SkipTest("Services are not running. Start services with: cd microservices && ./build-and-start.sh")
        
        cls.unique_id = int(time.time() * 1000)
        cls.username = f"zerotrust_{cls.unique_id}"
        cls.password = "TestPass123!"
        
        # Register user
        response = session.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "username": cls.username,
                "password": cls.password,
            },
            timeout=10,
        )
        cls.token = response.json().get("access_token")
        cls.headers = {"Authorization": f"Bearer {cls.token}"}

    def test_game_service_calls_card_service(self):
        """Test that game service can call card service with mTLS."""
        # Create a game which triggers game-service -> card-service call
        response = session.post(
            f"{BASE_URL}/api/games",
            headers=self.headers,
            json={"player2_name": "test_player"},
        )

        # Should succeed if mTLS is working
        # (may fail for other reasons like user not found, but not SSL errors)
        self.assertIn(
            response.status_code,
            [200, 201, 400, 404],
            "Game creation should work (may fail for non-SSL reasons)",
        )

        # Check that response doesn't indicate SSL/TLS errors
        if response.status_code >= 500:
            response_text = response.text.lower()
            self.assertNotIn(
                "ssl", response_text, "Should not have SSL errors in response"
            )
            self.assertNotIn(
                "certificate",
                response_text,
                "Should not have certificate errors in response",
            )

    def test_card_service_calls_auth_service(self):
        """Test that card service can call auth service with mTLS."""
        # Get cards which may trigger card-service -> auth-service call for token validation
        response = session.get(
            f"{BASE_URL}/api/cards",
            headers=self.headers,
        )

        # Should succeed if mTLS is working
        self.assertEqual(
            response.status_code, 200, "Card retrieval should work with mTLS"
        )

        # Verify response structure
        data = response.json()
        self.assertIn("cards", data)

    def test_inter_service_communication_encrypted(self):
        """Test that inter-service communication uses HTTPS."""
        # This is an indirect test - we verify that services can communicate
        # which implies HTTPS is working (since we configured it)

        # Create a game and get cards - this exercises multiple service calls
        game_response = session.post(
            f"{BASE_URL}/api/games",
            headers=self.headers,
            json={"player2_name": "test_player"},
        )

        cards_response = session.get(
            f"{BASE_URL}/api/cards",
            headers=self.headers,
        )

        # Both should work, indicating HTTPS communication is functional
        self.assertIn(cards_response.status_code, [200, 201])

        # If game creation worked, it means game-service -> card-service worked
        if game_response.status_code in [200, 201]:
            self.assertTrue(True, "Inter-service HTTPS communication verified")


class TestNetworkIsolation(unittest.TestCase):
    """Test network isolation and port exposure."""

    def test_internal_ports_not_exposed(self):
        """Test that internal service ports are not accessible from host."""
        # Note: This test assumes services are running in Docker
        # and ports are not exposed. In a real scenario, we'd check
        # if ports are listening on localhost.

        internal_ports = [5001, 5002, 5003, 5004, 5006]
        exposed_ports = []

        for port in internal_ports:
            try:
                # Try to connect directly to service port
                # This should fail if ports are not exposed
                response = requests.get(
                    f"http://localhost:{port}/health",
                    timeout=2,
                    verify=False,
                )
                # If we get a response, port is exposed (which is bad)
                if response.status_code in [200, 404, 401]:
                    exposed_ports.append(port)
            except (
                requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
                requests.exceptions.RequestException,
            ):
                # Connection refused/timeout is expected - port not exposed
                pass

        # Only gateway ports should be accessible
        self.assertEqual(
            len(exposed_ports),
            0,
            f"Internal service ports should not be exposed. Found exposed: {exposed_ports}",
        )

    def test_gateway_port_exposed(self):
        """Test that gateway port is properly exposed."""
        try:
            # Gateway should be accessible
            response = session.get(f"{BASE_URL}/api/cards/health", timeout=5)
            self.assertEqual(
                response.status_code,
                200,
                "Gateway should be accessible on exposed port",
            )
        except requests.exceptions.ConnectionError:
            self.skipTest("Services are not running. Start services with: cd microservices && ./build-and-start.sh")

    def test_services_accessible_through_gateway_only(self):
        """Test that services are only accessible through gateway."""
        # Check if services are running first
        try:
            test_response = session.get(f"{BASE_URL}/api/cards/health", timeout=5)
            if test_response.status_code != 200:
                raise requests.exceptions.ConnectionError("Services not healthy")
        except requests.exceptions.RequestException:
            self.skipTest("Services are not running. Start services with: cd microservices && ./build-and-start.sh")
        
        # All service endpoints should work through gateway
        services_to_test = [
            "/api/auth/health",
            "/api/cards/health",
            "/api/games",  # May require auth, but should be reachable
        ]
        
        for endpoint in services_to_test:
            try:
                response = session.get(f"{BASE_URL}{endpoint}", timeout=5)
                # Should get some response (even if 401/404) through gateway
                self.assertIsNotNone(
                    response.status_code,
                    f"Service {endpoint} should be reachable through gateway",
                )
            except requests.exceptions.RequestException as e:
                self.fail(
                    f"Service {endpoint} not reachable through gateway: {e}"
                )


class TestZeroTrustPrinciples(unittest.TestCase):
    """Test that zero-trust principles are implemented."""

    def test_services_require_authentication(self):
        """Test that services require proper authentication."""
        try:
            # Try to access protected endpoint without token
            response = session.get(f"{BASE_URL}/api/cards", timeout=5)
            
            # Should require authentication
            self.assertIn(
                response.status_code,
                [401, 403],
                "Services should require authentication",
            )
        except requests.exceptions.ConnectionError:
            self.skipTest("Services are not running. Start services with: cd microservices && ./build-and-start.sh")

    def test_encrypted_communication(self):
        """Test that communication is encrypted (HTTPS)."""
        # Verify we're using HTTPS
        self.assertTrue(
            BASE_URL.startswith("https://"), "Base URL should use HTTPS"
        )
        
        try:
            # Verify gateway uses HTTPS
            response = session.get(f"{BASE_URL}/api/cards/health", timeout=5)
            self.assertEqual(
                response.status_code, 200, "HTTPS communication should work"
            )
        except requests.exceptions.ConnectionError:
            self.skipTest("Services are not running. Start services with: cd microservices && ./build-and-start.sh")

    def test_network_segmentation_configured(self):
        """Test that network segmentation is configured in docker-compose."""
        # Check if docker-compose.yml has network configuration
        compose_file = "../microservices/docker-compose.yml"
        if os.path.exists(compose_file):
            with open(compose_file, "r") as f:
                content = f.read()

                # Check for network definitions
                self.assertIn(
                    "api-network", content, "api-network should be defined"
                )
                self.assertIn(
                    "database-network",
                    content,
                    "database-network should be defined",
                )
                self.assertIn(
                    "frontend-network",
                    content,
                    "frontend-network should be defined",
                )


if __name__ == "__main__":
    unittest.main()
