"""
Everything that touches Postgres lives in this one class. bot.py creates a
single Database instance in setup_hook and hangs it off the bot as bot.db,
then every command reaches it through cogs.cards.utils.get_pool().
"""

from __future__ import annotations

import pathlib
from dataclasses import dataclass, field

import asyncpg

from data.catalog import CARD_BY_KEY, CATEGORIES, TOTAL_CARDS

SCHEMA_PATH = pathlib.Path(__file__).parent / "schema.sql"


@dataclass
class ProgressSnapshot:
    by_category: dict[str, int] = field(default_factory=dict)
    owned_total: int = 0
    catalog_total: int = TOTAL_CARDS


@dataclass
class TradeMatch:
    other_id: int
    they_have_you_want: list[str]
    you_have_they_want: list[str]

    @property
    def mutual(self) -> bool:
        return bool(self.they_have_you_want) and bool(self.you_have_they_want)


class Database:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    @classmethod
    async def connect(cls, dsn: str) -> "Database":
        # sized with 100+ guilds in mind, bump max_size if the logs start
        # showing pool exhaustion warnings
        pool = await asyncpg.create_pool(dsn=dsn, min_size=5, max_size=20)
        instance = cls(pool)
        await instance._run_migrations()
        return instance

    async def close(self):
        await self.pool.close()

    async def _run_migrations(self):
        sql = SCHEMA_PATH.read_text()
        async with self.pool.acquire() as conn:
            await conn.execute(sql)

    # collection ------------------------------------------------------

    async def set_count(self, guild_id: int, user_id: int, card_key: str, amount: int) -> None:
        async with self.pool.acquire() as conn:
            if amount <= 0:
                await conn.execute(
                    "DELETE FROM user_cards WHERE guild_id = $1 AND user_id = $2 AND card_key = $3",
                    guild_id, user_id, card_key,
                )
                return
            await conn.execute(
                """
                INSERT INTO user_cards (guild_id, user_id, card_key, count)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (guild_id, user_id, card_key)
                DO UPDATE SET count = EXCLUDED.count
                """,
                guild_id, user_id, card_key, amount,
            )

    async def bump_count(self, guild_id: int, user_id: int, card_key: str, delta: int) -> int:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT count FROM user_cards WHERE guild_id = $1 AND user_id = $2 AND card_key = $3",
                guild_id, user_id, card_key,
            )
        current = row["count"] if row else 0
        updated = max(0, current + delta)
        await self.set_count(guild_id, user_id, card_key, updated)
        return updated

    async def fetch_collection(self, guild_id: int, user_id: int) -> dict[str, int]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT card_key, count FROM user_cards WHERE guild_id = $1 AND user_id = $2",
                guild_id, user_id,
            )
        return {row["card_key"]: row["count"] for row in rows}

    async def wipe_collection(self, guild_id: int, user_id: int) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM user_cards WHERE guild_id = $1 AND user_id = $2", guild_id, user_id
            )

    async def progress_for(self, guild_id: int, user_id: int) -> ProgressSnapshot:
        collection = await self.fetch_collection(guild_id, user_id)
        owned_keys = {key for key, amount in collection.items() if amount > 0}
        by_category = {category: 0 for category in CATEGORIES}
        for key in owned_keys:
            card = CARD_BY_KEY.get(key)
            if card:
                by_category[card.category] += 1
        return ProgressSnapshot(by_category=by_category, owned_total=len(owned_keys))

    async def top_collectors(self, guild_id: int, cap: int = 10) -> list[tuple[int, int]]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT user_id, COUNT(*) AS unique_owned
                FROM user_cards
                WHERE guild_id = $1 AND count > 0
                GROUP BY user_id
                ORDER BY unique_owned DESC
                LIMIT $2
                """,
                guild_id, cap,
            )
        return [(row["user_id"], row["unique_owned"]) for row in rows]

    # wishlist ----------------------------------------------------------

    async def add_want(self, guild_id: int, user_id: int, card_key: str) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO wishlist (guild_id, user_id, card_key) VALUES ($1, $2, $3) ON CONFLICT DO NOTHING",
                guild_id, user_id, card_key,
            )

    async def remove_want(self, guild_id: int, user_id: int, card_key: str) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM wishlist WHERE guild_id = $1 AND user_id = $2 AND card_key = $3",
                guild_id, user_id, card_key,
            )

    async def wants_for(self, guild_id: int, user_id: int) -> list[str]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT card_key FROM wishlist WHERE guild_id = $1 AND user_id = $2 ORDER BY added_at",
                guild_id, user_id,
            )
        return [row["card_key"] for row in rows]

    # trade offers --------------------------------------------------------

    async def add_offer(self, guild_id: int, user_id: int, card_key: str) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO trade_offers (guild_id, user_id, card_key) VALUES ($1, $2, $3) ON CONFLICT DO NOTHING",
                guild_id, user_id, card_key,
            )

    async def remove_offer(self, guild_id: int, user_id: int, card_key: str) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM trade_offers WHERE guild_id = $1 AND user_id = $2 AND card_key = $3",
                guild_id, user_id, card_key,
            )

    async def offers_for(self, guild_id: int, user_id: int) -> list[str]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT card_key FROM trade_offers WHERE guild_id = $1 AND user_id = $2 ORDER BY added_at",
                guild_id, user_id,
            )
        return [row["card_key"] for row in rows]

    # matching --------------------------------------------------------------

    async def trade_matches(
        self, guild_id: int, user_id: int, only_against: int | None = None
    ) -> list[TradeMatch]:
        async with self.pool.acquire() as conn:
            mine_want = {row["card_key"] for row in await conn.fetch(
                "SELECT card_key FROM wishlist WHERE guild_id = $1 AND user_id = $2", guild_id, user_id
            )}
            mine_offer = {row["card_key"] for row in await conn.fetch(
                "SELECT card_key FROM trade_offers WHERE guild_id = $1 AND user_id = $2", guild_id, user_id
            )}

            if not mine_want and not mine_offer:
                return []

            params = [guild_id, user_id]
            narrow_clause = ""
            if only_against is not None:
                narrow_clause = "AND user_id = $3"
                params.append(only_against)

            offer_rows = await conn.fetch(
                f"SELECT user_id, card_key FROM trade_offers WHERE guild_id = $1 AND user_id != $2 {narrow_clause}",
                *params,
            )
            want_rows = await conn.fetch(
                f"SELECT user_id, card_key FROM wishlist WHERE guild_id = $1 AND user_id != $2 {narrow_clause}",
                *params,
            )

        offers_by_user: dict[int, set[str]] = {}
        for row in offer_rows:
            offers_by_user.setdefault(row["user_id"], set()).add(row["card_key"])

        wants_by_user: dict[int, set[str]] = {}
        for row in want_rows:
            wants_by_user.setdefault(row["user_id"], set()).add(row["card_key"])

        everyone_else = set(offers_by_user) | set(wants_by_user)
        results: list[TradeMatch] = []
        for other_id in everyone_else:
            they_have_you_want = sorted(mine_want & offers_by_user.get(other_id, set()))
            you_have_they_want = sorted(mine_offer & wants_by_user.get(other_id, set()))
            if they_have_you_want or you_have_they_want:
                results.append(TradeMatch(other_id, they_have_you_want, you_have_they_want))

        results.sort(key=lambda entry: (not entry.mutual, -(len(entry.they_have_you_want) + len(entry.you_have_they_want))))
        return results
