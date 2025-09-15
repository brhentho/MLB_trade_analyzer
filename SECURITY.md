# Security Policy

## Reporting Security Vulnerabilities

If you discover a security vulnerability in Baseball Trade AI, please report it responsibly by emailing security@baseballtradeai.com or by opening a private security advisory through GitHub.

**Please do not report security vulnerabilities through public issues.**

## Security Features

### Current Security Measures

1. **CORS Protection**: Properly configured Cross-Origin Resource Sharing
2. **Security Headers**: Comprehensive security headers including:
   - X-Content-Type-Options: nosniff
   - X-Frame-Options: DENY
   - X-XSS-Protection: 1; mode=block
   - Strict-Transport-Security (HTTPS only)
   - Content-Security-Policy
   - Referrer-Policy: strict-origin-when-cross-origin

3. **Environment-Based Security**: Different security configurations for development vs production
4. **API Documentation Protection**: Swagger docs only available in development
5. **Input Validation**: Pydantic models for request validation
6. **Database Security**: Supabase ORM prevents SQL injection

### Security Configuration

#### Required Environment Variables for Production

```bash
# Generate a strong secret for revalidation
REVALIDATION_SECRET=your-32-character-random-secret-here

# Set environment to production
ENVIRONMENT=production

# Ensure all API keys are set
OPENAI_API_KEY=your-openai-api-key
SUPABASE_URL=your-supabase-url
SUPABASE_SECRET_KEY=your-supabase-service-key
```

#### CORS Configuration

The application automatically configures CORS based on environment:
- **Development**: Allows localhost origins
- **Production**: Only allows specified production domains

To add your production domain:
```python
ALLOWED_ORIGINS = [
    "https://yourdomain.com",
    "https://www.yourdomain.com"
]
```

### Security Best Practices

#### For Developers

1. **Never commit secrets**: Use `.env` files and add them to `.gitignore`
2. **Use environment variables**: All sensitive configuration should be environment-based
3. **Validate inputs**: Use Pydantic models for all API inputs
4. **Rate limiting**: Implement rate limiting for public endpoints
5. **Authentication**: Implement proper authentication for sensitive operations

#### For Deployment

1. **Use HTTPS**: Always use HTTPS in production
2. **Set strong secrets**: Generate cryptographically strong secrets
3. **Monitor logs**: Implement security monitoring and alerting
4. **Regular updates**: Keep dependencies updated
5. **Database security**: Use connection pooling and proper credentials

### Security Checklist

Before deploying to production:

- [ ] All environment variables are set
- [ ] CORS is configured for your domain only
- [ ] HTTPS is enabled and certificate is valid
- [ ] Secrets are cryptographically strong (32+ characters)
- [ ] API documentation is disabled in production
- [ ] Rate limiting is enabled
- [ ] Security monitoring is configured
- [ ] Database credentials are secure
- [ ] All dependencies are up to date

### Known Security Considerations

1. **API Rate Limiting**: Currently implemented but may need tuning based on usage patterns
2. **Authentication**: Basic security measures in place, consider implementing JWT for user sessions
3. **Input Sanitization**: Additional sanitization may be needed for certain edge cases
4. **Monitoring**: Implement comprehensive security logging for production use

### Security Updates

This project follows security best practices and regularly updates dependencies. Security patches are prioritized and deployed as soon as possible.

### Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Contact

For security concerns or questions, contact:
- Email: security@baseballtradeai.com
- GitHub: Create a private security advisory