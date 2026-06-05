import re
from datetime import datetime, timedelta, date

def calculate_ai_priority(due_date_str, priority, estimated_time, category, is_goal=False):
    """
    Calculates an AI prioritization score (0 to 100) based on multiple factors.
    """
    score = 0
    
    # Factor 1: Priority Level (Max 40 points)
    priority_weights = {
        'Critical': 40,
        'High': 30,
        'Medium': 20,
        'Low': 10
    }
    score += priority_weights.get(priority, 10)
    
    # Factor 2: Due Date Urgency & Overdue status (Max 30 points)
    try:
        due_dt = datetime.strptime(due_date_str, "%Y-%m-%d %H:%M:%S")
        now = datetime.now()
        
        if now > due_dt:
            # Overdue
            score += 30
        else:
            time_diff = due_dt - now
            hours_left = time_diff.total_seconds() / 3600.0
            
            if hours_left <= 6:
                score += 30
            elif hours_left <= 12:
                score += 25
            elif hours_left <= 24:
                score += 20
            elif hours_left <= 48:
                score += 15
            elif hours_left <= 72:
                score += 10
            else:
                score += 5
    except Exception:
        # Fallback if due date parsing fails
        score += 10
        
    # Factor 3: Estimated Effort (Max 15 points)
    # Quick wins (short tasks under 2 hours) get a bonus to clear the queue, 
    # but very long tasks (> 6 hours) get a smaller urgency bump to start early.
    est_time = float(estimated_time) if estimated_time else 1.0
    if est_time <= 1.0:
        score += 15 # High priority to quick actions
    elif est_time <= 2.0:
        score += 10
    elif est_time <= 5.0:
        score += 5
    else:
        score += 2
        
    # Factor 4: User-defined goals or category focus (Max 15 points)
    # Goals or specific categories receive extra importance
    if is_goal:
        score += 15
    elif category in ['Work', 'Study']:
        score += 8
    else:
        score += 5
        
    return min(float(score), 100.0)

