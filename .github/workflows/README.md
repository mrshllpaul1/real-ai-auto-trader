# CI/CD Pipeline Configuration

This directory contains GitHub Actions workflows for automated testing and deployment.

## Workflows

### `ci.yml` - Main CI/CD Pipeline

Triggered on:
- Push to `main` or `develop` branches
- Pull requests to `main`

#### Jobs:

1. **Lint & Code Quality**
   - Python linting with flake8
   - JavaScript/TypeScript linting with ESLint
   - Code formatting checks

2. **Backend Tests**
   - Unit tests with pytest
   - Integration tests
   - Code coverage reporting
   - MongoDB service container

3. **Frontend Tests**
   - Component tests
   - Build verification
   - Coverage reporting

4. **Security Scan**
   - Vulnerability scanning with Trivy
   - Dependency audit

5. **Integration Tests**
   - End-to-end API tests
   - Workflow tests

6. **Build**
   - Docker image building
   - Caching for faster builds

7. **Deploy**
   - Staging deployment (develop branch)
   - Production deployment (main branch)

## Required Secrets

Configure these secrets in your GitHub repository settings:

```
MONGO_URL           - MongoDB connection string
KRAKEN_API_KEY      - Kraken API key
KRAKEN_API_SECRET   - Kraken API secret
```

## Running Tests Locally

### Backend
```bash
cd backend
pip install pytest pytest-asyncio pytest-cov httpx
python -m pytest tests/ -v --cov=.
```

### Frontend
```bash
cd frontend
yarn test --coverage
```

## Coverage Targets

- Backend: 70%+ overall coverage
- Frontend: 60%+ component coverage
- Critical paths: 90%+ coverage

## Branch Strategy

- `main` - Production-ready code
- `develop` - Integration branch
- `feature/*` - Feature branches
- `bugfix/*` - Bug fix branches
