-- LocalScript | StarterPlayerScripts | Roblox Client
-- قائمة عمودية + أزرار على الشاشة شغالة

local Players = game:GetService("Players")
local CAS     = game:GetService("ContextActionService")

-- إرسال ضغطات حقيقية للّعبة
local VIM
pcall(function() VIM = game:GetService("VirtualInputManager") end)
local function send_key(kc, down)
    if not VIM or not kc then return end
    pcall(function() VIM:SendKeyEvent(down, kc, false, game) end)
end

local player    = Players.LocalPlayer
local playerGui = player:WaitForChild("PlayerGui")

-- ─── KEYS ───────────────────────────────────────────────
local ALL_KEYS = {
    "W","A","S","D","Q","E","R","F","G","H",
    "T","Y","U","I","O","P","Z","X","C","V",
    "B","N","M","J","K","L",
    "1","2","3","4",
    "SPACE","CTRL","SHIFT","ALT","TAB","ESC",
    "F1","F2","F3",
    "UP","DOWN","LEFT","RIGHT",
}

local KEY_MAP = {
    W=Enum.KeyCode.W, A=Enum.KeyCode.A, S=Enum.KeyCode.S, D=Enum.KeyCode.D,
    Q=Enum.KeyCode.Q, E=Enum.KeyCode.E, R=Enum.KeyCode.R, F=Enum.KeyCode.F,
    G=Enum.KeyCode.G, H=Enum.KeyCode.H, T=Enum.KeyCode.T, Y=Enum.KeyCode.Y,
    U=Enum.KeyCode.U, I=Enum.KeyCode.I, O=Enum.KeyCode.O, P=Enum.KeyCode.P,
    Z=Enum.KeyCode.Z, X=Enum.KeyCode.X, C=Enum.KeyCode.C, V=Enum.KeyCode.V,
    B=Enum.KeyCode.B, N=Enum.KeyCode.N, M=Enum.KeyCode.M, J=Enum.KeyCode.J,
    K=Enum.KeyCode.K, L=Enum.KeyCode.L,
    ["1"]=Enum.KeyCode.One, ["2"]=Enum.KeyCode.Two,
    ["3"]=Enum.KeyCode.Three, ["4"]=Enum.KeyCode.Four,
    SPACE=Enum.KeyCode.Space, CTRL=Enum.KeyCode.LeftControl,
    SHIFT=Enum.KeyCode.LeftShift, ALT=Enum.KeyCode.LeftAlt,
    TAB=Enum.KeyCode.Tab, ESC=Enum.KeyCode.Escape,
    F1=Enum.KeyCode.F1, F2=Enum.KeyCode.F2, F3=Enum.KeyCode.F3,
    UP=Enum.KeyCode.Up, DOWN=Enum.KeyCode.Down,
    LEFT=Enum.KeyCode.Left, RIGHT=Enum.KeyCode.Right,
}

-- ─── COLORS ─────────────────────────────────────────────
local C = {
    bg       = Color3.fromRGB(15, 15, 15),
    key_idle = Color3.fromRGB(14, 20, 42),
    key_press= Color3.fromRGB(90, 200, 255),
    key_on   = Color3.fromRGB(0, 90, 200),
    sel      = Color3.fromRGB(0, 110, 230),
    unsel    = Color3.fromRGB(40, 40, 40),
    lock_on  = Color3.fromRGB(200, 30, 30),
    lock_off = Color3.fromRGB(35, 35, 35),
    text     = Color3.new(1,1,1),
    close    = Color3.fromRGB(160,30,30),
}

-- ─── STATE ──────────────────────────────────────────────
local locked      = false
local active_keys = {}   -- label → frame
local menu_open   = false
local menu_btns   = {}   -- label → TextButton
local x_buttons   = {}   -- label → زر الحذف

-- ─── GUI ────────────────────────────────────────────────
local gui = Instance.new("ScreenGui")
gui.Name           = "PCOverlay"
gui.ResetOnSpawn   = false
gui.IgnoreGuiInset = true
gui.DisplayOrder   = 100
gui.Parent         = playerGui

