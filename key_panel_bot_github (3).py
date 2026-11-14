import asyncio
import base64
import json
import os
import secrets
import time
from collections import defaultdict
from threading import Lock, Thread

import discord
import urllib.request
import urllib.error
from discord import app_commands
from discord.ext import commands
from flask import Flask, Response, request

_web = Flask(__name__)

@_web.route("/")
def _home():
    return "Key panel bot is running"

# ============================================================
#                        الإعدادات
# ============================================================
TOKEN = os.environ["DISCORD_TOKEN"]
OWNER_IDS = {1441717777558798397, 1521996879473283271}
ALLOWED_GUILDS = {int(x) for x in os.environ.get("GUILD_IDS", "").replace(" ", "").split(",") if x.isdigit()}
BUYER_ROLE_ID = int(os.environ.get("BUYER_ROLE_ID", "0"))
PROJECT_NAME = os.environ.get("PROJECT_NAME", "My Project")
SCRIPT_TEXT = os.environ.get("SCRIPT_TEXT", "ضع هنا رابط أو لودر المشروع (متغير SCRIPT_TEXT).")
PUBLIC_URL = os.environ.get("PUBLIC_URL", "https://hxxfddhdj-1.onrender.com").rstrip("/")
SCRIPT_FILE = os.environ.get("SCRIPT_FILE", "protected_script.lua")
RESET_COOLDOWN = 24 * 3600

DATA_FILE = "keys_data.json"
BLUE, GREEN, RED = 0x5865F2, 0x57F287, 0xED4245

# rate limiting: max 10 requests per minute per IP
_rate_data = defaultdict(list)
_rate_lock = Lock()
RATE_LIMIT = 10
RATE_WINDOW = 60

_hwid_blacklist = set()

# brute force: max failed key attempts per HWID before auto-ban
BRUTEFORCE_LIMIT = 5
BRUTEFORCE_WINDOW = 300  # seconds
_bf_attempts: dict = defaultdict(list)  # hwid -> [timestamps]
_bf_lock = Lock()


def _record_failed_attempt(hwid: str) -> bool:
    """record a bad-key attempt; return True if hwid just hit the limit and was auto-banned."""
    now = time.time()
    with _bf_lock:
        hits = _bf_attempts[hwid]
        _bf_attempts[hwid] = [t for t in hits if now - t < BRUTEFORCE_WINDOW]
        _bf_attempts[hwid].append(now)
        if len(_bf_attempts[hwid]) >= BRUTEFORCE_LIMIT:
            _hwid_blacklist.add(hwid)
            DATA["blacklist"] = list(_hwid_blacklist)
            return True
    return False

def is_rate_limited(ip):
    now = time.time()
    with _rate_lock:
        hits = _rate_data[ip]
        _rate_data[ip] = [t for t in hits if now - t < RATE_WINDOW]
        if len(_rate_data[ip]) >= RATE_LIMIT:
            return True
        _rate_data[ip].append(now)
        return False

# ============================================================
#                   GitHub Storage
# ============================================================
GH_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GH_REPO  = os.environ.get("GITHUB_REPO", "alsalehsamer2022-code/hxxfddhdj")
GH_PATH  = os.environ.get("GITHUB_DATA_PATH", "keys_data.json")
GH_API   = "https://api.github.com/repos/" + GH_REPO + "/contents/" + GH_PATH

_save_lock = Lock()
_gh_sha = None


