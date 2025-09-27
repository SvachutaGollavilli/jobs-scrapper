# Update proxy list from free sources (wrapper script)

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the main proxy updater
from proxy_updater import main

if __name__ == "__main__":
    """
    This is a convenience script in the scripts/ folder
    that calls the main proxy_updater.py in the root
    """
    print("🔄 Running proxy updater from scripts folder...")
    main()

---
