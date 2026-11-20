"""
botur.py — Discord obfuscation bot v4.0 (merged + Luraph VM)
requires: pip install discord.py
single file — no external dependencies
"""

import discord
from discord import app_commands
import os, re, tempfile, sys, threading, random, struct, math, urllib.request, urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler

TOKEN = os.getenv("DISCORD_TOKEN")


# ══════════════════════════════════════════════════════════════
#  lua_deobf — فك التشفير
# ══════════════════════════════════════════════════════════════

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
                j = i + 1; num = ''
                while j < len(s) and s[j].isdigit():
                    num += s[j]; j += 1
                out.append(int(num)); i = j
            else:
                out.append(ord(s[i])); i += 1
        return bytes(out)
    chunks = [_decode(c) for c in chunk_strs]
    result = [None] * len(order)
    for idx, pos in enumerate(order):
        result[pos - 1] = chunks[idx]
    return b''.join(x for x in result if x is not None)

def _xor8(a, b):
    r, p = 0, 1
    for _ in range(8):
        u, v = a % 2, b % 2
        if u != v: r += p
        a = (a - u) // 2; b = (b - v) // 2; p *= 2
    return r

def _ror8(b, n):
    n = n % 8
    if n == 0: return b
    return ((b >> n) | (b << (8 - n))) & 0xFF

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
    key1    = _extract_assembled(k1n,         src)
    key2    = _extract_assembled(k2n,         src)
    key3    = _extract_assembled(k3n,         src)
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
        b   = _ror8(b, rotation[i % 7])
        b   = _xor8(b, _xor8(key1[ia], mka))
        out.append(b)
    return bytes(out)

# ══════════════════════════════════════════════════════════════
#  luraph_vm_deobf — فك Luraph VM الحقيقي (getfenv pattern)
# ══════════════════════════════════════════════════════════════

def _luraph_custom_b64_decode(s, alphabet):
    idx = {ord(c): i for i, c in enumerate(alphabet)}
    bits = nbits = 0
    result = []
    for c in s:
        v = idx.get(ord(c))
        if v is None:
            continue
        bits = bits * 64 + v
        nbits += 6
        if nbits >= 8:
            nbits -= 8
            result.append((bits >> nbits) & 0xFF)
            bits &= (1 << nbits) - 1
    return bytes(result)

def _luraph_find_alphabet(src):
    # الـ alphabet دايماً assigned لـ variable قبل IjjlOoOIl function
    m = re.search(r'local \w+=\n?"([A-Za-z0-9+/=]{60,70})"', src)
    if m:
        return m.group(1)
    # fallback: أطول string مكونة من base64 chars
    candidates = re.findall(r'"([A-Za-z0-9+/]{62,66})"', src)
    for c in candidates:
        if len(set(c)) >= 60:
            return c
    return None

def _luraph_compute_seed(src):
    # iOI010iLli = string.byte("w") + (string.char(81,69)=="QE" and 2691 or 87) + select("#",0,0)*16 + tonumber("2994")*7
    # لكن الـ seed ممكن يتغير — نجرب نستخرجه من الكود
    # Pattern: IOOI0llO("w")+(LLll1jil1lo(81,69)=="QE" and 2691 or 87)+...select("#",0,0)*\d+...*(\d+)
    m = re.search(
        r'IOOI0llO\("(\w)"\)\+'           # string.byte(char)
        r'\([^)]+\((\d+),(\d+)\)[^)]+and\s*(\d+)\s*or\s*(\d+)\)'  # char check
        r'\+\w+\("#",0,0\)\*(\d+)'         # select * N
        r'\+\w+\("(\d+)"\)\*(\d+)',         # tonumber * M
        src
    )
    if m:
        char_byte  = ord(m.group(1))
        c1, c2     = int(m.group(2)), int(m.group(3))
        and_val    = int(m.group(4))
        or_val     = int(m.group(5))
        select_mul = int(m.group(6))
        num_str    = int(m.group(7))
        num_mul    = int(m.group(8))
        char_check = chr(c1) + chr(c2)
        cond_val   = and_val if (chr(c1) + chr(c2)) == chr(c1) + chr(c2) else or_val
        # select("#",0,0) = 2
        seed = char_byte + and_val + 2 * select_mul + num_str * num_mul
        return seed
    return None

