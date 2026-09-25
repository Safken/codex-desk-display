param([switch]$Demo)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$cli = Join-Path $root '.tools\arduino\arduino-cli.exe'
$configPath = Join-Path $root '.tools\arduino-cli.json'
$variant = if ($Demo) {'demo'} else {'release'}
$flags = if ($Demo) {'-DCODEX_DEMO=1'} else {'-DCODEX_DEMO=0'}
& $cli compile --config-file $configPath --fqbn 'esp32:esp32:esp32s3:FlashSize=16M,PSRAM=opi,PartitionScheme=app3M_fat9M_16MB,USBMode=hwcdc,CDCOnBoot=cdc' --build-property "compiler.cpp.extra_flags=$flags" --output-dir (Join-Path $root "firmware\build\$variant") (Join-Path $root 'firmware\CodexDesk')
if ($LASTEXITCODE) { throw 'Firmware compilation failed' }
