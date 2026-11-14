"""
luraph_style_mobile.py — Luraph-style multi-layer obfuscator + string extractor
استخدام مع botur.py
"""

import re, random, struct, os

# ─── helpers ──────────────────────────────────────────────────────────────────

def _xor8(a: int, b: int) -> int:
    return a ^ b

def _ror8(b: int, n: int) -> int:
    n &= 7
    if n == 0:
        return b
    return ((b >> n) | (b << (8 - n))) & 0xFF

def _rol8(b: int, n: int) -> int:
    return _ror8(b, 8 - (n & 7))

def _encode_bytes_lua(data: bytes) -> str:
    """bytes → Lua escape string  "\\97\\98\\99..." """
    return '"' + ''.join(f'\\{b}' for b in data) + '"'

def _build_assembled_var(varname: str, data: bytes, rng: random.Random) -> str:
    """
    بيبني متغير على شكل:
    local <varname>=(function()local _p={...}local _o={...}...end)()
    """
    n = max(2, min(8, len(data) // 64 + 2))
    chunk_size = max(1, len(data) // n)
    chunks: list[bytes] = []
    i = 0
    while i < len(data):
        end = i + chunk_size if len(chunks) < n - 1 else len(data)
        chunks.append(data[i:end])
        i = end

    order = list(range(len(chunks)))
    rng.shuffle(order)
    # _p صفيف الـ chunks بالترتيب المخلوط، _o الترتيب الصحيح
    perm_chunks = [None] * len(chunks)
    inv_order = [0] * len(chunks)
    for shuffled_idx, orig_idx in enumerate(order):
        perm_chunks[shuffled_idx] = chunks[orig_idx]
        inv_order[orig_idx] = shuffled_idx + 1   # 1-based

    p_entries = ','.join(_encode_bytes_lua(c) for c in perm_chunks)
    o_entries = ','.join(str(x) for x in inv_order)

    # الدالة بتجمّع الـ chunks بالترتيب الصحيح
    return (
        f'local {varname}=(function()'
        f'local _p={{{p_entries}}}'
        f'local _o={{{o_entries}}}'
        f'local _r={{}}for _i=1,#{{{o_entries}}} do _r[_o[_i]]=_p[_i] end '
        f'local _s=""for _=1,#_r do _s=_s.._r[_] end return _s end)()'
    )


# ─── obfuscator ───────────────────────────────────────────────────────────────

ROTATION_TABLE = (3, 1, 5, 2, 6, 4, 7)   # 7 عناصر — نفس المستخدم في الـ decoder

class LuraphStyleObf:
    def __init__(self, seed: int | None = None):
        self.seed = seed if seed is not None else random.getrandbits(64)
        self._rng = random.Random(self.seed)

    def _make_varname(self) -> str:
        prefix = '_' + ''.join(self._rng.choice('IlO0ij1oL') for _ in range(self._rng.randint(6, 10)))
        return prefix

    def obfuscate(self, src: str) -> str:
        data = src.encode('utf-8')
        result = self._encrypt_layer(data)
        return result

    def _encrypt_layer(self, payload: bytes) -> str:
        rng = self._rng

        key1 = bytes(rng.randint(0, 255) for _ in range(rng.randint(32, 64)))
        key2 = bytes(rng.randint(0, 255) for _ in range(rng.randint(32, 64)))
        key3 = bytes(rng.randint(0, 255) for _ in range(rng.randint(16, 32)))
        rotation = list(ROTATION_TABLE)

        L1, L2, L3 = len(key1), len(key2), len(key3)
        enc = bytearray()
        for i, b in enumerate(payload):
            ia = i % L1; ib = i % L2
            mka = key3[ia % L3]; mkb = key3[ib % L3]
            b = _xor8(b, _xor8(key1[ia], mka))
            b = _rol8(b, rotation[i % 7])
            b = _xor8(b, _xor8(key2[ib], mkb))
            enc.append(b)

        k1n = self._make_varname()
        k2n = self._make_varname()
        k3n = self._make_varname()
        pn  = self._make_varname()
        vn  = self._make_varname()   # اسم متغير الـ size
        an  = self._make_varname()
        bn  = self._make_varname()
        cn  = self._make_varname()

        rot_str = ','.join(f'({r})' for r in rotation)

        lines = [
            _build_assembled_var(k1n, key1, rng),
            _build_assembled_var(k2n, key2, rng),
            _build_assembled_var(k3n, key3, rng),
            _build_assembled_var(pn,  bytes(enc), rng),
            f'local {an},{bn},{cn}=#{k1n},#{k2n},#{k3n}',
            f'local _rot={{{rot_str}}}',
            (
                f'local _out={{}} '
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
                f'load({vn})()'
            ),
        ]
        return '\n'.join(lines)


# ─── string extractor (للـ /deobf command البسيط) ────────────────────────────

def deobfuscate_strings(src: str) -> tuple[str | None, list[tuple[str, str]]]:
    """
    يبحث عن دالة فك تشفير Luraph-style في src.
    يرجع (اسم الدالة, [(encoded, decoded), ...])
    """
    # pattern: function name + string table
    # يبحث عن _0xNNNN pattern أو أي اسم مشابه
    fn_m = re.search(
        r'local function (_0x[0-9a-f]+)\s*\(_0x[0-9a-f]+\).*?'
        r'local _0x[0-9a-f]+=_0x[0-9a-f]+\[',
        src, re.DOTALL
    )
    if not fn_m:
        return None, []

    dec_func = fn_m.group(1)

    # استخراج الـ key
    key_m = re.search(r'_0x041f\s*=\s*\{([^}]+)\}', src)
    if not key_m:
        # محاولة ثانية — أي متغير يبدو key
        key_m = re.search(r'local\s+(_0x[0-9a-f]+)\s*=\s*\{((?:\s*\d+\s*,?\s*){4,})\}', src)
        if not key_m:
            return dec_func, []
        key = [int(x.strip()) for x in key_m.group(2).split(',') if x.strip()]
    else:
        key = [int(x.strip()) for x in key_m.group(1).split(',') if x.strip()]

    # استخراج الـ string table
    t_start = src.find('local _0x945f={"')
    t_end   = src.find('};local _0x95902=')
    if t_start < 0 or t_end < 0:
        return dec_func, []

    table_src   = src[t_start + len('local _0x945f={'):t_end]
    raw_entries = re.findall(r'"((?:\\[0-9]+|[^"\\])*)"', table_src)

    kl = len(key)
    results: list[tuple[str, str]] = []
    for entry in raw_entries:
        raw: list[int] = []
        i = 0
        while i < len(entry):
            if entry[i] == '\\':
                j = i + 1; num = ''
                while j < len(entry) and entry[j].isdigit():
                    num += entry[j]; j += 1
                raw.append(int(num)); i = j
            else:
                raw.append(ord(entry[i])); i += 1
        db = bytes((b - key[idx % kl] + 256) % 256 for idx, b in enumerate(raw))
        try:
            dec = db.decode('utf-8', 'replace')
        except Exception:
            dec = repr(db)
        results.append((entry[:40], dec[1:] if dec else ''))   # strip type prefix

    return dec_func, results
