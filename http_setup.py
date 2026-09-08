from __future__ import annotations

import os

import requests

_PROXY_VARS = (
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
)


def disable_env_proxy() -> None:
    for name in _PROXY_VARS:
        os.environ.pop(name, None)


def no_proxy_session(session: requests.Session | None = None) -> requests.Session:
    session = session if session is not None else requests.Session()
    session.trust_env = False
    return session
