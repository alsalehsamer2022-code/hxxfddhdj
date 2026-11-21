"""
botur.py — Discord obfuscation bot v5.0 (MEGA obf)
requires: pip install discord.py
"""

import discord
from discord import app_commands
import os, re, tempfile, sys, threading, random, struct, math, urllib.request, urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler

TOKEN = os.getenv("DISCORD_TOKEN")

# ══════════════════════════════════════════════════════════════
#  helpers مشتركة
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

def _rname(rng, length=None):
    """اسم متغير عشوائي من حروف مشابهة"""
    pool = 'IlO0ij1oLJjl'
    n = length or rng.randint(8, 14)
    return '_' + ''.join(rng.choice(pool) for _ in range(n))

# ══════════════════════════════════════════════════════════════
#  LAYER 1 — NumericByteObf (جدول أرقام عادي)
# ══════════════════════════════════════════════════════════════

class NumericByteObf:
    def obfuscate(self, src):
        raw = src.encode("utf-8")
        values = [str(b) for b in raw]
        rows = ["    " + ", ".join(values[i:i+24]) for i in range(0, len(values), 24)]
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

# ══════════════════════════════════════════════════════════════
#  LAYER 2 — LuraphStyleObf (XOR + ROL/ROR + 3 مفاتيح)
# ══════════════════════════════════════════════════════════════

class LuraphStyleObf:
    def __init__(self, seed=None):
        self.seed = seed if seed is not None else random.getrandbits(64)
        self._rng = random.Random(self.seed)

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
        k1n=_rname(rng); k2n=_rname(rng)
        k3n=_rname(rng); pn=_rname(rng)
        vn=_rname(rng);  an=_rname(rng)
        bn=_rname(rng);  cn=_rname(rng)
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
#  LAYER 3 — DoubleXorObf (XOR مزدوج بمفتاحين مختلفين)
# ══════════════════════════════════════════════════════════════

class DoubleXorObf:
    """
    طبقتان XOR متتاليتان بمفاتيح مختلفة.
    المفتاح الأول يتولّد من seed، الثاني من seed^0xDEAD.
    """
    def __init__(self, seed=None):
        self.seed = seed if seed is not None else random.getrandbits(32)
        self._rng = random.Random(self.seed)

    def obfuscate(self, src):
        rng = self._rng
        raw = src.encode('utf-8')

        # مفتاح A
        kA_len = rng.randint(48, 96)
        kA = bytes(rng.randint(1, 255) for _ in range(kA_len))
        # مفتاح B (من seed مختلف)
        rng2 = random.Random(self.seed ^ 0xDEADBEEF)
        kB_len = rng2.randint(48, 96)
        kB = bytes(rng2.randint(1, 255) for _ in range(kB_len))

        # تشفير طبقة A ثم B
        enc = bytearray()
        for i, b in enumerate(raw):
            b = b ^ kA[i % kA_len]
            b = b ^ kB[i % kB_len]
            enc.append(b)

        # اسماء متغيرات
        vA  = _rname(rng); vB  = _rname(rng)
        vP  = _rname(rng); vO  = _rname(rng)
        vLA = _rname(rng); vLB = _rname(rng)
        vi  = _rname(rng); vb  = _rname(rng)
        vs  = _rname(rng)

        kA_lua = '{' + ','.join(str(x) for x in kA) + '}'
        kB_lua = '{' + ','.join(str(x) for x in kB) + '}'
        p_lua  = '{' + ','.join(str(x) for x in enc) + '}'

        lua = (
            f"local {vA}={kA_lua}\n"
            f"local {vB}={kB_lua}\n"
            f"local {vP}={p_lua}\n"
            f"local {vLA},{vLB}=#{vA},#{vB}\n"
            f"local {vO}={{}}\n"
            f"for {vi}=1,#{vP} do\n"
            f"  local {vb}={vP}[{vi}]\n"
            f"  {vb}={vb}~{vB}[(({vi}-1)%{vLB})+1]\n"
            f"  {vb}={vb}~{vA}[(({vi}-1)%{vLA})+1]\n"
            f"  {vO}[{vi}]=string.char({vb})\n"
            f"end\n"
            f"local {vs}=table.concat({vO})\n"
            f"load({vs})()\n"
        )
        return lua

