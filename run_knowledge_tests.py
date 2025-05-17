#!/usr/bin/env python3
"""
Quick test runner for knowledge repository tests
"""

import subprocess
import sys

# Run tests without coverage
cmd = [sys.executable, "-m", "pytest", "tests/unit/test_knowledge_service.py", "-v", "-p", "no:cov"]
result = subprocess.run(cmd, cwd="/Users/arielmuslera/Development/Projects/bluelabel-AIOS-V2")
sys.exit(result.returncode)