# timetable_manager.py
# Author: The Duc Nguyen
# Student ID: 110482092
#
# This is my own work as defined by
#  the University's Academic Misconduct Policy.
#

"""
Weekly Timetable Manager — COMP5076 Assignment 2 (Advanced Version)

Meets Functional Requirements FR1–FR13:
- FR1  : Prints title, author, email at start.
- FR2  : Text menu with validated prompts.
- FR3  : Quit via menu.
- FR4  : Robust validation and re-prompting.
- FR5  : Create event (title, start, end, optional location).
- FR6  : Update event identified by START time.
- FR7  : Delete event identified by START time.
- FR8  : Supports at least 9:00–17:00 (actually supports full day).
- FR9  : At least hourly (actually minute-level granularity).
- FR10 : Overlap prevention on create/update.
- FR11 : Print weekly overview (abbreviated as needed).
- FR12 : Print full details for a selected day (chronological).
- FR13 : Save/Load timetable to/from a user-named file (manual text format).

Meets Non-Functional Requirements NFR1–NFR10:
- NFR1 : Single script, no imports (only built-ins); no external modules.
- NFR2 : Header with required identity details.
- NFR3 : No 'break' statements in loops.
- NFR4 : Docstrings and descriptive comments.
- NFR5–6: Meaningful snake_case names, readable style.
- NFR7 : Procedural style (no classes), built as functions.
- NFR8 : Only global statement is the call to main().
- NFR9 : Defensive input handling; avoids crashes.
- NFR10: Clear prompts and outputs for first-time users.

Advanced Features implemented:
- Minute-level times (e.g., 10:10am, 14:45).
- Optional week start day (Sunday or Monday) applied to prints.
- Case-insensitive keyword search in title/location.
- Manual text save/load (no pickle) with delimiter escaping.
"""

# ---------- Program metadata (edit email before submission) ----------
PROGRAM_TITLE = "Weekly Timetable Manager"
PROGRAM_AUTHOR = "The Duc Nguyen"
STUDENT_ID = "110482092"
PROGRAM_EMAIL = "your_unisa_email_id"  # e.g., ngtd0001


# ---------- State constructors ----------
def empty_week():
    """
    Return a 7-element list; each element is a list of event dicts for that day.
    Event dict: {'title': str, 'start': int, 'end': int, 'location': str}
    Time values are minutes since midnight [0..1439].
    """
    return [list() for _ in range(7)]


def default_state():
    """
    App state holds the week data and the preferred week start:
      week_start: 0 => Sunday, 1 => Monday.
    """
    return {
        "week": empty_week(),
        "week_start": 1,  # default to Monday; user can change via menu
    }


# ---------- Time parsing/formatting ----------
def parse_time_to_minutes(text):
    """
    Parse user-entered time strings into minutes since midnight.
    Accepts forms like:
      '9', '09', '9:00', '09:00',
      '9am', '9:00am', '12pm', '12:30PM',
      '14', '14:15' (24-hour).
    Returns int minutes [0..1439], or None if invalid.
    """
    if text is None:
        return None
    s = text.strip().lower().replace(" ", "")
    if s == "":
        return None

    is_pm = s.endswith("pm")
    is_am = s.endswith("am")
    if is_pm or is_am:
        s = s[:-2]

    if ":" in s:
        parts = s.split(":")
        if len(parts) != 2:
            return None
        h_str, m_str = parts[0], parts[1]
    else:
        h_str, m_str = s, "0"

    if not (h_str.isdigit() and m_str.isdigit()):
        return None

    hour = int(h_str)
    minute = int(m_str)
    if minute < 0 or minute > 59:
        return None

    if is_am or is_pm:
        if hour < 1 or hour > 12:
            return None
        if is_pm:
            hour = 12 if hour == 12 else hour + 12
        else:
            hour = 0 if hour == 12 else hour
    else:
        if hour < 0 or hour > 23:
            return None

    return hour * 60 + minute


def minutes_to_pretty(m):
    """
    Convert minutes (0..1439) to 'h:mmam/pm', e.g., 9:00am, 2:45pm.
    """
    if m < 0:
        m = 0
    if m > 1439:
        m = 1439
    h24 = m // 60
    mn = m % 60
    am = h24 < 12
    h12 = h24 % 12
    if h12 == 0:
        h12 = 12
    return f"{h12}:{mn:02d}{'am' if am else 'pm'}"


