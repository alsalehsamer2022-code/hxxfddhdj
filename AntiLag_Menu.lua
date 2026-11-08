--[[
    مضاد لاج | ANTI LAG   (Roblox executor script, one file)
    - Anti-AFK: stops the 20-minute idle kick (Error 278)
    - FPS cap + graphics quality, kill effects, flat materials, no shadows, lite lighting/water
    - Memory cleaner, optional 3D freeze for AFK, FPS / Ping / RAM meter
    - Every tweak is reversible ("Restore defaults"). Player characters are never touched (skins stay).
    Close button: restores visuals but keeps Anti-AFK alive. Re-running the script replaces the old menu.
]]

local Players      = game:GetService("Players")
local Lighting     = game:GetService("Lighting")
local RunService   = game:GetService("RunService")
local UIS          = game:GetService("UserInputService")
local Stats        = game:GetService("Stats")
local lp           = Players.LocalPlayer

if _G.__ALM and _G.__ALM.unload then pcall(_G.__ALM.unload, true) end

-- ================= state =================
local S = {
    afk = true, gc = true, effects = true, flat = true, shadow = true, tex = false,
    light = true, terrain = true, freeze = false, hud = false,
    fps = 60, quality = 3, lang = "ar",
}
local FPS_STEPS = {30, 45, 60, 90, 120, 240}

local alive = true
local conns = {}
local function bind(sig, fn)
    local c = sig:Connect(fn)
    table.insert(conns, c)
    return c
end

-- ================= tweaks on the map =================
local TW = {
    effects = {prop = "Enabled", val = false, match = function(o)
        return o:IsA("ParticleEmitter") or o:IsA("Trail") or o:IsA("Smoke") or o:IsA("Fire")
            or o:IsA("Sparkles") or o:IsA("Beam")
    end},
    flat = {prop = "Material", val = Enum.Material.SmoothPlastic, match = function(o)
        return o:IsA("BasePart") and not o:IsA("Terrain")
    end},
    shadow = {prop = "CastShadow", val = false, match = function(o) return o:IsA("BasePart") end},
    tex = {prop = "Transparency", val = 1, match = function(o) return o:IsA("Texture") end},
}
local orig = setmetatable({}, {__mode = "k"})      -- inst -> {tweakKey = originalValue}

local function in_char(o)
    local m = o:FindFirstAncestorOfClass("Model")
    return m ~= nil and (m:FindFirstChildOfClass("Humanoid") ~= nil or Players:GetPlayerFromCharacter(m) ~= nil)
end

local function apply_obj(o)
    for key, tw in pairs(TW) do
        if S[key] and tw.match(o) and not in_char(o) then
            local t = orig[o]
            if not t then t = {}; orig[o] = t end
            if t[key] == nil then t[key] = o[tw.prop] end
            o[tw.prop] = tw.val
        end
    end
end

local function restore(key)
    local prop = TW[key].prop
    for o, t in pairs(orig) do
        if t[key] ~= nil then
            pcall(function() o[prop] = t[key] end)
            t[key] = nil
        end
    end
end

local sweepGen = 0
local function sweep()
    sweepGen = sweepGen + 1
    local gen = sweepGen
    task.spawn(function()
        local n = 0
        for _, o in ipairs(workspace:GetDescendants()) do
            if gen ~= sweepGen or not alive then return end
            pcall(apply_obj, o)
            n = n + 1
            if n % 300 == 0 then task.wait() end          -- chunks: no freeze while working
        end
    end)
end

bind(workspace.DescendantAdded, function(o)
    if not alive or not (S.effects or S.flat or S.shadow or S.tex) then return end
    task.delay(0.4, function() pcall(apply_obj, o) end)   -- let models assemble first
end)

