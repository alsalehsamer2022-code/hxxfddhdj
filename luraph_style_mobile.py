#!/usr/bin/env python3
"""
luraph_style_mobile.py — v2.1 نسخة موبايل (Pydroid)
شغّله مباشرة، يسألك عن مسار الملف
الجديد: إصلاح Roblox globals + خيار فك التشفير
"""

VERSION = "2.1"

import re, random, secrets, os

# ══════════════════════════════════════════════════════════════════
CONFUSING = list("IlO0ij1oL")

def gen_name(rng, length=None):
    if length is None:
        length = rng.randint(8, 14)
    first_pool = [c for c in CONFUSING if not c.isdigit()]
    name = rng.choice(first_pool)
    for _ in range(length - 1):
        name += rng.choice(CONFUSING)
    return name

LUA_KEYWORDS = {
    'and','break','do','else','elseif','end','false','for',
    'function','goto','if','in','local','nil','not','or',
    'repeat','return','then','true','until','while',
}

# Roblox globals + standard Lua globals — لا يتم تشفيرها كـ ENV[x]
# بل تُضاف كـ local في الهيدر مباشرة
ROBLOX_DIRECT = {
    'game','workspace','script','wait','task',
    'Instance','Vector3','CFrame','Color3','UDim2','Enum',
    'Vector2','TweenInfo','NumberSequence','ColorSequence',
    'Ray','Region3','BrickColor','Random','tick','time',
    'typeof','spawn','delay',
    'HttpService','RunService','Players','UserInputService',
    'TweenService','Lighting','SoundService','StarterGui',
    'ReplicatedStorage','ServerStorage','ServerScriptService',
}

LUA_GLOBALS = {
    'print','warn','error','type','tostring','tonumber',
    'pairs','ipairs','next','select','unpack','table','string',
    'math','pcall','xpcall','assert','require','load','loadstring',
    'rawget','rawset','rawequal','rawlen','setmetatable','getmetatable',
    'collectgarbage','dofile','_VERSION','coroutine',
    'getfenv','_ENV','_G','io','bit32','utf8','debug','package','arg',
    'os',
} | ROBLOX_DIRECT

def gen_unique_names(rng, count):
    seen = set()
    result = []
    while len(result) < count:
        n = gen_name(rng, rng.randint(8, 14))
        if n not in seen and n not in LUA_KEYWORDS and n not in LUA_GLOBALS:
            seen.add(n)
            result.append(n)
    return result

def gen_key(rng, length=None):
    if length is None:
        length = rng.randint(4, 12)
    pool = [chr(c) for c in range(33, 127) if chr(c) not in ('"', '\\')]
    return ''.join(rng.choice(pool) for _ in range(length))

def xor_encrypt(text, key):
    kl = len(key)
    out = []
    for i, c in enumerate(text):
        kb = ord(key[i % kl])
        eb = (ord(c) + kb) % 256
        out.append(eb)
    return bytes(out)

def xor_decrypt(data, key):
    kl = len(key)
    out = []
    for i, b in enumerate(data):
        kb = ord(key[i % kl]) if isinstance(key[i % kl], str) else key[i % kl]
        db = (b - kb) % 256
        out.append(chr(db))
    return ''.join(out)

def lua_escape(data):
    out = []
    for b in data:
        if b == ord('"'):
            out.append('\\"')
        elif b == ord('\\'):
            out.append('\\\\')
        elif b == ord('\n'):
            out.append('\\n')
        elif b == ord('\r'):
            out.append('\\r')
        elif b == ord('\0'):
            out.append('\\0')
        elif 32 <= b <= 126:
            out.append(chr(b))
        else:
            out.append(f'\\{b}')
    return '"' + ''.join(out) + '"'

TOKEN_RE = re.compile(
    r'(--\[\[.*?\]\]'
    r'|--[^\n]*'
    r'|\[\[.*?\]\]'
    r'|"(?:\\.|[^"\\])*"'
    r"|'(?:\\.|[^'\\])*'"
    r'|0[xX][0-9a-fA-F]+'
    r'|\d+\.?\d*(?:[eE][+-]?\d+)?'
    r'|[A-Za-z_][A-Za-z0-9_]*'
    r'|\.\.'
    r'|\.\.\.'
    r'|==|~=|<=|>=|::'
    r'|[-+*/%%^#&|~<>=(){}\[\];:,./\\]'
    r'|\s+)',
    re.DOTALL
)

def tokenize(src):
    tokens = []
    for m in TOKEN_RE.finditer(src):
        tokens.append(m.group(0))
    rebuilt = ''.join(tokens)
    if rebuilt != src:
        return [src]
    return tokens


