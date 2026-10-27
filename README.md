# Telegram product catalog

Stack: Next.js, FastAPI, aiogram, PostgreSQL and MinIO.

## Run locally

1. Copy .env.example to .env.
2. Set BOT_TOKEN, ADMIN_IDS (comma-separated numeric Telegram user IDs), BOT_API_SECRET and database/storage passwords.
3. Set WEBAPP_URL to your public HTTPS frontend URL. For development, use an HTTPS tunnel to localhost:3000.
4. Run: docker compose up --build
5. Open http://localhost:3000. Admins can use /create in a private bot chat and send a photo with a title in the caption. Use /cancel to cancel.

API docs: http://localhost:8000/docs. MinIO console: http://localhost:9001.

The catalog loads 24 products per page, fetching fresh API data on each request. Images are stored in MinIO and served through the frontend API proxy. Product creation requires X-Bot-Secret. Images are validated by Pillow and limited to MAX_IMAGE_MB (default 10).

## Operational limitations

The bot currently uses polling and in-memory conversation state: run one bot instance; restarting cancels unfinished product creation. Multiple backend instances share PostgreSQL and MinIO, but initial database schema creation should be run once before scaling. Use Alembic migrations for production schema changes.

This implementation is a catalog: prices, cart, checkout and orders are not implemented. Do not expose the MinIO console publicly. Never commit .env or bot tokens. Rotate any token previously pasted into source code through BotFather.

## Validation

Install backend/requirements.txt and bot/requirements.txt in a Python virtual environment. Run python -m compileall backend/app bot for syntax validation. For the frontend, run npm ci and npm run build inside frontend. Docker must be installed for full integration validation.
