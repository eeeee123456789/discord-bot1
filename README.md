import discord
from discord.ext import commands, tasks
import asyncio
import random
from datetime import datetime
import json
import os

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

# משתנים גלובליים
user_invites = {}
active_tickets = {}
private_rooms = {}
counting_channel_name = "counting"
server_open_datetime = datetime(2025, 6, 30, 12, 0, 0)

last_number = 0
last_user_id = None

active_draw = False
participants = set()

WARNING_ROLE_NAME = "Warned"
WARNINGS_FILE = "warnings.json"

# טען את רשימת האזהרות אם קיימת
if os.path.exists(WARNINGS_FILE):
    with open(WARNINGS_FILE, "r") as f:
        warnings = json.load(f)
else:
    warnings = {}

# אירועים
@bot.event
async def on_ready():
    print(f"הבוט מחובר בתור {bot.user}")
    check_warnings.start()

@bot.event
async def on_member_join(member):
    guild = member.guild
    channel = discord.utils.get(guild.text_channels, name="ברוכים-הבאים")
    if channel:
        await channel.send(f"ברוך הבא {member.mention} לשרת שלנו! 🎉")

# מערכת ספירה בערוץ ספציפי
@bot.event
async def on_message(message):
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

    # אם מישהו רשם בדיוק pong
    if message.content.lower() == "pong":
        await message.channel.send("!ping")

    if message.content.lower() == "!ping":
        await message.channel.send("pong")

    await bot.process_commands(message)

# לולאת בדיקה להסרת אזהרות
@tasks.loop(minutes=1)
async def check_warnings():
    now = datetime.now()
    to_remove = []

    for user_id, data in warnings.items():
        remove_time = datetime.strptime(data["remove_at"], "%Y-%m-%d %H:%M:%S")
        if now >= remove_time:
            guild = bot.get_guild(data["guild_id"])
            if guild:
                member = guild.get_member(int(user_id))
                if member:
                    role = discord.utils.get(guild.roles, name=WARNING_ROLE_NAME)
                    if role in member.roles:
                        await member.remove_roles(role)
                        print(f"הוסרה אזהרה מ־{member.name}")
            to_remove.append(user_id)

    for uid in to_remove:
        warnings.pop(uid)

    if to_remove:
        with open(WARNINGS_FILE, "w") as f:
            json.dump(warnings, f, indent=4)

# פקודות בסיסיות
@bot.command()
async def ping(ctx):
    await ctx.send("pong 🏓")

@bot.command()
async def say(ctx, *, text):
    await ctx.message.delete()
    await ctx.send(text)

@bot.command()
async def server_info(ctx):
    guild = ctx.guild
    embed = discord.Embed(title=f"מידע על {guild.name}", color=discord.Color.green())
    embed.add_field(name="תאריך יצירה", value=guild.created_at.strftime("%d/%m/%Y"))
    embed.add_field(name="מספר חברים", value=guild.member_count)
    await ctx.send(embed=embed)

@bot.command()
async def sh(ctx):
    joined = ctx.author.joined_at
    now = datetime.utcnow()
    days = (now - joined).days
    await ctx.send(f"אתה בשרת כבר {days} ימים.")

@bot.command()
async def countdown(ctx):
    now = datetime.utcnow()
    diff = server_open_datetime - now
    if diff.total_seconds() > 0:
        await ctx.send(f"נותרו {diff.days} ימים, {diff.seconds//3600} שעות ו-{(diff.seconds%3600)//60} דקות לפתיחת השרת.")
    else:
        await ctx.send("השרת כבר נפתח!")

@bot.command()
async def ar(ctx):
    try:
        await ctx.author.send("🔗 קישור לשיתוף השרת: https://discord.gg/takc7VcU")
        await ctx.message.add_reaction("✅")
    except:
        await ctx.send(f"{ctx.author.mention}, לא ניתן לשלוח הודעה בפרטי.")

@bot.command()
async def invite(ctx):
    await ctx.send("🔗 הזמינו חברים עם הקישור: https://discord.gg/takc7VcU\nהשתמשו ב-!invites ו-!timeleft כדי לעקוב!")

@bot.command()
async def invites(ctx):
    count = user_invites.get(ctx.author.id, 0)
    await ctx.send(f"{ctx.author.mention}, הזמנת {count} משתמשים לשרת!")

@bot.command()
async def timeleft(ctx):
    now = datetime.utcnow()
    diff = server_open_datetime - now
    if diff.total_seconds() > 0:
        await ctx.send(f"{ctx.author.mention}, נותרו {diff.days} ימים, {diff.seconds//3600} שעות ו-{(diff.seconds%3600)//60} דקות!")
    else:
        await ctx.send(f"{ctx.author.mention}, הזמן עבר!")