def parse_natural_language_task(text):
    """
    Parses natural language strings to extract task metadata:
    Title, Due Date, Priority, Category
    
    Example: "Finish project proposal by tomorrow 4 PM critical work"
    Returns: {
        'title': 'Finish project proposal',
        'due_date': datetime object,
        'priority': 'Critical',
        'category': 'Work'
    }
    """
    clean_text = text.strip()
    
    # 1. Extract Priority (default: Medium)
    priority = 'Medium'
    priorities_map = {
        r'\bcritical\b': 'Critical',
        r'\burgent\b': 'Critical',
        r'\bhigh priority\b': 'High',
        r'\bhigh\b': 'High',
        r'\bmedium priority\b': 'Medium',
        r'\bmedium\b': 'Medium',
        r'\bnormal\b': 'Medium',
        r'\blow priority\b': 'Low',
        r'\blow\b': 'Low',
        r'\beasy\b': 'Low'
    }
    for pattern, p_val in priorities_map.items():
        if re.search(pattern, clean_text, re.IGNORECASE):
            priority = p_val
            clean_text = re.sub(pattern, '', clean_text, flags=re.IGNORECASE)
            break
            
    # 2. Extract Category (default: Personal)
    category = 'Personal'
    categories_map = {
        r'\bwork\b': 'Work',
        r'\boffice\b': 'Work',
        r'\bjob\b': 'Work',
        r'\bmeeting\b': 'Work',
        r'\bstudy\b': 'Study',
        r'\bexam\b': 'Study',
        r'\bassignment\b': 'Study',
        r'\bread\b': 'Study',
        r'\bcourse\b': 'Study',
        r'\blearn\b': 'Study',
        r'\bpersonal\b': 'Personal',
        r'\blife\b': 'Personal',
        r'\bhome\b': 'Personal',
        r'\bhealth\b': 'Health',
        r'\bworkout\b': 'Health',
        r'\bgym\b': 'Health',
        r'\brun\b': 'Health',
        r'\bdoctor\b': 'Health',
        r'\bexercise\b': 'Health',
        r'\bfinance\b': 'Finance',
        r'\bbill\b': 'Finance',
        r'\bpay\b': 'Finance',
        r'\bbank\b': 'Finance',
        r'\bmoney\b': 'Finance',
        r'\btax\b': 'Finance'
    }
    for pattern, c_val in categories_map.items():
        if re.search(pattern, clean_text, re.IGNORECASE):
            category = c_val
            clean_text = re.sub(pattern, '', clean_text, flags=re.IGNORECASE)
            break

    # 3. Extract Due Date and Time
    now = datetime.now()
    target_date = now.date()
    target_time = datetime.strptime("17:00:00", "%H:%M:%S").time() # Default 5 PM
    
    # Look for dates
    date_parsed = False
    
    # "tomorrow"
    if re.search(r'\btomorrow\b', clean_text, re.IGNORECASE):
        target_date = now.date() + timedelta(days=1)
        clean_text = re.sub(r'\btomorrow\b', '', clean_text, flags=re.IGNORECASE)
        date_parsed = True
    # "today"
    elif re.search(r'\btoday\b', clean_text, re.IGNORECASE):
        target_date = now.date()
        clean_text = re.sub(r'\btoday\b', '', clean_text, flags=re.IGNORECASE)
        date_parsed = True
    # Weekdays: monday, tuesday, etc.
    else:
        weekdays = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        for day, weekday_num in weekdays.items():
            pattern = rf'\bby\s+{day}\b|\bon\s+{day}\b|\b{day}\b'
            if re.search(pattern, clean_text, re.IGNORECASE):
                # Calculate next occurrence of this day
                curr_weekday = now.weekday()
                days_ahead = weekday_num - curr_weekday
                if days_ahead <= 0: # Already passed or is today, go to next week
                    days_ahead += 7
                target_date = now.date() + timedelta(days=days_ahead)
                clean_text = re.sub(pattern, '', clean_text, flags=re.IGNORECASE)
                date_parsed = True
                break

    # Look for times: "at 5 PM", "by 14:30", "at 9am", "5pm"
    time_match = re.search(r'(?:at|by)?\s*(\d{1,2})(?::(\d{2}))?\s*(am|pm|AM|PM)?\b', clean_text)
    if time_match:
        # Ensure we didn't just match a random digit inside a word
        matched_str = time_match.group(0).strip()
        # Avoid matching small numbers that are part of other concepts unless explicitly formatted
        if re.match(r'^\d+$', matched_str) and int(matched_str) > 12:
            # Probably a random number, ignore
            pass
        else:
            hr = int(time_match.group(1))
            mn = int(time_match.group(2)) if time_match.group(2) else 0
            ampm = time_match.group(3)
            
            if ampm:
                ampm = ampm.lower()
                if ampm == 'pm' and hr < 12:
                    hr += 12
                elif ampm == 'am' and hr == 12:
                    hr = 0
            else:
                # No am/pm, if hour is < 8, assume PM (e.g. 5 means 5 PM)
                if hr < 8:
                    hr += 12
                    
            if 0 <= hr < 24 and 0 <= mn < 60:
                target_time = datetime.strptime(f"{hr:02d}:{mn:02d}:00", "%H:%M:%S").time()
                clean_text = clean_text.replace(time_match.group(0), '')

    # Clean up excess spaces/prepositions (by, on, at, for)
    clean_text = re.sub(r'\b(by|on|at|for|to|the)\b', '', clean_text, flags=re.IGNORECASE)
    # Remove extra spaces
    title = ' '.join(clean_text.split())
    if not title:
        title = "New Task"
        
    due_datetime = datetime.combine(target_date, target_time)
    
    return {
        'title': title,
        'due_date': due_datetime,
        'priority': priority,
        'category': category
    }

