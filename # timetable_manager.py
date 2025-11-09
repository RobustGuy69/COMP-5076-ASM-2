#
# File: main.py
# Author: The Duc Nguyen
# Student ID: 110482092
# Email ID: nguty494@mymail.unisa.edu.au
#
# This is my own work as defined by
#  the University's Academic Misconduct Policy.
#

PROGRAM_TITLE = "Weekly Timetable Manager"
PROGRAM_AUTHOR = "The Duc Nguyen"
STUDENT_ID = "110482092"
PROGRAM_EMAIL = "your_unisa_email_id"  # e.g., ngtd0001

def empty_week():
    return [list() for _ in range(7)]

def default_state():
    return {"week": empty_week(), "week_start": 1}  # 0=Sun, 1=Mon

def parse_time_to_minutes(text):
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
        if len(parts) != 2 or (not parts[0].isdigit()) or (not parts[1].isdigit()):
            return None
        hour, minute = int(parts[0]), int(parts[1])
    else:
        if not s.isdigit():
            return None
        hour, minute = int(s), 0
    if minute < 0 or minute > 59:
        return None
    if is_am or is_pm:
        if hour < 1 or hour > 12:
            return None
        hour = (0 if hour == 12 else hour) if is_am else (12 if hour == 12 else hour + 12)
    else:
        if hour < 0 or hour > 23:
            return None
    return hour * 60 + minute

def minutes_to_pretty(m):
    if m < 0:
        m = 0
    if m > 1439:
        m = 1439
    h24, mn = m // 60, m % 60
    am = h24 < 12
    h12 = h24 % 12 or 12
    return f"{h12}:{mn:02d}{'am' if am else 'pm'}"

def within_day_range(start_m, end_m):
    return 0 <= start_m < end_m <= 24 * 60

def abbreviate(s, max_len):
    if not s:
        return ""
    if len(s) <= max_len:
        return s
    return s[: max(1, max_len - 2)] + ".."

def get_days_view(week_start):
    base = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    labels, mapping, i = [None] * 7, [0] * 7, 0
    while i < 7:
        a = (week_start + i) % 7
        labels[i], mapping[i] = base[a], a
        i = i + 1
    return labels, mapping

def name_to_absolute_day(name3):
    base, i, found = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"], 0, -1
    while i < 7:
        if base[i].lower().startswith(name3.lower()):
            found = i
        i = i + 1
    return 0 if found == -1 else found

def ask_day_index(week_start):
    labels, mapping = get_days_view(week_start)
    i = 0
    print("Choose a day:")
    while i < 7:
        print(f"  {i+1}. {labels[i]}")
        i = i + 1
    chosen_ok, absolute_index = False, 0
    while not chosen_ok:
        raw = input("Enter number (1-7) or name (e.g., Mon): ").strip()
        if raw.isdigit():
            n = int(raw)
            if 1 <= n <= 7:
                absolute_index, chosen_ok = mapping[n - 1], True
            else:
                print("  Out of range. Choose 1..7.")
        else:
            name = raw.title()[:3]
            j, found = 0, -1
            while j < 7:
                if labels[j].lower().startswith(name.lower()):
                    found = j
                j = j + 1
            if found == -1:
                print("  Not a valid day. Try 'Mon', 'Tue', etc.")
            else:
                absolute_index, chosen_ok = mapping[found], True
    return absolute_index

def ask_time(prompt):
    ok, val = False, 0
    while not ok:
        t = parse_time_to_minutes(input(prompt).strip())
        if t is None:
            print("  Invalid time. Examples: 9, 9am, 9:30, 14:00, 3:15pm.")
        else:
            ok, val = True, t
    return val

def ask_menu_choice():
    ok, val = False, -1
    while not ok:
        s = input("Choose an option (0-9): ").strip()
        if s.isdigit():
            v = int(s)
            if 0 <= v <= 9:
                ok, val = True, v
            else:
                print("  Please choose a number 0..9.")
        else:
            print("  Please enter a number.")
    return val

def sort_day_events(day_events):
    i, n = 1, len(day_events)
    while i < n:
        key, j, done = day_events[i], i - 1, False
        while j >= 0 and (not done):
            if day_events[j]["start"] > key["start"]:
                day_events[j + 1] = day_events[j]
                j = j - 1
            else:
                done = True
        day_events[j + 1] = key
        i = i + 1

def has_overlap(evs, new_start, new_end, skip_index=-1):
    k = 0
    while k < len(evs):
        if k != skip_index:
            s, e = evs[k]["start"], evs[k]["end"]
            if (new_start < e) and (new_end > s):
                return True
        k = k + 1
    return False

def find_event_index_by_start(evs, start_m):
    i, found = 0, -1
    while i < len(evs):
        if evs[i]["start"] == start_m:
            found = i
        i = i + 1
    return found

