"""
bot.py — Discord obfuscation bot v2.1
requires: pip install discord.py
place luraph_style_mobile.py in same folder
"""

import discord
from discord import app_commands
import os
import re
import tempfile
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

TOKEN = os.getenv("DISCORD_TOKEN")

sys.path.insert(0, os.path.dirname(__file__))
from luraph_style_mobile import LuraphStyleObf, deobfuscate_strings


# ── health server ──────────────────────────────────────
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")
    def log_message(self, *args):
        pass

def run_health_server():
    port = int(os.getenv("PORT", 10000))
    HTTPServer(("0.0.0.0", port), HealthHandler).serve_forever()


# ── detect ─────────────────────────────────────────────
def detect_obfuscation(src: str) -> str:
    results = []
    if re.search(r'local\s+\w+\s*=\s*\(getfenv', src):
        results.append("🔴 Luraph (getfenv pattern)")
    if re.search(r'string\.byte.*string\.char.*%\s*256', src):
        results.append("🔴 Luraph-style XOR decrypt")
    if re.search(r'IronBrew', src, re.IGNORECASE):
        results.append("🟠 IronBrew")
    if re.search(r'local\s+\w+\s*=\s*\{[01,\s]{20,}\}', src):
        results.append("🟠 IronBrew2 (VM bytecode array)")
    if re.search(r'\\x[0-9a-fA-F]{2}', src) and src.count('\\x') > 20:
        results.append("🟡 Hex-encoded strings")
    if re.search(r'Prometheus', src, re.IGNORECASE):
        results.append("🟡 Prometheus")
    if re.search(r'bxor|bit\.bxor|~\s*\d', src):
        results.append("⚪ Generic XOR / bit ops")
    if re.search(r'local\s+\w+\s*=\s*\{[^}]{500,}\}', src) and src.count('function') > 10:
        results.append("🟣 Custom VM")
    if not results:
        if len(re.findall(r'\b[IlO0ij1oL]{8,}\b', src)) > 10:
            results.append("✅ luraph_style (هذا البوت)")
        else:
            results.append("✅ Plain Lua — مفيش تشفير")
    return "\n".join(results)


def obfuscate_lua(src: str) -> tuple[str, str]:
    obf = LuraphStyleObf()
    result = obf.obfuscate(src)
    return result, f"{obf.seed:#018x}"


# ── client ─────────────────────────────────────────────
class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default() | discord.Intents(message_content=True))
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()

client = MyClient()


# ── slash commands ──────────────────────────────────────
@client.tree.command(name="get", description="تشفير ملف Lua")
async def cmd_get(interaction: discord.Interaction, file: discord.Attachment):
    if not file.filename.endswith(".lua"):
        await interaction.response.send_message("⚠️ الملف مش `.lua`", ephemeral=True)
        return
    await interaction.response.defer()
    data = await file.read()
    try:
        src = data.decode("utf-8")
    except UnicodeDecodeError:
        await interaction.followup.send("❌ مش قادر يقرأ الملف")
        return
    try:
        obf_src, seed_hex = obfuscate_lua(src)
    except Exception as e:
        await interaction.followup.send(f"❌ error: `{e}`")
        return
    base = file.filename.rsplit(".", 1)[0]
    out_name = f"{base}_obf.lua"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.lua', encoding='utf-8', delete=False) as tmp:
        tmp.write(obf_src)
        tmp_path = tmp.name
    try:
        await interaction.followup.send(
            f"✅ **{out_name}** جاهز\nseed: `{seed_hex}`\n"
            f"الحجم: `{len(src):,}` → `{len(obf_src):,}` chars",
            file=discord.File(tmp_path, filename=out_name)
        )
    finally:
        os.unlink(tmp_path)


@client.tree.command(name="deobf", description="فك تشفير ملف Lua (Luraph-style)")
async def cmd_deobf(interaction: discord.Interaction, file: discord.Attachment):
    if not file.filename.endswith(".lua"):
        await interaction.response.send_message("⚠️ الملف مش `.lua`", ephemeral=True)
        return
    await interaction.response.defer()
    data = await file.read()
    try:
        src = data.decode("utf-8", errors="replace")
    except Exception:
        await interaction.followup.send("❌ مش قادر يقرأ الملف")
        return
    try:
        dec_func, strings = deobfuscate_strings(src)
    except Exception as e:
        await interaction.followup.send(f"❌ error: `{e}`")
        return

    if dec_func is None or not strings:
        await interaction.followup.send(
            "⚠️ ما لقيت تشفير Luraph-style في الملف\n"
            "جرّب `/sss` تعرف نوع التشفير أول"
        )
        return

    # بناء ملف النتيجة
    lines = [f"فك تشفير: {file.filename}", f"دالة الفك: {dec_func}",
             f"عدد الـ strings: {len(strings)}", "=" * 50, ""]
    for i, (orig, dec) in enumerate(strings, 1):
        lines.append(f"[{i}] → {dec!r}")
    out_text = "\n".join(lines)

    # ملخص أول 15 للرسالة
    preview = "\n".join(f"`{dec}`" for _, dec in strings[:15])
    if len(strings) > 15:
        preview += f"\n_... و {len(strings)-15} أكثر في الملف_"

    out_name = file.filename.rsplit(".", 1)[0] + "_decoded.txt"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', encoding='utf-8', delete=False) as tmp:
        tmp.write(out_text)
        tmp_path = tmp.name
    try:
        await interaction.followup.send(
            f"🔓 **{file.filename}** — فُكّ تشفيره\n"
            f"دالة الفك: `{dec_func}` | strings: `{len(strings)}`\n\n"
            f"**أول النتائج:**\n{preview}",
            file=discord.File(tmp_path, filename=out_name)
        )
    finally:
        os.unlink(tmp_path)


@client.tree.command(name="sss", description="كشف نوع تشفير ملف Lua")
async def cmd_sss(interaction: discord.Interaction, file: discord.Attachment):
    if not file.filename.endswith(".lua"):
        await interaction.response.send_message("⚠️ الملف مش `.lua`", ephemeral=True)
        return
    await interaction.response.defer()
    data = await file.read()
    try:
        src = data.decode("utf-8")
    except UnicodeDecodeError:
        src = data.decode("latin-1")
    detection = detect_obfuscation(src)
    await interaction.followup.send(
        f"**📄 {file.filename}**\n"
        f"الحجم: `{len(data):,} bytes` | الأسطر: `{src.count(chr(10))+1:,}`\n\n"
        f"**🔍 نوع التشفير:**\n{detection}"
    )


@client.tree.command(name="help", description="قائمة الأوامر")
async def cmd_help(interaction: discord.Interaction):
    await interaction.response.send_message(
        "**الأوامر:**\n"
        "`/get` — تشفير ملف `.lua`\n"
        "`/deobf` — فك تشفير ملف `.lua` (Luraph-style)\n"
        "`/sss` — كشف نوع التشفير\n"
        "`/help` — القائمة دي"
    )


@client.event
async def on_ready():
    print(f"[✓] bot online: {client.user}")


# ── run ─────────────────────────────────────────────────
threading.Thread(target=run_health_server, daemon=True).start()
client.run(TOKEN)