def generate_ai_subtasks(title, category):
    """
    AI Subtask breakdown heuristics based on text keywords and categories.
    Returns 4 progressive subtasks.
    """
    title_lower = title.lower()
    
    # 1. Dev / Tech Tasks
    if any(k in title_lower for k in ['build', 'develop', 'website', 'app', 'code', 'program', 'software', 'git']):
        return [
            "Research requirements, set up folder structure & Git repo",
            "Design UI mockup and schema / data models",
            "Write core logic & style user interface",
            "Perform testing, fix bugs & deploy application"
        ]
    
    # 2. Writing / Report / Documentation Tasks
    if any(k in title_lower for k in ['write', 'paper', 'report', 'essay', 'draft', 'article', 'thesis', 'blog']):
        return [
            "Gather sources, references & brainstorm structure",
            "Create detailed outline & section headers",
            "Write first complete draft (focus on flow, not perfection)",
            "Proofread, edit grammar & format citations / submission details"
        ]

    # 3. Learning / Academic / Study Tasks
    if any(k in title_lower for k in ['study', 'learn', 'exam', 'read', 'class', 'course', 'quiz', 'assignment', 'homework']):
        return [
            "Gather learning materials (lecture slides, notes, textbook chapters)",
            "Review key concepts, write summaries / flashcards",
            "Solve practice questions or outline assignment answers",
            "Review challenging concepts and complete final review quiz / submit assignment"
        ]

    # 4. Fitness / Workout / Health
    if any(k in title_lower for k in ['workout', 'gym', 'exercise', 'run', 'cardio', 'stretch', 'training', 'fit']):
        return [
            "Prepare gym clothes, water bottle & select workout routine / music",
            "Warm up with light cardio and stretching (10 mins)",
            "Complete core workout set (resistance or targeted cardio)",
            "Cool down, hydrate, and stretch (5-10 mins)"
        ]

    # 5. Shopping / Groceries
    if any(k in title_lower for k in ['buy', 'shop', 'groceries', 'market', 'store', 'purchase', 'order']):
        return [
            "Check current inventory and draft shopping list",
            "Select shop/online platform & set a budget",
            "Locate/order items and pay",
            "Organize purchased items and clean up packaging"
        ]

    # 6. Cleaning / Organizing
    if any(k in title_lower for k in ['clean', 'room', 'house', 'organize', 'tidy', 'wash', 'laundry', 'fold']):
        return [
            "Gather cleaning supplies and put away clutter",
            "Dust surfaces, clean counters, and wipe down mirrors",
            "Vacuum, sweep, or mop floors",
            "Empty garbage bins and set up clean organizational layout"
        ]

    # Category fallback
    if category == 'Work':
        return [
            "Define objective & outline success criteria",
            "Gather inputs and discuss with stakeholders if needed",
            "Draft core deliverable / execute primary work blocks",
            "Self-review, format, and present / submit final outcome"
        ]
    elif category == 'Study':
        return [
            "Identify study scope & clear study space",
            "Read textbook pages / view lecture videos & take notes",
            "Explain key ideas in own words or write code examples",
            "Complete exercises & review errors"
        ]
    elif category == 'Finance':
        return [
            "Gather financial statements / bills & check bank balance",
            "Validate amounts, calculations, and due dates",
            "Process payments or update budget spreadsheet",
            "Save receipts and file records / set calendar alerts"
        ]
    elif category == 'Health':
        return [
            "Research healthy guidelines / prepare necessary gear",
            "Execute health check / log baseline metrics",
            "Follow through with action item (activity, meal, appointment)",
            "Log feedback / evaluate physical/mental response"
        ]
        
    # Absolute Fallback
    return [
        "Plan execution strategy and gather resources",
        "Complete initial draft / foundation steps",
        "Refine work, solve blockers, and polish details",
        "Perform final quality check & mark complete"
    ]

