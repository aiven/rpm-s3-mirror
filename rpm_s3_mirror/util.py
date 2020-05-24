# Copyright (c) 2020 Aiven, Helsinki, Finland. https://aiven.io/

import datetime
import hashlib
import os
import shutil
from os.path import join, basename

import requests
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3 import Retry


def sha256(content):
    return hashlib.sha256(content).hexdigest()


def validate_checksum(path, checksum_type, checksum) -> None:
    if checksum_type != "sha256":
        raise ValueError("Only sha256 checksums are currently supported")
    with open(path, "rb") as f:
        local_checksum = sha256(content=f.read())
        assert checksum == local_checksum, f"{path}: expected {checksum} found {local_checksum}"


def get_requests_session() -> Session:
    session = requests.session()
    retries = Retry(total=5, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
    session.mount("http://", HTTPAdapter(max_retries=retries))
    session.mount("https://", HTTPAdapter(max_retries=retries))
    return session


def download_file(temp_dir: str, url: str, session: Session = None) -> str:
    session = session or get_requests_session()
    with session.get(url, stream=True) as request:
        request.raise_for_status()
        out_path = join(temp_dir, os.path.basename(url))
        with open(out_path, "wb") as f:
            shutil.copyfileobj(request.raw, f)
        return out_path


def now(*, microsecond=False) -> datetime.datetime:
    current_time = datetime.datetime.now(datetime.timezone.utc)
    if microsecond:
        return current_time
    return current_time.replace(microsecond=0)


def get_snapshot_path(base_path, snapshot_id, file_path):
    return join(get_snapshot_directory(base_path, snapshot_id), "repodata", basename(file_path))


def get_snapshot_directory(base_path, snapshot_id):
    return join(base_path, "snapshots", snapshot_id)