# פקודת אזהרה עם תאריך ושעה
@bot.command()
@commands.has_permissions(manage_roles=True)
async def warning(ctx, member: discord.Member, date: str, time: str = "00:00"):
    """נותן אזהרה למשתמש עד תאריך ושעה מסוימים"""
    try:
        full_datetime = f"{date} {time}"
        until_date = datetime.strptime(full_datetime, "%d.%m.%y %H:%M")
    except ValueError:
        await ctx.send("❌ פורמט לא תקין. נסה למשל: `!warning @משתמש 30.7.25 14:30`")
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
# מערכת טיקטים עם כפתורי בחירה
@bot.command()
async def ticket(ctx):
    class TicketView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)

        @discord.ui.button(label="תמיכה טכנית", style=discord.ButtonStyle.primary, custom_id="support_tech")
        async def support_tech(self, interaction, button):
            await create_ticket(interaction, "תמיכה טכנית")

        @discord.ui.button(label="שאלה כללית", style=discord.ButtonStyle.primary, custom_id="general_question")
        async def general_question(self, interaction, button):
            await create_ticket(interaction, "שאלה כללית")

    await ctx.send("בחרו את סוג הטיקט לפתיחה:", view=TicketView())

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

    def check(msg):
        return msg.channel == channel and msg.content == "!d" and msg.author == author

    try:
        msg = await bot.wait_for('message', check=check, timeout=3600)
        await asyncio.sleep(60)
        await channel.delete()
        del active_tickets[author.id]
    except asyncio.TimeoutError:
        pass

@bot.command()
async def d(ctx):
    if ctx.author.id in active_tickets and ctx.channel.id == active_tickets[ctx.author.id]:
        await ctx.send("הטיקט יימחק בעוד דקה...")
        await asyncio.sleep(60)
        await ctx.channel.delete()
        del active_tickets[ctx.author.id]
    else:
        await ctx.send("פקודה זו זמינה רק בתוך הטיקט שלך.")

# מערכת חדרים פרטיים (טקסט וקול)
@bot.command()
async def create(ctx):
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

@bot.command()
async def add(ctx, member: discord.Member):
    if ctx.author.id not in private_rooms:
        await ctx.send("אין לך חדר פרטי.")
        return
    text = ctx.guild.get_channel(private_rooms[ctx.author.id]["text"])
    voice = ctx.guild.get_channel(private_rooms[ctx.author.id]["voice"])
    await text.set_permissions(member, read_messages=True, send_messages=True)
    await voice.set_permissions(member, connect=True)
    await ctx.send(f"{member.mention} נוסף לחדר.")

@bot.command()
async def remove(ctx, member: discord.Member):
    if ctx.author.id not in private_rooms:
        await ctx.send("אין לך חדר פרטי.")
        return
    text = ctx.guild.get_channel(private_rooms[ctx.author.id]["text"])
    voice = ctx.guild.get_channel(private_rooms[ctx.author.id]["voice"])
    await text.set_permissions(member, overwrite=None)
    await voice.set_permissions(member, overwrite=None)
    await ctx.send(f"{member.mention} הוסר מהחדר.")

@bot.command()
async def setname(ctx, *, name):
    if ctx.author.id not in private_rooms:
        await ctx.send("אין לך חדר פרטי.")
        return
    text = ctx.guild.get_channel(private_rooms[ctx.author.id]["text"])
    voice = ctx.guild.get_channel(private_rooms[ctx.author.id]["voice"])
    await text.edit(name=name)
    await voice.edit(name=name)
    await ctx.send("שם החדר עודכן.")

@bot.command()
async def makepublic(ctx):
    if ctx.author.id not in private_rooms:
        await ctx.send("אין לך חדר פרטי.")
        return
    text = ctx.guild.get_channel(private_rooms[ctx.author.id]["text"])
    voice = ctx.guild.get_channel(private_rooms[ctx.author.id]["voice"])
    await text.set_permissions(ctx.guild.default_role, read_messages=True)
    await voice.set_permissions(ctx.guild.default_role, connect=True)
    await ctx.send("החדר הפך לציבורי.")

@bot.command()
async def makeprivate(ctx):
    if ctx.author.id not in private_rooms:
        await ctx.send("אין לך חדר פרטי.")
        return
    text = ctx.guild.get_channel(private_rooms[ctx.author.id]["text"])
    voice = ctx.guild.get_channel(private_rooms[ctx.author.id]["voice"])
    await text.set_permissions(ctx.guild.default_role, read_messages=False)
    await voice.set_permissions(ctx.guild.default_role, connect=False)
    await ctx.send("החדר הפך לפרטי.")

