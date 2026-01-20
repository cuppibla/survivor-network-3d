
import sys
import os

print(f"Python executable: {sys.executable}")
print(f"User Base: {os.path.expanduser('~')}")
print("sys.path:")
for p in sys.path:
    print(f"  {p}")

try:
    import google
    print(f"google package: {google}")
    print(f"google path: {google.__path__}")
except ImportError as e:
    print(f"Failed to import google: {e}")

try:
    import google.adk
    print(f"google.adk package: {google.adk}")
    print("SUCCESS: google.adk imported")
except ImportError as e:
    print(f"Failed to import google.adk: {e}")

try:
    from google.adk.agents import Agent
    print("SUCCESS: Agent imported")
except ImportError as e:
    print(f"Failed to import Agent: {e}")
