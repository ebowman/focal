tell application "Calendar"
    set calendarList to {}
    repeat with cal in calendars
        set end of calendarList to name of cal
    end repeat
    return calendarList
end tell