@bot.command()
async def delete(ctx):
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

@bot.command()
async def userlimit(ctx, limit: int):
    if ctx.author.id not in private_rooms:
        await ctx.send("אין לך חדר פרטי.")
        return
    voice = ctx.guild.get_channel(private_rooms[ctx.author.id]["voice"])
    await voice.edit(user_limit=limit)
    await ctx.send(f"הגבלת משתמשים הוגדרה ל-{limit}")

# פקודות ניהול חדרים פרטיים למנהלים
@bot.command()
async def transfer(ctx, member: discord.Member):
    author = ctx.author
    if author.id not in private_rooms:
        await ctx.send(f"{author.mention}, אין לך חדר פרטי להעביר.")
        return
    if member.id in private_rooms:
        await ctx.send(f"{member.mention} כבר יש לו חדר פרטי. לא ניתן להעביר.")
        return
    private_rooms[member.id] = private_rooms.pop(author.id)
    private_rooms[member.id]["owner"] = member.id
    await ctx.send(f"{author.mention} העביר את בעלות החדר הפרטי ל-{member.mention}.")

@bot.command()
@commands.has_permissions(administrator=True)
async def forcedelete(ctx, member: discord.Member):
    guild = ctx.guild
    if member.id not in private_rooms:
        await ctx.send(f"{ctx.author.mention}, ל-{member.mention} אין חדר פרטי למחוק.")
        return
    text_channel = guild.get_channel(private_rooms[member.id]["text"])
    voice_channel = guild.get_channel(private_rooms[member.id]["voice"])
    if text_channel:
        await text_channel.delete()
    if voice_channel:
        await voice_channel.delete()
    del private_rooms[member.id]
    await ctx.send(f"חדר פרטי של {member.mention} נמחק בכפייה.")

# מערכת הגרלות
@bot.command()
@commands.has_permissions(administrator=True)
async def start246(ctx):
    global active_draw, participants
    if active_draw:
        await ctx.send("הגרלה כבר פעילה.")
    return
    active_draw = True
    participants.clear()
    await ctx.send("🎉 הגרלה התחילה! השתמשו ב-!gty כדי להיכנס.")

@bot.command()
async def gty(ctx):
    if not active_draw:
        await ctx.send("אין הגרלה פעילה.")
        return
    if ctx.author.id in participants:
        await ctx.send("כבר נכנסת.")
    else:
        participants.add(ctx.author.id)
        await ctx.send("נכנסת להגרלה!")

@bot.command()
async def exitdraw(ctx):
    if ctx.author.id in participants:
        participants.remove(ctx.author.id)
        await ctx.send("יצאת מההגרלה.")
    else:
        await ctx.send("לא היית בפנים.")

@bot.command()
@commands.has_permissions(administrator=True)
async def winner246(ctx):
    global active_draw, participants
    if not participants:
        await ctx.send("אין משתתפים.")
        return
    winner_id = random.choice(list(participants))
    winner = ctx.guild.get_member(winner_id)
    await ctx.send(f"🎉 הזוכה הוא {winner.mention}!")
    active_draw = False
    participants.clear()

# פקודות ניהול כלליות
@bot.command()
@commands.has_permissions(administrator=True)
async def hide_server(ctx):
    guild = ctx.guild
    for channel in guild.channels:
        await channel.set_permissions(guild.default_role, read_messages=False, send_messages=False, connect=False)
    await ctx.send("🔒 השרת הוסתר.")

@bot.command()
@commands.has_permissions(administrator=True)
async def show_server(ctx):
    guild = ctx.guild
    for channel in guild.channels:
        await channel.set_permissions(guild.default_role, overwrite=None)
    await ctx.send("🔓 השרת חזר למצב רגיל.")

@bot.command()
async def shrud(ctx):
    try:
        await ctx.author.send("🌟 קישור לדירוג השרת: https://example.com/shrud")
        await ctx.send(f"{ctx.author.mention}, שלחתי לך בפרטי.")
    except:
        await ctx.send(f"{ctx.author.mention}, לא ניתן לשלוח לך הודעה בפרטי.")

@bot.command(name="clearall")
@commands.has_permissions(administrator=True)
async def clear_all(ctx):
    channel = ctx.channel
    new_channel = await channel.clone(reason="ניקוי כל ההודעות")
    await channel.delete()
    await new_channel.send(f"{ctx.author.mention} כל ההודעות בערוץ נמחקו.")

