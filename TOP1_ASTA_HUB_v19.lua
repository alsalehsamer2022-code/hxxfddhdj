do -- Key gate + language picker (runs FIRST, before anything else loads)
local CoreGui = game:GetService("CoreGui")
local HttpService = game:GetService("HttpService")
local env = (getgenv and getgenv()) or _G

local KEY_CONFIG = {
    -- روابط المهمتين (داخل السكربت نفسه)
    Discord = "https://discord.gg/hvENSHRV",
    TikTok = "https://www.tiktok.com/@faryz_55?_r=1&_t=ZS-9AnnLgFhnTa",
    TaskFile = "top1asta_tasks.txt",
    SaveFile = "top1asta_key_v2.txt",
    LangFile = "top1asta_lang.txt",
}

local function mk(class, props, parent)
    local o = Instance.new(class)
    for k, v in pairs(props or {}) do o[k] = v end
    if parent then o.Parent = parent end
    return o
end

local function readF(name)
    local ok, v = pcall(function() if isfile and isfile(name) then return readfile(name) end end)
    if ok and v then return tostring(v) end
    return nil
end
local function writeF(name, v) pcall(function() if writefile then writefile(name, v) end end) end

-- ============ Warning notice (no key) ============
local function KeyGate()
    local env = (getgenv and getgenv()) or _G
    local result = nil
    local gui = mk("ScreenGui", {Name = "Top1AstaNotice", ResetOnSpawn = false, DisplayOrder = 100, IgnoreGuiInset = true}, CoreGui)
    local frame = mk("Frame", {Size = UDim2.fromOffset(340, 210), Position = UDim2.new(0.5, -170, 0.5, -105),
        BackgroundColor3 = Color3.fromRGB(20, 20, 28), BorderSizePixel = 0, Active = true, Draggable = true}, gui)
    mk("UICorner", {CornerRadius = UDim.new(0, 14)}, frame)
    mk("UIStroke", {Color = Color3.fromRGB(255, 60, 60), Thickness = 2}, frame)
    mk("TextLabel", {BackgroundTransparency = 1, Position = UDim2.fromOffset(16, 10), Size = UDim2.new(1, -60, 0, 28),
        Text = "top 1 Asta", TextColor3 = Color3.new(1, 1, 1), Font = Enum.Font.GothamBold, TextSize = 18,
        TextXAlignment = Enum.TextXAlignment.Left}, frame)
    local x = mk("TextButton", {Text = "X", Size = UDim2.fromOffset(28, 28), Position = UDim2.new(1, -38, 0, 10),
        BackgroundColor3 = Color3.fromRGB(150, 40, 40), TextColor3 = Color3.new(1, 1, 1), Font = Enum.Font.GothamBold,
        TextSize = 14, BorderSizePixel = 0}, frame)
    mk("UICorner", {CornerRadius = UDim.new(0, 8)}, x)
    mk("TextLabel", {BackgroundTransparency = 1, Position = UDim2.fromOffset(16, 48), Size = UDim2.new(1, -32, 0, 90),
        Text = "ملاحظة: نحن لسنا مسؤولين عن الباند، استخدم السكربت بحذر كي لا تتبند",
        TextColor3 = Color3.fromRGB(255, 60, 60), Font = Enum.Font.GothamBold, TextSize = 17, TextWrapped = true}, frame)
    local ok = mk("TextButton", {Text = "موافق", Size = UDim2.new(1, -32, 0, 40), Position = UDim2.fromOffset(16, 152),
        BackgroundColor3 = Color3.fromRGB(40, 140, 80), TextColor3 = Color3.new(1, 1, 1), Font = Enum.Font.GothamBold,
        TextSize = 16, BorderSizePixel = 0}, frame)
    mk("UICorner", {CornerRadius = UDim.new(0, 10)}, ok)
    ok.MouseButton1Click:Connect(function() result = true end)
    x.MouseButton1Click:Connect(function() result = false end)
    while result == nil do task.wait(0.1) end
    gui:Destroy()
    return result
end

-- ============ Language picker ============
local function LangPicker()
    local chosen = nil
    local gui = mk("ScreenGui", {Name = "Top1AstaLang", ResetOnSpawn = false, DisplayOrder = 100, IgnoreGuiInset = true}, CoreGui)
    local frame = mk("Frame", {Size = UDim2.fromOffset(320, 190), Position = UDim2.new(0.5, -160, 0.5, -95),
        BackgroundColor3 = Color3.fromRGB(20, 20, 28), BorderSizePixel = 0, Active = true, Draggable = true}, gui)
    mk("UICorner", {CornerRadius = UDim.new(0, 14)}, frame)
    mk("UIStroke", {Color = Color3.fromRGB(120, 90, 255), Thickness = 2}, frame)
    mk("TextLabel", {BackgroundTransparency = 1, Position = UDim2.fromOffset(16, 12), Size = UDim2.new(1, -32, 0, 28),
        Text = "🌐 Choose your language • اختر لغتك", TextColor3 = Color3.new(1, 1, 1), Font = Enum.Font.GothamBold,
        TextSize = 16}, frame)
    local function langBtn(y, text, code, color)
        local b = mk("TextButton", {Text = text, Size = UDim2.new(1, -32, 0, 48), Position = UDim2.fromOffset(16, y),
            BackgroundColor3 = color, TextColor3 = Color3.new(1, 1, 1), Font = Enum.Font.GothamBold,
            TextSize = 18, BorderSizePixel = 0}, frame)
        mk("UICorner", {CornerRadius = UDim.new(0, 10)}, b)
        b.MouseButton1Click:Connect(function() chosen = code end)
    end
    langBtn(58, "العربية", "ar", Color3.fromRGB(40, 140, 80))
    langBtn(118, "English", "en", Color3.fromRGB(70, 60, 140))
    while chosen == nil do task.wait(0.1) end
    gui:Destroy()
    return chosen
end

