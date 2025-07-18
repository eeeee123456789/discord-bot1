# config.py

from datetime import datetime

counting_channel_name = "counting"
server_open_datetime = datetime(2025, 6, 30, 12, 0, 0)
WARNING_ROLE_NAME = "Warned"
WARNINGS_FILE = "warnings.json"
REVIEWER_ROLE_NAME = "Reviewer"
REVIEW_CHANNEL_ID = 1389617814339321897
SUGGESTION_CHANNEL_ID = 1390384008398897333

ALLOWED_ROLES = [
    "🛠️ Admin", "👑 Community Manager", "🛡️ Moderator",
    "🔧 Support Team", "🎨 Content Creator"
]

# משתנים דינמיים בזמן ריצה
user_invites = {}
active_tickets = {}
private_rooms = {}
last_number = 0
last_user_id = None
active_draw = False
participants = set()
