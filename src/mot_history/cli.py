import itertools
import os
from pathlib import Path

import click
import requests
from rich.console import Console
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from .api_client import APIClient

client = APIClient()
console = Console()


@click.group()
def cli():
    """This is a CLI to use the MOT History API."""


@cli.command()
@click.argument("vrm")
def vrm(vrm: str):
    """Lookup MOT history for a single vehicle by VRM (vehicle registration mark)."""
    console.print(client.get_vrm(vrm))


@cli.command()
@click.argument("vin")
def vin(vin: str):
    """Lookup MOT history for a single vehicle by VIN."""
    console.print(client.get_vin(vin))


@cli.command()
def bulk_urls():
    """Get time-limited download URLs for bulk MOT history data."""
    console.print(client.get_bulk_urls())


@cli.command()
def bulk_data_download():
    """Downloads bulk MOT history data via the time-limited download URLs."""
    bulk_urls = client.get_bulk_urls()
    for bulk_file in itertools.chain(bulk_urls["bulk"], bulk_urls["delta"]):
        download_file(
            url=bulk_file["downloadUrl"],
            destination=Path("data") / Path(bulk_file["filename"]).name,
            expected_size=bulk_file["fileSize"],
        )


def download_file(url, destination, expected_size=None):
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)

    # Skip files we don't need to download
    if (
        destination.exists()
        and destination.is_file()
        and (expected_size is None or destination.stat().st_size == expected_size)
    ):
        console.print(f"File {destination.name} already exists. Skipping download.")
        return destination

    # We need to be able to resume large downloads if they get interrupted
    headers = {}
    initial_size = 0
    if destination.exists():
        initial_size = destination.stat().st_size
        headers["Range"] = f"bytes={initial_size}-"

    with requests.get(url, stream=True, headers=headers) as request:
        request.raise_for_status()
        total_size = int(request.headers.get("content-length", 0))

        with destination.open("ab") as f:
            with Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                DownloadColumn(),
                TransferSpeedColumn(),
                TimeRemainingColumn(),
            ) as progress:
                task = progress.add_task(
                    f"Downloading {destination.name}",
                    total=total_size,
                    completed=initial_size,
                )
                for chunk in request.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        progress.update(task, advance=len(chunk))

    return destination


if __name__ == "__main__":
    cli()
