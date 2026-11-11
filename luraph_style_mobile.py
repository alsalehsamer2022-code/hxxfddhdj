#!/usr/bin/env python3
"""
luraph_style_mobile.py — نسخة موبايل (Pydroid)
شغّله مباشرة، يسألك عن مسار الملف
"""

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

LUA_GLOBALS = {
    'print','warn','error','type','tostring','tonumber',
    'pairs','ipairs','next','select','unpack','table','string',
    'math','pcall','xpcall','assert','require','load','loadstring',
    'rawget','rawset','rawequal','rawlen','setmetatable','getmetatable',
    'collectgarbage','dofile','_VERSION',
    'game','workspace','script','wait','task',
    'Instance','Vector3','CFrame','Color3','UDim2','Enum',
    'Vector2','TweenInfo','NumberSequence','ColorSequence',
    'Ray','Region3','BrickColor','Random','tick','time',
    'os','typeof','warn','spawn','delay','coroutine',
    'HttpService','RunService','Players','UserInputService',
    'TweenService','Lighting','SoundService','StarterGui',
    'ReplicatedStorage','ServerStorage','ServerScriptService',
    'getfenv','_ENV','_G','string','math','table','io',
    'bit32','utf8','debug','package','arg',
}

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
{dummy_block}
'''
        return header

    def obfuscate(self, src):
        body   = self.transform(src)
        header = self.build_header()
        return header + body


def main():
    print("=== luraph_style_mobile ===")
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