def within_day_range(start_m, end_m):
    """
    Allow full-day scheduling but require same-day range and start < end.
    Satisfies FR8 minimal requirement (9–5) while being more flexible.
    """
    return 0 <= start_m < end_m <= 24 * 60


# ---------- Day helpers ----------
def get_days_view(week_start):
    """
    Return (labels, mapping) where labels are day names starting at week_start,
    and mapping maps relative index to absolute day index.
    Absolute indices: 0=Sun..6=Sat.
    """
    absolute_labels = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    labels = [None] * 7
    mapping = [0] * 7
    i = 0
    while i < 7:
        abs_idx = (week_start + i) % 7
        labels[i] = absolute_labels[abs_idx]
        mapping[i] = abs_idx
        i = i + 1
    return (labels, mapping)


def ask_day_index(week_start):
    """
    Prompt for a day (number or name). Applies current week_start view.
    Return absolute day index 0..6.
    """
    labels, mapping = get_days_view(week_start)
    print("Choose a day:")
    i = 0
    while i < 7:
        print(f"  {i+1}. {labels[i]}")
        i = i + 1

    chosen = 0
    ok = False
    while not ok:
        raw = input("Enter number (1-7) or name (e.g., Mon): ").strip()
        if raw.isdigit():
            n = int(raw)
            if 1 <= n <= 7:
                chosen = mapping[n - 1]
                ok = True
            else:
                print("  Out of range. Choose 1..7.")
        else:
            name = raw.title()[:3]
            found = -1
            j = 0
            while j < 7:
                if labels[j].lower().startswith(name.lower()):
                    found = j
                j = j + 1
            if found == -1:
                print("  Not a valid day. Try 'Mon', 'Tue', etc.")
            else:
                chosen = mapping[found]
                ok = True
    return chosen


def name_to_absolute_day(name3):
    """
    Convert 'Sun'..'Sat' to absolute index 0..6 (fallback 0).
    """
    base = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    i = 0
    found = -1
    while i < 7:
        if base[i].lower().startswith(name3.lower()):
            found = i
        i = i + 1
    if found == -1:
        return 0
    return found


# ---------- Input helpers ----------
def ask_time(prompt):
    """
    Prompt until a valid time is entered; return minutes.
    """
    valid = False
    result = 0
    while not valid:
        txt = input(prompt).strip()
        t = parse_time_to_minutes(txt)
        if t is None:
            print("  Invalid time. Examples: 9, 9am, 9:30, 14:00, 3:15pm.")
        else:
            valid = True
            result = t
    return result


def ask_menu_choice():
    """
    Read menu choice 0..9 with validation.
    """
    ok = False
    val = -1
    while not ok:
        s = input("Choose an option (0-9): ").strip()
        if s.isdigit():
            v = int(s)
            if 0 <= v <= 9:
                ok = True
                val = v
            else:
                print("  Please choose a number 0..9.")
        else:
            print("  Please enter a number.")
    return val


# ---------- Event operations ----------
def sort_day_events(day_events):
    """
    In-place insertion sort by 'start' to keep chronological order.
    """
    i = 1
    n = len(day_events)
    while i < n:
        key = day_events[i]
        j = i - 1
        done = False
        while (j >= 0) and (not done):
            if day_events[j]["start"] > key["start"]:
                day_events[j + 1] = day_events[j]
                j = j - 1
            else:
                done = True
        day_events[j + 1] = key
        i = i + 1


def has_overlap(events_of_day, new_start, new_end, skip_index=-1):
    """
    Check if [new_start, new_end) overlaps any event in events_of_day,
    ignoring skip_index (for updates).
    """
    k = 0
    while k < len(events_of_day):
        if k != skip_index:
            ev = events_of_day[k]
            s = ev["start"]
            e = ev["end"]
            if (new_start < e) and (new_end > s):
                return True
        k = k + 1
    return False


def find_event_index_by_start(events_of_day, start_m):
    """
    Identify an event by its exact start time; return index or -1.
    """
    i = 0
    found = -1
    while i < len(events_of_day):
        if events_of_day[i]["start"] == start_m:
            found = i
        i = i + 1
    return found


