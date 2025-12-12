# Zero-Trust Networking Implementation

## Overview

This document describes the zero-trust networking implementation for the Battle Cards microservices architecture. The implementation demonstrates key zero-trust principles including service-to-service authentication via mTLS, network segmentation, and least privilege access.

## Zero-Trust Principles Implemented

### 1. Service-to-Service Authentication (mTLS)

**Implementation:**
- All inter-service communication uses mutual TLS (mTLS)
- Each service has both server and client certificates
- Services authenticate each other using certificates signed by a common CA
- Additional service API keys provide defense-in-depth

**Files:**
- `microservices/certs/generate-certs.sh` - Certificate generation script
- `microservices/utils/mtls_auth.py` - mTLS utilities
- `microservices/utils/service_auth.py` - Service API key validation

**How it works:**
1. Services use HTTPS with server certificates to accept connections
2. Services use client certificates when making requests to other services
3. Certificate validation ensures only authorized services can communicate

### 2. Remove Port Exposure for Internal Services

**Implementation:**
- Internal service ports (5001-5006) are no longer exposed to the host
- Only the nginx gateway (ports 8080, 8443) is exposed
- Services communicate exclusively through Docker internal networks

**Changes:**
- Removed `ports:` mappings from all internal services in `docker-compose.yml`
- Services are only accessible through the nginx gateway or from other services on the internal network

### 3. Network Segmentation

**Implementation:**
- Three separate Docker networks enforce network boundaries:
  - `frontend-network`: Nginx gateway only
  - `api-network`: All microservices (auth, card, game, leaderboard, logs)
  - `database-network`: PostgreSQL database only

**Network Topology:**
```
frontend-network (nginx only)
    ↓
api-network (all services)
    ↓
database-network (postgresql only)
```

**Service Network Memberships:**
- **Nginx Gateway**: `frontend-network` + `api-network` (routes to services)
- **Microservices**: `api-network` + `database-network` (need DB access)
- **PostgreSQL**: `database-network` only (isolated)

### 4. Encrypted Inter-Service Communication

**Implementation:**
- All service-to-service communication uses HTTPS
- Nginx gateway uses HTTPS when proxying to backend services
- Services use mTLS for direct service-to-service calls

**Configuration:**
- Gunicorn configured with `--certfile` and `--keyfile` for HTTPS
- Nginx configured with `proxy_ssl_verify` to verify backend certificates
- Python `requests` library uses client certificates for outbound calls

### 5. Separate Credentials for Each Service

**Implementation:**
- Each service has a unique `SERVICE_API_KEY` environment variable
- Service API keys are used for additional authentication layer
- Keys are passed via `X-Service-API-Key` header

**Environment Variables:**
- `AUTH_SERVICE_API_KEY`
- `CARD_SERVICE_API_KEY`
- `GAME_SERVICE_API_KEY`
- `LEADERBOARD_SERVICE_API_KEY`
- `LOGS_SERVICE_API_KEY`

### 6. Principle of Least Privilege

**Implementation:**
- Services only have access to networks they need
- Services only have certificates for services they communicate with
- Database access limited to services that need it
- Network policies enforce communication boundaries

**Access Matrix:**
- **Game Service** → Card Service (for deck generation)
- **Card Service** → Auth Service (for token validation)
- **All Services** → Database (for data access)
- **Nginx** → All Services (for routing)

## Architecture Changes

### Before (Traditional)
- All services exposed on host ports
- HTTP communication between services
- Single network for all services
- No service-to-service authentication
- Shared credentials

### After (Zero-Trust)
- Only gateway exposed
- HTTPS with mTLS between services
- Network segmentation (3 networks)
- Certificate-based authentication
- Unique credentials per service

## File Changes Summary

### New Files
- `microservices/certs/generate-certs.sh` - Certificate generation
- `microservices/certs/README.md` - Certificate documentation
- `microservices/utils/mtls_auth.py` - mTLS utilities
- `microservices/utils/service_auth.py` - Service authentication
- `documentation/ZERO_TRUST_IMPLEMENTATION.md` - This file

### Modified Files
- `microservices/docker-compose.yml` - Network segmentation, removed ports, added certs
- `microservices/nginx/nginx.conf` - HTTPS proxying to backend services
- `microservices/*/Dockerfile` - Certificate mounting, HTTPS configuration
- `microservices/game-service/app.py` - mTLS for card-service calls
- `microservices/card-service/app.py` - mTLS for auth-service calls

## Deployment

### Prerequisites
1. Generate certificates:
   ```bash
   cd microservices/certs
   ./generate-certs.sh
   ```

2. Set service API keys in `.env` file:
   ```bash
   AUTH_SERVICE_API_KEY=your-auth-key
   CARD_SERVICE_API_KEY=your-card-key
   GAME_SERVICE_API_KEY=your-game-key
   LEADERBOARD_SERVICE_API_KEY=your-leaderboard-key
   LOGS_SERVICE_API_KEY=your-logs-key
   ```

3. Build and start services:
   ```bash
   cd microservices
   ./build-and-start.sh
   ```

### Verification

1. **Check network isolation:**
   ```bash
   docker network inspect battlecards-api
   docker network inspect battlecards-database
   docker network inspect battlecards-frontend
   ```

2. **Verify no port exposure:**
   ```bash
   docker ps --format "table {{.Names}}\t{{.Ports}}"
   # Should only show nginx gateway ports
   ```

3. **Test service communication:**
   - Services should communicate via HTTPS
   - Check service logs for SSL/TLS errors
   - Verify certificate validation

## Security Considerations

### Development Environment
- Self-signed certificates are acceptable for development
- Service API keys can be simple for development
- Network policies demonstrate principles

### Production Recommendations
1. **Certificates:**
   - Use certificates from trusted CA or organization PKI
   - Implement certificate rotation
   - Use certificate management system (e.g., Vault)

2. **Service API Keys:**
   - Use strong, randomly generated keys
   - Store in secrets management system
   - Rotate regularly

3. **Network Policies:**
   - Consider Kubernetes NetworkPolicies for more granular control
   - Implement service mesh (Istio, Linkerd) for advanced features
   - Use firewall rules for additional protection

4. **Monitoring:**
   - Monitor certificate expiration
   - Alert on authentication failures
   - Track service-to-service communication patterns

## Troubleshooting

### Services Can't Connect
1. Verify certificates are generated and mounted
2. Check network memberships in docker-compose
3. Verify service API keys are set correctly
4. Check service logs for SSL errors

### Certificate Errors
1. Regenerate certificates if needed
2. Verify CA certificate is in all containers
3. Check certificate file permissions
4. Verify certificate paths in environment variables

### Network Issues
1. Verify Docker networks are created
2. Check service network memberships
3. Test connectivity between services
4. Review docker-compose network configuration

## References

- [Zero Trust Architecture](https://www.nist.gov/publications/zero-trust-architecture)
- [mTLS Documentation](https://www.cloudflare.com/learning/access-management/what-is-mutual-tls/)
- [Docker Networking](https://docs.docker.com/network/)
- [Gunicorn SSL](https://docs.gunicorn.org/en/stable/settings.html#ssl)

## Conclusion

This implementation demonstrates core zero-trust networking principles:
- ✅ Service-to-service authentication (mTLS)
- ✅ No internal port exposure
- ✅ Network segmentation
- ✅ Encrypted communication
- ✅ Separate service credentials
- ✅ Least privilege access

While this is a development/demonstration implementation, it provides a solid foundation for understanding and implementing zero-trust principles in production environments.
