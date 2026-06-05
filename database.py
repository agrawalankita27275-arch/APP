import sqlite3
import os
from datetime import datetime, date, timedelta

DB_PATH = "tracker.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Tasks table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        due_date TEXT NOT NULL,
        priority TEXT NOT NULL,
        category TEXT NOT NULL,
        estimated_time REAL,
        ai_score REAL DEFAULT 0,
        status TEXT NOT NULL DEFAULT 'Pending',
        completed_at TEXT,
        xp_awarded INTEGER DEFAULT 0
    )
    """)
    
    # Subtasks table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS subtasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        completed INTEGER NOT NULL DEFAULT 0,
        FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE CASCADE
    )
    """)
    
    # Meals table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS meals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        type TEXT NOT NULL, -- 'Breakfast', 'Lunch', 'Dinner', 'Snack'
        description TEXT,
        completed INTEGER NOT NULL DEFAULT 0,
        healthy_tag TEXT NOT NULL DEFAULT 'Neutral', -- 'Healthy', 'Neutral', 'Unhealthy'
        timestamp TEXT NOT NULL
    )
    """)
    
    # User Profile table (for storing XP, levels, streaks)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_profile (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )
    """)
    
    # Badges table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS badges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        badge_name TEXT UNIQUE NOT NULL,
        badge_description TEXT NOT NULL,
        date_earned TEXT NOT NULL,
        icon TEXT NOT NULL
    )
    """)
    
    # Initialize default user profile keys if empty
    cursor.execute("SELECT count(*) FROM user_profile")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO user_profile (key, value) VALUES (?, ?)", [
            ('xp', '0'),
            ('level', '1'),
            ('task_streak', '0'),
            ('meal_streak', '0'),
            ('last_task_completed_date', ''),
            ('last_meal_streak_date', '')
        ])
    
    conn.commit()
    conn.close()

# XP & Level Mechanics
def get_user_stats():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM user_profile")
    stats = {row[0]: row[1] for row in cursor.fetchall()}
    conn.close()
    
    # Ensure stats values are typed correctly
    xp = int(stats.get('xp', 0))
    level = int(stats.get('level', 1))
    task_streak = int(stats.get('task_streak', 0))
    meal_streak = int(stats.get('meal_streak', 0))
    
    return {
        'xp': xp,
        'level': level,
        'task_streak': task_streak,
        'meal_streak': meal_streak,
        'last_task_completed_date': stats.get('last_task_completed_date', ''),
        'last_meal_streak_date': stats.get('last_meal_streak_date', '')
    }

def add_xp(amount):
    conn = get_connection()
    cursor = conn.cursor()
    
    stats = get_user_stats()
    new_xp = stats['xp'] + amount
    # Level formula: Every 200 XP is a level. Level = (XP // 200) + 1
    new_level = (new_xp // 200) + 1
    
    cursor.execute("UPDATE user_profile SET value = ? WHERE key = 'xp'", (str(new_xp),))
    
    level_up = False
    if new_level > stats['level']:
        cursor.execute("UPDATE user_profile SET value = ? WHERE key = 'level'", (str(new_level),))
        level_up = True
        
    conn.commit()
    conn.close()
    return level_up, new_xp, new_level

# Task Operations
def add_task(title, description, due_date, priority, category, estimated_time, ai_score):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO tasks (title, description, due_date, priority, category, estimated_time, ai_score, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, 'Pending')
    """, (title, description, due_date, priority, category, estimated_time, ai_score))
    task_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return task_id

def get_tasks(status=None):
    conn = get_connection()
    cursor = conn.cursor()
    if status:
        cursor.execute("SELECT * FROM tasks WHERE status = ? ORDER BY ai_score DESC, due_date ASC", (status,))
    else:
        cursor.execute("SELECT * FROM tasks ORDER BY ai_score DESC, due_date ASC")
    
    columns = [col[0] for col in cursor.description]
    tasks = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    return tasks