def _luraph_make_prng(seed, enc_data):
    """Generator يرجع bytes مفكوكة واحدة واحدة"""
    state  = (3633890356 + seed) % (2**32)
    jLO    = 95
    for pos, enc in enumerate(enc_data):
        state   = (state * 61653 + 3015945891) % (2**32)
        iLIOjlj = (int(state / 65536) + jLO + pos * 38) % 256
        result  = (enc - iLIOjlj) % 256
        jLO     = (jLO * 31 + enc + 1) % 251
        yield result

def _luraph_decrypt_const(enc_key, enc_val_str, LIii1Oo):
    state = (LIii1Oo + enc_key * 251 + 1) % 65536
    result = []
    for idx_1b, c in enumerate(enc_val_str, 1):
        state = (state * 40503 + 12345) % 65536
        dec   = (ord(c) - int(state / 256) % 256 - idx_1b * (LIii1Oo % 256)) % 256
        result.append(chr(dec))
    s = ''.join(result)
    if len(s) < 5:
        return None
    type_b = ord(s[0])
    length = ord(s[1]) + ord(s[2])*256 + ord(s[3])*65536 + ord(s[4])*16777216
    if length != len(s) - 5:
        return None
    raw = s[5:]
    if type_b == 0:
        try:
            return int(raw) if ('.' not in raw and 'e' not in raw.lower()) else float(raw)
        except Exception:
            return raw
    elif type_b == 1:
        return raw
    elif type_b == 2:
        return math.inf
    elif type_b == 3:
        return -math.inf
    return None

def decrypt_luraph_vm(src):
    """
    يفك Luraph VM الحقيقي (getfenv pattern).
    يرجع (strings_list, payload_bytes) أو None لو مش Luraph VM.
    """
    if not re.search(r'local\s+\w+\s*=\s*\(getfenv', src):
        return None

    alphabet = _luraph_find_alphabet(src)
    if not alphabet:
        return None

    seed = _luraph_compute_seed(src)
    if seed is None:
        return None

    # استخرج الـ payload (base64 string الكبيرة)
    m = re.search(r'[A-Za-z_]\w*\s*=\s*"([A-Za-z0-9+/=]{5000,})"', src)
    if not m:
        return None
    enc_data = _luraph_custom_b64_decode(m.group(1), alphabet)
    if len(enc_data) < 1000:
        return None

    # شغّل الـ PRNG
    dec_iter  = _luraph_make_prng(seed, enc_data)
    dec_bytes = list(dec_iter)

    pos = [0]

    def r8():
        v = dec_bytes[pos[0]]; pos[0] += 1; return v
    def r16():
        a, b = r8(), r8(); return a + b * 256
    def r32():
        a, b, c, d = r8(), r8(), r8(), r8()
        return a + b*256 + c*65536 + d*16777216
    def rstr():
        n = r32()
        if n > len(dec_bytes):
            raise ValueError(f"string too long {n}")
        return bytes(r8() for _ in range(n)).decode('latin-1')

    iOI010iLli = seed

    def parse_func(depth=0):
        if depth > 200:
            raise ValueError("nesting too deep")
        _params = r8()
        flags   = r8()
        if flags > 1:
            raise ValueError(f"bad flags {flags}")
        func_id      = r32()
        ljiloIjloio  = func_id % 65536
        n_consts     = r16()
        consts_raw   = [(r16(), rstr()) for _ in range(n_consts)]
        n_instrs     = r32()
        instrs       = []
        for _ in range(n_instrs):
            a, b, c, d = r32(), r16(), r32(), r16()
            instrs.append((a, b, c, d))
            for ki, vi in enumerate([a, b, c, d]):
                ljiloIjloio = (ljiloIjloio * 131 + vi % 65536 + ki + 1) % 65536
        n_children = r16()
        children   = [parse_func(depth + 1) for _ in range(n_children)]
        n_upvals   = r16()
        for _ in range(n_upvals):
            r8(); r16()
        LIii1Oo = (iOI010iLli + 40647 + ljiloIjloio) % 65536
        consts  = [_luraph_decrypt_const(k, v, LIii1Oo) for k, v in consts_raw]
        return {'consts': consts, 'children': children}

    try:
        # اقرأ opcode remap table أولاً
        n_remap = r16()
        for _ in range(n_remap):
            r16(); r16()
        root = parse_func(0)
    except Exception:
        return None

    # اجمع كل الـ strings
    all_strings = []

    def collect(node):
        for c in node['consts']:
            if isinstance(c, str) and c:
                all_strings.append(c)
        for child in node['children']:
            collect(child)

    collect(root)
    return all_strings, bytes(dec_bytes)


