from typing import Annotated, Iterable, Optional

from colorama import Fore, Style

from .abstract import LogDownloader
from .constants import DEFAULT_FILES, DEFAULT_NUMBER_OF_ROUNDS, DEFAULT_ONLY_PLAYED, DEFAULT_CKEY_OUTPUT_PATH
from ..byond import canonicalize
from .. import scrubby
from ..constants import NEGATIVE_RESPONSES, POSITIVE_RESPONSES


class CkeyLogDownloaderException(Exception):
    """Uh oh, something went wrong"""


class CkeyLogDownloader(LogDownloader):
    """Downloads logs in which a ckey was present"""
    ckey: Annotated[Optional[str], "Canonical form of user's key, can be None"]
    only_played: Annotated[bool, "If ckey is set dictates if the log downloader only counts player rounds"]\
        = DEFAULT_ONLY_PLAYED
    number_of_rounds: Annotated[int, "The number of rounds to download"] = DEFAULT_NUMBER_OF_ROUNDS
    output_path: Annotated[str, "Where should we write the file to?"] = DEFAULT_CKEY_OUTPUT_PATH.format(ckey="output")
    filter_logs: Annotated[bool, "Should we filter the logs?"] = True

    def __init__(self, key: str = None, only_played: bool = DEFAULT_ONLY_PLAYED,
                 number_of_rounds: int = DEFAULT_NUMBER_OF_ROUNDS, output_path: str = None) -> None:
        self.ckey = canonicalize(key) if key else None
        self.only_played = only_played
        self.number_of_rounds = number_of_rounds
        self.output_path = output_path.format(ckey=self.ckey or "output")

    async def update_round_list(self) -> None:
        self.rounds = await scrubby.GetReceipts(self.ckey, self.number_of_rounds, self.only_played)

    def filter_lines(self, logs: Iterable[bytes]) -> Iterable[bytes]:
        if not self.filter_logs:
            for log in logs:
                yield log
        if not self.ckey:
            raise CkeyLogDownloaderException("Ckey was empty")
        ckey = self.ckey.lower().encode('utf-8')
        for log in logs:
            if ckey in log.lower():
                yield log

    @staticmethod
    def interactive() -> LogDownloader:
        ckey = input("CKEY: ").strip()
        while True:
            number_of_rounds = input(f"How many rounds? [{DEFAULT_NUMBER_OF_ROUNDS}] ")
            try:
                if not number_of_rounds.strip():
                    number_of_rounds = DEFAULT_NUMBER_OF_ROUNDS
                    break
                number_of_rounds = int(number_of_rounds) if number_of_rounds.isdigit() else int(number_of_rounds, 16)
                break
            except ValueError:
                print(f"{Fore.RED}Rounds should be an int in base 10 or 16{Fore.RESET}")
        print(f"Do you want to get only rounds in which they played? [y/{Style.BRIGHT}N{Style.RESET_ALL}] ", end="")
        only_played = input().lower() in POSITIVE_RESPONSES  # Input and colorama don't mix
        output_path = input(f"Where should I write the file? [{DEFAULT_CKEY_OUTPUT_PATH}] ")
        output_path = output_path or DEFAULT_CKEY_OUTPUT_PATH.format(ckey=ckey)
        downloader = CkeyLogDownloader(key=ckey, only_played=only_played,
                                       number_of_rounds=number_of_rounds, output_path=output_path)
        print("Which files do you want to download?")
        print("(separate the files with a comma, like so: attack.txt,game.txt,pda.txt)")
        file_list = [x.strip() for x in input(f"[{','.join(DEFAULT_FILES)}] ").split(',') if x.strip()]
        if file_list:
            downloader.files = file_list
        print(f"Want only the logs that this person is in? [{Style.BRIGHT}Y{Style.RESET_ALL}/n] ", end="")
        downloader.filter_logs = input().lower().strip() not in NEGATIVE_RESPONSES
        downloader.try_authenticate_interactive()
        return downloader
