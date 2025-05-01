import asyncio
from pprint import pprint

from config import amo_api


async def main():

    result = await amo_api.fetch_lead_data(15084243)
    pprint(result)
    return result

asyncio.run(main())
