from app.integrations.google.gee_auth import get_gee
from functools import lru_cache


class GEEClient:
    def __init__(self):
        self.ee = get_gee()

    def get_ee(self):
        return self.ee


@lru_cache()
def get_gee_client():
    return GEEClient()