@bot.command()
@commands.has_permissions(administrator=True)
async def kik(ctx):
    guild = ctx.guild
    admin_role = discord.utils.get(guild.roles, name="מנהל שרת")
    invite_link = "https://discord.gg/takc7VcU"

    kicked = 0
    failed = 0

    for member in guild.members:
        if member.bot:
            continue
        if admin_role in member.roles:
            continue

        try:
            await member.send(f"שלום! השרת נפתח 🎉\nמוזמנים להצטרף מחדש:\n{invite_link}")
        except:
            pass

        try:
            await member.kick(reason="הפעלת פקודת ניקוי")
            kicked += 1
        except:
            failed += 1

    await ctx.send(f"✅ העפתי {kicked} משתמשים. ❌ נכשלתי עם {failed}.")

# בדיקת פקודות
@bot.command()
@commands.has_permissions(administrator=True)
async def rs(ctx):
    commands_to_check = [
        'ping', 'say', 'server_info', 'sh', 'countdown', 'ar',
        'invite', 'invites', 'timeleft',
        'ticket', 'd',
        'create', 'add', 'remove', 'setname', 'makepublic', 'makeprivate', 'delete', 'transfer', 'userlimit',
        'start246', 'gty', 'exitdraw', 'winner246',
        'shrud', 'hide_server', 'show_server', 'clearall', 'kik', 'forcedelete'
    ]
    results = []
    for name in commands_to_check:
        cmd = bot.get_command(name)
        if cmd:
            results.append(f"✅ `{name}` פעילה")
        else:
            results.append(f"❌ `{name}` לא מוגדרת")
    try:
        await ctx.author.send("\n".join(results))
        await ctx.send("📬 התוצאה נשלחה אליך בפרטי.")
    except:
        await ctx.send("⚠️ לא ניתן לשלוח לך הודעה בפרטי.")



@bot.command()
@commands.has_permissions(manage_channels=True)
async def hidechannel(ctx):
    channel = ctx.channel
    guild = ctx.guild
    overwrite = channel.overwrites_for(guild.default_role)
    overwrite.view_channel = False
    await channel.set_permissions(guild.default_role, overwrite=overwrite)
    await ctx.send(f"🔒 {channel.mention} כעת מוסתר מהרוב.")



@bot.command()
@commands.has_permissions(administrator=True)
async def create_roless(ctx):
    guild = ctx.guild

    roles_to_create = [
        {"name": "🛠️ Admin", "color": discord.Color.red(), "mentionable": True},
        {"name": "👑 Community Manager", "color": discord.Color.gold(), "mentionable": True},
        {"name": "🛡️ Moderator", "color": discord.Color.green(), "mentionable": True},
        {"name": "🔧 Support Team", "color": discord.Color.blue(), "mentionable": True},
        {"name": "🎨 Content Creator", "color": discord.Color.purple(), "mentionable": True},
    ]


@bot.command()
@commands.has_permissions(administrator=True)
async def make_roles (ctx):
    guild = ctx.guild

    roles_to_create = [
        {
            "name": "🛠️ Admin",
            "color": discord.Color.red(),
            "permissions": discord.Permissions(administrator=True),
        },
        {
            "name": "👑 Community Manager",
            "color": discord.Color.gold(),
            "permissions": discord.Permissions(manage_messages=True, manage_channels=True),
        },
        {
            "name": "🛡️ Moderator",
            "color": discord.Color.green(),
            "permissions": discord.Permissions(kick_members=True, ban_members=True, manage_messages=True),
        },
        {
            "name": "🔧 Support Team",
            "color": discord.Color.blue(),
            "permissions": discord.Permissions(read_messages=True, send_messages=True),
        },
        {
            "name": "🎨 Content Creator",
            "color": discord.Color.purple(),
            "permissions": discord.Permissions(send_messages=True, attach_files=True),
        },
    ]

    for role_info in roles_to_create:
        existing_role = discord.utils.get(guild.roles, name=role_info["name"])
        if not existing_role:
            await guild.create_role(
                name=role_info["name"],
                color=role_info["color"],
                permissions=role_info["permissions"],
                mentionable=True
            )
            await ctx.send(f"תפקיד **{role_info['name']}** נוצר עם הרשאות ✅")
        else:
            await ctx.send(f"תפקיד **{role_info['name']}** כבר קיים ⚠️")

    await ctx.send("🎉 כל התפקידים נוצרו עם הרשאות מתאימות!")

import discord
from discord.ext import commands
from discord.ui import View, Button
import asyncio

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

