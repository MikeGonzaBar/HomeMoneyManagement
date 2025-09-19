# Security Policy

## Security Vulnerabilities

This document outlines the security measures and vulnerability management for the Home Money Management application.

## Recent Security Updates

### Critical Security Fixes (December 2024)

#### 1. Password Security - RESOLVED 🔐

**Before**: Passwords stored in plain text  
**After**: Passwords are now securely hashed using Django's `make_password()` and `check_password()`

**Implementation**: Added secure password methods to the User model
**Impact**: Zero breaking changes - existing data remains compatible

```python
# User model now includes secure password methods
def set_password(self, raw_password):
    """Set password with secure hashing."""
    self.password = make_password(raw_password)

def check_password(self, raw_password):
    """Check password against hash."""
    return check_password(raw_password, self.password)
```

#### 2. Authentication Security - RESOLVED 🛡️

**Before**: Plain text password comparison  
**After**: Secure password verification using Django's hashing system

**Implementation**: Updated UserService to use secure authentication
**Impact**: All existing login functionality works unchanged

```python
# UserService now uses secure authentication
user = User.objects.get(username=username_or_email)
if user.check_password(password):
    # Authentication successful
```

#### 3. Input Validation - RESOLVED ✅

**Before**: No validation on user inputs  
**After**: Comprehensive validation using DRF serializers

**Implementation**: Enhanced serializers with proper validation
**Impact**: Better error handling and data integrity

#### 4. Error Handling - RESOLVED ⚠️

**Before**: Inconsistent error responses  
**After**: Standardized error handling across all endpoints

**Implementation**: Centralized error handling system
**Impact**: Consistent API responses

#### 5. CORS Configuration - RESOLVED 🌐

**Before**: Overly permissive CORS settings  
**After**: Restricted to specific origins

**Implementation**: Proper CORS middleware configuration
**Impact**: Enhanced security without breaking frontend

### Fixed Vulnerabilities (December 2024)

The following CVEs have been addressed in the latest updates:

#### High Severity (7.5+ CVSS)

- **CVE-2025-47273** (CVSS 7.7) - setuptools vulnerability
- **CVE-2024-6345** (CVSS 7.5) - setuptools vulnerability

#### Medium Severity (4.0-6.9 CVSS)

- **CVE-2024-0232** (CVSS 4.7) - Alpine SQLite vulnerability
- **CVE-2023-6992** (CVSS 4.0) - Alpine zlib vulnerability

### Mitigation Actions Taken

1. **Updated Base Images**:
   - Backend: Upgraded from `python:3.10-alpine3.18` to `python:3.10-alpine3.19`
   - Frontend: Upgraded from `nginx:stable-alpine3.17` to `nginx:stable-alpine3.19`

2. **Updated Dependencies**:
   - Added explicit setuptools version pinning (`>= 75.0.0`)
   - Enhanced pip upgrade process to include setuptools and wheel

3. **Security Best Practices**:
   - Regular dependency updates
   - Container image scanning
   - Minimal base images

4. **Application Security Enhancements**:
   - Secure password hashing with PBKDF2
   - Input validation and sanitization
   - Centralized error handling
   - CORS security configuration

### Security Improvements Summary

| Security Issue | Status | Implementation |
|----------------|--------|----------------|
| **Password Hashing** | ✅ **FIXED** | Django's secure hashing system |
| **Authentication** | ✅ **FIXED** | Secure password verification |
| **Input Validation** | ✅ **FIXED** | DRF serializer validation |
| **Error Handling** | ✅ **FIXED** | Centralized error system |
| **CORS Security** | ✅ **FIXED** | Restricted origins |
| **API Consistency** | ✅ **FIXED** | Standardized responses |

### Benefits of Security Implementation

#### Immediate Benefits

1. **Zero Downtime** - Application continues working immediately
2. **No Frontend Changes** - Existing UI works without modification
3. **Secure Passwords** - All passwords are now properly hashed
4. **Better Validation** - Enhanced input validation and error handling

#### Long-term Benefits

1. **Production Ready** - Secure enough for production deployment
2. **Maintainable** - Clean, well-structured code
3. **Scalable** - Foundation for future enhancements
4. **Compliant** - Follows Django security best practices

## Security Measures

### Application Security

#### Authentication & Authorization

- User authentication with secure session management
- User-specific data isolation
- Input validation on all endpoints
- SQL injection protection via Django ORM

#### Data Protection

- Password hashing using Django's built-in security features
- CSRF protection enabled
- XSS protection through Django's security middleware
- Secure headers configuration

#### API Security

- RESTful API design with proper HTTP methods
- Input validation and sanitization
- Rate limiting considerations
- CORS configuration for frontend-backend communication

### Infrastructure Security

#### Container Security

- Minimal Alpine Linux base images
- Regular base image updates
- Non-root user execution (where applicable)
- Security scanning of container images

#### Network Security

- Internal container communication
- Exposed ports only for necessary services
- No unnecessary network services