-- ================= lighting / terrain / settings =================
local origShadows = Lighting.GlobalShadows
local lfx = {}
local function light_set(v)
    for _, o in ipairs(Lighting:GetChildren()) do
        if o:IsA("BloomEffect") or o:IsA("BlurEffect") or o:IsA("SunRaysEffect") or o:IsA("DepthOfFieldEffect") then
            if v then
                if lfx[o] == nil then lfx[o] = o.Enabled end
                o.Enabled = false
            elseif lfx[o] ~= nil then
                o.Enabled = lfx[o]
                lfx[o] = nil
            end
        end
    end
end

local torig = nil
local function terrain_set(v)
    local t3 = workspace:FindFirstChildOfClass("Terrain")
    if not t3 then return end
    pcall(function()
        if v then
            torig = torig or {t3.Decoration, t3.WaterWaveSize, t3.WaterWaveSpeed, t3.WaterReflectance}
            t3.Decoration = false
            t3.WaterWaveSize = 0; t3.WaterWaveSpeed = 0; t3.WaterReflectance = 0
        elseif torig then
            t3.Decoration, t3.WaterWaveSize, t3.WaterWaveSpeed, t3.WaterReflectance = torig[1], torig[2], torig[3], torig[4]
            torig = nil
        end
    end)
end

local function shadows_global()
    pcall(function() Lighting.GlobalShadows = (not S.shadow) and origShadows end)
end
local function fps_apply() pcall(function() if setfpscap then setfpscap(S.fps) end end) end
local function q_apply()
    local ok = pcall(function()
        settings().Rendering.QualityLevel = Enum.QualityLevel["Level" .. string.format("%02d", S.quality)]
    end)
    if not ok then pcall(function() settings().Rendering.QualityLevel = S.quality end) end
end
local function freeze_apply() pcall(function() RunService:Set3dRenderingEnabled(not S.freeze) end) end

local afkConn
local function afk_set(v)
    if afkConn then afkConn:Disconnect(); afkConn = nil end
    if v then
        local ok, VU = pcall(function() return game:GetService("VirtualUser") end)
        if ok and VU then
            afkConn = lp.Idled:Connect(function()
                pcall(function() VU:CaptureController(); VU:ClickButton2(Vector2.new(0, 0)) end)
            end)
        end
    end
end

task.spawn(function()
    while alive do
        task.wait(30)
        if S.gc then pcall(collectgarbage) end
    end
end)

-- ================= GUI =================
local PAL = {
    bg = Color3.fromRGB(14, 18, 24), card = Color3.fromRGB(24, 30, 40), acc = Color3.fromRGB(46, 204, 113),
    off = Color3.fromRGB(52, 60, 74), text = Color3.fromRGB(240, 244, 248), sub = Color3.fromRGB(150, 160, 175),
    bad = Color3.fromRGB(200, 70, 60),
}
local FONT = Enum.Font.SourceSansBold

local function new(class, props, parent)
    local o = Instance.new(class)
    for k, v in pairs(props or {}) do o[k] = v end
    if parent then o.Parent = parent end
    return o
end
local function corner(o, r) return new("UICorner", {CornerRadius = UDim.new(0, r or 8)}, o) end

local gui = new("ScreenGui", {Name = "AntiLagMenu", ResetOnSpawn = false, IgnoreGuiInset = true,
    ZIndexBehavior = Enum.ZIndexBehavior.Sibling, DisplayOrder = 1000})
local okp = pcall(function() gui.Parent = (gethui and gethui()) or game:GetService("CoreGui") end)
if not okp or not gui.Parent then gui.Parent = lp:WaitForChild("PlayerGui") end

local main = new("Frame", {Name = "Main", AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.new(0.5, 0, 0.5, 0),
    Size = UDim2.fromOffset(300, 330), BackgroundColor3 = PAL.bg, BorderSizePixel = 0, Active = true}, gui)
corner(main, 12)
new("UIStroke", {Color = PAL.acc, Thickness = 1.5, ApplyStrokeMode = Enum.ApplyStrokeMode.Border}, main)