def add_event(state):
    """
    Create a new event with validated times and no overlap.
    """
    day_idx = ask_day_index(state["week_start"])
    title = input("Title: ").strip()
    location = input("Where (optional): ").strip()
    start_m = ask_time("Start time (e.g., 9am, 13:00): ")
    end_m = ask_time("End time (e.g., 10am, 14:45): ")

    if not within_day_range(start_m, end_m):
        print("  Invalid time range. Start must be before end within the same day.")
        return

    evs = state["week"][day_idx]
    if has_overlap(evs, start_m, end_m):
        print("  Overlap detected with an existing event. Please reschedule.")
        return

    evs.append({"title": title, "start": start_m, "end": end_m, "location": location})
    sort_day_events(evs)
    print("  Event added.")


def update_event(state):
    """
    Update event details; identification by start time (FR6).
    """
    day_idx = ask_day_index(state["week_start"])
    evs = state["week"][day_idx]
    if len(evs) == 0:
        print("  No events to update on that day.")
        return

    print_day_list(state, day_idx, full=False)
    start_m = ask_time("Enter START time of the event to update: ")
    idx = find_event_index_by_start(evs, start_m)
    if idx == -1:
        print("  No event found with that start time.")
        return

    ev = evs[idx]
    print("Leave a field empty to keep existing value.")
    new_title = input(f"New title [{ev['title']}]: ").strip()
    new_loc = input(f"New where [{ev['location']}]: ").strip()
    raw_start = input(f"New start [{minutes_to_pretty(ev['start'])}]: ").strip()
    raw_end = input(f"New end [{minutes_to_pretty(ev['end'])}]: ").strip()

    upd_title = ev["title"] if new_title == "" else new_title
    upd_loc = ev["location"] if new_loc == "" else new_loc

    if raw_start == "":
        upd_start = ev["start"]
    else:
        t = parse_time_to_minutes(raw_start)
        if t is None:
            print("  Invalid new start time. Update cancelled.")
            return
        upd_start = t

    if raw_end == "":
        upd_end = ev["end"]
    else:
        t = parse_time_to_minutes(raw_end)
        if t is None:
            print("  Invalid new end time. Update cancelled.")
            return
        upd_end = t

    if not within_day_range(upd_start, upd_end):
        print("  Invalid time range. Update cancelled.")
        return
    if has_overlap(evs, upd_start, upd_end, skip_index=idx):
        print("  Overlap detected. Update cancelled.")
        return

    ev["title"] = upd_title
    ev["location"] = upd_loc
    ev["start"] = upd_start
    ev["end"] = upd_end
    sort_day_events(evs)
    print("  Event updated.")


def delete_event(state):
    """
    Delete an event by its start time (FR7).
    """
    day_idx = ask_day_index(state["week_start"])
    evs = state["week"][day_idx]
    if len(evs) == 0:
        print("  No events to delete on that day.")
        return

    print_day_list(state, day_idx, full=False)
    start_m = ask_time("Enter START time of the event to delete: ")
    idx = find_event_index_by_start(evs, start_m)
    if idx == -1:
        print("  No event with that start time.")
        return

    confirm = input("Confirm delete? (y/n): ").strip().lower()
    if confirm == "y":
        # rebuild list without the deleted element (no break)
        new_evs = []
        i = 0
        while i < len(evs):
            if i != idx:
                new_evs.append(evs[i])
            i = i + 1
        state["week"][day_idx] = new_evs
        print("  Event deleted.")
    else:
        print("  Delete cancelled.")


# ---------- Printing ----------
def abbreviate(s, max_len):
    """
    Abbreviate string to max_len with '..' if needed.
    """
    if s is None:
        return ""
    if len(s) <= max_len:
        return s
    cut = max_len - 2
    if cut < 1:
        cut = 1
    return s[:cut] + ".."