local function rnd(p, r)
    local c = Instance.new("UICorner")
    c.CornerRadius = UDim.new(0, r or 10)
    c.Parent = p
end

-- ─── DRAG HELPER ────────────────────────────────────────
local UIS = game:GetService("UserInputService")

local function make_draggable(obj, tap_down, tap_up, can_move)
    local cur, moved = nil, false
    local startIn = Vector2.new()
    local startPos = obj.Position

    obj.InputBegan:Connect(function(i)
        if cur then return end
        if i.UserInputType ~= Enum.UserInputType.Touch
        and i.UserInputType ~= Enum.UserInputType.MouseButton1 then return end
        cur, moved = i, false
        startIn  = Vector2.new(i.Position.X, i.Position.Y)
        startPos = obj.Position
        if tap_down then tap_down() end
    end)

    UIS.InputChanged:Connect(function(i)
        if not cur then return end
        local ok = (i == cur)
            or (cur.UserInputType == Enum.UserInputType.MouseButton1
                and i.UserInputType == Enum.UserInputType.MouseMovement)
        if not ok then return end
        local d = Vector2.new(i.Position.X, i.Position.Y) - startIn
        if d.Magnitude > 8 and (not can_move or can_move()) then moved = true end
        if moved then
            obj.Position = UDim2.new(
                startPos.X.Scale, startPos.X.Offset + d.X,
                startPos.Y.Scale, startPos.Y.Offset + d.Y)
        end
    end)

    UIS.InputEnded:Connect(function(i)
        if not cur then return end
        local ok = (i == cur)
            or (cur.UserInputType == Enum.UserInputType.MouseButton1
                and i.UserInputType == Enum.UserInputType.MouseButton1)
        if not ok then return end
        local was_moved = moved
        cur, moved = nil, false
        if tap_up then tap_up(was_moved) end
    end)
end

-- ─── SPAWN KEY ON SCREEN ────────────────────────────────
local function spawn_key(label)
    if active_keys[label] then return end
    local kc   = KEY_MAP[label]
    local wide = label=="SPACE" or label=="CTRL" or label=="SHIFT" or label=="ALT"
    local w    = wide and 110 or 54
    local h    = 54

    local frame = Instance.new("Frame")
    frame.Size                   = UDim2.new(0, w, 0, h)
    frame.Position               = UDim2.new(0.5, -w/2, 0.6, 0)
    frame.BackgroundColor3       = C.key_idle
    frame.BackgroundTransparency = 0.12
    frame.BorderSizePixel        = 0
    frame.Active                 = true
    frame.ZIndex                 = 10
    frame.Parent                 = gui
    rnd(frame, 12)

    local stroke = Instance.new("UIStroke")
    stroke.Color = Color3.fromRGB(40,55,95)
    stroke.Thickness = 1
    stroke.Parent = frame

    local lbl = Instance.new("TextLabel")
    lbl.Size                   = UDim2.new(1, 0, 1, 0)
    lbl.BackgroundTransparency = 1
    lbl.TextColor3             = C.text
    lbl.Text                   = label
    lbl.FontFace               = Font.new("rbxasset://fonts/families/GothamSSm.json", Enum.FontWeight.Bold)
    lbl.TextSize               = wide and 13 or 20
    lbl.ZIndex                 = 11
    lbl.Parent                 = frame

    -- X زر حذف صغير
    local xbtn = Instance.new("TextButton")
    xbtn.Size               = UDim2.new(0,16,0,16)
    xbtn.Position           = UDim2.new(1,-17,0,1)
    xbtn.BackgroundColor3   = C.close
    xbtn.TextColor3         = C.text
    xbtn.Text               = "×"
    xbtn.FontFace           = Font.new("rbxasset://fonts/families/GothamSSm.json", Enum.FontWeight.Bold)
    xbtn.TextSize           = 11
    xbtn.BorderSizePixel    = 0
    xbtn.ZIndex             = 12
    xbtn.Parent             = frame
    rnd(xbtn, 4)

    xbtn.Visible = not locked
    x_buttons[label] = xbtn
    xbtn.MouseButton1Click:Connect(function()
        x_buttons[label] = nil
        active_keys[label] = nil
        frame:Destroy()
        if menu_btns[label] then
            menu_btns[label].BackgroundColor3 = C.unsel
        end
    end)

    -- drag + press
    local held = false
    local function release()
        if held then
            held = false
            frame.BackgroundColor3 = C.key_idle
            send_key(kc, false)
        end
    end
    make_draggable(frame,
        function() -- down
            if locked and kc then
                held = true
                frame.BackgroundColor3 = C.key_press
                send_key(kc, true)
            end
        end,
        function() release() end,
        function() return not locked end
    )
    frame.AncestryChanged:Connect(release)

    active_keys[label] = frame
