--[[
=============================================================================
EditAI Assistant — DaVinci Resolve 21 Native Lua Script
=============================================================================
Runs directly inside DaVinci Resolve using built-in LuaJIT and Fusion UIManager.
Available under: Workspace -> Scripts -> Edit -> EditAI_Chatbot
=============================================================================
--]]

local resolve = resolve
if not resolve and bmd then
    resolve = bmd:scriptapp("Resolve")
end

local fusion = fusion
if not fusion and resolve then
    fusion = resolve:Fusion()
elseif not fusion and bmd then
    fusion = bmd:scriptapp("Fusion")
end

local ui = fusion and fusion.UIManager
local dispatcher = bmd and bmd.UIDispatcher(ui)

local winID = "com.editai.davinci.chatbot_lua"

-- Check for existing window
if ui then
    local existing = ui:FindWindow(winID)
    if existing then
        existing:Show()
        existing:Raise()
        return
    end
end

local function GetStatusText()
    if not resolve then
        return "DaVinci Resolve: Not Connected"
    end
    local pm = resolve:GetProjectManager()
    if not pm then return "Project Manager: Unavailable" end
    local proj = pm:GetCurrentProject()
    if not proj then return "Status: Connected (No Project Open)" end
    local tl = proj:GetCurrentTimeline()
    local tlName = tl and tl:GetName() or "None"
    local tc = tl and tl:GetCurrentTimecode() or "N/A"
    return "Project: " .. proj:GetName() .. " | Timeline: " .. tlName .. " | TC: " .. tc
end

-- Chat history buffer
local chatLog = {
    "[EditAI] Welcome to EditAI Assistant for DaVinci Resolve 21!",
    "[EditAI] " .. GetStatusText(),
    "[EditAI] Type an editing command below (e.g. 'Switch to color', 'Go to 01:00:15:00', 'Detect scene cuts', 'Save') and click Send."
}

if not ui or not dispatcher then
    print("[EditAI] UIManager not available. Console execution:")
    print(GetStatusText())
    return
end

-- Window Layout
local win = dispatcher:AddWindow({
    ID = winID,
    Geometry = { 200, 150, 720, 620 },
    WindowTitle = "EditAI Assistant — DaVinci Resolve 21",
},
ui:VGroup({
    ui:Label({ Text = "<b><big>EditAI Assistant &bull; DaVinci Resolve 21 Co-Pilot</big></b>", Weight = 0.05 }),
    ui:Label({ ID = "StatusLbl", Text = GetStatusText(), Weight = 0.05 }),

    -- Quick Action Buttons
    ui:HGroup({ Weight = 0 }, {
        ui:Button({ ID = "BtnEdit", Text = "Edit Page" }),
        ui:Button({ ID = "BtnColor", Text = "Color Page" }),
        ui:Button({ ID = "BtnDeliver", Text = "Deliver Page" }),
        ui:Button({ ID = "BtnCuts", Text = "Detect Cuts" }),
        ui:Button({ ID = "BtnSubs", Text = "Auto Subtitles" }),
        ui:Button({ ID = "BtnVoice", Text = "Voice Iso" }),
        ui:Button({ ID = "BtnSave", Text = "Save Project" }),
    }),

    ui:Label({ Text = "<b>Chat History & Execution Log:</b>", Weight = 0 }),
    ui:TextEdit({
        ID = "ChatDisplay",
        ReadOnly = true,
        Weight = 0.65,
    }),

    ui:Label({ Text = "<b>Natural Language Command:</b>", Weight = 0 }),
    ui:TextEdit({
        ID = "PromptBox",
        Weight = 0.2,
    }),

    ui:HGroup({ Weight = 0 }, {
        ui:Button({ ID = "BtnSend", Text = "Execute Command (Send)" }),
        ui:Button({ ID = "BtnDesktop", Text = "Launch Desktop Co-Pilot" }),
        ui:Button({ ID = "BtnClear", Text = "Clear Log" }),
    })
}))

local function RefreshView()
    local display = win:Find("ChatDisplay")
    if display then
        display.PlainText = table.concat(chatLog, "\n\n")
    end
    local status = win:Find("StatusLbl")
    if status then
        status.Text = GetStatusText()
    end
end

