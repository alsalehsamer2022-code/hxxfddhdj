import json
import os
import secrets
import time
from threading import Lock, Thread

import discord
from discord import app_commands
from discord.ext import commands
from flask import Flask, Response, request

# ---- سيرفر ويب صغير عشان Render ما يوقف الخدمة ----
_web = Flask(__name__)


@_web.route("/")
def _home():
    return "Key panel bot is running"



# ============================================================
#                        الإعدادات
# ============================================================
TOKEN = os.environ["DISCORD_TOKEN"]
OWNER_IDS = {1441717777558798397}  # الأونر الوحيد
# سيرفرات مسموحة فقط (ايدي السيرفر). لو فاضي ما فيه تقييد
ALLOWED_GUILDS = {int(x) for x in os.environ.get("GUILD_IDS", "").replace(" ", "").split(",") if x.isdigit()}
BUYER_ROLE_ID = int(os.environ.get("BUYER_ROLE_ID", "0"))   # رتبة المشترين (0 = بدون)
PROJECT_NAME = os.environ.get("PROJECT_NAME", "My Project")  # اسم مشروعك في اللوحة
# النص اللي يستلمه المشتري عند الضغط على Get Script (رابط التحميل أو اللودر حقك)
SCRIPT_TEXT = os.environ.get("SCRIPT_TEXT", "ضع هنا رابط أو لودر المشروع (متغير SCRIPT_TEXT).")
PUBLIC_URL = os.environ.get("PUBLIC_URL", "https://hxxfddhdj-1.onrender.com").rstrip("/")   # رابط خدمة Render مثل https://xxx.onrender.com
SCRIPT_FILE = os.environ.get("SCRIPT_FILE", "protected_script.lua")  # ملف السكربت الحقيقي (يبقى على السيرفر فقط)
RESET_COOLDOWN = 24 * 3600  # كل كم ثانية يقدر المشتري يعمل Reset

DATA_FILE = "keys_data.json"
BLUE, GREEN, RED = 0x5865F2, 0x57F287, 0xED4245

# ============================================================
#                        التخزين
# ============================================================


def load():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
    except Exception:
        d = {}
    d.setdefault("keys", {})   # key -> {"days": int, "used_by": uid|None}
    d.setdefault("users", {})  # uid -> {"key","redeemed","expires","resets","last_reset"}
    return d


DATA = load()


_save_lock = Lock()


def save():
    with _save_lock:
        tmp = DATA_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(DATA, f, ensure_ascii=False)
        os.replace(tmp, DATA_FILE)


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
#     التحقق من الجهاز وتسليم السكربت (يشتغل من اللودر)
# ============================================================
def script_body():
    try:
        with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return None


@_web.route("/script")
def serve_script():
    key = (request.args.get("key") or "").strip().upper()
    hwid = (request.args.get("hwid") or "").strip()
    if len(hwid) < 8 or len(hwid) > 128 or not hwid.replace("-", "").isalnum():
        return Response('warn("[license] invalid device id")', 400, mimetype="text/plain")
    info = DATA["keys"].get(key)
    if not info or not info.get("used_by"):
        return Response('warn("[license] invalid key")', 403, mimetype="text/plain")
    u = DATA["users"].get(str(info["used_by"]))
    if not u or u.get("key") != key:
        return Response('warn("[license] invalid key")', 403, mimetype="text/plain")
    if u["expires"] and u["expires"] < time.time():
        return Response('warn("[license] key expired")', 403, mimetype="text/plain")
    bound = u.get("hwid")
    if not bound:
        u["hwid"] = hwid       # أول جهاز يستخدمه يتسجّل
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


class PanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Redeem Key", emoji="🔑", style=discord.ButtonStyle.success, custom_id="kp:redeem", row=0)
    async def redeem(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RedeemModal())

    @discord.ui.button(label="Get Script", emoji="📜", style=discord.ButtonStyle.primary, custom_id="kp:script", row=0)
    async def get_script(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not active_license(interaction.user.id):
            await interaction.response.send_message("🔒 ما عندك ترخيص فعّال. فعّل مفتاحك أول.", ephemeral=True)
            return
        u = active_license(interaction.user.id)
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


@bot.event
async def on_guild_join(guild):
    if ALLOWED_GUILDS and guild.id not in ALLOWED_GUILDS:
        await guild.leave()


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
    keys = []
    for _ in range(count):
        k = "-".join(secrets.token_hex(2).upper() for _ in range(3))
        DATA["keys"][k] = {"days": days, "used_by": None}
        keys.append(k)
    save()
    await interaction.response.send_message(
        "🔑 المفاتيح (" + ("مدى الحياة" if not days else str(days) + " يوم") + "):\n```\n" + "\n".join(keys) + "\n```",
        ephemeral=True,
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


if __name__ == "__main__":
    Thread(target=lambda: _web.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000))), daemon=True).start()
    bot.run(TOKEN)