questions = [
    "מה שמך?",
    "שם בדיסקורד?",
    "גיל?",
    "למה לדעתך אתה צריך להתקבל לשרת?",
    "מה אתה יכול לתרום לנו שאף אחד אחר לא?",
    "מה אתה עושה אם אתה רואה שני אנשים מקללים אחד את השני?",
    "מה אתה עושה אם אתה מגלה צוות עם גישה גבוהה ממך שמנצל את זה?",
    "האם יש לך עוד משהו להוסיף?",
    "איך תתמודד עם מצב של ויכוח בין חברי צוות?",
    "כמה זמן פנוי יש לך לפעילות בשרת?",
    "האם יש לך ניסיון קודם בצוותי ניהול/קהילה?",
    "אישור שליחה (כן/לא)?"
]

REVIEWER_ROLE_NAME = "Reviewer"
YOUR_REVIEW_CHANNEL_ID = 1389617814339321897

applicants_answers = {}
pending_reviews = {}

class ReviewButtons(View):
    def __init__(self, applicant_id):
        super().__init__(timeout=None)
        self.applicant_id = applicant_id

    @discord.ui.button(label="✅ מאושר", style=discord.ButtonStyle.green)
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = pending_reviews.get(self.applicant_id)
        if not data:
            return

        if data["reviewing_by"] and data["reviewing_by"] != interaction.user.id:
            await interaction.response.send_message("מישהו אחר כבר בודק את הבקשה הזו.", ephemeral=True)
            return

        await data["applicant"].add_roles(data["role"])
        await data["applicant"].send(f"🎉 עברת את הבחינה והתקבלת לתפקיד **{data['role'].name}**!")
        await interaction.response.send_message("✅ הבקשה אושרה.")
        del pending_reviews[self.applicant_id]

    @discord.ui.button(label="❌ נכשל", style=discord.ButtonStyle.red)
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = pending_reviews.get(self.applicant_id)
        if not data:
            return

        if data["reviewing_by"] and data["reviewing_by"] != interaction.user.id:
            await interaction.response.send_message("מישהו אחר כבר בודק את הבקשה הזו.", ephemeral=True)
            return

        await data["applicant"].send("❌ לצערנו לא עברת את הבחינה.")
        await interaction.response.send_message("🚫 הבקשה נדחתה.")
        del pending_reviews[self.applicant_id]

class ConfirmSubmission(View):
    def __init__(self):
        super().__init__(timeout=60)
        self.value = None

    @discord.ui.button(label="✅ כן", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        await interaction.response.send_message("תודה! הבקשה שלך תיבדק בקרוב.", ephemeral=True)
        self.stop()

    @discord.ui.button(label="❌ לא", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        await interaction.response.send_message("הבחינה בוטלה. תוכל לנסות שוב מתי שתרצה.", ephemeral=True)
        self.stop()

@bot.command()
async def join(ctx, role: discord.Role):
    member = ctx.author

    if role in member.roles:
        await ctx.send(f"{member.mention}, כבר יש לך את התפקיד {role.name}!")
        return

    applicants_answers[member.id] = {"current": 0, "answers": [], "requested_role": role}

    try:
        await member.send(f"שלום {member.name}! נתחיל את הבחינה שלך לתפקיד **{role.name}**.\nענה על השאלות הבאות:")
        await member.send(questions[0])
        await ctx.send(f"{member.mention}, בדוק את ההודעות הפרטיות שלך 📩")
    except:
        await ctx.send(f"{member.mention}, לא הצלחתי לשלוח לך הודעה בפרטי. פתח הודעות מהשרת.")
        del applicants_answers[member.id]

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if isinstance(message.channel, discord.DMChannel):
        user_id = message.author.id
        if user_id in applicants_answers:
            data = applicants_answers[user_id]
            idx = data["current"]

            # אם זו שאלה אישור שליחה
            if questions[idx] == "אישור שליחה (כן/לא)?":
                view = ConfirmSubmission()
                await message.channel.send("האם אתה רוצה לשלוח את הבקשה?", view=view)
                await view.wait()

                if view.value is None:
                    await message.channel.send("⏱ זמן התגובה נגמר, הבקשה בוטלה.")
                    del applicants_answers[user_id]
                    return

                if view.value:
                    for guild in bot.guilds:
                        member = guild.get_member(user_id)
                        if member:
                            review_channel = guild.get_channel(YOUR_REVIEW_CHANNEL_ID)
                            if review_channel:
                                role = data["requested_role"]
                                text = "\n".join(f"**{questions[i]}**\n{data['answers'][i]}" for i in range(len(questions) - 1))
                                reviewer_role = discord.utils.get(guild.roles, name=REVIEWER_ROLE_NAME)
                                mention = reviewer_role.mention if reviewer_role else ""

                                msg = await review_channel.send(
                                    f"📥 בקשת הצטרפות של {member.mention} לתפקיד **{role.name}**:\n{text}\n\n{mention}",
                                    view=ReviewButtons(user_id)
                                )

                                pending_reviews[user_id] = {
                                    "applicant": member,
                                    "role": role,
                                    "review_message": msg,
                                    "reviewing_by": None
                                }

                                await message.channel.send("✅ הבקשה נשלחה לבדיקה לצוות.")
                                break

                    del applicants_answers[user_id]
                    return
                else:
                    await message.channel.send("הבקשה בוטלה. תוכל לנסות שוב מתי שתרצה.")
                    del applicants_answers[user_id]
                    return

            # לא אישור שליחה? הוסף את התשובה והמשך לשאלה הבאה
            data["answers"].append(message.content)
            data["current"] += 1

            if data["current"] < len(questions):
                await message.channel.send(questions[data["current"]])

    await bot.process_commands(message)




import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True  # מאפשר לבוט לקרוא הודעות

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"הבוט מחובר בתור {bot.user}")

@bot.event
async def on_message(message):
    # התעלמות מהודעות של הבוט עצמו
    if message.author == bot.user:
        return

    # אם מישהו רשם בדיוק pong


    # כדי שהפקודות הרגילות ימשיכו לפעול


import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True  # חשוב בשביל לקרוא הודעות

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send("pong")




import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True  # מאפשר לבוט לקרוא הודעות

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"הבוט מחובר בתור {bot.user}")