class LuraphStyleObf:
    def __init__(self, seed=None):
        self.seed = seed if seed is not None else secrets.randbits(64)
        self.rng  = random.Random(self.seed)
        self.vENV  = gen_name(self.rng, 12)
        self.vBYTE = gen_name(self.rng, 10)
        self.vCHAR = gen_name(self.rng, 10)
        self.vDEC  = gen_name(self.rng, 10)
        self.id_map = {}
        self.str_cache = {}
        self._name_pool = []
        self._name_idx = 0
        # اسماء مشفّرة للـ Roblox direct globals
        self._rbx_map = {}

    def _new_name(self):
        while self._name_idx >= len(self._name_pool):
            self._name_pool += gen_unique_names(self.rng, 100)
        n = self._name_pool[self._name_idx]
        self._name_idx += 1
        return n

    def obf_id(self, name):
        if name not in self.id_map:
            self.id_map[name] = self._new_name()
        return self.id_map[name]

    def encrypt_string(self, text):
        if text in self.str_cache:
            enc_bytes, key = self.str_cache[text]
        else:
            key = gen_key(self.rng)
            enc_bytes = xor_encrypt(text, key)
            self.str_cache[text] = (enc_bytes, key)
        enc_lit = lua_escape(enc_bytes)
        key_lit = lua_escape(key.encode('utf-8'))
        return f'{self.vDEC}({enc_lit},{key_lit})'

    def _collect_identifiers(self, tokens):
        ids = set()
        for tok in tokens:
            if re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', tok):
                if tok not in LUA_KEYWORDS and tok not in LUA_GLOBALS:
                    ids.add(tok)
        return ids

    def _is_string(self, tok):
        return tok.startswith('"') or tok.startswith("'") or tok.startswith('[[')

    def _unescape_string(self, tok):
        if tok.startswith('[['):
            return tok[2:-2]
        inner = tok[1:-1]
        result = []
        i = 0
        while i < len(inner):
            if inner[i] == '\\' and i+1 < len(inner):
                e = inner[i+1]
                esc = {'n':'\n','r':'\r','t':'\t','a':'\a','b':'\b',
                       'f':'\f','v':'\v','\\':'\\','"':'"',"'":"'","0":'\0'}
                if e in esc:
                    result.append(esc[e]); i+=2
                elif e.isdigit():
                    j=i+1
                    while j < min(i+4,len(inner)) and inner[j].isdigit(): j+=1
                    result.append(chr(int(inner[i+1:j]))); i=j
                else:
                    result.append(e); i+=2
            else:
                result.append(inner[i]); i+=1
        return ''.join(result)

    def transform(self, src):
        tokens = tokenize(src)
        ids = self._collect_identifiers(tokens)

        # اعطي اسماء مشفّرة للـ Roblox direct globals المستخدمة في الكود
        used_rbx = {t for t in tokens if t in ROBLOX_DIRECT}
        for g in used_rbx:
            self._rbx_map[g] = self._new_name()

        new_names = gen_unique_names(self.rng, len(ids) + 50)
        for orig, new in zip(sorted(ids), new_names):
            self.id_map[orig] = new
        self._name_pool = new_names[len(ids):]
        self._name_idx  = 0

        out_tokens = []
        i = 0
        while i < len(tokens):
            tok = tokens[i]
            if tok.startswith('--'):
                i += 1; continue
            if tok.strip() == '':
                out_tokens.append('\n' if '\n' in tok else ' ')
                i += 1; continue
            if self._is_string(tok):
                try:
                    value = self._unescape_string(tok)
                    out_tokens.append('""' if len(value)==0 else self.encrypt_string(value))
                except Exception:
                    out_tokens.append(tok)
                i += 1; continue
            if re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', tok):
                if tok in LUA_KEYWORDS:
                    out_tokens.append(tok)
                elif tok in ROBLOX_DIRECT:
                    # استخدم الاسم المشفّر المحلي بدل ENV[x]
                    out_tokens.append(self._rbx_map.get(tok, tok))
                elif tok in LUA_GLOBALS:
                    out_tokens.append(f'{self.vENV}[{self.encrypt_string(tok)}]')
                else:
                    out_tokens.append(self.id_map.get(tok, tok))
                i += 1; continue
            out_tokens.append(tok)
            i += 1
        return ''.join(out_tokens)

    def build_header(self):
        vCT  = gen_name(self.rng, 8)
        vKEY = gen_name(self.rng, 8)
        vOUT = gen_name(self.rng, 8)
        vKL  = gen_name(self.rng, 8)
        vIDX = gen_name(self.rng, 7)
        dummies = []
        for _ in range(self.rng.randint(3, 6)):
            dv = gen_name(self.rng, 9)
            dummies.append(f'local {dv}=nil')
        dummy_block = '\n'.join(dummies)

        # سطور الـ Roblox direct globals — local مشفّر = الـ global الأصلي
        rbx_lines = []
        for orig, alias in self._rbx_map.items():
            rbx_lines.append(f'local {alias}={orig}')
        rbx_block = '\n'.join(rbx_lines)

        header = f'''local {self.vENV}=(getfenv and getfenv(1)) or _ENV or _G
local {self.vBYTE},{self.vCHAR}=string.byte,string.char
local function {self.vDEC}({vCT},{vKEY})
local {vOUT}=""
local {vKL}=#{vKEY}
for {vIDX}=1,#{vCT} do
{vOUT}={vOUT}..{self.vCHAR}(({self.vBYTE}({vCT},{vIDX})-{self.vBYTE}({vKEY},({vIDX}-1)%{vKL}+1))%256)
end
return {vOUT}
end
{rbx_block}
{dummy_block}
'''
        return header

    def obfuscate(self, src):
        body   = self.transform(src)
        header = self.build_header()
        return header + body


