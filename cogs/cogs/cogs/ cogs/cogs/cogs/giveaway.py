# cogs/giveaway.py

import discord
from discord.ext import commands
import random
from config import active_draw, participants

class Giveaway(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def start246(self, ctx):
        global active_draw, participants
        if active_draw:
            await ctx.send("הגרלה כבר פעילה.")
            return
        active_draw = True
        participants.clear()
        await ctx.send("🎉 הגרלה התחילה! השתמשו ב-!gty כדי להיכנס.")

    @commands.command()
    async def gty(self, ctx):
        if not active_draw:
            await ctx.send("אין הגרלה פעילה.")
            return
        if ctx.author.id in participants:
            await ctx.send("כבר נכנסת.")
        else:
            participants.add(ctx.author.id)
            await ctx.send("נכנסת להגרלה!")

    @commands.command()
    async def exitdraw(self, ctx):
        if ctx.author.id in participants:
            participants.remove(ctx.author.id)
            await ctx.send("יצאת מההגרלה.")
        else:
            await ctx.send("לא היית בפנים.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def winner246(self, ctx):
        if not participants:
            await ctx.send("אין משתתפים.")
            return
        winner_id = random.choice(list(participants))
        winner = ctx.guild.get_member(winner_id)
        await ctx.send(f"🎉 הזוכה הוא {winner.mention}!")
        active_draw = False
        participants.clear()

async def setup(bot):
    await bot.add_cog(Giveaway(bot))
