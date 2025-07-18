import discord
from discord.ext import commands

class Suggestions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.suggestion_channel_id = 123456789012345678  # יש להחליף למזהה הערוץ המתאים

    @commands.command(name='suggest')
    async def suggest(self, ctx, *, suggestion):
        channel = self.bot.get_channel(self.suggestion_channel_id)
        if channel is None:
            await ctx.send('ערוץ ההצעות לא נמצא, אנא פנה למנהל.')
            return

        embed = discord.Embed(
            title="הצעה חדשה",
            description=suggestion,
            color=discord.Color.blue(),
            timestamp=ctx.message.created_at
        )
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        embed.set_footer(text=f'מומלץ על ידי: {ctx.author}')

        message = await channel.send(embed=embed)
        await message.add_reaction('👍')
        await message.add_reaction('👎')
        await ctx.send('הצעתך נרשמה, תודה!')

def setup(bot):
    bot.add_cog(Suggestions(bot))