def luraph_vm_strings_report(src):
    """
    يرجع تقرير نصي بالـ strings المستخرجة من Luraph VM.
    يرجع None لو مش Luraph VM.
    """
    result = decrypt_luraph_vm(src)
    if result is None:
        return None
    strings, _ = result

    seen   = []
    seen_s = set()
    for s in strings:
        if s not in seen_s and len(s) < 300:
            seen_s.add(s)
            seen.append(s)

    webhooks = [s for s in seen if 'webhook' in s.lower() or 'discord.gg' in s.lower()]
    urls     = [s for s in seen if s.startswith('http')]
    keywords = [s for s in seen if any(k in s.lower() for k in
                ('hwid','executor','getfenv','loadstring','require','pcall',
                 'tostring','game','player','workspace','getgenv'))]

    lines = [f"🔴 **Luraph VM** — استُخرج `{len(seen)}` string مشفرة\n"]

    if webhooks:
        lines.append("**🎯 Webhooks / Discord:**")
        for w in webhooks[:10]:
            lines.append(f"• `{w}`")
        lines.append("")

    if urls:
        lines.append("**🌐 URLs:**")
        for u in urls[:15]:
            lines.append(f"• `{u}`")
        lines.append("")

    if keywords:
        lines.append("**🔑 Keywords مهمة:**")
        for k in keywords[:20]:
            lines.append(f"• `{k}`")
        lines.append("")

    lines.append(f"**📋 كل الـ strings ({len(seen)}):**")
    chunk = []
    for s in seen[:200]:
        chunk.append(repr(s))
    lines.append("```\n" + "\n".join(chunk[:80]) + "\n```")

    return "\n".join(lines)


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
                j = i + 1; num = ''
                while j < len(s) and s[j].isdigit():
                    num += s[j]; j += 1
                raw.append(int(num)); i = j
            else:
                raw.append(ord(s[i])); i += 1
        kl = len(key)
        db = bytes((b - key[idx % kl] + 256) % 256 for idx, b in enumerate(raw))
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
        return table[idx - 1] if 1 <= idx <= len(table) else m.group(0)
    return re.sub(r'_0xd215db\((\d+)\)', repl, code_part)


# ══════════════════════════════════════════════════════════════
#  luraph_style_mobile — التشفير
# ══════════════════════════════════════════════════════════════

ROTATION_TABLE = (3, 1, 5, 2, 6, 4, 7)

def _xor8_obf(a, b): return a ^ b
def _ror8_obf(b, n):
    n &= 7
    if n == 0: return b
    return ((b >> n) | (b << (8 - n))) & 0xFF
def _rol8_obf(b, n): return _ror8_obf(b, 8 - (n & 7))

def _encode_bytes_lua(data):
    return '"' + ''.join(f'\\{b}' for b in data) + '"'

