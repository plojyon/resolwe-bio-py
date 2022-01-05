"""RNATables utility functions."""

import asyncio
import json
from io import BytesIO
from urllib.parse import urljoin

import aiohttp
import pandas as pd
from requests.exceptions import HTTPError


async def _download_file(uri, url, session, parser):
    """Download and parse single file."""
    async with session.get(url) as response:
        response.raise_for_status()
        with BytesIO() as f:
            f.write(await response.content.read())
            f.seek(0)
            data = parser(f, uri)
    return data


def _uri_to_url(resolwe, uris):
    """Convert uris to urls."""
    response = resolwe.session.post(
        urljoin(resolwe.url, "resolve_uris/"),
        json={"uris": list(uris)},
        auth=resolwe.auth,
    )
    response.raise_for_status()
    return json.loads(response.content.decode("utf-8"))


async def _batch_download(resolwe, uris, parser) -> pd.DataFrame:
    """Download multiple files defined by their uri asynchronously."""
    try:
        uri_to_url = _uri_to_url(resolwe, uris)
    except HTTPError:
        return pd.DataFrame()

    async with aiohttp.ClientSession() as session:
        futures = [
            _download_file(uri, url, session, parser)
            for uri, url in uri_to_url.items()
            if url
        ]
        data = await asyncio.gather(*futures)

    if data:
        return pd.concat(data, axis=1).T.sort_index()
    return pd.DataFrame()


def batch_download(resolwe, uris, parser) -> pd.DataFrame:
    """Download multiple files defined by their uri asynchronously."""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_batch_download(resolwe, uris, parser))
