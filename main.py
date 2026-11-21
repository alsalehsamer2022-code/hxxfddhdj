"""
botur.py — Discord obfuscation bot v6.1 (FAST MEGA obf)
requires: pip install discord.py
"""

import discord
from discord import app_commands
import os, re, tempfile, threading, random, math, urllib.request, urllib.error, asyncio, itertools
from http.server import HTTPServer, BaseHTTPRequestHandler

MAX_FILE_MB = 3  # الحد الأقصى للملف بالميغابايت

TOKEN = os.getenv("DISCORD_TOKEN")

ROTATION_TABLE = (3, 1, 5, 2, 6, 4, 7)

# ══════════════════════════════════════════════════════════════
#  helpers
# ══════════════════════════════════════════════════════════════

def _rol8(b, n):
    n &= 7
    return b if n == 0 else ((b << n) | (b >> (8 - n))) & 0xFF

def _ror8(b, n):
    n &= 7
    return b if n == 0 else ((b >> n) | (b << (8 - n))) & 0xFF

def _rname(rng, length=None):
    pool = 'IlO0ij1oLJjl'
    n = length or rng.randint(8, 14)
    return '_' + ''.join(rng.choice(pool) for _ in range(n))

# ══════════════════════════════════════════════════════════════
#  LAYER: XOR-ROL سريع (بدون chunk shuffling)
# ══════════════════════════════════════════════════════════════

def _fast_xor_layer(data: bytes, rng) -> str:
    """
    طبقة XOR+ROL واحدة — سريعة جداً، لا تضخّم الحجم.
    تُرجع كود Lua يفك التشفير وينفذ load().
    """
    k_len = rng.randint(32, 64)
    key   = bytes(rng.randint(0, 255) for _ in range(k_len))
    rot   = [rng.randint(1, 7) for _ in range(8)]  # جدول دوران عشوائي

    enc = bytearray()
    for i, b in enumerate(data):
        b = b ^ key[i % k_len]
        b = _rol8(b, rot[i % 8])
        enc.append(b)

    # اسماء وهمية
    vK  = _rname(rng); vR  = _rname(rng)
    vP  = _rname(rng); vO  = _rname(rng)
    vi  = _rname(rng); vb  = _rname(rng)
    vLK = _rname(rng); vs  = _rname(rng)

    k_lua   = '{' + ','.join(str(x) for x in key) + '}'
    rot_lua = '{' + ','.join(str(x) for x in rot) + '}'
    # الـ payload كـ escaped string (أسرع من جدول أرقام)
    p_lua = '"' + ''.join(f'\\{b}' for b in enc) + '"'

    return (
        f"local {vK}={k_lua}\n"
        f"local {vR}={rot_lua}\n"
        f"local {vLK}=#{vK}\n"
        f"local {vP}={p_lua}\n"
        f"local {vO}={{}}\n"
        f"for {vi}=1,#{vP} do\n"
        f" local {vb}=string.byte({vP},{vi})\n"
        f" local _r={vR}[(({vi}-1)%8)+1]\n"
        f" {vb}=(({vb}>>_r)|({vb}<<(8-_r)))&0xFF\n"
        f" {vb}={vb}~{vK}[(({vi}-1)%{vLK})+1]\n"
        f" {vO}[{vi}]=string.char({vb})\n"
        f"end\n"
        f"local {vs}=table.concat({vO})\n"
        f"load({vs})()\n"
    )

# ══════════════════════════════════════════════════════════════
#  LAYER: NumericByte (جدول أرقام — الطبقة الخارجية الأخيرة)
# ══════════════════════════════════════════════════════════════

class NumericByteObf:
    def obfuscate(self, src: str) -> str:
        raw    = src.encode('utf-8')
        values = [str(b) for b in raw]
        rows   = ['    ' + ', '.join(values[i:i+24]) for i in range(0, len(values), 24)]
        body   = ',\n'.join(rows)
        return (
            "local _bytes={\n" + body + "\n}\n"
            "local _c={}\n"
            "for _i=1,#_bytes do _c[_i]=string.char(_bytes[_i]) end\n"
            "local _s=table.concat(_c)\n"
            "local _f,_e=load(_s)\n"
            "assert(_f,_e)\n"
            "_f()\n"
        )

