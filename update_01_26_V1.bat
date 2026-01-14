@echo off
setlocal enabledelayedexpansion

:: ============================================================================
:: DEBUG MODE: Set to 1 to see detailed PowerShell output, 0 for silent mode
:: ============================================================================
set DEBUG_MODE=0

cls
echo.
echo =============================================================================
echo        Rigveda JSON Updater - Smart Version Chain Manager
echo =============================================================================
echo.

:: Check for update files
set update_count=0
set /a index=0

echo Scanning for available updates...
echo.

for %%F in (update*.zip) do (
    set /a index+=1
    set "update_file_!index!=%%F"
    set /a update_count+=1
    echo   [!index!] %%F
)

if !update_count! equ 0 (
    echo No update*.zip files found in this folder!
    echo.
    echo Please download an update file with format: update_MM_YY_VX.zip
    echo Example: update_01_26_V3.zip
    echo.
    pause
    exit /b 1
)

echo.
echo Found !update_count! update package(s).
echo.

:: User selection
if !update_count! equ 1 (
    set selected_index=1
    echo Only one update found. Using: !update_file_1!
) else (
    set /p selected_index="Select update to apply (enter number 1-%update_count%): "
    
    if !selected_index! lss 1 (
        echo Invalid selection. Cancelled.
        pause
        exit /b 1
    )
    if !selected_index! gtr !update_count! (
        echo Invalid selection. Cancelled.
        pause
        exit /b 1
    )
)

set "selected_update=!update_file_%selected_index%!"
echo.
echo Selected: !selected_update!
echo.

:: Extract version from filename (update_01_26_V3.zip -> V3)
:: Get the last token before .zip
set "version="
for /f "tokens=1-10 delims=_" %%A in ("!selected_update!") do (
    set "last_token=%%A"
    if not "%%B"=="" set "last_token=%%B"
    if not "%%C"=="" set "last_token=%%C"
    if not "%%D"=="" set "last_token=%%D"
    if not "%%E"=="" set "last_token=%%E"
    if not "%%F"=="" set "last_token=%%F"
    if not "%%G"=="" set "last_token=%%G"
    if not "%%H"=="" set "last_token=%%H"
    if not "%%I"=="" set "last_token=%%I"
    if not "%%J"=="" set "last_token=%%J"
)

:: Remove .zip extension
set "version=!last_token:.zip=!"

if "!version!"=="" (
    echo ERROR: Could not extract version from filename.
    echo Expected format: update_MM_YY_VX.zip
    echo Example: update_01_26_V3.zip
    pause
    exit /b 1
)

echo Target version: !version!
echo.

:: Scan for Mandala files and find latest version of each
echo Scanning for Mandala files...
echo.

set mandala_count=0

:: Scan M1 through M10
for /L %%M in (1,1,10) do (
    call :find_latest "%%M"
)

echo.

if !mandala_count! equ 0 (
    echo No Mandala files found ^(M1_R2.zip, M1_R2_V*.zip, etc.^)
    echo Make sure your Mandala files are in this folder.
    pause
    exit /b 1
)

echo Found !mandala_count! Mandala file^(s^) to update.
echo.
echo This will:
echo   - Use the LATEST available version of each Mandala as source
echo   - Apply updates from: !selected_update!
echo   - Create new files with version: !version!
echo.
echo Your existing files will NOT be modified ^(safe operation^).
echo.

set /p proceed="Proceed with update? (Y/N): "

if /i NOT "!proceed!"=="Y" (
    echo Update cancelled.
    pause
    exit /b 0
)

echo.
echo =============================================================================
echo Starting update process...
echo =============================================================================
echo.

:: Initialize log file
set "log_file=update_log.txt"
set "timestamp=%date% %time:~0,5%"

echo ============================================================================= >> "!log_file!"
echo Update Log - !timestamp! >> "!log_file!"
echo ============================================================================= >> "!log_file!"
echo Update Package: !selected_update! >> "!log_file!"
echo Target Version: !version! >> "!log_file!"
echo. >> "!log_file!"

set success_count=0
set failed_count=0

:: Process each Mandala
for /L %%M in (1,1,10) do (
    if defined source_M%%M (
        call :process_zip "!source_M%%M!" "%%M" "!selected_update!" "!version!"
    )
)

echo.
echo =============================================================================
echo                          UPDATE COMPLETE
echo =============================================================================
echo.
echo Summary:
echo   Successful: !success_count!
echo   Failed: !failed_count!
echo   Total: !mandala_count!
echo.
echo New files created with _!version! suffix.
echo Update log saved to: !log_file!
echo.

if !failed_count! gtr 0 (
    echo WARNING: Some updates failed. Check the log for details.
    echo.
)

echo ============================================================================= >> "!log_file!"
echo Summary: !success_count! successful, !failed_count! failed >> "!log_file!"
echo ============================================================================= >> "!log_file!"
echo. >> "!log_file!"

:: Show popup summary using PowerShell (works on all Windows versions)
powershell -Command "Add-Type -AssemblyName PresentationFramework; [System.Windows.MessageBox]::Show('Success: !success_count!`nFailed: !failed_count!`nTotal: !mandala_count!`n`nSee update_log.txt for details.', 'Rigveda Update Complete', 'OK', 'Information')" >nul 2>&1

