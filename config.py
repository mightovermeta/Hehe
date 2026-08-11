import os

from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
DATABASE_URL = os.environ["DATABASE_URL"]

# Point this at a single test server while building things out, slash
# commands land there instantly instead of waiting on the global sync delay.
DEV_GUILD_ID = os.environ.get("DEV_GUILD_ID")
DEV_GUILD_ID = int(DEV_GUILD_ID) if DEV_GUILD_ID else None
