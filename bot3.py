print("بدأ البرنامج")

import asyncio
import json
import os
import re
import time

import discord
from discord.ext import commands

# ---- سيرفر ويب صغير عشان Render ما يوقف الخدمة ----
from flask import Flask
from threading import Thread

_web = Flask(__name__)


@_web.route("/")
def _home():
    return "Bot is running"


def _run_web():
    _web.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))


Thread(target=_run_web, daemon=True).start()

# ============================================================
#                        الإعدادات
# ============================================================
TOKEN = os.environ["DISCORD_TOKEN"]  # حطه في Render > Environment، مش هنا

WIN_SCORE = 10            # أول من يوصل هذا الرقم يفوز
OWNER_ROLE_ID = 0         # ايدي رتبة الأونر (اتركه 0 وبيدور على رتبة اسمها Owner / اونر)
OWNER_ROLE_NAMES = {"owner", "اونر", "أونر", "الاونر", "الأونر"}
ROOM_CATEGORY_ID = 0      # ايدي كاتيجوري الغرف (0 = نفس كاتيجوري قناة اللوحة)
LOG_CHANNEL_ID = 0        # ايدي قناة سجل النتائج (0 = بدون سجل)
CLOSE_DELAY = 30          # ثواني قبل حذف الغرفة بعد انتهاء المباراة
QUEUE_TIMEOUT = 900       # بعد كم ثانية يطلع اللاعب من قائمة الانتظار
DATA_FILE = "data_1v1.json"

BLUE = 0x5865F2
GREEN = 0x57F287
RED = 0xED4245
GOLD = 0xFEE75C

# ============================================================
#                        التخزين
# ============================================================


def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
    except Exception:
        d = {}
    d.setdefault("matches", {})
    d.setdefault("stats", {})
    d.setdefault("counter", 0)
    d.setdefault("lb", None)
    return d


DATA = load_data()
QUEUES = {}  # guild_id -> [(user_id, time)]


