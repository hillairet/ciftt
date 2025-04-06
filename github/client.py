import logging
import sys
from collections import deque
from time import sleep, time
from typing import Deque
from urllib.parse import urljoin

import requests
from pandas import DataFrame, to_datetime
from pydantic import BaseModel

ONE_MIN = 60


class GitHubClient(BaseModel):
    api_key: str
    url: str = "https://api.github.com/"
    _api_requests_counter: int = 0
    _api_calls: Deque = deque()
    _api_rate_limit_per_min: int = 100

    def _get_request(self, endpoint: str, params: dict = {}) -> dict:
        self._throttle_api_calls()
        resp = requests.get(
            url=urljoin(self.url, endpoint),
            params=params,
            auth=(self.api_key, "X"),
        )
        if resp.json().get("code") != 200:
            logging.error(
                f"Timetask GET {endpoint} request status: "
                f"{resp.status_code}\n{resp.text}"
            )
            sys.exit(1)
        return resp.json()

    def _throttle_api_calls(self):
        current_time = time()

        # Remove calls that are older than the 1-minute window
        while self._api_calls and (current_time - self._api_calls[0]) > ONE_MIN:
            self._api_calls.popleft()

        if len(self._api_calls) >= self._api_rate_limit_per_min:
            # If 100 calls have been made in the last 60 seconds,
            # sleep until it's safe to make a new call
            time_to_wait = ONE_MIN - (current_time - self._api_calls[0])
            print(
                f"Timetask rate limit reached. Sleeping for {time_to_wait:.2f} seconds."
            )
            sleep(time_to_wait)
            # Remove the oldest call after sleeping
            self._api_calls.popleft()

        # Add the current time to the deque
        self._api_calls.append(current_time)