## Vulnerability Management Process

### Regular Security Updates

1. **Monthly Security Review**:
   - Check for new CVEs in dependencies
   - Update base images to latest stable versions
   - Review and update Python/Node.js packages

2. **Dependency Scanning**:
   - Use tools like `safety` for Python dependencies
   - Use `npm audit` for Node.js dependencies
   - Monitor security advisories

3. **Container Security**:
   - Regular base image updates
   - Security scanning of final images
   - Minimal attack surface

### Security Tools Integration

#### Recommended Tools

```bash
# Python security scanning
pip install safety
safety check

# Node.js security scanning
npm audit
npm audit fix

# Container security scanning
docker scan <image-name>
```

#### Automated Security Checks

```bash
# Add to CI/CD pipeline
docker-compose build
docker scan money-management-api
docker scan money-management-ui
```

## Security Configuration

### Django Security Settings

Key security configurations in `settings.py`:

```python
# Security settings
DEBUG = False  # In production
SECRET_KEY = 'your-secret-key'  # Use environment variables
ALLOWED_HOSTS = ['your-domain.com']  # Restrict allowed hosts

# Security middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    # ... other middleware
]

# Security headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

### Environment Variables

Use environment variables for sensitive data:

```bash
# Production environment variables
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=your-domain.com
DATABASE_URL=postgresql://user:pass@host:port/db
```

## Reporting Security Issues

### How to Report

If you discover a security vulnerability, please report it responsibly:

1. **Email**: Send details to [security-email]
2. **GitHub**: Create a private security advisory
3. **Include**:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### Response Timeline

- **Initial Response**: Within 24 hours
- **Assessment**: Within 72 hours
- **Fix Development**: Within 1 week
- **Public Disclosure**: After fix is deployed

## Security Checklist

### Before Deployment

- [ ] All dependencies updated to latest secure versions
- [ ] Security scanning completed
- [ ] Environment variables properly configured
- [ ] DEBUG mode disabled in production
- [ ] Database credentials secured
- [ ] SSL/TLS certificates configured
- [ ] Security headers enabled
- [ ] Container images scanned

### Regular Maintenance

- [ ] Monthly dependency updates
- [ ] Quarterly security review
- [ ] Annual penetration testing
- [ ] Regular backup verification
- [ ] Access log monitoring
- [ ] Performance monitoring

## Resources

### Security Documentation

- [Django Security](https://docs.djangoproject.com/en/stable/topics/security/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Docker Security](https://docs.docker.com/engine/security/)

### Security Tools

- [Safety](https://pyup.io/safety/) - Python dependency scanning
- [npm audit](https://docs.npmjs.com/cli/v8/commands/npm-audit) - Node.js security audit
- [Docker Scan](https://docs.docker.com/engine/scan/) - Container vulnerability scanning

---

**Last Updated**: December 2024  
**Next Review**: January 2025

## Known outstanding advisories (frontend)

The current UI dependencies include advisories that would require breaking upgrades to remediate. Since production uses a static build served by Nginx (no dev server), the immediate runtime risk is limited. We are deferring major upgrades for now and tracking them here.

Outstanding advisories from `npm audit` (moderate+):

- esbuild (affects vite <= 6.1.6)
  - Risk: Development server request exposure. Not applicable in production builds.
  - Mitigation: Use static Nginx build in production; avoid exposing `vite` dev server.
  - Upgrade path: `vite@^7` and compatible plugins.

- request / form-data / tough-cookie chain via `@vue/cli-shared-utils` → `vue-cli-plugin-component`
  - Risk: Prototype pollution and weak randomness in old transitive deps.
  - Mitigation: Plugin is build-time only; remove if not used.
  - Upgrade path: Replace/remove plugin; avoid deprecated `request` ecosystem.

- parse-git-config → git-user-name
  - Risk: Prototype pollution.
  - Mitigation: Build-time only; remove if not needed.
  - Upgrade path: Replace with maintained alternative or drop.

- rollup 3.x DOM clobbering gadget
  - Risk: Bundled script gadget; low likelihood when hashes/integrity not reused.
  - Upgrade path: Update via `vite@^7`.

- vue-template-compiler (no upstream fix)
  - Risk: Client-side XSS in compiler; affects development tooling only for Vue 2 templates.
  - Mitigation: Use vetted templates; no runtime exposure in compiled output.
  - Upgrade path: Migrate away from dependencies that pin this package; consider Vue 3-only toolchain.

Action items (planned):

1. Migrate to `vite@^7` and update `@vitejs/plugin-vue`, `vite-plugin-vuetify`, `unplugin-fonts`.
2. Remove `vue-cli-plugin-component` and any transitive `request` usage if not strictly required.
3. Replace `git-user-name`/`parse-git-config` usage or drop entirely.
4. Re-run `npm audit` post-migration and document residual items.

Note: The above are deferred because they introduce breaking changes to the build pipeline. Production risk remains low due to static asset serving via Nginx.
