#!/usr/bin/env python3
"""
Quick setup script for Valley Catholic Basketball Stats
This script helps you get started quickly by:
1. Checking Python version
2. Creating virtual environment
3. Installing dependencies
4. Setting up .env file
5. Running initial tests
"""

import sys
import os
import subprocess
import platform
from pathlib import Path


def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")


def check_python_version():
    """Check if Python version is 3.11 or higher."""
    print_header("Checking Python Version")
    version = sys.version_info
    print(f"Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print("❌ Error: Python 3.11 or higher is required!")
        print("   Please upgrade Python and try again.")
        return False
    
    print("✅ Python version is compatible")
    return True


def create_virtual_environment():
    """Create a virtual environment."""
    print_header("Creating Virtual Environment")
    
    venv_path = Path(".venv")
    if venv_path.exists():
        print("⚠️  Virtual environment already exists")
        response = input("   Recreate it? (y/N): ").strip().lower()
        if response == 'y':
            import shutil
            shutil.rmtree(venv_path)
            print("   Removed existing virtual environment")
        else:
            print("   Keeping existing virtual environment")
            return True
    
    try:
        subprocess.run([sys.executable, "-m", "venv", ".venv"], check=True)
        print("✅ Virtual environment created successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to create virtual environment")
        return False


def get_pip_command():
    """Get the pip command for the current platform."""
    if platform.system() == "Windows":
        return str(Path(".venv") / "Scripts" / "pip.exe")
    else:
        return str(Path(".venv") / "bin" / "pip")


def install_dependencies():
    """Install required dependencies."""
    print_header("Installing Dependencies")
    
    pip_cmd = get_pip_command()
    
    try:
        # Upgrade pip first
        print("Upgrading pip...")
        subprocess.run([pip_cmd, "install", "--upgrade", "pip"], check=True)
        
        # Install requirements
        print("Installing project dependencies...")
        subprocess.run([pip_cmd, "install", "-r", "requirements.txt"], check=True)
        
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return False


def setup_env_file():
    """Set up the .env file."""
    print_header("Setting Up Environment Variables")
    
    env_path = Path(".env")
    env_example_path = Path(".env.example")
    
    if env_path.exists():
        print("⚠️  .env file already exists")
        response = input("   Overwrite it? (y/N): ").strip().lower()
        if response != 'y':
            print("   Keeping existing .env file")
            return True
    
    if not env_example_path.exists():
        print("❌ .env.example file not found")
        return False
    
    # Copy .env.example to .env
    with open(env_example_path, 'r') as f:
        content = f.read()
    
    with open(env_path, 'w') as f:
        f.write(content)
    
    print("✅ .env file created from template")
    print("\n⚠️  IMPORTANT: Edit .env and add your OpenAI API key!")
    print("   Get your API key from: https://platform.openai.com/api-keys")
    
    return True


def run_tests():
    """Run basic tests to verify setup."""
    print_header("Running Tests")
    
    # Check if tests directory exists
    if not Path("tests").exists():
        print("⚠️  Tests directory not found, skipping tests")
        return True
    
    response = input("Run tests now? (Y/n): ").strip().lower()
    if response == 'n':
        print("Skipping tests")
        return True
    
    try:
        if platform.system() == "Windows":
            python_cmd = str(Path(".venv") / "Scripts" / "python.exe")
        else:
            python_cmd = str(Path(".venv") / "bin" / "python")
        
        subprocess.run([python_cmd, "-m", "pytest", "tests/", "-v"], check=True)
        print("✅ Tests passed successfully")
        return True
    except subprocess.CalledProcessError:
        print("⚠️  Some tests failed (this may be expected)")
        return True
    except FileNotFoundError:
        print("⚠️  pytest not found, skipping tests")
        return True


def print_next_steps():
    """Print next steps for the user."""
    print_header("Setup Complete! 🎉")
    
    if platform.system() == "Windows":
        activate_cmd = ".venv\\Scripts\\activate"
        python_cmd = "python"
    else:
        activate_cmd = "source .venv/bin/activate"
        python_cmd = "python3"
    
    print("Next steps:")
    print(f"\n1. Activate the virtual environment:")
    print(f"   {activate_cmd}")
    print(f"\n2. Edit .env and add your OpenAI API key:")
    print(f"   OPENAI_API_KEY=your_key_here")
    print(f"\n3. Run the application:")
    print(f"   {python_cmd} main.py")
    print(f"\n4. Open your browser:")
    print(f"   http://localhost:5000")
    print("\nFor more information, see README.md")
    print("\n" + "=" * 60 + "\n")


def main():
    """Main setup function."""
    print("\n🏀 Valley Catholic Basketball Stats - Quick Setup 🏀\n")
    
    # Check if we're in the right directory
    if not Path("main.py").exists():
        print("❌ Error: main.py not found!")
        print("   Please run this script from the project root directory.")
        sys.exit(1)
    
    # Run setup steps
    steps = [
        ("Checking Python version", check_python_version),
        ("Creating virtual environment", create_virtual_environment),
        ("Installing dependencies", install_dependencies),
        ("Setting up environment", setup_env_file),
    ]
    
    for step_name, step_func in steps:
        if not step_func():
            print(f"\n❌ Setup failed at: {step_name}")
            print("   Please fix the error and run the script again.")
            sys.exit(1)
    
    # Optional: Run tests
    run_tests()
    
    # Print next steps
    print_next_steps()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
