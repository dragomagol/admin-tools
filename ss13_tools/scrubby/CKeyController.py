"""Wrapper for the CKeyController on Scrubby"""
# pylint: disable=invalid-name
from aiohttp import ClientSession

from .round_data import RoundData
from .constants import PLAYER_ROUNDS_URL
from ..constants import USER_AGENT


class ScrubbyException(Exception):
    """Wuh oh, scrubby died"""


async def GetReceipts(ckey: str, number_of_rounds: int, only_played: bool = False) -> list[RoundData]:
    """Calls the scrubby API and retrieves the specified number of rounds"""
    data = {
        "ckey": ckey,
        "startingRound": 999999,  # that's how scrubby does it, sue Bobbah, not me
        "limit": number_of_rounds
    }
    # ckey is specified twice, but it seems like the url ckey does not matter at all
    # https://github.com/bobbahbrown/ScrubbyWebPublic/blob/d71ad368e156f56524bf7ec323685ca29af35baa/Controllers/CKeyController.cs#L78
    async with ClientSession(headers={"User-Agent": USER_AGENT}) as session:
        resp = await session.post(PLAYER_ROUNDS_URL.format(ckey=ckey), json=data)
        if not resp.ok:
            raise ScrubbyException("Scrubby errored with code " + str(resp.status))
        if await resp.read() == b"[]":
            raise ScrubbyException("CKEY could not be found")
        if not only_played:
            return await RoundData.from_scrubby_response_async(resp)

        played_in = []
        while True:
            rounds = await RoundData.from_scrubby_response_async(resp)
            if not rounds:
                return played_in
            for round_data in rounds:
                if round_data.playedInRound:
                    played_in.append(round_data)
                if len(played_in) == number_of_rounds:
                    return played_in
            data["startingRound"] = rounds[-1].roundID
            resp = await session.post(PLAYER_ROUNDS_URL.format(ckey=ckey), json=data)