def save_data():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(DATA, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("تعذر حفظ البيانات:", repr(e))


# ============================================================
#                        البوت
# ============================================================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True


class OneVsOneBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.queue_lock = None

    async def setup_hook(self):
        self.queue_lock = asyncio.Lock()
        # أزرار دائمة تشتغل حتى بعد إعادة تشغيل البوت
        self.add_view(PanelView())
        self.add_view(RoomView())
        self.add_view(ResultView())
        self.add_view(DisputeView())
        self.add_view(LeaderboardView())


bot = OneVsOneBot()

# ============================================================
#                        دوال مساعدة
# ============================================================


def mention(uid):
    return "<@" + str(uid) + ">"


def owner_roles(guild):
    roles = []
    if OWNER_ROLE_ID:
        r = guild.get_role(OWNER_ROLE_ID)
        if r is not None:
            roles.append(r)
    else:
        for r in guild.roles:
            if r.name.strip().lower() in OWNER_ROLE_NAMES:
                roles.append(r)
    return roles


def is_owner(member):
    if member.guild_permissions.administrator or member.id == member.guild.owner_id:
        return True
    mine = set(r.id for r in member.roles)
    return any(r.id in mine for r in owner_roles(member.guild))


def owner_ping(guild):
    roles = owner_roles(guild)
    if roles:
        return " ".join(r.mention for r in roles)
    if guild.owner_id:
        return mention(guild.owner_id)
    return "الأونر"


def parse_score(text):
    text = text.strip().translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789"))
    if not text.isdigit():
        return None
    n = int(text)
    if 0 <= n <= WIN_SCORE:
        return n
    return None


ROBLOX_RE = re.compile(r"^https?://([a-z0-9-]+\.)*(roblox\.com|ro\.blox\.com)/\S+$", re.I)


def get_match(channel_id):
    return DATA["matches"].get(str(channel_id))


def find_active_match(guild, uid):
    for cid, m in list(DATA["matches"].items()):
        if m.get("done") or m.get("guild") != guild.id:
            continue
        if uid not in (m["p1"], m["p2"]):
            continue
        if guild.get_channel(int(cid)) is None:
            m["done"] = True
            save_data()
            continue
        return cid, m
    return None


RANKS = [
    (0, "🟫 برونزي", 0x8C5A2B),
    (100, "⚪ فضي", 0xB4B4B4),
    (200, "🟡 ذهبي", 0xFFD700),
    (300, "💎 بلاتيني", 0x4FD1E8),
    (400, "🔷 ماسي", 0x4F8FE8),
    (500, "🔥 أسطوري", 0xE8594F),
    (600, "⚡ نخبة", 0xF1C40F),
    (700, "🌟 بطل", 0x9B59B6),
    (800, "🛡️ فاتح", 0x1ABC9C),
    (900, "🌌 إمبراطور", 0x2C3E50),
    (1000, "👑 ملك 1v1", 0xFFC107),
]
STRONG_RANK_THRESHOLD = 500  # من هذا المجموع فما فوق، الخسارة تخصم أكتر
NORMAL_LOSS_PENALTY = 10
STRONG_LOSS_PENALTY = 20
WIN_POINTS = 10


def rank_for(points):
    cur = RANKS[0]
    for threshold, name, color in RANKS:
        if points >= threshold:
            cur = (threshold, name, color)
        else:
            break
    return cur


def next_rank_for(points):
    for threshold, name, color in RANKS:
        if points < threshold:
            return threshold, name, color
    return None


def add_stats(p1, p2, s1, s2):
    for uid, mine, theirs in ((p1, s1, s2), (p2, s2, s1)):
        s = DATA["stats"].setdefault(
            str(uid), {"w": 0, "l": 0, "d": 0, "pf": 0, "pa": 0, "pts": 0}
        )
        s.setdefault("pts", 0)
        s["pf"] += mine
        s["pa"] += theirs
        if mine > theirs:
            s["w"] += 1
            s["pts"] += WIN_POINTS
        elif mine < theirs:
            s["l"] += 1
            # اللاعب القوي (مجمّع 500+ نقطة) يخسر 20 بدل 10
            penalty = STRONG_LOSS_PENALTY if s["pts"] >= STRONG_RANK_THRESHOLD else NORMAL_LOSS_PENALTY
            s["pts"] = max(0, s["pts"] - penalty)
        else:
            s["d"] += 1


async def strip_buttons(channel, message_id):
    if not message_id:
        return
    try:
        msg = await channel.fetch_message(message_id)
        await msg.edit(view=None)
    except Exception:
        pass


# ============================================================
#                        الـ Embeds
# ============================================================


def panel_embed():
    e = discord.Embed(
        title="⚔️ نظام 1v1",
        description="تحدّى لاعبين ثانيين وجهاً لوجه في غرفة خاصة، والنتيجة تنحسب لك في الترتيب.",
        color=BLUE,
    )
    e.add_field(
        name="🎯 وش فايدة النظام؟",
        value=(
            "• تلاقي خصم بسرعة بدون ما تدور في الشات.\n"
            "• تلعبون في غرفة خاصة ما يشوفها غيركم والأونر.\n"
            "• النتائج تنحفظ وتطلع إحصائياتك وترتيب المتصدرين.\n"
            "• أي خلاف بينكم يحله الأونر."
        ),
        inline=False,
    )
    e.add_field(
        name="📜 القوانين",
        value=(
            "1️⃣ المباراة تنتهي لأول من يوصل **" + str(WIN_SCORE) + "** نقاط.\n"
            "2️⃣ بعد المباراة أي لاعب يسجل النتيجة، والخصم لازم **يوافق** عليها.\n"
            "3️⃣ إذا الخصم رفض أو ما وافق، اضغط **استدعاء أونر** وهو يحكم بينكم.\n"
            "4️⃣ ممنوع الغش أو الانسحاب بدون ما تبلغ الأونر.\n"
            "5️⃣ النتيجة اللي يثبتها الأونر نهائية."
        ),
        inline=False,
    )
    e.add_field(
        name="🚀 كيف تبدأ؟",
        value=(
            "1. اضغط **ابدأ البحث عن خصم**.\n"
            "2. أول ما يلاقي لك خصم يفتح لكم غرفة خاصة وينبهكم.\n"
            "3. حطوا رابط سيرفر روبلوكس بزر **رابط روبلوكس**.\n"
            "4. العبوا، وبعدها سجلوا النتيجة."
        ),
        inline=False,
    )
    return e


def room_embed(m):
    claim = m.get("claim")
    if m.get("cancelled"):
        status = "🚫 المباراة ملغية بدون نقاط"
    elif m.get("done"):
        status = "✅ انتهت المباراة"
    elif claim and claim["status"] == "pending":
        status = "⏳ بانتظار موافقة الخصم على النتيجة"
    elif claim and claim["status"] == "rejected":
        status = "⚠️ النتيجة انرفضت، سجلوا من جديد أو استدعوا الأونر"
    else:
        status = "🎮 المباراة شغالة"
    e = discord.Embed(title="⚔️ مباراة 1v1 #" + str(m["id"]), color=BLUE)
    e.add_field(name="1️⃣ اللاعب 1", value=mention(m["p1"]), inline=True)
    e.add_field(name="2️⃣ اللاعب 2", value=mention(m["p2"]), inline=True)
    e.add_field(name="🎮 رابط السيرفر", value=m.get("roblox") or "لم يُحدد بعد", inline=False)
    e.add_field(name="📌 الحالة", value=status, inline=False)
    e.add_field(
        name="📜 تذكير",
        value="أول من يوصل **" + str(WIN_SCORE) + "** يفوز. سجلوا النتيجة بعد ما تخلصون.",
        inline=False,
    )
    return e


def story_embed(m, caller):
    e = discord.Embed(title="🚨 استدعاء أونر — مباراة #" + str(m["id"]), color=RED)
    e.description = caller.mention + " يطلب تدخل الأونر."
    e.add_field(
        name="👥 اللاعبين",
        value="1️⃣ " + mention(m["p1"]) + "\n2️⃣ " + mention(m["p2"]),
        inline=False,
    )
    claim = m.get("claim")
    if not claim:
        story = "ما فيه أي نتيجة مسجلة للحين."
    else:
        story = (
            mention(claim["by"]) + " سجل النتيجة: " + mention(m["p1"]) + " **" + str(claim["s1"])
            + "** - **" + str(claim["s2"]) + "** " + mention(m["p2"]) + "\n"
        )
        if claim["status"] == "pending":
            story += "⏳ الخصم ما وافق عليها للحين."
        elif claim["status"] == "rejected":
            story += "❌ الخصم رفض النتيجة."
            if claim.get("reason"):
                story += "\n📝 سبب الرفض: " + claim["reason"]
    e.add_field(name="📖 القصة", value=story, inline=False)
    e.add_field(name="🎮 رابط السيرفر", value=m.get("roblox") or "لم يُحدد", inline=False)
    e.add_field(
        name="👑 على الأونر",
        value="اضغط زر **🏁 إنهاء القيم** وحدد النتيجة النهائية لكل لاعب.",
        inline=False,
    )
    return e


def stats_embed(user):
    s = DATA["stats"].get(str(user.id))
    e = discord.Embed(title="📊 إحصائيات " + user.display_name, color=BLUE)
    if not s:
        e.description = "ما لعبت أي مباراة للحين."
        return e
    s.setdefault("pts", 0)
    total = s["w"] + s["l"] + s["d"]
    rate = (s["w"] / total * 100) if total else 0
    pts = s["pts"]
    threshold, rank_name, rank_color = rank_for(pts)
    nxt = next_rank_for(pts)
    e.color = rank_color
    e.add_field(name="🏅 الرتبة", value=rank_name, inline=True)
    e.add_field(name="🔢 النقاط", value=str(pts), inline=True)
    e.add_field(
        name="⏭️ للرتبة الجاية",
        value=(str(nxt[0] - pts) + " نقطة لـ " + nxt[1]) if nxt else "وصلت لأعلى رتبة 👑",
        inline=True,
    )
    e.add_field(name="✅ فوز", value=str(s["w"]), inline=True)
    e.add_field(name="❌ خسارة", value=str(s["l"]), inline=True)
    e.add_field(name="🤝 تعادل", value=str(s["d"]), inline=True)
    e.add_field(name="🎯 نقاط له / عليه", value=str(s["pf"]) + " / " + str(s["pa"]), inline=True)
    e.add_field(name="📈 نسبة الفوز", value=str(round(rate)) + "%", inline=True)
    return e


def leaderboard_embed():
    items = sorted(
        DATA["stats"].items(),
        key=lambda kv: (kv[1].get("pts", 0), kv[1]["w"], kv[1]["pf"] - kv[1]["pa"]),
        reverse=True,
    )[:10]
    e = discord.Embed(title="🏆 المتصدرين", color=GOLD)
    if not items:
        e.description = "ما فيه نتائج للحين."
        return e
    medals = ["🥇", "🥈", "🥉"]
    lines = []
    for i, (uid, st) in enumerate(items):
        pts = st.get("pts", 0)
        _, rank_name, _ = rank_for(pts)
        nxt = next_rank_for(pts)
        if nxt:
            left = "⏭️ باقي **" + str(nxt[0] - pts) + "** نقطة لـ " + nxt[1]
        else:
            left = "👑 وصل لأعلى رتبة"
        prefix = medals[i] if i < 3 else "**" + str(i + 1) + ".**"
        lines.append(
            prefix + " " + mention(uid) + " — " + rank_name + " | **" + str(pts) + "** نقطة\n"
            + "┗ " + left + " • فوز " + str(st["w"]) + " / خسارة " + str(st["l"])
        )
    e.description = "\n\n".join(lines)
    e.set_footer(text="فوز = +" + str(WIN_POINTS) + " نقاط | خسارة = -" + str(NORMAL_LOSS_PENALTY))
    e.timestamp = discord.utils.utcnow()
    return e


async def refresh_leaderboard():
    lb = DATA.get("lb")
    if not lb:
        return
    try:
        ch = bot.get_channel(lb["channel"]) or await bot.fetch_channel(lb["channel"])
        msg = await ch.fetch_message(lb["message"])
        await msg.edit(embed=leaderboard_embed(), view=LeaderboardView())
    except Exception as ex:
        print("تعذر تحديث لوحة المتصدرين:", repr(ex))


class LeaderboardView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="تحديث", emoji="🔄", style=discord.ButtonStyle.secondary, custom_id="v1:lb_refresh")
    async def refresh_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(embed=leaderboard_embed(), view=LeaderboardView())

    @discord.ui.button(label="إحصائياتي", emoji="📊", style=discord.ButtonStyle.primary, custom_id="v1:lb_stats")
    async def stats_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(embed=stats_embed(interaction.user), ephemeral=True)