def _build_assembled_var(varname, data, rng):
    n = max(2, min(8, len(data) // 64 + 2))
    chunk_size = max(1, len(data) // n)
    chunks = []
    i = 0
    while i < len(data):
        end = i + chunk_size if len(chunks) < n - 1 else len(data)
        chunks.append(data[i:end]); i = end
    order = list(range(len(chunks)))
    rng.shuffle(order)
    perm_chunks = [None] * len(chunks)
    inv_order   = [0] * len(chunks)
    for shuffled_idx, orig_idx in enumerate(order):
        perm_chunks[shuffled_idx] = chunks[orig_idx]
        inv_order[orig_idx] = shuffled_idx + 1
    p_entries = ','.join(_encode_bytes_lua(c) for c in perm_chunks)
    o_entries = ','.join(str(x) for x in inv_order)
    return (
        f'local {varname}=(function()'
        f'local _p={{{p_entries}}}'
        f'local _o={{{o_entries}}}'
        f'local _r={{}}for _i=1,#{{{o_entries}}} do _r[_o[_i]]=_p[_i] end '
        f'local _s=""for _=1,#_r do _s=_s.._r[_] end return _s end)()'
    )

class NumericByteObf:
    """Wrap Lua source as a decimal byte table; this is obfuscation, not encryption."""
    def obfuscate(self, src):
        raw = src.encode("utf-8")
        values = [str(b) for b in raw]
        rows = [
            "    " + ", ".join(values[i:i + 24])
            for i in range(0, len(values), 24)
        ]
        table_body = ",\n".join(rows)
        return (
            "-- PRIME numeric-byte obfuscation (not secure encryption)\n"
            "local _bytes = {\n" + table_body + "\n}\n"
            "local _chars = {}\n"
            "for _i = 1, #_bytes do\n"
            "    _chars[_i] = string.char(_bytes[_i])\n"
            "end\n"
            "local _source = table.concat(_chars)\n"
            "local _compile = loadstring or load\n"
            "assert(_compile, 'This environment does not support loadstring/load')\n"
            "local _fn, _err = _compile(_source)\n"
            "assert(_fn, _err)\n"
            "_fn()\n"
        )


class LuraphStyleObf:
    def __init__(self, seed=None):
        self.seed = seed if seed is not None else random.getrandbits(64)
        self._rng = random.Random(self.seed)
    def _make_varname(self):
        return '_' + ''.join(self._rng.choice('IlO0ij1oL') for _ in range(self._rng.randint(6, 10)))
    def obfuscate(self, src):
        return self._encrypt_layer(src.encode('utf-8'))
    def _encrypt_layer(self, payload):
        rng = self._rng
        key1 = bytes(rng.randint(0,255) for _ in range(rng.randint(32,64)))
        key2 = bytes(rng.randint(0,255) for _ in range(rng.randint(32,64)))
        key3 = bytes(rng.randint(0,255) for _ in range(rng.randint(16,32)))
        rotation = list(ROTATION_TABLE)
        L1, L2, L3 = len(key1), len(key2), len(key3)
        enc = bytearray()
        for i, b in enumerate(payload):
            ia = i % L1; ib = i % L2
            mka = key3[ia % L3]; mkb = key3[ib % L3]
            b = _xor8_obf(b, _xor8_obf(key1[ia], mka))
            b = _rol8_obf(b, rotation[i % 7])
            b = _xor8_obf(b, _xor8_obf(key2[ib], mkb))
            enc.append(b)
        k1n=self._make_varname(); k2n=self._make_varname()
        k3n=self._make_varname(); pn=self._make_varname()
        vn=self._make_varname();  an=self._make_varname()
        bn=self._make_varname();  cn=self._make_varname()
        rot_str = ','.join(f'({r})' for r in rotation)
        lines = [
            _build_assembled_var(k1n, key1, rng),
            _build_assembled_var(k2n, key2, rng),
            _build_assembled_var(k3n, key3, rng),
            _build_assembled_var(pn, bytes(enc), rng),
            f'local {an},{bn},{cn}=#{k1n},#{k2n},#{k3n}',
            f'local _rot={{{rot_str}}}',
            (f'local _out={{}} '
             f'for _i=1,#{pn} do '
             f'local _b=string.byte({pn},_i) '
             f'local _ia=((_i-1)%{an})+1 '
             f'local _ib=((_i-1)%{bn})+1 '
             f'local _mka=string.byte({k3n},((_ia-1)%{cn})+1) '
             f'local _mkb=string.byte({k3n},((_ib-1)%{cn})+1) '
             f'local _r=_rot[((_i-1)%7)+1] '
             f'_b=(_b~(string.byte({k2n},_ib)~_mkb)) '
             f'_b=((_b>>_r)|(_b<<(8-_r)))&0xFF '
             f'_b=(_b~(string.byte({k1n},_ia)~_mka)) '
             f'_out[_i]=string.char(_b) '
             f'end '
             f'local {vn}=table.concat(_out) '
             f'load({vn})()')
        ]
        return '\n'.join(lines)


# ══════════════════════════════════════════════════════════════
#  bot
# ══════════════════════════════════════════════════════════════

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"ok")
    def log_message(self, *args): pass

def run_health_server():
    port = int(os.getenv("PORT", 10000))
    HTTPServer(("0.0.0.0", port), HealthHandler).serve_forever()

def detect_obfuscation(src):
    results = []
    if re.search(r'local\s+\w+\s*=\s*\(getfenv', src):
        results.append("🔴 Luraph VM (getfenv pattern) — `/luraph` يفكه")
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

class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default() | discord.Intents(message_content=True))
        self.tree = app_commands.CommandTree(self)
    async def setup_hook(self):
        await self.tree.sync()

client = MyClient()

@client.tree.command(name="get", description="تمويه ملف Lua بجدول أرقام")
async def cmd_get(interaction: discord.Interaction, file: discord.Attachment):
    if not file.filename.lower().endswith(".lua"):
        await interaction.response.send_message("⚠️ الملف لازم يكون `.lua`", ephemeral=True)
        return

    await interaction.response.defer()
    data = await file.read()

    try:
        src = data.decode("utf-8")
    except UnicodeDecodeError:
        await interaction.followup.send("❌ الملف ليس نص Lua بترميز UTF-8.")
        return

    try:
        obf_src = NumericByteObf().obfuscate(src)
    except Exception as e:
        await interaction.followup.send(f"❌ فشل التمويه: `{e}`")
        return

    out_name = file.filename.rsplit(".", 1)[0] + "_numeric_obf.lua"
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".lua", encoding="utf-8", delete=False
        ) as tmp:
            tmp.write(obf_src)
            tmp_path = tmp.name

        await interaction.followup.send(
            f"✅ **{out_name}** جاهز\n"
            f"تم تحويل محتوى الملف كاملًا إلى جدول أرقام.\n"
            f"الحجم: `{len(src):,}` → `{len(obf_src):,}` chars\n"
            f"ملاحظة: هذا تمويه وليس تشفيرًا مستحيل الفك.",
            file=discord.File(tmp_path, filename=out_name),
        )
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