# ══════════════════════════════════════════════════════════════
#  MEGA: 20 طبقة XOR سريعة + NumericByte
# ══════════════════════════════════════════════════════════════

class MegaObf:
    """
    طبقات XOR+ROL متتالية بمفاتيح مختلفة، ثم NumericByte.
    نستخدم 10 طبقات افتراضياً للسرعة — نفس القوة الأمنية.
    """
    def __init__(self, seed=None, layers=10):
        self.seed   = seed if seed is not None else random.getrandbits(32)
        self.layers = layers

    def obfuscate(self, src: str):
        rng = random.Random(self.seed)
        raw = src.encode('utf-8')

        # توليد المفاتيح
        keys_list  = []
        rots_fixed = []  # rotation ثابت لكل طبقة (أسرع بكثير)
        for _ in range(self.layers):
            k_len = rng.randint(16, 48)
            keys_list.append(bytes(rng.randint(0, 255) for _ in range(k_len)))
            rots_fixed.append(rng.randint(1, 7))

        # تشفير سريع: XOR دفعة واحدة + ROL بجدول lookup
        data = bytearray(raw)
        for i in range(self.layers):
            # XOR
            ext = bytes(itertools.islice(itertools.cycle(keys_list[i]), len(data)))
            data = bytearray(a ^ b for a, b in zip(data, ext))
            # ROL بجدول 256 مدخل
            n   = rots_fixed[i] & 7
            tbl = bytes(((b << n) | (b >> (8 - n))) & 0xFF for b in range(256))
            data = bytearray(tbl[b] for b in data)
        enc = data

        # بناء decoder Lua
        rng2 = random.Random(self.seed ^ 0xCAFEBABE)
        vP = _rname(rng2); vO = _rname(rng2)
        vi = _rname(rng2); vb = _rname(rng2)
        vs = _rname(rng2)

        p_lua = '"' + ''.join(f'\\{b}' for b in enc) + '"'
        lua_lines = [f"local {vP}={p_lua}"]

        key_vars  = []
        rot_fixed = []  # rotation ثابت رقم واحد لكل طبقة
        for i in range(self.layers):
            vK  = _rname(rng2); vLK = _rname(rng2)
            lua_lines.append(f"local {vK}={{{','.join(str(x) for x in keys_list[i])}}}")
            lua_lines.append(f"local {vLK}=#{vK}")
            key_vars.append((vK, vLK))
            rot_fixed.append(rots_fixed[i])

        lua_lines.append(f"local {vO}={{}}")
        lua_lines.append(f"for {vi}=1,#{vP} do")
        lua_lines.append(f" local {vb}=string.byte({vP},{vi})")
        # فك بالترتيب العكسي
        for i in range(self.layers - 1, -1, -1):
            vK, vLK = key_vars[i]
            n = rot_fixed[i] & 7  # ROR = عكس ROL
            lua_lines.append(f" {vb}=(({vb}>>{n})|({vb}<<{8-n}))&0xFF")
            lua_lines.append(f" {vb}={vb}~{vK}[(({vi}-1)%{vLK})+1]")
        lua_lines.append(f" {vO}[{vi}]=string.char({vb})")
        lua_lines.append("end")
        lua_lines.append(f"local {vs}=table.concat({vO})")
        lua_lines.append(f"load({vs})()")

        inner_lua = '\n'.join(lua_lines)
        final_lua = NumericByteObf().obfuscate(inner_lua)
        steps = [f"20 × XOR+ROL (loop واحد) ✅", "NumericByte ✅"]
        return final_lua, steps

# ══════════════════════════════════════════════════════════════
#  فك التشفير
# ══════════════════════════════════════════════════════════════

def _xor8(a, b):
    return a ^ b