local bar = new("Frame", {Size = UDim2.new(1, 0, 0, 40), BackgroundColor3 = PAL.card, BorderSizePixel = 0}, main)
corner(bar, 12)
new("TextLabel", {BackgroundTransparency = 1, Position = UDim2.fromOffset(12, 0), Size = UDim2.new(1, -90, 1, 0),
    Font = FONT, TextSize = 20, TextColor3 = PAL.text, TextXAlignment = Enum.TextXAlignment.Left,
    Text = "مضاد لاج | ANTI LAG"}, bar)
local btnMin = new("TextButton", {AnchorPoint = Vector2.new(1, 0.5), Position = UDim2.new(1, -44, 0.5, 0),
    Size = UDim2.fromOffset(30, 28), BackgroundColor3 = PAL.off, BorderSizePixel = 0, Font = FONT, TextSize = 20,
    TextColor3 = PAL.text, Text = "–", AutoButtonColor = true}, bar)
corner(btnMin, 8)
local btnClose = new("TextButton", {AnchorPoint = Vector2.new(1, 0.5), Position = UDim2.new(1, -8, 0.5, 0),
    Size = UDim2.fromOffset(30, 28), BackgroundColor3 = PAL.bad, BorderSizePixel = 0, Font = FONT, TextSize = 16,
    TextColor3 = PAL.text, Text = "X", AutoButtonColor = true}, bar)
corner(btnClose, 8)

local body = new("ScrollingFrame", {Position = UDim2.fromOffset(8, 48), Size = UDim2.new(1, -16, 1, -56),
    BackgroundTransparency = 1, BorderSizePixel = 0, ScrollBarThickness = 4, ScrollBarImageColor3 = PAL.acc,
    CanvasSize = UDim2.new(0, 0, 0, 0), AutomaticCanvasSize = Enum.AutomaticSize.Y}, main)
new("UIListLayout", {Padding = UDim.new(0, 6), SortOrder = Enum.SortOrder.LayoutOrder}, body)

local order, langs, renders = 0, {}, {}
local function nxt() order = order + 1; return order end

local function row_base()
    local row = new("Frame", {Size = UDim2.new(1, -6, 0, 40), BackgroundColor3 = PAL.card, BorderSizePixel = 0,
        LayoutOrder = nxt()}, body)
    corner(row, 8)
    return row
end
local function row_label(row, x, ar, en)
    local lbl = new("TextLabel", {BackgroundTransparency = 1, Position = UDim2.fromOffset(x, 0),
        Size = UDim2.new(1, -(x + 8), 1, 0), Font = FONT, TextSize = 16, TextColor3 = PAL.text, TextWrapped = true,
        TextXAlignment = Enum.TextXAlignment.Right, Text = ar}, row)
    table.insert(langs, {lbl, ar, en, false})
    return lbl
end

local function toggle_row(key, ar, en, on_change)
    local row = row_base()
    row_label(row, 70, ar, en)
    local pill = new("TextButton", {Position = UDim2.fromOffset(8, 8), Size = UDim2.fromOffset(52, 24), Font = FONT,
        TextSize = 13, TextColor3 = PAL.text, AutoButtonColor = false, BorderSizePixel = 0, Text = "OFF",
        BackgroundColor3 = PAL.off}, row)
    corner(pill, 12)
    local function render()
        pill.Text = S[key] and "ON" or "OFF"
        pill.BackgroundColor3 = S[key] and PAL.acc or PAL.off
    end
    pill.Activated:Connect(function()
        S[key] = not S[key]
        render()
        if on_change then pcall(on_change, S[key]) end
    end)
    table.insert(renders, render)
    render()
end

