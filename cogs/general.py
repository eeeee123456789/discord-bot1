# cogs/general.py

import discord
from discord.ext import commands
from config import server_open_datetime, user_invites

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx):
        await ctx.send("pong 🏓")

    @commands.command()
    async def say(self, ctx, *, text):
        await ctx.message.delete()
        await ctx.send(text)

    @commands.command()
    async def server_info(self, ctx):
        guild = ctx.guild
        embed = discord.Embed(title=f"מידע על {guild.name}", color=discord.Color.green())
        embed.add_field(name="תאריך יצירה", value=guild.created_at.strftime("%d/%m/%Y"))
        embed.add_field(name="מספר חברים", value=guild.member_count)
        await ctx.send(embed=embed)

    @commands.command()
    async def sh(self, ctx):
        joined = ctx.author.joined_at
        now = discord.utils.utcnow()
        days = (now - joined).days
        await ctx.send(f"אתה בשרת כבר {days} ימים.")

    @commands.command()
    async def countdown(self, ctx):
        now = discord.utils.utcnow()
        diff = server_open_datetime - now
        if diff.total_seconds() > 0:
            await ctx.send(f"נותרו {diff.days} ימים, {diff.seconds//3600} שעות ו-{(diff.seconds%3600)//60} דקות לפתיחת השרת.")
        else:
            await ctx.send("השרת כבר נפתח!")

    @commands.command()
    async def ar(self, ctx):
        try:
            await ctx.author.send("🔗 קישור לשיתוף השרת: https://discord.gg/takc7VcU")
            await ctx.message.add_reaction("✅")
        except:
            await ctx.send(f"{ctx.author.mention}, לא ניתן לשלוח הודעה בפרטי.")

    @commands.command()
    async def invite(self, ctx):
        await ctx.send("🔗 הזמינו חברים עם הקישור: https://discord.gg/takc7VcU")

    @commands.command()
    async def invites(self, ctx):
        count = user_invites.get(ctx.author.id, 0)
        await ctx.send(f"{ctx.author.mention}, הזמנת {count} משתמשים לשרת!")

    @commands.command()
    async def timeleft(self, ctx):
        now = discord.utils.utcnow()
        diff = server_open_datetime - now
        if diff.total_seconds() > 0:
            await ctx.send(f"{ctx.author.mention}, נותרו {diff.days} ימים, {diff.seconds//3600} שעות ו-{(diff.seconds%3600)//60} דקות!")
        else:
            await ctx.send(f"{ctx.author.mention}, הזמן עבר!")

async def setup(bot):
    await bot.add_cog(General(bot))