async def refresh_panel(channel, m):
    mid = m.get("panel_msg")
    if not mid:
        return
    try:
        msg = await channel.fetch_message(mid)
        if m.get("done"):
            await msg.edit(embed=room_embed(m), view=None)
        else:
            await msg.edit(embed=room_embed(m))
    except Exception as e:
        print("تعذر تحديث اللوحة:", repr(e))


# ============================================================
#                  إنشاء الغرفة وإنهاء المباراة
# ============================================================


async def create_room(guild, panel_channel, p1, p2):
    DATA["counter"] += 1
    n = DATA["counter"]
    allow = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        guild.me: allow,
        p1: allow,
        p2: allow,
    }
    for r in owner_roles(guild):
        overwrites[r] = allow

    category = None
    if ROOM_CATEGORY_ID:
        category = guild.get_channel(ROOM_CATEGORY_ID)
    if category is None:
        category = getattr(panel_channel, "category", None)

    channel = await guild.create_text_channel(
        name="1v1-" + str(n),
        category=category,
        overwrites=overwrites,
        topic="غرفة 1v1 خاصة",
        reason="مباراة 1v1",
    )
    m = {
        "id": n,
        "guild": guild.id,
        "p1": p1.id,
        "p2": p2.id,
        "roblox": None,
        "claim": None,
        "done": False,
        "last_call": 0,
        "panel_msg": None,
    }
    DATA["matches"][str(channel.id)] = m
    msg = await channel.send(
        content=p1.mention + " " + p2.mention + " 🎉 لقينا لكم خصم! بالتوفيق.",
        embed=room_embed(m),
        view=RoomView(),
        allowed_mentions=discord.AllowedMentions(users=True),
    )
    m["panel_msg"] = msg.id
    save_data()
    return channel


async def close_room(channel):
    await asyncio.sleep(CLOSE_DELAY)
    try:
        await channel.delete(reason="انتهت مباراة 1v1")
    except Exception as e:
        print("تعذر حذف الغرفة:", repr(e))
    DATA["matches"].pop(str(channel.id), None)
    save_data()