def add_event(state):
    d = ask_day_index(state["week_start"])
    title = input("Title: ").strip()
    location = input("Where (optional): ").strip()
    start_m = ask_time("Start time (e.g., 9am, 13:00): ")
    end_m = ask_time("End time (e.g., 10am, 14:45): ")
    if not within_day_range(start_m, end_m):
        print("  Invalid time range. Start must be before end within the same day.")
        return
    evs = state["week"][d]
    if has_overlap(evs, start_m, end_m):
        print("  Overlap detected with an existing event. Please reschedule.")
        return
    evs.append({"title": title, "start": start_m, "end": end_m, "location": location})
    sort_day_events(evs)
    print("  Event added.")

def update_event(state):
    d = ask_day_index(state["week_start"])
    evs = state["week"][d]
    if len(evs) == 0:
        print("  No events to update on that day.")
        return
    print_day_list(state, d, full=False)
    target = ask_time("Enter START time of the event to update: ")
    idx = find_event_index_by_start(evs, target)
    if idx == -1:
        print("  No event found with that start time.")
        return
    ev = evs[idx]
    print("Leave a field empty to keep existing value.")
    new_title = input(f"New title [{ev['title']}]: ").strip()
    new_loc = input(f"New where [{ev['location']}]: ").strip()
    raw_start = input(f"New start [{minutes_to_pretty(ev['start'])}]: ").strip()
    raw_end = input(f"New end [{minutes_to_pretty(ev['end'])}]: ").strip()
    title = ev["title"] if new_title == "" else new_title
    loc = ev["location"] if new_loc == "" else new_loc
    if raw_start == "":
        start_m = ev["start"]
    else:
        t = parse_time_to_minutes(raw_start)
        if t is None:
            print("  Invalid new start time. Update cancelled."); return
        start_m = t
    if raw_end == "":
        end_m = ev["end"]
    else:
        t = parse_time_to_minutes(raw_end)
        if t is None:
            print("  Invalid new end time. Update cancelled."); return
        end_m = t
    if not within_day_range(start_m, end_m):
        print("  Invalid time range. Update cancelled."); return
    if has_overlap(evs, start_m, end_m, skip_index=idx):
        print("  Overlap detected. Update cancelled."); return
    ev.update({"title": title, "location": loc, "start": start_m, "end": end_m})
    sort_day_events(evs)
    print("  Event updated.")

def delete_event(state):
    d = ask_day_index(state["week_start"])
    evs = state["week"][d]
    if len(evs) == 0:
        print("  No events to delete on that day.")
        return
    print_day_list(state, d, full=False)
    target = ask_time("Enter START time of the event to delete: ")
    idx = find_event_index_by_start(evs, target)
    if idx == -1:
        print("  No event with that start time.")
        return
    if input("Confirm delete? (y/n): ").strip().lower() == "y":
        new_list, i = [], 0
        while i < len(evs):
            if i != idx:
                new_list.append(evs[i])
            i = i + 1
        state["week"][d] = new_list
        print("  Event deleted.")
    else:
        print("  Delete cancelled.")

def print_week_overview(state):
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
                t1, t2 = minutes_to_pretty(ev["start"]), minutes_to_pretty(ev["end"])
                title = abbreviate(ev["title"], 18)
                where = abbreviate(ev["location"], 12)
                where_str = f" @ {where}" if where else ""
                print(f"  {t1}-{t2}  {title}{where_str}")
                k = k + 1
        i = i + 1
    print("")

def print_day_full(state):
    d = ask_day_index(state["week_start"])
    print_day_list(state, d, full=True)

def print_day_list(state, day_idx, full):
    labels = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    print(f"\n=== {labels[day_idx]} ===")
    evs = state["week"][day_idx]
    if len(evs) == 0:
        print("  (no events)\n"); return
    i = 0
    while i < len(evs):
        ev = evs[i]
        t1, t2 = minutes_to_pretty(ev["start"]), minutes_to_pretty(ev["end"])
        if full:
            where = f"\n  Where: {ev['location']}" if ev["location"] else ""
            print(f"- {ev['title']}\n  When: {t1} - {t2}{where}\n")
        else:
            where = f" @ {ev['location']}" if ev["location"] else ""
            print(f"  {t1}-{t2}  {ev['title']}{where}")
        i = i + 1

def sanitize_pipe(text):
    return "" if text is None else text.replace("|", "／")

def restore_pipe(text):
    return "" if text is None else text.replace("／", "|")

def save_to_file(state):
    name = input("Enter filename to SAVE (e.g., my_timetable.txt): ").strip()
    if name == "":
        print("  Save cancelled."); return
    lines = [f"WEEK_START:{state['week_start']}"]
    labels, d = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"], 0
    while d < 7:
        lines.append(f"DAY:{labels[d]}")
        evs, i = state["week"][d], 0
        while i < len(evs):
            ev = evs[i]
            lines.append(f"{sanitize_pipe(ev['title'])}|{ev['start']}|{ev['end']}|{sanitize_pipe(ev['location'])}")
            i = i + 1
        d = d + 1
    try:
        fh, i = open(name, "w", encoding="utf-8"), 0
        while i < len(lines):
            fh.write(lines[i] + "\n")
            i = i + 1
        fh.close()
        print("  Saved.")
    except Exception:
        print("  Error saving file (check path/permissions).")