def generate_ai_daily_planner(tasks_list, start_hour=8):
    """
    Generates an hour-by-hour planner list combining tasks and standard meals.
    Filters tasks for today (or pending sorted by priority score).
    """
    # Filter pending or in progress tasks
    active_tasks = [t for t in tasks_list if t['status'] != 'Completed']
    # Sort by AI score descending
    active_tasks.sort(key=lambda x: x['ai_score'], reverse=True)
    
    schedule = []
    
    # Define fixed standard meals
    meals = [
        {'time_val': 8.5, 'label': '🍳 Breakfast', 'duration': 0.5, 'type': 'meal'},
        {'time_val': 13.0, 'label': '🥗 Lunch', 'duration': 1.0, 'type': 'meal'},
        {'time_val': 19.5, 'label': '🍽️ Dinner', 'duration': 1.0, 'type': 'meal'},
    ]
    
    current_time = float(start_hour)
    
    # We allocate tasks around meals
    task_idx = 0
    
    while current_time < 22.0: # End planning at 10 PM
        # Check if a meal is scheduled at this current time
        meal_found = None
        for m in meals:
            if abs(current_time - m['time_val']) < 0.1:
                meal_found = m
                break
                
        if meal_found:
            schedule.append({
                'start_time': format_time_float(current_time),
                'end_time': format_time_float(current_time + meal_found['duration']),
                'title': meal_found['label'],
                'type': 'Meal',
                'id': None
            })
            current_time += meal_found['duration']
            continue
            
        # Check if the next meal starts before our default task time block ends
        next_meal = None
        for m in meals:
            if m['time_val'] > current_time:
                if not next_meal or m['time_val'] < next_meal['time_val']:
                    next_meal = m
                    
        # If we have tasks left
        if task_idx < len(active_tasks):
            task = active_tasks[task_idx]
            est_hours = float(task['estimated_time']) if task['estimated_time'] else 1.0
            
            # Bound check: does it overlap with next meal?
            available_time = 22.0 - current_time
            if next_meal:
                available_time = next_meal['time_val'] - current_time
                
            if available_time >= 0.5:
                # We can fit a part of or the whole task here
                duration = min(est_hours, available_time)
                schedule.append({
                    'start_time': format_time_float(current_time),
                    'end_time': format_time_float(current_time + duration),
                    'title': f"💻 {task['title']}" if task['category'] == 'Work' else f"📚 {task['title']}" if task['category'] == 'Study' else f"🎯 {task['title']}",
                    'type': 'Task',
                    'id': task['id'],
                    'priority': task['priority'],
                    'category': task['category']
                })
                current_time += duration
                task_idx += 1
            else:
                # Too small of a slot before the next meal, let's fast forward to meal
                if next_meal:
                    current_time = next_meal['time_val']
                else:
                    current_time += 0.5
        else:
            # No tasks left, inject free time/wellness blocks
            available_time = 22.0 - current_time
            if next_meal:
                available_time = next_meal['time_val'] - current_time
                
            if available_time >= 0.5:
                schedule.append({
                    'start_time': format_time_float(current_time),
                    'end_time': format_time_float(current_time + available_time),
                    'title': "🧘 Free Time / Relaxation",
                    'type': 'Buffer',
                    'id': None
                })
                current_time += available_time
            elif next_meal:
                current_time = next_meal['time_val']
            else:
                current_time += 0.5
                
    return schedule

def format_time_float(time_val):
    """Formats float hours like 13.5 into '01:30 PM'"""
    hours = int(time_val)
    minutes = int((time_val - hours) * 60)
    
    suffix = 'AM'
    if hours >= 12:
        suffix = 'PM'
        if hours > 12:
            hours -= 12
    elif hours == 0:
        hours = 12
        
    return f"{hours:02d}:{minutes:02d} {suffix}"

def get_meal_timing_suggestions(schedule_events):
    """
    Analyzes the daily schedule. If high priority tasks are occurring 
    immediately after or during standard meal hours, suggests custom shifts.
    """
    suggestions = []
    
    # Look for tasks near or overlapping Breakfast (8:30), Lunch (13:00), Dinner (19:30)
    # Check if a critical task is adjacent
    for event in schedule_events:
        if event['type'] == 'Task' and event.get('priority') in ['High', 'Critical']:
            # Check if task runs through standard hours
            # We can provide smart suggestions based on categories
            if "12:00 PM" in event['start_time'] or "01:00 PM" in event['start_time'] or "02:00 PM" in event['start_time']:
                suggestions.append(
                    f"⚠️ **High energy demand detected:** You have a **{event['priority']}** task *'{event['title'][2:]}'* near lunchtime. "
                    "We recommend eating a nutritious, low-glycemic lunch 30 minutes earlier (around 12:30 PM) to avoid afternoon brain fog."
                )
                break
                
    # Add a healthy meal guideline default if no schedule conflict is found
    if not suggestions:
        suggestions.append(
            "💡 **AI Healthy Habits Tip:** Maintain a minimum of 4 hours between major meals to allow proper digestion. "
            "Hydrate with at least 500ml of water between Breakfast and Lunch."
        )
    else:
        suggestions.append(
            "💡 **AI Wellness Alert:** Remember to stand up and stretch for 5 minutes after completing each high-intensity task block."
        )
        
    return suggestions

if __name__ == "__main__":
    # Small test
    parsed = parse_natural_language_task("finish streamlit app design tomorrow at 3:30 pm critical work")
    print("Parsed NLP Result:")
    print("Title:", parsed['title'])
    print("Due:", parsed['due_date'])
    print("Priority:", parsed['priority'])
    print("Category:", parsed['category'])
    
    score = calculate_ai_priority(parsed['due_date'].strftime("%Y-%m-%d %H:%M:%S"), parsed['priority'], 2.0, parsed['category'])
    print("AI Priority Score:", score)
    
    subtasks = generate_ai_subtasks(parsed['title'], parsed['category'])
    print("Subtasks breakdown:")
    for st in subtasks:
        print(" -", st)
