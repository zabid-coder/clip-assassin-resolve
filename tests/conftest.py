"""Keep all test databases and library state separate from the user's app data."""
import os
from pathlib import Path
import tempfile
os.environ['CLIP_ASSASSIN_DB_PATH']=str(Path(tempfile.mkdtemp(prefix='clip-assassin-tests-'))/'settings.db')