@client.tree.command(name="deobf", description="فك تشفير ملف Lua (multi-layer)")
async def cmd_deobf(interaction: discord.Interaction, file: discord.Attachment):
    if not file.filename.endswith((".lua", ".txt")):
        await interaction.response.send_message("⚠️ الملف لازم `.lua` أو `.txt`", ephemeral=True); return
    await interaction.response.defer()
    data = await file.read()
    try: layer = data.decode("utf-8", errors="replace")
    except Exception:
        await interaction.followup.send("❌ مش قادر يقرأ الملف"); return
    try:
        depth = 0
        while True:
            result = decrypt_xor_ror_layer(layer)
            if result is None: break
            depth += 1; layer = result
        if isinstance(layer, bytes): layer = layer.decode("utf-8", "replace")
        cleaned = inline_string_table(layer)
        if cleaned != layer: layer = cleaned
    except Exception as e:
        await interaction.followup.send(f"❌ error: `{e}`"); return
    if depth == 0 and layer == data.decode("utf-8", "replace"):
        await interaction.followup.send("⚠️ ما لقيت تشفير XOR+ROR في الملف\nجرّب `/sss` تعرف نوع التشفير أول"); return
    out_name = file.filename.rsplit(".", 1)[0] + "_decoded.lua"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.lua', encoding='utf-8', delete=False) as tmp:
        tmp.write(layer); tmp_path = tmp.name
    try:
        await interaction.followup.send(
            f"🔓 **{file.filename}** — فُكّ تشفيره\n"
            f"طبقات: `{depth}` | الحجم: `{len(data):,}` → `{len(layer):,}` chars",
            file=discord.File(tmp_path, filename=out_name))
    finally: os.unlink(tmp_path)

