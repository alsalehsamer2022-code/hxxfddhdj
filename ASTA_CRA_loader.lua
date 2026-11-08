-- ASTA CRA loader (small, fits the 50k limit)
local URL = "PUT_YOUR_RAW_LINK_HERE"

local ok, src = pcall(function()
	return game:HttpGet(URL)
end)

if not ok or type(src) ~= "string" or #src < 1000 then
	warn("ASTA CRA: failed to download the script")
	return
end

local fn, err = loadstring(src)
if not fn then
	warn("ASTA CRA: " .. tostring(err))
	return
end

fn()