# ══════════════════════════════════════════════════════════════
#  LAYER 4 — JunkSplitObf
#  يقسم البايتات لأجزاء صغيرة + يضيف آلاف الأسطر وهمية
# ══════════════════════════════════════════════════════════════

class JunkSplitObf:
    """
    يقسم جدول البايتات لـ N chunk ويضيف بين كل chunk
    متغيرات وهمية وعمليات حسابية لا معنى لها.
    """
    def __init__(self, seed=None, junk_density=3):
        self.seed = seed if seed is not None else random.getrandbits(32)
        self.junk_density = junk_density  # عدد أسطر junk بين كل chunk

    def _make_junk_line(self, rng):
        """سطر Lua وهمي لا يؤثر على التنفيذ"""
        a = rng.randint(1, 999)
        b = rng.randint(1, 999)
        ops = ['+', '-', '*']
        op = rng.choice(ops)
        vj = _rname(rng)
        return f"local {vj}={a}{op}{b} -- junk"

    def obfuscate(self, src):
        rng = random.Random(self.seed)
        raw = src.encode('utf-8')

        # XOR بسيط أولاً
        k_len = rng.randint(32, 64)
        key   = bytes(rng.randint(1, 255) for _ in range(k_len))
        enc   = bytes(b ^ key[i % k_len] for i, b in enumerate(raw))

        # تقسيم لـ chunks
        chunk_size = max(64, len(enc) // 20)
        chunks = [enc[i:i+chunk_size] for i in range(0, len(enc), chunk_size)]

        vK   = _rname(rng)
        vOut = _rname(rng)
        vi   = _rname(rng)
        vb   = _rname(rng)
        vs   = _rname(rng)
        vLen = _rname(rng)

        lines = []
        # المفتاح
        k_lua = '{' + ','.join(str(x) for x in key) + '}'
        lines.append(f"local {vK}={k_lua}")
        lines.append(f"local {vLen}=#{vK}")
        lines.append(f"local {vOut}={{}}")

        offset = 0
        for idx, chunk in enumerate(chunks):
            # junk قبل كل chunk
            for _ in range(self.junk_density):
                lines.append(self._make_junk_line(rng))

            # الـ chunk كجدول
            vC = _rname(rng)
            c_lua = '{' + ','.join(str(x) for x in chunk) + '}'
            lines.append(f"local {vC}={c_lua}")

            # فك XOR وإضافة للـ output
            vI2 = _rname(rng)
            vB2 = _rname(rng)
            lines.append(
                f"for {vI2}=1,#{vC} do "
                f"local {vB2}={vC}[{vI2}]~{vK}[(({offset}+{vI2}-1)%{vLen})+1] "
                f"{vOut}[{offset}+{vI2}]=string.char({vB2}) "
                f"end"
            )
            offset += len(chunk)

        # junk نهائي
        for _ in range(self.junk_density * 2):
            lines.append(self._make_junk_line(rng))

        lines.append(f"local {vs}=table.concat({vOut})")
        lines.append(f"load({vs})()")

        return '\n'.join(lines)

# ══════════════════════════════════════════════════════════════
#  LAYER 5 — StringSplitObf
#  يقطع الـ strings المرئية في الكود ويبنيها وقت التشغيل
#  (يُطبَّق على النص الأصلي قبل التشفير)
# ══════════════════════════════════════════════════════════════

class StringSplitObf:
    """
    يبحث عن الـ strings في كود Lua ويقطعها لأجزاء
    مثل: "hello" → ("hel" .. "lo")
    """
    def __init__(self, seed=None):
        self._rng = random.Random(seed or random.getrandbits(32))

    def obfuscate(self, src):
        rng = self._rng

        def split_string(m):
            s = m.group(0)
            inner = s[1:-1]  # بدون الاقتباسات
            if len(inner) < 4:
                return s
            # قسّم لجزأين أو ثلاثة
            parts = []
            i = 0
            while i < len(inner):
                size = rng.randint(2, max(3, len(inner) // 2))
                parts.append(inner[i:i+size])
                i += size
            return '(' + ' .. '.join(f'"{p}"' for p in parts if p) + ')'

        # نطبق على strings بين اقتباسات مزدوجة بسيطة
        result = re.sub(r'"[^"\\]{4,}"', split_string, src)
        return result

# ══════════════════════════════════════════════════════════════
#  MEGA — كل الطبقات مع بعض
# ══════════════════════════════════════════════════════════════

class MegaObf:
    """
    الترتيب:
    1. StringSplit  → يقطع الـ strings
    2. DoubleXor    → XOR مزدوج
    3. LuraphStyle  → XOR+ROL+3 مفاتيح
    4. JunkSplit    → تقطيع + junk
    5. NumericByte  → جدول أرقام نهائي
    """
    def __init__(self, seed=None):
        self.seed = seed if seed is not None else random.getrandbits(32)

    def obfuscate(self, src):
        rng = random.Random(self.seed)

        steps = []

        # 1. StringSplit (على الكود الأصلي)
        ss = StringSplitObf(seed=rng.getrandbits(32))
        src = ss.obfuscate(src)
        steps.append("StringSplit ✅")

        # 2. DoubleXor
        dx = DoubleXorObf(seed=rng.getrandbits(32))
        src = dx.obfuscate(src)
        steps.append("DoubleXor ✅")

        # 3. LuraphStyle
        lx = LuraphStyleObf(seed=rng.getrandbits(64))
        src = lx.obfuscate(src)
        steps.append("LuraphStyle XOR+ROL ✅")

        # 4. JunkSplit
        js = JunkSplitObf(seed=rng.getrandbits(32), junk_density=4)
        src = js.obfuscate(src)
        steps.append("JunkSplit ✅")

        # 5. NumericByte (الطبقة الخارجية)
        nb = NumericByteObf()
        src = nb.obfuscate(src)
        steps.append("NumericByte ✅")

        return src, steps

# ══════════════════════════════════════════════════════════════
#  فك التشفير (deobf)
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
        b   = _ror8(b, rotation[i % 7])
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
#  Luraph VM deobf
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
    m = re.search(r'local \w+=\n?"([A-Za-z0-9+/=]{60,70})"', src)
    if m:
        return m.group(1)
    candidates = re.findall(r'"([A-Za-z0-9+/]{62,66})"', src)
    for c in candidates:
        if len(set(c)) >= 60:
            return c
    return None

def _luraph_compute_seed(src):
    m = re.search(
        r'IOOI0llO\("(\w)"\)\+'
        r'\([^)]+\((\d+),(\d+)\)[^)]+and\s*(\d+)\s*or\s*(\d+)\)'
        r'\+\w+\("#",0,0\)\*(\d+)'
        r'\+\w+\("(\d+)"\)\*(\d+)',
        src
    )
    if m:
        char_byte  = ord(m.group(1))
        and_val    = int(m.group(4))
        select_mul = int(m.group(6))
        num_str    = int(m.group(7))
        num_mul    = int(m.group(8))
        seed = char_byte + and_val + 2 * select_mul + num_str * num_mul
        return seed
    return None

def _luraph_make_prng(seed, enc_data):
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
    if not re.search(r'local\s+\w+\s*=\s*\(getfenv', src):
        return None
    alphabet = _luraph_find_alphabet(src)
    if not alphabet:
        return None
    seed = _luraph_compute_seed(src)
    if seed is None:
        return None
    m = re.search(r'[A-Za-z_]\w*\s*=\s*"([A-Za-z0-9+/=]{5000,})"', src)
    if not m:
        return None
    enc_data = _luraph_custom_b64_decode(m.group(1), alphabet)
    if len(enc_data) < 1000:
        return None
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
        _params = r8(); flags = r8()
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
        n_remap = r16()
        for _ in range(n_remap):
            r16(); r16()
        root = parse_func(0)
    except Exception:
        return None
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
        super().__init__(intents=discord.Intents.default() | discord.Intents(message_content=True))
        self.tree = app_commands.CommandTree(self)
    async def setup_hook(self):
        await self.tree.sync()

client = MyClient()

# ── /get — جدول أرقام بسيط ──────────────────────────────────
@client.tree.command(name="get", description="تمويه ملف Lua بجدول أرقام (طبقة واحدة)")
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
        with tempfile.NamedTemporaryFile(mode="w", suffix=".lua", encoding="utf-8", delete=False) as tmp:
            tmp.write(obf_src)
            tmp_path = tmp.name
        await interaction.followup.send(
            f"✅ **{out_name}** جاهز\n"
            f"الحجم: `{len(src):,}` → `{len(obf_src):,}` chars\n"
            f"ملاحظة: هذا تمويه بسيط — جرّب `/mega` للتشفير القوي",
            file=discord.File(tmp_path, filename=out_name),
        )
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

# ── /mega — كل الطبقات مع بعض ───────────────────────────────
@client.tree.command(name="mega", description="🔐 تشفير MEGA — 5 طبقات متداخلة (شبه مستحيل الفك)")
async def cmd_mega(interaction: discord.Interaction, file: discord.Attachment):
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
        obf_src, steps = MegaObf().obfuscate(src)
    except Exception as e:
        await interaction.followup.send(f"❌ فشل التشفير: `{e}`")
        return
    out_name = file.filename.rsplit(".", 1)[0] + "_mega_obf.lua"
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".lua", encoding="utf-8", delete=False) as tmp:
            tmp.write(obf_src)
            tmp_path = tmp.name
        steps_text = "\n".join(f"  {i+1}. {s}" for i, s in enumerate(steps))
        await interaction.followup.send(
            f"🔐 **{out_name}** جاهز!\n"
            f"**الطبقات المطبّقة:**\n{steps_text}\n"
            f"الحجم: `{len(src):,}` → `{len(obf_src):,}` chars\n"
            f"⚠️ لا يوجد أداة عامة تفك هذا التشفير تلقائياً",
            file=discord.File(tmp_path, filename=out_name),
        )
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

# ── /xor — LuraphStyle فقط ──────────────────────────────────
@client.tree.command(name="xor", description="🔑 تشفير XOR+ROL (طبقة Luraph Style)")
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
    try:
        obf = LuraphStyleObf().obfuscate(src)
    except Exception as e:
        await interaction.followup.send(f"❌ خطأ: `{e}`")
        return
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
@client.tree.command(name="deobf", description="فك تشفير ملف Lua (multi-layer)")
async def cmd_deobf(interaction: discord.Interaction, file: discord.Attachment):
    if not file.filename.endswith((".lua", ".txt")):
        await interaction.response.send_message("⚠️ الملف لازم `.lua` أو `.txt`", ephemeral=True)
        return
    await interaction.response.defer()
    data = await file.read()
    try:
        layer = data.decode("utf-8", errors="replace")
    except Exception:
        await interaction.followup.send("❌ مش قادر يقرأ الملف")
        return
    try:
        depth = 0
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
    if depth == 0 and layer == data.decode("utf-8", "replace"):
        await interaction.followup.send("⚠️ ما لقيت تشفير XOR+ROR\nجرّب `/sss` تعرف نوع التشفير")
        return
    out_name = file.filename.rsplit(".", 1)[0] + "_decoded.lua"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.lua', encoding='utf-8', delete=False) as tmp:
        tmp.write(layer); tmp_path = tmp.name
    try:
        await interaction.followup.send(
            f"🔓 **{file.filename}** — فُكّ تشفيره\n"
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
    try:
        src = data.decode("utf-8")
    except UnicodeDecodeError:
        src = data.decode("latin-1")
    detection = detect_obfuscation(src)
    await interaction.followup.send(
        f"**📄 {file.filename}**\n"
        f"الحجم: `{len(data):,} bytes` | الأسطر: `{src.count(chr(10))+1:,}`\n\n"
        f"**🔍 نوع التشفير:**\n{detection}")

# ── /luraph ──────────────────────────────────────────────────
@client.tree.command(name="luraph", description="فك Luraph VM الحقيقي (getfenv)")
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
    if not re.search(r'local\s+\w+\s*=\s*\(getfenv', src):
        await interaction.followup.send("⚠️ الملف مش Luraph VM\nجرّب `/sss`")
        return
    try:
        report = luraph_vm_strings_report(src)
    except Exception as e:
        await interaction.followup.send(f"❌ error: `{e}`")
        return
    if report is None:
        await interaction.followup.send("❌ ما قدر يفك الـ VM")
        return
    if len(report) <= 1900:
        await interaction.followup.send(report)
    else:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', encoding='utf-8', delete=False) as tmp:
            tmp.write(report); tmp_path = tmp.name
        try:
            await interaction.followup.send(
                f"🔴 **Luraph VM** — الحجم: `{len(data):,}` bytes",
                file=discord.File(tmp_path, filename="luraph_report.txt"))
        finally:
            os.unlink(tmp_path)

# ── /fetch ───────────────────────────────────────────────────
@client.tree.command(name="fetch", description="جيب كود من URL وافكه")
async def cmd_fetch(interaction: discord.Interaction, url: str):
    await interaction.response.defer()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Roblox/WinInet", "Accept": "*/*"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read(5 * 1024 * 1024)
    except urllib.error.HTTPError as e:
        await interaction.followup.send(f"❌ HTTP {e.code}: `{url}`"); return
    except Exception as e:
        await interaction.followup.send(f"❌ فشل الجلب: `{e}`"); return
    try:
        layer = raw.decode("utf-8", errors="replace")
    except Exception:
        await interaction.followup.send("❌ مش قادر يقرأ الرد"); return
    original = layer
    detection = detect_obfuscation(original)
    is_luraph_vm = re.search(r'local\s+\w+\s*=\s*\(getfenv', original)
    out_name = "fetched_decoded.lua"
    if is_luraph_vm:
        try:
            report = luraph_vm_strings_report(original)
        except Exception as e:
            await interaction.followup.send(f"❌ error في فك Luraph VM: `{e}`"); return
        if report is None:
            await interaction.followup.send(f"🌐 `{url[:80]}`\n❌ ما قدر يفك الـ VM"); return
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', encoding='utf-8', delete=False) as tmp:
            tmp.write(report); tmp_path = tmp.name
        try:
            await interaction.followup.send(
                f"🌐 `{url[:80]}`\nنوع: {detection.splitlines()[0]}",
                file=discord.File(tmp_path, filename="luraph_report.txt"))
        finally:
            os.unlink(tmp_path)
    else:
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
            await interaction.followup.send(f"❌ error: `{e}`"); return
        with tempfile.NamedTemporaryFile(mode='w', suffix='.lua', encoding='utf-8', delete=False) as tmp:
            tmp.write(layer); tmp_path = tmp.name
        try:
            await interaction.followup.send(
                f"🌐 `{url[:80]}`\nنوع: {detection.splitlines()[0]}\nطبقات مفكوكة: `{depth}`",
                file=discord.File(tmp_path, filename=out_name))
        finally:
            os.unlink(tmp_path)

# ── /help ─────────────────────────────────────────────────────
@client.tree.command(name="help", description="قائمة الأوامر")
async def cmd_help(interaction: discord.Interaction):
    await interaction.response.send_message(
        "**🔐 أوامر التشفير:**\n"
        "`/mega` — **MEGA: 5 طبقات متداخلة** (الأقوى) 🆕\n"
        "  ├ StringSplit → يقطع كل الـ strings\n"
        "  ├ DoubleXor  → XOR مزدوج بمفتاحين\n"
        "  ├ LuraphStyle → XOR+ROL+3 مفاتيح\n"
        "  ├ JunkSplit  → تقطيع + آلاف أسطر وهمية\n"
        "  └ NumericByte → جدول أرقام خارجي\n\n"
        "`/xor` — تشفير XOR+ROL (طبقة واحدة)\n"
        "`/get` — تمويه بجدول أرقام (بسيط)\n\n"
        "**🔓 أوامر الفك:**\n"
        "`/deobf` — فك تشفير XOR+ROR (multi-layer)\n"
        "`/luraph` — فك Luraph VM الحقيقي (getfenv)\n"
        "`/fetch` — جيب كود من URL وافكه\n"
        "`/sss` — كشف نوع التشفير\n"
        "`/help` — القائمة دي")

@client.event
async def on_ready():
    print(f"[✓] bot online: {client.user}")

threading.Thread(target=run_health_server, daemon=True).start()
client.run(TOKEN)