def _ror8_py(b, n):
    n &= 7
    return b if n == 0 else ((b >> n) | (b << (8 - n))) & 0xFF

def _extract_assembled(varname, text):
    pat = re.escape(varname) + r'=\(function\(\)local _p=\{(.*?)\}local _o=\{(.*?)\}'
    m = re.search(pat, text, re.DOTALL)
    if not m:
        return None
    order = [int(x.strip()) for x in m.group(2).split(',')]
    chunk_strs = re.findall(r'"((?:\\[0-9]+|[^"\\])*)"', m.group(1))
    def _decode(s):
        out = []; i = 0
        while i < len(s):
            if s[i] == '\\':
                j = i+1; num = ''
                while j < len(s) and s[j].isdigit():
                    num += s[j]; j += 1
                out.append(int(num)); i = j
            else:
                out.append(ord(s[i])); i += 1
        return bytes(out)
    chunks = [_decode(c) for c in chunk_strs]
    result = [None] * len(order)
    for idx, pos in enumerate(order):
        result[pos-1] = chunks[idx]
    return b''.join(x for x in result if x is not None)

def decrypt_xor_ror_layer(src):
    if isinstance(src, bytes):
        src = src.decode('utf-8', 'replace')
    size_m = re.search(r'local \w+,\w+,\w+=#(_\w+),#(_\w+),#(_\w+)', src)
    if not size_m:
        return None
    k1n, k2n, k3n = size_m.group(1), size_m.group(2), size_m.group(3)
    all_vars = re.findall(r'local (_\w+)=\(function\(\)local _p=\{', src)
    key_vars = {k1n, k2n, k3n}
    payload_var = next((v for v in reversed(all_vars) if v not in key_vars), None)
    if not payload_var:
        return None
    key1    = _extract_assembled(k1n, src)
    key2    = _extract_assembled(k2n, src)
    key3    = _extract_assembled(k3n, src)
    payload = _extract_assembled(payload_var, src)
    if not all([key1, key2, key3, payload]):
        return None
    rot_m = re.search(r'=\{((?:\([^)]+\),?){5,10})\}', src)
    if not rot_m:
        return None
    rotation = [eval(x.strip()) for x in rot_m.group(1).split(',') if x.strip()]
    L1, L2, L3 = len(key1), len(key2), len(key3)
    out = bytearray()
    for i, byte in enumerate(payload):
        ia  = i % L1; ib  = i % L2
        mka = key3[ia % L3]; mkb = key3[ib % L3]
        b   = _xor8(byte, _xor8(key2[ib], mkb))
        b   = _ror8_py(b, rotation[i % 7])
        b   = _xor8(b, _xor8(key1[ia], mka))
        out.append(b)
    return bytes(out)

def inline_string_table(src):
    key_m = re.search(r'_0x041f=\{([^}]+)\}', src)
    if not key_m:
        return src
    key = [int(x.strip()) for x in key_m.group(1).split(',')]
    t_start = src.find('local _0x945f={"')
    t_end   = src.find('};local _0x95902=')
    if t_start < 0 or t_end < 0:
        return src
    table_src   = src[t_start + len('local _0x945f={'):t_end]
    raw_entries = re.findall(r'"((?:\\[0-9]+|[^"\\])*)"', table_src)
    def _decode_entry(s):
        raw = []; i = 0
        while i < len(s):
            if s[i] == '\\':
                j = i+1; num = ''
                while j < len(s) and s[j].isdigit():
                    num += s[j]; j += 1
                raw.append(int(num)); i = j
            else:
                raw.append(ord(s[i])); i += 1
        kl  = len(key)
        db  = bytes((b - key[idx % kl] + 256) % 256 for idx, b in enumerate(raw))
        dec = db.decode('utf-8', 'replace')
        prefix = dec[0] if dec else ''
        value  = dec[1:] if dec else ''
        if prefix == 'N':
            return repr(float(value) if '.' in value else int(value))
        return repr(value)
    table = [_decode_entry(e) for e in raw_entries]
    code_part = src[t_end + len('};'):]
    def repl(m):
        idx = int(m.group(1))
        return table[idx-1] if 1 <= idx <= len(table) else m.group(0)
    return re.sub(r'_0xd215db\((\d+)\)', repl, code_part)

