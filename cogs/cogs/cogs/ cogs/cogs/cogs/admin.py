import discord
from discord.ext import commands

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='kick')
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        try:
            await member.kick(reason=reason)
            await ctx.send(f'{member} הודח בהצלחה מהשרת.')
        except Exception as e:
            await ctx.send(f'שגיאה בעת ניסיון להדיח: {e}')

    @commands.command(name='ban')
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        try:
            await member.ban(reason=reason)
            await ctx.send(f'{member} הועף מהשרת.')
        except Exception as e:
            await ctx.send(f'שגיאה בעת ניסיון להטיל חרם: {e}')

    @commands.command(name='unban')
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, *, member_name):
        banned_users = await ctx.guild.bans()
        member_name, member_discriminator = member_name.split('#')

        for ban_entry in banned_users:
            user = ban_entry.user

            if (user.name, user.discriminator) == (member_name, member_discriminator):
                await ctx.guild.unban(user)
                await ctx.send(f'{user} הוסר החרם.')
                return

        await ctx.send('המשתמש לא נמצא ברשימת החרמים.')

def setup(bot):
    bot.add_cog(Admin(bot))
