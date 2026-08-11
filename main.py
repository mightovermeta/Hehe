import logging

import discord
from discord.ext import commands

import config
from db.database import Database

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("clash-card-bank")


class ClashCardBank(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)
        self.db: Database | None = None

    async def setup_hook(self):
        self.db = await Database.connect(config.DATABASE_URL)
        log.info("database pool ready")

        await self.load_extension("cogs.cards")

        if config.DEV_GUILD_ID:
            guild = discord.Object(id=config.DEV_GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            log.info("commands synced to dev guild %s", config.DEV_GUILD_ID)
        else:
            await self.tree.sync()
            log.info("commands synced globally, can take up to an hour to show up everywhere")

    async def close(self):
        if self.db:
            await self.db.close()
        await super().close()


bot = ClashCardBank()


@bot.event
async def on_ready():
    log.info("logged in as %s (%s), watching %d guilds", bot.user, bot.user.id, len(bot.guilds))


if __name__ == "__main__":
    bot.run(config.DISCORD_TOKEN)