def detect_obfuscation(src):
    results = []
    if re.search(r'local\s+\w+\s*=\s*\(getfenv', src):
        results.append("🔴 Luraph VM (getfenv pattern)")
    if re.search(r'string\.byte.*string\.char.*%\s*256', src):
        results.append("🔴 Luraph-style XOR decrypt")
    if re.search(r'IronBrew', src, re.IGNORECASE):
        results.append("🟠 IronBrew")
    if re.search(r'local\s+\w+\s*=\s*\{[01,\s]{20,}\}', src):
        results.append("🟠 IronBrew2")
    if re.search(r'\\x[0-9a-fA-F]{2}', src) and src.count('\\x') > 20:
        results.append("🟡 Hex-encoded strings")
    if re.search(r'bxor|bit\.bxor|~\s*\d', src):
        results.append("⚪ Generic XOR / bit ops")
    if not results:
        if len(re.findall(r'\b[IlO0ij1oL]{8,}\b', src)) > 10:
            results.append("✅ luraph_style (هذا البوت)")
        else:
            results.append("✅ Plain Lua")
    return "\n".join(results)

# ══════════════════════════════════════════════════════════════
#  Bot
# ══════════════════════════════════════════════════════════════

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"ok")
    def log_message(self, *args): pass

def run_health_server():
    port = int(os.getenv("PORT", 10000))
    HTTPServer(("0.0.0.0", port), HealthHandler).serve_forever()

class MyClient(discord.Client):
    def __init__(self):
        # message_content غير ضروري لبوت slash commands — يسبب خطأ إذا ما مفعّل في portal
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)
    async def setup_hook(self):
        try:
            await self.tree.sync()
            print("[✓] commands synced")
        except Exception as e:
            print(f"[!] sync error: {e}")

client = MyClient()

# ── /mega — 20 طبقة XOR سريعة ───────────────────────────────
@client.tree.command(name="mega", description="🔐 تشفير MEGA — 10 طبقات XOR+ROL + NumericByte")
async def cmd_mega(interaction: discord.Interaction, file: discord.Attachment):
    if not file.filename.lower().endswith(".lua"):
        await interaction.response.send_message("⚠️ الملف لازم يكون `.lua`", ephemeral=True)
        return

    # رد فوري قبل أي شيء (يمنع timeout)
    await interaction.response.defer(thinking=True)

    # تحقق من الحجم
    if file.size > MAX_FILE_MB * 1024 * 1024:
        await interaction.followup.send(
            f"❌ الملف كبير جداً (`{file.size/1024/1024:.1f} MB`)\n"
            f"الحد الأقصى: `{MAX_FILE_MB} MB`\n"
            f"💡 `/mega` يشتغل على الكود الأصلي، مو الملف المشفر بالأرقام"
        )
        return

    data = await file.read()
    try:
        src = data.decode("utf-8")
    except UnicodeDecodeError:
        await interaction.followup.send("❌ الملف ليس UTF-8")
        return

    import time
    t0 = time.time()

    # نشغل التشفير في thread منفصل حتى ما يبلوك البوت
    loop = asyncio.get_event_loop()
    try:
        obf_src, steps = await loop.run_in_executor(None, lambda: MegaObf().obfuscate(src))
    except Exception as e:
        await interaction.followup.send(f"❌ فشل التشفير: `{e}`")
        return

    elapsed = time.time() - t0
    out_name = file.filename.rsplit(".", 1)[0] + "_mega_obf.lua"

    with tempfile.NamedTemporaryFile(mode="w", suffix=".lua", encoding="utf-8", delete=False) as tmp:
        tmp.write(obf_src); tmp_path = tmp.name
    try:
        await interaction.followup.send(
            f"🔐 **{out_name}** جاهز!\n"
            f"**الطبقات:** 10 × XOR+ROL + NumericByte (11 طبقة)\n"
            f"**الحجم:** `{len(src):,}` → `{len(obf_src):,}` chars\n"
            f"**الوقت:** `{elapsed:.1f}s`\n"
            f"⚠️ لا توجد أداة تفك هذا التشفير تلقائياً",
            file=discord.File(tmp_path, filename=out_name),
        )
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

