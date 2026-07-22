#软件 [Download - Wez's Terminal Emulator](https://wezterm.org/installation.html)

支持加载 `~/.wezterm-config.json` 配置文件
C:\Users\user\.wezterm.lua
```lua
-- WezTerm API
local wezterm = require("wezterm")

local config = wezterm.config_builder()
local git_bash_args = { "C:\\Program Files\\Git\\bin\\bash.exe", "--login", "-i" }

local function get_external_config_path()
  local home_dir = os.getenv("USERPROFILE") or wezterm.home_dir or "~"
  return home_dir .. "\\.wezterm-config.json"
end

local function load_external_config()
  local config_path = get_external_config_path()
  local file = io.open(config_path, "r")

  if not file then
    wezterm.log_error("Failed to open WezTerm external config: " .. config_path)
    return {}
  end

  local content = file:read("*a")
  file:close()

  local ok, parsed = pcall(wezterm.json_parse, content)
  if not ok then
    wezterm.log_error("Failed to parse WezTerm external config: " .. tostring(parsed))
    return {}
  end

  if type(parsed) ~= "table" then
    wezterm.log_error("Invalid WezTerm external config format: expected JSON object")
    return {}
  end

  return parsed
end

wezterm.add_to_config_reload_watch_list(get_external_config_path())

local external_config = load_external_config()

-- config.initial_cols = 128
-- config.initial_rows = 28
-- config.font_size = 11
-- https://wezterm.org/colorschemes/m/index.html?h=material+darker#material-darker-base16
config.color_scheme = "Material Darker (base16)"
-- config.color_scheme = "AdventureTime"

config.default_prog = { "powershell.exe", "-NoLogo" }

-- Ctrl+Shift+L. Launch menu items are loaded from ~/.wezterm-config.json.
-- update1
config.launch_menu = external_config.launch_menu or {}

config.keys = {
  {
    key = "g",
    mods = "CTRL|SHIFT",
    action = wezterm.action.SpawnCommandInNewTab({
      args = git_bash_args,
    }),
  },
}

return config

```

```json
{
  "launch_menu": [
    {
      "label": "Git Bash",
      "args": [
        "C:\\Program Files\\Git\\bin\\bash.exe",
        "--login",
        "-i"
      ],
      "cwd": "~"
    },
    {
      "label": "Windows PowerShell",
      "args": [
        "powershell.exe",
        "-NoLogo"
      ],
      "cwd": "~"
    }
  ]
}
```