def print_week_overview(state):
    """
    Weekly overview (FR11). Applies week_start; abbreviates long fields.
    """
    labels, mapping = get_days_view(state["week_start"])
    print("\n=== Weekly Overview ===")
    i = 0
    while i < 7:
        abs_idx = mapping[i]
        print(f"\n{labels[i]}:")
        evs = state["week"][abs_idx]
        if len(evs) == 0:
            print("  (no events)")
        else:
            k = 0
            while k < len(evs):
                ev = evs[k]
                t1 = minutes_to_pretty(ev["start"])
                t2 = minutes_to_pretty(ev["end"])
                title = abbreviate(ev["title"], 18)
                loc = abbreviate(ev["location"], 12)
                where = f" @ {loc}" if (loc is not None and len(loc) > 0) else ""
                print(f"  {t1}-{t2}  {title}{where}")
                k = k + 1
        i = i + 1
    print("")


def print_day_full(state):
    """
    Choose a day then print full details (FR12).
    """
    day_idx = ask_day_index(state["week_start"])
    print_day_list(state, day_idx, full=True)


def print_day_list(state, day_idx, full):
    """
    Print events for a specific day in chronological order.
    """
    labels = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    print(f"\n=== {labels[day_idx]} ===")
    evs = state["week"][day_idx]
    if len(evs) == 0:
        print("  (no events)\n")
        return

    i = 0
    while i < len(evs):
        ev = evs[i]
        t1 = minutes_to_pretty(ev["start"])
        t2 = minutes_to_pretty(ev["end"])
        if full:
            where = f"\n  Where: {ev['location']}" if (ev["location"] is not None and len(ev["location"]) > 0) else ""
            print(f"- {ev['title']}\n  When: {t1} - {t2}{where}\n")
        else:
            where = f" @ {ev['location']}" if (ev["location"] is not None and len(ev["location"]) > 0) else ""
            print(f"  {t1}-{t2}  {ev['title']}{where}")
        i = i + 1


# ---------- Save / Load (manual text format) ----------
def sanitize_pipe(text):
    """
    Replace '|' with '／' to protect delimiter in manual save format.
    """
    if text is None:
        return ""
    return text.replace("|", "／")


def restore_pipe(text):
    """
    Restore '／' back to '|'.
    """
    if text is None:
        return ""
    return text.replace("／", "|")


def save_to_file(state):
    """
    Save timetable to a user file (FR13). Format:
      WEEK_START:<0|1>
      DAY:<Sun|Mon|...>
      title|start|end|location  (times are minutes)
    """
    name = input("Enter filename to SAVE (e.g., my_timetable.txt): ").strip()
    if name == "":
        print("  Save cancelled.")
        return

    lines = []
    lines.append(f"WEEK_START:{state['week_start']}")
    labels = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    d = 0
    while d < 7:
        lines.append(f"DAY:{labels[d]}")
        evs = state["week"][d]
        i = 0
        while i < len(evs):
            ev = evs[i]
            title = sanitize_pipe(ev["title"])
            loc = sanitize_pipe(ev["location"])
            lines.append(f"{title}|{ev['start']}|{ev['end']}|{loc}")
            i = i + 1
        d = d + 1

    try:
        fh = open(name, "w", encoding="utf-8")
        i = 0
        while i < len(lines):
            fh.write(lines[i] + "\n")
            i = i + 1
        fh.close()
        print("  Saved.")
    except Exception:
        print("  Error saving file (check path/permissions).")


def load_from_file(state):
    """
    Load timetable from a user file (FR13). Accepts format written by save_to_file().
    """
    name = input("Enter filename to LOAD (e.g., my_timetable.txt): ").strip()
    if name == "":
        print("  Load cancelled.")
        return

    try:
        fh = open(name, "r", encoding="utf-8")
        lines = fh.readlines()
        fh.close()
    except Exception:
        print("  Could not open file.")
        return

    new_week = empty_week()
    new_week_start = state["week_start"]
    current_day = -1

    i = 0
    while i < len(lines):
        raw = lines[i].rstrip("\n")
        if raw.startswith("WEEK_START:"):
            ws = raw.split(":")[1].strip()
            if ws.isdigit():
                v = int(ws)
                if v == 0 or v == 1:
                    new_week_start = v
        elif raw.startswith("DAY:"):
            day_name = raw.split(":")[1].strip().title()[:3]
            current_day = name_to_absolute_day(day_name)
        else:
            if current_day != -1 and "|" in raw:
                p = raw.split("|")
                if len(p) == 4 and p[1].isdigit() and p[2].isdigit():
                    title = restore_pipe(p[0])
                    start_m = int(p[1])
                    end_m = int(p[2])
                    location = restore_pipe(p[3])
                    if within_day_range(start_m, end_m) and (not has_overlap(new_week[current_day], start_m, end_m)):
                        new_week[current_day].append({
                            "title": title,
                            "start": start_m,
                            "end": end_m,
                            "location": location
                        })
                        sort_day_events(new_week[current_day])
        i = i + 1

    state["week"] = new_week
    state["week_start"] = new_week_start
    print("  Loaded timetable.")