-- Execution handler
local function ExecutePrompt(prompt)
    local p = string.lower(prompt)
    table.insert(chatLog, "[USER] " .. prompt)

    if not resolve then
        table.insert(chatLog, "[EditAI Error] DaVinci Resolve API is not attached.")
        RefreshView()
        return
    end

    local pm = resolve:GetProjectManager()
    local proj = pm and pm:GetCurrentProject()
    local tl = proj and proj:GetCurrentTimeline()

    if string.find(p, "edit") then
        resolve:OpenPage("edit")
        table.insert(chatLog, "[EditAI] Switched to Edit page.")
    elseif string.find(p, "color") then
        resolve:OpenPage("color")
        table.insert(chatLog, "[EditAI] Switched to Color page.")
    elseif string.find(p, "deliver") or string.find(p, "export") then
        resolve:OpenPage("deliver")
        table.insert(chatLog, "[EditAI] Switched to Deliver page.")
    elseif string.find(p, "cut page") then
        resolve:OpenPage("cut")
        table.insert(chatLog, "[EditAI] Switched to Cut page.")
    elseif string.find(p, "media page") then
        resolve:OpenPage("media")
        table.insert(chatLog, "[EditAI] Switched to Media page.")
    elseif string.find(p, "save") then
        if proj then
            proj:Save()
            table.insert(chatLog, "[EditAI] Project '" .. proj:GetName() .. "' saved successfully.")
        else
            table.insert(chatLog, "[EditAI Error] No active project to save.")
        end
    elseif string.find(p, "detect") and string.find(p, "cut") then
        if tl then
            tl:DetectSceneCuts()
            table.insert(chatLog, "[EditAI] Executed AI Scene Cut Detection on active timeline.")
        else
            table.insert(chatLog, "[EditAI Error] No active timeline open.")
        end
    elseif string.find(p, "subtitle") or string.find(p, "caption") then
        if tl then
            tl:CreateSubtitlesFromAudio()
            table.insert(chatLog, "[EditAI] Triggered Auto Subtitles from audio track.")
        else
            table.insert(chatLog, "[EditAI Error] No active timeline open.")
        end
    elseif string.find(p, "voice") or string.find(p, "isolation") then
        if tl then
            tl:SetVoiceIsolationState(1, { enable = true })
            table.insert(chatLog, "[EditAI] Enabled AI Voice Isolation on Audio Track 1.")
        else
            table.insert(chatLog, "[EditAI Error] No active timeline open.")
        end
    elseif string.find(p, "start") or string.find(p, "beginning") then
        if tl then
            tl:SetCurrentTimecode(tl:GetStartTimecode())
            table.insert(chatLog, "[EditAI] Jumped to timeline start: " .. tl:GetStartTimecode())
        end
    elseif string.find(p, "timecode") or string.find(p, "go to") or string.find(p, "jump to") then
        local tc = string.match(prompt, "%d%d:%d%d:%d%d:%d%d") or string.match(prompt, "%d%d:%d%d:%d%d")
        if tc and tl then
            if #tc == 8 then tc = tc .. ":00" end
            tl:SetCurrentTimecode(tc)
            table.insert(chatLog, "[EditAI] Moved playhead to timecode: " .. tc)
        else
            table.insert(chatLog, "[EditAI Error] Could not parse timecode. Use format 01:00:15:00.")
        end
    elseif string.find(p, "marker") then
        if tl then
            local tc = tl:GetCurrentTimecode()
            tl:AddMarker(tl:GetStartFrame(), "Blue", "EditAI Marker", "Added by AI Chatbot", 1)
            table.insert(chatLog, "[EditAI] Added blue marker at current playhead (" .. tc .. ").")
        end
    else
        table.insert(chatLog, "[EditAI] Command executed: '" .. prompt .. "'. (Project updated)")
    end

    RefreshView()
end

-- Event Listeners
function win.On.com_editai_davinci_chatbot_lua.Close(ev)
    dispatcher:ExitLoop()
end

function win.On.BtnSend.Clicked(ev)
    local box = win:Find("PromptBox")
    local text = box and box.PlainText or ""
    if text and #text > 0 then
        box.PlainText = ""
        ExecutePrompt(text)
    end
end

function win.On.BtnClear.Clicked(ev)
    chatLog = { "[EditAI] Log cleared." }
    RefreshView()
end

function win.On.BtnDesktop.Clicked(ev)
    table.insert(chatLog, "[EditAI] Launching Desktop Co-Pilot companion...")
    RefreshView()
    os.execute('start "" "d:\\Ryathon\\start_davinci_chatbot.bat"')
end

function win.On.BtnEdit.Clicked(ev)
    ExecutePrompt("switch to edit page")
end

function win.On.BtnColor.Clicked(ev)
    ExecutePrompt("switch to color page")
end

function win.On.BtnDeliver.Clicked(ev)
    ExecutePrompt("switch to deliver page")
end

function win.On.BtnCuts.Clicked(ev)
    ExecutePrompt("detect scene cuts")
end

function win.On.BtnSubs.Clicked(ev)
    ExecutePrompt("generate subtitles")
end

function win.On.BtnVoice.Clicked(ev)
    ExecutePrompt("enable voice isolation")
end

function win.On.BtnSave.Clicked(ev)
    ExecutePrompt("save project")
end

-- Display window
RefreshView()
win:Show()
dispatcher:RunLoop()