async def finish_match(channel, m, s1, s2, decided_by):
    m["done"] = True
    m["final"] = {"s1": s1, "s2": s2, "by": decided_by}
    add_stats(m["p1"], m["p2"], s1, s2)
    save_data()
    asyncio.create_task(refresh_leaderboard())

    if s1 > s2:
        result = "🏆 الفائز: " + mention(m["p1"])
    elif s2 > s1:
        result = "🏆 الفائز: " + mention(m["p2"])
    else:
        result = "🤝 تعادل"

    e = discord.Embed(title="🏁 انتهت المباراة #" + str(m["id"]), color=GREEN)
    e.add_field(name="1️⃣", value=mention(m["p1"]) + "\n**" + str(s1) + "**", inline=True)
    e.add_field(name="2️⃣", value=mention(m["p2"]) + "\n**" + str(s2) + "**", inline=True)
    e.add_field(name="النتيجة", value=result, inline=False)
    e.add_field(name="📌 اعتمدها", value=decided_by, inline=False)

    if LOG_CHANNEL_ID:
        lc = channel.guild.get_channel(LOG_CHANNEL_ID)
        if lc is not None:
            try:
                await lc.send(embed=e)
            except Exception as ex:
                print("تعذر الإرسال لقناة السجل:", repr(ex))

    e.set_footer(text="الغرفة بتنقفل بعد " + str(CLOSE_DELAY) + " ثانية")
    try:
        await channel.send(embed=e)
    except Exception as ex:
        print("تعذر إرسال النتيجة:", repr(ex))
    await refresh_panel(channel, m)
    asyncio.create_task(close_room(channel))


async def cancel_match(channel, m, by_text):
    m["done"] = True
    m["cancelled"] = True
    claim = m.get("claim")
    if claim and claim.get("status") == "pending":
        claim["status"] = "cancelled"
        await strip_buttons(channel, claim.get("msg"))
    save_data()

    e = discord.Embed(
        title="🚫 تم إلغاء المباراة #" + str(m["id"]),
        description="ما انحسبت أي نقاط ولا فوز ولا خسارة لأي لاعب.",
        color=RED,
    )
    e.add_field(name="اللاعبين", value=mention(m["p1"]) + " و " + mention(m["p2"]), inline=False)
    e.add_field(name="📌 ألغاها", value=by_text, inline=False)

    if LOG_CHANNEL_ID:
        lc = channel.guild.get_channel(LOG_CHANNEL_ID)
        if lc is not None:
            try:
                await lc.send(embed=e)
            except Exception as ex:
                print("تعذر الإرسال لقناة السجل:", repr(ex))

    e.set_footer(text="الغرفة بتنقفل بعد " + str(CLOSE_DELAY) + " ثانية")
    try:
        await channel.send(embed=e)
    except Exception as ex:
        print("تعذر إرسال رسالة الإلغاء:", repr(ex))
    await refresh_panel(channel, m)
    asyncio.create_task(close_room(channel))


# ============================================================
#                  البحث عن خصم (القائمة)
# ============================================================


async def handle_join(interaction):
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message("هذا الأمر داخل السيرفر فقط.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    user = interaction.user

    active = find_active_match(guild, user.id)
    if active:
        await interaction.followup.send("⚠️ عندك مباراة شغالة: <#" + str(active[0]) + ">", ephemeral=True)
        return

    status = "waiting"
    opponent = None
    async with bot.queue_lock:
        q = QUEUES.setdefault(guild.id, [])
        now = time.time()
        q[:] = [(u, t) for (u, t) in q if now - t < QUEUE_TIMEOUT]
        if any(u == user.id for (u, _) in q):
            status = "already"
        else:
            while q:
                uid, _ = q.pop(0)
                member = guild.get_member(uid)
                if member is not None and not find_active_match(guild, uid):
                    opponent = member
                    break
            if opponent is None:
                q.append((user.id, now))
            else:
                status = "matched"

    if status == "already":
        await interaction.followup.send("⏳ انت بالفعل في قائمة الانتظار.", ephemeral=True)
        return
    if status == "waiting":
        await interaction.followup.send(
            "🔎 جاري البحث عن خصم...\nأول ما نلاقي لك واحد نفتح لكم غرفة وننبهك بمنشن.\n"
            "تقدر تلغي بزر **إلغاء البحث**.",
            ephemeral=True,
        )
        return

    try:
        channel = await create_room(guild, interaction.channel, opponent, user)
    except Exception as e:
        print("خطأ إنشاء الغرفة:", repr(e))
        async with bot.queue_lock:
            QUEUES.setdefault(guild.id, []).insert(0, (opponent.id, time.time()))
        await interaction.followup.send(
            "❌ ما قدرت أنشئ الغرفة. تأكد إن البوت عنده صلاحية **Manage Channels**.",
            ephemeral=True,
        )
        return
    await interaction.followup.send("✅ لقينا لك خصم! الغرفة: " + channel.mention, ephemeral=True)


async def handle_leave(interaction):
    guild = interaction.guild
    if guild is None:
        return
    async with bot.queue_lock:
        q = QUEUES.setdefault(guild.id, [])
        before = len(q)
        q[:] = [(u, t) for (u, t) in q if u != interaction.user.id]
        removed = len(q) != before
    if removed:
        await interaction.response.send_message("✅ تم إلغاء البحث.", ephemeral=True)
    else:
        await interaction.response.send_message("انت مو في قائمة الانتظار.", ephemeral=True)


# ============================================================
#                        لوحة النظام
# ============================================================


class PanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="ابدأ البحث عن خصم", emoji="🔍", style=discord.ButtonStyle.success, custom_id="v1:join", row=0)
    async def join_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await handle_join(interaction)

    @discord.ui.button(label="إلغاء البحث", emoji="❌", style=discord.ButtonStyle.secondary, custom_id="v1:leave", row=0)
    async def leave_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await handle_leave(interaction)

    @discord.ui.button(label="إحصائياتي", emoji="📊", style=discord.ButtonStyle.primary, custom_id="v1:stats", row=1)
    async def stats_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(embed=stats_embed(interaction.user), ephemeral=True)

    @discord.ui.button(label="المتصدرين", emoji="🏆", style=discord.ButtonStyle.primary, custom_id="v1:top", row=1)
    async def top_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(embed=leaderboard_embed(), ephemeral=True)