# ══════════════════════════════════════════════════════════════════
# فك التشفير — يستخرج الـ strings المشفّرة ويفكّها
# ══════════════════════════════════════════════════════════════════

def lua_unescape_bytes(s):
    """تحويل Lua string literal إلى bytes"""
    result = []
    i = 0
    while i < len(s):
        if s[i] == '\\' and i+1 < len(s):
            e = s[i+1]
            if e == 'n':  result.append(10);  i+=2
            elif e == 'r': result.append(13); i+=2
            elif e == '0': result.append(0);  i+=2
            elif e == '\\': result.append(92); i+=2
            elif e == '"': result.append(34);  i+=2
            elif e == "'": result.append(39);  i+=2
            elif e.isdigit():
                j = i+1
                while j < min(i+4, len(s)) and s[j].isdigit(): j+=1
                result.append(int(s[i+1:j]) % 256); i=j
            else:
                result.append(ord(e)); i+=2
        else:
            result.append(ord(s[i])); i+=1
    return bytes(result)

def deobfuscate_strings(lua_code):
    """يستخرج كل الـ strings المشفّرة ويفكّها"""
    # البحث عن نمط: FNAME("encrypted","key")
    # أول دالة تعريف في الملف هي دالة الفك
    dec_func = None
    func_m = re.search(r'local function (\w+)\(', lua_code)
    if func_m:
        dec_func = func_m.group(1)

    if not dec_func:
        return None, []

    pattern = re.compile(
        rf'{re.escape(dec_func)}\("((?:\\.|[^"\\])*)","((?:\\.|[^"\\])*)"\)',
    )

    results = []
    for m in pattern.finditer(lua_code):
        enc_str = m.group(1)
        key_str = m.group(2)
        try:
            enc_bytes = lua_unescape_bytes(enc_str)
            key_bytes = lua_unescape_bytes(key_str)
            key_text  = key_bytes.decode('utf-8', errors='replace')
            kl = len(key_text)
            decrypted = ''
            for i, b in enumerate(enc_bytes):
                kb = ord(key_text[i % kl])
                decrypted += chr((b - kb) % 256)
            results.append((m.group(0)[:40] + '...', decrypted))
        except Exception as ex:
            results.append((m.group(0)[:40], f'[error: {ex}]'))

    return dec_func, results


def deobf_main():
    print("=== فك تشفير ===")
    path = input("مسار الملف المشفّر (.lua): ").strip()
    if not os.path.isfile(path):
        print(f"[!] مش موجود: {path}")
        return

    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        code = f.read()

    dec_func, strings = deobfuscate_strings(code)
    if dec_func is None:
        print("[!] ما لقيت دالة فك التشفير في الملف")
        return

    print(f"[*] دالة الفك: {dec_func}")
    print(f"[*] عدد الـ strings المشفّرة: {len(strings)}\n")

    out_path = path.rsplit('.', 1)[0] + "_decoded.txt"
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(f"فك تشفير: {os.path.basename(path)}\n")
        f.write(f"دالة الفك: {dec_func}\n")
        f.write("=" * 60 + "\n\n")
        for i, (orig, dec) in enumerate(strings, 1):
            f.write(f"[{i}] {orig}\n    → {dec!r}\n\n")
            if i <= 20:
                print(f"  [{i}] → {dec!r}")

    if len(strings) > 20:
        print(f"  ... و {len(strings)-20} أكثر")
    print(f"\n[✓] الكل محفوظ في: {out_path}")


# ══════════════════════════════════════════════════════════════════
def main():
    print(f"=== luraph_style_mobile v{VERSION} ===")
    print("1) تشفير ملف")
    print("2) فك تشفير ملف")
    choice = input("اختر (1/2): ").strip()

    if choice == '2':
        deobf_main()
        return

    # === تشفير ===
    input_path = input("مسار ملف الـ input (.lua): ").strip()
    if not os.path.isfile(input_path):
        print(f"[!] مش موجود: {input_path}")
        return

    default_out = input_path.rsplit('.', 1)[0] + "_obf.lua"
    out_prompt = input(f"مسار الـ output [{default_out}]: ").strip()
    output_path = out_prompt if out_prompt else default_out

    seed_str = input("seed (اتركه فاضي = عشوائي): ").strip()
    seed = int(seed_str, 0) if seed_str else None

    with open(input_path, 'r', encoding='utf-8') as f:
        src = f.read()

    print(f"[*] input  {len(src)} chars")
    obf = LuraphStyleObf(seed=seed)
    print(f"[*] seed   {obf.seed:#018x}")

    result = obf.obfuscate(src)

    with open(output_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(result)

    print(f"[*] output {len(result)} chars  → {output_path}")
    print("[✓] done")

if __name__ == '__main__':
    main()