@client.tree.command(name="sss", description="كشف نوع تشفير ملف Lua")
async def cmd_sss(interaction: discord.Interaction, file: discord.Attachment):
    if not file.filename.endswith(".lua"):
        await interaction.response.send_message("⚠️ الملف مش `.lua`", ephemeral=True); return
    await interaction.response.defer()
    data = await file.read()
    try: src = data.decode("utf-8")
    except UnicodeDecodeError: src = data.decode("latin-1")
    detection = detect_obfuscation(src)
    await interaction.followup.send(
        f"**📄 {file.filename}**\n"
        f"الحجم: `{len(data):,} bytes` | الأسطر: `{src.count(chr(10))+1:,}`\n\n"
        f"**🔍 نوع التشفير:**\n{detection}")

@client.tree.command(name="luraph", description="فك Luraph VM الحقيقي (getfenv) — يستخرج كل الـ strings")
async def cmd_luraph(interaction: discord.Interaction, file: discord.Attachment):
    if not file.filename.endswith((".lua", ".txt")):
        await interaction.response.send_message("⚠️ الملف لازم `.lua` أو `.txt`", ephemeral=True)
        return
    await interaction.response.defer()
    data = await file.read()
    try:
        src = data.decode("utf-8", errors="replace")
    except Exception:
        await interaction.followup.send("❌ مش قادر يقرأ الملف")
        return

    # تحقق إنه Luraph VM فعلاً
    if not re.search(r'local\s+\w+\s*=\s*\(getfenv', src):
        await interaction.followup.send(
            "⚠️ الملف مش Luraph VM (ما فيه `getfenv` pattern)\n"
            "جرّب `/sss` تعرف نوع التشفير")
        return

    try:
        report = luraph_vm_strings_report(src)
    except Exception as e:
        await interaction.followup.send(f"❌ error: `{e}`")
        return

    if report is None:
        await interaction.followup.send(
            "❌ ما قدر يفك الـ VM — ممكن seed أو alphabet مختلف\n"
            "أرسل الملف في الـ support")
        return

    # لو التقرير كبير — قسّمه
    if len(report) <= 1900:
        await interaction.followup.send(report)
    else:
        # أرسل كملف نصي
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', encoding='utf-8', delete=False) as tmp:
            tmp.write(report); tmp_path = tmp.name
        try:
            await interaction.followup.send(
                f"🔴 **Luraph VM** — الحجم: `{len(data):,}` bytes\n"
                f"التقرير كبير — شوفه في الملف 👇",
                file=discord.File(tmp_path, filename="luraph_report.txt"))
        finally:
            os.unlink(tmp_path)


@client.tree.command(name="help", description="قائمة الأوامر")
async def cmd_help(interaction: discord.Interaction):
    await interaction.response.send_message(
        "**الأوامر:**\n"
        "`/get` — تمويه ملف `.lua` بجدول أرقام\n"
        "`/deobf` — فك تشفير XOR+ROR (multi-layer)\n"
        "`/luraph` — فك **Luraph VM** الحقيقي (getfenv) 🆕\n"
        "`/fetch` — جيب كود من URL وافكه\n"
        "`/sss` — كشف نوع التشفير\n"
        "`/help` — القائمة دي")

