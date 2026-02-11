#!/bin/bash

###############################################################################
# Dependency Update Script
# Safely updates Python and Node.js dependencies
# Usage: ./scripts/update-dependencies.sh [backend|frontend|all|audit|rollback]
###############################################################################

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

backup_file() {
    local file=$1
    if [ -f "$file" ]; then
        cp "$file" "${file}.backup.$(date +%Y%m%d_%H%M%S)"
        log_info "Backed up $file"
    fi
}

update_backend() {
    log_info "Updating backend dependencies..."
    cd "$PROJECT_ROOT/backend"
    backup_file "requirements.txt"
    log_info "Checking for outdated packages..."
    pip list --outdated || true
    log_info "Update critical packages with: pip install --upgrade <package>"
    log_success "Backend check complete!"
    cd "$PROJECT_ROOT"
}

update_frontend() {
    log_info "Updating frontend dependencies..."
    cd "$PROJECT_ROOT/frontend"
    backup_file "package.json"
    backup_file "package-lock.json"
    log_info "Checking for outdated packages..."
    npm outdated || true
    log_info "Run 'npm update' to update compatible versions"
    log_success "Frontend check complete!"
    cd "$PROJECT_ROOT"
}

security_audit() {
    log_info "Running security audit..."
    cd "$PROJECT_ROOT/frontend"
    npm audit || log_warning "Security vulnerabilities found"
    cd "$PROJECT_ROOT"
}

main() {
    local target=${1:-all}
    log_info "Dependency check for: $target"
    
    case $target in
        backend) update_backend ;;
        frontend) update_frontend ;;
        all) update_backend; update_frontend ;;
        audit) security_audit ;;
        *)
            log_error "Invalid target: $target"
            log_info "Usage: $0 [backend|frontend|all|audit]"
            exit 1 ;;
    esac
    
    log_success "Check complete!"
}

main "$@"