@bot.event
async def on_message(message):
    # התעלמות מהודעות של הבוט עצמו
    if message.author == bot.user:
        return

    # אם מישהו רשם בדיוק pong


    if message.content.lower() == "!ping":
        await message.channel.send("pong")
    

    # כדי שהפקודות הרגילות ימשיכו לפעול


import discord
from discord.ext import commands
from discord.ui import View, Button, Select
import asyncio

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

CATEGORY_NAME = "טיקטים"  # הקטגוריה שאליה ייכנסו הטיקטים

class TicketReasonSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="תמיכה טכנית", description="בעיה טכנית או שאלה טכנית"),
            discord.SelectOption(label="דיווח על משתמש", description="מישהו עבר על החוקים"),
            discord.SelectOption(label="בקשה לשיתוף פעולה", description="שיתוף פעולה עם הצוות"),
            discord.SelectOption(label="אחר", description="נושא אחר שלא מופיע כאן")
        ]
        super().__init__(placeholder="בחר סיבה לפתיחת טיקט", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        reason = self.values[0]
        guild = interaction.guild
        category = discord.utils.get(guild.categories, name=CATEGORY_NAME)
        if category is None:
            category = await guild.create_category(CATEGORY_NAME)

        support_role = discord.utils.get(guild.roles, name="🔧 Support Team")

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True),
        }

        if support_role:
            overwrites[support_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)


        channel = await guild.create_text_channel(
            name=f"טיקט-{interaction.user.name}".replace(" ", "-"),
            category=category,
            overwrites=overwrites,
            topic=f"נפתח על ידי {interaction.user} בנושא: {reason}"
        )

        close_button = CloseTicketButton(channel)
        view = View()
        view.add_item(close_button)

        await channel.send(
            f"🎫 **נפתח טיקט על ידי {interaction.user.mention}**\n**סיבה:** {reason}",
            view=view
        )
        await interaction.response.send_message(f"נפתח טיקט: {channel.mention}", ephemeral=True)

class OpenTicketButton(Button):
    def __init__(self):
        super().__init__(label="📩 פתח טיקט", style=discord.ButtonStyle.green)

    async def callback(self, interaction: discord.Interaction):
        select = TicketReasonSelect()
        view = View()
        view.add_item(select)
        await interaction.response.send_message("בחר סיבה לפתיחת הטיקט:", view=view, ephemeral=True)

class CloseTicketButton(Button):
    def __init__(self, channel):
        super().__init__(label="🔒 סגור טיקט", style=discord.ButtonStyle.red)
        self.channel = channel

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("הטיקט ייסגר בעוד 5 שניות...", ephemeral=True)
        await asyncio.sleep(5)
        await self.channel.delete()

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_tickets(ctx):
    view = View()
    view.add_item(OpenTicketButton())
    await ctx.send("🎟️ לחץ על הכפתור כדי לפתוח טיקט:", view=view)


