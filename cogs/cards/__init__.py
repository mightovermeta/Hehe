"""
Entry point for the cards extension. Builds the /cards command tree,
pulls in every module under commands/ so each one attaches itself to the
groups below, then exposes the setup(bot) coroutine bot.py calls through
bot.load_extension("cogs.cards").

Heads up for whoever adds commands later: don't name a command coroutine
setup, that name is reserved down at the bottom of this file for the
extension loader hook. If a command genuinely needs to be called setup
from the user's side, rename the Python function itself (something like
run_setup or open_setup) and just point the slash command's name kwarg
at "setup" instead.
"""

from discord import app_commands

card_group_ = app_commands.Group(name="cards", description="Track and trade Clash of Clans cards")
want_group_ = app_commands.Group(name="wishlist", description="Cards you are chasing", parent=card_group_)
offer_group_ = app_commands.Group(name="offer", description="Spares you are willing to give up", parent=card_group_)

from .commands import (  # noqa: E402
    card_set,
    card_add,
    card_collection,
    card_progress,
    card_leaderboard,
    card_reset,
    wishlist_add,
    wishlist_remove,
    wishlist_list,
    offer_add,
    offer_remove,
    offer_list,
    swap,
)


async def setup(bot):
    bot.tree.add_command(card_group_)