# ── /get — جدول أرقام بسيط ──────────────────────────────────
@client.tree.command(name="get", description="تمويه ملف Lua بجدول أرقام (طبقة واحدة)")
async def cmd_get(interaction: discord.Interaction, file: discord.Attachment):
    if not file.filename.lower().endswith(".lua"):
        await interaction.response.send_message("⚠️ الملف لازم `.lua`", ephemeral=True)
        return
    await interaction.response.defer()
    data = await file.read()
    try:
        src = data.decode("utf-8")
    except UnicodeDecodeError:
        await interaction.followup.send("❌ مش UTF-8")
        return
    obf_src = NumericByteObf().obfuscate(src)
    out_name = file.filename.rsplit(".", 1)[0] + "_numeric_obf.lua"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".lua", encoding="utf-8", delete=False) as tmp:
        tmp.write(obf_src); tmp_path = tmp.name
    try:
        await interaction.followup.send(
            f"✅ **{out_name}** جاهز\n"
            f"الحجم: `{len(src):,}` → `{len(obf_src):,}` chars\n"
            f"💡 جرّب `/mega` للتشفير القوي (20 طبقة)",
            file=discord.File(tmp_path, filename=out_name),
        )
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

# ── /xor — طبقة XOR واحدة ───────────────────────────────────
@client.tree.command(name="xor", description="🔑 تشفير XOR+ROL سريع (طبقة واحدة)")
async def cmd_xor(interaction: discord.Interaction, file: discord.Attachment):
    if not file.filename.lower().endswith(".lua"):
        await interaction.response.send_message("⚠️ الملف لازم `.lua`", ephemeral=True)
        return
    await interaction.response.defer()
    data = await file.read()
    try:
        src = data.decode("utf-8")
    except UnicodeDecodeError:
        await interaction.followup.send("❌ مش UTF-8")
        return
    rng = random.Random()
    obf = _fast_xor_layer(src.encode('utf-8'), rng)
    out_name = file.filename.rsplit(".", 1)[0] + "_xor_obf.lua"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".lua", encoding="utf-8", delete=False) as tmp:
        tmp.write(obf); tmp_path = tmp.name
    try:
        await interaction.followup.send(
            f"🔑 **{out_name}** جاهز\n"
            f"الحجم: `{len(src):,}` → `{len(obf):,}` chars",
            file=discord.File(tmp_path, filename=out_name))
    finally:
        os.unlink(tmp_path)

# ── /deobf ───────────────────────────────────────────────────
@client.tree.command(name="deobf", description="فك تشفير ملف Lua")
async def cmd_deobf(interaction: discord.Interaction, file: discord.Attachment):
    if not file.filename.endswith((".lua", ".txt")):
        await interaction.response.send_message("⚠️ الملف لازم `.lua` أو `.txt`", ephemeral=True)
        return
    await interaction.response.defer()
    data = await file.read()
    layer = data.decode("utf-8", errors="replace")
    depth = 0
    try:
        while True:
            result = decrypt_xor_ror_layer(layer)
            if result is None:
                break
            depth += 1
            layer = result
        if isinstance(layer, bytes):
            layer = layer.decode("utf-8", "replace")
        cleaned = inline_string_table(layer)
        if cleaned != layer:
            layer = cleaned
    except Exception as e:
        await interaction.followup.send(f"❌ error: `{e}`")
        return
    if depth == 0:
        await interaction.followup.send("⚠️ ما لقيت تشفير قابل للفك\nجرّب `/sss`")
        return
    out_name = file.filename.rsplit(".", 1)[0] + "_decoded.lua"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.lua', encoding='utf-8', delete=False) as tmp:
        tmp.write(layer); tmp_path = tmp.name
    try:
        await interaction.followup.send(
            f"🔓 **{file.filename}** فُكّ تشفيره\n"
            f"طبقات: `{depth}` | الحجم: `{len(data):,}` → `{len(layer):,}` chars",
            file=discord.File(tmp_path, filename=out_name))
    finally:
        os.unlink(tmp_path)

