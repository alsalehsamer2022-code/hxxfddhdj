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
LOG_CHANNEL_ID = int(os.environ.get("LOG_CHANNEL_ID", "0"))  # ايدي قناة سجل النتائج (0 = يدور على روم اسمه match)
LOG_CHANNEL_NAME = "match"  # اسم الروم الاحتياطي لو الايدي = 0
CLOSE_DELAY = 10          # ثواني قبل حذف الغرفة بعد انتهاء المباراة
QUEUE_TIMEOUT = 900       # بعد كم ثانية يطلع اللاعب من قائمة الانتظار
DATA_FILE = "data_1v1.json"
MAX_PURGE_SEARCH = 5000   # أقصى عدد رسائل يفتش فيها أمر حذف رسايل العضو

BLUE = 0x5865F2
GREEN = 0x57F287
RED = 0xED4245
GOLD = 0xFEE75C

# ============================================================
#                        التخزين
# ============================================================


# --- تخزين دائم عبر Upstash Redis (مجاني) + نسخة ملف احتياطية ---
import urllib.request
from threading import Lock

UPSTASH_URL = os.environ.get("UPSTASH_REDIS_REST_URL", "").rstrip("/")
UPSTASH_TOKEN = os.environ.get("UPSTASH_REDIS_REST_TOKEN", "")
DB_KEY = "asta_1v1_data"