# ============================================================
#                        غرفة المباراة
# ============================================================


async def get_room_match(interaction, players_only=True):
    m = get_match(interaction.channel_id)
    if not m or m.get("done"):
        await interaction.response.send_message("هذي المباراة منتهية أو غير موجودة.", ephemeral=True)
        return None
    if players_only and interaction.user.id not in (m["p1"], m["p2"]):
        await interaction.response.send_message("هذا الزر للاعبين فقط.", ephemeral=True)
        return None
    return m


async def do_call_owner(interaction):
    m = await get_room_match(interaction)
    if not m:
        return
    now = time.time()
    if now - m.get("last_call", 0) < 120:
        await interaction.response.send_message("⏳ تم استدعاء الأونر قبل شوي، انتظر شوي.", ephemeral=True)
        return
    m["last_call"] = now
    save_data()
    await interaction.response.send_message(
        content="🚨 " + owner_ping(interaction.guild),
        embed=story_embed(m, interaction.user),
        allowed_mentions=discord.AllowedMentions(roles=True, users=True),
    )


class RoomView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="رابط روبلوكس", emoji="🎮", style=discord.ButtonStyle.primary, custom_id="v1:link", row=0)
    async def link_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        m = await get_room_match(interaction)
        if m:
            await interaction.response.send_modal(LinkModal())

    @discord.ui.button(label="تسجيل النتيجة", emoji="📝", style=discord.ButtonStyle.success, custom_id="v1:score", row=0)
    async def score_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        m = await get_room_match(interaction)
        if not m:
            return
        claim = m.get("claim")
        if claim and claim["status"] == "pending" and claim["by"] != interaction.user.id:
            await interaction.response.send_message(
                "الخصم سجل نتيجة وينتظر ردك، اضغط ✅ أوافق أو ❌ أرفض على رسالته.",
                ephemeral=True,
            )
            return
        await interaction.response.send_modal(ScoreModal())

    @discord.ui.button(label="استدعاء أونر", emoji="🚨", style=discord.ButtonStyle.danger, custom_id="v1:owner", row=0)
    async def owner_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await do_call_owner(interaction)

    @discord.ui.button(label="إنهاء القيم", emoji="🏁", style=discord.ButtonStyle.secondary, custom_id="v1:end", row=1)
    async def end_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        m = await get_room_match(interaction, players_only=False)
        if not m:
            return
        if not is_owner(interaction.user):
            await interaction.response.send_message("🔒 هذا الزر للأونر فقط.", ephemeral=True)
            return
        g = interaction.guild
        a = g.get_member(m["p1"])
        b = g.get_member(m["p2"])
        n1 = a.display_name if a else str(m["p1"])
        n2 = b.display_name if b else str(m["p2"])
        await interaction.response.send_modal(EndModal(n1, n2))

    @discord.ui.button(label="إلغاء المباراة", emoji="🚫", style=discord.ButtonStyle.danger, custom_id="v1:cancel", row=1)
    async def cancel_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        m = await get_room_match(interaction, players_only=False)
        if not m:
            return
        if not is_owner(interaction.user):
            await interaction.response.send_message("🔒 هذا الزر للأونر فقط.", ephemeral=True)
            return
        await interaction.response.send_message(
            "⚠️ متأكد تبي تلغي المباراة بدون نقاط لأي أحد؟",
            view=CancelConfirmView(),
            ephemeral=True,
        )


class CancelConfirmView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.button(label="تأكيد الإلغاء", emoji="✅", style=discord.ButtonStyle.danger)
    async def yes_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_owner(interaction.user):
            await interaction.response.send_message("🔒 للأونر فقط.", ephemeral=True)
            return
        m = get_match(interaction.channel_id)
        if not m or m.get("done"):
            await interaction.response.edit_message(content="المباراة منتهية أو ملغية.", view=None)
            return
        await interaction.response.edit_message(content="✅ تم إلغاء المباراة.", view=None)
        await cancel_match(interaction.channel, m, "الأونر 👑 " + interaction.user.mention)

    @discord.ui.button(label="تراجع", style=discord.ButtonStyle.secondary)
    async def no_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="تم التراجع.", view=None)


class LinkModal(discord.ui.Modal, title="🎮 رابط سيرفر روبلوكس"):
    link = discord.ui.TextInput(
        label="الصق الرابط هنا",
        placeholder="https://www.roblox.com/...",
        max_length=300,
    )

    async def on_submit(self, interaction: discord.Interaction):
        m = get_match(interaction.channel_id)
        if not m or m.get("done"):
            await interaction.response.send_message("المباراة منتهية.", ephemeral=True)
            return
        url = self.link.value.strip()
        if not ROBLOX_RE.match(url):
            await interaction.response.send_message(
                "❌ الرابط غير صحيح. لازم يكون رابط روبلوكس (roblox.com).", ephemeral=True
            )
            return
        m["roblox"] = url
        save_data()
        view = discord.ui.View(timeout=None)
        view.add_item(discord.ui.Button(label="ادخل السيرفر", emoji="🎮", style=discord.ButtonStyle.link, url=url))
        await interaction.response.send_message(
            "🎮 " + interaction.user.mention + " حط رابط السيرفر:",
            view=view,
            allowed_mentions=discord.AllowedMentions.none(),
        )
        await refresh_panel(interaction.channel, m)


