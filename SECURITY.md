# Security Guidelines

This document outlines security best practices for the AI Crypto Auto Trading Platform, with a focus on protecting API keys, credentials, and sensitive data.

## 🔐 Secret Management

### Environment Variables

All sensitive data (API keys, secrets, passwords) **MUST** be stored in environment variables, never hardcoded in source code.

#### Required Setup

1. **Copy the template file:**
   ```bash
   cp .env.example .env
   ```

2. **Fill in your actual credentials:**
   - Open `.env` in a secure text editor
   - Replace placeholder values with real API keys
   - Never commit `.env` to version control (it's in `.gitignore`)

3. **Verify `.env` is ignored:**
   ```bash
   git status
   # .env should NOT appear in untracked files
   ```

### Critical Environment Variables

#### Encryption Key (CRITICAL)
```bash
ENCRYPTION_KEY=<your-fernet-key>
```

⚠️ **WARNING:** This key encrypts Kraken API credentials in the database.
- **Generate once:** `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
- **Never regenerate** - losing this key means losing all stored credentials
- **Backup securely** - store in password manager or secret vault
- **Production:** Use AWS Secrets Manager, HashiCorp Vault, or similar

#### Database Connection
```bash
MONGO_URL=mongodb://localhost:27017
DB_NAME=crypto_trading_db
```

⚠️ **Production:** Never use default credentials. Use:
- Strong authentication
- Encrypted connections (TLS/SSL)
- Network isolation (VPC, firewall rules)

## 🔑 API Key Management

### Exchange API Keys

#### Kraken (Primary Exchange)

1. **Generate API Keys:**
   - Visit: https://www.kraken.com/u/security/api
   - Click "Generate New Key"

2. **Required Permissions:**
   - ✅ Query Funds
   - ✅ Create & Modify Orders
   - ✅ Cancel/Close Orders
   - ❌ **NEVER** enable "Withdraw" permission

3. **Security Settings:**
   - Enable 2FA on your Kraken account
   - Set IP whitelist if possible
   - Use API key nonce window for replay protection
   - Regularly review API key usage in Kraken dashboard

4. **Storage:**
   - Store in `.env` file or environment variables
   - App encrypts keys before storing in database
   - Never log or display full API keys

#### Other Exchanges (Binance, Coinbase)

Follow similar principles:
- Minimum required permissions only
- Never enable withdrawal permissions
- Use IP whitelisting where available
- Enable 2FA on exchange accounts

### Market Data APIs

Less sensitive but still important:
- CoinMarketCap, CoinStats, TwelveData, etc.
- Free tiers may have rate limits
- Keep keys private to avoid quota theft

### LLM & AI Services

```bash
EMERGENT_LLM_KEY=<your-key>
```
- Used for AI strategy generation
- Shared key - usage may be metered
- Never expose in client-side code or logs

## 🛡️ Security Best Practices

### Development

1. **Never commit secrets:**
   ```bash
   # Good - using environment variable
   api_key = os.getenv('API_KEY')
   
   # Bad - hardcoded
   api_key = "sk-12345..."
   ```

2. **Use `.env.example` for templates:**
   - Document all required variables
   - Use placeholder values
   - Update when adding new secrets

3. **Local testing:**
   - Use paper trading mode for development
   - Test with minimal funds initially
   - Never use production credentials in tests

### Production Deployment

1. **Environment Variable Management:**
   - Use platform-specific secret management (Vercel Secrets, Heroku Config Vars, etc.)
   - Never store secrets in CI/CD logs
   - Rotate keys regularly (quarterly recommended)

2. **Access Control:**
   - Principle of least privilege
   - Separate dev/staging/production credentials
   - Audit access logs regularly

3. **Monitoring:**
   - Enable API key usage alerts
   - Monitor for suspicious trading patterns
   - Set up anomaly detection

4. **Encryption:**
   - HTTPS/TLS for all API communications
   - Encrypted database connections
   - Encrypted backups

### CORS Configuration

```bash
# Development
CORS_ORIGINS=*

# Production - restrict to your domain(s)
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

## 🚨 Incident Response

### If API Keys are Compromised

1. **Immediate Actions:**
   ```
   ⚠️ STOP ALL TRADING IMMEDIATELY
   ⚠️ Disable API keys on exchange (Kraken, Binance, etc.)
   ⚠️ Check recent trades for unauthorized activity
   ⚠️ Change all passwords with 2FA
   ```

2. **Investigate:**
   - Review access logs
   - Check git history for accidental commits
   - Scan codebase for exposed secrets

3. **Remediate:**
   - Generate new API keys
   - Update `.env` with new keys
   - Update encryption key if database was compromised
   - Review and improve security practices

4. **Prevent:**
   - Enable pre-commit hooks
   - Use git-secrets or similar tools
   - Conduct security training

### Reporting Security Issues

If you discover a security vulnerability:

1. **DO NOT** open a public GitHub issue
2. **DO NOT** share details publicly
3. **Contact:** [Your security contact email]
4. **Provide:** Detailed description, steps to reproduce, potential impact

## 🔧 Security Tools

### Pre-commit Hooks

Install to prevent accidental secret commits:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install
```

Hooks automatically check for:
- Hardcoded secrets
- Private keys
- AWS credentials
- API tokens

### Secret Scanning

Tools to scan for exposed secrets:
- **git-secrets** - AWS secret scanner
- **truffleHog** - Git secret scanner
- **detect-secrets** - Yelp's secret scanner
- **GitHub Secret Scanning** - Built into GitHub

### Code Review Checklist

Before merging code:
- [ ] No hardcoded API keys or secrets
- [ ] All credentials use environment variables
- [ ] `.env.example` updated with new variables
- [ ] No secrets in logs or error messages
- [ ] API keys have minimum required permissions
- [ ] CORS origins restricted in production

## 📚 Additional Resources

- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [Kraken API Security](https://support.kraken.com/hc/en-us/articles/360000919733-API-Security)
- [12 Factor App - Config](https://12factor.net/config)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)

## 🔄 Key Rotation Schedule

Recommended rotation schedule:

| Credential Type | Rotation Frequency | Priority |
|----------------|-------------------|----------|
| Exchange API Keys | Quarterly | Critical |
| Encryption Key | Annually | Critical |
| Database Credentials | Annually | High |
| Market Data APIs | Annually | Medium |
| Email API Keys | Annually | Low |

## 📞 Emergency Contacts

In case of security incident:

- **Exchange Support:**
  - Kraken: https://support.kraken.com
  - Binance: https://www.binance.com/en/support

- **Database Provider:** [Your MongoDB support]
- **Hosting Provider:** [Your hosting support]

---

**Last Updated:** February 2026
**Review Frequency:** Quarterly
**Next Review:** May 2026
