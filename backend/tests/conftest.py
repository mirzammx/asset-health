import os
import tempfile

# must be set before app modules are imported
os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp()}/test.db"
os.environ["REFRESH_SECONDS"] = "0"
