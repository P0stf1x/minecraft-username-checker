import requests
from dotenv import load_dotenv

from itertools import product, islice
import time
from datetime import datetime
import os
import sys

def main():
    load_dotenv()
    # ==================== ENVVARS ==================== #
    charset = os.getenv("SEARCH_CHARSET", "1234567890_qwertyuiopasdfghjklzxcvbnm")
    min_length = int(os.getenv("SEARCH_MIN_LENGTH", "3"))
    max_length = int(os.getenv("SEARCH_MAX_LENGTH", "3"))
    sleep_time = float(os.getenv("SEARCH_SLEEP_TIME", "1.0"))

    api_timeout = int(os.getenv("SEARCH_API_TIMEOUT", "60"))

    ntfy_enabled = os.getenv("NTFY_ENABLED", "false").lower() == "true"
    ntfy_host = os.getenv("NTFY_HOST", "https://ntfy.sh")
    ntfy_topic = os.getenv("NTFY_TOPIC")

    # Some time later
    # save_to_disk = os.getenv("SAVE_TO_DISK", "false").lower() == "true"
    # save_path = os.getenv("SAVE_PATH", "./results/")
    # ================================================= #

    if ntfy_enabled and ntfy_topic is None:
        print("ntfy topic is not set", file=sys.stderr)
        ntfy_enabled = False

    free_names = check_all_names(min_length, max_length, charset, sleep_time, api_timeout)

    if ntfy_enabled:
        ntfy_post_names(free_names, ntfy_host, ntfy_topic, api_timeout) # type: ignore stupid python


def get_minecraft_profiles(names: list, api_timeout: int):
    if len(names) > 10:
        raise ValueError("Checking more than 10 names at a time is not supported by tha API")

    response = requests.post(
        "https://api.mojang.com/profiles/minecraft",
        json=names,
        timeout=api_timeout,
    )
    response.raise_for_status()
    return response.json()


def check_all_names(min_length: int, max_length: int, charset: str, sleep_time: float, api_timeout: int):
    non_taken_names = []
    possible_names = generate_names(min_length, max_length, charset)
    while names_batch := list(islice(possible_names, 10)):
        time.sleep(sleep_time)
        print(f"Checking {names_batch}")
        result = get_minecraft_profiles(names_batch, api_timeout)
        existing = list(map(lambda i: i["name"].lower(), result)) # If account exists = name taken
        # There are false negatives for banned words that don't have an account but are not allowed, but eh it's ok
        for name in names_batch:
            if name.lower() not in existing:
                # Account doesn't exist
                print(f"Username not taken: {name}")
                non_taken_names.append(name)
    return non_taken_names


def generate_names(min_length: int, max_length: int, charset: str):
    if min_length <= 0:
        raise ValueError("min_length must be > 0")
    if max_length < min_length:
        raise ValueError("max_length must be >= min_length")

    for length in range(min_length, max_length + 1):
        for chars in product(charset, repeat=length):
            yield "".join(chars)


def ntfy_post_names(names: list, host: str, topic: str, api_timeout: float):
    now = datetime.now().strftime("%d.%m.%Y")
    requests.post(
        f"{host}/{topic}",
        data=f"{names}",
        headers={"Title": f"{now} found {len(names)} free names"},
        timeout=api_timeout,
    )


if __name__ == "__main__":
    main()