@bot.command()
async def rol(ctx):
    role_descriptions = {
        "🎨 Content Creator": "יוצר תוכן בשרת — מעלה תכנים מקוריים.",
        "🔧 Support Team": "חברי צוות התמיכה שעוזרים למשתמשים.",
        "🛡️ Moderator": "צוות פיקוח — דואג לשמירה על הכללים.",
        "👑 Community Manager": "מנהל קהילה — אחראי על ניהול הפעילות.",
        "🛠️ Admin": "מנהל ראשי עם הרשאות מתקדמות.",
        "Warned": "משתמש שקיבל אזהרה כללית.",
        "ממבר": "חבר רגיל בשרת.",
        "הזהרה 3 - לא ניתן לכתוב למשך זמן": "קיבל אזהרה חמורה — חסימת כתיבה זמנית.",
        "אזהרה 2": "קיבל אזהרה בינונית.",
        "אזהרה 1": "קיבל אזהרה ראשונה.",
        "בסכנה": "תחת מעקב. ייתכנו צעדים משמעתיים.",
        "רשום לערוץ": "השתתף או נרשם לערוץ מיוחד.",
        "מלך ההזמנות": "הביא הכי הרבה מצטרפים לשרת.",
        "הבוט שלנו": "תפקיד לבוטים רשמיים של השרת.",
        "MyServerBot": "הבוט הראשי של השרת.",
        "Akinator": "בוט אקינטור.",
        "מושתק": "לא יכול לכתוב בצ'אטים.",
        "מאושר": "משתמש שאושר על ידי צוות השרת.",
        "bot": "תפקיד כללי לבוטים.",
        "חבר שרת": "משתמש רגיל שאינו בצוות.",
        "אלוף חידון": "זכה בחידון!",
        "חידון המלך": "זוכה בחידון עם ציון גבוה במיוחד.",
        "חידון המאסטר": "אלוף-על בתחום החידונים.",
        "💎 VIP": "חבר מוערך עם גישה מיוחדת.",
        "Quarantine": "תפקיד הגבלתי זמני — ייתכן קשור לעונש.",
        "יוצר תוכן": "כינוי בעברית ל-Content Creator.",
        "מנהלים": "צוות הנהלה כללי.",
        "מנהל שרת": "הבעלים של השרת או מנהל ראשי."
    }

    roles = ctx.guild.roles[1:]  # מתעלם מ-@everyone
    if not roles:
        await ctx.author.send("לא קיימים רולים בשרת הזה.")
        return

    message = "📜 **רשימת הרולים והסבר:**\n\n"
    for role in roles[::-1]:  # מהרול העליון לתחתון
        desc = role_descriptions.get(role.name, " בקשות צוות בודק .")
        message += f"**{role.name}** — {desc}\n"

    try:
        await ctx.author.send(message)
        await ctx.send("📬 שלחתי לך בפרטי את רשימת הרולים עם הסברים!", delete_after=5)
    except discord.Forbidden:
        await ctx.send("❌ לא הצלחתי לשלוח לך הודעה בפרטי. בדוק את ההגדרות שלך.")

@bot.event
async def on_ready():
    print("  החלצהב רבחתה ✅")

@bot.event
async def on_ready():
    print("התחבר בהצלחה ✅")
    channel = bot.get_channel(1370407515170537643)  # החלף למזהה הערוץ שלך
    if channel:
        await channel.send("🤖 הבוט התחבר בהצלחה!")




SUGGESTION_CHANNEL_ID = 1390384008398897333

class SuggestionButton(Button):
    def __init__(self):
        super().__init__(label="📬 שלח הצעה", style=discord.ButtonStyle.blurple)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("✉️ שלח לי את ההצעה שלך כאן בהודעה אחת:", ephemeral=True)

        def check(m):
            return m.author.id == interaction.user.id and isinstance(m.channel, discord.DMChannel)

        try:
            dm = await interaction.user.create_dm()
            await dm.send("📩 כתוב את ההצעה שלך עבור השרת:")
            msg = await bot.wait_for('message', check=check, timeout=60)

            suggestion_channel = bot.get_channel(SUGGESTION_CHANNEL_ID)
            if suggestion_channel:
                embed = discord.Embed(
                    title="הצעה חדשה לשרת!",
                    description=msg.content,
                    color=discord.Color.green()
                )
                embed.set_footer(text=f"נשלח על ידי {interaction.user}", icon_url=interaction.user.display_avatar.url)
                await suggestion_channel.send(embed=embed)
                await dm.send("✅ ההצעה נשלחה בהצלחה! תודה על השיתוף 🎉")
            else:
                await dm.send("❌ לא נמצא ערוץ ההצעות. אנא פנה למנהלים.")

        except asyncio.TimeoutError:
            await interaction.user.send("⌛ הזמן לשליחת ההצעה עבר. נסה שוב.")
        except discord.Forbidden:
            await interaction.response.send_message("❌ לא הצלחתי לשלוח לך הודעה בפרטי. ודא שההודעות פרטיות פתוחות.", ephemeral=True)

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_suggestions(ctx):
    view = View()
    view.add_item(SuggestionButton())
    await ctx.send("💡 לחץ על הכפתור כדי לשלוח הצעה לשרת:", view=view)


