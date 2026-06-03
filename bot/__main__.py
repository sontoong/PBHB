import asyncio
from bot.app import Application

app = Application()

if __name__ == "__main__":
    asyncio.run(app.start())