def _gh_headers():
    return {
        "Authorization": "Bearer " + GH_TOKEN,
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def load():
    global _gh_sha
    d = {}
    if GH_TOKEN:
        try:
            req = urllib.request.Request(GH_API, headers=_gh_headers())
            with urllib.request.urlopen(req, timeout=10) as r:
                resp = json.loads(r.read())
            _gh_sha = resp.get("sha")
            content = base64.b64decode(resp["content"]).decode("utf-8")
            d = json.loads(content)
            print("✅ GitHub data loaded, sha=" + str(_gh_sha))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                print("⚠️ keys_data.json مش موجود على GitHub، رح ينشئه عند أول save")
            else:
                print("GitHub load error:", e.code, e.reason)
        except Exception as e:
            print("GitHub load error:", repr(e))
    else:
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
        except Exception:
            pass
    d.setdefault("keys", {})
    d.setdefault("users", {})
    d.setdefault("blacklist", [])
    return d


def save():
    global _gh_sha
    with _save_lock:
        content_b64 = base64.b64encode(json.dumps(DATA, ensure_ascii=False).encode()).decode()
        if GH_TOKEN:
            try:
                payload = {"message": "update keys_data", "content": content_b64}
                if _gh_sha:
                    payload["sha"] = _gh_sha
                data_bytes = json.dumps(payload).encode()
                req = urllib.request.Request(GH_API, data=data_bytes, headers=_gh_headers(), method="PUT")
                with urllib.request.urlopen(req, timeout=10) as r:
                    resp = json.loads(r.read())
                _gh_sha = resp["content"]["sha"]
            except Exception as e:
                print("GitHub save error:", repr(e))
        else:
            tmp = DATA_FILE + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(DATA, f, ensure_ascii=False)
            os.replace(tmp, DATA_FILE)


try:
    DATA = load()
except Exception as e:
    print("load failed:", repr(e))
    DATA = {"keys": {}, "users": {}, "blacklist": []}

_hwid_blacklist = set(DATA.get("blacklist", []))


def is_owner(user):
    return user.id in OWNER_IDS


def active_license(uid):
    u = DATA["users"].get(str(uid))
    if not u:
        return None
    if u["expires"] and u["expires"] < time.time():
        return None
    return u


def fmt_expiry(u):
    return "مدى الحياة ♾️" if not u["expires"] else "<t:" + str(int(u["expires"])) + ":R>"


async def give_role(member):
    if BUYER_ROLE_ID and isinstance(member, discord.Member):
        role = member.guild.get_role(BUYER_ROLE_ID)
        if role is not None:
            try:
                await member.add_roles(role, reason="تفعيل مفتاح")
                return True
            except Exception as e:
                print("تعذر إعطاء الرتبة:", repr(e))
    return False


# ============================================================
#     التحقق من الجهاز وتسليم السكربت
# ============================================================
def script_body():
    try:
        with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return None


@_web.route("/script")
def serve_script():
    ip = request.headers.get("X-Forwarded-For", request.remote_addr).split(",")[0].strip()
    if is_rate_limited(ip):
        return Response('warn("[license] too many requests")', 429, mimetype="text/plain")
    key = (request.args.get("key") or "").strip().upper()
    hwid = (request.args.get("hwid") or "").strip()
    if len(hwid) < 8 or len(hwid) > 128 or not hwid.replace("-", "").isalnum():
        return Response('warn("[license] invalid device id")', 400, mimetype="text/plain")
    if hwid in _hwid_blacklist:
        return Response('warn("[license] device banned")', 403, mimetype="text/plain")
    info = DATA["keys"].get(key)
    if not info or not info.get("used_by"):
        auto_banned = _record_failed_attempt(hwid)
        if auto_banned:
            asyncio.run_coroutine_threadsafe(
                notify_owners(
                    "🤖 **Auto-Ban HWID (brute force)**\n"
                    "HWID: `" + hwid + "`\n"
                    "سبب: " + str(BRUTEFORCE_LIMIT) + " محاولات خاطئة خلال " + str(BRUTEFORCE_WINDOW // 60) + " دقيقة"
                ),
                bot.loop,
            )
            save()
        return Response('warn("[license] invalid key")', 403, mimetype="text/plain")
    u = DATA["users"].get(str(info["used_by"]))
    if not u or u.get("key") != key:
        return Response('warn("[license] invalid key")', 403, mimetype="text/plain")
    if u["expires"] and u["expires"] < time.time():
        return Response('warn("[license] key expired")', 403, mimetype="text/plain")
    if u.get("paused"):
        return Response('warn("[license] key paused by admin")', 403, mimetype="text/plain")
    bound = u.get("hwid")
    if not bound:
        u["hwid"] = hwid
        save()
    elif bound != hwid:
        return Response('warn("[license] this key is locked to another device")', 403, mimetype="text/plain")
    body = script_body()
    if body is None:
        return Response('warn("[license] script not available yet")', 503, mimetype="text/plain")
    return Response(body, mimetype="text/plain")


def loader_line(key):
    return (
        'loadstring(game:HttpGet("' + PUBLIC_URL + '/script?key=' + key
        + '&hwid=" .. game:GetService("RbxAnalyticsService"):GetClientId()))()'
    )


async def notify_owners(text):
    for oid in OWNER_IDS:
        try:
            user = await bot.fetch_user(oid)
            await user.send(text)
        except Exception as e:
            print("تعذر إرسال إشعار للأونر:", repr(e))


# ============================================================
#                        الواجهة
# ============================================================
class RedeemModal(discord.ui.Modal, title="تفعيل المفتاح"):
    key = discord.ui.TextInput(label="المفتاح", placeholder="XXXX-XXXX-XXXX", min_length=6, max_length=40)

    async def on_submit(self, interaction: discord.Interaction):
        k = self.key.value.strip().upper()
        info = DATA["keys"].get(k)
        if info is None:
            await interaction.response.send_message("❌ المفتاح غير صحيح.", ephemeral=True)
            return
        if info["used_by"]:
            await interaction.response.send_message("❌ هذا المفتاح مستخدم من قبل.", ephemeral=True)
            return
        if active_license(interaction.user.id):
            await interaction.response.send_message("⚠️ عندك ترخيص فعّال بالفعل.", ephemeral=True)
            return
        now = time.time()
        info["used_by"] = interaction.user.id
        DATA["users"][str(interaction.user.id)] = {
            "key": k,
            "redeemed": now,
            "expires": (now + info["days"] * 86400) if info["days"] else 0,
            "resets": 0,
            "last_reset": 0,
        }
        save()
        got_role = await give_role(interaction.user)
        await interaction.response.send_message(
            "✅ تم تفعيل المفتاح! اضغط **Get Script** لاستلام المشروع."
            + (" وتم إعطاؤك رتبة المشتري." if got_role else ""),
            ephemeral=True,
        )
        exp = ("مدى الحياة ♾️" if not info["days"] else "<t:" + str(int(now + info["days"] * 86400)) + ":R>")
        await notify_owners(
            "🔑 **تفعيل مفتاح**\n"
            "المشتري: " + interaction.user.mention + " (`" + str(interaction.user.id) + "`)\n"
            "المفتاح: `" + k + "`\n"
            "الصلاحية: " + exp
        )


class PanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Redeem Key", emoji="🔑", style=discord.ButtonStyle.success, custom_id="kp:redeem", row=0)
    async def redeem(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RedeemModal())

    @discord.ui.button(label="Get Script", emoji="📜", style=discord.ButtonStyle.primary, custom_id="kp:script", row=0)
    async def get_script(self, interaction: discord.Interaction, button: discord.ui.Button):
        u = active_license(interaction.user.id)
        if not u:
            await interaction.response.send_message("🔒 ما عندك ترخيص فعّال. فعّل مفتاحك أول.", ephemeral=True)
            return
        await interaction.response.send_message(
            "📜 انسخ هذا السطر وشغّله. **مربوط بجهازك الأول**، وإذا أعطيته لشخص ما راح يشتغل عنده:\n```lua\n"
            + loader_line(u["key"]) + "\n```",
            ephemeral=True,
        )

    @discord.ui.button(label="Get Role", emoji="👤", style=discord.ButtonStyle.primary, custom_id="kp:role", row=1)
    async def get_role(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not active_license(interaction.user.id):
            await interaction.response.send_message("🔒 ما عندك ترخيص فعّال.", ephemeral=True)
            return
        ok = await give_role(interaction.user)
        await interaction.response.send_message(
            "✅ تم إعطاؤك الرتبة." if ok else "⚠️ ما قدرت أعطيك الرتبة (تأكد من BUYER_ROLE_ID وصلاحيات البوت).",
            ephemeral=True,
        )

    @discord.ui.button(label="Reset HWID", emoji="⚙️", style=discord.ButtonStyle.secondary, custom_id="kp:reset", row=1)
    async def reset(self, interaction: discord.Interaction, button: discord.ui.Button):
        u = active_license(interaction.user.id)
        if not u:
            await interaction.response.send_message("🔒 ما عندك ترخيص فعّال.", ephemeral=True)
            return
        left = u["last_reset"] + RESET_COOLDOWN - time.time()
        if left > 0:
            await interaction.response.send_message(
                "⏳ تقدر تعمل Reset بعد **" + str(int(left // 3600) + 1) + "** ساعة.", ephemeral=True
            )
            return
        u["resets"] += 1
        u["last_reset"] = time.time()
        u["hwid"] = None
        save()
        await interaction.response.send_message(
            "✅ تم تصفير ربط الجهاز. أول جهاز تشغّل عليه السكربت بعد الآن يتسجّل.", ephemeral=True
        )
        await notify_owners(
            "⚙️ **Reset HWID**\nالمشتري: " + interaction.user.mention + " (`" + str(interaction.user.id) + "`)\n"
            "عدد المرات الكلي: **" + str(u["resets"]) + "**"
        )

    @discord.ui.button(label="Get Stats", emoji="📊", style=discord.ButtonStyle.secondary, custom_id="kp:stats", row=2)
    async def stats(self, interaction: discord.Interaction, button: discord.ui.Button):
        u = DATA["users"].get(str(interaction.user.id))
        if not u:
            await interaction.response.send_message("ما عندك ترخيص مسجّل.", ephemeral=True)
            return
        e = discord.Embed(title="📊 إحصائياتك", color=BLUE)
        e.add_field(name="الحالة", value="فعّال ✅" if active_license(interaction.user.id) else "منتهي ❌", inline=True)
        e.add_field(name="ينتهي", value=fmt_expiry(u), inline=True)
        e.add_field(name="تاريخ التفعيل", value="<t:" + str(int(u["redeemed"])) + ":D>", inline=True)
        e.add_field(name="عدد الـ Reset", value=str(u["resets"]), inline=True)
        await interaction.response.send_message(embed=e, ephemeral=True)


# ============================================================
#                        البوت
# ============================================================
intents = discord.Intents.default()


class KeyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents, status=discord.Status.invisible)

    async def setup_hook(self):
        self.add_view(PanelView())
        await self.tree.sync()


bot = KeyBot()


@bot.event
async def on_ready():
    print("✅ شغّال كـ", bot.user)
    if ALLOWED_GUILDS:
        for g in bot.guilds:
            if g.id not in ALLOWED_GUILDS:
                await g.leave()
    await notify_owners(
        "🟢 **البوت شغال / ريستارت**\n"
        "الوقت: <t:" + str(int(time.time())) + ":F>\n"
        "السيرفرات: **" + str(len(bot.guilds)) + "**"
    )
    bot.loop.create_task(daily_report())
    bot.loop.create_task(expiry_notifier())


@bot.event
async def on_guild_join(guild):
    if ALLOWED_GUILDS and guild.id not in ALLOWED_GUILDS:
        await guild.leave()


# ============================================================
#                   Daily Report
# ============================================================
async def daily_report():
    await bot.wait_until_ready()
    while True:
        await asyncio.sleep(86400)
        now = time.time()
        total = len(DATA["users"])
        active = sum(1 for u in DATA["users"].values() if not u["expires"] or u["expires"] > now)
        expired = total - active
        total_resets = sum(u.get("resets", 0) for u in DATA["users"].values())
        await notify_owners(
            "📋 **تقرير يومي — " + PROJECT_NAME + "**\n"
            "المشترين الكلي: **" + str(total) + "**\n"
            "فعّالين: **" + str(active) + "**\n"
            "منتهين: **" + str(expired) + "**\n"
            "Resets الكلي: **" + str(total_resets) + "**"
        )


# ============================================================
#                   Expiry Notifier (3 days)
# ============================================================
async def expiry_notifier():
    await bot.wait_until_ready()
    notified = set()
    while True:
        await asyncio.sleep(3600)
        now = time.time()
        for uid, u in DATA["users"].items():
            if not u["expires"]:
                continue
            left = u["expires"] - now
            if 0 < left < 3 * 86400 and uid not in notified:
                try:
                    user = await bot.fetch_user(int(uid))
                    await user.send(
                        "⚠️ **تنبيه انتهاء الترخيص**\n"
                        "ترخيصك في **" + PROJECT_NAME + "** ينتهي " + fmt_expiry(u) + ".\n"
                        "تواصل مع الأونر للتجديد."
                    )
                    notified.add(uid)
                except Exception:
                    pass


# ============================================================
#                        الأوامر
# ============================================================
@bot.tree.command(name="panel", description="انشر لوحة التحكم (للأونر)")
async def panel(interaction: discord.Interaction):
    if not is_owner(interaction.user):
        await interaction.response.send_message("🔒 للأونر فقط.", ephemeral=True)
        return
    e = discord.Embed(
        title=PROJECT_NAME + " Control Panel",
        description="لوحة التحكم الخاصة بمشروع **" + PROJECT_NAME + "**.\n"
        "إذا كنت مشتري، اضغط الأزرار بالأسفل لتفعيل مفتاحك أو استلام المشروع أو الرتبة.",
        color=BLUE,
    )
    await interaction.response.send_message(embed=e, view=PanelView())


@bot.tree.command(name="genkey", description="توليد مفاتيح جديدة (للأونر)")
@app_commands.describe(count="عدد المفاتيح (1-100)", days="مدة الصلاحية بالأيام (0 = مدى الحياة)")
async def genkey(interaction: discord.Interaction, count: app_commands.Range[int, 1, 100] = 1,
                 days: app_commands.Range[int, 0, 3650] = 30):
    if not is_owner(interaction.user):
        await interaction.response.send_message("🔒 للأونر فقط.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    keys = []
    for _ in range(count):
        k = "-".join(secrets.token_hex(2).upper() for _ in range(3))
        DATA["keys"][k] = {"days": days, "used_by": None}
        keys.append(k)
    await asyncio.to_thread(save)
    await interaction.followup.send(
        "🔑 المفاتيح (" + ("مدى الحياة" if not days else str(days) + " يوم") + "):\n```\n" + "\n".join(keys) + "\n```",
        ephemeral=True,
    )
    await notify_owners(
        "🗝️ **توليد مفاتيح**\n"
        "بواسطة: " + interaction.user.mention + "\n"
        "العدد: **" + str(count) + "** | المدة: " + ("مدى الحياة" if not days else str(days) + " يوم") + "\n"
        "المفاتيح:\n```\n" + "\n".join(keys) + "\n```"
    )


@bot.tree.command(name="revoke", description="سحب ترخيص مشتري (للأونر)")
async def revoke(interaction: discord.Interaction, member: discord.Member):
    if not is_owner(interaction.user):
        await interaction.response.send_message("🔒 للأونر فقط.", ephemeral=True)
        return
    u = DATA["users"].pop(str(member.id), None)
    if not u:
        await interaction.response.send_message("هذا العضو ما عنده ترخيص.", ephemeral=True)
        return
    save()
    if BUYER_ROLE_ID:
        role = interaction.guild.get_role(BUYER_ROLE_ID)
        if role is not None:
            try:
                await member.remove_roles(role, reason="سحب ترخيص")
            except Exception as e:
                print("تعذر سحب الرتبة:", repr(e))
    await interaction.response.send_message("✅ تم سحب الترخيص من " + member.mention, ephemeral=True)


@bot.tree.command(name="resetuser", description="تصفير HWID لمشتري بدون cooldown (للأونر)")
@app_commands.describe(member="المشتري")
async def resetuser(interaction: discord.Interaction, member: discord.Member):
    if not is_owner(interaction.user):
        await interaction.response.send_message("🔒 للأونر فقط.", ephemeral=True)
        return
    u = DATA["users"].get(str(member.id))
    if not u:
        await interaction.response.send_message("هذا العضو ما عنده ترخيص.", ephemeral=True)
        return
    u["hwid"] = None
    u["last_reset"] = 0
    save()
    await interaction.response.send_message(
        "✅ تم تصفير HWID لـ " + member.mention + ". يقدر يستخدم Reset الحين.", ephemeral=True
    )
    await notify_owners(
        "🔧 **Owner Reset HWID**\nبواسطة: " + interaction.user.mention +
        "\nللمشتري: " + member.mention + " (`" + str(member.id) + "`)"
    )


@bot.tree.command(name="addtime", description="تمديد ترخيص مشتري (للأونر)")
@app_commands.describe(member="المشتري", days="عدد الأيام للإضافة")
async def addtime(interaction: discord.Interaction, member: discord.Member, days: app_commands.Range[int, 1, 3650]):
    if not is_owner(interaction.user):
        await interaction.response.send_message("🔒 للأونر فقط.", ephemeral=True)
        return
    u = DATA["users"].get(str(member.id))
    if not u:
        await interaction.response.send_message("هذا العضو ما عنده ترخيص.", ephemeral=True)
        return
    if not u["expires"]:
        await interaction.response.send_message("ترخيصه مدى الحياة، ما يحتاج تمديد.", ephemeral=True)
        return
    u["expires"] += days * 86400
    save()
    await interaction.response.send_message(
        "✅ تم إضافة **" + str(days) + "** يوم لـ " + member.mention + ". ينتهي " + fmt_expiry(u),
        ephemeral=True,
    )


@bot.tree.command(name="listusers", description="قائمة المشترين (للأونر)")
async def listusers(interaction: discord.Interaction):
    if not is_owner(interaction.user):
        await interaction.response.send_message("🔒 للأونر فقط.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    now = time.time()
    if not DATA["users"]:
        await interaction.followup.send("ما في مشترين.", ephemeral=True)
        return
    lines = []
    for uid, u in DATA["users"].items():
        status = "✅" if (not u["expires"] or u["expires"] > now) else "❌"
        exp = "♾️" if not u["expires"] else "<t:" + str(int(u["expires"])) + ":d>"
        lines.append(status + " <@" + uid + "> | ينتهي: " + exp + " | Reset: " + str(u.get("resets", 0)))
    e = discord.Embed(title="👥 المشترين — " + PROJECT_NAME, color=BLUE,
                      description="\n".join(lines[:25]))
    e.set_footer(text="الكلي: " + str(len(DATA["users"])))
    await interaction.followup.send(embed=e, ephemeral=True)


@bot.tree.command(name="ownerstats", description="إحصائيات المشروع (للأونر)")
async def ownerstats(interaction: discord.Interaction):
    if not is_owner(interaction.user):
        await interaction.response.send_message("🔒 للأونر فقط.", ephemeral=True)
        return
    now = time.time()
    total = len(DATA["users"])
    active = sum(1 for u in DATA["users"].values() if not u["expires"] or u["expires"] > now)
    expired = total - active
    unused_keys = sum(1 for k in DATA["keys"].values() if not k["used_by"])
    total_resets = sum(u.get("resets", 0) for u in DATA["users"].values())
    blacklisted = len(_hwid_blacklist)
    e = discord.Embed(title="📊 إحصائيات " + PROJECT_NAME, color=BLUE)
    e.add_field(name="المشترين الكلي", value=str(total), inline=True)
    e.add_field(name="فعّالين", value=str(active), inline=True)
    e.add_field(name="منتهين", value=str(expired), inline=True)
    e.add_field(name="مفاتيح غير مستخدمة", value=str(unused_keys), inline=True)
    e.add_field(name="Resets الكلي", value=str(total_resets), inline=True)
    e.add_field(name="HWIDs محجوبة", value=str(blacklisted), inline=True)
    await interaction.response.send_message(embed=e, ephemeral=True)


@bot.tree.command(name="banhwid", description="حجب HWID (للأونر)")
@app_commands.describe(hwid="الـ HWID المراد حجبه")
async def banhwid(interaction: discord.Interaction, hwid: str):
    if not is_owner(interaction.user):
        await interaction.response.send_message("🔒 للأونر فقط.", ephemeral=True)
        return
    _hwid_blacklist.add(hwid)
    DATA["blacklist"] = list(_hwid_blacklist)
    save()
    await interaction.response.send_message("🚫 تم حجب HWID: `" + hwid + "`", ephemeral=True)


@bot.tree.command(name="unbanhwid", description="رفع حجب HWID (للأونر)")
@app_commands.describe(hwid="الـ HWID المراد رفع حجبه")
async def unbanhwid(interaction: discord.Interaction, hwid: str):
    if not is_owner(interaction.user):
        await interaction.response.send_message("🔒 للأونر فقط.", ephemeral=True)
        return
    _hwid_blacklist.discard(hwid)
    DATA["blacklist"] = list(_hwid_blacklist)
    save()
    await interaction.response.send_message("✅ تم رفع حجب HWID: `" + hwid + "`", ephemeral=True)


# ============================================================
#              banhwid by member
# ============================================================
@bot.tree.command(name="banhwiduser", description="حجب HWID مشتري مباشرة بالمنشن (للأونر)")
@app_commands.describe(member="المشتري")
async def banhwiduser(interaction: discord.Interaction, member: discord.Member):
    if not is_owner(interaction.user):
        await interaction.response.send_message("🔒 للأونر فقط.", ephemeral=True)
        return
    u = DATA["users"].get(str(member.id))
    if not u or not u.get("hwid"):
        await interaction.response.send_message("هذا العضو ما عنده HWID مسجّل.", ephemeral=True)
        return
    hwid = u["hwid"]
    _hwid_blacklist.add(hwid)
    DATA["blacklist"] = list(_hwid_blacklist)
    save()
    await interaction.response.send_message(
        "🚫 تم حجب HWID لـ " + member.mention + "\nHWID: `" + hwid + "`", ephemeral=True
    )
    await notify_owners(
        "🚫 **banhwid by member**\nبواسطة: " + interaction.user.mention +
        "\nالعضو: " + member.mention + " (`" + str(member.id) + "`)\nHWID: `" + hwid + "`"
    )


# ============================================================
#              transfer license
# ============================================================
@bot.tree.command(name="transfer", description="نقل ترخيص من مشتري لآخر (للأونر)")
@app_commands.describe(from_member="المشتري الأصلي", to_member="المشتري الجديد",
                       keep_hwid="ابقِ HWID المرتبط؟ (افتراضي: لا)")
async def transfer(interaction: discord.Interaction, from_member: discord.Member,
                   to_member: discord.Member, keep_hwid: bool = False):
    if not is_owner(interaction.user):
        await interaction.response.send_message("🔒 للأونر فقط.", ephemeral=True)
        return
    src = DATA["users"].pop(str(from_member.id), None)
    if not src:
        await interaction.response.send_message("المشتري الأصلي ما عنده ترخيص.", ephemeral=True)
        return
    if DATA["users"].get(str(to_member.id)):
        await interaction.response.send_message(
            "⚠️ " + to_member.mention + " عنده ترخيص بالفعل. revoke أول.", ephemeral=True
        )
        DATA["users"][str(from_member.id)] = src  # rollback
        return
    if not keep_hwid:
        src["hwid"] = None
        src["last_reset"] = 0
    DATA["users"][str(to_member.id)] = src
    # update key ownership
    key_info = DATA["keys"].get(src["key"])
    if key_info:
        key_info["used_by"] = to_member.id
    save()
    # adjust roles
    if BUYER_ROLE_ID:
        role = interaction.guild.get_role(BUYER_ROLE_ID)
        if role:
            try:
                await from_member.remove_roles(role, reason="نقل ترخيص")
            except Exception:
                pass
            try:
                await to_member.add_roles(role, reason="نقل ترخيص")
            except Exception:
                pass
    await interaction.response.send_message(
        "✅ تم نقل الترخيص من " + from_member.mention + " إلى " + to_member.mention +
        ("\n🔗 HWID محتفظ به." if keep_hwid else "\n🔄 HWID تم تصفيره للعضو الجديد."),
        ephemeral=True,
    )
    await notify_owners(
        "🔀 **Transfer License**\nبواسطة: " + interaction.user.mention +
        "\nمن: " + from_member.mention + " → إلى: " + to_member.mention +
        "\nHWID: " + ("محتفظ" if keep_hwid else "صُفِّر")
    )


# ============================================================
#              pause / resume license
# ============================================================
@bot.tree.command(name="pause", description="تجميد ترخيص (يوقف عداد الوقت) (للأونر)")
@app_commands.describe(member="المشتري")
async def pause_license(interaction: discord.Interaction, member: discord.Member):
    if not is_owner(interaction.user):
        await interaction.response.send_message("🔒 للأونر فقط.", ephemeral=True)
        return
    u = DATA["users"].get(str(member.id))
    if not u:
        await interaction.response.send_message("هذا العضو ما عنده ترخيص.", ephemeral=True)
        return
    if u.get("paused"):
        await interaction.response.send_message("⚠️ الترخيص مجمّد بالفعل.", ephemeral=True)
        return
    if not u["expires"]:
        await interaction.response.send_message("ترخيصه مدى الحياة، التجميد ما يؤثر عليه.", ephemeral=True)
        return
    u["paused"] = True
    u["paused_at"] = time.time()
    save()
    await interaction.response.send_message("⏸️ تم تجميد ترخيص " + member.mention, ephemeral=True)
    await notify_owners(
        "⏸️ **Pause License**\nبواسطة: " + interaction.user.mention +
        "\nالعضو: " + member.mention
    )


@bot.tree.command(name="resume", description="استئناف ترخيص مجمّد (للأونر)")
@app_commands.describe(member="المشتري")
async def resume_license(interaction: discord.Interaction, member: discord.Member):
    if not is_owner(interaction.user):
        await interaction.response.send_message("🔒 للأونر فقط.", ephemeral=True)
        return
    u = DATA["users"].get(str(member.id))
    if not u:
        await interaction.response.send_message("هذا العضو ما عنده ترخيص.", ephemeral=True)
        return
    if not u.get("paused"):
        await interaction.response.send_message("⚠️ الترخيص مش مجمّد.", ephemeral=True)
        return
    # extend expiry by frozen duration
    frozen_duration = time.time() - u.get("paused_at", time.time())
    if u["expires"]:
        u["expires"] += frozen_duration
    u.pop("paused", None)
    u.pop("paused_at", None)
    save()
    await interaction.response.send_message(
        "▶️ تم استئناف ترخيص " + member.mention +
        "\n+**" + str(int(frozen_duration // 3600)) + "** ساعة أُضيفت للصلاحية.",
        ephemeral=True,
    )
    await notify_owners(
        "▶️ **Resume License**\nبواسطة: " + interaction.user.mention +
        "\nالعضو: " + member.mention +
        "\nمدة التجميد: " + str(int(frozen_duration // 3600)) + " ساعة أُعيدت"
    )


# ============================================================
#              whois hwid
# ============================================================
@bot.tree.command(name="whoishwid", description="اعرف مين يملك HWID معيّن (للأونر)")
@app_commands.describe(hwid="الـ HWID")
async def whoishwid(interaction: discord.Interaction, hwid: str):
    if not is_owner(interaction.user):
        await interaction.response.send_message("🔒 للأونر فقط.", ephemeral=True)
        return
    hwid = hwid.strip()
    matches = [(uid, u) for uid, u in DATA["users"].items() if u.get("hwid") == hwid]
    if not matches:
        banned_note = " *(محجوب)*" if hwid in _hwid_blacklist else ""
        await interaction.response.send_message(
            "❌ ما في مشتري مرتبط بهذا الـ HWID." + banned_note, ephemeral=True
        )
        return
    uid, u = matches[0]
    e = discord.Embed(title="🔍 whois HWID", color=BLUE)
    e.add_field(name="HWID", value="`" + hwid + "`", inline=False)
    e.add_field(name="المشتري", value="<@" + uid + ">", inline=True)
    e.add_field(name="المفتاح", value="`" + u.get("key", "?") + "`", inline=True)
    e.add_field(name="الحالة",
                value="فعّال ✅" if (not u["expires"] or u["expires"] > time.time()) else "منتهي ❌",
                inline=True)
    e.add_field(name="ينتهي", value=fmt_expiry(u), inline=True)
    e.add_field(name="محجوب؟", value="نعم 🚫" if hwid in _hwid_blacklist else "لا ✅", inline=True)
    await interaction.response.send_message(embed=e, ephemeral=True)


# ============================================================
#              bulk genkey → file attachment
# ============================================================
@bot.tree.command(name="genkeyfile", description="توليد مفاتيح كثيرة وتسليمها كملف .txt (للأونر)")
@app_commands.describe(count="عدد المفاتيح (1-500)", days="مدة الصلاحية بالأيام (0 = مدى الحياة)")
async def genkeyfile(interaction: discord.Interaction,
                     count: app_commands.Range[int, 1, 500] = 10,
                     days: app_commands.Range[int, 0, 3650] = 30):
    if not is_owner(interaction.user):
        await interaction.response.send_message("🔒 للأونر فقط.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    keys = []
    for _ in range(count):
        k = "-".join(secrets.token_hex(2).upper() for _ in range(3))
        DATA["keys"][k] = {"days": days, "used_by": None}
        keys.append(k)
    await asyncio.to_thread(save)
    duration_label = "مدى الحياة" if not days else str(days) + " يوم"
    file_content = (
        "# " + PROJECT_NAME + " — Keys\n"
        "# المدة: " + duration_label + "\n"
        "# التاريخ: " + str(int(time.time())) + "\n\n" +
        "\n".join(keys)
    ).encode("utf-8")
    file = discord.File(
        fp=__import__("io").BytesIO(file_content),
        filename="keys_" + duration_label.replace(" ", "_") + "_" + str(count) + ".txt"
    )
    await interaction.followup.send(
        "🔑 **" + str(count) + "** مفتاح (" + duration_label + ") — مرفق كملف.",
        file=file,
        ephemeral=True,
    )
    await notify_owners(
        "🗝️ **genkeyfile**\nبواسطة: " + interaction.user.mention +
        "\nالعدد: **" + str(count) + "** | المدة: " + duration_label
    )


if __name__ == "__main__":
    Thread(target=lambda: _web.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000))), daemon=True).start()
    bot.run(TOKEN)
