# cogs/private_rooms.py

import discord
from discord.ext import commands
import asyncio
from config import private_rooms

class PrivateRooms(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def create(self, ctx):
        guild = ctx.guild
        author = ctx.author
        if author.id in private_rooms:
            await ctx.send("כבר יש לך חדר פרטי.")
            return

        category = discord.utils.get(guild.categories, name="חדרים פרטיים")
        if not category:
            category = await guild.create_category("חדרים פרטיים")

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False, connect=False),
            author: discord.PermissionOverwrite(read_messages=True, connect=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, connect=True)
        }

        text = await guild.create_text_channel(f"פרטי-{author.name}", category=category, overwrites=overwrites)
        voice = await guild.create_voice_channel(f"פרטי-{author.name}", category=category, overwrites=overwrites)

        private_rooms[author.id] = {"text": text.id, "voice": voice.id}
        await ctx.send(f"{author.mention}, החדר שלך נוצר.")

        await asyncio.sleep(14400)  # 4 שעות
        if guild.get_channel(text.id):
            await text.delete()
        if guild.get_channel(voice.id):
            await voice.delete()
        private_rooms.pop(author.id, None)

    @commands.command()
    async def delete(self, ctx):
        if ctx.author.id not in private_rooms:
            await ctx.send("אין לך חדר פרטי.")
            return
        text = ctx.guild.get_channel(private_rooms[ctx.author.id]["text"])
        voice = ctx.guild.get_channel(private_rooms[ctx.author.id]["voice"])
        if text:
            await text.delete()
        if voice:
            await voice.delete()
        del private_rooms[ctx.author.id]
        await ctx.send("החדר נמחק.")

async def setup(bot):
    await bot.add_cog(PrivateRooms(bot))