# ---------- Preferences & Search (advanced) ----------
def set_week_start(state):
    """
    Let user choose Sunday (0) or Monday (1) as week start for printing.
    """
    print("Choose week start day:")
    print("  1. Sunday")
    print("  2. Monday")
    ok = False
    choice = 0
    while not ok:
        s = input("Enter 1 or 2: ").strip()
        if s == "1":
            choice = 0
            ok = True
        elif s == "2":
            choice = 1
            ok = True
        else:
            print("  Please enter 1 or 2.")
    state["week_start"] = choice
    print("  Week start updated.")


def search_events(state):
    """
    Case-insensitive keyword search across title and location.
    Prints results chronologically across the whole week.
    """
    kw = input("Enter keyword to search (title/location): ").strip().lower()
    if kw == "":
        print("  Empty keyword; search cancelled.")
        return

    matches = []
    d = 0
    while d < 7:
        evs = state["week"][d]
        i = 0
        while i < len(evs):
            ev = evs[i]
            t = ev["title"].lower()
            l = (ev["location"] or "").lower()
            if (kw in t) or (kw in l):
                matches.append((d, ev))
            i = i + 1
        d = d + 1

    # selection sort by (day, start) to avoid imports
    j = 0
    while j < len(matches):
        min_idx = j
        k = j + 1
        while k < len(matches):
            d1, e1 = matches[min_idx]
            d2, e2 = matches[k]
            if (d2 < d1) or (d2 == d1 and e2["start"] < e1["start"]):
                min_idx = k
            k = k + 1
        temp = matches[j]
        matches[j] = matches[min_idx]
        matches[min_idx] = temp
        j = j + 1

    if len(matches) == 0:
        print("  No matches.")
        return

    labels = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    print("\n=== Search Results ===")
    m = 0
    while m < len(matches):
        d, ev = matches[m]
        print(f"{labels[d]}  {minutes_to_pretty(ev['start'])}-{minutes_to_pretty(ev['end'])}")
        where = f" @ {ev['location']}" if (ev['location'] is not None and len(ev['location']) > 0) else ""
        print(f"  {ev['title']}{where}")
        m = m + 1
    print("")


# ---------- UI ----------
def print_header():
    """
    Print program header (FR1).
    """
    print("=" * 64)
    print(f"{PROGRAM_TITLE}")
    print(f"Author: {PROGRAM_AUTHOR} | Student ID: {STUDENT_ID} | UniSA email: {PROGRAM_EMAIL}")
    print("=" * 64)


def main_menu():
    """
    Show menu and return validated choice.
    """
    print("Menu:")
    print("  1. Add event")
    print("  2. Update event (by start time)")
    print("  3. Delete event (by start time)")
    print("  4. Print weekly overview")
    print("  5. Print one day (full details)")
    print("  6. Save timetable to file")
    print("  7. Load timetable from file")
    print("  8. Search events (title/location)")
    print("  9. Set week start day (Sun/Mon)")
    print("  0. Quit")
    return ask_menu_choice()


# ---------- Main ----------
def main():
    """
    Entry point. Only call main() at global level (NFR8).
    """
    state = default_state()
    print_header()
    running = True
    while running:
        choice = main_menu()
        if choice == 1:
            add_event(state)
        elif choice == 2:
            update_event(state)
        elif choice == 3:
            delete_event(state)
        elif choice == 4:
            print_week_overview(state)
        elif choice == 5:
            print_day_full(state)
        elif choice == 6:
            save_to_file(state)
        elif choice == 7:
            load_from_file(state)
        elif choice == 8:
            search_events(state)
        elif choice == 9:
            set_week_start(state)
        elif choice == 0:
            # no break; flip flag to exit cleanly (NFR3)
            running = False

    print("Goodbye!")


# Only global-level statement allowed (NFR8)
if __name__ == "__main__":
    main()
