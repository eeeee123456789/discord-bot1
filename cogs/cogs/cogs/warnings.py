# cogs/warnings.py

import discord
from discord.ext import commands, tasks
import json
import os
from datetime import datetime
from config import WARNING_ROLE_NAME, WARNINGS_FILE

if os.path.exists(WARNINGS_FILE):
    with open(WARNINGS_FILE, "r") as f:
        warnings = json.load(f)
else:
    warnings = {}

class Warnings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_warnings.start()

    @tasks.loop(minutes=1)
    async def check_warnings(self):
        now = datetime.now()
        to_remove = []

        for user_id, data in warnings.items():
            remove_time = datetime.strptime(data["remove_at"], "%Y-%m-%d %H:%M:%S")
            if now >= remove_time:
                guild = self.bot.get_guild(data["guild_id"])
                if guild:
                    member = guild.get_member(int(user_id))
                    if member:
                        role = discord.utils.get(guild.roles, name=WARNING_ROLE_NAME)
                        if role and role in member.roles:
                            await member.remove_roles(role)
                            print(f"הוסרה אזהרה מ־{member.name}")
                to_remove.append(user_id)

        for uid in to_remove:
            warnings.pop(uid)

        if to_remove:
            with open(WARNINGS_FILE, "w") as f:
                json.dump(warnings, f, indent=4)

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def warning(self, ctx, member: discord.Member, date: str, time: str = "00:00"):
        try:
            full_datetime = f"{date} {time}"
            until_date = datetime.strptime(full_datetime, "%d.%m.%y %H:%M")
        except ValueError:
            await ctx.send("❌ פורמט לא תקין. נסה למשל: !warning @משתמש 30.7.25 14:30")
            return

        now = datetime.now()
        if until_date <= now:
            await ctx.send("❌ התאריך והשעה כבר עברו.")
            return

        guild = ctx.guild
        warned_role = discord.utils.get(guild.roles, name=WARNING_ROLE_NAME)
        if not warned_role:
            warned_role = await guild.create_role(name=WARNING_ROLE_NAME)
            for channel in guild.channels:
                await channel.set_permissions(warned_role, send_messages=False)

        await member.add_roles(warned_role)
        await ctx.send(f"⚠️ {member.mention} קיבל אזהרה עד {until_date.strftime('%d.%m.%y %H:%M')}.")

        warnings[str(member.id)] = {
            "guild_id": guild.id,
            "remove_at": until_date.strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(WARNINGS_FILE, "w") as f:
            json.dump(warnings, f, indent=4)

async def setup(bot):
    await bot.add_cog(Warnings(bot))