-- ============ Translator (Arabic UI -> English) ============
local AR_EN = {
        ["حفظ"] = "Save",
        ["استرجاع"] = "Restore",
        ["top 1 Asta • حقوق استا"] = "top 1 Asta • Asta Credits",
        ["يجب عليك نسخ رابط الديسكورد والتفعيل لكي تتمكن من استخدام السكربت بالكامل!\nجميع الحقوق محفوظة لـ Asta ©"] = "You must copy the Discord link and activate to use the full script!\nAll rights reserved to Asta ©",
        ["نسخ رابط الديسكورد وتفعيل"] = "Copy Discord link & activate",
        ["تم تفعيل السكربت بنجاح، أهلاً بك!"] = "Script activated successfully, welcome!",
        ["خطأ"] = "Error",
        ["لم يتم العثور على اسم المستخدم!"] = "Username not found!",
        ["فشل جلب سكن اللاعب!"] = "Failed to fetch the player's skin!",
        ["ما قدرت أطبق السكن: "] = "Couldn't apply the skin: ",
        ["  👻 راس مخفي"] = "  👻 Headless",
        ["  🦿 رجل مخفية"] = "  🦿 Hidden leg",
        ["تغيير السكنات"] = "Skin Changer",
        ["تم تطبيق السكن بنجاح!"] = "Skin applied successfully!",
        ["تم إرجاع سكنك الأصلي!"] = "Your original skin was restored!",
        ["بدون"] = "None",
        ["شبح"] = "Ghost",
        ["حرق"] = "Burn",
        ["خالي من الوزن"] = "Weightless",
        ["بالون"] = "Balloon",
        ["قلب أسود"] = "Black Heart",
        ["تجميد"] = "Freeze",
        ["ذهب"] = "Gold",
        ["الرعد"] = "Thunder",
        ["فضة"] = "Silver",
        ["القنبلة الحمراء"] = "Red Bomb",
        ["الصوت ما تحمّل (ممكن الرقم خاص أو محذوف)"] = "Sound failed to load (the ID may be private or deleted)",
        ["دعس"] = "Stomp",
        ["جاهز"] = "Ready",
        ["جاري الدعس..."] = "Stomping...",
        ["زر الدعس على الشاشة"] = "On-screen Stomp button",
        ["الخلفية ما انبنت"] = "Background wasn't built",
        ["المنفّذ ما يدعم تحميل الصور"] = "Executor doesn't support loading images",
        ["ما قدرت أحمّل الرابط"] = "Couldn't load the link",
        ["ما قدرت أحفظ الصورة"] = "Couldn't save the image",
        ["المنفّذ ما يعرض الصورة"] = "Executor can't display the image",
        ["الخلفية"] = "Background",
        ["نسخة المكتبة ما تدعم خلفية مخصصة"] = "This library version doesn't support custom backgrounds",
        ["الرئيسية"] = "Home",
        ["أهلاً بك، "] = "Welcome, ",
        ["اسم المستخدم: @"] = "Username: @",
        ["\nالآيدي: "] = "\nID: ",
        ["معدل الإطارات"] = "FPS",
        ["نسخ رابط الديسكورد"] = "Copy Discord link",
        ["اضغط لنسخ رابط السيرفر إلى الحافظة"] = "Tap to copy the server link to the clipboard",
        ["تم النسخ بنجاح"] = "Copied successfully",
        ["رابط ديسكورد top 1 Asta في الحافظة!"] = "top 1 Asta Discord link is in your clipboard!",
        ["مميزات استا"] = "Asta Features",
        ["الاوتو"] = "Auto",
        ["تفعيل"] = "Enable",
        ["إيقاف"] = "Stop",
        ["الاوتو والاسيست"] = "Auto & Assist",
        ["عرض واجهة مصغرة تحتوي على زر تشغيل/إيقاف الاوتو"] = "Show a mini widget with an Auto on/off button",
        ["اسيست Asta top1"] = "Asta top1 Assist",
        ["يلحق الخصم ويوقف قريب منه (مطفي لين تشغله)"] = "Follows the opponent and stops near them (off until you enable it)",
        ["اوتو قراب"] = "Auto Grab",
        ["ياخذ القنبلة لما تقرب من الخصم (مطفي لين تشغله)"] = "Takes the bomb when you get close to the opponent (off until you enable it)",
        ["حركة اللاعب"] = "Player Movement",
        ["ول هوب (Wall Hop)"] = "Wall Hop",
        ["لما تكبس زر النط وانت قريب من حيط ينطك منه (ما يشتغل لحاله)"] = "When you press jump near a wall, it bounces you off it (doesn't work by itself)",
        ["تاثيرات القتل"] = "Kill Effects",
        ["تأثير القتل"] = "Kill Effect",
        ["يطلع التأثير على اللي تقتله (يبان عندك بس)"] = "Plays the effect on whoever you kill (visible to you only)",
        ["الجودات"] = "Graphics",
        ["إعدادات الرؤية والأداء"] = "Visual & Performance Settings",
        ["جودة تخفيف الاق (Anti-Lag)"] = "Anti-Lag Quality",
        ["تقليل المواد والظلال ويرفع حد الفريمات لإزالة التقطيع"] = "Reduces materials and shadows and raises the FPS cap to remove stutter",
        ["تخفيف الاق"] = "Anti-Lag",
        ["تمت إزالة التأثيرات لتنعيم اللعبة!"] = "Effects removed to smooth the game!",
        ["جودة سينمائية للماب"] = "Cinematic Map Quality",
        ["إضاءة وغروب وبلوم (تظهر عندك بس)"] = "Lighting, sunset and bloom (visible to you only)",
        ["القنبلة تلمع"] = "Glowing Bomb",
        ["القنبلة اللي بيدك تلمع أحمر/أبيض (تظهر عندك بس)"] = "The bomb in your hand glows red/white (visible to you only)",
        ["جودة سوداء"] = "Dark Quality",
        ["يخلي الماب أغمق شوي (مو سواد كامل) - تظهر عندك بس"] = "Makes the map a bit darker (not fully black) - visible to you only",
        ["كام لوك"] = "Cam Lock",
        ["الكاميرا تظل تطالع على أقرب خصم (ما تثبّت على زميلك بالفريق)"] = "Camera keeps looking at the nearest opponent (won't lock onto teammates)",
        ["قوة التثبيت"] = "Lock Strength",
        ["100 = ثابت تماماً، أقل = أنعم وأطبيعي"] = "100 = fully locked, lower = smoother and more natural",
        ["مكان التثبيت"] = "Lock Position",
        ["هيت بوكس (Hitbox)"] = "Hitbox",
        ["هيت بوكس"] = "Hitbox",
        ["يكبّر مربع الإصابة، وأول ما لاعب يدخل المدى يلمسه ويفعّل الأداة اللي بيدك من بعيد (لازم تكون ماسك القنبلة)"] = "Enlarges the hit box, and as soon as a player enters range it touches them and activates the tool in your hand from afar (you must be holding the bomb)",
        ["حجم الهيت بوكس"] = "Hitbox Size",
        ["حدد الحجم اللي تبيه"] = "Choose the size you want",
        ["المظهر والتأثيرات"] = "Look & Effects",
        ["إظهار اللاعبين"] = "Show Players",
        ["ESP اللاعبين"] = "Player ESP",
        ["يلوّن اللاعبين ويظهرهم من ورا الجدران (عندك بس)"] = "Colors players and shows them through walls (you only)",
        ["يخلي الجدران والأشياء شبه شفافة (عندك بس)"] = "Makes walls and objects semi-transparent (you only)",
        ["تأثيرات"] = "Effects",
        ["أثر ملوّن وراك وانت تمشي"] = "A colored trail behind you as you walk",
        ["دائرة تطلع تحتك لما تنط"] = "A ring appears under you when you jump",
        ["قبعة مضيئة فوق راسك (تظهر عندك بس)"] = "A glowing hat above your head (visible to you only)",
        ["يغيّر اسمك فوق شخصيتك عندك بس"] = "Changes the name above your character (you only)",
        ["الشاشة والألوان"] = "Screen & Colors",
        ["تشبّع الألوان"] = "Color Saturation",
        ["0 = عادي، أعلى = ألوان أقوى، أقل = باهتة"] = "0 = normal, higher = stronger colors, lower = faded",
        ["مجال الرؤية (FOV)"] = "Field of View (FOV)",
        ["ما عرفت نوع الغرض"] = "Couldn't identify the item type",
        ["هذا النوع ما ينلبس"] = "This type can't be worn",
        ["فشل التلبيس، جرّب غرض ثاني"] = "Failed to wear it, try another item",
        ["👕 شيرتات"] = "👕 Shirts",
        ["👖 بناطيل"] = "👖 Pants",
        ["🎽 تيشيرتات"] = "🎽 T-Shirts",
        ["الكل"] = "All",
        ["🔥 تعريق"] = "🔥 Tryhard",
        ["😎 برو"] = "😎 Pro",
        ["🖤 أسود"] = "🖤 Black",
        ["💀 ايمو"] = "💀 Emo",
        ["🧢 ستريت"] = "🧢 Street",
        ["✨ درِب"] = "✨ Drip",
        ["🥷 تكتيكال"] = "🥷 Tactical",
        ["⚔️ ساموراي"] = "⚔️ Samurai",
        ["🔥 مبيعاً"] = "🔥 Best Selling",
        ["💰 الأغلى"] = "💰 Priciest",
        ["🆕 الأحدث"] = "🆕 Newest",
        ["الكتالوج"] = "Catalog",
        ["تم تلبيس: "] = "Wore: ",
        ["فشل"] = "Failed",
        ["جاري التحميل..."] = "Loading...",
        ["ما قدرت أتصل بالكتالوج"] = "Couldn't connect to the catalog",
        ["ما فيه نتائج، جرّب ستايل أو كلمة ثانية"] = "No results, try another style or keyword",
        ["↩ إرجاع سكني"] = "↩ Restore my skin",
        ["ابحث عن شيرت أو بنطلون..."] = "Search for a shirt or pants...",
        ["المزيد"] = "More",
        ["الصق رابط الغرض أو رقمه واضغط Enter"] = "Paste the item link or ID and press Enter",
        ["الرابط غير صحيح"] = "Invalid link",
        ["تم التلبيس"] = "Worn",
        ["المنفّذ ما يدعم الاتصال بالكتالوج"] = "Executor doesn't support connecting to the catalog",
        ["اسم اللاعب"] = "Player Name",
        ["ادخل اسم المستخدم للاعب لنسخ سكنه"] = "Enter a player's username to copy their skin",
        ["اكتب هنا"] = "Type here",
        ["تطبيق السكن"] = "Apply Skin",
        ["اضغط لتطبيق السكن المدخل على شخصيتك"] = "Tap to apply the entered skin to your character",
        ["↩ إرجاع سكني الأصلي"] = "↩ Restore my original skin",
        ["يرجّع شكل شخصيتك الأصلي"] = "Restores your character's original look",
        ["📦 الكتالوج"] = "📦 Catalog",
        ["يفتح قائمة بكل أغراض وسكنات الكتالوج، اختر وتظهر عليك بس"] = "Opens a list of catalog items and skins, pick one and it shows on you only",
        ["الرجل والراس"] = "Leg & Head",
        ["الرجل (Korblox)"] = "Leg (Korblox)",
        ["تفعيل / إخفاء الرجل اليمنى باستمرار حتى بعد الموت"] = "Enable / hide the right leg permanently, even after death",
        ["الراس المخفي (Headless)"] = "Headless",
        ["تفعيل / إخفاء رأس الشخصية باستمرار حتى بعد الموت"] = "Enable / hide the character's head permanently, even after death",
        ["الدعس"] = "Stomp",
        ["تفعيل الدعس"] = "Enable Stomp",
        ["الدعس وزره ما يشتغلون إلا لما تفعّل هذا الخيار"] = "Stomp and its button only work when this option is enabled",
        ["يظهر زر تكبسه عشان يدعس 3 ثواني (تقدر تسحبه). يظهر بس لما الدعس مفعّل، وتقدر تخفيه من هنا"] = "Shows a button you press to stomp for 3 seconds (you can drag it). Only appears when Stomp is enabled, and you can hide it from here",
        ["تدعيس الموتى"] = "Stomp the Dead",
        ["أول ما لاعب يموت تروح فوقه وتنط عليه وتضغط الأداة"] = "As soon as a player dies you go over them, jump on them and press the tool",
        ["الأغاني"] = "Songs",
        ["مشغل الأغاني"] = "Song Player",
        ["(ما فيه أغاني محفوظة)"] = "(no saved songs)",
        ["يشتغل: "] = "Playing: ",
        ["ما اشتغلت: "] = "Failed: ",
        ["رقم الصوت أو رابط"] = "Sound ID or link",
        ["رقم ساوند روبلوكس أو رابط mp3/ogg مباشر"] = "Roblox sound ID or a direct mp3/ogg link",
        ["الصق هنا"] = "Paste here",
        ["إضافة وتشغيل"] = "Add & Play",
        ["يشغّل الأغنية"] = "Plays the song",
        ["اكتب رقم صوت أو رابط صحيح"] = "Enter a valid sound ID or link",
        ["إيقاف الأغنية"] = "Stop Song",
        ["تكرار (Loop)"] = "Loop",
        ["مستوى الصوت"] = "Volume",
        ["الإعدادات"] = "Settings",
        ["حفظ واسترجاع الإعدادات"] = "Save & Restore Settings",
        ["كيف تشتغل؟"] = "How does it work?",
        ["ظبّط خياراتك (الاسيست، الدعس، التأثيرات، السكن...) ثم اضغط «حفظ جميع الإعدادات». أي وقت تطلع وترجع وتشغّل السكربت ترجع إعداداتك المحفوظة لحالها تلقائياً."] = "Set up your options (assist, stomp, effects, skin...) then tap \"Save All Settings\". Whenever you leave and run the script again, your saved settings come back automatically.",
        ["المنفّذ عندك ما يدعم حفظ الملفات!"] = "Your executor doesn't support saving files!",
        ["💾 حفظ جميع الإعدادات"] = "💾 Save All Settings",
        ["يحفظ كل خياراتك الحالية (والسكن اللي لابسه)"] = "Saves all your current options (and the skin you're wearing)",
        ["تم حفظ جميع إعداداتك!"] = "All your settings were saved!",
        ["فشل حفظ الإعدادات"] = "Failed to save settings",
        ["🔄 استرجاع الإعدادات المحفوظة"] = "🔄 Restore Saved Settings",
        ["يرجّع كل خياراتك اللي حفظتها قبل"] = "Restores all the options you saved before",
        ["تم استرجاع إعداداتك المحفوظة!"] = "Your saved settings were restored!",
        ["ما فيه إعدادات محفوظة، اضغط حفظ أول"] = "No saved settings, tap Save first",
        ["إعادة الضبط (الافتراضي)"] = "Reset (Default)",
        ["يطفي كل الميزات ويرجّع الخيارات لوضعها الأصلي (ما يمسح المحفوظ)"] = "Turns off all features and resets options to default (doesn't delete saved settings)",
        ["رجعت كل الإعدادات للوضع الافتراضي"] = "All settings reset to default",
        ["🗑 حذف الإعدادات المحفوظة"] = "🗑 Delete Saved Settings",
        ["يمسح ملف الحفظ (الخيارات الحالية تبقى لين تطلع)"] = "Deletes the save file (current options stay until you leave)",
        ["تم حذف الإعدادات المحفوظة"] = "Saved settings deleted",
        ["استرجاع تلقائي عند الدخول"] = "Auto-restore on join",
        ["أول ما تشغّل السكربت ترجع إعداداتك المحفوظة لحالها"] = "Your saved settings come back as soon as you run the script",
        ["خلفية الواجهة"] = "UI Background",
        ["رابط صورة مخصصة (اختياري)"] = "Custom image link (optional)",
        ["الصق رابط صورة مباشر (png / jpg) لو تبي تغيّر الخلفية"] = "Paste a direct image link (png / jpg) to change the background",
        ["تطبيق الصورة"] = "Apply Image",
        ["اكتب الرابط أول"] = "Enter the link first",
        ["تم تطبيق الصورة!"] = "Image applied!",
        ["إرجاع الخلفية الأصلية"] = "Restore Original Background",
        ["الحقوق"] = "Credits",
        ["طاقم العمل"] = "Team",
        ["تم البرمجة والتطوير بواسطة:\n★ Asta"] = "Programmed and developed by:\n★ Asta",
        ["تم استرجاع إعداداتك المحفوظة تلقائياً"] = "Your saved settings were restored automatically",
}
local function installTranslator()
    local keys = {}
    for k in pairs(AR_EN) do keys[#keys + 1] = k end
    table.sort(keys, function(a, b) return #a > #b end)
    local cache = {}
    local function tr(s)
        if type(s) ~= "string" or not s:find("[\216-\219]") then return s end
        local c = cache[s]
        if c then return c end
        local out = s
        for _, k in ipairs(keys) do
            local v = AR_EN[k]
            local i, j = out:find(k, 1, true)
            while i do
                out = out:sub(1, i - 1) .. v .. out:sub(j + 1)
                i, j = out:find(k, i + #v, true)
            end
        end
        out = out:gsub("^(.-) | %1$", "%1")
        cache[s] = out
        return out
    end
    local function hookObj(o)
        if o:IsA("TextLabel") or o:IsA("TextButton") or o:IsA("TextBox") then
            local function fix()
                local t = o.Text
                local n = tr(t)
                if n ~= t then o.Text = n end
                if o:IsA("TextBox") then
                    local p = o.PlaceholderText
                    local np = tr(p)
                    if np ~= p then o.PlaceholderText = np end
                end
            end
            pcall(fix)
            o:GetPropertyChangedSignal("Text"):Connect(function() pcall(fix) end)
            if o:IsA("TextBox") then o:GetPropertyChangedSignal("PlaceholderText"):Connect(function() pcall(fix) end) end
        end
    end
    local function hookRoot(root)
        for _, d in ipairs(root:GetDescendants()) do hookObj(d) end
        root.DescendantAdded:Connect(function(d) task.defer(hookObj, d) end)
    end
    local function watch(container)
        container.ChildAdded:Connect(function(child)
            if child:IsA("ScreenGui") then hookRoot(child) end
        end)
    end
    watch(CoreGui)
    pcall(function()
        local h = gethui and gethui()
        if h and h ~= CoreGui then watch(h) end
    end)
    pcall(function()
        local pg = game:GetService("Players").LocalPlayer:FindFirstChild("PlayerGui")
        if pg then watch(pg) end
    end)
end

if not KeyGate() then return end
-- اختيار اللغة يطلع كل مرة (ما ينحفظ)
local lang = LangPicker()
env.Top1AstaLang = lang
if lang == "en" then installTranslator() end
end

local function FetchWindUI()
    local urls = {
        "https://raw.githubusercontent.com/Footagesus/WindUI/main/dist/main.lua",
        "https://tree-hub.fyle.dev/windui",
        "https://github.com/Footagesus/WindUI/releases/latest/download/main.lua"
    }
    
    for _, url in ipairs(urls) do
        local success, result = pcall(function()
            return game:HttpGet(url)
        end)
        if success and result and #result > 100 then
            local loadSuccess, library = pcall(loadstring(result))
            if loadSuccess and library then
                return library
            end
        end
    end
    return nil
end

local WindUI = FetchWindUI()

if not WindUI then
    warn("[top 1 Asta Error]: متعذر تحميل مكتبة WindUI!")
    return
end

local RunService = game:GetService("RunService")
local Players = game:GetService("Players")
local TweenService = game:GetService("TweenService")
local Lighting = game:GetService("Lighting")
local Debris = game:GetService("Debris")
local CoreGui = game:GetService("CoreGui")
local LocalPlayer = Players.LocalPlayer
local HttpService = game:GetService("HttpService")

-- دالة مختصرة لإنشاء عناصر الواجهة (تُستخدم في المتجر)
local function mk(class, props, parent)
    local o = Instance.new(class)
    for k, v in pairs(props or {}) do o[k] = v end
    if parent then o.Parent = parent end
    return o
end


-- ================= نظام حفظ واسترجاع الإعدادات =================
-- كل ميزة تتسجل هنا (المفتاح، القيمة الافتراضية، دالة التطبيق).
-- "حفظ" يكتب القيم في ملف، و"استرجاع" يقرأها ويطبقها (وتنطبق تلقائياً عند الدخول).
local SETTINGS_FILE = "Top1Asta_settings.json"
local Settings = {items = {}, order = {}}

function Settings.register(key, default, apply, kind)
    Settings.items[key] = {value = default, default = default, apply = apply, kind = kind}
    table.insert(Settings.order, key)
end

-- تُستدعى من أزرار الواجهة عند ما المستخدم يغيّر شي
function Settings.set(key, v)
    local it = Settings.items[key]
    if not it then return end
    it.value = v
    if it.apply then pcall(it.apply, v) end
end

-- يحدّث شكل العنصر بالواجهة (التوقل/السلايدر/القائمة) من غير ما يعيد تشغيله
function Settings.setUI(key, v)
    local it = Settings.items[key]
    if not it or not it.ui then return end
    pcall(function()
        if it.kind == "toggle" then
            it.ui:Set(v, false)
        elseif it.kind == "slider" then
            it.ui:Set(v)
        elseif it.kind == "dropdown" then
            it.ui:Select(v)
        end
    end)
end

function Settings.supported()
    return (writefile and readfile and isfile) and true or false
end

function Settings.read()
    local ok, data = pcall(function()
        if isfile and isfile(SETTINGS_FILE) then
            return HttpService:JSONDecode(readfile(SETTINGS_FILE))
        end
        return nil
    end)
    if ok and type(data) == "table" then return data end
    return nil
end

function Settings.save()
    local data = {}
    for _, k in ipairs(Settings.order) do data[k] = Settings.items[k].value end
    if Settings.getSkin then data._skin = Settings.getSkin() end
    local ok, err = pcall(function()
        writefile(SETTINGS_FILE, HttpService:JSONEncode(data))
    end)
    return ok, err
end

function Settings.restore(data)
    data = data or Settings.read()
    if not data then return false end
    for _, k in ipairs(Settings.order) do
        local v = data[k]
        if v ~= nil then
            local it = Settings.items[k]
            it.value = v
            if it.apply then pcall(it.apply, v) end
            Settings.setUI(k, v)
        end
    end
    if data._skin and Settings.applySkin then Settings.applySkin(data._skin) end
    return true
end

function Settings.reset()
    for _, k in ipairs(Settings.order) do
        local it = Settings.items[k]
        it.value = it.default
        if it.apply then pcall(it.apply, it.default) end
        Settings.setUI(k, it.default)
    end
    if Settings.clearSkin then Settings.clearSkin() end
end

function Settings.delete()
    local ok = pcall(function()
        if isfile and isfile(SETTINGS_FILE) then delfile(SETTINGS_FILE) end
    end)
    return ok
end

-- ينشئ توقل مربوط بالحفظ
local function RegToggle(tab, key, title, desc, default, apply)
    Settings.register(key, default, apply, "toggle")
    local el = tab:Toggle({
        Title = title,
        Desc = desc,
        Value = default,
        Callback = function(v) Settings.set(key, v and true or false) end
    })
    Settings.items[key].ui = el
    return el
end

local AuthGui = Instance.new("ScreenGui")
AuthGui.Name = "Top1AstaAuthGui"
AuthGui.Parent = CoreGui
AuthGui.ResetOnSpawn = false
AuthGui.IgnoreGuiInset = true

local AuthOverlay = Instance.new("Frame", AuthGui)
AuthOverlay.Size = UDim2.new(1, 0, 1, 0)
AuthOverlay.BackgroundColor3 = Color3.fromRGB(10, 10, 15)
AuthOverlay.BackgroundTransparency = 0.15

local AuthFrame = Instance.new("Frame", AuthOverlay)
AuthFrame.Size = UDim2.fromOffset(400, 220)
AuthFrame.Position = UDim2.new(0.5, -200, 0.5, -110)
AuthFrame.BackgroundColor3 = Color3.fromRGB(18, 18, 25)

local AuthCorner = Instance.new("UICorner", AuthFrame)
AuthCorner.CornerRadius = UDim.new(0, 14)

local AuthTitle = Instance.new("TextLabel", AuthFrame)
AuthTitle.Size = UDim2.new(1, 0, 0, 50)
AuthTitle.Text = "top 1 Asta • حقوق استا"
AuthTitle.TextColor3 = Color3.fromRGB(0, 255, 127)
AuthTitle.BackgroundTransparency = 1
AuthTitle.Font = Enum.Font.GothamBold
AuthTitle.TextSize = 20

local AuthDesc = Instance.new("TextLabel", AuthFrame)
AuthDesc.Size = UDim2.new(0.9, 0, 0, 66)
AuthDesc.Position = UDim2.new(0.05, 0, 0.26, 0)
AuthDesc.Text = "يجب عليك نسخ رابط الديسكورد والتفعيل لكي تتمكن من استخدام السكربت بالكامل!\nجميع الحقوق محفوظة لـ Asta ©"
AuthDesc.TextColor3 = Color3.fromRGB(210, 210, 210)
AuthDesc.BackgroundTransparency = 1
AuthDesc.Font = Enum.Font.Gotham
AuthDesc.TextSize = 14
AuthDesc.TextWrapped = true

local DiscordBtn = Instance.new("TextButton", AuthFrame)
DiscordBtn.Size = UDim2.new(0.85, 0, 0, 42)
DiscordBtn.Position = UDim2.new(0.075, 0, 0.65, 0)
DiscordBtn.Text = "نسخ رابط الديسكورد وتفعيل"
DiscordBtn.BackgroundColor3 = Color3.fromRGB(114, 137, 218)
DiscordBtn.TextColor3 = Color3.fromRGB(255, 255, 255)
DiscordBtn.Font = Enum.Font.GothamBold
DiscordBtn.TextSize = 15

local DBtnCorner = Instance.new("UICorner", DiscordBtn)
DBtnCorner.CornerRadius = UDim.new(0, 8)

local Window = nil

-- عنوان بألوان متغيرة (كل حرف بلون)
function RainbowText(text, offset)
    local out = {}
    local i = 0
    for _, ch in utf8.codes(text) do
        i = i + 1
        local c = Color3.fromHSV((offset + i * 0.07) % 1, 0.85, 1)
        out[#out + 1] = string.format('<font color="#%s">%s</font>', c:ToHex(), utf8.char(ch))
    end
    return table.concat(out)
end

DiscordBtn.MouseButton1Click:Connect(function()
    setclipboard("https://discord.gg/hvENSHRV")
    AuthGui:Destroy()
    
    WindUI:Notify({
        Title = "Asta",
        Content = "تم تفعيل السكربت بنجاح، أهلاً بك!",
        Duration = 4
    })
    
    if Window then
        Window:SelectTab(1)
    end
end)

local lastUsernameSkin = nil
local lastSkinOpts = nil
local applyToken = 0
local idCache = {}

local function resolveUserId(name)
    local key = string.lower(name)
    if idCache[key] then return idCache[key] end
    for _ = 1, 2 do
        local ok, id = pcall(Players.GetUserIdFromNameAsync, Players, name)
        if ok and type(id) == "number" then
            idCache[key] = id
            return id
        end
        task.wait(0.6)
    end
    return nil
end

-- طريقة بديلة: ننسخ ملابس واكسسوارات الحساب يدوياً (تشتغل لما ApplyDescription ما تنفع)
local function applyViaAppearance(char, hum, userId)
    local ok, model = pcall(Players.GetCharacterAppearanceAsync, Players, userId)
    if not ok or not model then return false, tostring(model) end
    for _, c in ipairs(char:GetChildren()) do
        if c:IsA("Accessory") or c:IsA("Hat") or c:IsA("BodyColors")
        or c:IsA("CharacterMesh") or c:IsA("Shirt") or c:IsA("Pants")
        or c:IsA("ShirtGraphic") then
            c:Destroy()
        end
    end
    for _, c in ipairs(model:GetChildren()) do
        if c:IsA("Accessory") or c:IsA("Hat") then
            pcall(function() hum:AddAccessory(c) end)
        elseif c:IsA("Shirt") or c:IsA("Pants") or c:IsA("ShirtGraphic")
            or c:IsA("BodyColors") or c:IsA("CharacterMesh") then
            c.Parent = char
        end
    end
    pcall(function()
        local head, mh = char:FindFirstChild("Head"), model:FindFirstChild("Head")
        local face = mh and mh:FindFirstChildOfClass("Decal")
        if head and face then
            local old = head:FindFirstChildOfClass("Decal")
            if old then old:Destroy() end
            face.Parent = head
        end
    end)
    return true
end

-- ================= إخفاء الراس والرجل للسكن المطبّق (يظهر عندك بس) =================
local HEADLESS_HEAD, KORBLOX_LEG = 134082579, 139607718
local skinFx = {head = false, leg = false, conn = nil}

local Wear = {fields = {}, acc = {}, cache = {}}

local function manualOn(key)
    local it = Settings.items[key]
    return it and it.value and true or false
end

local function isRightLegPart(p)
    local n = p.Name
    if n == "Right Leg" or n == "RightUpperLeg" or n == "RightLowerLeg" or n == "RightFoot" then return true end
    -- أي جزء تابع للرجل اليمنى (مو اكسسوار)
    return n:find("^Right") ~= nil and (n:find("Leg") ~= nil or n:find("Foot") ~= nil) and not p:FindFirstAncestorWhichIsA("Accessory")
end

local function fxHide(char)
    if skinFx.head then
        local head = char:FindFirstChild("Head")
        if head and head:IsA("BasePart") then
            if head.Transparency ~= 1 then head.Transparency = 1 end
            for _, d in ipairs(head:GetChildren()) do
                if d:IsA("Decal") and d.Transparency ~= 1 then d.Transparency = 1 end
            end
        end
    end
    if skinFx.leg then
        for _, p in ipairs(char:GetDescendants()) do
            if p:IsA("BasePart") and p.Transparency ~= 1 and isRightLegPart(p) then
                p.Transparency = 1
            end
        end
    end
end

local function fxShow(char, showHead, showLeg)
    if showHead and not manualOn("headless") then
        local head = char:FindFirstChild("Head")
        if head and head:IsA("BasePart") then
            head.Transparency = 0
            for _, d in ipairs(head:GetChildren()) do
                if d:IsA("Decal") then d.Transparency = 0 end
            end
        end
    end
    if showLeg and not manualOn("korblox") then
        for _, p in ipairs(char:GetDescendants()) do
            if p:IsA("BasePart") and isRightLegPart(p) then p.Transparency = 0 end
        end
    end
end

local function setSkinFx(head, leg)
    head, leg = head and true or false, leg and true or false
    local wasHead, wasLeg = skinFx.head, skinFx.leg
    skinFx.head, skinFx.leg = head, leg
    if skinFx.conn then skinFx.conn:Disconnect() skinFx.conn = nil end
    local char = LocalPlayer.Character
    if char then pcall(fxShow, char, wasHead and not head, wasLeg and not leg) end
    if head or leg then
        skinFx.conn = RunService.RenderStepped:Connect(function()
            local c = LocalPlayer.Character
            if c then pcall(fxHide, c) end
        end)
    end
end

-- يلبّس شخصيتك سكن حساب معيّن (opts.userId يختصر البحث، opts.noFx يعني ارجاع السكن الأصلي)
-- الراس المخفي والرجل المقطوعة تنكشف من سكن الحساب الحقيقي، والاثنين ينخفون عندك بس
local function apply_avatar(username, isInitialApply, opts)
    applyToken = applyToken + 1
    local myToken = applyToken

    task.spawn(function()
        local char = LocalPlayer.Character or LocalPlayer.CharacterAdded:Wait()
        local hum = char:WaitForChild("Humanoid", 10)
        if not hum then return end

        local userId = opts and opts.userId
        if not userId then
            for _, p in ipairs(Players:GetPlayers()) do
                if p.Name:lower() == username:lower() then
                    userId = p.UserId
                    break
                end
            end
        end
        if not userId then userId = resolveUserId(username) end
        if not userId then
            if isInitialApply then
                WindUI:Notify({ Title = "خطأ", Content = "لم يتم العثور على اسم المستخدم!", Duration = 3 })
            end
            return
        end

        local desc
        for _ = 1, 2 do
            local ok, d = pcall(Players.GetHumanoidDescriptionFromUserId, Players, userId)
            if ok and d then
                desc = d
                break
            end
            task.wait(0.6)
        end
        if not desc then
            if isInitialApply then
                WindUI:Notify({ Title = "خطأ", Content = "فشل جلب سكن اللاعب!", Duration = 3 })
            end
            return
        end

        if myToken ~= applyToken then return end

        char = LocalPlayer.Character
        hum = char and char:FindFirstChildOfClass("Humanoid")
        if not hum then return end

        -- نقرأ من السكن الحقيقي: هل فيه راس مخفي؟ هل فيه رجل كوربلوكس؟
        local isHeadless = (desc.Head == HEADLESS_HEAD)
        local isKorblox = (desc.RightLeg == KORBLOX_LEG)
        -- الكوربلوكس ما نلبسه (تطلع مقطوعة)، نلبس رجل عادية وننخفيها
        if isKorblox then pcall(function() desc.RightLeg = 0 end) end

        local applied, err = pcall(function() hum:ApplyDescription(desc) end)
        if not applied then
            applied, err = pcall(function() hum:ApplyDescriptionClientServer(desc) end)
        end
        if not applied then
            applied, err = applyViaAppearance(char, hum, userId)
        end
        if not applied then
            if isInitialApply then
                WindUI:Notify({ Title = "خطأ", Content = "ما قدرت أطبق السكن: " .. tostring(err), Duration = 5 })
            end
            return
        end

        pcall(function()
            local bc = char:FindFirstChildOfClass("BodyColors") or Instance.new("BodyColors")
            bc.Parent = char
            bc.HeadColor3 = desc.HeadColor
            bc.TorsoColor3 = desc.TorsoColor
            bc.LeftArmColor3 = desc.LeftArmColor
            bc.RightArmColor3 = desc.RightArmColor
            bc.LeftLegColor3 = desc.LeftLegColor
            bc.RightLegColor3 = desc.RightLegColor
        end)

        if opts and opts.noFx then
            setSkinFx(false, false)
        else
            setSkinFx(isHeadless, isKorblox)
            if next(Wear.fields) or next(Wear.acc) then Wear.apply() end
        end

        if isInitialApply then
            local fxMsg = ""
            if not (opts and opts.noFx) then
                if isHeadless then fxMsg = fxMsg .. "  👻 راس مخفي" end
                if isKorblox then fxMsg = fxMsg .. "  🦿 رجل مخفية" end
            end
            WindUI:Notify({ Title = "تغيير السكنات", Content = ((opts and opts.msg) or "تم تطبيق السكن بنجاح!") .. fxMsg, Duration = 3 })
        end
    end)
end

LocalPlayer.CharacterAdded:Connect(function(char)
    if lastUsernameSkin then
        char:WaitForChild("Humanoid", 10)
        task.wait(0.65)
        apply_avatar(lastUsernameSkin, false, lastSkinOpts)
    elseif next(Wear.fields) or next(Wear.acc) then
        char:WaitForChild("Humanoid", 10)
        task.wait(0.65)
        Wear.apply()
    end
end)

local function startAvatarChange(username)
    if username and username ~= "" then
        lastUsernameSkin = username
        lastSkinOpts = nil
        apply_avatar(username, true)
    end
end

-- يرجّع سكنك الأصلي
local function resetAvatar()
    lastUsernameSkin = nil
    lastSkinOpts = nil
    for k in pairs(Wear.fields) do Wear.fields[k] = nil end
    for k in pairs(Wear.acc) do Wear.acc[k] = nil end
    apply_avatar(LocalPlayer.Name, true, {userId = LocalPlayer.UserId, noFx = true, msg = "تم إرجاع سكنك الأصلي!"})
end

-- ربط السكن بنظام حفظ الإعدادات
Settings.getSkin = function()
    if not lastUsernameSkin then return nil end
    return {username = lastUsernameSkin, userId = lastSkinOpts and lastSkinOpts.userId or nil}
end
Settings.applySkin = function(s)
    if type(s) ~= "table" or type(s.username) ~= "string" or s.username == "" then return end
    lastUsernameSkin = s.username
    lastSkinOpts = type(s.userId) == "number" and {userId = s.userId} or nil
    apply_avatar(s.username, false, lastSkinOpts)
end
Settings.clearSkin = function()
    if lastUsernameSkin then resetAvatar() end
end

-- ================= متجر السكنات =================
-- نافذة فيها أقسام وصور للسكنات، تضغط على السكن ويلبس عليك مباشرة.
-- الحسابات تنفحص بالخلفية (تظهر السكنات واحد واحد) والنتائج تنحفظ بملف عشان المرة الجاية أسرع.
-- ================= الملبس: أغراض الكتالوج الحقيقي (تظهر عندك بس) =================

function Wear.applyDesc()
    local char = LocalPlayer.Character
    local hum = char and char:FindFirstChildOfClass("Humanoid")
    if not hum then return false end
    local ok, d = pcall(function() return hum:GetAppliedDescription() end)
    if not ok or not d then return false end
    for k, v in pairs(Wear.fields) do pcall(function() d[k] = v end) end
    local headless = skinFx.head or Wear.fields.Head == HEADLESS_HEAD or d.Head == HEADLESS_HEAD
    local korblox = skinFx.leg or Wear.fields.RightLeg == KORBLOX_LEG or d.RightLeg == KORBLOX_LEG
    if d.RightLeg == KORBLOX_LEG then d.RightLeg = 0 end -- ما نلبس المقطوعة، ننخفيها
    if next(Wear.acc) then
        pcall(function()
            local list = d:GetAccessories(true)
            for _, a in pairs(Wear.acc) do
                local dup = false
                for _, x in ipairs(list) do
                    if x.AssetId == a.id then dup = true break end
                end
                if not dup then
                    table.insert(list, {AssetId = a.id, AccessoryType = Enum.AccessoryType[a.kind], IsLayered = a.layered and true or false})
                end
            end
            d:SetAccessories(list, true)
        end)
    end
    local applied = pcall(function() hum:ApplyDescription(d) end)
    if not applied then applied = pcall(function() hum:ApplyDescriptionClientServer(d) end) end
    setSkinFx(headless, korblox)
    return applied
end

-- طريقة بديلة تشتغل عندك مباشرة: نحمّل الغرض ونحطه على شخصيتك (ما تحتاج سيرفر)
function Wear.manualApply()
    local char = LocalPlayer.Character
    local hum = char and char:FindFirstChildOfClass("Humanoid")
    if not hum then return false end
    local function fetch(id)
        local c = Wear.cache[id]
        if c == nil then
            local ok, objs = pcall(function() return game:GetObjects("rbxassetid://" .. id) end)
            c = (ok and type(objs) == "table" and objs[1]) or false
            Wear.cache[id] = c
        end
        return c or nil
    end
    local n = 0
    for id, a in pairs(Wear.acc) do
        local obj = fetch(id)
        if obj then
            local acc = obj:IsA("Accessory") and obj or obj:FindFirstChildWhichIsA("Accessory", true)
            if acc then
                for _, c in ipairs(char:GetChildren()) do
                    if c:GetAttribute("AstaWear") == id then c:Destroy() end
                end
                local cl = acc:Clone()
                cl:SetAttribute("AstaWear", id)
                if pcall(function() hum:AddAccessory(cl) end) then n = n + 1 end
            end
        end
    end
    for field, id in pairs(Wear.fields) do
        local obj = fetch(id)
        if obj then
            local cls = (field == "Shirt" and "Shirt") or (field == "Pants" and "Pants") or (field == "GraphicTShirt" and "ShirtGraphic")
            if cls then
                for _, c in ipairs(char:GetChildren()) do
                    if c:IsA(cls) then c:Destroy() end
                end
                local cl = obj:Clone()
                cl.Parent = char
                n = n + 1
            elseif field == "Face" then
                local head = char:FindFirstChild("Head")
                local decal = obj:IsA("Decal") and obj or obj:FindFirstChildWhichIsA("Decal", true)
                if head and decal then
                    local old = head:FindFirstChildOfClass("Decal")
                    if old then old:Destroy() end
                    local cl = decal:Clone()
                    cl.Name = "face"
                    cl.Parent = head
                    n = n + 1
                end
            end
        end
    end
    return n > 0
end

function Wear.apply()
    if Wear.applyDesc() then return true end
    return Wear.manualApply()
end


local ActiveEffects = {
    RedBombFX = false
}

local function PlayRedBombCinematicFX(targetChar)
    if not targetChar then return end
    local hrp = targetChar:FindFirstChild("HumanoidRootPart") or targetChar:FindFirstChild("Torso") or targetChar:FindFirstChild("UpperTorso")
    if not hrp then return end

    pcall(function()
        local pos = hrp.Position
        local BOMB_TIME = 1.15

        local function ghostPart(data)
            local p = Instance.new("Part")
            for k, v in pairs(data) do p[k] = v end
            p.Anchored = false
            p.CanCollide = false
            p.Parent = workspace
            return p
        end

        local function sphere(pPos, color, size0, size1, t)
            local s = ghostPart({Shape = Enum.PartType.Ball, Size = Vector3.one * size0, Color = color,
                Material = Enum.Material.Neon, Transparency = 0, CFrame = CFrame.new(pPos)})
            s.Anchored = true
            TweenService:Create(s, TweenInfo.new(t, Enum.EasingStyle.Quint, Enum.EasingDirection.Out),
                {Size = Vector3.one * size1, Transparency = 1}):Play()
            Debris:AddItem(s, t + 0.2)
            return s
        end

        local function boomSound(parent, id, speed, vol, delay)
            task.delay(delay or 0, function()
                local s = Instance.new("Sound")
                s.SoundId = id
                s.Volume = vol
                s.PlaybackSpeed = speed
                s.RollOffMaxDistance = 300
                s.RollOffMinDistance = 30
                s.Parent = parent
                s:Play()
                Debris:AddItem(s, 8)
            end)
        end

        local RED, WHITE = Color3.fromRGB(255, 25, 25), Color3.fromRGB(255, 255, 255)
        local bomb = ghostPart({Shape = Enum.PartType.Ball, Size = Vector3.one * 2.1, Color = RED,
            Material = Enum.Material.Neon, CFrame = hrp.CFrame + Vector3.new(0, 0.5, 0)})
        
        local weld = Instance.new("WeldConstraint")
        weld.Part0 = bomb
        weld.Part1 = hrp
        weld.Parent = bomb

        local band = ghostPart({Shape = Enum.PartType.Cylinder, Size = Vector3.new(0.45, 2.16, 2.16), Color = WHITE,
            Material = Enum.Material.Neon, CFrame = bomb.CFrame * CFrame.Angles(0, 0, math.pi / 2)})
        local bandWeld = Instance.new("WeldConstraint")
        bandWeld.Part0 = band
        bandWeld.Part1 = hrp
        bandWeld.Parent = band

        local eye = ghostPart({Shape = Enum.PartType.Ball, Size = Vector3.one * 0.8, Color = WHITE,
            Material = Enum.Material.Neon, CFrame = bomb.CFrame + Vector3.new(0, 1.1, 0)})
        local eyeWeld = Instance.new("WeldConstraint")
        eyeWeld.Part0 = eye
        eyeWeld.Part1 = hrp
        eyeWeld.Parent = eye

        local glow = Instance.new("PointLight", bomb)
        glow.Color = RED
        glow.Range = 18
        glow.Brightness = 8

        local beep = Instance.new("Sound")
        beep.SoundId = "rbxasset://sounds/electronicpingshort.wav"
        beep.Volume = 2
        beep.RollOffMaxDistance = 120
        beep.Parent = bomb

        local phase, lastOn = 0, false
        local startTime = os.clock()

        local conn
        conn = RunService.Heartbeat:Connect(function(dt)
            local elapsed = os.clock() - startTime
            if elapsed >= BOMB_TIME then
                conn:Disconnect()
                return
            end
            local a = elapsed / BOMB_TIME
            phase = phase + dt * (9 + a * 34)
            local on = math.sin(phase) > 0
            bomb.Color = on and RED or WHITE
            band.Color = on and WHITE or RED
            eye.Color = on and WHITE or RED
            glow.Color = on and RED or WHITE
            glow.Brightness = 6 + a * 12
            if on and not lastOn then
                beep.PlaybackSpeed = 0.9 + a * 1.2
                beep:Play()
            end
            lastOn = on
        end)

        task.delay(BOMB_TIME, function()
            local currentPos = bomb.Position
            if bomb then bomb:Destroy() end
            if band then band:Destroy() end
            if eye then eye:Destroy() end

            local ep = Instance.new("Part")
            ep.Size = Vector3.one
            ep.Transparency = 1
            ep.Anchored = true
            ep.CanCollide = false
            ep.CFrame = CFrame.new(currentPos)
            ep.Parent = workspace
            Debris:AddItem(ep, 8)

            boomSound(ep, "rbxasset://sounds/impact_explosion_03.mp3", 1.0, 4.5, 0)
            boomSound(ep, "rbxasset://sounds/impact_explosion_03.mp3", 0.55, 4, 0.08)

            sphere(currentPos, Color3.fromRGB(255, 255, 255), 4, 32, 0.22)
            sphere(currentPos, Color3.fromRGB(255, 45, 45), 3, 26, 0.55)
            sphere(currentPos, Color3.fromRGB(190, 10, 10), 2, 18, 0.75)

            local core = Instance.new("Part")
            core.Shape = Enum.PartType.Ball
            core.Size = Vector3.one * 2
            core.Color = Color3.fromRGB(18, 14, 12)
            core.Material = Enum.Material.SmoothPlastic
            core.Transparency = 0.1
            core.Anchored = true
            core.CanCollide = false
            core.CFrame = CFrame.new(currentPos)
            core.Parent = workspace
            TweenService:Create(core, TweenInfo.new(1.5, Enum.EasingStyle.Quad, Enum.EasingDirection.Out),
                {Size = Vector3.one * 15, Transparency = 1}):Play()
            Debris:AddItem(core, 1.7)

            local lt = Instance.new("PointLight", ep)
            lt.Color = Color3.fromRGB(255, 70, 70)
            lt.Range = 60
            lt.Brightness = 25
            TweenService:Create(lt, TweenInfo.new(1.1, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {Brightness = 0}):Play()
        end)
    end)
end

local function TriggerEffectForClosestDeadPlayer(deadChar)
    if not ActiveEffects.RedBombFX then return end
    local myChar = LocalPlayer.Character
    if not myChar then return end
    local myRoot = myChar:FindFirstChild("HumanoidRootPart")
    if not myRoot then return end

    local closestChar = nil
    local shortestDist = math.huge

    for _, p in ipairs(Players:GetPlayers()) do
        if p ~= LocalPlayer and p.Character then
            local hum = p.Character:FindFirstChildOfClass("Humanoid")
            local targetRoot = p.Character:FindFirstChild("HumanoidRootPart")
            if hum and targetRoot and hum.Health <= 0 then
                local dist = (myRoot.Position - targetRoot.Position).Magnitude
                if dist < shortestDist then
                    shortestDist = dist
                    closestChar = p.Character
                end
            end
        end
    end

    if closestChar == deadChar and shortestDist <= 30 then
        PlayRedBombCinematicFX(deadChar)
    end
end

local function CheckAndHookPlayer(otherPlayer)
    if otherPlayer == LocalPlayer then return end
    
    local function HookChar(char)
        if not char then return end
        local hum = char:WaitForChild("Humanoid", 5)
        if not hum then return end
        
        local triggered = false
        local function onDied()
            if triggered then return end
            triggered = true
            TriggerEffectForClosestDeadPlayer(char)
        end

        hum.Died:Connect(onDied)
        hum.HealthChanged:Connect(function(health)
            if health <= 0 then
                onDied()
            end
        end)
    end

    if otherPlayer.Character then HookChar(otherPlayer.Character) end
    otherPlayer.CharacterAdded:Connect(HookChar)
end

for _, p in ipairs(Players:GetPlayers()) do CheckAndHookPlayer(p) end
Players.PlayerAdded:Connect(CheckAndHookPlayer)

-- ================= ميزات إضافية (دعس / تأثيرات القتل / جودة / أغاني) =================
local AstaX = {}
do
    local lp = LocalPlayer
    local closed = false
    local conns = {}
    local stompToggleObj = nil
    local autoClick, clickCPS, lastClick = false, 8, 0

    local function new(class, props, parent)
        local o = Instance.new(class)
        for k, v in pairs(props or {}) do o[k] = v end
        if parent then o.Parent = parent end
        return o
    end

    local gui = Instance.new("ScreenGui")
    gui.Name = "Top1AstaFX"
    gui.ResetOnSpawn = false
    gui.IgnoreGuiInset = true
    gui.DisplayOrder = 5
    pcall(function() gui.Parent = CoreGui end)
    if not gui.Parent then gui.Parent = lp:WaitForChild("PlayerGui") end

    local function getChar(p)
        local c = p.Character
        return c, c and c:FindFirstChildOfClass("Humanoid"), c and c:FindFirstChild("HumanoidRootPart")
    end

    local function isTeammate(p)
        local myTeam = lp.Team
        if myTeam and p.Team == myTeam then return true end
        if lp.Neutral == false and p.Neutral == false and p.TeamColor == lp.TeamColor then
            return true
        end
        return false
    end

    -- ===== الدعس (3 ثواني) =====
local STOMP_BURST_DURATION = 3
local STOMP_MOVE_DISTANCE = 2.5
local STOMP_MOVE_INTERVAL = 0.07
local stompBurstRunning = false
local stompBurstToken = 0
local stompEnabled = false      -- الدعس ما يشتغل إلا لما المستخدم يفعّله

local function startStompBurst()
    if closed or not stompEnabled or stompBurstRunning then return end

    stompBurstToken = stompBurstToken + 1
    local myToken = stompBurstToken
    stompBurstRunning = true

    task.spawn(function()
        local started = os.clock()
        local endT = started + STOMP_BURST_DURATION

        while not closed
            and myToken == stompBurstToken
            and stompBurstRunning
            and os.clock() < endT do

            local char = lp.Character
            local hum = char and char:FindFirstChildOfClass("Humanoid")
            local hrp = char and char:FindFirstChild("HumanoidRootPart")

            if hum and hrp and hum.Health > 0 then
                -- خطوة للأمام
                local fwd = hrp.CFrame.LookVector
                hum:MoveTo(hrp.Position + fwd * STOMP_MOVE_DISTANCE)
                task.wait(STOMP_MOVE_INTERVAL)

                -- خطوة للخلف
                local char2 = lp.Character
                local hum2 = char2 and char2:FindFirstChildOfClass("Humanoid")
                local hrp2 = char2 and char2:FindFirstChild("HumanoidRootPart")

                if hum2 and hrp2 and hum2.Health > 0
                    and not closed
                    and myToken == stompBurstToken then
                    local fwd2 = hrp2.CFrame.LookVector
                    hum2:MoveTo(hrp2.Position - fwd2 * STOMP_MOVE_DISTANCE)
                end

                task.wait(STOMP_MOVE_INTERVAL)
            else
                task.wait(STOMP_MOVE_INTERVAL)
            end
        end

        -- إيقاف الدعس فقط؛ لا نغير WalkSpeed ولا Anchored ولا PlatformStand
        -- ولا نرسل أي مفاتيح للكيبورد، لذلك التحكم الطبيعي يبقى مباشر.
        stompBurstRunning = false

        pcall(function()
            if stompToggleObj then stompToggleObj.render() end
        end)
    end)
end

    -- ===== تدعيس الموتى =====
local STOMP = {busy = false, list = {}, alive = {}, range = 90, life = 5}
STOMP.click = function(tool)
    pcall(function() tool:Activate() end)
    local done = false
    if mouse1click then done = pcall(mouse1click) end
    if not done then
        pcall(function()
            local vim = game:GetService("VirtualInputManager")
            local c = workspace.CurrentCamera.ViewportSize
            vim:SendMouseButtonEvent(c.X / 2, c.Y / 2, 0, true, game, 0)
            vim:SendMouseButtonEvent(c.X / 2, c.Y / 2, 0, false, game, 0)
        end)
    end
end
STOMP.getTool = function(ch)
    local t = ch:FindFirstChildOfClass("Tool")
    if t then return t end
    local hum = ch:FindFirstChildOfClass("Humanoid")
    local bp = lp:FindFirstChildOfClass("Backpack")
    local bt = bp and bp:FindFirstChildOfClass("Tool")
    if bt and hum then pcall(function() hum:EquipTool(bt) end) return bt end
    return nil
end
do
    -- يراقب كل لاعب كل 0.05 ثانية: يحفظ آخر مكان وهو حي، ولما يموت (صحة 0 / اختفى جسمه / تغيّر جسمه) يسجله
    local acc, lastJump = 0, 0
    table.insert(conns, RunService.Heartbeat:Connect(function(dt)
        if closed then return end
        acc = acc + dt
        if acc < 0.05 then return end
        acc = 0
        local now = os.clock()
        for _, p in ipairs(Players:GetPlayers()) do
            if p ~= lp then
                local ch = p.Character
                local hum = ch and ch:FindFirstChildOfClass("Humanoid")
                local hrp = ch and ch:FindFirstChild("HumanoidRootPart")
                local rec = STOMP.alive[p]
                if hum and hrp and hrp.Parent and hum.Health > 0 then
                    STOMP.alive[p] = {ch = ch, pos = hrp.Position, hrp = hrp}
                    STOMP.list[p] = nil                              -- رجع حي
                elseif rec then
                    -- كان حي وصار ميت أو اختفى
                    STOMP.alive[p] = nil
                    local pos = rec.pos
                    if rec.hrp and rec.hrp.Parent then pos = rec.hrp.Position end
                    STOMP.list[p] = {t = now, pos = pos, hrp = rec.hrp, p = p}
                end
            end
        end
        for p in pairs(STOMP.alive) do
            if not p.Parent then STOMP.alive[p] = nil end
        end

        if not autoClick then STOMP.busy = false return end
        local ch = lp.Character
        local hum = ch and ch:FindFirstChildOfClass("Humanoid")
        local root = ch and ch:FindFirstChild("HumanoidRootPart")
        if not (hum and root) or hum.Health <= 0 then STOMP.busy = false return end
        local best, bd = nil, STOMP.range
        for p, info in pairs(STOMP.list) do
            if not p.Parent or now - info.t > STOMP.life then
                STOMP.list[p] = nil
            elseif not isTeammate(p) then
                local pos = (info.hrp and info.hrp.Parent) and info.hrp.Position or info.pos
                local d = (pos - root.Position).Magnitude
                if d < bd then best, bd = pos, d end
            end
        end
        if not best then STOMP.busy = false return end
        STOMP.busy = true
        local flat = Vector3.new(best.X - root.Position.X, 0, best.Z - root.Position.Z).Magnitude
        if flat > 2.5 then
            hum:MoveTo(best)
            if best.Y - root.Position.Y > 3 and now - lastJump > 0.4 then lastJump = now; hum.Jump = true end
        else
            hum:MoveTo(root.Position)
            if now - lastJump > 0.28 then lastJump = now; hum.Jump = true end      -- ننط فوقه (دعس)
        end
        local tool = STOMP.getTool(ch)
        if tool and bd <= 12 and now - lastClick >= 1 / math.max(clickCPS, 1) then
            lastClick = now
            STOMP.click(tool)
        end
    end))
end

    -- ===== جودة سينمائية للماب =====
local CINE = {on = false}
do
    local Lighting = game:GetService("Lighting")
    local Terrain = workspace:FindFirstChildOfClass("Terrain")
    local cam = workspace.CurrentCamera

    -- ===== إعدادات (غيّرها بسهولة) =====
    local S = {
        timeOfDay    = "17:40:00",   -- وقت الغروب الذهبي (سينمائي). "" = لا تغيّر الوقت
        exposure     = 0.15,
        brightness   = 2.2,
        warmSun      = Color3.fromRGB(255, 214, 170),
        shadowTint   = Color3.fromRGB(70, 85, 120),
        bloom        = {Intensity = 0.55, Size = 32, Threshold = 1.0},
        sunRays      = {Intensity = 0.12, Spread = 0.75},
        grade        = {Brightness = 0.02, Contrast = 0.22, Saturation = 0.12, Tint = Color3.fromRGB(255, 242, 228)},
        dof          = {FarIntensity = 0.18, FocusDistance = 55, InFocusRadius = 45, NearIntensity = 0},
        atmosphere   = {Density = 0.33, Offset = 0.25, Color = Color3.fromRGB(205, 190, 175),
                        Decay = Color3.fromRGB(110, 100, 110), Glare = 0.4, Haze = 1.6},
        vignette     = true,
        fov          = 0,
    }
    local KEYS = {"ClockTime", "Brightness", "ExposureCompensation", "Ambient", "OutdoorAmbient",
        "ColorShift_Top", "ColorShift_Bottom", "EnvironmentDiffuseScale", "EnvironmentSpecularScale",
        "GlobalShadows", "ShadowSoftness", "FogEnd", "FogStart"}

    local saved, created, disabled, oldAtmo, oldAtmoParent, oldFov = {}, {}, {}, nil, nil, nil
    local function add(class, props, parent)
        local o = new(class, props, parent or Lighting)
        table.insert(created, o)
        return o
    end

    function CINE.apply()
        if CINE.on or closed then return end
        CINE.on = true
        saved, created, disabled = {}, {}, {}
        for _, k in ipairs(KEYS) do pcall(function() saved[k] = Lighting[k] end) end
        oldFov = cam and cam.FieldOfView
        for _, e in ipairs(Lighting:GetChildren()) do
            pcall(function()
                if e:IsA("PostEffect") and e.Enabled then e.Enabled = false; table.insert(disabled, e) end
            end)
        end
        oldAtmo = Lighting:FindFirstChildOfClass("Atmosphere")
        oldAtmoParent = oldAtmo and oldAtmo.Parent
        if oldAtmo then pcall(function() oldAtmo.Parent = nil end) end

        pcall(function()
            if S.timeOfDay ~= "" then Lighting.TimeOfDay = S.timeOfDay end
            Lighting.Brightness = S.brightness
            Lighting.ExposureCompensation = S.exposure
            Lighting.Ambient = Color3.fromRGB(70, 74, 88)
            Lighting.OutdoorAmbient = Color3.fromRGB(95, 100, 120)
            Lighting.ColorShift_Top = S.warmSun
            Lighting.ColorShift_Bottom = S.shadowTint
            Lighting.EnvironmentDiffuseScale = 1
            Lighting.EnvironmentSpecularScale = 1
            Lighting.GlobalShadows = true
            Lighting.ShadowSoftness = 0.15
            Lighting.FogStart = 0
            Lighting.FogEnd = 100000
        end)
        pcall(function() sethiddenproperty(Lighting, "Technology", Enum.Technology.Future) end)
        pcall(function() settings().Rendering.QualityLevel = Enum.QualityLevel.Level21 end)
        if Terrain then pcall(function() Terrain.Decoration = true end) end

        add("BloomEffect", S.bloom)
        add("SunRaysEffect", S.sunRays)
        add("ColorCorrectionEffect", {Brightness = S.grade.Brightness, Contrast = S.grade.Contrast,
            Saturation = S.grade.Saturation, TintColor = S.grade.Tint})
        add("DepthOfFieldEffect", S.dof)
        add("Atmosphere", S.atmosphere)
        if cam and S.fov > 0 then pcall(function() cam.FieldOfView = S.fov end) end

        if S.vignette then
            local function edge(pos, size, rot)
                local f = add("Frame", {BackgroundColor3 = Color3.new(0, 0, 0), BorderSizePixel = 0, Position = pos,
                    Size = size, ZIndex = 0, Active = false}, gui)
                new("UIGradient", {Rotation = rot, Transparency = NumberSequence.new({
                    NumberSequenceKeypoint.new(0, 0.55), NumberSequenceKeypoint.new(1, 1)})}, f)
            end
            edge(UDim2.new(0, 0, 0, 0), UDim2.new(1, 0, 0.18, 0), 90)
            edge(UDim2.new(0, 0, 0.82, 0), UDim2.new(1, 0, 0.18, 0), 270)
            edge(UDim2.new(0, 0, 0, 0), UDim2.new(0.12, 0, 1, 0), 0)
            edge(UDim2.new(0.88, 0, 0, 0), UDim2.new(0.12, 0, 1, 0), 180)
        end
    end

    function CINE.restore()
        if not CINE.on then return end
        CINE.on = false
        for _, o in ipairs(created) do pcall(function() o:Destroy() end) end
        for _, e in ipairs(disabled) do pcall(function() e.Enabled = true end) end
        if oldAtmo and oldAtmoParent then pcall(function() oldAtmo.Parent = oldAtmoParent end) end
        for k, v in pairs(saved) do pcall(function() Lighting[k] = v end) end
        if cam and oldFov then pcall(function() cam.FieldOfView = oldFov end) end
        created, disabled = {}, {}
    end
end

    -- ===== القنبلة اللي بيدك تلمع =====
local BOMBSKIN = {on = false}
do
    local RED, WHITE = Color3.fromRGB(255, 85, 110), Color3.fromRGB(255, 255, 255)   -- احمر وردي + ابيض مثل الفيديو
    local NAMES = {"bomb", "قنبل"}       -- اي اداة/جزء اسمه فيه هذي الكلمات يتلون (زيد كلمات لو اسم القنبلة بالماب غير)
    local orig = setmetatable({}, {__mode = "k"})   -- part -> {Color, Material, Reflectance, tex}
    local lights = {}
    local cache = {}                      -- char -> {parts = {...}, n = counter}
    local phase = {}                      -- char -> phase
    local conn, acc = nil, 0

    local function isBomb(name)
        name = string.lower(name)
        for _, k in ipairs(NAMES) do if string.find(name, k, 1, true) then return true end end
        return false
    end
    local function addParts(inst, list)
        if inst:IsA("BasePart") then table.insert(list, inst) end
        for _, d in ipairs(inst:GetDescendants()) do
            if d:IsA("BasePart") then table.insert(list, d) end
        end
    end
    local function readCounter(char)      -- العداد فوق اللاعب (رقم داخل BillboardGui) لو لقيناه نسرّع اللمعان
        for _, d in ipairs(char:GetDescendants()) do
            if d:IsA("TextLabel") and d:FindFirstAncestorWhichIsA("BillboardGui") then
                local n = tonumber(d.Text)
                if n then return n end
            end
        end
    end
    local function scan()
        for _, p in ipairs(Players:GetPlayers()) do
            local char = p.Character
            if char then
                local list = {}
                for _, c in ipairs(char:GetChildren()) do
                    if isBomb(c.Name) then addParts(c, list) end
                end
                if #list > 0 then local o = cache[char]; cache[char] = {parts = list, n = readCounter(char), last = (o and #o.parts == #list) and o.last or nil} else cache[char] = nil end
            end
        end
        for char in pairs(cache) do if not char.Parent then cache[char] = nil end end
    end
    local function paint(part, color)
        if not orig[part] then
            local tex
            if part:IsA("MeshPart") then tex = part.TextureID elseif part:IsA("SpecialMesh") then tex = part.TextureId end
            orig[part] = {Color = part.Color, Material = part.Material, Reflectance = part.Reflectance, tex = tex}
            pcall(function() if part:IsA("MeshPart") then part.TextureID = "" end end)
        end
        part.Material = Enum.Material.SmoothPlastic    -- مو نيون عشان ما يعمي الشاشة
        part.Color = color
        part.Reflectance = 0
        for _, ch in ipairs(part:GetChildren()) do
            if ch:IsA("SpecialMesh") then pcall(function() ch.TextureId = "" end) end
        end
    end

    function BOMBSKIN.set(v)
        if v == BOMBSKIN.on then return end
        BOMBSKIN.on = v
        if v then
            scan()
            acc = 0
            conn = RunService.Heartbeat:Connect(function(dt)
                if closed then return end
                acc = acc + dt
                if acc >= 0.5 then acc = 0; scan() end
                for char, info in pairs(cache) do
                    -- سرعة اللمعان: كل ما العداد يقل (يقرب الانفجار) تسرع
                    local rate = info.n and math.clamp(14 - info.n, 4, 12) or 5
                    phase[char] = (phase[char] or 0) + dt * rate
                    local on = math.sin(phase[char]) > 0
                    if info.last ~= on then
                        info.last = on
                        local col = on and RED or WHITE
                        for i, part in ipairs(info.parts) do
                            if part.Parent then
                                paint(part, col)
                            end
                        end
                    end
                end
            end)
            table.insert(conns, conn)
        else
            if conn then conn:Disconnect(); conn = nil end
            for part, o in pairs(orig) do
                pcall(function()
                    if part.Parent then
                        part.Color = o.Color; part.Material = o.Material; part.Reflectance = o.Reflectance
                        if o.tex ~= nil and part:IsA("MeshPart") then part.TextureID = o.tex end
                    end
                end)
            end
            for _, l in pairs(lights) do pcall(function() l:Destroy() end) end
            orig = setmetatable({}, {__mode = "k"}); lights = {}; cache = {}; phase = {}
        end
    end
end

    -- ===== تأثيرات القتل =====
local KFX = {current = 1, range = 45}     -- range: أقصى مسافة بينك وبين الخصم عشان يطلع التأثير
KFX.list = {
    {id = "none",       en = "None",        ar = "بدون"},
    {id = "ghost",      en = "Ghost",       ar = "شبح"},
    {id = "burn",       en = "Burn",        ar = "حرق"},
    {id = "weightless", en = "Weightless",  ar = "خالي من الوزن"},
    {id = "balloon",    en = "Balloon",     ar = "بالون"},
    {id = "blackheart", en = "Black Heart", ar = "قلب أسود"},
    {id = "freeze",     en = "Freeze",      ar = "تجميد"},
    {id = "gold",       en = "Gold",        ar = "ذهب"},
    {id = "thunder",    en = "Thunder",     ar = "الرعد"},
    {id = "silver",     en = "Silver",      ar = "فضة"},
    {id = "redbomb",    en = "Red Bomb",    ar = "القنبلة الحمراء"},
}
do
    local Debris = game:GetService("Debris")
    local rng = Random.new()
    for _, o in ipairs(workspace:GetChildren()) do if o.Name == "AstaFX" then o:Destroy() end end
    local folder = new("Folder", {Name = "AstaFX"}, workspace)
    local FX = {}
    local H = {}

    function H.partsOf(m)
        local l = {}
        for _, d in ipairs(m:GetDescendants()) do if d:IsA("BasePart") then table.insert(l, d) end end
        return l
    end
    function H.ghostPart(props)
        props.Anchored = true; props.CanCollide = false; props.CanQuery = false; props.CanTouch = false
        return new("Part", props, folder)
    end
    function H.run(dur, step)
        local t0 = os.clock()
        local conn
        conn = RunService.Heartbeat:Connect(function(dt)
            local a = (os.clock() - t0) / dur
            if a >= 1 or closed then conn:Disconnect(); pcall(step, 1, dt); return end
            pcall(step, a, dt)
        end)
    end
    function H.fade(m, dur)
        for _, d in ipairs(m:GetDescendants()) do
            if d:IsA("BasePart") or d:IsA("Decal") then
                TweenService:Create(d, TweenInfo.new(dur), {Transparency = 1}):Play()
            elseif d:IsA("Fire") or d:IsA("Smoke") or d:IsA("ParticleEmitter") then
                d.Enabled = false
            elseif d:IsA("PointLight") then
                TweenService:Create(d, TweenInfo.new(dur), {Brightness = 0}):Play()
            elseif d:IsA("Highlight") then
                TweenService:Create(d, TweenInfo.new(dur), {FillTransparency = 1, OutlineTransparency = 1}):Play()
            end
        end
    end
    function H.strip(m)      -- نشيل الملابس والوجه عشان يبان لون التأثير نظيف
        for _, d in ipairs(m:GetDescendants()) do
            pcall(function()
                if d:IsA("Shirt") or d:IsA("Pants") or d:IsA("ShirtGraphic") or d:IsA("BodyColors")
                    or d:IsA("SurfaceAppearance") or d:IsA("Decal") or d:IsA("Texture") or d:IsA("CharacterMesh") then
                    d:Destroy()
                elseif d:IsA("MeshPart") then d.TextureID = ""
                elseif d:IsA("SpecialMesh") then d.TextureId = "" end
            end)
        end
    end
    function H.paint(parts, color, material, reflect, dur)
        for _, p in ipairs(parts) do
            if p.Name ~= "HumanoidRootPart" then
                p.Material = material; p.Reflectance = reflect or 0
                if dur then TweenService:Create(p, TweenInfo.new(dur), {Color = color}):Play() else p.Color = color end
            end
        end
    end
    function H.sparkles(parts, color, rate)
        local list = {}
        for _, p in ipairs(parts) do
            if p.Name == "Torso" or p.Name == "UpperTorso" or p.Name == "Head" then
                table.insert(list, new("ParticleEmitter", {Color = ColorSequence.new(color), Size = NumberSequence.new(0.6, 0),
                    Lifetime = NumberRange.new(0.8, 1.4), Rate = rate or 30, Speed = NumberRange.new(3, 7),
                    SpreadAngle = Vector2.new(180, 180), LightEmission = 1, Transparency = NumberSequence.new(0, 1)}, p))
            end
        end
        return list
    end
    function H.shards(pos, color, material, count, speed, life)
        local list = {}
        for i = 1, count do
            local s = rng:NextNumber(0.3, 0.9)
            local p = H.ghostPart({Size = Vector3.new(s, s * rng:NextNumber(0.6, 1.4), s * rng:NextNumber(0.6, 1.4)),
                Color = color, Material = material,
                CFrame = CFrame.new(pos + Vector3.new(rng:NextNumber(-1.2, 1.2), rng:NextNumber(-2, 2), rng:NextNumber(-1.2, 1.2)))
                    * CFrame.Angles(rng:NextNumber(0, 6), rng:NextNumber(0, 6), rng:NextNumber(0, 6))})
            local dir = Vector3.new(rng:NextNumber(-1, 1), rng:NextNumber(0.2, 1.2), rng:NextNumber(-1, 1)).Unit
            list[i] = {p = p, v = dir * rng:NextNumber(0.5, 1) * speed,
                w = Vector3.new(rng:NextNumber(-6, 6), rng:NextNumber(-6, 6), rng:NextNumber(-6, 6))}
            Debris:AddItem(p, life + 0.5)
        end
        H.run(life, function(a, dt)
            for _, s in ipairs(list) do
                if s.p.Parent then
                    s.v = s.v + Vector3.new(0, -60 * dt, 0)
                    s.p.CFrame = CFrame.new(s.p.Position + s.v * dt) * (s.p.CFrame - s.p.Position)
                        * CFrame.Angles(s.w.X * dt, s.w.Y * dt, s.w.Z * dt)
                    if a > 0.6 then s.p.Transparency = (a - 0.6) / 0.4 end
                end
            end
        end)
    end
    function H.flatRing(pos, color)
        local r = H.ghostPart({Shape = Enum.PartType.Cylinder, Size = Vector3.new(0.3, 2, 2), Color = color,
            Material = Enum.Material.Neon, CFrame = CFrame.new(pos - Vector3.new(0, 2.5, 0)) * CFrame.Angles(0, 0, math.pi / 2)})
        TweenService:Create(r, TweenInfo.new(0.7, Enum.EasingStyle.Quad, Enum.EasingDirection.Out),
            {Size = Vector3.new(0.3, 22, 22), Transparency = 1}):Play()
        Debris:AddItem(r, 1)
    end

    -- ====== التأثيرات ======
    FX.ghost = function(m, hrp)
        H.strip(m)
        local parts = H.partsOf(m)
        H.paint(parts, Color3.fromRGB(215, 235, 255), Enum.Material.ForceField, 0)
        local hl = new("Highlight", {FillColor = Color3.fromRGB(200, 230, 255), OutlineColor = Color3.new(1, 1, 1),
            FillTransparency = 0.6, OutlineTransparency = 0.3}, m)
        local base = m:GetPivot()
        H.run(3, function(a)
            m:PivotTo(base * CFrame.new(math.sin(a * 12) * 0.6, 14 * a, 0) * CFrame.Angles(0, a * math.pi * 2, 0))
            local tr = 0.35 + 0.65 * math.max(0, (a - 0.5) / 0.5)
            for _, p in ipairs(parts) do if p.Name ~= "HumanoidRootPart" then p.Transparency = tr end end
            hl.FillTransparency = math.min(1, 0.6 + 0.4 * math.max(0, (a - 0.5) / 0.5))
            hl.OutlineTransparency = math.min(1, 0.3 + 0.7 * math.max(0, (a - 0.5) / 0.5))
        end)
    end

    FX.burn = function(m, hrp)
        H.strip(m)
        local parts = H.partsOf(m)
        H.paint(parts, Color3.fromRGB(25, 20, 18), Enum.Material.Slate, 0, 1.2)
        for _, p in ipairs(parts) do
            if p.Name ~= "HumanoidRootPart" and p.Size.Magnitude > 1 then
                new("Fire", {Size = 6, Heat = 9, Color = Color3.fromRGB(255, 120, 20), SecondaryColor = Color3.fromRGB(255, 40, 0)}, p)
            end
        end
        new("Smoke", {Size = 6, Opacity = 0.35, RiseVelocity = 6, Color = Color3.fromRGB(40, 40, 40)}, hrp)
        new("PointLight", {Color = Color3.fromRGB(255, 130, 40), Range = 14, Brightness = 2}, hrp)
        task.delay(2.4, function() H.fade(m, 0.8) end)
    end

    FX.weightless = function(m, hrp)
        local parts = H.partsOf(m)
        local head = m:FindFirstChild("Head")
        local owner, vel, spin = {}, {}, {}
        for _, p in ipairs(parts) do
            local o = p
            if head and p:FindFirstAncestorOfClass("Accessory") then o = head end
            owner[p] = o
            if not vel[o] then
                vel[o] = Vector3.new(rng:NextNumber(-3, 3), rng:NextNumber(3, 7), rng:NextNumber(-3, 3))
                spin[o] = Vector3.new(rng:NextNumber(-3, 3), rng:NextNumber(-3, 3), rng:NextNumber(-3, 3))
            end
        end
        H.run(3.2, function(a, dt)
            local centers = {}
            for o in pairs(vel) do centers[o] = o.Position end
            for _, p in ipairs(parts) do
                local o = owner[p]; local c = centers[o]; local s = spin[o]
                p.CFrame = CFrame.new(vel[o] * dt) * (CFrame.new(c) * CFrame.Angles(s.X * dt, s.Y * dt, s.Z * dt) * CFrame.new(-c) * p.CFrame)
            end
        end)
        task.delay(2.4, function() H.fade(m, 0.8) end)
    end

    FX.balloon = function(m, hrp)      -- الجسم نفسه يطلع لفوق مربوط ببالون
        local base = m:GetPivot()
        local bpos = hrp.Position
        local balloon = H.ghostPart({Shape = Enum.PartType.Ball, Size = Vector3.new(0.5, 0.5, 0.5),
            Color = Color3.fromRGB(150, 205, 120), Material = Enum.Material.SmoothPlastic, Reflectance = 0.1,
            CFrame = CFrame.new(bpos + Vector3.new(0, 9, 0))})
        local str = H.ghostPart({Size = Vector3.new(0.12, 3.2, 0.12), Color = Color3.fromRGB(235, 235, 235),
            Material = Enum.Material.SmoothPlastic, CFrame = CFrame.new(bpos + Vector3.new(0, 4, 0))})
        Debris:AddItem(balloon, 7); Debris:AddItem(str, 7)
        task.delay(4.2, function()
            for _, o in ipairs({balloon, str}) do
                TweenService:Create(o, TweenInfo.new(0.7), {Transparency = 1}):Play()
            end
            H.fade(m, 0.7)
        end)
        H.run(5, function(a)
            local grow = math.min(1, a / 0.07)
            local h = (a < 0.07) and 0 or (((a - 0.07) / 0.93) ^ 1.8) * 90
            local off = Vector3.new(math.sin(a * 14) * 1.2, h, 0)
            local sway = math.sin(a * 9) * 0.12
            m:PivotTo((base + off) * CFrame.Angles(0, a * 2, sway))
            local r = 0.5 + 5.5 * (1 - (1 - grow) ^ 3)
            balloon.Size = Vector3.new(r, r * 1.15, r)
            balloon.CFrame = CFrame.new(bpos + off + Vector3.new(0, 6 + r * 0.55, 0)) * CFrame.Angles(0, 0, sway)
            str.CFrame = CFrame.new(bpos + off + Vector3.new(0, 4, 0))
        end)
    end

    FX.blackheart = function(m, hrp)
        H.strip(m)
        local parts = H.partsOf(m)
        H.paint(parts, Color3.fromRGB(12, 12, 14), Enum.Material.Slate, 0, 0.6)
        local pos = hrp.Position
        task.delay(0.9, function()
            H.fade(m, 0.5)
            H.shards(pos, Color3.fromRGB(14, 14, 18), Enum.Material.Slate, 22, 28, 1.6)
        end)
        for i = 1, 6 do
            task.delay(0.15 * i, function()
                local st = pos + Vector3.new(rng:NextNumber(-2, 2), 1 + i * 0.3, rng:NextNumber(-2, 2))
                local hp = H.ghostPart({Size = Vector3.new(0.4, 0.4, 0.4), Transparency = 1, CFrame = CFrame.new(st)})
                local bb = new("BillboardGui", {Size = UDim2.new(0, 56, 0, 56), LightInfluence = 0}, hp)
                local lb = new("TextLabel", {BackgroundTransparency = 1, Size = UDim2.new(1, 0, 1, 0), Text = "♥",
                    TextScaled = true, Font = Enum.Font.GothamBlack, TextColor3 = Color3.fromRGB(8, 8, 10)}, bb)
                local sk = new("UIStroke", {Color = Color3.fromRGB(110, 110, 140), Thickness = 2}, lb)
                Debris:AddItem(hp, 3)
                H.run(2.2, function(a)
                    hp.Position = st + Vector3.new(0, a * 9, 0)
                    local tr = math.max(0, (a - 0.4) / 0.6)
                    lb.TextTransparency = tr; sk.Transparency = tr
                end)
            end)
        end
    end

    FX.freeze = function(m, hrp)
        H.strip(m)
        local parts = H.partsOf(m)
        H.paint(parts, Color3.fromRGB(170, 225, 255), Enum.Material.Ice, 0.1, 0.4)
        local pos = hrp.Position
        local block = H.ghostPart({Size = Vector3.new(0.5, 0.5, 0.5), CFrame = CFrame.new(pos), Color = Color3.fromRGB(190, 235, 255),
            Material = Enum.Material.Glass, Transparency = 0.45, Reflectance = 0.2})
        Debris:AddItem(block, 4)
        TweenService:Create(block, TweenInfo.new(0.35, Enum.EasingStyle.Back, Enum.EasingDirection.Out),
            {Size = Vector3.new(5.5, 7, 5)}):Play()
        task.delay(2.2, function()
            block:Destroy()
            H.shards(pos, Color3.fromRGB(190, 235, 255), Enum.Material.Ice, 26, 22, 1.6)
            H.fade(m, 0.3)
        end)
    end

    FX.gold = function(m, hrp)
        H.strip(m)
        local parts = H.partsOf(m)
        H.paint(parts, Color3.fromRGB(255, 196, 40), Enum.Material.Metal, 0.35, 0.5)
        new("PointLight", {Color = Color3.fromRGB(255, 200, 60), Range = 16, Brightness = 2}, hrp)
        H.sparkles(parts, Color3.fromRGB(255, 230, 120), 35)
        local base = m:GetPivot()
        H.run(3, function(a) m:PivotTo(base * CFrame.new(0, 1.2 * a, 0) * CFrame.Angles(0, a * math.pi * 4, 0)) end)
        task.delay(2.4, function() H.fade(m, 0.6) end)
    end

    FX.silver = function(m, hrp)
        H.strip(m)
        local parts = H.partsOf(m)
        H.paint(parts, Color3.fromRGB(200, 205, 215), Enum.Material.Metal, 0.55, 0.5)
        H.sparkles(parts, Color3.fromRGB(235, 240, 255), 25)
        local pos = hrp.Position
        task.delay(2.0, function()
            H.shards(pos, Color3.fromRGB(205, 210, 220), Enum.Material.Metal, 24, 22, 1.5)
            H.fade(m, 0.2)
        end)
    end

    -- ====== الرعد (سينمائي): برق متفرع + فلاش + هزة كاميرا + صوت رعد ======
    local THUNDER_SOUND_ID  = 0     -- رقم صوت رعد من روبلوكس (يغلب على الافتراضي). 0 = الافتراضي
    local THUNDER_SOUND_URL = ""    -- أو رابط مباشر mp3/ogg (يشتغل بالاكسكيوتر)
    local THUNDER_VOLUME    = 3     -- مستوى الصوت
    local Lighting = game:GetService("Lighting")
    local thunderAsset

    local function resolveThunderSound()
        if thunderAsset then return thunderAsset end
        if THUNDER_SOUND_URL ~= "" then
            local ok, a = pcall(function()
                writefile("asta_thunder.mp3", game:HttpGet(THUNDER_SOUND_URL))
                return getcustomasset("asta_thunder.mp3")
            end)
            if ok and a then thunderAsset = a; return a end
        end
        if THUNDER_SOUND_ID ~= 0 then thunderAsset = "rbxassetid://" .. THUNDER_SOUND_ID
        else thunderAsset = "rbxasset://sounds/impact_explosion_03.mp3" end
        return thunderAsset
    end

    local function thunderSound(emitter, speed, vol, delay, long)
        task.delay(delay, function()
            if closed then return end
            local s = new("Sound", {SoundId = resolveThunderSound(), Volume = vol, PlaybackSpeed = speed,
                RollOffMaxDistance = 300, RollOffMinDistance = 30}, emitter)
            new("EqualizerSoundEffect", {LowGain = long and 8 or 0, MidGain = long and -10 or -2, HighGain = long and -14 or 4}, s)
            new("ReverbSoundEffect", {DecayTime = long and 4.5 or 1.2, Density = 1, Diffusion = 1,
                DryLevel = -3, WetLevel = long and 3 or -2}, s)
            s:Play()
            Debris:AddItem(s, 10)
        end)
    end

    -- برق متفرع: ازاحة نقطة المنتصف بشكل عشوائي + فروع جانبية
    local function jag(a, b, disp, depth, thick, list)
        if depth == 0 then
            local len = (b - a).Magnitude
            if len < 0.05 then return end
            local cf = CFrame.lookAt(a, b) * CFrame.new(0, 0, -len / 2)
            local glow = H.ghostPart({Size = Vector3.new(thick * 4, thick * 4, len), Color = Color3.fromRGB(110, 160, 255),
                Material = Enum.Material.Neon, Transparency = 0.7, CFrame = cf})
            local core = H.ghostPart({Size = Vector3.new(thick, thick, len), Color = Color3.fromRGB(245, 250, 255),
                Material = Enum.Material.Neon, CFrame = cf})
            Debris:AddItem(glow, 1); Debris:AddItem(core, 1)
            table.insert(list, glow); table.insert(list, core)
            return
        end
        local mid = (a + b) / 2 + Vector3.new(rng:NextNumber(-disp, disp), rng:NextNumber(-disp, disp) * 0.3, rng:NextNumber(-disp, disp))
        jag(a, mid, disp * 0.55, depth - 1, thick, list)
        jag(mid, b, disp * 0.55, depth - 1, thick, list)
        if depth >= 3 and rng:NextNumber() < 0.45 then
            local dir = (b - a)
            local tip = mid + Vector3.new(rng:NextNumber(-1, 1) * 12, -math.abs(dir.Y) * 0.35, rng:NextNumber(-1, 1) * 12)
            jag(mid, tip, disp * 0.6, depth - 2, thick * 0.55, list)
        end
    end

    local function screenFlash(power)
        local cc = new("ColorCorrectionEffect", {Brightness = power, Contrast = power * 0.6, Saturation = -power * 0.5}, Lighting)
        TweenService:Create(cc, TweenInfo.new(0.35, Enum.EasingStyle.Quad, Enum.EasingDirection.Out),
            {Brightness = 0, Contrast = 0, Saturation = 0}):Play()
        Debris:AddItem(cc, 0.5)
    end

    local function camShake(dur, power)
        local hum = lp.Character and lp.Character:FindFirstChildOfClass("Humanoid")
        if not hum then return end
        H.run(dur, function(a)
            local k = (1 - a) * power
            hum.CameraOffset = Vector3.new(rng:NextNumber(-k, k), rng:NextNumber(-k, k), 0)
            if a >= 1 then hum.CameraOffset = Vector3.zero end
        end)
    end

    FX.thunder = function(m, hrp)
        H.strip(m)
        local parts = H.partsOf(m)
        local pos = hrp.Position
        local groundPos = pos - Vector3.new(0, 2.8, 0)
        local emitter = H.ghostPart({Size = Vector3.new(1, 1, 1), Transparency = 1, CFrame = CFrame.new(pos)})
        Debris:AddItem(emitter, 12)
        local light = new("PointLight", {Color = Color3.fromRGB(180, 210, 255), Range = 45, Brightness = 0}, hrp)
        local top = pos + Vector3.new(rng:NextNumber(-6, 6), 85, rng:NextNumber(-6, 6))

        -- ضربات متتالية مثل الصاعقة الحقيقية (الأولى أقوى، وبعدها ارتدادات)
        local strikes = {{0, 1.0}, {0.09, 0.6}, {0.21, 0.8}}
        for k, st in ipairs(strikes) do
            task.delay(st[1], function()
                if closed then return end
                local list = {}
                jag(top + Vector3.new(rng:NextNumber(-1, 1), 0, rng:NextNumber(-1, 1)), pos, 14, 5, 0.35 + 0.15 * st[2], list)
                for _, p in ipairs(list) do
                    TweenService:Create(p, TweenInfo.new(0.22 + 0.1 * k), {Transparency = 1}):Play()
                end
                light.Brightness = 14 * st[2]
                TweenService:Create(light, TweenInfo.new(0.3), {Brightness = 0}):Play()
                H.paint(parts, Color3.fromRGB(250, 252, 255), Enum.Material.Neon, 0)
                screenFlash(0.45 * st[2])
                if k == 1 then
                    H.flatRing(pos, Color3.fromRGB(140, 190, 255))
                    camShake(0.55, 0.45)
                    thunderSound(emitter, 1.35, THUNDER_VOLUME * 1.1, 0, false)    -- طقة البرق (قريبة وحادة)
                    thunderSound(emitter, 0.5, THUNDER_VOLUME, 0.28, true)         -- هزيم الرعد (واطي وطويل)
                    -- شرر وقطع متطايرة عند الضربة
                    H.shards(groundPos + Vector3.new(0, 1, 0), Color3.fromRGB(255, 240, 160), Enum.Material.Neon, 14, 26, 0.6)
                    -- بقعة احتراق على الارض
                    local scorch = H.ghostPart({Shape = Enum.PartType.Cylinder, Size = Vector3.new(0.12, 6, 6),
                        Color = Color3.fromRGB(12, 12, 14), Material = Enum.Material.Slate, Transparency = 0.15,
                        CFrame = CFrame.new(groundPos) * CFrame.Angles(0, 0, math.pi / 2)})
                    task.delay(4, function() TweenService:Create(scorch, TweenInfo.new(3), {Transparency = 1}):Play() end)
                    Debris:AddItem(scorch, 8)
                end
                task.delay(0.06, function()
                    H.paint(parts, Color3.fromRGB(22, 20, 24), Enum.Material.Slate, 0)   -- يتفحم بعد الضوء
                end)
            end)
        end

        -- دخان وجمرات من الجسم المتفحم + رعشة قصيرة
        task.delay(0.3, function()
            for _, p in ipairs(parts) do
                if p.Name == "Torso" or p.Name == "UpperTorso" or p.Name == "Head" then
                    new("ParticleEmitter", {Color = ColorSequence.new(Color3.fromRGB(60, 60, 66)), Size = NumberSequence.new(0.8, 2.4),
                        Lifetime = NumberRange.new(1.2, 2.2), Rate = 22, Speed = NumberRange.new(2, 4), Acceleration = Vector3.new(0, 4, 0),
                        SpreadAngle = Vector2.new(25, 25), Transparency = NumberSequence.new(0.4, 1)}, p)
                    new("ParticleEmitter", {Color = ColorSequence.new(Color3.fromRGB(255, 150, 50)), Size = NumberSequence.new(0.25, 0),
                        Lifetime = NumberRange.new(0.5, 1.1), Rate = 18, Speed = NumberRange.new(3, 8), LightEmission = 1,
                        SpreadAngle = Vector2.new(60, 60)}, p)
                end
            end
            local base = m:GetPivot()
            H.run(0.5, function(a)
                local k = (1 - a) * 0.25
                m:PivotTo(base * CFrame.new(rng:NextNumber(-k, k), 0, rng:NextNumber(-k, k)))
            end)
        end)
        task.delay(2.6, function() H.fade(m, 0.8) end)
    end

    -- ====== القنبلة الحمراء: تلزق بالقتيل، تنبض بالاحمر ثم تنفجر انفجار سينمائي ======
    local function boomSound(parent, id, speed, vol, delay, deep)
        task.delay(delay, function()
            if closed then return end
            local s = new("Sound", {SoundId = id, Volume = vol, PlaybackSpeed = speed,
                RollOffMaxDistance = 300, RollOffMinDistance = 30}, parent)
            new("EqualizerSoundEffect", {LowGain = deep and 8 or 0, MidGain = deep and -6 or 0, HighGain = deep and -12 or 2}, s)
            new("ReverbSoundEffect", {DecayTime = deep and 3.5 or 1.4, Density = 1, Diffusion = 1,
                DryLevel = -2, WetLevel = deep and 2 or -3}, s)
            s:Play()
            Debris:AddItem(s, 8)
        end)
    end
    local function sphere(pos, color, size0, size1, t, tr0, ease)
        local s = H.ghostPart({Shape = Enum.PartType.Ball, Size = Vector3.one * size0, Color = color,
            Material = Enum.Material.Neon, Transparency = tr0, CFrame = CFrame.new(pos)})
        TweenService:Create(s, TweenInfo.new(t, ease or Enum.EasingStyle.Quint, Enum.EasingDirection.Out),
            {Size = Vector3.one * size1, Transparency = 1}):Play()
        Debris:AddItem(s, t + 0.2)
        return s
    end

    FX.redbomb = function(m, hrp)
        local parts = H.partsOf(m)
        local pos = hrp.Position
        local groundY = pos.Y - 2.6
        local BOMB_TIME = 1.15

        -- القنبلة: جسم احمر + حزام ابيض + راس ابيض، كلها تلمع احمر/ابيض بالتناوب
        local RED, WHITE = Color3.fromRGB(255, 25, 25), Color3.fromRGB(255, 255, 255)
        local DRED = Color3.fromRGB(120, 8, 8)
        local bpos = pos + Vector3.new(0, 0.6, -0.9)
        local bomb = H.ghostPart({Shape = Enum.PartType.Ball, Size = Vector3.one * 2.1, Color = RED,
            Material = Enum.Material.Neon, CFrame = CFrame.new(bpos)})
        local band = H.ghostPart({Shape = Enum.PartType.Cylinder, Size = Vector3.new(0.45, 2.16, 2.16), Color = WHITE,
            Material = Enum.Material.Neon, CFrame = CFrame.new(bpos) * CFrame.Angles(0, 0, math.pi / 2)})
        local eye = H.ghostPart({Shape = Enum.PartType.Ball, Size = Vector3.one * 0.8, Color = WHITE,
            Material = Enum.Material.Neon, CFrame = CFrame.new(bpos + Vector3.new(0, 1.1, 0))})
        local glow = new("PointLight", {Color = RED, Range = 18, Brightness = 0}, bomb)
        new("ParticleEmitter", {Texture = "rbxasset://textures/particles/sparkles_main.dds", Color = ColorSequence.new(WHITE, RED),
            Size = NumberSequence.new(0.5, 0), Lifetime = NumberRange.new(0.2, 0.5), Rate = 40, Speed = NumberRange.new(3, 7),
            SpreadAngle = Vector2.new(60, 60), LightEmission = 1}, eye)
        local beep = new("Sound", {SoundId = "rbxasset://sounds/electronicpingshort.wav", Volume = 2, RollOffMaxDistance = 120}, bomb)

        local phase, lastOn = 0, false
        local basePivot = m:GetPivot()
        H.run(BOMB_TIME, function(a, dt)
            phase = phase + dt * (9 + a * 34)
            local on = math.sin(phase) > 0            -- يلمع: احمر <-> ابيض وكل ما يقرب ينفجر يسرّع
            bomb.Color = on and RED or WHITE
            band.Color = on and WHITE or RED
            eye.Color = on and WHITE or RED
            glow.Color = on and RED or WHITE
            glow.Brightness = 6 + a * 12
            if on and not lastOn then beep.PlaybackSpeed = 0.9 + a * 1.2; beep:Play() end
            lastOn = on
            local k = a * 0.18          -- الجسم يرتجف قبل الانفجار
            m:PivotTo(basePivot * CFrame.new(rng:NextNumber(-k, k), 0, rng:NextNumber(-k, k)))
        end)

        task.delay(BOMB_TIME, function()
            if closed then return end
            bomb:Destroy(); band:Destroy(); eye:Destroy()
            local ep = H.ghostPart({Size = Vector3.one, Transparency = 1, CFrame = CFrame.new(bpos)})
            Debris:AddItem(ep, 8)

            -- صوت: فرقعة قريبة + هزيم عميق
            boomSound(ep, "rbxasset://sounds/impact_explosion_03.mp3", 1.0, 4.5, 0, false)
            boomSound(ep, "rbxasset://sounds/impact_explosion_03.mp3", 0.55, 4, 0.08, true)

            -- فلاش ابيض-اصفر ثم كرة النار البرتقالية ثم قلب دخان اسود (مثل الفيديو)
            sphere(bpos, Color3.fromRGB(255, 255, 255), 4, 32, 0.22, 0, Enum.EasingStyle.Quad)
            sphere(bpos, Color3.fromRGB(255, 45, 45), 3, 26, 0.55, 0.15)
            sphere(bpos, Color3.fromRGB(190, 10, 10), 2, 18, 0.75, 0.3)
            local core = H.ghostPart({Shape = Enum.PartType.Ball, Size = Vector3.one * 2, Color = Color3.fromRGB(18, 14, 12),
                Material = Enum.Material.SmoothPlastic, Transparency = 0.1, CFrame = CFrame.new(bpos)})
            TweenService:Create(core, TweenInfo.new(1.5, Enum.EasingStyle.Quad, Enum.EasingDirection.Out),
                {Size = Vector3.one * 15, Transparency = 1}):Play()
            Debris:AddItem(core, 1.7)
            H.flatRing(Vector3.new(bpos.X, groundY + 2.5, bpos.Z), Color3.fromRGB(255, 255, 255))

            -- جزيئات: نار + شرر + دخان
            local fire = new("ParticleEmitter", {Texture = "rbxasset://textures/particles/fire_main.dds", Rate = 0,
                Color = ColorSequence.new({ColorSequenceKeypoint.new(0, Color3.fromRGB(255, 255, 255)),
                    ColorSequenceKeypoint.new(0.4, Color3.fromRGB(255, 40, 40)), ColorSequenceKeypoint.new(1, Color3.fromRGB(60, 20, 20))}),
                Size = NumberSequence.new({NumberSequenceKeypoint.new(0, 4), NumberSequenceKeypoint.new(0.4, 9), NumberSequenceKeypoint.new(1, 13)}),
                Lifetime = NumberRange.new(0.5, 1.1), Speed = NumberRange.new(25, 55), Drag = 3,
                Acceleration = Vector3.new(0, 10, 0), SpreadAngle = Vector2.new(180, 180), LightEmission = 1,
                Transparency = NumberSequence.new({NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(0.7, 0.4), NumberSequenceKeypoint.new(1, 1)}),
                Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-120, 120)}, ep)
            local sparks = new("ParticleEmitter", {Texture = "rbxasset://textures/particles/sparkles_main.dds", Rate = 0,
                Color = ColorSequence.new(Color3.fromRGB(255, 255, 255), Color3.fromRGB(255, 40, 40)), Size = NumberSequence.new(0.7, 0),
                Lifetime = NumberRange.new(0.6, 1.6), Speed = NumberRange.new(40, 85), Drag = 1.5,
                Acceleration = Vector3.new(0, -45, 0), SpreadAngle = Vector2.new(180, 180), LightEmission = 1}, ep)
            local smoke = new("ParticleEmitter", {Texture = "rbxasset://textures/particles/smoke_main.dds", Rate = 0,
                Color = ColorSequence.new(Color3.fromRGB(35, 33, 32), Color3.fromRGB(95, 92, 90)),
                Size = NumberSequence.new({NumberSequenceKeypoint.new(0, 5), NumberSequenceKeypoint.new(1, 18)}),
                Lifetime = NumberRange.new(2, 3.4), Speed = NumberRange.new(6, 16), Drag = 2,
                Acceleration = Vector3.new(0, 7, 0), SpreadAngle = Vector2.new(180, 180),
                Transparency = NumberSequence.new({NumberSequenceKeypoint.new(0, 0.35), NumberSequenceKeypoint.new(1, 1)}),
                Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-40, 40)}, ep)
            fire:Emit(70); sparks:Emit(45)
            task.delay(0.12, function() smoke:Emit(34) end)
            H.shards(bpos, Color3.fromRGB(30, 28, 28), Enum.Material.Slate, 18, 38, 1.4)

            -- اضاءة برتقالية + فلاش للشاشة + هزة كاميرا
            local lt = new("PointLight", {Color = Color3.fromRGB(255, 70, 70), Range = 60, Brightness = 25}, ep)
            TweenService:Create(lt, TweenInfo.new(1.1, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {Brightness = 0}):Play()
            screenFlash(0.5)
            camShake(0.8, 0.7)

            -- الضحية تتطاير وتتفحم
            for _, p in ipairs(parts) do
                if p.Name ~= "HumanoidRootPart" then
                    TweenService:Create(p, TweenInfo.new(0.4), {Color = Color3.fromRGB(28, 22, 20)}):Play()
                end
            end
            local v = Vector3.new(rng:NextNumber(-1, 1) * 34, 42, rng:NextNumber(-1, 1) * 34)
            local w = Vector3.new(rng:NextNumber(-9, 9), rng:NextNumber(-9, 9), rng:NextNumber(-9, 9))
            local cf = m:GetPivot()
            H.run(1.8, function(a, dt)
                v = v + Vector3.new(0, -75 * dt, 0)
                local p = cf.Position + v * dt
                if p.Y < groundY then
                    p = Vector3.new(p.X, groundY, p.Z)
                    v = Vector3.new(v.X * 0.55, math.abs(v.Y) * 0.3, v.Z * 0.55)
                    w = w * 0.6
                end
                cf = CFrame.new(p) * (cf - cf.Position) * CFrame.Angles(w.X * dt, w.Y * dt, w.Z * dt)
                m:PivotTo(cf)
            end)
            task.delay(2.2, function() H.fade(m, 0.8) end)
        end)
    end

    -- ====== التشغيل ======
    local function snapshot(char, cf)
        local clone
        pcall(function()
            local old = char.Archivable
            char.Archivable = true
            clone = char:Clone()
            char.Archivable = old
        end)
        if not clone then return nil end
        for _, d in ipairs(clone:GetDescendants()) do
            pcall(function()
                if d:IsA("Script") or d:IsA("LocalScript") or d:IsA("Humanoid") or d:IsA("Sound") or d:IsA("BillboardGui")
                    or d:IsA("ForceField") or d:IsA("Tool") or d:IsA("Highlight") or d:IsA("ParticleEmitter")
                    or d:IsA("Fire") or d:IsA("Smoke") or d:IsA("Sparkles") then
                    d:Destroy()
                end
            end)
        end
        for _, p in ipairs(H.partsOf(clone)) do
            p.Anchored = true; p.CanCollide = false; p.CanTouch = false; p.CanQuery = false; p.Massless = true
        end
        if cf then clone:PivotTo(cf) end
        clone.Parent = folder
        Debris:AddItem(clone, 12)
        return clone
    end
    local function hideOriginal(char)      -- نخفي جسم القتيل كله، يبقى بس التأثير
        local hum = char:FindFirstChildOfClass("Humanoid")
        if hum then pcall(function() hum.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None end) end
        local function hide()
            for _, d in ipairs(char:GetDescendants()) do
                if d:IsA("BasePart") then
                    d.LocalTransparencyModifier = 1; d.Transparency = 1
                elseif d:IsA("Decal") or d:IsA("Texture") then
                    d.Transparency = 1
                elseif d:IsA("BillboardGui") then
                    d.Enabled = false
                elseif d:IsA("ParticleEmitter") or d:IsA("Fire") or d:IsA("Smoke") or d:IsA("Sparkles") then
                    d.Enabled = false
                end
            end
        end
        hide()
        task.spawn(function()
            local t = os.clock()
            while os.clock() - t < 8 and char.Parent and not closed do
                hide()
                RunService.Heartbeat:Wait()
            end
        end)
    end
    function KFX.play(id, char, cf)
        local fn = FX[id]
        if not fn or not char then return end
        local m = snapshot(char, cf)
        if not m then return end
        if not cf then hideOriginal(char) end
        local hrp = m:FindFirstChild("HumanoidRootPart") or m.PrimaryPart or m:FindFirstChildWhichIsA("BasePart")
        if not hrp then m:Destroy(); return end
        local ok = pcall(fn, m, hrp)
        if not ok then m:Destroy() end
    end

    -- ====== كشف القتل ======
    local hooked = setmetatable({}, {__mode = "k"})
    local played = setmetatable({}, {__mode = "k"})
    local function onDeath(char)
        if closed or played[char] then return end
        played[char] = true
        if KFX.current <= 1 then return end
        local _, _, myRoot = getChar(lp)
        local root = char:FindFirstChild("HumanoidRootPart")
        if not (myRoot and root) then return end
        if (root.Position - myRoot.Position).Magnitude > KFX.range then return end
        KFX.play(KFX.list[KFX.current].id, char)
    end
    local function watchChar(char)
        if hooked[char] then return end
        hooked[char] = true
        local hum = char:WaitForChild("Humanoid", 5)
        if not hum then return end
        local fired = false
        local function died()
            if fired then return end
            fired = true
            pcall(onDeath, char)
        end
        table.insert(conns, hum.Died:Connect(died))
        table.insert(conns, hum.HealthChanged:Connect(function(h) if h <= 0 then died() end end))
        table.insert(conns, char.AncestryChanged:Connect(function(_, parent)
            if not parent and hum.Health <= 0 then died() end
        end))
    end
    local function watchPlayer(p)
        if p == lp then return end
        if p.Character then task.spawn(watchChar, p.Character) end
        table.insert(conns, p.CharacterAdded:Connect(watchChar))
        table.insert(conns, p.CharacterRemoving:Connect(function(c)
            local h = c:FindFirstChildOfClass("Humanoid")
            if h and h.Health <= 0 then pcall(onDeath, c) end
        end))
    end
    for _, p in ipairs(Players:GetPlayers()) do watchPlayer(p) end
    table.insert(conns, Players.PlayerAdded:Connect(watchPlayer))
    KFX.folder = folder
end

    -- ===== الأغاني =====
    local SoundService = game:GetService("SoundService")
    local HttpService = game:GetService("HttpService")
    local SONGS_FILE = "Top1Asta_songs.json"
    local songSound = Instance.new("Sound")
    songSound.Name = "Top1AstaSong"
    songSound.Volume = 0.6
    songSound.Looped = false
    songSound.Parent = SoundService
    local songs, songCache = {}, {}

    pcall(function()
        if isfile and isfile(SONGS_FILE) then
            for _, d in ipairs(HttpService:JSONDecode(readfile(SONGS_FILE))) do
                if d.name and d.kind and d.value then table.insert(songs, d) end
            end
        end
    end)

    local function saveSongs()
        pcall(function() writefile(SONGS_FILE, HttpService:JSONEncode(songs)) end)
    end

    local function songAsset(s)
        if songCache[s.value] then return songCache[s.value] end
        local asset
        if s.kind == "id" then
            asset = "rbxassetid://" .. s.value
        else
            local ext = string.find(string.lower(s.value), "%.ogg") and "ogg" or "mp3"
            local fname = "Top1Asta_url_" .. tostring(#s.value) .. "_" .. tostring(os.time() % 100000) .. "." .. ext
            writefile(fname, game:HttpGet(s.value))
            asset = getcustomasset(fname)
        end
        songCache[s.value] = asset
        return asset
    end

    -- يحوّل اللي كتبته (رقم / رابط روبلوكس / رابط mp3) لأغنية
    function AstaX.parseSong(raw)
        raw = tostring(raw or ""):gsub("^%s+", ""):gsub("%s+$", "")
        if raw == "" then return nil end
        local id = raw:match("^(%d+)$")
            or raw:match("rbxassetid://(%d+)")
            or raw:match("[?&]id=(%d+)")
            or raw:match("/library/(%d+)")
            or raw:match("/catalog/(%d+)")
            or raw:match("/store/asset/(%d+)")
            or raw:match("/asset/(%d+)")
        if id then return {name = "ID " .. id, kind = "id", value = id} end
        if raw:match("^https?://") then
            return {name = raw:match("([^/%?]+)%s*$") or "Link", kind = "url", value = raw}
        end
        return nil
    end

    function AstaX.addSong(s)
        for _, x in ipairs(songs) do
            if x.kind == s.kind and x.value == s.value then return x end
        end
        table.insert(songs, s)
        saveSongs()
        return s
    end

    function AstaX.removeSong(name)
        for i, x in ipairs(songs) do
            if x.name == name then table.remove(songs, i) saveSongs() return true end
        end
        return false
    end

    function AstaX.findSong(name)
        for _, x in ipairs(songs) do
            if x.name == name then return x end
        end
    end

    function AstaX.songNames()
        local out = {}
        for _, x in ipairs(songs) do table.insert(out, x.name) end
        return out
    end

    -- يشغّل الأغنية ويرجّع النتيجة (true/false, رسالة) عن طريق callback
    function AstaX.playSong(s, done)
        task.spawn(function()
            local ok, err = pcall(function()
                local asset = songAsset(s)
                songSound:Stop()
                songSound.SoundId = asset
                songSound.TimePosition = 0
                songSound:Play()
                local started = os.clock()
                while not songSound.IsLoaded and os.clock() - started < 5 do task.wait(0.1) end
                if not songSound.IsLoaded then error("الصوت ما تحمّل (ممكن الرقم خاص أو محذوف)") end
            end)
            if done then done(ok, ok and s.name or tostring(err)) end
        end)
    end

    function AstaX.stopSong() pcall(function() songSound:Stop() end) end
    function AstaX.setVolume(v) songSound.Volume = math.clamp(v, 0, 100) / 100 end
    function AstaX.setLoop(v) songSound.Looped = v and true or false end

    -- ===== زر الدعس على الشاشة (تقدر تسحبه وتحطه وين تبي) =====
    local stompGui = Instance.new("ScreenGui")
    stompGui.Name = "Top1AstaStompGui"
    stompGui.ResetOnSpawn = false
    stompGui.IgnoreGuiInset = true
    stompGui.DisplayOrder = 30
    pcall(function() stompGui.Parent = CoreGui end)
    if not stompGui.Parent then stompGui.Parent = lp:WaitForChild("PlayerGui") end

    local stompBtn = new("TextButton", {
        Name = "StompBtn", AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.new(0.85, 0, 0.45, 0),
        Size = UDim2.fromOffset(80, 80), BackgroundColor3 = Color3.fromRGB(25, 25, 32), BackgroundTransparency = 0.12,
        Text = "دعس", TextColor3 = Color3.fromRGB(255, 255, 255), Font = Enum.Font.GothamBold, TextSize = 22,
        AutoButtonColor = true, Active = true, Draggable = true,
    }, stompGui)
    new("UICorner", {CornerRadius = UDim.new(1, 0)}, stompBtn)
    new("UIStroke", {Color = Color3.fromRGB(0, 255, 127), Thickness = 2, Transparency = 0.2}, stompBtn)
    local stompLbl = new("TextLabel", {
        BackgroundTransparency = 1, Size = UDim2.new(1, 0, 0, 18), Position = UDim2.new(0, 0, 1, 3),
        Text = "جاهز", TextColor3 = Color3.fromRGB(0, 255, 127), Font = Enum.Font.GothamBold, TextSize = 14,
        TextStrokeTransparency = 0.4,
    }, stompBtn)

    local function stompRender()
        if stompBurstRunning then
            stompLbl.Text = "جاري الدعس..."
            stompLbl.TextColor3 = Color3.fromRGB(255, 170, 60)
            stompBtn.BackgroundColor3 = Color3.fromRGB(120, 30, 30)
        else
            stompLbl.Text = "جاهز"
            stompLbl.TextColor3 = Color3.fromRGB(0, 255, 127)
            stompBtn.BackgroundColor3 = Color3.fromRGB(25, 25, 32)
        end
    end
    stompToggleObj = {render = stompRender}

    stompBtn.MouseButton1Click:Connect(function()
        if not stompBurstRunning then
            startStompBurst()
            stompRender()
        end
    end)
    task.spawn(function()
        while stompGui.Parent do
            task.wait(0.2)
            pcall(stompRender)
        end
    end)
    -- الزر يظهر بس لما الدعس مفعّل + خيار "زر الدعس على الشاشة" شغال
    local stompBtnWanted = true
    stompGui.Enabled = false
    local function refreshStompGui()
        stompGui.Enabled = (stompEnabled and stompBtnWanted) and true or false
    end
    AstaX.setStompButton = function(v)
        stompBtnWanted = v and true or false
        refreshStompGui()
    end
    AstaX.setStompEnabled = function(v)
        stompEnabled = v and true or false
        if not stompEnabled then
            stompBurstToken = stompBurstToken + 1
            stompBurstRunning = false
        end
        refreshStompGui()
    end
    AstaX.isStompEnabled = function() return stompEnabled end

    AstaX.startStomp = startStompBurst
    AstaX.stopStomp = function() stompBurstToken = stompBurstToken + 1; stompBurstRunning = false end
    AstaX.setDeadStomp = function(v) autoClick = v and true or false end
    AstaX.KFX = KFX
    AstaX.CINE = CINE
    AstaX.BOMBSKIN = BOMBSKIN
end

Window = WindUI:CreateWindow({
    Title = RainbowText("top 1 Asta", 0),
    Author = "by Asta",
    Folder = "Top1AstaConfig",
    Size = UDim2.fromOffset(620, 480),
    Transparent = true,
    Theme = "Dark",
    SideBarWidth = 200,
    HasOutline = true,
})

-- ألوان العنوان تتغير (لو نسخة المكتبة ما تدعم تغيير العنوان يبقى ملوّن ثابت)
task.spawn(function()
    local t = 0
    while Window do
        t = (t + 0.02) % 1
        pcall(function() AuthTitle.TextColor3 = Color3.fromHSV(t, 0.8, 1) end)
        pcall(function()
            if Window.SetTitle then Window:SetTitle(RainbowText("top 1 Asta", t)) end
        end)
        task.wait(0.12)
    end
end)

-- ================= خلفية الواجهة (صورة مدمجة بالسكربت) =================
local BG_B64 = table.concat({
    "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",
})

local Backdrop = {}
do
    local scene, imgLabel
    local B64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
    local function decode64(str)
        local lut = {}
        for i = 1, #B64 do lut[B64:byte(i)] = i - 1 end
        local out, n, bits, acc = {}, 0, 0, 0
        for i = 1, #str do
            local v = lut[str:byte(i)]
            if v then
                acc = acc * 64 + v
                bits = bits + 6
                if bits >= 8 then
                    bits = bits - 8
                    local p = 2 ^ bits
                    n = n + 1
                    out[n] = string.char(math.floor(acc / p) % 256)
                    acc = acc % p
                end
            end
        end
        return table.concat(out)
    end
    local function findMain()
        local ok, m = pcall(function()
            local ui = Window.UIElements
            return ui and (ui.Main or ui.MainBar)
        end)
        if ok and typeof(m) == "Instance" then return m end
        return nil
    end
    function Backdrop.build()
        local main = findMain()
        if not main then return false end
        scene = mk("Frame", {
            Name = "Top1AstaScene", Size = UDim2.new(1, 0, 1, 0), BackgroundColor3 = Color3.fromRGB(10, 14, 36),
            BackgroundTransparency = 0.3, BorderSizePixel = 0, ZIndex = 0, ClipsDescendants = true, Active = false,
        }, main)
        pcall(function() mk("UICorner", {CornerRadius = UDim.new(0, 14)}, scene) end)
        imgLabel = mk("ImageLabel", {Name = "CustomBg", Size = UDim2.new(1, 0, 1, 0), BackgroundTransparency = 1,
            ImageTransparency = 0.35, ScaleType = Enum.ScaleType.Crop, ZIndex = 0, Visible = false}, scene)
        pcall(function() mk("UICorner", {CornerRadius = UDim.new(0, 14)}, imgLabel) end)
        return true
    end

    local function show(file)
        local oka, asset = pcall(function() return getcustomasset(file) end)
        if not oka or not asset then return false end
        imgLabel.Image = asset
        imgLabel.Visible = true
        return true
    end

    -- الصورة المدمجة (بدون رابط)
    function Backdrop.setDefault()
        if not imgLabel then return false end
        if not (writefile and getcustomasset) then return false end
        local ok = pcall(function() writefile("Top1Asta_bg_default.jpg", decode64(BG_B64)) end)
        return ok and show("Top1Asta_bg_default.jpg")
    end

    -- صورة من رابط تحطه انت (اختياري)
    function Backdrop.setImage(url)
        if not imgLabel then return false, "الخلفية ما انبنت" end
        if not (writefile and getcustomasset and game.HttpGet) then return false, "المنفّذ ما يدعم تحميل الصور" end
        local ok, data = pcall(function() return game:HttpGet(url) end)
        if not ok or not data or #data < 100 then return false, "ما قدرت أحمّل الرابط" end
        if not pcall(function() writefile("Top1Asta_bg.png", data) end) then return false, "ما قدرت أحفظ الصورة" end
        if not show("Top1Asta_bg.png") then return false, "المنفّذ ما يعرض الصورة" end
        return true
    end
    function Backdrop.clearImage()
        if imgLabel then imgLabel.Visible = false end
    end
end
task.defer(function()
    task.wait(0.5)
    if not Backdrop.build() then
        pcall(function() WindUI:Notify({ Title = "الخلفية", Content = "نسخة المكتبة ما تدعم خلفية مخصصة", Duration = 4 }) end)
    else
        Backdrop.setDefault()
    end
end)

local MainTab = Window:Tab({ Title = "الرئيسية", Icon = "home" })

local userThumb = "rbxthumb://type=AvatarBust&id=" .. LocalPlayer.UserId .. "&w=420&h=420"

MainTab:Paragraph({
    Title = "أهلاً بك، " .. LocalPlayer.DisplayName,
    Desc = "اسم المستخدم: @" .. LocalPlayer.Name .. "\nالآيدي: " .. LocalPlayer.UserId,
    Image = userThumb,
    ImageSize = 64
})

local FpsParagraph = MainTab:Paragraph({ Title = "معدل الإطارات", Desc = "FPS: 0" })
local FrameCount = 0
local LastCheck = tick()

RunService.RenderStepped:Connect(function()
    FrameCount = FrameCount + 1
    if tick() - LastCheck >= 1 then
        FpsParagraph:SetDesc("FPS: " .. math.floor(FrameCount / (tick() - LastCheck)))
        FrameCount = 0
        LastCheck = tick()
    end
end)

MainTab:Button({
    Title = "نسخ رابط الديسكورد",
    Desc = "اضغط لنسخ رابط السيرفر إلى الحافظة",
    Callback = function()
        setclipboard("https://discord.gg/hvENSHRV")
        WindUI:Notify({ Title = "تم النسخ بنجاح", Content = "رابط ديسكورد top 1 Asta في الحافظة!", Duration = 3 })
    end
})

local FeaturesTab = Window:Tab({ Title = "مميزات استا", Icon = "sparkles" })

local AutoGui = Instance.new("ScreenGui")
AutoGui.Name = "Top1AstaAutoMiniGui"
AutoGui.Parent = CoreGui
AutoGui.Enabled = false

local AutoFrame = Instance.new("Frame", AutoGui)
AutoFrame.Size = UDim2.fromOffset(210, 112)
AutoFrame.Position = UDim2.new(0.05, 0, 0.4, 0)
AutoFrame.BackgroundColor3 = Color3.fromRGB(25, 25, 25)
AutoFrame.Active = true
AutoFrame.Draggable = true

local AutoCorner = Instance.new("UICorner", AutoFrame)
AutoCorner.CornerRadius = UDim.new(0, 10)

local AutoTitle = Instance.new("TextLabel", AutoFrame)
AutoTitle.Size = UDim2.new(1, 0, 0, 38)
AutoTitle.Text = "الاوتو"
AutoTitle.TextColor3 = Color3.fromRGB(0, 255, 127)
AutoTitle.BackgroundTransparency = 1
AutoTitle.Font = Enum.Font.GothamBold
AutoTitle.TextSize = 19

local AutoBtn = Instance.new("TextButton", AutoFrame)
AutoBtn.Size = UDim2.new(0.88, 0, 0, 52)
AutoBtn.Position = UDim2.new(0.06, 0, 0.42, 0)
AutoBtn.Text = "تفعيل"
AutoBtn.BackgroundColor3 = Color3.fromRGB(40, 180, 80)
AutoBtn.TextColor3 = Color3.fromRGB(255, 255, 255)
AutoBtn.Font = Enum.Font.GothamBold
AutoBtn.TextSize = 21

local BtnCorner = Instance.new("UICorner", AutoBtn)
BtnCorner.CornerRadius = UDim.new(0, 8)

local FollowingState = false

AutoBtn.MouseButton1Click:Connect(function()
    FollowingState = not FollowingState
    if FollowingState then
        AutoBtn.Text = "إيقاف"
        AutoBtn.BackgroundColor3 = Color3.fromRGB(220, 50, 50)
    else
        AutoBtn.Text = "تفعيل"
        AutoBtn.BackgroundColor3 = Color3.fromRGB(40, 180, 80)
    end
end)

-- ================= اسيست Asta top1 (مدمج في الهب) =================
local AstaAssist = {SetAssist = function() end, SetGrab = function() end}

do
    local players = Players
    local runService = RunService
    local uis = game:GetService("UserInputService")
    local localPlayer = LocalPlayer
    local playerGui = localPlayer:WaitForChild("PlayerGui")

    -- تنظيف أي نسخة قديمة
    local oldJoy = playerGui:FindFirstChild("AstaJoyGui")
    if oldJoy then oldJoy:Destroy() end
    if _G.AstaConn then pcall(function() _G.AstaConn:Disconnect() end) end
    if _G.AstaManualConns then
        for _, c in ipairs(_G.AstaManualConns) do pcall(function() c:Disconnect() end) end
    end
    _G.AstaManualConns = {}
    pcall(function() runService:UnbindFromRenderStep("AstaAssistDrive") end)
    pcall(function() runService:UnbindFromRenderStep("AstaThumbVis") end)

    -- الإعدادات
    local ASSIST_MAX_RANGE = 60     -- أقصى مسافة يلحق فيها
    local ASSIST_STOP_DIST = 2.4    -- يوقف على هذي المسافة من الخصم
    local RESUME_GAP = 0.7          -- لو الخصم ابتعد بزيادة يرجع يلحقه
    local TAKE_PAUSE = 0.7          -- وقفة قصيرة أول ما تاخذ القنبلة
    local GRAB_RANGE = 14           -- من هذي المسافة يبدأ الاوتو قراب
    local GRAB_COOLDOWN = 0.2
    local REQUIRE_TARGET_TOOL = false
    local LEAD_MAX = 0.35
    local JOY_BASE_X = 0.20         -- مكان الجويستيك على الشاشة
    local JOY_BASE_Y = 0.72

    local autoActive = false   -- الاسيست مطفي لين المستخدم يشغله
    local autoGrab = false     -- الاوتو قراب مطفي لين المستخدم يشغله
    AstaAssist.SetAssist = function(v) autoActive = v and true or false end
    AstaAssist.SetGrab = function(v) autoGrab = v and true or false end

    -- لو حطيت يدك على الجويستيك (أو WASD) الاسيست يوقف وأول ما تشيلها يكمل
    local manualTouches = {}
    local MOVE_KEYS = {
        Enum.KeyCode.W, Enum.KeyCode.A, Enum.KeyCode.S, Enum.KeyCode.D,
        Enum.KeyCode.Up, Enum.KeyCode.Down, Enum.KeyCode.Left, Enum.KeyCode.Right,
    }

    table.insert(_G.AstaManualConns, uis.InputBegan:Connect(function(input)
        if input.UserInputType ~= Enum.UserInputType.Touch then return end
        local cam = workspace.CurrentCamera
        if not cam then return end
        local vp = cam.ViewportSize
        if input.Position.X < vp.X * 0.5 and input.Position.Y > vp.Y * 0.35 then
            manualTouches[input] = true
        end
    end))

    table.insert(_G.AstaManualConns, uis.InputEnded:Connect(function(input)
        manualTouches[input] = nil
    end))

    local function manualHeld()
        for input in pairs(manualTouches) do
            local st = input.UserInputState
            if st == Enum.UserInputState.End or st == Enum.UserInputState.Cancel then
                manualTouches[input] = nil
            end
        end
        if next(manualTouches) ~= nil then return true end
        if not uis:GetFocusedTextBox() then
            for _, k in ipairs(MOVE_KEYS) do
                if uis:IsKeyDown(k) then return true end
            end
        end
        return false
    end

local function isTeammate(p)
    local myTeam = localPlayer.Team
    if myTeam and p.Team == myTeam then return true end
    if localPlayer.Neutral == false and p.Neutral == false and p.TeamColor == localPlayer.TeamColor then
        return true
    end
    return false
end

-- ================= التحكم بالحركة =================
local driveTarget, driveUntil = nil, 0
local driveDir = Vector3.zero

local function setDrive(pos)
    driveTarget = pos
    driveUntil = os.clock() + 0.2
end

runService:BindToRenderStep("AstaAssistDrive", Enum.RenderPriority.Input.Value + 1, function()
    driveDir = Vector3.zero
    if not autoActive or manualHeld() or not driveTarget or os.clock() > driveUntil then return end
    local char = localPlayer.Character
    local hum = char and char:FindFirstChildOfClass("Humanoid")
    local root = char and char:FindFirstChild("HumanoidRootPart")
    if not hum or not root or hum.Health <= 0 then return end
    local d = Vector3.new(driveTarget.X - root.Position.X, 0, driveTarget.Z - root.Position.Z)
    if d.Magnitude > 1.2 then
        driveDir = d.Unit
        hum:Move(d.Unit, false)
    else
        hum:Move(Vector3.zero, false)
    end
end)


    -- الجويستيك: بس يطلع (دايرة غامقة ثابتة) وهو يلحق، بدون حركة
    local joyGui = Instance.new("ScreenGui")
    joyGui.Name = "AstaJoyGui"
    joyGui.ResetOnSpawn = false
    joyGui.IgnoreGuiInset = true
    joyGui.DisplayOrder = 40
    joyGui.Parent = playerGui

    local joyDisc = Instance.new("Frame")
    joyDisc.AnchorPoint = Vector2.new(0.5, 0.5)
    joyDisc.BackgroundColor3 = Color3.fromRGB(40, 40, 40)
    joyDisc.BackgroundTransparency = 0.45
    joyDisc.BorderSizePixel = 0
    joyDisc.Visible = false
    joyDisc.Parent = joyGui
    Instance.new("UICorner", joyDisc).CornerRadius = UDim.new(1, 0)
    local discStroke = Instance.new("UIStroke", joyDisc)
    discStroke.Thickness = 2
    discStroke.Color = Color3.fromRGB(110, 110, 110)
    discStroke.Transparency = 0.5

    runService:BindToRenderStep("AstaThumbVis", Enum.RenderPriority.Input.Value + 2, function()
        local cam = workspace.CurrentCamera
        if not cam or not autoActive or manualHeld() or driveDir.Magnitude < 0.1 or os.clock() > driveUntil then
            joyDisc.Visible = false
            return
        end
        local vp = cam.ViewportSize
        local sz = 125 * vp.Y / 1080
        joyDisc.Size = UDim2.fromOffset(sz, sz)
        joyDisc.Position = UDim2.fromOffset(vp.X * JOY_BASE_X, vp.Y * JOY_BASE_Y)
        joyDisc.Visible = true
    end)

-- ================= اوتو قراب (ياخذ القنبلة لما تقرب حتى لو الخصم لافف وجهه) =================
local lastGrab = 0

local function findBomb(char)
    local fallback
    for _, it in ipairs(char:GetChildren()) do
        if it:IsA("Tool") then
            local n = it.Name:lower()
            if n:find("bomb") or it.Name:find("قنبل") then return it end
            fallback = fallback or it
        end
    end
    return fallback
end

local function tryGrab(targetChar, targetRoot, myChar, myRoot)
    local now = os.clock()
    if now - lastGrab < GRAB_COOLDOWN then return end
    lastGrab = now

    -- 1) يستخدم الأداة اللي بيدك
    for _, item in ipairs(myChar:GetChildren()) do
        if item:IsA("Tool") then pcall(function() item:Activate() end) end
    end

    -- 2) أزرار التفاعل (لو اللعبة تستخدمها)
    if fireproximityprompt then
        for _, d in ipairs(targetChar:GetDescendants()) do
            if d:IsA("ProximityPrompt") and d.Enabled then pcall(fireproximityprompt, d) end
        end
    end

    -- 3) لمس القنبلة/الخصم (لو اللعبة تنقلها باللمس)
    if not firetouchinterest then
        -- الاكسكيوتر ما يدعم firetouchinterest: نقرب شخصيتك لحد ما تلمس الخصم
        local flat = Vector3.new(targetRoot.Position.X - myRoot.Position.X, 0, targetRoot.Position.Z - myRoot.Position.Z)
        if flat.Magnitude > 1.6 then
            local step = math.min(flat.Magnitude - 1.4, 5)
            local dest = myRoot.Position + flat.Unit * step
            myRoot.CFrame = CFrame.new(dest) * (myRoot.CFrame - myRoot.CFrame.Position)
        end
    else
        local bomb = findBomb(targetChar)
        local parts = {targetRoot}
        local handle = bomb and bomb:FindFirstChild("Handle")
        if handle then table.insert(parts, handle) end
        for _, n in ipairs({"Torso", "UpperTorso", "Head", "Right Arm", "RightHand"}) do
            local pt = targetChar:FindFirstChild(n)
            if pt then table.insert(parts, pt) end
        end
        pcall(function()
            for _, pt in ipairs(parts) do
                firetouchinterest(myRoot, pt, 0)
                firetouchinterest(myRoot, pt, 1)
            end
        end)
    end
end

local holding = false
local hadTool = false
local pauseUntil = 0

_G.AstaConn = runService.Heartbeat:Connect(function()
    -- ولا ميزة مفعّلة؟ ما نسوي شي أبداً
    if not autoActive and not autoGrab then
        holding = false
        driveTarget = nil
        return
    end
    local manual = manualHeld()

    local character = localPlayer.Character
    if not character then return end

    local hasTool = false
    for _, item in ipairs(character:GetChildren()) do
        if item:IsA("Tool") then hasTool = true break end
    end
    -- أول ما تاخذ القنبلة (تظهر أداة بيدك): وقفة قصيرة ثم يمشي للخصم
    if hasTool and not hadTool then pauseUntil = os.clock() + TAKE_PAUSE end
    hadTool = hasTool

    local humanoid = character:FindFirstChild("Humanoid")
    local rootPart = character:FindFirstChild("HumanoidRootPart")
    if not humanoid or not rootPart or humanoid.Health <= 0 then return end

    local nearestTarget = nil
    local shortestDist = ASSIST_MAX_RANGE

    for _, p in ipairs(players:GetPlayers()) do
        if p ~= localPlayer and not isTeammate(p) and p.Character and p.Character:FindFirstChild("HumanoidRootPart") then
            local targetHumanoid = p.Character:FindFirstChild("Humanoid")
            if targetHumanoid and targetHumanoid.Health > 0 then
                local dist = (rootPart.Position - p.Character.HumanoidRootPart.Position).Magnitude
                if dist < shortestDist then
                    shortestDist = dist
                    nearestTarget = p.Character.HumanoidRootPart
                end
            end
        end
    end

    if not nearestTarget then
        holding = false
        driveTarget = nil
        return
    end

    local tPos = nearestTarget.Position
    local me = rootPart.Position
    local flat = Vector3.new(tPos.X - me.X, 0, tPos.Z - me.Z)
    local dist = flat.Magnitude

    -- اوتو قراب: لما تقرب منه ياخذ القنبلة
    if autoGrab and dist <= GRAB_RANGE then
        local tChar = nearestTarget.Parent
        if tChar and (not REQUIRE_TARGET_TOOL or findBomb(tChar)) then
            tryGrab(tChar, nearestTarget, character, rootPart)
        end
    end

    -- الملاحقة (الاسيست) تشتغل بس لو مفعّل وانت ما تحرك بيدك؛ الاوتو قراب فوق مستقل عنها
    if not autoActive or manual then
        holding = false
        driveTarget = nil
        return
    end

    -- وقفة ما بعد أخذ القنبلة
    if os.clock() < pauseUntil then
        holding = false
        driveTarget = nil
        driveUntil = 0
        return
    end

    -- الملاحقة (الجويستيك) تشتغل بس لو بيدك أداة؛ الاوتو قراب فوق يشتغل بكل الحالات
    if not hasTool then
        holding = false
        driveTarget = nil
        return
    end

    -- يوقف على ASSIST_STOP_DIST ولا يلزق، ويرجع يلحقه لو ابتعد
    if holding then
        if dist > ASSIST_STOP_DIST + RESUME_GAP then holding = false end
    elseif dist <= ASSIST_STOP_DIST then
        holding = true
    end

    if holding then
        driveTarget = nil
        return
    end

    -- يلحق مكان الخصم (مع توقع بسيط جداً لحركته وهو بعيد)
    local rv = nearestTarget.AssemblyLinearVelocity
    local vel = Vector3.new(rv.X, 0, rv.Z)
    if vel.Magnitude > 80 then vel = Vector3.zero end
    local lead = math.clamp(dist / 20, 0, LEAD_MAX)
    local offset = vel * lead
    if offset.Magnitude > 6 then offset = offset.Unit * 6 end
    setDrive(tPos + offset)
end)
end

FeaturesTab:Section({ Title = "الاوتو والاسيست" })

-- كل الميزات هنا مطفية افتراضياً وما تشتغل إلا لما تشغلها بنفسك
RegToggle(FeaturesTab, "autoMini", "الاوتو",
    "عرض واجهة مصغرة تحتوي على زر تشغيل/إيقاف الاوتو", false,
    function(v)
        AutoGui.Enabled = v and true or false
        if not v then
            FollowingState = false
            AutoBtn.Text = "تفعيل"
            AutoBtn.BackgroundColor3 = Color3.fromRGB(40, 180, 80)
        end
    end)

RegToggle(FeaturesTab, "assist", "اسيست Asta top1",
    "يلحق الخصم ويوقف قريب منه (مطفي لين تشغله)", false,
    function(v) AstaAssist.SetAssist(v) end)

RegToggle(FeaturesTab, "grab", "اوتو قراب",
    "ياخذ القنبلة لما تقرب من الخصم (مطفي لين تشغله)", false,
    function(v) AstaAssist.SetGrab(v) end)

local WallHopEnabled = false
local lastWallHop = 0
local UserInputService = game:GetService("UserInputService")

-- ول هوب: لما تكبس زر النط وانت قريب من حيط، ينطك من الحيط (ما يشتغل لحاله)
UserInputService.JumpRequest:Connect(function()
    if not WallHopEnabled then return end
    if tick() - lastWallHop < 0.15 then return end
    local char = LocalPlayer.Character
    local hum = char and char:FindFirstChildOfClass("Humanoid")
    local root = char and char:FindFirstChild("HumanoidRootPart")
    if not hum or not root or hum.Health <= 0 then return end

    local params = RaycastParams.new()
    params.FilterType = Enum.RaycastFilterType.Exclude
    params.FilterDescendantsInstances = {char}

    -- نفحص 8 اتجاهات حولك ونختار أقرب حيط
    local best, bestDist = nil, 3.5
    for i = 0, 7 do
        local ang = math.rad(i * 45)
        local dir = Vector3.new(math.cos(ang), 0, math.sin(ang))
        local hit = workspace:Raycast(root.Position, dir * 3.5, params)
        if hit and hit.Instance.CanCollide and math.abs(hit.Normal.Y) < 0.35 then
            local d = (hit.Position - root.Position).Magnitude
            if d < bestDist then best, bestDist = hit, d end
        end
    end
    if not best then return end

    lastWallHop = tick()
    local power = hum.UseJumpPower and hum.JumpPower or math.sqrt(2 * workspace.Gravity * hum.JumpHeight)
    local n = Vector3.new(best.Normal.X, 0, best.Normal.Z)
    if n.Magnitude > 0 then n = n.Unit end
    root.AssemblyLinearVelocity = Vector3.new(n.X * 6, power, n.Z * 6)
    hum:ChangeState(Enum.HumanoidStateType.Jumping)
end)

FeaturesTab:Section({ Title = "حركة اللاعب" })
RegToggle(FeaturesTab, "wallhop", "ول هوب (Wall Hop)",
    "لما تكبس زر النط وانت قريب من حيط ينطك منه (ما يشتغل لحاله)", false,
    function(v) WallHopEnabled = v and true or false end)

local function GetClosestPlayer()
    local Closest = nil
    local ShortestDistance = math.huge
    local MyChar = LocalPlayer.Character
    if not MyChar or not MyChar:FindFirstChild("HumanoidRootPart") then return nil end
    local MyPos = MyChar.HumanoidRootPart.Position

    for _, v in pairs(Players:GetPlayers()) do
        if v ~= LocalPlayer and v.Character and v.Character:FindFirstChild("HumanoidRootPart") and v.Character:FindFirstChild("Humanoid") and v.Character.Humanoid.Health > 0 then
            local Dist = (v.Character.HumanoidRootPart.Position - MyPos).Magnitude
            if Dist < ShortestDistance then
                ShortestDistance = Dist
                Closest = v.Character
            end
        end
    end
    return Closest
end

RunService.RenderStepped:Connect(function()
    if AutoGui.Enabled and FollowingState then
        local MyChar = LocalPlayer.Character
        if MyChar then
            local HasTool = MyChar:FindFirstChildOfClass("Tool")
            if HasTool then
                local TargetChar = GetClosestPlayer()
                if TargetChar and TargetChar:FindFirstChild("HumanoidRootPart") and MyChar:FindFirstChild("Humanoid") then
                    MyChar.Humanoid:MoveTo(TargetChar.HumanoidRootPart.Position)
                end
            end
        end
    end
end)

local EffectsTab = Window:Tab({ Title = "تاثيرات القتل", Icon = "wand" })

local kfxNames = {}
for i, e in ipairs(AstaX.KFX.list) do kfxNames[i] = e.en .. " | " .. e.ar end

local function setKillFx(v)
    if type(v) == "table" then v = v.Title or v[1] end
    for i, n in ipairs(kfxNames) do
        if n == v then AstaX.KFX.current = i break end
    end
end
Settings.register("kfx", kfxNames[1], setKillFx, "dropdown")
Settings.items["kfx"].ui = EffectsTab:Dropdown({
    Title = "تأثير القتل",
    Desc = "يطلع التأثير على اللي تقتله (يبان عندك بس)",
    Values = kfxNames,
    Value = kfxNames[1],
    Callback = function(v)
        if type(v) == "table" then v = v.Title or v[1] end
        Settings.set("kfx", v)
    end
})

local QualityTab = Window:Tab({ Title = "الجودات", Icon = "monitor" })
QualityTab:Section({ Title = "إعدادات الرؤية والأداء" })

QualityTab:Button({
    Title = "جودة تخفيف الاق (Anti-Lag)",
    Desc = "تقليل المواد والظلال ويرفع حد الفريمات لإزالة التقطيع",
    Callback = function()
        pcall(function()
            for _, v in pairs(workspace:GetDescendants()) do
                if v:IsA("BasePart") then
                    v.Material = Enum.Material.SmoothPlastic
                elseif v:IsA("Decal") or v:IsA("Texture") then
                    v:Destroy()
                end
            end
            Lighting.GlobalShadows = false
        end)
        pcall(function() if setfpscap then setfpscap(999) end end)
        pcall(function() settings().Rendering.QualityLevel = Enum.QualityLevel.Level01 end)
        WindUI:Notify({ Title = "تخفيف الاق", Content = "تمت إزالة التأثيرات لتنعيم اللعبة!", Duration = 3 })
    end
})

RegToggle(QualityTab, "cine", "جودة سينمائية للماب",
    "إضاءة وغروب وبلوم (تظهر عندك بس)", false,
    function(v)
        if v then AstaX.CINE.apply() else AstaX.CINE.restore() end
    end)

RegToggle(QualityTab, "bombglow", "القنبلة تلمع",
    "القنبلة اللي بيدك تلمع أحمر/أبيض (تظهر عندك بس)", false,
    function(v) AstaX.BOMBSKIN.set(v and true or false) end)

-- ================= القتال: جودة سوداء / كام لوك / هيت بوكس =================
QualityTab:Section({ Title = "جودة سوداء" })

local DarkQ = {saved = nil, cc = nil, on = false}
function DarkQ.set(on)
    if on == DarkQ.on then return end
    DarkQ.on = on
    pcall(function()
        if on then
            DarkQ.saved = {
                Ambient = Lighting.Ambient, OutdoorAmbient = Lighting.OutdoorAmbient,
                Brightness = Lighting.Brightness, ClockTime = Lighting.ClockTime,
                FogColor = Lighting.FogColor, FogEnd = Lighting.FogEnd,
                ColorShift_Top = Lighting.ColorShift_Top, ColorShift_Bottom = Lighting.ColorShift_Bottom,
                GlobalShadows = Lighting.GlobalShadows,
            }
            Lighting.Brightness = math.max(0.8, Lighting.Brightness * 0.6)
            Lighting.Ambient = Color3.fromRGB(70, 70, 80)
            Lighting.OutdoorAmbient = Color3.fromRGB(70, 70, 80)
            Lighting.ColorShift_Top = Color3.fromRGB(0, 0, 0)
            Lighting.ColorShift_Bottom = Color3.fromRGB(0, 0, 0)
            local cc = Instance.new("ColorCorrectionEffect")
            cc.Name = "Top1AstaDark"
            cc.Brightness = -0.06
            cc.Contrast = 0.18
            cc.Saturation = -0.18
            cc.TintColor = Color3.fromRGB(215, 215, 228)
            cc.Parent = Lighting
            DarkQ.cc = cc
        else
            local sv = DarkQ.saved
            if sv then for k, v in pairs(sv) do pcall(function() Lighting[k] = v end) end end
            if DarkQ.cc then DarkQ.cc:Destroy() DarkQ.cc = nil end
        end
    end)
end

RegToggle(QualityTab, "darkq", "جودة سوداء",
    "يخلي الماب أغمق شوي (مو سواد كامل) - تظهر عندك بس", false,
    function(v) DarkQ.set(v and true or false) end)

FeaturesTab:Section({ Title = "كام لوك" })

local CamLock = {on = false, smooth = 100, part = "Head", conn = nil}
local function clTarget()
    local myChar = LocalPlayer.Character
    local myRoot = myChar and myChar:FindFirstChild("HumanoidRootPart")
    if not myRoot then return nil end
    local best, bd = nil, math.huge
    for _, p in ipairs(Players:GetPlayers()) do
        if p ~= LocalPlayer and p.Character and not (p.Team ~= nil and p.Team == LocalPlayer.Team and not p.Neutral) then
            local h = p.Character:FindFirstChildOfClass("Humanoid")
            local part = p.Character:FindFirstChild(CamLock.part) or p.Character:FindFirstChild("HumanoidRootPart")
            if h and h.Health > 0 and part then
                local d = (part.Position - myRoot.Position).Magnitude
                if d < bd then bd, best = d, part end
            end
        end
    end
    return best
end
function CamLock.set(on)
    CamLock.on = on
    pcall(function() RunService:UnbindFromRenderStep("Top1AstaCamLock") end)
    if on then
        RunService:BindToRenderStep("Top1AstaCamLock", Enum.RenderPriority.Camera.Value + 1, function()
            local cam = workspace.CurrentCamera
            local t = clTarget()
            if not (cam and t) then return end
            local goal = CFrame.lookAt(cam.CFrame.Position, t.Position)
            local a = math.clamp(CamLock.smooth / 100, 0.05, 1)
            cam.CFrame = (a >= 1) and goal or cam.CFrame:Lerp(goal, a)
        end)
    end
end

RegToggle(FeaturesTab, "camlock", "كام لوك",
    "الكاميرا تظل تطالع على أقرب خصم (ما تثبّت على زميلك بالفريق)", false,
    function(v) CamLock.set(v and true or false) end)

Settings.register("camlockSmooth", 100, function(v) CamLock.smooth = tonumber(v) or 100 end, "slider")
Settings.items["camlockSmooth"].ui = FeaturesTab:Slider({
    Title = "قوة التثبيت",
    Desc = "100 = ثابت تماماً، أقل = أنعم وأطبيعي",
    Value = { Min = 5, Max = 100, Default = 100 },
    Callback = function(v) Settings.set("camlockSmooth", tonumber(v) or 100) end
})

Settings.register("camlockPart", "Head", function(v) CamLock.part = (v == "HumanoidRootPart") and "HumanoidRootPart" or "Head" end, "dropdown")
Settings.items["camlockPart"].ui = FeaturesTab:Dropdown({
    Title = "مكان التثبيت",
    Values = { "Head", "HumanoidRootPart" },
    Value = "Head",
    Callback = function(v) Settings.set("camlockPart", v) end
})

FeaturesTab:Section({ Title = "هيت بوكس (Hitbox)" })

local Hitbox = {on = false, size = 20, orig = {}, conn = nil, acc = 0}
local function hbRestore()
    for part, o in pairs(Hitbox.orig) do
        if part and part.Parent then
            pcall(function()
                part.Size = o.Size
                part.Transparency = o.Transparency
                part.CanCollide = o.CanCollide
            end)
        end
    end
    Hitbox.orig = {}
end
local function hbTeammate(p)
    local myTeam = LocalPlayer.Team
    if myTeam and p.Team == myTeam then return true end
    if LocalPlayer.Neutral == false and p.Neutral == false and p.TeamColor == LocalPlayer.TeamColor then return true end
    return false
end

-- لمس حقيقي من بعيد: لما اللاعب يدخل مدى الهيت بوكس يرسل لمس + تفعيل الأداة اللي بيدك
local hbLastHit = 0
local function hbReach(myChar, myRoot, tChar, tRoot)
    if os.clock() - hbLastHit < 0.12 then return end
    hbLastHit = os.clock()
    local tool
    for _, it in ipairs(myChar:GetChildren()) do
        if it:IsA("Tool") then tool = it break end
    end
    if not tool then return end
    pcall(function() tool:Activate() end)
    if not firetouchinterest then return end
    local handle = tool:FindFirstChild("Handle")
    local sources = {myRoot}
    if handle then table.insert(sources, handle) end
    local targets = {tRoot}
    for _, n in ipairs({"Torso", "UpperTorso", "Head"}) do
        local pt = tChar:FindFirstChild(n)
        if pt then table.insert(targets, pt) end
    end
    pcall(function()
        for _, a in ipairs(sources) do
            for _, b in ipairs(targets) do
                firetouchinterest(a, b, 0)
                firetouchinterest(a, b, 1)
            end
        end
    end)
end

function Hitbox.set(on)
    Hitbox.on = on
    if Hitbox.conn then Hitbox.conn:Disconnect() Hitbox.conn = nil end
    if on then
        Hitbox.conn = RunService.Heartbeat:Connect(function(dt)
            Hitbox.acc = Hitbox.acc + dt
            if Hitbox.acc < 0.1 then return end
            Hitbox.acc = 0
            local s = Vector3.new(Hitbox.size, Hitbox.size, Hitbox.size)
            local myChar = LocalPlayer.Character
            local myRoot = myChar and myChar:FindFirstChild("HumanoidRootPart")
            for _, p in ipairs(Players:GetPlayers()) do
                if p ~= LocalPlayer and p.Character and not hbTeammate(p) then
                    local r = p.Character:FindFirstChild("HumanoidRootPart")
                    local hum = p.Character:FindFirstChildOfClass("Humanoid")
                    if r and hum and hum.Health > 0 then
                        if not Hitbox.orig[r] then
                            Hitbox.orig[r] = {Size = r.Size, Transparency = r.Transparency, CanCollide = r.CanCollide}
                        end
                        pcall(function()
                            r.Size = s
                            r.Transparency = 0.75
                            r.CanCollide = false
                        end)
                        -- داخل المدى؟ يضرب من بعيد
                        if myRoot and (myRoot.Position - r.Position).Magnitude <= Hitbox.size + 4 then
                            hbReach(myChar, myRoot, p.Character, r)
                        end
                    end
                end
            end
        end)
    else
        hbRestore()
    end
end

RegToggle(FeaturesTab, "hitbox", "هيت بوكس",
    "يكبّر مربع الإصابة، وأول ما لاعب يدخل المدى يلمسه ويفعّل الأداة اللي بيدك من بعيد (لازم تكون ماسك القنبلة)", false,
    function(v) Hitbox.set(v and true or false) end)

Settings.register("hitboxSize", 20, function(v)
    Hitbox.size = math.clamp(tonumber(v) or 20, 2, 100)
end, "slider")
Settings.items["hitboxSize"].ui = FeaturesTab:Slider({
    Title = "حجم الهيت بوكس",
    Desc = "حدد الحجم اللي تبيه",
    Value = { Min = 2, Max = 100, Default = 20 },
    Callback = function(v) Settings.set("hitboxSize", tonumber(v) or 20) end
})


-- ================= المظهر: مميزات بصرية عندك بس (ما تأثر على السيرفر) =================
local VisTab = Window:Tab({ Title = "المظهر والتأثيرات", Icon = "eye" })
VisTab:Section({ Title = "إظهار اللاعبين" })

local VIS = {}
do
    local espOn, espConn, espAcc = false, nil, 0
    local function espClear()
        for _, p in ipairs(Players:GetPlayers()) do
            if p.Character then
                local h = p.Character:FindFirstChild("Top1AstaESP")
                if h then h:Destroy() end
            end
        end
    end
    function VIS.esp(on)
        espOn = on
        if espConn then espConn:Disconnect() espConn = nil end
        if on then
            espConn = RunService.Heartbeat:Connect(function(dt)
                espAcc = espAcc + dt
                if espAcc < 0.5 then return end
                espAcc = 0
                for _, p in ipairs(Players:GetPlayers()) do
                    if p ~= LocalPlayer and p.Character and not p.Character:FindFirstChild("Top1AstaESP") then
                        pcall(function()
                            local h = Instance.new("Highlight")
                            h.Name = "Top1AstaESP"
                            h.FillColor = Color3.fromRGB(255, 60, 60)
                            h.FillTransparency = 0.65
                            h.OutlineColor = Color3.new(1, 1, 1)
                            h.DepthMode = Enum.HighlightDepthMode.AlwaysOnTop
                            h.Parent = p.Character
                        end)
                    end
                end
            end)
        else
            espClear()
        end
    end

    -- X-Ray
    local xr = {}
    function VIS.xray(on)
        if on then
            task.spawn(function()
                local n = 0
                for _, v in ipairs(workspace:GetDescendants()) do
                    if v:IsA("BasePart") and not v:IsDescendantOf(workspace.CurrentCamera) then
                        local isChar = false
                        for _, p in ipairs(Players:GetPlayers()) do
                            if p.Character and v:IsDescendantOf(p.Character) then isChar = true break end
                        end
                        if not isChar and v.Transparency < 1 then
                            xr[v] = true
                            pcall(function() v.LocalTransparencyModifier = 0.55 end)
                        end
                    end
                    n = n + 1
                    if n % 400 == 0 then task.wait() end
                end
            end)
        else
            for v in pairs(xr) do
                pcall(function() v.LocalTransparencyModifier = 0 end)
            end
            xr = {}
        end
    end

    -- Trails
    local trConn, trObjs = nil, {}
    local function trClear()
        for _, o in ipairs(trObjs) do pcall(function() o:Destroy() end) end
        trObjs = {}
    end
    local function trBuild()
        trClear()
        local c = LocalPlayer.Character
        local r = c and c:FindFirstChild("HumanoidRootPart")
        if not r then return end
        local a0 = Instance.new("Attachment") a0.Position = Vector3.new(0, 1, 0) a0.Parent = r
        local a1 = Instance.new("Attachment") a1.Position = Vector3.new(0, -1.5, 0) a1.Parent = r
        local t = Instance.new("Trail")
        t.Attachment0, t.Attachment1 = a0, a1
        t.Lifetime = 0.6
        t.LightEmission = 1
        t.Transparency = NumberSequence.new(0.1, 1)
        t.Color = ColorSequence.new({
            ColorSequenceKeypoint.new(0, Color3.fromRGB(255, 70, 70)),
            ColorSequenceKeypoint.new(0.5, Color3.fromRGB(120, 90, 255)),
            ColorSequenceKeypoint.new(1, Color3.fromRGB(70, 200, 255)),
        })
        t.Parent = r
        trObjs = {a0, a1, t}
    end
    function VIS.trails(on)
        if trConn then trConn:Disconnect() trConn = nil end
        if on then
            trBuild()
            trConn = LocalPlayer.CharacterAdded:Connect(function()
                task.wait(0.6)
                trBuild()
            end)
        else
            trClear()
        end
    end

    -- Jump circle
    local jcConn, wasJump = nil, false
    function VIS.jumpCircle(on)
        if jcConn then jcConn:Disconnect() jcConn = nil end
        if on then
            jcConn = RunService.Heartbeat:Connect(function()
                local c = LocalPlayer.Character
                local h = c and c:FindFirstChildOfClass("Humanoid")
                local r = c and c:FindFirstChild("HumanoidRootPart")
                if not (h and r) then return end
                local j = h:GetState() == Enum.HumanoidStateType.Jumping
                if j and not wasJump then
                    pcall(function()
                        local ring = Instance.new("Part")
                        ring.Anchored, ring.CanCollide, ring.CanQuery, ring.CanTouch = true, false, false, false
                        ring.Material = Enum.Material.Neon
                        ring.Color = Color3.fromRGB(150, 110, 255)
                        ring.Shape = Enum.PartType.Cylinder
                        ring.Size = Vector3.new(0.2, 2, 2)
                        ring.CFrame = CFrame.new(r.Position - Vector3.new(0, h.HipHeight + r.Size.Y / 2 - 0.1, 0)) * CFrame.Angles(0, 0, math.rad(90))
                        ring.Parent = workspace
                        TweenService:Create(ring, TweenInfo.new(0.6), {Size = Vector3.new(0.2, 12, 12), Transparency = 1}):Play()
                        Debris:AddItem(ring, 0.7)
                    end)
                end
                wasJump = j
            end)
        end
    end

    -- China hat
    local hat, hatConn = nil, nil
    local function hatBuild()
        if hat then hat:Destroy() hat = nil end
        local c = LocalPlayer.Character
        local head = c and c:FindFirstChild("Head")
        if not head then return end
        pcall(function()
            hat = Instance.new("Part")
            hat.Name = "Top1AstaHat"
            hat.Size = Vector3.new(3, 0.7, 3)
            hat.Material = Enum.Material.Neon
            hat.Color = Color3.fromRGB(255, 200, 60)
            hat.CanCollide, hat.CanQuery, hat.CanTouch, hat.Massless = false, false, false, true
            local m = Instance.new("SpecialMesh", hat)
            m.MeshId = "rbxassetid://1033714"
            m.Scale = Vector3.new(1.6, 0.9, 1.6)
            hat.CFrame = head.CFrame * CFrame.new(0, 0.9, 0)
            local w = Instance.new("WeldConstraint")
            w.Part0, w.Part1 = head, hat
            w.Parent = hat
            hat.Parent = c
        end)
    end
    function VIS.hat(on)
        if hatConn then hatConn:Disconnect() hatConn = nil end
        if on then
            hatBuild()
            hatConn = LocalPlayer.CharacterAdded:Connect(function()
                task.wait(0.6)
                hatBuild()
            end)
        elseif hat then
            hat:Destroy() hat = nil
        end
    end

    -- Name protect (محلي بس)
    local origName = nil
    function VIS.nameProtect(on)
        local c = LocalPlayer.Character
        local h = c and c:FindFirstChildOfClass("Humanoid")
        if not h then return end
        pcall(function()
            if on then
                origName = origName or h.DisplayName
                h.DisplayName = "top 1 Asta"
            elseif origName then
                h.DisplayName = origName
            end
        end)
    end

    -- Saturation + FOV
    local satCC = nil
    function VIS.saturation(v)
        v = (tonumber(v) or 0) / 100
        if not satCC then
            satCC = Instance.new("ColorCorrectionEffect")
            satCC.Name = "Top1AstaSat"
            satCC.Parent = Lighting
        end
        satCC.Saturation = v
    end
    function VIS.fov(v)
        pcall(function() workspace.CurrentCamera.FieldOfView = tonumber(v) or 70 end)
    end
end

RegToggle(VisTab, "esp", "ESP اللاعبين", "يلوّن اللاعبين ويظهرهم من ورا الجدران (عندك بس)", false,
    function(v) VIS.esp(v and true or false) end)
RegToggle(VisTab, "xray", "X-Ray", "يخلي الجدران والأشياء شبه شفافة (عندك بس)", false,
    function(v) VIS.xray(v and true or false) end)

VisTab:Section({ Title = "تأثيرات" })
RegToggle(VisTab, "trails", "Trails", "أثر ملوّن وراك وانت تمشي", false,
    function(v) VIS.trails(v and true or false) end)
RegToggle(VisTab, "jumpcircle", "Jump Circle", "دائرة تطلع تحتك لما تنط", false,
    function(v) VIS.jumpCircle(v and true or false) end)
RegToggle(VisTab, "chinahat", "China Hat", "قبعة مضيئة فوق راسك (تظهر عندك بس)", false,
    function(v) VIS.hat(v and true or false) end)
RegToggle(VisTab, "nameprotect", "Name Protect", "يغيّر اسمك فوق شخصيتك عندك بس", false,
    function(v) VIS.nameProtect(v and true or false) end)

QualityTab:Section({ Title = "الشاشة والألوان" })
Settings.register("saturation", 0, function(v) VIS.saturation(v) end, "slider")
Settings.items["saturation"].ui = QualityTab:Slider({
    Title = "تشبّع الألوان",
    Desc = "0 = عادي، أعلى = ألوان أقوى، أقل = باهتة",
    Value = { Min = -100, Max = 100, Default = 0 },
    Callback = function(v) Settings.set("saturation", tonumber(v) or 0) end
})
Settings.register("fovSlider", 70, function(v) VIS.fov(v) end, "slider")
Settings.items["fovSlider"].ui = QualityTab:Slider({
    Title = "مجال الرؤية (FOV)",
    Value = { Min = 30, Max = 160, Default = 70 },
    Callback = function(v) Settings.set("fovSlider", tonumber(v) or 70) end
})


-- ================= الكتالوج: شيرتات وبناطيل مدفوعة بس (يظهر عندك بس) =================
local Catalog = {}
do
    local MarketplaceService = game:GetService("MarketplaceService")
    local ASSET_FIELD = {[18]="Face", [11]="Shirt", [12]="Pants", [2]="GraphicTShirt",
        [17]="Head", [27]="Torso", [28]="RightArm", [29]="LeftArm", [30]="LeftLeg", [31]="RightLeg"}
    local ASSET_ACC = {[8]="Hat", [41]="Hair", [42]="Face", [43]="Neck", [44]="Shoulder",
        [45]="Front", [46]="Back", [47]="Waist"}
    local ASSET_LAYERED = {[64]="TShirt", [65]="Shirt", [66]="Pants", [67]="Jacket", [68]="Sweater",
        [69]="Shorts", [70]="LeftShoe", [71]="RightShoe", [72]="DressSkirt"}

    -- يلبّس غرض كتالوج (يظهر عندك بس)
    function Wear.equip(item)
        local at = item.assetType
        if not at then
            local ok, info = pcall(function() return MarketplaceService:GetProductInfo(item.id, Enum.InfoType.Asset) end)
            if ok and info then at = info.AssetTypeId end
        end
        if not at then return false, "ما عرفت نوع الغرض" end
        if ASSET_ACC[at] then
            Wear.acc[item.id] = {id = item.id, kind = ASSET_ACC[at]}
        elseif ASSET_LAYERED[at] then
            Wear.acc[item.id] = {id = item.id, kind = ASSET_LAYERED[at], layered = true}
        elseif ASSET_FIELD[at] then
            Wear.fields[ASSET_FIELD[at]] = item.id
        else
            return false, "هذا النوع ما ينلبس"
        end
        if Wear.apply() then return true end
        return false, "فشل التلبيس، جرّب غرض ثاني"
    end

    local HOSTS = {"https://catalog.roblox.com", "https://catalog.roproxy.com"}
    local function getJson(path)
        for _, h in ipairs(HOSTS) do
            local ok, res = pcall(function() return game:HttpGet(h .. path) end)
            if ok and res and #res > 2 then
                local ok2, data = pcall(function() return HttpService:JSONDecode(res) end)
                if ok2 and type(data) == "table" and not data.errors then return data end
            end
        end
        return nil
    end

    local gui, grid, status, searchBox, moreBtn, linkBox
    local keyword, cursor, loading = "", nil, false
    local sortType = 2          -- 2 مبيعات، 5 الأغلى، 3 الأحدث
    local seen = {}
    local sortBtns, catBtns, styleBtns = {}, {}, {}
    local typeCache = {}
    local subIds, curCat, curStyle = nil, 1, 1

    -- الأقسام: شيرتات / بناطيل / تيشيرتات (نوع الغرض بالروبلوكس)
    local cats = {
        {"👕 شيرتات", {"ClassicShirts", "Shirts"}, 11},
        {"👖 بناطيل", {"ClassicPants", "Pants"}, 12},
        {"🎽 تيشيرتات", {"ClassicTShirts", "TShirts"}, 2},
    }
    -- ستايلات البحث (تضغط وتطلع لك أغراض بهالستايل)
    local styles = {
        {"الكل", ""},
        {"🔥 تعريق", "tryhard"},
        {"😎 برو", "pro"},
        {"🖤 أسود", "black"},
        {"💀 ايمو", "emo"},
        {"🧢 ستريت", "streetwear"},
        {"✨ درِب", "drip"},
        {"🥷 تكتيكال", "techwear"},
        {"⚔️ ساموراي", "samurai"},
    }
    local sortDefs = {{"🔥 مبيعاً", 2}, {"💰 الأغلى", 5}, {"🆕 الأحدث", 3}}

    local function notify(t)
        pcall(function() WindUI:Notify({ Title = "الكتالوج", Content = t, Duration = 3 }) end)
    end

    local function getSubId()
        if not subIds then
            local d = getJson("/v1/subcategories")
            if type(d) == "table" then subIds = d end
        end
        if subIds then
            for _, k in ipairs(cats[curCat][2]) do
                if type(subIds[k]) == "number" then return subIds[k] end
            end
        end
        return nil
    end

    local function addItem(it, price)
        local btn = mk("TextButton", {Text = "", BackgroundColor3 = Color3.fromRGB(38, 38, 46), AutoButtonColor = true,
            Size = UDim2.fromOffset(104, 128), BorderSizePixel = 0}, grid)
        mk("UICorner", {CornerRadius = UDim.new(0, 8)}, btn)
        mk("ImageLabel", {BackgroundTransparency = 1, Position = UDim2.fromOffset(6, 6), Size = UDim2.fromOffset(92, 92),
            Image = "rbxthumb://type=Asset&id=" .. it.id .. "&w=150&h=150"}, btn)
        mk("TextLabel", {BackgroundTransparency = 1, Position = UDim2.fromOffset(4, 100), Size = UDim2.fromOffset(96, 26),
            Text = tostring(it.name or "?"), TextColor3 = Color3.new(1, 1, 1), TextScaled = true, Font = Enum.Font.GothamMedium}, btn)
        local tag = mk("TextLabel", {BackgroundColor3 = Color3.fromRGB(30, 120, 60), Position = UDim2.fromOffset(6, 6),
            Size = UDim2.fromOffset(52, 16), Text = "R$ " .. tostring(price or "?"), TextColor3 = Color3.new(1, 1, 1),
            TextScaled = true, Font = Enum.Font.GothamBold, BorderSizePixel = 0, ZIndex = 3}, btn)
        mk("UICorner", {CornerRadius = UDim.new(0, 6)}, tag)
        btn.MouseButton1Click:Connect(function()
            task.spawn(function()
                -- نلبّس حسب القسم المختار (شيرت/بنطلون/تيشيرت) حتى لو الموقع ما رجّع النوع
                local ok, err = Wear.equip({id = it.id, assetType = it.assetType or typeCache[it.id] or cats[curCat][3]})
                notify(ok and ("تم تلبيس: " .. tostring(it.name)) or (err or "فشل"))
            end)
        end)
    end

    local function buildPath(safe, subId)
        local path
        if safe then
            path = "/v1/search/items/details?Limit=30&SortType=" .. (sortType == 3 and 3 or 2)
                .. "&MinPrice=1&salesTypeFilter=1&IncludeNotForSale=false&Keyword=" .. HttpService:UrlEncode(keyword)
        else
            path = "/v1/search/items/details?Limit=30&SortType=" .. sortType
                .. "&MinPrice=1&salesTypeFilter=1&IncludeNotForSale=false&Keyword=" .. HttpService:UrlEncode(keyword)
            if sortType == 5 then path = path .. "&MaxPrice=5000" end
            if subId then path = path .. "&Subcategory=" .. subId end
        end
        if cursor then path = path .. "&Cursor=" .. HttpService:UrlEncode(cursor) end
        return path
    end

    -- لو الموقع ما رجّع نوع الغرض نسأل عنه (بالتوازي) عشان ما يطلع لك غير شيرتات/بناطيل
    local function resolveTypes(list)
        local pending = 0
        for _, it in ipairs(list) do
            if it.id and not it.assetType and typeCache[it.id] == nil then
                pending = pending + 1
                task.spawn(function()
                    local ok, info = pcall(function() return MarketplaceService:GetProductInfo(it.id, Enum.InfoType.Asset) end)
                    typeCache[it.id] = (ok and info and info.AssetTypeId) or false
                    pending = pending - 1
                end)
            end
        end
        local t0 = os.clock()
        while pending > 0 and os.clock() - t0 < 10 do task.wait(0.1) end
    end

    local function passes(it, price, trustSub)
        if not it.id or seen[it.id] then return false end
        if it.itemType == "Bundle" then return false end
        if not price or price <= 0 or it.priceStatus == "Free" then return false end
        local at = it.assetType or typeCache[it.id]
        local want = cats[curCat][3]
        if at then return at == want end
        return trustSub and true or false
    end

    local function load(reset)
        if loading then return end
        loading = true
        if reset then
            cursor = nil
            seen = {}
            for _, c in ipairs(grid:GetChildren()) do
                if c:IsA("GuiButton") then c:Destroy() end
            end
        end
        status.Text = "جاري التحميل..."
        local subId = getSubId()
        local count, tries, failed = 0, 0, false
        repeat
            tries = tries + 1
            local data = getJson(buildPath(false, subId))
            local usedSub = subId ~= nil and data ~= nil
            if not data then
                data = getJson(buildPath(true, nil))
                usedSub = false
            end
            if not data or not data.data then
                failed = true
                break
            end
            if not usedSub then resolveTypes(data.data) end
            for _, it in ipairs(data.data) do
                local price = tonumber(it.price) or tonumber(it.lowestPrice)
                if passes(it, price, usedSub) then
                    seen[it.id] = true
                    addItem(it, price)
                    count = count + 1
                end
            end
            cursor = data.nextPageCursor
        until count >= 18 or not cursor or tries >= 6
        if failed and count == 0 then
            status.Text = "ما قدرت أتصل بالكتالوج"
        else
            status.Text = count == 0 and "ما فيه نتائج، جرّب ستايل أو كلمة ثانية" or ""
        end
        moreBtn.Visible = cursor ~= nil
        loading = false
    end

    local function parseLink(raw)
        raw = tostring(raw or "")
        local id = raw:match("/catalog/(%d+)") or raw:match("/library/(%d+)") or raw:match("[?&]id=(%d+)")
            or raw:match("rbxassetid://(%d+)") or raw:match("^%s*(%d+)%s*$")
        return id and tonumber(id)
    end

    local function recolor()
        for _, s in ipairs(sortBtns) do
            s.btn.BackgroundColor3 = (s.mode == sortType) and Color3.fromRGB(200, 120, 20) or Color3.fromRGB(80, 60, 40)
        end
        for i, b in ipairs(catBtns) do
            b.BackgroundColor3 = (i == curCat) and Color3.fromRGB(40, 140, 80) or Color3.fromRGB(30, 80, 55)
        end
        for i, b in ipairs(styleBtns) do
            b.BackgroundColor3 = (i == curStyle) and Color3.fromRGB(110, 80, 200) or Color3.fromRGB(52, 40, 90)
        end
    end

    local function build()
        gui = mk("ScreenGui", {Name = "Top1AstaCatalog", ResetOnSpawn = false, DisplayOrder = 50}, CoreGui)
        local frame = mk("Frame", {Size = UDim2.fromOffset(520, 380), Position = UDim2.new(0.5, -260, 0.5, -190),
            BackgroundColor3 = Color3.fromRGB(24, 24, 30), BorderSizePixel = 0, Active = true, Draggable = true}, gui)
        mk("UICorner", {CornerRadius = UDim.new(0, 12)}, frame)
        mk("TextLabel", {BackgroundTransparency = 1, Position = UDim2.fromOffset(14, 8), Size = UDim2.fromOffset(200, 24),
            Text = "الكتالوج", TextColor3 = Color3.new(1, 1, 1), Font = Enum.Font.GothamBold, TextSize = 18,
            TextXAlignment = Enum.TextXAlignment.Left}, frame)
        local close = mk("TextButton", {Text = "X", Size = UDim2.fromOffset(28, 28), Position = UDim2.new(1, -36, 0, 6),
            BackgroundColor3 = Color3.fromRGB(150, 40, 40), TextColor3 = Color3.new(1, 1, 1), Font = Enum.Font.GothamBold,
            TextSize = 14, BorderSizePixel = 0}, frame)
        mk("UICorner", {CornerRadius = UDim.new(0, 8)}, close)
        close.MouseButton1Click:Connect(function() gui.Enabled = false end)
        local reset = mk("TextButton", {Text = "↩ إرجاع سكني", Size = UDim2.fromOffset(100, 28), Position = UDim2.new(1, -146, 0, 6),
            BackgroundColor3 = Color3.fromRGB(60, 60, 75), TextColor3 = Color3.new(1, 1, 1), Font = Enum.Font.GothamMedium,
            TextSize = 12, BorderSizePixel = 0}, frame)
        mk("UICorner", {CornerRadius = UDim.new(0, 8)}, reset)
        reset.MouseButton1Click:Connect(function() resetAvatar() end)

        for i, sd in ipairs(sortDefs) do
            local sb = mk("TextButton", {Text = sd[1], Size = UDim2.fromOffset(78, 24), Position = UDim2.fromOffset(100 + (i - 1) * 84, 8),
                BackgroundColor3 = Color3.fromRGB(80, 60, 40), TextColor3 = Color3.new(1, 1, 1), Font = Enum.Font.GothamMedium,
                TextSize = 12, BorderSizePixel = 0}, frame)
            mk("UICorner", {CornerRadius = UDim.new(1, 0)}, sb)
            table.insert(sortBtns, {btn = sb, mode = sd[2]})
            sb.MouseButton1Click:Connect(function()
                sortType = sd[2]
                recolor()
                task.spawn(load, true)
            end)
        end

        searchBox = mk("TextBox", {PlaceholderText = "ابحث عن شيرت أو بنطلون...", Text = "", ClearTextOnFocus = false,
            Size = UDim2.new(1, -28, 0, 30), Position = UDim2.fromOffset(14, 40), BackgroundColor3 = Color3.fromRGB(38, 38, 46),
            TextColor3 = Color3.new(1, 1, 1), PlaceholderColor3 = Color3.fromRGB(140, 140, 150), Font = Enum.Font.Gotham,
            TextSize = 14, BorderSizePixel = 0}, frame)
        mk("UICorner", {CornerRadius = UDim.new(0, 8)}, searchBox)
        searchBox.FocusLost:Connect(function()
            keyword = searchBox.Text
            curStyle = 0
            recolor()
            task.spawn(load, true)
        end)

        local chipRow = mk("ScrollingFrame", {BackgroundTransparency = 1, Position = UDim2.fromOffset(14, 76), Size = UDim2.new(1, -110, 0, 28),
            CanvasSize = UDim2.fromOffset(0, 0), AutomaticCanvasSize = Enum.AutomaticSize.X, ScrollBarThickness = 0,
            ScrollingDirection = Enum.ScrollingDirection.X, BorderSizePixel = 0}, frame)
        mk("UIListLayout", {FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, 6)}, chipRow)
        for i, c in ipairs(cats) do
            local b = mk("TextButton", {Text = c[1], Size = UDim2.fromOffset(92, 26), BackgroundColor3 = Color3.fromRGB(30, 80, 55),
                TextColor3 = Color3.new(1, 1, 1), Font = Enum.Font.GothamMedium, TextSize = 13, BorderSizePixel = 0}, chipRow)
            mk("UICorner", {CornerRadius = UDim.new(1, 0)}, b)
            catBtns[i] = b
            b.MouseButton1Click:Connect(function()
                curCat = i
                recolor()
                task.spawn(load, true)
            end)
        end
        for i, s in ipairs(styles) do
            local b = mk("TextButton", {Text = s[1], Size = UDim2.fromOffset(86, 26), BackgroundColor3 = Color3.fromRGB(52, 40, 90),
                TextColor3 = Color3.new(1, 1, 1), Font = Enum.Font.GothamMedium, TextSize = 13, BorderSizePixel = 0}, chipRow)
            mk("UICorner", {CornerRadius = UDim.new(1, 0)}, b)
            styleBtns[i] = b
            b.MouseButton1Click:Connect(function()
                keyword = s[2]
                searchBox.Text = s[2]
                curStyle = i
                recolor()
                task.spawn(load, true)
            end)
        end

        grid = mk("ScrollingFrame", {BackgroundTransparency = 1, Position = UDim2.fromOffset(10, 110), Size = UDim2.new(1, -20, 1, -154),
            CanvasSize = UDim2.fromOffset(0, 0), AutomaticCanvasSize = Enum.AutomaticSize.Y, ScrollBarThickness = 4,
            BorderSizePixel = 0}, frame)
        mk("UIGridLayout", {CellSize = UDim2.fromOffset(104, 128), CellPadding = UDim2.fromOffset(6, 6),
            SortOrder = Enum.SortOrder.LayoutOrder}, grid)
        status = mk("TextLabel", {BackgroundTransparency = 1, Position = UDim2.fromOffset(14, 150), Size = UDim2.new(1, -28, 0, 24),
            Text = "", TextColor3 = Color3.fromRGB(190, 190, 200), Font = Enum.Font.Gotham, TextSize = 14, ZIndex = 3}, frame)
        moreBtn = mk("TextButton", {Text = "المزيد", Visible = false, Size = UDim2.fromOffset(80, 26), Position = UDim2.new(1, -94, 0, 76),
            BackgroundColor3 = Color3.fromRGB(40, 140, 80), TextColor3 = Color3.new(1, 1, 1), Font = Enum.Font.GothamMedium,
            TextSize = 13, BorderSizePixel = 0}, frame)
        mk("UICorner", {CornerRadius = UDim.new(0, 8)}, moreBtn)
        moreBtn.MouseButton1Click:Connect(function() task.spawn(load, false) end)

        linkBox = mk("TextBox", {PlaceholderText = "الصق رابط الغرض أو رقمه واضغط Enter", Text = "", ClearTextOnFocus = false,
            Size = UDim2.new(1, -28, 0, 28), Position = UDim2.new(0, 14, 1, -36), BackgroundColor3 = Color3.fromRGB(38, 38, 46),
            TextColor3 = Color3.new(1, 1, 1), PlaceholderColor3 = Color3.fromRGB(140, 140, 150), Font = Enum.Font.Gotham,
            TextSize = 13, BorderSizePixel = 0}, frame)
        mk("UICorner", {CornerRadius = UDim.new(0, 8)}, linkBox)
        linkBox.FocusLost:Connect(function()
            local id = parseLink(linkBox.Text)
            if not id then
                if linkBox.Text ~= "" then notify("الرابط غير صحيح") end
                return
            end
            linkBox.Text = ""
            task.spawn(function()
                local ok, err = Wear.equip({id = id})
                notify(ok and "تم التلبيس" or (err or "فشل"))
            end)
        end)
        recolor()
    end

    function Catalog.open()
        if not game.HttpGet then notify("المنفّذ ما يدعم الاتصال بالكتالوج") return end
        if not gui or not gui.Parent then
            build()
            task.spawn(load, true)
        end
        gui.Enabled = true
    end
end

local SkinsTab = Window:Tab({ Title = "تغيير السكنات", Icon = "user" })

local skinInputText = ""

SkinsTab:Input({
    Title = "اسم اللاعب",
    Desc = "ادخل اسم المستخدم للاعب لنسخ سكنه",
    Placeholder = "اكتب هنا",
    Callback = function(val)
        skinInputText = val
    end
})

SkinsTab:Button({
    Title = "تطبيق السكن",
    Desc = "اضغط لتطبيق السكن المدخل على شخصيتك",
    Callback = function()
        startAvatarChange(skinInputText)
    end
})

SkinsTab:Button({
    Title = "↩ إرجاع سكني الأصلي",
    Desc = "يرجّع شكل شخصيتك الأصلي",
    Callback = function()
        resetAvatar()
    end
})

SkinsTab:Button({
    Title = "📦 الكتالوج",
    Desc = "يفتح قائمة بكل أغراض وسكنات الكتالوج، اختر وتظهر عليك بس",
    Callback = function() Catalog.open() end
})

SkinsTab:Section({ Title = "الرجل والراس" })

local KorbloxConn = nil
RegToggle(SkinsTab, "korblox", "الرجل (Korblox)",
    "تفعيل / إخفاء الرجل اليمنى باستمرار حتى بعد الموت", false,
    function(v)
        if KorbloxConn then KorbloxConn:Disconnect() KorbloxConn = nil end
        if v then
            KorbloxConn = RunService.RenderStepped:Connect(function()
                pcall(function()
                    local char = LocalPlayer.Character
                    if char then
                        local rLeg = char:FindFirstChild("Right Leg") or char:FindFirstChild("RightLowerLeg")
                        if rLeg and rLeg.Transparency ~= 1 then
                            rLeg.Transparency = 1
                        end
                    end
                end)
            end)
        else
            pcall(function()
                local char = LocalPlayer.Character
                if char then
                    local rLeg = char:FindFirstChild("Right Leg") or char:FindFirstChild("RightLowerLeg")
                    if rLeg then rLeg.Transparency = 0 end
                end
            end)
        end
    end)

local HeadlessConn = nil
RegToggle(SkinsTab, "headless", "الراس المخفي (Headless)",
    "تفعيل / إخفاء رأس الشخصية باستمرار حتى بعد الموت", false,
    function(v)
        if HeadlessConn then HeadlessConn:Disconnect() HeadlessConn = nil end
        if v then
            HeadlessConn = RunService.RenderStepped:Connect(function()
                pcall(function()
                    local char = LocalPlayer.Character
                    if char and char:FindFirstChild("Head") then
                        if char.Head.Transparency ~= 1 then
                            char.Head.Transparency = 1
                            for _, child in ipairs(char.Head:GetChildren()) do
                                if child:IsA("Decal") then child.Transparency = 1 end
                            end
                        end
                    end
                end)
            end)
        else
            pcall(function()
                local char = LocalPlayer.Character
                if char and char:FindFirstChild("Head") then
                    char.Head.Transparency = 0
                    for _, child in ipairs(char.Head:GetChildren()) do
                        if child:IsA("Decal") then child.Transparency = 0 end
                    end
                end
            end)
        end
    end)

local StompTab = Window:Tab({ Title = "الدعس", Icon = "zap" })

RegToggle(StompTab, "stompOn", "تفعيل الدعس",
    "الدعس وزره ما يشتغلون إلا لما تفعّل هذا الخيار", false,
    function(v) AstaX.setStompEnabled(v) end)

RegToggle(StompTab, "stompBtn", "زر الدعس على الشاشة",
    "يظهر زر تكبسه عشان يدعس 3 ثواني (تقدر تسحبه). يظهر بس لما الدعس مفعّل، وتقدر تخفيه من هنا", true,
    function(v) AstaX.setStompButton(v) end)

RegToggle(StompTab, "deadStomp", "تدعيس الموتى",
    "أول ما لاعب يموت تروح فوقه وتنط عليه وتضغط الأداة", false,
    function(v) AstaX.setDeadStomp(v) end)

local SongsTab = Window:Tab({ Title = "الأغاني", Icon = "music" })
SongsTab:Section({ Title = "مشغل الأغاني" })

local songInputText = ""
local selectedSong = nil
local songDropdown

local function refreshSongList()
    local names = AstaX.songNames()
    if #names == 0 then names = {"(ما فيه أغاني محفوظة)"} end
    selectedSong = names[1] ~= "(ما فيه أغاني محفوظة)" and names[1] or nil
    pcall(function() songDropdown:Refresh(names) end)
end

local function songResult(ok, msg)
    if ok then
        WindUI:Notify({ Title = "الأغاني", Content = "يشتغل: " .. msg, Duration = 3 })
    else
        WindUI:Notify({ Title = "الأغاني", Content = "ما اشتغلت: " .. msg, Duration = 4 })
    end
end

SongsTab:Input({
    Title = "رقم الصوت أو رابط",
    Desc = "رقم ساوند روبلوكس أو رابط mp3/ogg مباشر",
    Placeholder = "الصق هنا",
    Callback = function(val)
        songInputText = val
    end
})

SongsTab:Button({
    Title = "إضافة وتشغيل",
    Desc = "يشغّل الأغنية",
    Callback = function()
        local s = AstaX.parseSong(songInputText)
        if not s then
            WindUI:Notify({ Title = "الأغاني", Content = "اكتب رقم صوت أو رابط صحيح", Duration = 3 })
            return
        end
        s = AstaX.addSong(s)
        refreshSongList()
        AstaX.playSong(s, songResult)
    end
})

SongsTab:Button({
    Title = "إيقاف الأغنية",
    Callback = function()
        AstaX.stopSong()
    end
})

RegToggle(SongsTab, "songLoop", "تكرار (Loop)", nil, false,
    function(v) AstaX.setLoop(v) end)

Settings.register("songVol", 60, function(v) AstaX.setVolume(tonumber(v) or 60) end, "slider")
Settings.items["songVol"].ui = SongsTab:Slider({
    Title = "مستوى الصوت",
    Value = { Min = 0, Max = 100, Default = 60 },
    Callback = function(v)
        Settings.set("songVol", tonumber(v) or 60)
    end
})

task.defer(refreshSongList)

-- ================= تاب الإعدادات: حفظ واسترجاع =================
local SettingsTab = Window:Tab({ Title = "الإعدادات", Icon = "settings" })
SettingsTab:Section({ Title = "حفظ واسترجاع الإعدادات" })

SettingsTab:Paragraph({
    Title = "كيف تشتغل؟",
    Desc = "ظبّط خياراتك (الاسيست، الدعس، التأثيرات، السكن...) ثم اضغط «حفظ جميع الإعدادات». أي وقت تطلع وترجع وتشغّل السكربت ترجع إعداداتك المحفوظة لحالها تلقائياً."
})

local function filesSupported()
    if Settings.supported() then return true end
    WindUI:Notify({ Title = "الإعدادات", Content = "المنفّذ عندك ما يدعم حفظ الملفات!", Duration = 4 })
    return false
end

SettingsTab:Button({
    Title = "💾 حفظ جميع الإعدادات",
    Desc = "يحفظ كل خياراتك الحالية (والسكن اللي لابسه)",
    Callback = function()
        if not filesSupported() then return end
        local ok = Settings.save()
        WindUI:Notify({
            Title = "الإعدادات",
            Content = ok and "تم حفظ جميع إعداداتك!" or "فشل حفظ الإعدادات",
            Duration = 3
        })
    end
})

SettingsTab:Button({
    Title = "🔄 استرجاع الإعدادات المحفوظة",
    Desc = "يرجّع كل خياراتك اللي حفظتها قبل",
    Callback = function()
        if not filesSupported() then return end
        local ok = Settings.restore()
        WindUI:Notify({
            Title = "الإعدادات",
            Content = ok and "تم استرجاع إعداداتك المحفوظة!" or "ما فيه إعدادات محفوظة، اضغط حفظ أول",
            Duration = 3
        })
    end
})

SettingsTab:Button({
    Title = "إعادة الضبط (الافتراضي)",
    Desc = "يطفي كل الميزات ويرجّع الخيارات لوضعها الأصلي (ما يمسح المحفوظ)",
    Callback = function()
        Settings.reset()
        WindUI:Notify({ Title = "الإعدادات", Content = "رجعت كل الإعدادات للوضع الافتراضي", Duration = 3 })
    end
})

SettingsTab:Button({
    Title = "🗑 حذف الإعدادات المحفوظة",
    Desc = "يمسح ملف الحفظ (الخيارات الحالية تبقى لين تطلع)",
    Callback = function()
        if not filesSupported() then return end
        Settings.delete()
        WindUI:Notify({ Title = "الإعدادات", Content = "تم حذف الإعدادات المحفوظة", Duration = 3 })
    end
})

RegToggle(SettingsTab, "autoLoad", "استرجاع تلقائي عند الدخول",
    "أول ما تشغّل السكربت ترجع إعداداتك المحفوظة لحالها", true, nil)

SettingsTab:Section({ Title = "خلفية الواجهة" })
local bgUrlText = ""
SettingsTab:Input({
    Title = "رابط صورة مخصصة (اختياري)",
    Desc = "الصق رابط صورة مباشر (png / jpg) لو تبي تغيّر الخلفية",
    Placeholder = "https://...",
    Callback = function(val) bgUrlText = val end
})
SettingsTab:Button({
    Title = "تطبيق الصورة",
    Callback = function()
        if bgUrlText == "" then
            WindUI:Notify({ Title = "الخلفية", Content = "اكتب الرابط أول", Duration = 3 })
            return
        end
        local ok, err = Backdrop.setImage(bgUrlText)
        WindUI:Notify({ Title = "الخلفية", Content = ok and "تم تطبيق الصورة!" or (err or "فشل"), Duration = 3 })
    end
})
SettingsTab:Button({
    Title = "إرجاع الخلفية الأصلية",
    Callback = function() Backdrop.setDefault() end
})

local CreditsTab = Window:Tab({ Title = "الحقوق", Icon = "info" })
CreditsTab:Section({ Title = "طاقم العمل" })
CreditsTab:Paragraph({
    Title = "top 1 Asta V1.2",
    Desc = "تم البرمجة والتطوير بواسطة:\n★ Asta"
})

Window:SelectTab(1)

-- استرجاع تلقائي للإعدادات المحفوظة أول ما يشتغل السكربت
-- (نتأخر شوي عشان الواجهة تخلص إنشاء عناصرها قبل ما نرجّع القيم)
task.delay(1.5, function()
    local data = Settings.read()
    if data and data.autoLoad ~= false then
        Settings.restore(data)
        WindUI:Notify({ Title = "الإعدادات", Content = "تم استرجاع إعداداتك المحفوظة تلقائياً", Duration = 3 })
    end
end)
