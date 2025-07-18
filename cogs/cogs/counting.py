# cogs/counting.py

import discord
from discord.ext import commands
from config import counting_channel_name, last_number, last_user_id

class Counting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        global last_number, last_user_id
        if message.author.bot:
            return
        if isinstance(message.channel, discord.TextChannel) and message.channel.name == counting_channel_name:
            content = message.content.strip()
            if content.isdigit():
                number = int(content)
                if number != last_number + 1:
                    await message.delete()
                    await message.channel.send(f"{message.author.mention} המספר הבא הוא {last_number + 1}")
                    return
                if message.author.id == last_user_id:
                    await message.delete()
                    await message.channel.send(f"{message.author.mention} אסור לכתוב פעמיים ברצף!")
                    return
                last_number = number
                last_user_id = message.author.id
            else:
                await message.delete()
                await message.channel.send(f"{message.author.mention} רק מספרים מותרים כאן.")
                return

async def setup(bot):
    await bot.add_cog(Counting(bot))
