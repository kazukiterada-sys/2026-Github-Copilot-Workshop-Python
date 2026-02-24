"""Configure the test path so that imports work without package installation."""
import sys
import os

# Add the pomodoro package root to the path so `import gamification` resolves.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