class ScoreModal(discord.ui.Modal, title="📝 تسجيل النتيجة"):
    mine = discord.ui.TextInput(label="نتيجتك", placeholder="مثال: 10", max_length=2)
    theirs = discord.ui.TextInput(label="نتيجة الخصم", placeholder="مثال: 8", max_length=2)

    async def on_submit(self, interaction: discord.Interaction):
        m = get_match(interaction.channel_id)
        if not m or m.get("done"):
            await interaction.response.send_message("المباراة منتهية.", ephemeral=True)
            return
        a = parse_score(self.mine.value)
        b = parse_score(self.theirs.value)
        if a is None or b is None:
            await interaction.response.send_message(
                "❌ اكتب أرقام صحيحة من 0 إلى " + str(WIN_SCORE) + ".", ephemeral=True
            )
            return
        if max(a, b) != WIN_SCORE or a == b:
            await interaction.response.send_message(
                "❌ لازم أحد اللاعبين يوصل **" + str(WIN_SCORE) + "** والثاني أقل منه.", ephemeral=True
            )
            return

        reporter = interaction.user.id
        opp = m["p2"] if reporter == m["p1"] else m["p1"]
        if reporter == m["p1"]:
            s1, s2 = a, b
        else:
            s1, s2 = b, a

        old = m.get("claim")
        if old and old.get("status") == "pending":
            await strip_buttons(interaction.channel, old.get("msg"))

        claim = {"by": reporter, "s1": s1, "s2": s2, "status": "pending", "reason": "", "msg": None}
        m["claim"] = claim

        e = discord.Embed(
            title="📝 تسجيل نتيجة",
            description=mention(reporter) + " سجل النتيجة التالية:",
            color=GOLD,
        )
        e.add_field(
            name="النتيجة",
            value=mention(m["p1"]) + " **" + str(s1) + "** - **" + str(s2) + "** " + mention(m["p2"]),
            inline=False,
        )
        e.add_field(name="المطلوب", value=mention(opp) + " اضغط ✅ أوافق أو ❌ أرفض.", inline=False)
        await interaction.response.send_message(
            content=mention(opp),
            embed=e,
            view=ResultView(),
            allowed_mentions=discord.AllowedMentions(users=True),
        )
        msg = await interaction.original_response()
        claim["msg"] = msg.id
        save_data()
        await refresh_panel(interaction.channel, m)


class RejectModal(discord.ui.Modal, title="❌ رفض النتيجة"):
    reason = discord.ui.TextInput(
        label="سبب الرفض (اختياري)",
        style=discord.TextStyle.paragraph,
        required=False,
        max_length=400,
    )

    async def on_submit(self, interaction: discord.Interaction):
        m = get_match(interaction.channel_id)
        claim = m.get("claim") if m else None
        if not m or m.get("done") or not claim or claim["status"] != "pending":
            await interaction.response.send_message("هذي النتيجة ما عادت متاحة.", ephemeral=True)
            return
        if interaction.user.id == claim["by"] or interaction.user.id not in (m["p1"], m["p2"]):
            await interaction.response.send_message("ما تقدر ترفض هذي النتيجة.", ephemeral=True)
            return
        claim["status"] = "rejected"
        claim["reason"] = (self.reason.value or "").strip()
        save_data()
        await strip_buttons(interaction.channel, claim.get("msg"))

        e = discord.Embed(title="❌ تم رفض النتيجة", color=RED)
        e.description = (
            mention(interaction.user.id) + " رفض النتيجة اللي سجلها " + mention(claim["by"]) + "."
        )
        if claim["reason"]:
            e.add_field(name="📝 السبب", value=claim["reason"], inline=False)
        e.add_field(
            name="وش تسوون؟",
            value=(
                mention(claim["by"]) + " تقدر تضغط **🚨 استدعاء أونر** وبيحكم بينكم.\n"
                "أو سجلوا نتيجة جديدة بزر **تسجيل النتيجة** إذا اتفقتوا."
            ),
            inline=False,
        )
        await interaction.response.send_message(
            content=mention(claim["by"]),
            embed=e,
            view=DisputeView(),
            allowed_mentions=discord.AllowedMentions(users=True),
        )
        await refresh_panel(interaction.channel, m)


class ResultView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def _check(self, interaction):
        m = get_match(interaction.channel_id)
        if not m or m.get("done"):
            await interaction.response.send_message("المباراة منتهية.", ephemeral=True)
            return None
        claim = m.get("claim")
        if not claim or claim["status"] != "pending" or claim.get("msg") != interaction.message.id:
            await interaction.response.send_message("هذي النتيجة قديمة.", ephemeral=True)
            return None
        if interaction.user.id not in (m["p1"], m["p2"]):
            await interaction.response.send_message("هذا الزر للاعبين فقط.", ephemeral=True)
            return None
        if interaction.user.id == claim["by"]:
            await interaction.response.send_message("انت اللي سجلت النتيجة، لازم الخصم يرد عليها.", ephemeral=True)
            return None
        return m

    @discord.ui.button(label="أوافق", emoji="✅", style=discord.ButtonStyle.success, custom_id="v1:accept")
    async def accept_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        m = await self._check(interaction)
        if not m:
            return
        claim = m["claim"]
        claim["status"] = "accepted"
        save_data()
        await interaction.response.edit_message(view=None)
        await finish_match(interaction.channel, m, claim["s1"], claim["s2"], "اتفاق اللاعبين ✅")

    @discord.ui.button(label="أرفض", emoji="❌", style=discord.ButtonStyle.danger, custom_id="v1:reject")
    async def reject_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        m = await self._check(interaction)
        if not m:
            return
        await interaction.response.send_modal(RejectModal())


