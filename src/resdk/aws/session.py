""".. Ignore pydocstyle D400.

=======
Session
=======

Get refreshable boto3 session from temporary credentials.
"""


import logging
from typing import Callable, Dict

import boto3
import botocore

logger = logging.getLogger(__name__)


def get_refreshable_boto3_session(
    initial_credentials: Dict, refresh_credentials: Callable[[], Dict], region: str
) -> boto3.Session:
    """Get the botocore session object from temporary credentials.

    The term credentials refers to a dictionary containing the following keys:
    - "access_key"
    - "secret_key"
    - "token"
    - "expiry_time"

    :attr initial_credentials: credentials used when creating the session.

    :attr refresh_credentials: method returning a new set of credentials. It is
        called when existing credentials are about to expire.

    :raises KeyError: if credentials are in incorrect format.
    """
    session_credentials = (
        botocore.credentials.RefreshableCredentials.create_from_metadata(
            metadata=initial_credentials,
            refresh_using=refresh_credentials,
            method="custom-refreshable-session",
        )
    )
    botocore_session = botocore.session.get_session()
    # Currentty there is no way to set RefreshableCredentials to botocore
    # session besides using internal API. The type checking has to be ignored.
    botocore_session._credentials = session_credentials  # type: ignore
    botocore_session.set_config_variable("region", region)
    return boto3.Session(botocore_session=botocore_session)