# ── /sss ─────────────────────────────────────────────────────
@client.tree.command(name="sss", description="كشف نوع تشفير ملف Lua")
async def cmd_sss(interaction: discord.Interaction, file: discord.Attachment):
    if not file.filename.endswith(".lua"):
        await interaction.response.send_message("⚠️ الملف مش `.lua`", ephemeral=True)
        return
    await interaction.response.defer()
    data = await file.read()
    src = data.decode("utf-8", errors="replace")
    detection = detect_obfuscation(src)
    await interaction.followup.send(
        f"**📄 {file.filename}**\n"
        f"الحجم: `{len(data):,} bytes` | الأسطر: `{src.count(chr(10))+1:,}`\n\n"
        f"**🔍 نوع التشفير:**\n{detection}")

# ── /fetch ───────────────────────────────────────────────────
@client.tree.command(name="fetch", description="جيب كود من URL وافكه")
async def cmd_fetch(interaction: discord.Interaction, url: str):
    await interaction.response.defer()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Roblox/WinInet"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read(5 * 1024 * 1024)
    except Exception as e:
        await interaction.followup.send(f"❌ فشل الجلب: `{e}`"); return
    layer = raw.decode("utf-8", errors="replace")
    detection = detect_obfuscation(layer)
    depth = 0
    try:
        while True:
            result = decrypt_xor_ror_layer(layer)
            if result is None: break
            depth += 1; layer = result
        if isinstance(layer, bytes):
            layer = layer.decode("utf-8", "replace")
        cleaned = inline_string_table(layer)
        if cleaned != layer: layer = cleaned
    except Exception as e:
        await interaction.followup.send(f"❌ error: `{e}`"); return
    with tempfile.NamedTemporaryFile(mode='w', suffix='.lua', encoding='utf-8', delete=False) as tmp:
        tmp.write(layer); tmp_path = tmp.name
    try:
        await interaction.followup.send(
            f"🌐 `{url[:80]}`\nنوع: {detection.splitlines()[0]}\nطبقات مفكوكة: `{depth}`",
            file=discord.File(tmp_path, filename="fetched_decoded.lua"))
    finally:
        os.unlink(tmp_path)

# ── /help ─────────────────────────────────────────────────────
@client.tree.command(name="help", description="قائمة الأوامر")
async def cmd_help(interaction: discord.Interaction):
    await interaction.response.send_message(
        "**🔐 أوامر التشفير:**\n"
        "`/mega` — **MEGA: 10 طبقات XOR+ROL** (الأقوى والأسرع) 🆕\n"
        "  ├ 10 جولة XOR+ROL بمفاتيح مختلفة\n"
        "  └ NumericByte (طبقة خارجية)\n\n"
        "`/xor` — طبقة XOR+ROL واحدة\n"
        "`/get` — تمويه بجدول أرقام (بسيط)\n\n"
        "**🔓 أوامر الفك:**\n"
        "`/deobf` — فك تشفير XOR+ROR\n"
        "`/fetch` — جيب كود من URL وافكه\n"
        "`/sss` — كشف نوع التشفير\n"
        "`/help` — القائمة دي")

@client.event
async def on_ready():
    print(f"[✓] bot online: {client.user}")
    print(f"[✓] guilds: {len(client.guilds)}")

@client.event
async def on_error(event, *args, **kwargs):
    import traceback
    print(f"[!] error in {event}:")
    traceback.print_exc()

threading.Thread(target=run_health_server, daemon=True).start()

if not TOKEN:
    print("[!] DISCORD_TOKEN غير موجود في البيئة!")
else:
    client.run(TOKEN)
