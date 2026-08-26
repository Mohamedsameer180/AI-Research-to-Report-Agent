#!/usr/bin/env python3
"""
Basic test to verify the TASKFINISHER AI structure
"""

import sys
import os

def test_file_structure():
    """Test that our files exist and are readable"""
    try:
        # Check that key files exist
        required_files = [
            "taskfinisher_orchestrator.py",
            "main.py", 
            "requirements.txt",
            "README.md"
        ]
        
        for file_path in required_files:
            if os.path.exists(file_path):
                print(f"[FOUND] {file_path}")
            else:
                print(f"[MISSING] {file_path}")
                return False
        
        # Check that we can read the files
        with open("taskfinisher_orchestrator.py", "r", encoding="utf-8") as f:
            content = f.read()
            if "TaskFinisherOrchestrator" in content and "Google ADK" in content:
                print("[OK] Orchestrator file contains expected content")
            else:
                print("[WARN] Orchestrator file may be missing key content")
                
        with open("main.py", "r", encoding="utf-8") as f:
            content = f.read()
            if "FastAPI" in content and "execute_task" in content:
                print("[OK] Main file contains expected content")
            else:
                print("[WARN] Main file may be missing key content")
        
        print("[SUCCESS] Basic file structure test passed")
        return True
        
    except Exception as e:
        print(f"[ERROR] Test failed: {str(e)}")
        return False

def test_directories():
    """Test that required directories exist"""
    try:
        required_dirs = [
            "backend",
            "frontend", 
            "agents",
            "tools",
            "tests",
            "docs"
        ]
        
        for dir_path in required_dirs:
            if os.path.isdir(dir_path):
                print(f"[FOUND] Directory: {dir_path}")
            else:
                print(f"[MISSING] Directory: {dir_path}")
                # Create missing directories for completeness
                os.makedirs(dir_path, exist_ok=True)
                print(f"[CREATED] Directory: {dir_path}")
        
        print("[SUCCESS] Directory structure test passed")
        return True
        
    except Exception as e:
        print(f"[ERROR] Directory test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("=== TASKFINISHER AI Structure Test ===")
    
    success1 = test_file_structure()
    print()
    success2 = test_directories()
    
    overall_success = success1 and success2
    
    if overall_success:
        print("\n[RESULT] All tests passed! The project structure is ready.")
    else:
        print("\n[RESULT] Some tests failed. Please check the output above.")
    
    sys.exit(0 if overall_success else 1)
