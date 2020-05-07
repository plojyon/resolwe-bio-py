""".. Ignore pydocstyle D400.

=========
Constants
=========

ReSDK constants.

"""

CHUNK_SIZE = 8000000  # 8MB

RESOLWE_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"

# Permissions here should be ordered from most to least important
ALL_PERMISSIONS = ["owner", "share", "edit", "view"]
