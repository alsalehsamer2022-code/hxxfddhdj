"""
bot.py — Discord obfuscation bot
requires: pip install discord.py
place luraph_style_mobile.py in same folder
"""

import discord
import os
import re
import tempfile
import sys

# ══════════════════════════════════════════════════════════════════
TOKEN = os.getenv("DISCORD_TOKEN")
# ══════════════════════════════════════════════════════════════════

# import the obfuscator directly (same folder)
sys.path.insert(0, os.path.dirname(__file__))
from luraph_style_mobile import LuraphStyleObf

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


def detect_obfuscation(src: str) -> str:
    """يحدد نوع التشفير على الملف."""
    results = []

    # Luraph signatures
    if re.search(r'local\s+\w+\s*=\s*\(getfenv', src):
        results.append("🔴 Luraph (getfenv pattern)")
    if re.search(r'string\.byte.*string\.char.*%\s*256', src):
        results.append("🔴 Luraph-style XOR decrypt")

    # IronBrew / IB2
    if re.search(r'IronBrew', src, re.IGNORECASE):
        results.append("🟠 IronBrew")
    if re.search(r'local\s+\w+\s*=\s*\{[01,\s]{20,}\}', src):
        results.append("🟠 IronBrew2 (VM bytecode array)")

    # Obfuscator.io style
    if re.search(r'\\x[0-9a-fA-F]{2}', src) and src.count('\\x') > 20:
        results.append("🟡 Hex-encoded strings (obfuscator.io style)")

    # Prometheus
    if re.search(r'Prometheus', src, re.IGNORECASE):
        results.append("🟡 Prometheus")

    # Simple XOR (generic)
    if re.search(r'bxor|bit\.bxor|~\s*\d', src):
        results.append("⚪ Generic XOR / bit ops")

    # Custom VM indicators
    if re.search(r'local\s+\w+\s*=\s*\{[^}]{500,}\}', src) and \
       src.count('function') > 10:
        results.append("🟣 Custom VM (large table + many functions)")

    # No obfuscation detected
    if not results:
        # check if it looks like our own output
        confusing_pattern = r'\b[IlO0ij1oL]{8,}\b'
        matches = re.findall(confusing_pattern, src)
        if len(matches) > 10:
            results.append("✅ luraph_style (هذا البوت) — IlO0ij1 names")
        else:
            results.append("✅ Plain Lua — مفيش تشفير واضح")

    return "\n".join(results)


def obfuscate_lua(src: str) -> tuple[str, str]:
    """يشفّر الـ Lua source، يرجع (output_str, seed_hex)."""
    obf = LuraphStyleObf()
    result = obf.obfuscate(src)
    return result, f"{obf.seed:#018x}"


@client.event
async def on_ready():
    print(f"[✓] bot online: {client.user}")


@client.event
async def on_message(msg: discord.Message):
    if msg.author.bot:
        return

    content = msg.content.strip().lower()

    # ── sss : detect obfuscation ──────────────────────────────────
    if content == "sss":
        if not msg.attachments:
            await msg.reply("ارسل ملف `.lua` مع الرسالة.")
            return

        att = msg.attachments[0]
        if not att.filename.endswith(".lua"):
            await msg.reply("⚠️ الملف مش `.lua`")
            return

        data = await att.read()
        try:
            src = data.decode("utf-8")
        except UnicodeDecodeError:
            src = data.decode("latin-1")

        detection = detect_obfuscation(src)
        lines = src.count('\n') + 1
        size  = len(data)

        report = (
            f"**📄 {att.filename}**\n"
            f"الحجم: `{size:,} bytes` | الأسطر: `{lines:,}`\n\n"
            f"**🔍 نوع التشفير:**\n{detection}"
        )
        await msg.reply(report)
        return

    # ── get : obfuscate ───────────────────────────────────────────
    if content == "get":
        if not msg.attachments:
            await msg.reply("ارسل ملف `.lua` مع الرسالة.")
            return

        att = msg.attachments[0]
        if not att.filename.endswith(".lua"):
            await msg.reply("⚠️ الملف مش `.lua`")
            return

        data = await att.read()
        try:
            src = data.decode("utf-8")
        except UnicodeDecodeError:
            await msg.reply("❌ مش قادر يقرأ الملف (encoding مش utf-8)")
            return

        await msg.reply("⏳ شغّال...")

        try:
            obf_src, seed_hex = obfuscate_lua(src)
        except Exception as e:
            await msg.reply(f"❌ error: `{e}`")
            return

        base = att.filename.rsplit(".", 1)[0]
        out_name = f"{base}_obf.lua"

        # write to temp file and send
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.lua',
            encoding='utf-8', delete=False
        ) as tmp:
            tmp.write(obf_src)
            tmp_path = tmp.name

        try:
            await msg.reply(
                f"✅ **{out_name}** جاهز\n"
                f"seed: `{seed_hex}`\n"
                f"الحجم: `{len(src):,}` → `{len(obf_src):,}` chars",
                file=discord.File(tmp_path, filename=out_name)
            )
        finally:
            os.unlink(tmp_path)
        return


client.run(TOKEN)
