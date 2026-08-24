@echo off
set PORT=%1
if "%PORT%"=="" (
    echo Usage: flash_windows.bat COM_PORT
    echo Example: flash_windows.bat COM6
    exit /b 1
)
echo == Writing firmware to %PORT% (bootloader + partition table + OTA data + app) ==
python -m esptool --chip esp32s3 --port %PORT% -b 460800 --before default_reset --after no_reset write_flash --flash_mode dio --flash_freq 80m --flash_size 16MB 0x0 build/bootloader/bootloader.bin 0x8000 build/partition_table/partition-table.bin 0xe000 build/ota_data_initial.bin 0x10000 build/vanguard_firmware.bin
if %errorlevel% neq 0 exit /b %errorlevel%
echo.
echo == Erasing NVS partition on %PORT% (identity/contacts/challenge progress) ==
python -m esptool --chip esp32s3 --port %PORT% --before no_reset --after no_reset erase_region 0x9000 0x5000
if %errorlevel% neq 0 exit /b %errorlevel%
echo.
echo == Resetting %PORT% into the new firmware ==
python -m esptool --chip esp32s3 --port %PORT% --before no_reset --after hard_reset run
