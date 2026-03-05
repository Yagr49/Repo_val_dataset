import os
import asyncio

from pgnotify import await_pg_notifications

from backend.db_service import send_cvat_tag


def _database_url():
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    user = os.environ.get("POSTGRES_USER", "postgres")
    password = os.environ.get("POSTGRES_PASSWORD", "postgres")
    host = os.environ.get("POSTGRES_HOST", "127.0.0.1")
    port = os.environ.get("POSTGRES_PORT", "5432")
    db = os.environ.get("POSTGRES_DB", "postgres")
    return f"postgresql://{user}:{password}@{host}:{port}/{db}"


async def test():
    print("start")
    for notification in await_pg_notifications(
        _database_url(),
        ["sent_to_cvat_notify"],
    ):
        if notification.payload == "start":
            send_cvat_tag()


asyncio.run(test())