def _redis(cmd):
    req = urllib.request.Request(
        UPSTASH_URL,
        data=json.dumps(cmd).encode("utf-8"),
        headers={
            "Authorization": "Bearer " + UPSTASH_TOKEN,
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read().decode("utf-8"))


RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", "")  # Render يحطه تلقائي


def _keepalive():
    """يبينغ رابط الخدمة نفسه كل فترة عشان Render الفري ما ينايمها.
    نايمة الخدمة = ريستارت = ضياع DATA لو UPSTASH مو مضبوط = كل الأزرار
    ترجع 'المباراة منتهية' حتى لو المباراة شغالة فعليًا."""
    if not RENDER_URL:
        print("تنبيه: RENDER_EXTERNAL_URL مو موجود، الـ keepalive مو شغال")
        return
    while True:
        time.sleep(480)  # كل 8 دقايق، قبل ما تنايم Render الخدمة
        try:
            urllib.request.urlopen(RENDER_URL, timeout=10)
        except Exception as e:
            print("تعذر keepalive ping:", repr(e))


Thread(target=_keepalive, daemon=True).start()


_loaded_ok = False
_last_bak = {"t": 0.0}


def _file_load():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def load_data():
    """لو Upstash مضبوط وما قدرنا نقرا منه: نوقف البوت بدل ما نبدأ بداتا فاضية
    (البداية الفاضية + أول حفظ = مسح كل النقاط من Upstash نهائياً)."""
    global _loaded_ok
    d = None
    if UPSTASH_URL and UPSTASH_TOKEN:
        last = None
        for attempt in range(5):
            try:
                resp = _redis(["GET", DB_KEY])
                if resp.get("error"):
                    raise RuntimeError(resp["error"])
                res = resp.get("result")
                if res:
                    d = json.loads(res)
                    print("تم تحميل البيانات من Upstash")
                else:
                    d = {}  # المفتاح غير موجود فعلاً (أول تشغيل)
                    print("ما فيه بيانات سابقة في Upstash (أول تشغيل)")
                break
            except Exception as e:
                last = e
                print("تعذر التحميل من Upstash (محاولة " + str(attempt + 1) + "):", repr(e))
                time.sleep(3 * (attempt + 1))
        if d is None:
            raise RuntimeError("تعذر قراءة Upstash، تم الإيقاف لحماية النقاط: " + repr(last))
        if not d:
            d = _file_load()
    else:
        print("تنبيه: UPSTASH غير مضبوط، البيانات ما راح تنحفظ بعد إعادة النشر")
        d = _file_load()
    _loaded_ok = True
    d.setdefault("matches", {})
    d.setdefault("stats", {})
    d.setdefault("counter", 0)
    d.setdefault("lb", None)
    return d


DATA = load_data()
QUEUES = {}  # guild_id -> [(user_id, time)]

_save_lock = Lock()
_save_pending = {"payload": None, "running": False}


def _save_worker():
    while True:
        with _save_lock:
            payload = _save_pending["payload"]
            _save_pending["payload"] = None
            if payload is None:
                _save_pending["running"] = False
                return
        if not _loaded_ok:
            continue  # ما نكتب أبداً قبل ما نتأكد إن التحميل نجح
        try:
            tmp = DATA_FILE + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                f.write(payload)
            os.replace(tmp, DATA_FILE)
        except Exception as e:
            print("تعذر حفظ الملف:", repr(e))
        if UPSTASH_URL and UPSTASH_TOKEN:
            try:
                # كل 30 دقيقة: انسخ النسخة الحالية في Upstash لمفتاح احتياطي قبل ما نستبدلها
                if time.time() - _last_bak["t"] > 1800:
                    old = _redis(["GET", DB_KEY]).get("result")
                    if old:
                        _redis(["SET", DB_KEY + ":bak", old])
                    _last_bak["t"] = time.time()
                r = _redis(["SET", DB_KEY, payload])
                if r.get("error"):
                    print("Upstash رفض الحفظ:", r["error"])
            except Exception as e:
                print("تعذر الحفظ في Upstash:", repr(e))


def save_data():
    try:
        payload = json.dumps(DATA, ensure_ascii=False)
    except Exception as e:
        print("تعذر تجهيز البيانات:", repr(e))
        return
    with _save_lock:
        _save_pending["payload"] = payload
        if _save_pending["running"]:
            return
        _save_pending["running"] = True
    Thread(target=_save_worker, daemon=True).start()


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
        self.add_view(ModPanelView())
        asyncio.create_task(tempban_loop())


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



def get_log_channel(guild):
    """يرجع قناة سجل النتائج: بالايدي، وإذا ما انحط يدور على روم اسمه match"""
    if LOG_CHANNEL_ID:
        return guild.get_channel(LOG_CHANNEL_ID)
    for c in guild.text_channels:
        if c.name.lower() == LOG_CHANNEL_NAME:
            return c
    return None


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
        name="duel-" + str(n),
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

    if True:
        lc = get_log_channel(channel.guild)
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

    if True:
        lc = get_log_channel(channel.guild)
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
        g = interaction.guild
        p1m = g.get_member(m["p1"])
        p2m = g.get_member(m["p2"])
        n1 = p1m.display_name if p1m else str(m["p1"])
        n2 = p2m.display_name if p2m else str(m["p2"])
        await interaction.response.send_modal(ScoreModal(n1, n2))

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


class ScoreModal(discord.ui.Modal):
    def __init__(self, name1, name2):
        super().__init__(title="📝 تسجيل النتيجة")
        self.s1_input = discord.ui.TextInput(
            label=("1️⃣ نتيجة " + name1)[:45], placeholder="من 0 إلى " + str(WIN_SCORE), max_length=2
        )
        self.s2_input = discord.ui.TextInput(
            label=("2️⃣ نتيجة " + name2)[:45], placeholder="من 0 إلى " + str(WIN_SCORE), max_length=2
        )
        self.add_item(self.s1_input)
        self.add_item(self.s2_input)

    async def on_submit(self, interaction: discord.Interaction):
        m = get_match(interaction.channel_id)
        if not m or m.get("done"):
            await interaction.response.send_message("المباراة منتهية.", ephemeral=True)
            return
        s1 = parse_score(self.s1_input.value)
        s2 = parse_score(self.s2_input.value)
        if s1 is None or s2 is None:
            await interaction.response.send_message(
                "❌ اكتب أرقام صحيحة من 0 إلى " + str(WIN_SCORE) + ".", ephemeral=True
            )
            return
        if max(s1, s2) != WIN_SCORE or s1 == s2:
            await interaction.response.send_message(
                "❌ لازم أحد اللاعبين يوصل **" + str(WIN_SCORE) + "** والثاني أقل منه.", ephemeral=True
            )
            return

        reporter = interaction.user.id
        opp = m["p2"] if reporter == m["p1"] else m["p1"]

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
                "`!setpts @اللاعب 250`\n"
                "`!kick @الشخص سبب`\n"
                "`!ban @الشخص 7ي سبب` (أو `دائم`)\n"
                "`!timeout @الشخص 30د سبب`\n"
                "`!unban ايدي_الشخص`"
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
    if True:
        lc = get_log_channel(guild)
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


# ============================================================
#                  حذف رسايل عضو معيّن (للأونر)
# ============================================================


class DeleteUserMessagesConfirmView(discord.ui.View):
    def __init__(self, member, limit):
        super().__init__(timeout=60)
        self.member = member
        self.limit = limit

    @discord.ui.button(label="تأكيد الحذف", emoji="🗑️", style=discord.ButtonStyle.danger)
    async def yes_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_owner(interaction.user):
            await interaction.response.send_message("🔒 للأونر فقط.", ephemeral=True)
            return
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(content="⏳ جاري الحذف...", view=self)
        try:
            deleted = await interaction.channel.purge(
                limit=self.limit, check=lambda msg: msg.author.id == self.member.id
            )
        except discord.Forbidden:
            await interaction.followup.send(
                "❌ ما عندي صلاحية **Manage Messages** بهذي القناة.", ephemeral=True
            )
            return
        except Exception as e:
            print("خطأ حذف رسايل عضو:", repr(e))
            await interaction.followup.send("❌ صار خطأ أثناء الحذف.", ephemeral=True)
            return
        await interaction.followup.send(
            "✅ تم حذف **" + str(len(deleted)) + "** رسالة لـ " + self.member.mention
            + " بهذي القناة.",
            ephemeral=True,
        )

    @discord.ui.button(label="إلغاء", emoji="❌", style=discord.ButtonStyle.secondary)
    async def no_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(content="❌ ملغي.", view=self)


def _purge_warning(member, limit):
    return (
        "⚠️ بتحذف **كل رسايل** " + member.mention + " بهذي القناة (آخر "
        + str(limit) + " رسالة يفتش فيها). هذا **لا رجعة فيه**. متأكد؟\n"
        "-# ملاحظة: ديسكورد ما يسمح بحذف جماعي للرسايل الأقدم من 14 يوم، "
        "فهذي بتتحذف وحدة وحدة وبتاخذ وقت أطول."
    )


@bot.command(name="حذف_رسايل", aliases=["حذف_رسائل", "purgeuser"])
async def delmsgs_cmd(ctx, member: discord.Member, limit: int = 2000):
    if ctx.guild is None or not is_owner(ctx.author):
        return
    limit = max(1, min(limit, MAX_PURGE_SEARCH))
    await ctx.send(_purge_warning(member, limit), view=DeleteUserMessagesConfirmView(member, limit))


@bot.tree.command(name="حذف_رسايل", description="احذف كل رسايل عضو معيّن في هذي القناة (للأونر)")
@discord.app_commands.describe(member="العضو", limit="كم رسالة يفتش فيها بالقناة (افتراضي 2000)")
async def slash_delmsgs(interaction: discord.Interaction, member: discord.Member, limit: int = 2000):
    if interaction.guild is None or not is_owner(interaction.user):
        await interaction.response.send_message("🔒 هذا الأمر للأونر فقط.", ephemeral=True)
        return
    limit = max(1, min(limit, MAX_PURGE_SEARCH))
    await interaction.response.send_message(
        _purge_warning(member, limit), view=DeleteUserMessagesConfirmView(member, limit)
    )


# ============================================================
#                  تقفيل كل التكتات مرة وحدة (للإدارة)
# ============================================================
TICKET_PREFIX = "ticket-"
TICKET_ACTION_DELAY = 0.6  # ثواني بين كل تكت عشان ما ينضرب الـ rate limit


def tk_is_staff_member(member):
    p = member.guild_permissions
    return p.administrator or p.manage_channels or p.manage_guild


def tk_is_staff_role(role):
    p = role.permissions
    return p.administrator or p.manage_channels or p.manage_guild


def tk_channels(guild):
    return [c for c in guild.text_channels if c.name.lower().startswith(TICKET_PREFIX)]


async def tk_lock_channel(channel):
    """يمنع صاحب التكت (والرتب غير الإدارية) من الكتابة، ويبقي الستاف على صلاحياتهم."""
    guild = channel.guild
    for target, ow in list(channel.overwrites.items()):
        if target == guild.default_role:
            continue
        if isinstance(target, discord.Member):
            if target.bot or tk_is_staff_member(target):
                continue
        elif isinstance(target, discord.Role):
            if tk_is_staff_role(target):
                continue
        else:
            continue
        if ow.send_messages is False:
            continue
        ow.send_messages = False
        ow.add_reactions = False
        await channel.set_permissions(target, overwrite=ow, reason="تقفيل جماعي للتكتات")
    await channel.send("🔒 تم تقفيل هذا التكت من قبل الإدارة.")


async def tk_process(channel, guild, mode, invoker):
    chans = tk_channels(guild)
    if not chans:
        await channel.send("ما فيه تكتات مفتوحة.")
        return
    done, failed = 0, 0
    for ch in chans:
        try:
            if mode == "delete":
                await ch.delete(reason="حذف جماعي للتكتات بواسطة " + str(invoker))
            else:
                await tk_lock_channel(ch)
            done += 1
        except Exception as e:
            failed += 1
            print("تعذر معالجة", ch.name, repr(e))
        await asyncio.sleep(TICKET_ACTION_DELAY)

    action = "حذف" if mode == "delete" else "تقفيل"
    text = "✅ تم " + action + " **" + str(done) + "** تكت."
    if failed:
        text += "\n⚠️ فشل " + str(failed) + " تكت، تأكد إن البوت عنده صلاحية **Manage Channels**."
    try:
        await channel.send(text)
    except Exception as e:
        # إذا القناة الحالية هي نفسها اللي انحذفت، ما نقدر نرسل فيها
        print("تعذر إرسال النتيجة:", repr(e))


def tk_confirm_text(count, mode):
    if mode == "delete":
        return "⚠️ بتحذف **" + str(count) + "** تكت نهائياً. ما فيه رجعة. متأكد؟"
    return "⚠️ بتقفل **" + str(count) + "** تكت (صاحب التكت ما يقدر يكتب فيه). متأكد؟"


class TicketConfirmView(discord.ui.View):
    def __init__(self, mode):
        super().__init__(timeout=60)
        self.mode = mode

    @discord.ui.button(label="تأكيد", emoji="✅", style=discord.ButtonStyle.danger)
    async def tk_yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild is None or not tk_is_staff_member(interaction.user):
            await interaction.response.send_message("🔒 للإدارة فقط.", ephemeral=True)
            return
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(content="⏳ جاري المعالجة...", view=self)
        await tk_process(interaction.channel, interaction.guild, self.mode, interaction.user)

    @discord.ui.button(label="إلغاء", emoji="❌", style=discord.ButtonStyle.secondary)
    async def tk_no(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(content="❌ ملغي.", view=self)


@bot.command(name="closetickets", aliases=["تقفيل_التكتات"])
@commands.has_permissions(manage_channels=True)
async def closetickets_cmd(ctx, mode: str = "lock"):
    """!closetickets          → يقفل كل التكتات
       !closetickets delete   → يحذف كل التكتات"""
    mode = mode.lower()
    if mode not in ("lock", "delete"):
        await ctx.send("❌ الوضع لازم يكون `lock` أو `delete`.")
        return
    count = len(tk_channels(ctx.guild))
    if count == 0:
        await ctx.send("ما فيه تكتات مفتوحة.")
        return
    await ctx.send(tk_confirm_text(count, mode), view=TicketConfirmView(mode))


@closetickets_cmd.error
async def closetickets_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("🔒 هذا الأمر للإدارة فقط.")


@bot.tree.command(name="closetickets", description="قفّل كل التكتات مرة وحدة (للإدارة)")
@discord.app_commands.describe(delete="احذف التكتات بدل ما تقفلها (افتراضي: لا)")
@discord.app_commands.default_permissions(manage_channels=True)
async def slash_closetickets(interaction: discord.Interaction, delete: bool = False):
    if interaction.guild is None or not tk_is_staff_member(interaction.user):
        await interaction.response.send_message("🔒 هذا الأمر للإدارة فقط.", ephemeral=True)
        return
    mode = "delete" if delete else "lock"
    count = len(tk_channels(interaction.guild))
    if count == 0:
        await interaction.response.send_message("ما فيه تكتات مفتوحة.", ephemeral=True)
        return
    await interaction.response.send_message(
        tk_confirm_text(count, mode), view=TicketConfirmView(mode), ephemeral=True
    )


# ============================================================
#                  الطرد / الباند / التايم أوت
# ============================================================
from datetime import timedelta

_AR_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
_UNIT_SECONDS = {"s": 1, "ث": 1, "m": 60, "د": 60, "h": 3600, "س": 3600,
                 "d": 86400, "ي": 86400, "w": 604800, "أ": 604800, "ا": 604800}
_PERM_WORDS = {"perm", "permanent", "forever", "دائم", "دايم", "للابد", "للأبد"}
MAX_TIMEOUT = 28 * 86400


def parse_duration(text, require_unit=False):
    """يرجع (صحيح؟, ثواني أو None للدائم)."""
    t = (text or "").strip().lower().translate(_AR_DIGITS)
    if not t:
        return False, None
    if t in _PERM_WORDS:
        return True, None
    m = re.fullmatch(r"(\d+)\s*([a-zA-Zثدسيأا]\S*)?", t)
    if not m:
        return False, None
    n = int(m.group(1))
    unit = m.group(2)
    if unit is None:
        if require_unit:
            return False, None
        mult = 60  # بدون وحدة = دقايق
    else:
        mult = _UNIT_SECONDS.get(unit[0])
        if mult is None:
            return False, None
    if n <= 0:
        return False, None
    return True, n * mult


def fmt_duration(sec):
    if sec is None:
        return "دائم ♾️"
    parts = []
    for name, size in (("يوم", 86400), ("ساعة", 3600), ("دقيقة", 60), ("ثانية", 1)):
        if sec >= size:
            parts.append(str(sec // size) + " " + name)
            sec %= size
    return " و ".join(parts) or "0"


ACTION_INFO = {
    "kick": ("👢 طرد", RED),
    "ban": ("🔨 باند", RED),
    "timeout": ("🔇 تايم أوت", GOLD),
    "unban": ("♻️ فك باند", GREEN),
}


def can_mod(member, action):
    if member is None or getattr(member, "guild", None) is None:
        return False
    if is_owner(member):
        return True
    p = member.guild_permissions
    if action == "kick":
        return p.kick_members
    if action in ("ban", "unban"):
        return p.ban_members
    if action == "timeout":
        return p.moderate_members
    return False


def hierarchy_error(guild, actor, target):
    if target.id == actor.id:
        return "❌ ما تقدر تسوي هذا على نفسك."
    if bot.user and target.id == bot.user.id:
        return "❌ ما أقدر أسوي هذا على نفسي."
    if target.id == guild.owner_id:
        return "❌ ما تقدر على صاحب السيرفر."
    if isinstance(target, discord.Member) and actor.id != guild.owner_id and target.top_role >= actor.top_role:
        return "❌ رتبته أعلى منك أو تساويك."
    return None


async def _mod_dm(target, guild, action, seconds, reason):
    names = {"kick": "طردك من", "ban": "حظرك من", "timeout": "كتمك (تايم أوت) في"}
    text = "⚠️ تم " + names.get(action, "") + " سيرفر **" + guild.name + "**"
    if action in ("ban", "timeout"):
        text += "\n⏱️ المدة: " + fmt_duration(seconds)
    if reason:
        text += "\n📝 السبب: " + reason
    try:
        await target.send(text)
    except Exception:
        pass


def _mod_embed(action, target, actor, seconds, reason):
    title, color = ACTION_INFO[action]
    e = discord.Embed(title=title, color=color)
    e.add_field(name="الشخص", value="<@" + str(target.id) + ">", inline=True)
    e.add_field(name="بواسطة", value=actor.mention, inline=True)
    if action in ("ban", "timeout"):
        e.add_field(name="⏱️ المدة", value=fmt_duration(seconds), inline=True)
    if reason:
        e.add_field(name="📝 السبب", value=reason[:300], inline=False)
    e.timestamp = discord.utils.utcnow()
    return e


async def _mod_log(guild, embed):
    if True:
        lc = get_log_channel(guild)
        if lc is not None:
            try:
                await lc.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())
            except Exception as ex:
                print("تعذر الإرسال لقناة السجل:", repr(ex))


async def do_mod(guild, actor, target, action, seconds, reason):
    """يرجع (ok, embed_or_text)"""
    if guild is None or not can_mod(actor, action):
        return False, "🔒 ما عندك صلاحية لهذا الإجراء."
    err = hierarchy_error(guild, actor, target)
    if err:
        return False, err
    reason = (reason or "").strip()
    audit = ("بواسطة " + str(actor) + ((" | " + reason) if reason else ""))[:480]
    try:
        if action in ("kick", "timeout"):
            member = target if isinstance(target, discord.Member) else guild.get_member(target.id)
            if member is None:
                return False, "❌ الشخص مو موجود في السيرفر."
            if action == "timeout" and (seconds is None or seconds > MAX_TIMEOUT):
                return False, "❌ مدة التايم أوت من دقيقة إلى 28 يوم."
            await _mod_dm(member, guild, action, seconds, reason)
            if action == "kick":
                await guild.kick(member, reason=audit)
            else:
                await member.timeout(timedelta(seconds=seconds), reason=audit)
        elif action == "ban":
            await _mod_dm(target, guild, action, seconds, reason)
            await guild.ban(target, reason=audit, delete_message_seconds=0)
            tb = DATA.setdefault("tempbans", {})
            key = str(guild.id) + ":" + str(target.id)
            if seconds:
                tb[key] = {"guild": guild.id, "user": target.id, "until": time.time() + seconds}
            else:
                tb.pop(key, None)
            save_data()
    except discord.Forbidden:
        return False, "❌ ما أقدر أنفذها. تأكد إن رتبة البوت **أعلى** من رتبة الشخص وإن عنده الصلاحية."
    except discord.HTTPException as e:
        return False, "❌ فشل التنفيذ: " + str(e)[:150]
    e = _mod_embed(action, target, actor, seconds, reason)
    await _mod_log(guild, e)
    return True, e


async def do_unban(guild, actor, user_id, reason):
    if guild is None or not can_mod(actor, "unban"):
        return False, "🔒 ما عندك صلاحية لهذا الإجراء."
    reason = (reason or "").strip()
    try:
        user = discord.Object(id=user_id)
        await guild.unban(user, reason=("بواسطة " + str(actor) + ((" | " + reason) if reason else ""))[:480])
    except discord.NotFound:
        return False, "❌ هذا الشخص مو محظور."
    except discord.Forbidden:
        return False, "❌ ما عندي صلاحية **Ban Members**."
    except discord.HTTPException as e:
        return False, "❌ فشل: " + str(e)[:150]
    DATA.setdefault("tempbans", {}).pop(str(guild.id) + ":" + str(user_id), None)
    save_data()
    e = _mod_embed("unban", user, actor, None, reason)
    await _mod_log(guild, e)
    return True, e


async def tempban_loop():
    """يفك الباند المؤقت لما تخلص مدته (محفوظ في DATA فيشتغل حتى بعد ريستارت)."""
    await bot.wait_until_ready()
    while not bot.is_closed():
        try:
            now = time.time()
            for key, t in list(DATA.setdefault("tempbans", {}).items()):
                if t.get("until", 0) > now:
                    continue
                g = bot.get_guild(t["guild"])
                if g is None:
                    continue
                try:
                    await g.unban(discord.Object(id=t["user"]), reason="انتهت مدة الباند")
                except discord.NotFound:
                    pass
                except Exception as e:
                    print("تعذر فك الباند المؤقت:", repr(e))
                    continue
                DATA["tempbans"].pop(key, None)
                save_data()
        except Exception as e:
            print("خطأ tempban_loop:", repr(e))
        await asyncio.sleep(30)


# ---------- لوحة الأزرار: زر → اختيار الشخص → مدة وسبب ----------
class ModModal(discord.ui.Modal):
    def __init__(self, action, target):
        super().__init__(title=ACTION_INFO[action][0] + " — " + (getattr(target, "display_name", None) or str(target))[:25])
        self.action = action
        self.target = target
        self.duration = None
        if action in ("ban", "timeout"):
            self.duration = discord.ui.TextInput(
                label="المدة (30د / 2س / 7ي / 1أ)" + (" أو دائم" if action == "ban" else ""),
                placeholder="مثال: 2س" + ("  — اتركه فاضي = دائم" if action == "ban" else ""),
                max_length=20,
                required=(action == "timeout"),
            )
            self.add_item(self.duration)
        self.reason = discord.ui.TextInput(
            label="السبب (اختياري)", style=discord.TextStyle.paragraph, required=False, max_length=300
        )
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction):
        seconds = None
        if self.duration is not None:
            raw = (self.duration.value or "").strip()
            if raw or self.action == "timeout":
                ok, seconds = parse_duration(raw)
                if not ok:
                    await interaction.response.send_message("❌ مدة غير صحيحة. مثال: `30د` `2س` `7ي` `دائم`", ephemeral=True)
                    return
                if self.action == "timeout" and seconds is None:
                    await interaction.response.send_message("❌ التايم أوت ما يكون دائم.", ephemeral=True)
                    return
        await interaction.response.defer(ephemeral=True)
        ok, res = await do_mod(interaction.guild, interaction.user, self.target, self.action, seconds, self.reason.value)
        if not ok:
            await interaction.followup.send(res, ephemeral=True)
            return
        await interaction.followup.send("✅ تم.", ephemeral=True)
        try:
            await interaction.channel.send(embed=res, allowed_mentions=discord.AllowedMentions.none())
        except Exception:
            pass


class UnbanModal(discord.ui.Modal, title="♻️ فك باند"):
    uid = discord.ui.TextInput(label="ايدي الشخص", placeholder="123456789012345678", max_length=25)
    reason = discord.ui.TextInput(label="السبب (اختياري)", required=False, max_length=300)

    async def on_submit(self, interaction: discord.Interaction):
        raw = self.uid.value.strip().translate(_AR_DIGITS)
        if not raw.isdigit():
            await interaction.response.send_message("❌ اكتب الايدي أرقام فقط.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        ok, res = await do_unban(interaction.guild, interaction.user, int(raw), self.reason.value)
        if not ok:
            await interaction.followup.send(res, ephemeral=True)
            return
        await interaction.followup.send("✅ تم فك الباند.", ephemeral=True)
        try:
            await interaction.channel.send(embed=res, allowed_mentions=discord.AllowedMentions.none())
        except Exception:
            pass


class ModTargetView(discord.ui.View):
    def __init__(self, action):
        super().__init__(timeout=120)
        self.action = action

    @discord.ui.select(cls=discord.ui.UserSelect, placeholder="اختر الشخص", min_values=1, max_values=1)
    async def pick(self, interaction: discord.Interaction, select: discord.ui.UserSelect):
        if not can_mod(interaction.user, self.action):
            await interaction.response.send_message("🔒 ما عندك صلاحية.", ephemeral=True)
            return
        await interaction.response.send_modal(ModModal(self.action, select.values[0]))


async def _open_mod(interaction, action):
    if interaction.guild is None or not can_mod(interaction.user, action):
        await interaction.response.send_message("🔒 ما عندك صلاحية لهذا الإجراء.", ephemeral=True)
        return
    if action == "unban":
        await interaction.response.send_modal(UnbanModal())
        return
    await interaction.response.send_message("اختر الشخص:", view=ModTargetView(action), ephemeral=True)


class ModPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="طرد", emoji="👢", style=discord.ButtonStyle.secondary, custom_id="mod:kick", row=0)
    async def kick_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await _open_mod(interaction, "kick")

    @discord.ui.button(label="باند", emoji="🔨", style=discord.ButtonStyle.danger, custom_id="mod:ban", row=0)
    async def ban_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await _open_mod(interaction, "ban")

    @discord.ui.button(label="تايم أوت", emoji="🔇", style=discord.ButtonStyle.primary, custom_id="mod:timeout", row=0)
    async def timeout_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await _open_mod(interaction, "timeout")

    @discord.ui.button(label="فك باند", emoji="♻️", style=discord.ButtonStyle.success, custom_id="mod:unban", row=0)
    async def unban_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await _open_mod(interaction, "unban")


def modpanel_embed():
    e = discord.Embed(
        title="🛡️ لوحة الإدارة",
        description="اضغط الزر، اختر الشخص، حدد المدة والسبب.\nالمدة: `30د` دقيقة • `2س` ساعة • `7ي` يوم • `1أ` أسبوع • `دائم`",
        color=BLUE,
    )
    return e


# ---------- أوامر بالبريفكس ----------
async def _send_result(ctx, ok, res):
    if ok:
        await ctx.send(embed=res, allowed_mentions=discord.AllowedMentions.none())
    else:
        await ctx.send(res)


@bot.command(name="modpanel", aliases=["لوحة_الادارة"])
async def modpanel_cmd(ctx):
    if ctx.guild is None or not (can_mod(ctx.author, "kick") or can_mod(ctx.author, "ban")):
        return
    await ctx.send(embed=modpanel_embed(), view=ModPanelView())


@bot.command(name="kick", aliases=["طرد"])
async def kick_cmd(ctx, member: discord.Member, *, reason: str = ""):
    ok, res = await do_mod(ctx.guild, ctx.author, member, "kick", None, reason)
    await _send_result(ctx, ok, res)


@bot.command(name="ban", aliases=["باند", "حظر"])
async def ban_cmd(ctx, user: discord.User, *, rest: str = ""):
    seconds, reason = None, rest
    parts = rest.split(None, 1)
    if parts:
        ok, secs = parse_duration(parts[0], require_unit=True)
        if ok:
            seconds = secs
            reason = parts[1] if len(parts) > 1 else ""
    ok, res = await do_mod(ctx.guild, ctx.author, user, "ban", seconds, reason)
    await _send_result(ctx, ok, res)


@bot.command(name="timeout", aliases=["تايم", "اسكت"])
async def timeout_cmd(ctx, member: discord.Member, duration: str, *, reason: str = ""):
    ok, secs = parse_duration(duration)
    if not ok or secs is None:
        await ctx.send("❌ مدة غير صحيحة. مثال: `!timeout @الشخص 30د سبب`")
        return
    ok, res = await do_mod(ctx.guild, ctx.author, member, "timeout", secs, reason)
    await _send_result(ctx, ok, res)


@bot.command(name="unban", aliases=["فك_باند"])
async def unban_cmd(ctx, user_id: int, *, reason: str = ""):
    ok, res = await do_unban(ctx.guild, ctx.author, user_id, reason)
    await _send_result(ctx, ok, res)


# ---------- أوامر سلاش ----------
async def _slash_result(interaction, ok, res):
    if ok:
        await interaction.response.send_message(embed=res, allowed_mentions=discord.AllowedMentions.none())
    else:
        await interaction.response.send_message(res, ephemeral=True)


@bot.tree.command(name="modpanel", description="انشر لوحة الطرد والباند (للإدارة)")
async def slash_modpanel(interaction: discord.Interaction):
    if interaction.guild is None or not (can_mod(interaction.user, "kick") or can_mod(interaction.user, "ban")):
        await interaction.response.send_message("🔒 للإدارة فقط.", ephemeral=True)
        return
    await interaction.response.send_message(embed=modpanel_embed(), view=ModPanelView())


@bot.tree.command(name="kick", description="طرد عضو")
@discord.app_commands.describe(member="العضو", reason="السبب (اختياري)")
async def slash_kick(interaction: discord.Interaction, member: discord.Member, reason: str = ""):
    ok, res = await do_mod(interaction.guild, interaction.user, member, "kick", None, reason)
    await _slash_result(interaction, ok, res)


@bot.tree.command(name="ban", description="باند عضو (دائم أو مؤقت)")
@discord.app_commands.describe(user="الشخص", duration="المدة مثل 30د / 2س / 7ي / دائم (فاضي = دائم)", reason="السبب (اختياري)")
async def slash_ban(interaction: discord.Interaction, user: discord.User, duration: str = "", reason: str = ""):
    seconds = None
    if duration.strip():
        ok, seconds = parse_duration(duration)
        if not ok:
            await interaction.response.send_message("❌ مدة غير صحيحة. مثال: `30د` `2س` `7ي` `دائم`", ephemeral=True)
            return
    ok, res = await do_mod(interaction.guild, interaction.user, user, "ban", seconds, reason)
    await _slash_result(interaction, ok, res)


@bot.tree.command(name="timeout", description="كتم عضو مؤقتاً (تايم أوت)")
@discord.app_commands.describe(member="العضو", duration="المدة مثل 30د / 2س / 7ي (حد أقصى 28 يوم)", reason="السبب (اختياري)")
async def slash_timeout(interaction: discord.Interaction, member: discord.Member, duration: str, reason: str = ""):
    ok, secs = parse_duration(duration)
    if not ok or secs is None:
        await interaction.response.send_message("❌ مدة غير صحيحة. مثال: `30د` `2س` `7ي`", ephemeral=True)
        return
    ok, res = await do_mod(interaction.guild, interaction.user, member, "timeout", secs, reason)
    await _slash_result(interaction, ok, res)


@bot.tree.command(name="unban", description="فك باند عن شخص بالايدي")
@discord.app_commands.describe(user_id="ايدي الشخص", reason="السبب (اختياري)")
async def slash_unban(interaction: discord.Interaction, user_id: str, reason: str = ""):
    raw = user_id.strip().translate(_AR_DIGITS)
    if not raw.isdigit():
        await interaction.response.send_message("❌ اكتب الايدي أرقام فقط.", ephemeral=True)
        return
    ok, res = await do_unban(interaction.guild, interaction.user, int(raw), reason)
    await _slash_result(interaction, ok, res)


if __name__ == "__main__":
    print("جاري تشغيل البوت...")
    try:
        bot.run(TOKEN)
    except Exception as e:
        print("خطأ:", repr(e))
