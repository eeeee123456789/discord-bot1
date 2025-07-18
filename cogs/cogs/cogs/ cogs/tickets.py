# cogs/tickets.py

import discord
from discord.ext import commands
from config import active_tickets

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ticket(self, ctx):
        class TicketView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=None)

            @discord.ui.button(label="תמיכה טכנית", style=discord.ButtonStyle.primary)
            async def support_tech(self, interaction, button):
                await create_ticket(interaction, "תמיכה טכנית")

            @discord.ui.button(label="שאלה כללית", style=discord.ButtonStyle.primary)
            async def general_question(self, interaction, button):
                await create_ticket(interaction, "שאלה כללית")

        async def create_ticket(interaction, reason):
            guild = interaction.guild
            author = interaction.user
            category = discord.utils.get(guild.categories, name="טיקטים")
            if not category:
                category = await guild.create_category("טיקטים")

            existing = discord.utils.get(guild.text_channels, name=f"ticket-{author.name.lower()}")
            if existing:
                await interaction.response.send_message(f"כבר פתחת טיקט: {existing.mention}", ephemeral=True)
                return

            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                author: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                guild.me: discord.PermissionOverwrite(read_messages=True)
            }

            channel = await guild.create_text_channel(f"ticket-{author.name}", category=category, overwrites=overwrites)
            await channel.send(f"{author.mention}, טיקט נפתח בנושא: **{reason}**.")
            await interaction.response.send_message(f"טיקט נפתח: {channel.mention}", ephemeral=True)

            active_tickets[author.id] = channel.id

        await ctx.send("בחרו את סוג הטיקט לפתיחה:", view=TicketView())

    @commands.command()
    async def d(self, ctx):
        if ctx.author.id in active_tickets and ctx.channel.id == active_tickets[ctx.author.id]:
            await ctx.send("הטיקט יימחק בעוד דקה...")
            await discord.utils.sleep_until(discord.utils.utcnow() + discord.utils.timedelta(seconds=60))
            await ctx.channel.delete()
            del active_tickets[ctx.author.id]
        else:
            await ctx.send("פקודה זו זמינה רק בתוך הטיקט שלך.")

async def setup(bot):
    await bot.add_cog(Tickets(bot))