def load_from_file(state):
    name = input("Enter filename to LOAD (e.g., my_timetable.txt): ").strip()
    if name == "":
        print("  Load cancelled."); return
    try:
        fh = open(name, "r", encoding="utf-8")
        lines = fh.readlines()
        fh.close()
    except Exception:
        print("  Could not open file."); return
    new_week, new_start, current_day = empty_week(), state["week_start"], -1
    i = 0
    while i < len(lines):
        raw = lines[i].rstrip("\n")
        if raw.startswith("WEEK_START:"):
            ws = raw.split(":")[1].strip()
            if ws.isdigit():
                v = int(ws)
                if v in (0, 1):
                    new_start = v
        elif raw.startswith("DAY:"):
            current_day = name_to_absolute_day(raw.split(":")[1].strip().title()[:3])
        else:
            if current_day != -1 and "|" in raw:
                p = raw.split("|")
                if len(p) == 4 and p[1].isdigit() and p[2].isdigit():
                    title = restore_pipe(p[0])
                    start_m, end_m = int(p[1]), int(p[2])
                    location = restore_pipe(p[3])
                    if within_day_range(start_m, end_m) and (not has_overlap(new_week[current_day], start_m, end_m)):
                        new_week[current_day].append(
                            {"title": title, "start": start_m, "end": end_m, "location": location}
                        )
                        sort_day_events(new_week[current_day])
        i = i + 1
    state["week"], state["week_start"] = new_week, new_start
    print("  Loaded timetable.")

def set_week_start(state):
    print("Choose week start day:\n  1. Sunday\n  2. Monday")
    ok, choice = False, 0
    while not ok:
        s = input("Enter 1 or 2: ").strip()
        if s == "1":
            choice, ok = 0, True
        elif s == "2":
            choice, ok = 1, True
        else:
            print("  Please enter 1 or 2.")
    state["week_start"] = choice
    print("  Week start updated.")

def search_events(state):
    kw = input("Enter keyword to search (title/location): ").strip().lower()
    if kw == "":
        print("  Empty keyword; search cancelled."); return
    matches, d = [], 0
    while d < 7:
        evs, i = state["week"][d], 0
        while i < len(evs):
            ev = evs[i]
            if (kw in ev["title"].lower()) or (kw in (ev["location"] or "").lower()):
                matches.append((d, ev))
            i = i + 1
        d = d + 1
    j = 0
    while j < len(matches):
        m_idx, k = j, j + 1
        while k < len(matches):
            d1, e1 = matches[m_idx]
            d2, e2 = matches[k]
            if (d2 < d1) or (d2 == d1 and e2["start"] < e1["start"]):
                m_idx = k
            k = k + 1
        tmp = matches[j]
        matches[j] = matches[m_idx]
        matches[m_idx] = tmp
        j = j + 1
    if len(matches) == 0:
        print("  No matches."); return
    labels, m = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"], 0
    print("\n=== Search Results ===")
    while m < len(matches):
        d, ev = matches[m]
        where = f" @ {ev['location']}" if ev["location"] else ""
        print(f"{labels[d]}  {minutes_to_pretty(ev['start'])}-{minutes_to_pretty(ev['end'])}\n  {ev['title']}{where}")
        m = m + 1
    print("")

def print_header():
    print("=" * 64)
    print(PROGRAM_TITLE)
    print(f"Author: {PROGRAM_AUTHOR} | Student ID: {STUDENT_ID} | UniSA email: {PROGRAM_EMAIL}")
    print("=" * 64)

def main_menu():
    print(
        "Menu:\n"
        "  1. Add event\n"
        "  2. Update event (by start time)\n"
        "  3. Delete event (by start time)\n"
        "  4. Print weekly overview\n"
        "  5. Print one day (full details)\n"
        "  6. Save timetable to file\n"
        "  7. Load timetable from file\n"
        "  8. Search events (title/location)\n"
        "  9. Set week start day (Sun/Mon)\n"
        "  0. Quit"
    )
    return ask_menu_choice()

def main():
    state, running = default_state(), True
    print_header()
    while running:
        c = main_menu()
        if c == 1:
            add_event(state)
        elif c == 2:
            update_event(state)
        elif c == 3:
            delete_event(state)
        elif c == 4:
            print_week_overview(state)
        elif c == 5:
            print_day_full(state)
        elif c == 6:
            save_to_file(state)
        elif c == 7:
            load_from_file(state)
        elif c == 8:
            search_events(state)
        elif c == 9:
            set_week_start(state)
        elif c == 0:
            running = False
    print("Goodbye!")

if __name__ == "__main__":
    main()