local function step_row(ar, en, get, dec, inc)
    local row = row_base()
    row_label(row, 130, ar, en)
    local function small(x, txt)
        local b = new("TextButton", {Position = UDim2.fromOffset(x, 8), Size = UDim2.fromOffset(28, 24), Font = FONT,
            TextSize = 18, TextColor3 = PAL.text, BackgroundColor3 = PAL.off, BorderSizePixel = 0, Text = txt}, row)
        corner(b, 6)
        return b
    end
    local minus, plus = small(8, "-"), small(94, "+")
    local val = new("TextLabel", {BackgroundTransparency = 1, Position = UDim2.fromOffset(38, 8),
        Size = UDim2.fromOffset(52, 24), Font = FONT, TextSize = 16, TextColor3 = PAL.acc, Text = ""}, row)
    local function render() val.Text = tostring(get()) end
    minus.Activated:Connect(function() dec(); render() end)
    plus.Activated:Connect(function() inc(); render() end)
    table.insert(renders, render)
    render()
end

local function action_row(ar, en, color, fn)
    local b = new("TextButton", {Size = UDim2.new(1, -6, 0, 40), BackgroundColor3 = color, BorderSizePixel = 0,
        Font = FONT, TextSize = 17, TextColor3 = PAL.text, Text = ar, LayoutOrder = nxt()}, body)
    corner(b, 8)
    table.insert(langs, {b, ar, en, true})
    b.Activated:Connect(function() pcall(fn) end)
end

local function render_all() for _, r in ipairs(renders) do r() end end
local function relang()
    for _, e in ipairs(langs) do
        e[1].Text = (S.lang == "ar") and e[2] or e[3]
        if not e[4] then
            e[1].TextXAlignment = (S.lang == "ar") and Enum.TextXAlignment.Right or Enum.TextXAlignment.Left
        end
    end
end

local function fps_index()
    for i, v in ipairs(FPS_STEPS) do if v == S.fps then return i end end
    return 3
end

