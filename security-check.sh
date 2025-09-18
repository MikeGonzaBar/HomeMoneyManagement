#!/bin/bash

# Security Check Script for Home Money Management
# This script helps identify and fix security vulnerabilities

echo "🔒 Home Money Management - Security Check"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    if [ $2 -eq 0 ]; then
        echo -e "${GREEN}✅ $1${NC}"
    else
        echo -e "${RED}❌ $1${NC}"
    fi
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

echo ""
echo "1. Checking Python Dependencies Security..."
echo "-------------------------------------------"

# Check if we're in the right directory
if [ -f "API/requirements.txt" ]; then
    cd API
    
    # Check for safety tool
    if command -v safety &> /dev/null; then
        echo "Running safety check on Python dependencies..."
        safety check --json > safety-report.json 2>/dev/null
        if [ $? -eq 0 ]; then
            print_status "No known security vulnerabilities found in Python dependencies" 0
        else
            print_warning "Security vulnerabilities found in Python dependencies"
            echo "Check safety-report.json for details"
        fi
    else
        print_warning "Safety tool not installed. Install with: pip install safety"
        echo "Manual check: Review requirements.txt for known vulnerabilities"
    fi
    
    # Check setuptools version
    echo ""
    echo "Checking setuptools version..."
    pip show setuptools | grep Version
    cd ..
else
    print_warning "API/requirements.txt not found. Run from project root directory."
fi

echo ""
echo "2. Checking Node.js Dependencies Security..."
echo "--------------------------------------------"

if [ -f "UI/home-money-management/package.json" ]; then
    cd UI/home-money-management
    
    echo "Running npm audit..."
    npm audit --audit-level=moderate > npm-audit-report.txt 2>&1
    if [ $? -eq 0 ]; then
        print_status "No security vulnerabilities found in Node.js dependencies" 0
    else
        print_warning "Security vulnerabilities found in Node.js dependencies"
        echo "Check npm-audit-report.txt for details"
        echo "Run 'npm audit fix' to automatically fix issues"
    fi
    
    cd ../..
else
    print_warning "UI/home-money-management/package.json not found."
fi

echo ""
echo "3. Checking Docker Images Security..."
echo "-------------------------------------"

# Check if Docker is running
if command -v docker &> /dev/null; then
    if docker info &> /dev/null; then
        echo "Docker is running. Checking for security scanning capability..."
        
        # Check if docker scan is available
        if docker scan --help &> /dev/null; then
            print_status "Docker scan capability available" 0
            echo "To scan images, run:"
            echo "  docker-compose build"
            echo "  docker scan money-management-api"
            echo "  docker scan money-management-ui"
        else
            print_warning "Docker scan not available. Consider using Snyk or other container scanning tools"
        fi
    else
        print_warning "Docker is not running or not accessible"
    fi
else
    print_warning "Docker not installed"
fi

echo ""
echo "4. Checking Base Image Versions..."
echo "----------------------------------"

echo "Current base images:"
if [ -f "API/Dockerfile" ]; then
    echo "Backend: $(grep '^FROM' API/Dockerfile)"
fi

if [ -f "UI/home-money-management/Dockerfile" ]; then
    echo "Frontend: $(grep '^FROM.*nginx' UI/home-money-management/Dockerfile)"
fi

echo ""
echo "5. Security Recommendations..."
echo "-----------------------------"

echo "📋 Security Checklist:"
echo "  □ Update base images to latest stable versions"
echo "  □ Run 'pip install --upgrade pip setuptools wheel'"
echo "  □ Review and update all dependencies monthly"
echo "  □ Enable security headers in production"
echo "  □ Use environment variables for sensitive data"
echo "  □ Regular security scanning in CI/CD pipeline"
echo "  □ Monitor security advisories for all dependencies"

echo ""
echo "6. Recent Security Updates Applied..."
echo "------------------------------------"

echo "✅ Updated Alpine Linux base images to 3.19"
echo "✅ Added explicit setuptools version pinning (>= 75.0.0)"
echo "✅ Enhanced pip upgrade process"
echo "✅ Created SECURITY.md documentation"

echo ""
echo "🔒 Security Check Complete!"
echo "=========================="
echo ""
echo "For detailed security information, see SECURITY.md"
echo "For ongoing security monitoring, run this script monthly"