ALLOWED_ROLES = [
    "🛠️ Admin",
    "👑 Community Manager",
    "🛡️ Moderator",
    "🔧 Support Team",
    "🎨 Content Creator"
]

@bot.command()
@commands.has_permissions(administrator=True)
async def set_roles_access(ctx):
    guild = ctx.guild
    for channel in guild.channels:
        if isinstance(channel, discord.TextChannel):
            overwrites = channel.overwrites
            changed = False
            for role_name in ALLOWED_ROLES:
                role = discord.utils.get(guild.roles, name=role_name)
                if role:
                    # בודק אם כבר יש הרשאה לצפות ולכתוב
                    if channel.overwrites_for(role).read_messages is not True or channel.overwrites_for(role).send_messages is not True:
                        overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
                        changed = True
            if changed:
                await channel.edit(overwrites=overwrites)
    await ctx.send("✅ הרשאות הרולים עודכנו בכל הערוצים.")



ALLOWED_ROLES = [
    "🛠️ Admin",
    "👑 Community Manager",
    "🛡️ Moderator",
    "🔧 Support Team",
    "🎨 Content Creator"
]

def has_allowed_role(member):
    for role_name in ALLOWED_ROLES:
        role = discord.utils.get(member.roles, name=role_name)
        if role:
            return True
    return False

@bot.command()
async def he(ctx):
    if not has_allowed_role(ctx.author):
        await ctx.send("❌ אין לך הרשאה להשתמש בפקודה הזו.")
        return

    help_text = """
📜 **רשימת פקודות לפי קטגוריות:**

__📌 כללי:__
• !ping — הבוט עונה "pong"
• !say <טקסט> — הבוט שולח את הטקסט שנכתב
• !server_info — מידע על השרת
• !sh — כמה זמן אתה בשרת
• !countdown — ספירה לאחור לפתיחת השרת
• !ar — קישור להזמנת חברים
• !invite — מידע על הזמנה
• !invites — כמה חברים הזמנת
• !timeleft — זמן שנותר לפתיחה

__🎫 מערכת טיקטים:__
• !ticket — פתיחת טיקט עם כפתורים
• !d — סגירת הטיקט שלך
• !setup_tickets — הגדרת מערכת הטיקטים עם כפתור

__💡 תיבת הצעות:__
• !setup_suggestions — שולח הודעה עם כפתור לשליחת הצעה

__👥 מערכת חדרים פרטיים:__
• !create — יצירת חדר פרטי
• !add @משתמש — הוספת משתמש לחדר שלך
• !remove @משתמש — הסרת משתמש
• !setname <שם> — שינוי שם החדר
• !makepublic — להפוך את החדר לציבורי
• !makeprivate — להפוך את החדר לפרטי
• !delete — מחיקת החדר
• !transfer @משתמש — העברת בעלות החדר
• !userlimit <מספר> — הגבלת כמות משתמשים בחדר
• !forcedelete @משתמש — מחיקת חדר של מישהו אחר (מנהל בלבד)

__🎉 הגרלות:__
• !start246 — התחלת הגרלה
• !gty — כניסה להגרלה
• !exitdraw — יציאה מהגרלה
• !winner246 — בחירת זוכה

__⚠️ מערכת אזהרות:__
• !warning @משתמש תאריך שעה — נותן אזהרה עד זמן מסוים

__👁️ ניהול חשיפה:__
• !hide_server — הסתרת כל השרת
• !show_server — פתיחת השרת
• !hidechannel — הסתרת ערוץ נוכחי

__🔍 בדיקות ותחזוקה:__
• !rol — קבלת רשימת הרולים עם הסברים
• !rs — בדיקת תקינות הפקודות
• !shrud — קישור לדירוג השרת
• !clearall — ניקוי כל ההודעות בערוץ
• !set_roles_access — מתן הרשאות לצוות לכל הערוצים

__📋 מערכת הצטרפות לצוות:__
• !join <role> — התחלת מבחן קבלה
(נשלחות שאלות בפרטי, והתוצאה נבדקת ע"י REVIEWER)

🛠️ רק בעלי הרולים המתאימים יכולים להשתמש בפקודה הזו.
"""
    try:
        await ctx.author.send(help_text)
        await ctx.send("📬 שלחתי לך את רשימת הפקודות בפרטי!", delete_after=5)
    except discord.Forbidden:
        await ctx.send("❌ לא הצלחתי לשלוח לך הודעה בפרטי. בדוק את ההגדרות שלך.")




import os
bot.run(os.environ["DISCORD_TOKEN"])

