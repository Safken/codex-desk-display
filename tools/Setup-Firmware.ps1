$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$cli = Join-Path $root '.tools\arduino\arduino-cli.exe'
if (!(Test-Path $cli)) { throw 'Download Arduino CLI 1.2.2 into .tools/arduino first; see firmware/README.md.' }
$configPath = Join-Path $root '.tools\arduino-cli.json'
$settings = @{
  directories = @{data=(Join-Path $root '.tools\arduino-data'); downloads=(Join-Path $root '.tools\arduino-downloads'); user=(Join-Path $root '.tools\arduino-user')}
  board_manager = @{additional_urls=@('https://espressif.github.io/arduino-esp32/package_esp32_index.json')}
  network = @{connection_timeout='1800s'}
}
$settings | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $configPath -Encoding utf8
& $cli core update-index --config-file $configPath
if ($LASTEXITCODE) { throw 'Index download failed' }
& $cli core install 'esp32:esp32@3.2.0' --config-file $configPath
if ($LASTEXITCODE) { throw 'ESP32 core installation failed' }
& $cli lib install 'Adafruit ILI9341@1.6.1' 'Adafruit GFX Library@1.11.11' 'Adafruit BusIO@1.17.0' 'ArduinoJson@7.4.2' --config-file $configPath
if ($LASTEXITCODE) { throw 'Library installation failed' }
