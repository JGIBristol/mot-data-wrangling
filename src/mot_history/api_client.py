import urllib

from environs import Env
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session


class APIClient:
    def __init__(self) -> None:
        self.env = Env()
        self.env.read_env(".env")
        self.session = None

    def _ensure_authenticated(self) -> None:
        if not self.session:
            self.session = OAuth2Session(
                client=BackendApplicationClient(client_id=self.env("CLIENT_ID")),
            )
            self.session.fetch_token(
                token_url=self.env("TOKEN_URL"),
                client_secret=self.env("CLIENT_SECRET"),
                scope=self.env("SCOPE_URL"),
            )
            self.session.headers.update({"X-Api-Key": self.env("API_KEY")})

    def get(self, endpoint: str) -> dict:
        self._ensure_authenticated()
        response = self.session.get(urllib.parse.urljoin(self.env("API_URL"), endpoint))
        response.raise_for_status()
        return response.json()

    def get_vrm(self, vrm: str) -> dict:
        """Lookup MOT history for a single vehicle by `vrm`."""
        return self.get(f"/v1/trade/vehicles/registration/{vrm}")

    def get_vin(self, vin: str) -> dict:
        """Lookup MOT history for a single vehicle by `vin`."""
        return self.get(f"/v1/trade/vehicles/vin/{vin}")

    def get_bulk_urls(self) -> dict:
        """Get time-limited download URLs for bulk MOT history data."""
        return self.get("/v1/trade/vehicles/bulk-download")
