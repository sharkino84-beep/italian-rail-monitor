"""Constants for Italian Rail Monitor."""

from datetime import timedelta

DOMAIN = "italian_rail_monitor"
PLATFORMS = ["sensor"]

CONF_TRAIN_NUMBER = "train_number"
CONF_ORIGIN_STATION_CODE = "origin_station_code"
CONF_BOARDING_STATION_CODE = "boarding_station_code"

DEFAULT_BOARDING_STATION_CODE = "S01425"

UPDATE_INTERVAL = timedelta(seconds=60)

API_BASE_URL = "http://www.viaggiatreno.it/infomobilita/resteasy/viaggiatreno"
API_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
}