end

local function remove_key(label)
    if active_keys[label] then
        active_keys[label]:Destroy()
        active_keys[label] = nil
    end
end

-- ─── MENU PANEL ─────────────────────────────────────────
local PANEL_W = 160
local PANEL_H = 500

local panel = Instance.new("Frame")
panel.Name                   = "MenuPanel"
panel.Size                   = UDim2.new(0, PANEL_W, 0, PANEL_H)
panel.Position               = UDim2.new(0, 60, 0.5, -PANEL_H/2)
panel.BackgroundColor3       = C.bg
panel.BackgroundTransparency = 0.05
panel.BorderSizePixel        = 0
panel.Visible                = false
panel.ZIndex                 = 50
panel.Parent                 = gui
rnd(panel, 14)

local stroke2 = Instance.new("UIStroke")
stroke2.Color = Color3.fromRGB(60,60,60)
stroke2.Thickness = 1
stroke2.Parent = panel

-- header
local hdr = Instance.new("Frame")
hdr.Size             = UDim2.new(1,0,0,40)
hdr.BackgroundColor3 = Color3.fromRGB(10,10,10)
hdr.BorderSizePixel  = 0
hdr.ZIndex           = 51
hdr.Parent           = panel
rnd(hdr, 14)

local htxt = Instance.new("TextLabel")
htxt.Size                   = UDim2.new(1,-44,1,0)
htxt.Position               = UDim2.new(0,12,0,0)
htxt.BackgroundTransparency = 1
htxt.TextColor3             = C.text
htxt.Text                   = "الأزرار"
htxt.FontFace               = Font.new("rbxasset://fonts/families/GothamSSm.json", Enum.FontWeight.Bold)
htxt.TextSize               = 14
htxt.TextXAlignment         = Enum.TextXAlignment.Left
htxt.ZIndex                 = 52
htxt.Parent                 = hdr

local x_btn = Instance.new("TextButton")
x_btn.Size               = UDim2.new(0,30,0,30)
x_btn.Position           = UDim2.new(1,-35,0,5)
x_btn.BackgroundColor3   = Color3.fromRGB(60,60,60)
x_btn.TextColor3         = C.text
x_btn.Text               = "✕"
x_btn.FontFace           = Font.new("rbxasset://fonts/families/GothamSSm.json", Enum.FontWeight.Bold)
x_btn.TextSize           = 14
x_btn.BorderSizePixel    = 0
x_btn.ZIndex             = 52
x_btn.Parent             = hdr
rnd(x_btn, 8)

x_btn.MouseButton1Click:Connect(function()
    panel.Visible = false
    menu_open = false
end)

-- scroll
local scroll = Instance.new("ScrollingFrame")
scroll.Size                   = UDim2.new(1,-8,1,-48)
scroll.Position               = UDim2.new(0,4,0,44)
scroll.BackgroundTransparency = 1
scroll.BorderSizePixel        = 0
scroll.ScrollBarThickness     = 3
scroll.ScrollBarImageColor3   = Color3.fromRGB(80,80,80)
scroll.CanvasSize             = UDim2.new(0,0,0,0)
scroll.AutomaticCanvasSize    = Enum.AutomaticSize.Y
scroll.ZIndex                 = 51
scroll.Parent                 = panel

local list = Instance.new("UIListLayout")
list.SortOrder = Enum.SortOrder.LayoutOrder
list.Padding   = UDim.new(0,4)
list.Parent    = scroll

