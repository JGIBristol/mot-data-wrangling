"""Allow authenticated access to the MOT History API provided by the DVSA.

The main work is done in the APIClient class. See its docstring for more
information.
"""

import itertools
import urllib
from pathlib import Path

import requests
from environs import Env
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from .. import console, paths

PROGRESSBAR_COLUMNS = [
    TextColumn("[progress.description]{task.description}"),
    BarColumn(),
    DownloadColumn(),
    TransferSpeedColumn(),
    TimeRemainingColumn(),
]


class APIClient:
    """Allow authenticated access to the MOT History API provided by the DVSA.

    To access the API you must have the following credentials: a CLIENT_ID,
    CLIENT_SECRET, API_KEY, SCOPE_URL, TOKEN_URL and API_URL. You should set
    these in the .env file in the root directory of the project (or as
    environment variables, which will override entries in the .env file). See
    the file .env.sample for examples.

    The above credentials are provided by the DVSA when you register for the
    API. See <https://documentation.history.mot.api.gov.uk> to register, and for
    more information about the structure of the data returned.

    The API uses OAuth 2.0 with the client credentials flow for authentication
    and authorisation. This class handles the authentication and basic API calls
    for you.
    """

    def __init__(self) -> None:
        self.env = Env()
        self.env.read_env()

    def _ensure_authenticated(self) -> None:
        if getattr(self, "session", None) is None:
            self.session = OAuth2Session(
                client=BackendApplicationClient(client_id=self.env("DVSA_CLIENT_ID"))
            )
            self.session.fetch_token(
                token_url=self.env("DVSA_TOKEN_URL"),
                client_secret=self.env("DVSA_CLIENT_SECRET"),
                scope=self.env("DVSA_SCOPE_URL"),
            )
            self.session.headers.update({"X-Api-Key": self.env("DVSA_API_KEY")})

    def _get(self, endpoint_url: str) -> dict:
        self._ensure_authenticated()
        response = self.session.get(
            urllib.parse.urljoin(
                self.env("DVSA_API_URL"),
                endpoint_url,
            )
        )
        response.raise_for_status()
        return response.json()

    def get_vrm(self, vrm: str) -> dict:
        """Lookup MOT history for a single vehicle by registration.

        Args:
            vrm: The vehicle registration mark (VRM) of the vehicle.

        Returns:
            The MOT history data for the vehicle.
        """
        return self._get(f"/v1/trade/vehicles/registration/{vrm}")

    def get_vin(self, vin: str) -> dict:
        """Lookup MOT history for a single vehicle by VIN.

        Args:
            vin: The vehicle identification number (VIN) of the vehicle.

        Returns:
            The MOT history data for the vehicle.
        """
        return self._get(f"/v1/trade/vehicles/vin/{vin}")

    def get_bulk_urls(self) -> dict:
        """Get time-limited download URLs for bulk MOT history data.

        Returns:
            The bulk and delta download URLs, including file sizes.
        """
        return self._get("/v1/trade/vehicles/bulk-download")

    def download_bulk_data(self, destination_dir: Path | str = paths.data_dir) -> list[Path]:
        """Download bulk MOT history data files.

        Existing files are skipped, and incomplete downloads are resumed.

        Args:
            destination_dir: The directory to download the files to. Defaults to
            the project's `data` directory.

        Returns:
            The downloaded file paths.
        """
        destination_dir = Path(destination_dir)
        bulk_urls = self.get_bulk_urls()
        downloaded_files = [
            _download_file(
                url=bulk_file["downloadUrl"],
                destination=destination_dir / Path(bulk_file["filename"]).name,
                expected_size=bulk_file["fileSize"],
            )
            for bulk_file in itertools.chain(bulk_urls["bulk"], bulk_urls["delta"])
        ]
        return downloaded_files


def _download_file(url: str, destination: Path | str, expected_size: int | None = None) -> Path:
    """Download a file from a URL to a destination path, skipping if the
    file already exists, or resuming if the file is incomplete.

    Args:
        url: The URL of the file to download.
        destination: The path to save the file to.
        expected_size (optional): The expected size of the file in bytes.
            Required if resuming incomplete downloads is desired.

    Returns:
        The path to the downloaded file.
    """
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)

    # Skip files we don't need to download
    if (
        destination.exists()
        and destination.is_file()
        and (expected_size is None or destination.stat().st_size == expected_size)
    ):
        console.print(
            f"File {destination.name} already exists. Skipping download.", highlight=False
        )
        return destination

    # We need to be able to resume large downloads if they get interrupted
    headers = {}
    initial_size = 0
    if destination.exists() and expected_size is not None:
        initial_size = destination.stat().st_size
        headers["Range"] = f"bytes={initial_size}-"

    with requests.get(url, stream=True, headers=headers) as request:
        request.raise_for_status()
        total_size = int(request.headers.get("content-length", 0))

        # Stream the content into the destination file with a nice progress bar
        with destination.open("ab") as f:
            with Progress(*PROGRESSBAR_COLUMNS, console=console) as progress:
                task = progress.add_task(
                    f"Downloading {destination.name}", total=total_size, completed=initial_size
                )
                for chunk in request.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        progress.update(task, advance=len(chunk))

    return destination
