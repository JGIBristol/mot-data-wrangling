import click

from . import console
from .api_client import APIClient

client = APIClient()


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
    client.download_bulk_data()


if __name__ == "__main__":
    cli()