-- ---- rows ----
toggle_row("afk", "منع الطرد بسبب الخمول (Anti-AFK)", "Anti-AFK (no idle kick)", afk_set)
step_row("حد الفريمات", "FPS cap",
    function() return S.fps end,
    function() S.fps = FPS_STEPS[math.max(1, fps_index() - 1)]; fps_apply() end,
    function() S.fps = FPS_STEPS[math.min(#FPS_STEPS, fps_index() + 1)]; fps_apply() end)
step_row("جودة الرسوم (1-10)", "Graphics quality (1-10)",
    function() return S.quality end,
    function() S.quality = math.max(1, S.quality - 1); q_apply() end,
    function() S.quality = math.min(10, S.quality + 1); q_apply() end)
toggle_row("effects", "إيقاف المؤثرات (دخان / نار / جزيئات)", "Kill effects (smoke / fire / particles)",
    function(v) if v then sweep() else restore("effects") end end)
toggle_row("flat", "خامات مسطحة (توفر رام)", "Flat materials (saves RAM)",
    function(v) if v then sweep() else restore("flat") end end)
toggle_row("shadow", "إيقاف الظلال", "No shadows",
    function(v) shadows_global(); if v then sweep() else restore("shadow") end end)
toggle_row("light", "إيقاف البلوم والبلر والأشعة", "No bloom / blur / sun rays", light_set)
toggle_row("terrain", "تخفيف الماء والعشب", "Lite water & grass", terrain_set)
toggle_row("tex", "إخفاء التكستشر", "Hide textures",
    function(v) if v then sweep() else restore("tex") end end)
toggle_row("gc", "تنظيف الذاكرة كل 30 ثانية", "Memory cleaner (30s)")
toggle_row("freeze", "إيقاف الرسم ثلاثي الأبعاد (وضع AFK)", "Freeze 3D (AFK mode)", freeze_apply)

-- HUD
local hud = new("TextLabel", {Name = "AntiLagHud", AnchorPoint = Vector2.new(0.5, 0), Position = UDim2.new(0.5, 0, 0, 34),
    Size = UDim2.fromOffset(250, 22), BackgroundColor3 = PAL.bg, BackgroundTransparency = 0.3, BorderSizePixel = 0,
    Font = FONT, TextSize = 13, TextColor3 = PAL.text, Text = "...", Visible = false, ZIndex = 60}, gui)
corner(hud, 6)
toggle_row("hud", "عداد FPS / بنق / رام", "FPS / Ping / RAM meter", function(v) hud.Visible = v end)

do
    local acc, fpsS = 0, 60
    bind(RunService.Heartbeat, function(dt)
        if not alive or not S.hud then return end
        fpsS = fpsS + (1 / math.max(dt, 1e-4) - fpsS) * 0.1
        acc = acc + dt
        if acc < 0.4 then return end
        acc = 0
        local ping, mem = 0, 0
        pcall(function() ping = Stats.Network.ServerStatsItem["Data Ping"]:GetValue() end)
        pcall(function() mem = Stats:GetTotalMemoryUsageMb() end)
        hud.Text = string.format("FPS %d  |  PING %d ms  |  RAM %d MB", math.floor(fpsS + 0.5),
            math.floor(ping + 0.5), math.floor(mem + 0.5))
    end)
end

local function apply_all()
    afk_set(S.afk); fps_apply(); q_apply(); shadows_global()
    light_set(S.light); terrain_set(S.terrain); freeze_apply()
    hud.Visible = S.hud
    sweep()
end

local function restore_defaults()
    S.effects, S.flat, S.shadow, S.tex, S.light, S.terrain, S.freeze = false, false, false, false, false, false, false
    for key in pairs(TW) do restore(key) end
    light_set(false); terrain_set(false); shadows_global(); freeze_apply()
    render_all()
end

action_row("تطبيق الكل الآن", "Apply all now", PAL.acc, function() apply_all(); render_all() end)
action_row("استرجاع الأصلي", "Restore defaults", PAL.bad, restore_defaults)
action_row("English / عربي", "English / عربي", PAL.off, function()
    S.lang = (S.lang == "ar") and "en" or "ar"
    relang()
end)

-- ---- drag / minimize / close ----
do
    local dragging, dragStart, startPos = false, nil, nil
    bind(bar.InputBegan, function(i)
        if i.UserInputType == Enum.UserInputType.MouseButton1 or i.UserInputType == Enum.UserInputType.Touch then
            dragging, dragStart, startPos = true, i.Position, main.Position
        end
    end)
    bind(UIS.InputChanged, function(i)
        if dragging and (i.UserInputType == Enum.UserInputType.MouseMovement or i.UserInputType == Enum.UserInputType.Touch) then
            local d = i.Position - dragStart
            main.Position = UDim2.new(startPos.X.Scale, startPos.X.Offset + d.X, startPos.Y.Scale, startPos.Y.Offset + d.Y)
        end
    end)
    bind(UIS.InputEnded, function(i)
        if i.UserInputType == Enum.UserInputType.MouseButton1 or i.UserInputType == Enum.UserInputType.Touch then
            dragging = false
        end
    end)
end

local minimized = false
btnMin.Activated:Connect(function()
    minimized = not minimized
    body.Visible = not minimized
    main.Size = minimized and UDim2.fromOffset(300, 40) or UDim2.fromOffset(300, 330)
end)

local function unload(full)
    alive = false
    sweepGen = sweepGen + 1
    for key in pairs(TW) do restore(key) end
    light_set(false); terrain_set(false)
    pcall(function() Lighting.GlobalShadows = origShadows end)
    pcall(function() RunService:Set3dRenderingEnabled(true) end)
    for _, c in ipairs(conns) do pcall(function() c:Disconnect() end) end
    conns = {}
    if full then afk_set(false) end          -- closing the menu keeps Anti-AFK alive; re-running replaces it
    pcall(function() gui:Destroy() end)
end
btnClose.Activated:Connect(function() unload(false) end)
_G.__ALM = {unload = unload}

relang()
apply_all()
print("[ANTI LAG] ready | Anti-AFK " .. (S.afk and "on" or "off") .. " | fps cap " .. S.fps)
