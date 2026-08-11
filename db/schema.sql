CREATE TABLE IF NOT EXISTS user_cards (
    guild_id BIGINT NOT NULL,
    user_id  BIGINT NOT NULL,
    card_key TEXT   NOT NULL,
    count    INT    NOT NULL DEFAULT 0 CHECK (count >= 0),
    PRIMARY KEY (guild_id, user_id, card_key)
);

CREATE TABLE IF NOT EXISTS wishlist (
    guild_id BIGINT NOT NULL,
    user_id  BIGINT NOT NULL,
    card_key TEXT   NOT NULL,
    added_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (guild_id, user_id, card_key)
);

CREATE TABLE IF NOT EXISTS trade_offers (
    guild_id BIGINT NOT NULL,
    user_id  BIGINT NOT NULL,
    card_key TEXT   NOT NULL,
    added_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (guild_id, user_id, card_key)
);

CREATE INDEX IF NOT EXISTS idx_user_cards_guild ON user_cards (guild_id);
CREATE INDEX IF NOT EXISTS idx_wishlist_guild ON wishlist (guild_id);
CREATE INDEX IF NOT EXISTS idx_trade_offers_guild ON trade_offers (guild_id);