class DisputeView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="استدعاء أونر", emoji="🚨", style=discord.ButtonStyle.danger, custom_id="v1:dispute")
    async def call_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await do_call_owner(interaction)


class EndModal(discord.ui.Modal):
    def __init__(self, name1, name2):
        super().__init__(title="🏁 إنهاء القيم")
        self.s1 = discord.ui.TextInput(
            label=("1️⃣ نتيجة " + name1)[:45], placeholder="من 0 إلى " + str(WIN_SCORE), max_length=2
        )
        self.s2 = discord.ui.TextInput(
            label=("2️⃣ نتيجة " + name2)[:45], placeholder="من 0 إلى " + str(WIN_SCORE), max_length=2
        )
        self.add_item(self.s1)
        self.add_item(self.s2)

    async def on_submit(self, interaction: discord.Interaction):
        m = get_match(interaction.channel_id)
        if not m or m.get("done"):
            await interaction.response.send_message("المباراة منتهية.", ephemeral=True)
            return
        if not is_owner(interaction.user):
            await interaction.response.send_message("🔒 للأونر فقط.", ephemeral=True)
            return
        a = parse_score(self.s1.value)
        b = parse_score(self.s2.value)
        if a is None or b is None:
            await interaction.response.send_message(
                "❌ اكتب أرقام صحيحة من 0 إلى " + str(WIN_SCORE) + ".", ephemeral=True
            )
            return
        claim = m.get("claim")
        if claim and claim["status"] == "pending":
            await strip_buttons(interaction.channel, claim.get("msg"))
        await interaction.response.send_message("✅ تم تثبيت النتيجة.", ephemeral=True)
        await finish_match(
            interaction.channel, m, a, b, "قرار الأونر 👑 " + interaction.user.mention
        )


# ============================================================
#                        الأوامر
# ============================================================


@bot.event
async def on_ready():
    print("✅ شغّال كـ", bot.user)
    try:
        synced = await bot.tree.sync()
        print("تم مزامنة", len(synced), "أمر سلاش")
    except Exception as e:
        print("خطأ في المزامنة:", repr(e))


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, (commands.CommandOnCooldown, commands.CommandNotFound)):
        return
    if isinstance(error, (commands.BadArgument, commands.MissingRequiredArgument)):
        try:
            await ctx.send(
                "❌ الصيغة غلط. أمثلة:\n"
                "`!addpts @اللاعب 30 سبب اختياري`\n"
                "`!removepts @اللاعب 10`\n"
                "`!setpts @اللاعب 250`"
            )
        except Exception:
            pass
        return
    print("خطأ أمر:", repr(error))


@bot.command(name="1v1", aliases=["ابدا", "setup1v1"])
@commands.cooldown(1, 20, commands.BucketType.channel)
async def panel_cmd(ctx):
    await ctx.send(embed=panel_embed(), view=PanelView())


@bot.tree.command(name="1v1", description="ابحث عن خصم 1v1")
async def slash_1v1(interaction: discord.Interaction):
    await handle_join(interaction)


@bot.tree.command(name="panel1v1", description="انشر لوحة نظام 1v1")
@discord.app_commands.default_permissions(administrator=True)
async def slash_panel(interaction: discord.Interaction):
    await interaction.response.send_message(embed=panel_embed(), view=PanelView())


@bot.command(name="top", aliases=["المتصدرين", "lb"])
@commands.cooldown(1, 10, commands.BucketType.channel)
async def top_cmd(ctx):
    await ctx.send(embed=leaderboard_embed(), view=LeaderboardView())


@bot.command(name="setlb", aliases=["لوحة_المتصدرين"])
async def setlb_cmd(ctx):
    if ctx.guild is None or not is_owner(ctx.author):
        return
    msg = await ctx.send(embed=leaderboard_embed(), view=LeaderboardView())
    DATA["lb"] = {"channel": ctx.channel.id, "message": msg.id}
    save_data()


@bot.tree.command(name="top", description="عرض المتصدرين")
async def slash_top(interaction: discord.Interaction):
    await interaction.response.send_message(embed=leaderboard_embed(), view=LeaderboardView())


@bot.tree.command(name="setleaderboard", description="انشر لوحة متصدرين تتحدث تلقائياً")
@discord.app_commands.default_permissions(administrator=True)
async def slash_setlb(interaction: discord.Interaction):
    await interaction.response.send_message(embed=leaderboard_embed(), view=LeaderboardView())
    msg = await interaction.original_response()
    DATA["lb"] = {"channel": interaction.channel_id, "message": msg.id}
    save_data()


# ============================================================
#                  إدارة النقاط (للأونر)
# ============================================================
MAX_ADJUST = 100000


def new_stats():
    return {"w": 0, "l": 0, "d": 0, "pf": 0, "pa": 0, "pts": 0}


def apply_points(uid, mode, amount):
    s = DATA["stats"].setdefault(str(uid), new_stats())
    s.setdefault("pts", 0)
    old = s["pts"]
    if mode == "add":
        new = old + amount
    elif mode == "remove":
        new = old - amount
    else:
        new = amount
    s["pts"] = max(0, new)
    save_data()
    return old, s["pts"]


