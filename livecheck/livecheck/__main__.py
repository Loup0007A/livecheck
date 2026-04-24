"""Allow: python -m livecheck <command>"""
from .cli import main
import sys
sys.exit(main())
