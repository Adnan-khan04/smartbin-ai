#!/usr/bin/env python3
"""
SmartBin AI - Local Development Setup Script
Handles environment setup, database initialization, and service startup
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def print_header(text):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def print_success(text):
    """Print success message"""
    print(f"✓ {text}")

def print_error(text):
    """Print error message"""
    print(f"✗ {text}")

def print_info(text):
    """Print info message"""
    print(f"ℹ {text}")

def check_file(file_path, description):
    """Check if a file exists"""
    if Path(file_path).exists():
        print_success(f"{description} found")
        return True
    else:
        print_error(f"{description} not found at {file_path}")
        return False

def setup_env():
    """Setup environment files"""
    print_header("Setting up environment")
    
    env_file = ".env"
    env_example = ".env.example"
    
    # Check if .env exists
    if os.path.exists(env_file):
        print_info(".env already exists, skipping creation")
        return True
    
    # Check if .env.example exists
    if not os.path.exists(env_example):
        print_error(".env.example not found")
        return False
    
    # Copy template to .env
    print_info(f"Creating {env_file} from {env_example}")
    try:
        with open(env_example, 'r') as src, open(env_file, 'w') as dst:
            dst.write(src.read())
        print_success(f"{env_file} created")
        return True
    except Exception as e:
        print_error(f"Failed to create {env_file}: {e}")
        return False

def check_docker():
    """Check if Docker is installed and running"""
    print_header("Checking Docker")
    
    try:
        subprocess.run(["docker", "version"], capture_output=True, check=True)
        print_success("Docker is installed")
    except FileNotFoundError:
        print_error("Docker is not installed")
        return False
    except subprocess.CalledProcessError:
        print_error("Docker is not running")
        return False
    
    try:
        subprocess.run(["docker-compose", "version"], capture_output=True, check=True)
        print_success("Docker Compose is installed")
        return True
    except FileNotFoundError:
        print_error("Docker Compose is not installed")
        return False
    except subprocess.CalledProcessError:
        print_error("Docker Compose is not available")
        return False

def build_services():
    """Build Docker services"""
    print_header("Building Docker services")
    
    try:
        print_info("This may take several minutes...")
        subprocess.run(
            ["docker-compose", "build"],
            check=True
        )
        print_success("Docker services built successfully")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to build services: {e}")
        return False
    except FileNotFoundError:
        print_error("docker-compose command not found")
        return False

def start_services():
    """Start Docker services"""
    print_header("Starting services")
    
    try:
        print_info("Starting database, backend, and frontend...")
        subprocess.run(
            ["docker-compose", "up", "-d"],
            check=True
        )
        print_success("Services started")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to start services: {e}")
        return False

def wait_for_services():
    """Wait for services to be ready"""
    print_header("Waiting for services to be ready")
    
    import time
    
    endpoints = [
        ("Backend", "http://127.0.0.1:8000/health"),
        ("Frontend", "http://127.0.0.1:5173/"),
    ]
    
    max_attempts = 30
    attempt = 0
    
    while attempt < max_attempts:
        all_ready = True
        for name, url in endpoints:
            try:
                import urllib.request
                urllib.request.urlopen(url, timeout=5)
                print_success(f"{name} is ready")
            except Exception:
                all_ready = False
                print_info(f"Waiting for {name}...")
                break
        
        if all_ready:
            return True
        
        attempt += 1
        time.sleep(1)
    
    print_error("Services did not start in time")
    return False

def show_info():
    """Show application information"""
    print_header("SmartBin AI is ready!")
    
    print_info("Access the application at:")
    print(f"  Frontend:    http://localhost:5173")
    print(f"  Backend API: http://localhost:8000")
    print(f"  API Docs:    http://localhost:8000/api/docs")
    print(f"  Backend:     http://localhost:8000/api (from frontend)")
    
    print_info("\nDefault credentials (after registration):")
    print(f"  Username: testuser")
    print(f"  Password: Test@1234")
    
    print_info("\nUseful commands:")
    print(f"  View logs:    docker-compose logs -f")
    print(f"  Stop:         docker-compose down")
    print(f"  Restart:      docker-compose restart")
    print(f"  Clean:        docker-compose down -v")
    
    print_info("\nDocumentation:")
    print(f"  Deployment:   ./DEPLOYMENT.md")
    print(f"  API Docs:     ./docs/API.md")
    print(f"  Setup Guide:  ./docs/SETUP.md")

def main():
    """Main setup function"""
    print_header("SmartBin AI - Local Development Setup")
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    print_info(f"Working directory: {os.getcwd()}")
    
    # Perform setup steps
    steps = [
        ("Environment Setup", setup_env),
        ("Docker Check", check_docker),
        ("Build Services", build_services),
        ("Start Services", start_services),
        ("Wait for Services", wait_for_services),
    ]
    
    failed = False
    for step_name, step_func in steps:
        if not step_func():
            print_error(f"{step_name} failed")
            failed = True
            break
    
    if failed:
        print_error("Setup incomplete. Please fix the errors above.")
        sys.exit(1)
    
    show_info()
    print_success("Setup complete! Happy coding! 🎉")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_error("\nSetup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)