def points_embed(member, mode, amount, old, new, actor, reason):
    titles = {"add": "➕ تمت زيادة نقاط", "remove": "➖ تم إنقاص نقاط", "set": "✏️ تم تحديد النقاط"}
    colors = {"add": GREEN, "remove": RED, "set": GOLD}
    e = discord.Embed(title=titles[mode], color=colors[mode])
    e.add_field(name="اللاعب", value=member.mention, inline=True)
    e.add_field(name="النقاط", value=str(old) + " ➜ **" + str(new) + "**", inline=True)
    _, old_rank, _ = rank_for(old)
    _, new_rank, _ = rank_for(new)
    if old_rank != new_rank:
        arrow = "📈" if new > old else "📉"
        e.add_field(name=arrow + " تغيّرت الرتبة", value=old_rank + " ➜ " + new_rank, inline=False)
    else:
        e.add_field(name="🏅 الرتبة", value=new_rank, inline=False)
    nxt = next_rank_for(new)
    if nxt:
        e.add_field(name="⏭️ للرتبة الجاية", value=str(nxt[0] - new) + " نقطة لـ " + nxt[1], inline=False)
    if reason:
        e.add_field(name="📝 السبب", value=reason[:300], inline=False)
    e.add_field(name="👑 بواسطة", value=actor.mention, inline=False)
    return e


async def points_action(guild, actor, member, mode, amount, reason):
    """يرجع (ok, embed_or_text)"""
    if guild is None or not is_owner(actor):
        return False, "🔒 هذا الأمر للأونر فقط."
    if member.bot:
        return False, "❌ ما تقدر تعدل نقاط بوت."
    if amount < 0 or amount > MAX_ADJUST or (mode != "set" and amount == 0):
        return False, "❌ اكتب رقم صحيح (من 1 إلى " + str(MAX_ADJUST) + ")."
    old, new = apply_points(member.id, mode, amount)
    e = points_embed(member, mode, amount, old, new, actor, reason)
    if LOG_CHANNEL_ID:
        lc = guild.get_channel(LOG_CHANNEL_ID)
        if lc is not None:
            try:
                await lc.send(embed=e, allowed_mentions=discord.AllowedMentions.none())
            except Exception as ex:
                print("تعذر الإرسال لقناة السجل:", repr(ex))
    asyncio.create_task(refresh_leaderboard())
    return True, e


@bot.command(name="addpts", aliases=["زيد", "اضف"])
async def addpts_cmd(ctx, member: discord.Member, amount: int, *, reason: str = ""):
    ok, res = await points_action(ctx.guild, ctx.author, member, "add", amount, reason)
    if ok:
        await ctx.send(embed=res, allowed_mentions=discord.AllowedMentions.none())
    else:
        await ctx.send(res)


@bot.command(name="removepts", aliases=["انقص", "خصم"])
async def removepts_cmd(ctx, member: discord.Member, amount: int, *, reason: str = ""):
    ok, res = await points_action(ctx.guild, ctx.author, member, "remove", amount, reason)
    if ok:
        await ctx.send(embed=res, allowed_mentions=discord.AllowedMentions.none())
    else:
        await ctx.send(res)


@bot.command(name="setpts", aliases=["حدد"])
async def setpts_cmd(ctx, member: discord.Member, amount: int, *, reason: str = ""):
    ok, res = await points_action(ctx.guild, ctx.author, member, "set", amount, reason)
    if ok:
        await ctx.send(embed=res, allowed_mentions=discord.AllowedMentions.none())
    else:
        await ctx.send(res)


@bot.command(name="cancel", aliases=["الغاء", "الغِ"])
async def cancel_cmd(ctx):
    if ctx.guild is None or not is_owner(ctx.author):
        return
    m = get_match(ctx.channel.id)
    if not m or m.get("done"):
        await ctx.send("❌ هذا مو روم مباراة شغالة.")
        return
    await cancel_match(ctx.channel, m, "الأونر 👑 " + ctx.author.mention)


async def _slash_points(interaction, mode, member, amount, reason):
    ok, res = await points_action(interaction.guild, interaction.user, member, mode, amount, reason or "")
    if ok:
        await interaction.response.send_message(embed=res, allowed_mentions=discord.AllowedMentions.none())
    else:
        await interaction.response.send_message(res, ephemeral=True)


@bot.tree.command(name="addpoints", description="زيادة نقاط لاعب (للأونر)")
@discord.app_commands.describe(member="اللاعب", amount="عدد النقاط", reason="السبب (اختياري)")
async def slash_addpoints(interaction: discord.Interaction, member: discord.Member, amount: int, reason: str = ""):
    await _slash_points(interaction, "add", member, amount, reason)


@bot.tree.command(name="removepoints", description="إنقاص نقاط لاعب (للأونر)")
@discord.app_commands.describe(member="اللاعب", amount="عدد النقاط", reason="السبب (اختياري)")
async def slash_removepoints(interaction: discord.Interaction, member: discord.Member, amount: int, reason: str = ""):
    await _slash_points(interaction, "remove", member, amount, reason)


@bot.tree.command(name="setpoints", description="تحديد نقاط لاعب برقم معين (للأونر)")
@discord.app_commands.describe(member="اللاعب", amount="النقاط الجديدة", reason="السبب (اختياري)")
async def slash_setpoints(interaction: discord.Interaction, member: discord.Member, amount: int, reason: str = ""):
    await _slash_points(interaction, "set", member, amount, reason)


if __name__ == "__main__":
    print("جاري تشغيل البوت...")
    try:
        bot.run(TOKEN)
    except Exception as e:
        print("خطأ:", repr(e))