def get_task_by_id(task_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    columns = [col[0] for col in cursor.description]
    task = dict(zip(columns, row))
    conn.close()
    return task

def delete_task(task_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    cursor.execute("DELETE FROM subtasks WHERE task_id = ?", (task_id,))
    conn.commit()
    conn.close()

def edit_task(task_id, title, description, due_date, priority, category, estimated_time, ai_score):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE tasks 
    SET title = ?, description = ?, due_date = ?, priority = ?, category = ?, estimated_time = ?, ai_score = ?
    WHERE id = ?
    """, (title, description, due_date, priority, category, estimated_time, ai_score, task_id))
    conn.commit()
    conn.close()

def update_task_status(task_id, status):
    conn = get_connection()
    cursor = conn.cursor()
    
    current_task = get_task_by_id(task_id)
    if not current_task:
        conn.close()
        return 0, False
        
    old_status = current_task['status']
    
    if old_status == status:
        conn.close()
        return 0, False
        
    xp_gained = 0
    level_up = False
    completed_time = None
    
    if status == 'Completed':
        completed_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Calculate XP based on priority
        priority_xp = {
            'Low': 20,
            'Medium': 50,
            'High': 80,
            'Critical': 120
        }.get(current_task['priority'], 20)
        
        # Add AI score bonus
        ai_bonus = int(current_task['ai_score'] * 0.1) * 10
        xp_gained = priority_xp + ai_bonus
        
        # Check if completed before deadline
        due_dt = datetime.strptime(current_task['due_date'], "%Y-%m-%d %H:%M:%S")
        if datetime.now() <= due_dt:
            xp_gained += 20 # On-time bonus
            
        cursor.execute("UPDATE tasks SET status = ?, completed_at = ?, xp_awarded = ? WHERE id = ?", 
                       (status, completed_time, xp_gained, task_id))
        
        # Check and update Task Streak
        level_up = update_task_streak(cursor)
        
    else: # Reverted to Pending / In Progress
        xp_to_remove = current_task['xp_awarded']
        xp_gained = -xp_to_remove
        cursor.execute("UPDATE tasks SET status = ?, completed_at = NULL, xp_awarded = 0 WHERE id = ?", 
                       (status, task_id))
        # Streak calculations will adjust dynamically next time
        
    conn.commit()
    conn.close()
    
    if xp_gained != 0:
        lvl_up, _, _ = add_xp(xp_gained)
        level_up = level_up or lvl_up
        
    # Trigger badge check
    check_and_award_badges()
        
    return xp_gained, level_up

# Subtask Operations
def add_subtask(task_id, title):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO subtasks (task_id, title, completed) VALUES (?, ?, 0)", (task_id, title))
    conn.commit()
    conn.close()

def get_subtasks(task_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM subtasks WHERE task_id = ?", (task_id,))
    columns = [col[0] for col in cursor.description]
    subtasks = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    return subtasks

def toggle_subtask(subtask_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT completed, task_id FROM subtasks WHERE id = ?", (subtask_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return
    new_completed = 1 if row[0] == 0 else 0
    task_id = row[1]
    
    cursor.execute("UPDATE subtasks SET completed = ? WHERE id = ?", (new_completed, subtask_id))
    conn.commit()
    
    # Check if all subtasks for this task are completed
    cursor.execute("SELECT count(*) FROM subtasks WHERE task_id = ?", (task_id,))
    total_subtasks = cursor.fetchone()[0]
    cursor.execute("SELECT count(*) FROM subtasks WHERE task_id = ? AND completed = 1", (task_id,))
    completed_subtasks = cursor.fetchone()[0]
    
    conn.close()
    
    # Award small XP for subtask completion
    if new_completed == 1:
        add_xp(5)
        
    # If all completed and task is not completed, we don't auto-complete the main task,
    # but we give a nice bonus (+15 XP) if the user completes the main task while subtasks are all completed.
    if total_subtasks > 0 and total_subtasks == completed_subtasks:
        add_xp(15) # Bonus for completing all subtasks!

# Meal Operations
def log_meal(meal_date, meal_type, description, completed, healthy_tag):
    conn = get_connection()
    cursor = conn.cursor()
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Check if this meal type already exists for the day
    cursor.execute("SELECT id, completed FROM meals WHERE date = ? AND type = ?", (meal_date, meal_type))
    row = cursor.fetchone()
    
    xp_gained = 0
    
    if row:
        meal_id = row[0]
        was_completed = row[1]
        
        cursor.execute("""
        UPDATE meals 
        SET description = ?, completed = ?, healthy_tag = ?, timestamp = ?
        WHERE id = ?
        """, (description, completed, healthy_tag, timestamp, meal_id))
        
        # XP adjustments
        if not was_completed and completed:
            xp_gained += 10 # Meal completed XP
            if healthy_tag == 'Healthy':
                xp_gained += 5 # Healthy option bonus
        elif was_completed and not completed:
            xp_gained -= 10
            if healthy_tag == 'Healthy':
                xp_gained -= 5
    else:
        cursor.execute("""
        INSERT INTO meals (date, type, description, completed, healthy_tag, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (meal_date, meal_type, description, completed, healthy_tag, timestamp))
        
        if completed:
            xp_gained += 10
            if healthy_tag == 'Healthy':
                xp_gained += 5
                
    conn.commit()
    conn.close()
    
    level_up = False
    if xp_gained != 0:
        lvl_up, _, _ = add_xp(xp_gained)
        level_up = level_up or lvl_up
        
    # Check daily meal completion bonus
    meal_bonus_gained, bonus_lvl_up = check_daily_meal_bonus(meal_date)
    level_up = level_up or bonus_lvl_up
    
    # Check and update Meal Streaks
    streak_lvl_up = update_meal_streak()
    level_up = level_up or streak_lvl_up
    
    check_and_award_badges()
    
    return xp_gained + (50 if meal_bonus_gained else 0), level_up

def get_meals_for_day(meal_date):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM meals WHERE date = ?", (meal_date,))
    columns = [col[0] for col in cursor.description]
    meals = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    return meals

def check_daily_meal_bonus(meal_date):
    # If Breakfast, Lunch, and Dinner are completed, give a +50 XP bonus once.
    # We will use user_profile key 'meal_bonus_<date>' to track if already awarded.
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT value FROM user_profile WHERE key = ?", (f"meal_bonus_{meal_date}",))
    bonus_row = cursor.fetchone()
    if bonus_row and bonus_row[0] == '1':
        conn.close()
        return False, False
        
    cursor.execute("""
    SELECT count(*) FROM meals 
    WHERE date = ? AND type IN ('Breakfast', 'Lunch', 'Dinner') AND completed = 1
    """, (meal_date,))
    count = cursor.fetchone()[0]
    
    if count == 3:
        # Award bonus
        cursor.execute("INSERT OR REPLACE INTO user_profile (key, value) VALUES (?, '1')", (f"meal_bonus_{meal_date}",))
        conn.commit()
        conn.close()
        lvl_up, _, _ = add_xp(50)
        return True, lvl_up
        
    conn.close()
    return False, False

# Streak Calculations
def update_task_streak(cursor):
    # Run within transaction
    today_str = date.today().isoformat()
    yesterday_str = (date.today() - timedelta(days=1)).isoformat()
    
    cursor.execute("SELECT value FROM user_profile WHERE key = 'last_task_completed_date'")
    last_date = cursor.fetchone()[0]
    
    cursor.execute("SELECT value FROM user_profile WHERE key = 'task_streak'")
    current_streak = int(cursor.fetchone()[0])
    
    if last_date == today_str:
        # Already processed today
        return False
        
    level_up = False
    if last_date == yesterday_str:
        # Consecutive day!
        new_streak = current_streak + 1
        cursor.execute("UPDATE user_profile SET value = ? WHERE key = 'task_streak'", (str(new_streak),))
        cursor.execute("UPDATE user_profile SET value = ? WHERE key = 'last_task_completed_date'", (today_str,))
        
        # Streak milestones reward
        if new_streak in [3, 7, 14, 30]:
            lvl_up, _, _ = add_xp(new_streak * 10)
            level_up = lvl_up
    else:
        # Streak broken or first completion
        new_streak = 1
        cursor.execute("UPDATE user_profile SET value = ? WHERE key = 'task_streak'", ('1',))
        cursor.execute("UPDATE user_profile SET value = ? WHERE key = 'last_task_completed_date'", (today_str,))
        
    return level_up

def update_meal_streak():
    conn = get_connection()
    cursor = conn.cursor()
    
    today_str = date.today().isoformat()
    yesterday_str = (date.today() - timedelta(days=1)).isoformat()
    
    # A day counts if all 3 meals (Breakfast, Lunch, Dinner) were completed.
    cursor.execute("SELECT value FROM user_profile WHERE key = 'last_meal_streak_date'")
    last_streak_date = cursor.fetchone()[0]
    
    # Check if today qualifies
    cursor.execute("""
    SELECT count(*) FROM meals 
    WHERE date = ? AND type IN ('Breakfast', 'Lunch', 'Dinner') AND completed = 1
    """, (today_str,))
    today_qualifies = cursor.fetchone()[0] == 3
    
    if not today_qualifies:
        # If today doesn't qualify yet, check if yesterday was the last qualified date.
        # If yes, the streak is still intact (since today isn't over). If not, streak goes to 0 (or stays at what it is if it's earlier in the day).
        # Actually, let's look back to see if yesterday qualified.
        cursor.execute("""
        SELECT count(*) FROM meals 
        WHERE date = ? AND type IN ('Breakfast', 'Lunch', 'Dinner') AND completed = 1
        """, (yesterday_str,))
        yesterday_qualifies = cursor.fetchone()[0] == 3
        
        if not yesterday_qualifies and last_streak_date != today_str:
            # Both today and yesterday don't qualify, streak reset
            cursor.execute("UPDATE user_profile SET value = '0' WHERE key = 'meal_streak'")
            conn.commit()
            conn.close()
            return False
        else:
            conn.close()
            return False
            
    # If today qualifies:
    if last_streak_date == today_str:
        # Already completed and counted today
        conn.close()
        return False
        
    cursor.execute("SELECT value FROM user_profile WHERE key = 'meal_streak'")
    current_streak = int(cursor.fetchone()[0])
    
    level_up = False
    if last_streak_date == yesterday_str:
        # Consecutive day!
        new_streak = current_streak + 1
        cursor.execute("UPDATE user_profile SET value = ? WHERE key = 'meal_streak'", (str(new_streak),))
        cursor.execute("UPDATE user_profile SET value = ? WHERE key = 'last_meal_streak_date'", (today_str,))
        
        if new_streak in [3, 7, 14, 30]:
            lvl_up, _, _ = add_xp(new_streak * 10)
            level_up = lvl_up
    else:
        new_streak = 1
        cursor.execute("UPDATE user_profile SET value = '1' WHERE key = 'meal_streak'")
        cursor.execute("UPDATE user_profile SET value = ? WHERE key = 'last_meal_streak_date'", (today_str,))
        
    conn.commit()
    conn.close()
    return level_up

# Achievements & Badges System
def award_badge(badge_name, description, icon):
    conn = get_connection()
    cursor = conn.cursor()
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        cursor.execute("""
        INSERT INTO badges (badge_name, badge_description, date_earned, icon)
        VALUES (?, ?, ?, ?)
        """, (badge_name, description, date_str, icon))
        conn.commit()
        # Give XP bonus for the badge!
        conn.close()
        add_xp(100) # 100 XP bonus for any badge earned
        return True
    except sqlite3.IntegrityError:
        # Badge already earned
        conn.close()
        return False

def get_badges():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM badges ORDER BY date_earned DESC")
    columns = [col[0] for col in cursor.description]
    badges = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    return badges

def check_and_award_badges():
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Productive Day: Complete at least 3 tasks today
    today_str = date.today().isoformat()
    cursor.execute("""
    SELECT count(*) FROM tasks 
    WHERE status = 'Completed' AND completed_at LIKE ?
    """, (f"{today_str}%",))
    completed_today = cursor.fetchone()[0]
    if completed_today >= 3:
        conn.close()
        award_badge("Productive Day", "Completed at least 3 tasks in a single day!", "🔥")
        conn = get_connection()
        cursor = conn.cursor()
        
    # 2. Healthy Day: Log and complete Breakfast, Lunch, and Dinner today
    cursor.execute("""
    SELECT count(*) FROM meals 
    WHERE date = ? AND type IN ('Breakfast', 'Lunch', 'Dinner') AND completed = 1
    """, (today_str,))
    meals_today = cursor.fetchone()[0]
    if meals_today == 3:
        conn.close()
        award_badge("Healthy Day", "Logged and completed Breakfast, Lunch, and Dinner today!", "🥗")
        conn = get_connection()
        cursor = conn.cursor()
        
    # 3. Perfect Balance: Complete at least 2 tasks and 3 meals today
    if completed_today >= 2 and meals_today == 3:
        conn.close()
        award_badge("Perfect Balance", "Completed at least 2 tasks and all 3 core meals in one day!", "⚖️")
        conn = get_connection()
        cursor = conn.cursor()
        
    # 4. Task Crusher: Complete a Critical priority task
    cursor.execute("SELECT count(*) FROM tasks WHERE status = 'Completed' AND priority = 'Critical'")
    criticals = cursor.fetchone()[0]
    if criticals >= 1:
        conn.close()
        award_badge("Task Crusher", "Completed a Critical priority task!", "⚡")
        conn = get_connection()
        cursor = conn.cursor()
        
    # 5. Consistency King: Maintain a 3-day task streak
    cursor.execute("SELECT value FROM user_profile WHERE key = 'task_streak'")
    task_streak = int(cursor.fetchone()[0])
    if task_streak >= 3:
        conn.close()
        award_badge("Consistency King", "Maintained a task completion streak of 3 days or more!", "👑")
        conn = get_connection()
        cursor = conn.cursor()
        
    # 6. Wellness Warrior: Maintain a 3-day meal streak
    cursor.execute("SELECT value FROM user_profile WHERE key = 'meal_streak'")
    meal_streak = int(cursor.fetchone()[0])
    if meal_streak >= 3:
        conn.close()
        award_badge("Wellness Warrior", "Maintained a meal consistency streak of 3 days or more!", "🛡️")
        conn = get_connection()
        cursor = conn.cursor()
        
    conn.close()

def check_task_exists(title, due_date):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM tasks WHERE title = ? AND due_date = ?", (title, due_date))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def check_meal_exists(meal_date, meal_type):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM meals WHERE date = ? AND type = ?", (meal_date, meal_type))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def update_task_metadata(task_id, description, priority, category, estimated_time, ai_score):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE tasks 
    SET description = ?, priority = ?, category = ?, estimated_time = ?, ai_score = ?
    WHERE id = ?
    """, (description, priority, category, estimated_time, ai_score, task_id))
    conn.commit()
    conn.close()

def clear_subtasks(task_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM subtasks WHERE task_id = ?", (task_id,))
    conn.commit()
    conn.close()

def update_meal_metadata(meal_id, description, completed, healthy_tag):
    conn = get_connection()
    cursor = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
    UPDATE meals
    SET description = ?, completed = ?, healthy_tag = ?, timestamp = ?
    WHERE id = ?
    """, (description, completed, healthy_tag, timestamp, meal_id))
    conn.commit()
    conn.close()

# For dev testing
if __name__ == "__main__":
    init_db()
    print("Database initialized successfully!")
    print("User Stats:", get_user_stats())
