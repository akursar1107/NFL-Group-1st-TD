# Automated Grading Setup

## Option 1: Windows Task Scheduler

1. **Open Task Scheduler**
   - Press `Win + R`, type `taskschd.msc`, press Enter

2. **Create Basic Task**
   - Click "Create Basic Task" in the right panel
   - Name: `NFL First TD Auto Grading`
   - Description: `Automatically grade picks every Tuesday at 4am EST`

3. **Trigger Settings**
   - When: `Weekly`
   - Start date: Pick next Tuesday
   - Start time: `04:00:00` (4:00 AM)
   - Recur every: `1 week`
   - Days: Check `Tuesday`

4. **Action Settings**
   - Action: `Start a program`
   - Program/script: `C:\Users\akurs\Desktop\Vibe Coder\venv\Scripts\python.exe`
   - Arguments: `auto_grade.py --season 2025`
   - Start in: `C:\Users\akurs\Desktop\Vibe Coder\main\league_webapp`

5. **Finish and Test**
   - Click Finish
   - Right-click the task → Run to test it works

---

## Option 2: PowerShell Script with Scheduled Task

Save this as `schedule_grading.ps1` and run it once:

```powershell
$action = New-ScheduledTaskAction -Execute "C:\Users\akurs\Desktop\Vibe Coder\venv\Scripts\python.exe" `
    -Argument "auto_grade.py --season 2025" `
    -WorkingDirectory "C:\Users\akurs\Desktop\Vibe Coder\main\league_webapp"

$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Tuesday -At 4am

$principal = New-ScheduledTaskPrincipal -UserId "$env:USERNAME" -LogonType S4U

$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

Register-ScheduledTask -TaskName "NFL First TD Auto Grading" `
    -Action $action `
    -Trigger $trigger `
    -Principal $principal `
    -Settings $settings `
    -Description "Automatically grade NFL First TD picks every Tuesday at 4am EST"

Write-Host "Scheduled task created successfully!" -ForegroundColor Green
```

---

## Manual Testing

Test the auto-grading script manually:

```powershell
cd "C:\Users\akurs\Desktop\Vibe Coder\main\league_webapp"
python auto_grade.py --season 2025
```

Or grade a specific week:

```powershell
python auto_grade.py --season 2025 --week 13
```

---

## Script Features

- **Automatic week detection**: Grades the most recently completed week (current week - 1)
- **Uses cached data**: Efficient, doesn't re-download play-by-play data
- **Detailed logging**: Shows which picks were graded and results
- **Skips already graded**: Won't re-grade picks that already have results
- **Safe**: Only grades FTD picks (ATTS would need separate implementation)

---

## Monitoring

Check the scheduled task history:
1. Open Task Scheduler
2. Find "NFL First TD Auto Grading"
3. Click "History" tab to see execution logs

Or check the database after Tuesday 4am to verify picks were graded.