local pad = Instance.new("UIPadding")
pad.PaddingTop  = UDim.new(0,4)
pad.PaddingLeft = UDim.new(0,4)
pad.PaddingRight= UDim.new(0,4)
pad.Parent      = scroll

-- بناء قائمة الحروف (كل حرف في سطر)
for idx, label in ipairs(ALL_KEYS) do
    local row = Instance.new("TextButton")
    row.Size             = UDim2.new(1,-8,0,38)
    row.BackgroundColor3 = C.unsel
    row.TextColor3       = C.text
    row.Text             = label
    row.FontFace         = Font.new("rbxasset://fonts/families/GothamSSm.json", Enum.FontWeight.Bold)
    row.TextSize         = 15
    row.BorderSizePixel  = 0
    row.LayoutOrder      = idx
    row.ZIndex           = 53
    row.Parent           = scroll
    rnd(row, 8)

    menu_btns[label] = row

    row.MouseButton1Click:Connect(function()
        if active_keys[label] then
            remove_key(label)
            row.BackgroundColor3 = C.unsel
        else
            spawn_key(label)
            row.BackgroundColor3 = C.sel
        end
    end)
end

-- ─── OPEN BUTTON ⌨ ──────────────────────────────────────
local open_btn = Instance.new("TextButton")
open_btn.Size               = UDim2.new(0,44,0,44)
open_btn.Position           = UDim2.new(0,8,0.5,-22)
open_btn.BackgroundColor3   = Color3.fromRGB(20,20,20)
open_btn.TextColor3         = C.text
open_btn.Text               = "⌨"
open_btn.FontFace           = Font.new("rbxasset://fonts/families/GothamSSm.json", Enum.FontWeight.Bold)
open_btn.TextSize           = 24
open_btn.BorderSizePixel    = 0
open_btn.ZIndex             = 60
open_btn.Parent             = gui
rnd(open_btn, 12)

make_draggable(open_btn, nil, function(moved)
    if not moved then
        menu_open = not menu_open
        panel.Visible = menu_open
        if menu_open then
            local sz = gui.AbsoluteSize
            local ap = open_btn.AbsolutePosition
            local h  = math.min(PANEL_H, sz.Y - 20)
            panel.Size = UDim2.new(0, PANEL_W, 0, h)
            local x = math.clamp(ap.X + 52, 4, math.max(4, sz.X - PANEL_W - 4))
            local y = math.clamp(ap.Y - h/2, 10, math.max(10, sz.Y - h - 10))
            panel.Position = UDim2.fromOffset(x, y)
        end
    end
end)

-- ─── LOCK BUTTON 🔒 ──────────────────────────────────────
local lock_btn = Instance.new("TextButton")
lock_btn.Size               = UDim2.new(0,44,0,44)
lock_btn.Position           = UDim2.new(0,8,0.5,28)
lock_btn.BackgroundColor3   = C.lock_off
lock_btn.TextColor3         = C.text
lock_btn.Text               = "🔓"
lock_btn.FontFace           = Font.new("rbxasset://fonts/families/GothamSSm.json", Enum.FontWeight.Bold)
lock_btn.TextSize            = 24
lock_btn.BorderSizePixel    = 0
lock_btn.ZIndex             = 60
lock_btn.Parent             = gui
rnd(lock_btn, 12)

make_draggable(lock_btn, nil, function(moved)
    if not moved then
        locked = not locked
        if locked then
            lock_btn.Text             = "🔒"
            lock_btn.BackgroundColor3 = C.lock_on
            panel.Visible = false
            menu_open = false
            for _, xb in pairs(x_buttons) do xb.Visible = false end
        else
            for _, xb in pairs(x_buttons) do xb.Visible = true end
            lock_btn.Text             = "🔓"
            lock_btn.BackgroundColor3 = C.lock_off
            for label in pairs(KEY_MAP) do
                send_key(KEY_MAP[label], false)
                if active_keys[label] then
                    active_keys[label].BackgroundColor3 = C.key_idle
                end
            end
        end
    end
end)