pause
exit /b 0

:: ============================================================================
:: FUNCTION: Find latest version of a specific Mandala number
:: ============================================================================
:find_latest
set "num=%~1"
set "found_file="

:: Check for base R2 file
if exist "M%num%_R2.zip" (
    set "found_file=M%num%_R2.zip"
)

:: Check for any versioned files (last one found will be used)
for %%V in (M%num%_R2_V*.zip) do (
    set "found_file=%%V"
)

:: If we found something, register it
if defined found_file (
    set "source_M%num%=!found_file!"
    set /a mandala_count+=1
    echo   M%num%: !found_file! --^> M%num%_R2_!version!.zip
)

goto :eof

:: ============================================================================
:: FUNCTION: Process ZIP update
:: ============================================================================
:process_zip
set "source_zip=%~1"
set "mandala_num=%~2"
set "update_package=%~3"
set "target_version=%~4"
set "output_zip=M%mandala_num%_R2_%target_version%.zip"
set "mandala_folder=M%mandala_num%"

echo Processing M%mandala_num%: %source_zip% --^> %output_zip%

:: Create backup of source file
echo   Creating backup: %source_zip%.backup
copy "%source_zip%" "%source_zip%.backup" >nul 2>&1
if errorlevel 1 (
    echo   WARNING: Could not create backup file
) else (
    echo   Backup created successfully
)

:: Check if output already exists
if exist "%output_zip%" (
    echo   WARNING: %output_zip% already exists. Skipping.
    echo   - SKIPPED: %source_zip% ^(output already exists^) >> "!log_file!"
    set /a failed_count+=1
    echo.
    goto :eof
)

set "temp_dir=%TEMP%\Rigveda_Update_%RANDOM%"
set "update_temp=%TEMP%\Rigveda_Update_Source_%RANDOM%"
mkdir "%temp_dir%" 2>nul
mkdir "%update_temp%" 2>nul

echo   Extracting source: %source_zip%...
if %DEBUG_MODE%==1 (
    powershell -command "Expand-Archive -Path '%source_zip%' -DestinationPath '%temp_dir%' -Force"
) else (
    powershell -command "Expand-Archive -Path '%source_zip%' -DestinationPath '%temp_dir%' -Force" >nul 2>&1
)
if errorlevel 1 (
    echo   ERROR: Failed to extract %source_zip%
    echo   - FAILED: %source_zip% ^(extraction error^) >> "!log_file!"
    set /a failed_count+=1
    goto :cleanup
)

echo   Extracting update package...
if %DEBUG_MODE%==1 (
    powershell -command "Expand-Archive -Path '%update_package%' -DestinationPath '%update_temp%' -Force"
) else (
    powershell -command "Expand-Archive -Path '%update_package%' -DestinationPath '%update_temp%' -Force" >nul 2>&1
)
if errorlevel 1 (
    echo   ERROR: Failed to extract update package
    echo   - FAILED: %source_zip% ^(update extraction error^) >> "!log_file!"
    set /a failed_count+=1
    goto :cleanup
)

echo   Applying JSON updates for %mandala_folder%...
if exist "%update_temp%\%mandala_folder%" (
    set json_count=0
    for %%J in ("%update_temp%\%mandala_folder%\*.json") do set /a json_count+=1
    
    if !json_count! gtr 0 (
        xcopy "%update_temp%\%mandala_folder%\*.json" "%temp_dir%\%mandala_folder%\" /Y /Q >nul 2>&1
        if errorlevel 1 (
            echo   ERROR: Failed to copy JSON updates
            echo   - FAILED: %source_zip% ^(copy error^) >> "!log_file!"
            set /a failed_count+=1
            goto :cleanup
        )
        echo   Updated !json_count! JSON file^(s^)
    ) else (
        echo   INFO: No JSON files in update for %mandala_folder%
        echo   - INFO: %source_zip% ^(no JSON updates found^) >> "!log_file!"
    )
) else (
    echo   INFO: %mandala_folder% not in update package
    echo   - INFO: %source_zip% ^(folder not in update^) >> "!log_file!"
)

echo   Creating %output_zip%...
if %DEBUG_MODE%==1 (
    powershell -command "Compress-Archive -Path '%temp_dir%\*' -DestinationPath '%output_zip%' -Force -CompressionLevel Optimal"
) else (
    powershell -command "Compress-Archive -Path '%temp_dir%\*' -DestinationPath '%output_zip%' -Force -CompressionLevel Optimal" >nul 2>&1
)
if errorlevel 1 (
    echo   ERROR: Failed to create %output_zip%
    echo   - FAILED: %source_zip% ^(compression error^) >> "!log_file!"
    set /a failed_count+=1
    goto :cleanup
)

echo   SUCCESS!
echo   %source_zip% --^> %output_zip% [OK] >> "!log_file!"
set /a success_count+=1
echo.

:cleanup
rmdir /s /q "%temp_dir%" 2>nul
rmdir /s /q "%update_temp%" 2>nul
goto :eof