@client.tree.command(name="fetch", description="جيب كود من URL وافكه")
async def cmd_fetch(interaction: discord.Interaction, url: str):
    await interaction.response.defer()
    # جلب الكود
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Roblox/WinInet",
                "Accept":     "*/*",
            }
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read(5 * 1024 * 1024)  # 5MB max
    except urllib.error.HTTPError as e:
        await interaction.followup.send(f"❌ HTTP {e.code}: `{url}`"); return
    except Exception as e:
        await interaction.followup.send(f"❌ فشل الجلب: `{e}`"); return

    try:
        layer = raw.decode("utf-8", errors="replace")
    except Exception:
        await interaction.followup.send("❌ مش قادر يقرأ الرد"); return

    original = layer

    # اكتشاف نوع التشفير
    detection = detect_obfuscation(original)
    is_luraph_vm = re.search(r'local\s+\w+\s*=\s*\(getfenv', original)

    # pipeline فك التشفير
    out_name = "fetched_decoded.lua"

    if is_luraph_vm:
        # Luraph VM — نستخرج الـ strings كتقرير
        try:
            report = luraph_vm_strings_report(original)
        except Exception as e:
            await interaction.followup.send(f"❌ error في فك Luraph VM: `{e}`"); return

        if report is None:
            await interaction.followup.send(
                f"🌐 **URL:** `{url[:80]}`\n"
                f"📦 الحجم: `{len(raw):,}` bytes\n"
                f"🔍 نوع: {detection.splitlines()[0]}\n"
                f"❌ ما قدر يفك الـ VM — seed أو alphabet غير معروف")
            return

        # أرسل الملف الأصلي + التقرير
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', encoding='utf-8', delete=False) as tmp:
            tmp.write(report); tmp_path = tmp.name
        try:
            await interaction.followup.send(
                f"🌐 **URL:** `{url[:80]}`\n"
                f"📦 الحجم: `{len(raw):,}` bytes\n"
                f"🔍 نوع: {detection.splitlines()[0]}\n"
                f"🔓 طبقات مفكوكة: `1` (Luraph VM)",
                file=discord.File(tmp_path, filename="luraph_report.txt"))
        finally:
            os.unlink(tmp_path)

        # أرسل الملف الأصلي (decoded layer 0) كمان
        with tempfile.NamedTemporaryFile(mode='w', suffix='.lua', encoding='utf-8', delete=False) as tmp:
            tmp.write(original); tmp_path2 = tmp.name
        try:
            await interaction.followup.send(
                "📄 الملف الأصلي (قبل فك VM):",
                file=discord.File(tmp_path2, filename=out_name))
        finally:
            os.unlink(tmp_path2)

    else:
        # XOR+ROR pipeline العادي
        try:
            depth = 0
            while True:
                result = decrypt_xor_ror_layer(layer)
                if result is None: break
                depth += 1; layer = result
            if isinstance(layer, bytes):
                layer = layer.decode("utf-8", "replace")
            cleaned = inline_string_table(layer)
            if cleaned != layer: layer = cleaned
        except Exception as e:
            await interaction.followup.send(f"❌ error في الفك: `{e}`"); return

        with tempfile.NamedTemporaryFile(mode='w', suffix='.lua', encoding='utf-8', delete=False) as tmp:
            tmp.write(layer); tmp_path = tmp.name
        try:
            await interaction.followup.send(
                f"🌐 **URL:** `{url[:80]}`\n"
                f"📦 الحجم: `{len(raw):,}` bytes\n"
                f"🔍 نوع: {detection.splitlines()[0]}\n"
                f"🔓 طبقات مفكوكة: `{depth}`",
                file=discord.File(tmp_path, filename=out_name))
        finally:
            os.unlink(tmp_path)


@client.event
async def on_ready():
    print(f"[✓] bot online: {client.user}")

threading.Thread(target=run_health_server, daemon=True).start()
client.run(TOKEN)
