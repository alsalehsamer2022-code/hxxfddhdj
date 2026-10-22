-- Asta | إخفاء اسم المطور
-- يخفي اسمك واسم العرض واليوزر (@...) من الواجهات على شاشتك أنت فقط
local Players = game:GetService("Players")
local TweenService = game:GetService("TweenService")
local lp = Players.LocalPlayer
local HIDDEN = "▇▇▇▇▇"
local TOAST_NAME = "AstaNameHiderToast"

local oldToast = lp.PlayerGui:FindFirstChild(TOAST_NAME)
if oldToast then oldToast:Destroy() end

-- الأسماء اللي نخفيها (اسم العرض + اليوزر)
local patterns = {}
local seen = {}
for _, n in ipairs({lp.DisplayName, lp.Name}) do
    if n and #n > 0 and not seen[n:lower()] then
        seen[n:lower()] = true
        local escaped = n:lower():gsub("[%^%$%(%)%%%.%[%]%*%+%-%?]", "%%%0")
        patterns[#patterns + 1] = escaped
    end
end

local function censor(obj)
    if not (obj:IsA("TextLabel") or obj:IsA("TextButton") or obj:IsA("TextBox")) then return end
    if obj:FindFirstAncestor(TOAST_NAME) then return end
    local busy = false
    local function apply()
        if busy then return end
        busy = true
        local text = obj.Text
        local changed = false
        for _, pat in ipairs(patterns) do
            local lower = text:lower()
            local out, pos = "", 1
            while true do
                local s, e = lower:find(pat, pos)
                if not s then break end
                out = out .. text:sub(pos, s - 1) .. HIDDEN
                pos = e + 1
                changed = true
            end
            if changed then
                text = out .. text:sub(pos)
            end
        end
        -- أي يوزر على شكل @xxxx
        local masked, n = text:gsub("@[%w_]+", "@" .. HIDDEN)
        if n > 0 then text = masked; changed = true end
        if changed then obj.Text = text end
        busy = false
    end
    apply()
    obj:GetPropertyChangedSignal("Text"):Connect(apply)
end

local function watch(root)
    if not root then return end
    for _, d in ipairs(root:GetDescendants()) do pcall(censor, d) end
    root.DescendantAdded:Connect(function(d) pcall(censor, d) end)
end

-- الاسم فوق الراس
local function hideOverhead(char)
    local hum = char:WaitForChild("Humanoid", 10)
    if hum then hum.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None end
end
if lp.Character then task.spawn(hideOverhead, lp.Character) end
lp.CharacterAdded:Connect(hideOverhead)

-- إشعار التفعيل
local gui = Instance.new("ScreenGui")
gui.Name = TOAST_NAME
gui.ResetOnSpawn = false
gui.IgnoreGuiInset = true
gui.DisplayOrder = 999
gui.Parent = lp.PlayerGui

local box = Instance.new("Frame")
box.AnchorPoint = Vector2.new(0.5, 0)
box.Position = UDim2.new(0.5, 0, 0, -60)
box.Size = UDim2.new(0, 320, 0, 46)
box.BackgroundColor3 = Color3.fromRGB(18, 18, 24)
box.BorderSizePixel = 0
box.Parent = gui
Instance.new("UICorner", box).CornerRadius = UDim.new(0, 10)
local stroke = Instance.new("UIStroke", box)
stroke.Color = Color3.fromRGB(0, 220, 200)
stroke.Thickness = 1.5

local label = Instance.new("TextLabel")
label.Size = UDim2.new(1, -16, 1, 0)
label.Position = UDim2.new(0, 8, 0, 0)
label.BackgroundTransparency = 1
label.Text = "تم تفعيل اخفاء اسم المطور. ASTA"
label.TextColor3 = Color3.fromRGB(255, 255, 255)
label.TextScaled = true
label.Font = Enum.Font.GothamBold
label.Parent = box
Instance.new("UITextSizeConstraint", label).MaxTextSize = 18

TweenService:Create(box, TweenInfo.new(0.4, Enum.EasingStyle.Back), {Position = UDim2.new(0.5, 0, 0, 20)}):Play()
task.delay(4, function()
    TweenService:Create(box, TweenInfo.new(0.4), {Position = UDim2.new(0.5, 0, 0, -60)}):Play()
    task.wait(0.5)
    gui:Destroy()
end)

-- الواجهات (بطاقة الملف الشخصي، كيل فيد، قائمة اللاعبين، الشات)
watch(lp.PlayerGui)
watch(workspace) -- البطاقات اللي داخل العالم (SurfaceGui / BillboardGui)
pcall(function() watch(game:GetService("CoreGui")) end)
pcall(function() if gethui then watch(gethui()) end end)
