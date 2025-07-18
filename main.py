import discord
from discord.ext import commands
import os

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"הבוט מחובר בתור {bot.user}")
    channel = bot.get_channel(1370407515170537643)
    if channel:
        await channel.send("🤖 הבוט התחבר בהצלחה!")

# טוען את כל הקוגים מהתיקייה cogs
@bot.command()
@commands.has_permissions(administrator=True)
async def load_all(ctx):
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                print(f"טען את {filename}")
            except Exception as e:
                print(f"שגיאה בטעינת {filename}: {e}")
    await ctx.send("✅ כל המודולים נטענו!")

# טוען אוטומטית
async def load_extensions():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")

import asyncio
async def main():
    async with bot:
        await load_extensions()
        await bot.start(os.environ["DISCORD_TOKEN"])

asyncio.run(main())
