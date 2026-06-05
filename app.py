import streamlit as st
import database
import ai_engine
import styles
from datetime import datetime, date, time, timedelta

# Set page configuration
st.set_page_config(
    page_title="AI Task & Wellness Tracker",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
database.init_db()

# Apply custom CSS styles
st.markdown(f"<style>{styles.get_custom_css()}</style>", unsafe_allow_html=True)

# Helper function to format date/time
def format_datetime_str(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S")

# Load User Stats
stats = database.get_user_stats()
level = stats['level']
xp = stats['xp']
task_streak = stats['task_streak']
meal_streak = stats['meal_streak']

# Title and Greeting
today_date = date.today()
today_str = today_date.strftime("%A, %b %d, %Y")

# Sidebar - User Gamification profile
st.sidebar.markdown("## ⚡ Member Profile")

# XP Level Progress HTML card
xp_in_level = xp % 200
pct = int((xp_in_level / 200.0) * 100)

profile_html = f"""
<div class="sidebar-profile">
    <div class="avatar-badge">🎯</div>
    <h3 style="margin: 5px 0 0 0; font-size: 20px;">Habit Champion</h3>
    <div class="level-text">LEVEL {level}</div>
    <div style="font-size: 13px; color: #888; margin-top: 5px;">{xp_in_level} / 200 XP to Level {level+1}</div>
    <div class="custom-progress-container">
        <div class="custom-progress-bar" style="width: {pct}%;"></div>
    </div>
    <div style="font-size: 12px; color: #aaa; margin-top: 5px;">Total Score: <b>{xp} XP</b></div>
    <div class="stats-pill-grid">
        <div class="stats-pill">
            <div class="stats-pill-num">🔥 {task_streak}</div>
            <div class="stats-pill-label">Task Streak</div>
        </div>
        <div class="stats-pill">
            <div class="stats-pill-num">🥗 {meal_streak}</div>
            <div class="stats-pill-label">Meal Streak</div>
        </div>
    </div>
</div>
"""
st.sidebar.markdown(profile_html, unsafe_allow_html=True)

# Sidebar - Badges Preview
st.sidebar.markdown("### 🏆 Recent Achievements")
earned_badges = database.get_badges()
all_possible_badges = [
    {"name": "Productive Day", "icon": "🔥", "desc": "Completed 3 tasks today"},
    {"name": "Healthy Day", "icon": "🥗", "desc": "Completed Breakfast, Lunch, and Dinner"},
    {"name": "Perfect Balance", "icon": "⚖️", "desc": "2 tasks & 3 meals today"},
    {"name": "Task Crusher", "icon": "⚡", "desc": "Complete a Critical task"},
    {"name": "Consistency King", "icon": "👑", "desc": "3-day task streak"},
    {"name": "Wellness Warrior", "icon": "🛡️", "desc": "3-day meal streak"}
]

earned_names = [b['badge_name'] for b in earned_badges]

badge_preview_html = "<div class='badges-container'>"
for b in all_possible_badges[:4]: # Show first 4 in sidebar
    is_locked = b['name'] not in earned_names
    locked_class = "locked" if is_locked else ""
    tooltip = f"Title: {b['name']} ({b['desc']}) - " + ("LOCKED" if is_locked else "EARNED!")
    badge_preview_html += f"<span class='badge-icon {locked_class}' title='{tooltip}'>{b['icon']}</span>"
badge_preview_html += "</div>"
st.sidebar.markdown(badge_preview_html, unsafe_allow_html=True)

# Sidebar Information Panel
st.sidebar.markdown("---")
st.sidebar.markdown(
    "<div style='font-size: 12px; opacity: 0.6; text-align: center;'>"
    "AI Task & Wellness Tracker v1.0<br>"
    "A premium productivity tool"
    "</div>",
    unsafe_allow_html=True
)

# Main Application Layout
st.markdown(f"# 🚀 Streamlined Productivity Dashboard")
st.markdown(f"**Today's Date:** {today_str}")

# Setup core tabs
tab_dash, tab_tasks, tab_meals, tab_badges = st.tabs([
    "📊 Smart Dashboard", 
    "📝 Task Management", 
    "🥗 Wellness & Meals", 
    "🏆 Badges & Streaks"
])

# ----------------- TABS IMPLEMENTATION -----------------

# 1. SMART DASHBOARD
with tab_dash:
    col_left, col_right = st.columns([5, 4])
    
    tasks = database.get_tasks()
    pending_tasks = [t for t in tasks if t['status'] != 'Completed']
    completed_tasks = [t for t in tasks if t['status'] == 'Completed']
    
    meals_today = database.get_meals_for_day(today_date.isoformat())
    completed_meals = [m for m in meals_today if m['completed'] == 1]
    breakfast_done = any(m['type'] == 'Breakfast' and m['completed'] == 1 for m in meals_today)
    lunch_done = any(m['type'] == 'Lunch' and m['completed'] == 1 for m in meals_today)
    dinner_done = any(m['type'] == 'Dinner' and m['completed'] == 1 for m in meals_today)
    
    with col_left:
        st.markdown("### 🔥 Top 3 Tasks for Today")
        
        # Sort pending by AI score
        pending_sorted = sorted(pending_tasks, key=lambda x: x['ai_score'], reverse=True)
        top_tasks = pending_sorted[:3]
        
        if top_tasks:
            for task in top_tasks:
                card_col, action_col = st.columns([5, 1])
                with card_col:
                    p_class = task['priority'].lower()
                    due_dt = datetime.strptime(task['due_date'], "%Y-%m-%d %H:%M:%S")
                    due_time_str = due_dt.strftime("%I:%M %p")
                    due_date_str = due_dt.strftime("%b %d")
                    
                    task_html = f"""
                    <div class="glass-card {p_class}">
                        <div style="display: flex; justify-content: space-between; align-items: start;">
                            <span style="font-size: 11px; font-weight: 600; text-transform: uppercase; padding: 2px 8px; border-radius: 20px; background: rgba(255,255,255,0.1); color: #fff;">
                                {task['category']}
                            </span>
                            <span style="font-size: 12px; font-weight: 700; color: #e100ff;">
                                AI Score: {int(task['ai_score'])}
                            </span>
                        </div>
                        <h4 style="margin: 8px 0 4px 0; font-size: 16px;">{task['title']}</h4>
                        <p style="margin: 0; font-size: 13px; opacity: 0.7;">{task['description'] or 'No description provided.'}</p>
                        <div style="margin-top: 10px; display: flex; justify-content: space-between; font-size: 12px; opacity: 0.6;">
                            <span>📅 {due_date_str} at {due_time_str}</span>
                            <span>⏱️ {task['estimated_time'] or 1.0}h estimated</span>
                        </div>
                    </div>
                    """
                    st.markdown(task_html, unsafe_allow_html=True)
                with action_col:
                    st.write("") # vertical spacing
                    st.write("")
                    st.write("")
                    if st.button("Done", key=f"dash_comp_{task['id']}", use_container_width=True):
                        xp, lvl_up = database.update_task_status(task['id'], 'Completed')
                        st.toast(f"Task Completed! +{xp} XP earned!", icon="⭐")
                        if lvl_up:
                            st.toast("🎉 LEVEL UP! You reached a new milestone!", icon="🏆")
                        st.rerun()
        else:
            st.info("No pending tasks today! Add some tasks in the Task Management tab.")
            
        st.write("")
        st.markdown("### 📅 AI Suggested Schedule")
        
        # Generate schedule timeline
        timeline = ai_engine.generate_ai_daily_planner(tasks)
        if timeline:
            for item in timeline:
                item_class = "meal" if item['type'] == 'Meal' else "buffer" if item['type'] == 'Buffer' else "task"
                
                # Render timeline HTML
                timeline_html = f"""
                <div class="timeline-item {item_class}">
                    <div class="timeline-time">{item['start_time']} - {item['end_time']}</div>
                    <div class="timeline-title">{item['title']}</div>
                </div>
                """
                st.markdown(timeline_html, unsafe_allow_html=True)
        else:
            st.info("Log tasks to generate your automated AI schedule!")

    with col_right:
        st.markdown("### 🔔 Alerts & Notifications")
        
        # Notifications list
        notifications = []
        
        # Overdue Tasks Check
        now = datetime.now()
        overdue_count = 0
        critical_due_soon = False
        for t in pending_tasks:
            due_dt = datetime.strptime(t['due_date'], "%Y-%m-%d %H:%M:%S")
            if due_dt < now:
                overdue_count += 1
            elif t['priority'] == 'Critical' and (due_dt - now).total_seconds() < 21600: # 6 hours
                critical_due_soon = True
                
        if overdue_count > 0:
            notifications.append({
                "text": f"⚠️ **Attention Needed:** You have **{overdue_count} overdue task(s)**. Complete them to maintain your task completion streak!",
                "type": "error"
            })
        if critical_due_soon:
            notifications.append({
                "text": "⚡ **Critical Deadline:** A Critical priority task is due within the next 6 hours! Focus on this first.",
                "type": "error"
            })
            
        # Meal Alerts
        logged_meals_count = len([m for m in meals_today if m['completed'] == 1 and m['type'] in ['Breakfast', 'Lunch', 'Dinner']])
        if logged_meals_count < 3:
            missing = 3 - logged_meals_count
            notifications.append({
                "text": f"🍳 **Wellness Module:** You logged {logged_meals_count}/3 core meals today. You still need **{missing} more meal(s)** to meet your daily minimum & earn the +50 XP bonus!",
                "type": "warning"
            })
        elif logged_meals_count == 3:
            notifications.append({
                "text": "🎉 **Healthy Habits Achieved:** Excellent! You completed Breakfast, Lunch, and Dinner today! +50 XP Streak Bonus Awarded.",
                "type": "info"
            })
            
        # Morning greeting if earlier in day
        if now.hour < 12:
            notifications.append({
                "text": "🌅 **Morning Plan:** Review today's AI suggested timeline and focus on completing your 'Top 3 Tasks' first thing!",
                "type": "info"
            })
            
        if notifications:
            for note in notifications:
                c_class = "notification-tray"
                if note['type'] == 'info':
                    c_class += " info"
                elif note['type'] == 'warning':
                    c_class += " warning"
                
                st.markdown(f"<div class='{c_class}'>{note['text']}</div>", unsafe_allow_html=True)
        else:
            st.success("All caught up! No notifications or wellness alerts.")
            
        st.write("")
        st.markdown("### 📊 Productivity Summary")
        
        # Tasks chart/progress
        total_tasks = len(tasks)
        completed_tasks_count = len(completed_tasks)
        pending_tasks_count = len(pending_tasks)
        
        if total_tasks > 0:
            comp_rate = int((completed_tasks_count / total_tasks) * 100)
            
            summary_html = f"""
            <div class="glass-card" style="padding: 15px;">
                <h5 style="margin: 0; font-size: 15px;">Task Completion Rate</h5>
                <div style="font-size: 24px; font-weight: 700; color: #e100ff; margin: 5px 0;">{comp_rate}%</div>
                <div style="font-size: 13px; opacity: 0.7;">{completed_tasks_count} completed / {pending_tasks_count} pending</div>
                <div class="custom-progress-container" style="height: 8px;">
                    <div class="custom-progress-bar" style="width: {comp_rate}%;"></div>
                </div>
            </div>
            """
            st.markdown(summary_html, unsafe_allow_html=True)
        else:
            st.info("Create a task to view your completion stats.")
            
        # Meals completion preview
        b_icon = "🟢" if breakfast_done else "⚪"
        l_icon = "🟢" if lunch_done else "⚪"
        d_icon = "🟢" if dinner_done else "⚪"
        
        meal_summary_html = f"""
        <div class="glass-card" style="padding: 15px;">
            <h5 style="margin: 0; font-size: 15px;">Core Meals Logged</h5>
            <div style="font-size: 22px; font-weight: 700; color: #00cc66; margin: 5px 0;">{logged_meals_count} / 3</div>
            <div style="display: flex; gap: 20px; font-size: 14px; margin-top: 10px;">
                <span>{b_icon} Breakfast</span>
                <span>{l_icon} Lunch</span>
                <span>{d_icon} Dinner</span>
            </div>
        </div>
        """
        st.markdown(meal_summary_html, unsafe_allow_html=True)

# 2. TASK MANAGEMENT
with tab_tasks:
    st.markdown("### 🤖 Natural Language Quick Add")
    nl_input = st.text_input(
        "Describe your task in plain English (e.g. 'Submit budget review by Monday 4 PM Critical finance')",
        placeholder="AI will extract Title, Due Date, Priority, and Category...",
        key="nl_task_input"
    )
    
    if nl_input:
        parsed = ai_engine.parse_natural_language_task(nl_input)
        
        st.markdown("**AI Extraction Preview:**")
        col_p1, col_p2, col_p3, col_p4 = st.columns(4)
        with col_p1:
            parsed_title = st.text_input("Title", value=parsed['title'])
        with col_p2:
            parsed_due = st.date_input("Due Date", value=parsed['due_date'].date())
        with col_p3:
            parsed_time = st.time_input("Due Time", value=parsed['due_date'].time())
        with col_p4:
            parsed_priority = st.selectbox("Priority", ['Low', 'Medium', 'High', 'Critical'], index=['Low', 'Medium', 'High', 'Critical'].index(parsed['priority']))
            
        col_p5, col_p6 = st.columns(2)
        with col_p5:
            parsed_category = st.selectbox("Category", ['Work', 'Study', 'Personal', 'Health', 'Finance'], index=['Work', 'Study', 'Personal', 'Health', 'Finance'].index(parsed['category']))
        with col_p6:
            parsed_est = st.slider("Estimated Time (Hours)", 0.5, 8.0, 1.0, step=0.5)
            
        parsed_desc = st.text_area("Description (Optional)", value="")
        
        if st.button("Add Extracted Task", type="primary"):
            final_due_dt = datetime.combine(parsed_due, parsed_time)
            due_str = format_datetime_str(final_due_dt)
            
            # Recalculate AI score based on potential changes in preview form
            ai_score = ai_engine.calculate_ai_priority(due_str, parsed_priority, parsed_est, parsed_category)
            
            task_id = database.add_task(
                parsed_title, parsed_desc, due_str, parsed_priority, parsed_category, parsed_est, ai_score
            )
            
            st.success(f"Added task: '{parsed_title}' (AI Priority Score: {int(ai_score)})!")
            st.toast("New task created!", icon="📝")
            # Auto breakdown default subtasks
            subtasks = ai_engine.generate_ai_subtasks(parsed_title, parsed_category)
            for sub in subtasks:
                database.add_subtask(task_id, sub)
            st.rerun()
            
    st.write("")
    
    with st.expander("➕ Manually Add Task"):
        with st.form("manual_task_form"):
            t_title = st.text_input("Task Title")
            t_desc = st.text_area("Description")
            
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                t_due_date = st.date_input("Due Date", value=date.today())
            with col_d2:
                t_due_time = st.time_input("Due Time", value=time(17, 0))
                
            col_s1, col_s2, col_s3 = st.columns(3)
            with col_s1:
                t_priority = st.selectbox("Priority Level", ['Low', 'Medium', 'High', 'Critical'], index=1)
            with col_s2:
                t_category = st.selectbox("Task Category", ['Work', 'Study', 'Personal', 'Health', 'Finance'], index=2)
            with col_s3:
                t_est_time = st.number_input("Est. Time (Hours)", min_value=0.25, max_value=24.0, value=1.0, step=0.25)
                
            t_is_goal = st.checkbox("Mark as Goal Task (+15 AI score boost)")
            
            submit_manual = st.form_submit_button("Create Task", type="primary")
            if submit_manual:
                if not t_title:
                    st.error("Task title is required.")
                else:
                    final_dt = datetime.combine(t_due_date, t_due_time)
                    due_str = format_datetime_str(final_dt)
                    
                    ai_score = ai_engine.calculate_ai_priority(due_str, t_priority, t_est_time, t_category, t_is_goal)
                    
                    task_id = database.add_task(
                        t_title, t_desc, due_str, t_priority, t_category, t_est_time, ai_score
                    )
                    st.success(f"Added task: '{t_title}' (AI Score: {int(ai_score)})!")
                    
                    # Generate subtasks automatically
                    subtasks = ai_engine.generate_ai_subtasks(t_title, t_category)
                    for sub in subtasks:
                        database.add_subtask(task_id, sub)
                        
                    st.rerun()

    st.write("")
    st.markdown("### 📝 Tasks List")
    
    # Filtering interface
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        f_status = st.multiselect("Filter by Status", ['Pending', 'In Progress', 'Completed'], default=['Pending', 'In Progress'])
    with col_f2:
        f_priority = st.multiselect("Filter by Priority", ['Low', 'Medium', 'High', 'Critical'], default=['Low', 'Medium', 'High', 'Critical'])
    with col_f3:
        f_category = st.multiselect("Filter by Category", ['Work', 'Study', 'Personal', 'Health', 'Finance'], default=['Work', 'Study', 'Personal', 'Health', 'Finance'])
        
    filtered_tasks = database.get_tasks()
    
    # Apply filters
    if f_status:
        filtered_tasks = [t for t in filtered_tasks if t['status'] in f_status]
    if f_priority:
        filtered_tasks = [t for t in filtered_tasks if t['priority'] in f_priority]
    if f_category:
        filtered_tasks = [t for t in filtered_tasks if t['category'] in f_category]
        
    if filtered_tasks:
        for task in filtered_tasks:
            # Color-coded classes based on priority
            p_class = task['priority'].lower()
            status = task['status']
            
            # Format display dates
            due_dt = datetime.strptime(task['due_date'], "%Y-%m-%d %H:%M:%S")
            due_str = due_dt.strftime("%b %d, %Y at %I:%M %p")
            
            # Construct Card details
            task_card_html = f"""
            <div class="glass-card {p_class}">
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 5px;">
                    <span style="font-size: 11px; font-weight: 600; text-transform: uppercase; padding: 2px 8px; border-radius: 20px; background: rgba(255,255,255,0.1); color: #fff;">
                        {task['category']}
                    </span>
                    <div>
                        <span style="font-size: 11px; font-weight: 600; text-transform: uppercase; padding: 2px 8px; border-radius: 20px; background: rgba(255,255,255,0.1); margin-right: 5px;">
                            {status}
                        </span>
                        <span style="font-size: 12px; font-weight: 700; color: #e100ff;">
                            AI Score: {int(task['ai_score'])}
                        </span>
                    </div>
                </div>
                <h4 style="margin: 5px 0; font-size: 17px;">{task['title']}</h4>
                <p style="margin: 0; font-size: 13px; opacity: 0.8;">{task['description'] or 'No description provided.'}</p>
                <div style="margin-top: 10px; font-size: 12px; opacity: 0.6;">
                    <span>📅 Due: {due_str}</span> | <span>⏱️ Est. Time: {task['estimated_time'] or 1.0}h</span>
                    {f" | 🏆 XP Awarded: {task['xp_awarded']}" if status == 'Completed' else ''}
                </div>
            </div>
            """
            
            col_t_card, col_t_actions = st.columns([4, 1.2])
            with col_t_card:
                st.markdown(task_card_html, unsafe_allow_html=True)
                
                # Subtasks expander
                subtasks = database.get_subtasks(task['id'])
                if subtasks:
                    with st.expander(f"📝 Subtasks Breakdown ({len([s for s in subtasks if s['completed'] == 1])}/{len(subtasks)})"):
                        for sub in subtasks:
                            chk_val = sub['completed'] == 1
                            if st.checkbox(sub['title'], value=chk_val, key=f"sub_{sub['id']}"):
                                if not chk_val: # changed to True
                                    database.toggle_subtask(sub['id'])
                                    st.toast("+5 XP earned!", icon="⭐")
                                    st.rerun()
                            else:
                                if chk_val: # changed to False
                                    database.toggle_subtask(sub['id'])
                                    st.toast("-5 XP adjusted", icon="📉")
                                    st.rerun()
                else:
                    if st.button("💡 Auto-Generate AI Subtask Breakdown", key=f"gen_sub_{task['id']}"):
                        generated = ai_engine.generate_ai_subtasks(task['title'], task['category'])
                        for gs in generated:
                            database.add_subtask(task['id'], gs)
                        st.rerun()
                        
            with col_t_actions:
                st.write("") # spacers
                
                # Render state change controls
                if status != 'Completed':
                    if st.button("✅ Complete", key=f"done_btn_{task['id']}", use_container_width=True, type="primary"):
                        xp_gained, lvl_up = database.update_task_status(task['id'], 'Completed')
                        st.toast(f"Completed! +{xp_gained} XP", icon="🎉")
                        if lvl_up:
                            st.toast("🎉 LEVEL UP!", icon="🏆")
                        st.rerun()
                        
                    if status == 'Pending':
                        if st.button("⚡ Start Task", key=f"prog_btn_{task['id']}", use_container_width=True):
                            database.update_task_status(task['id'], 'In Progress')
                            st.rerun()
                    elif status == 'In Progress':
                        if st.button("⏳ Pause Task", key=f"pend_btn_{task['id']}", use_container_width=True):
                            database.update_task_status(task['id'], 'Pending')
                            st.rerun()
                else:
                    if st.button("🔄 Reopen Task", key=f"reopen_btn_{task['id']}", use_container_width=True):
                        xp_adj, _ = database.update_task_status(task['id'], 'Pending')
                        st.toast(f"Reopened. XP adjusted: {xp_adj}", icon="🔄")
                        st.rerun()
                        
                # Delete task button
                if st.button("🗑️ Delete", key=f"del_btn_{task['id']}", use_container_width=True):
                    database.delete_task(task['id'])
                    st.toast("Task deleted.", icon="🗑️")
                    st.rerun()
            st.markdown("---")
    else:
        st.info("No tasks matching filters. Add a task to get started!")

# 3. WELLNESS & MEALS
with tab_meals:
    st.markdown("### 🥗 Wellness & Daily Meal Tracker")
    st.markdown("Healthy eating is core to mental productivity. Log at least **3 meals today** to keep your streak!")
    
    selected_meal_date = st.date_input("Select Tracker Date", date.today(), key="meal_tracker_date")
    selected_date_str = selected_meal_date.isoformat()
    
    meals_selected_day = database.get_meals_for_day(selected_date_str)
    
    # Re-organize logged meals for easier lookup
    logged_dict = {m['type']: m for m in meals_selected_day}
    
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    
    meal_types = [
        {"type": "Breakfast", "icon": "🍳", "col": col_m1},
        {"type": "Lunch", "icon": "🥗", "col": col_m2},
        {"type": "Dinner", "icon": "🍽️", "col": col_m3},
        {"type": "Snack", "icon": "🍎", "col": col_m4}
    ]
    
    for m_info in meal_types:
        m_type = m_info['type']
        m_icon = m_info['icon']
        m_col = m_info['col']
        
        meal_data = logged_dict.get(m_type, {"completed": 0, "description": "", "healthy_tag": "Neutral"})
        
        with m_col:
            st.markdown(f"#### {m_icon} {m_type}")
            is_comp = meal_data['completed'] == 1
            
            with st.form(f"meal_form_{m_type}_{selected_date_str}"):
                comp_chk = st.checkbox("Completed / Logged", value=is_comp)
                m_desc = st.text_input("Meal details", value=meal_data['description'], placeholder="What did you eat?")
                m_healthy = st.selectbox("Healthy Rating", ["Healthy", "Neutral", "Unhealthy"], index=["Healthy", "Neutral", "Unhealthy"].index(meal_data['healthy_tag']))
                
                log_btn = st.form_submit_button(f"Log {m_type}")
                if log_btn:
                    xp_gained, lvl_up = database.log_meal(
                        selected_date_str, m_type, m_desc, 1 if comp_chk else 0, m_healthy
                    )
                    st.toast(f"{m_type} updated! XP Gained: +{xp_gained}", icon="🥗")
                    if lvl_up:
                        st.toast("🎉 LEVEL UP!", icon="🏆")
                    st.rerun()
                    
    st.write("")
    st.markdown("### 📊 Daily Progress")
    
    logged_count = len([m for m in meals_selected_day if m['completed'] == 1 and m['type'] in ['Breakfast', 'Lunch', 'Dinner']])
    
    # Progress display
    if logged_count == 3:
        st.success("🟢 Complete! You met your daily minimum goal of 3 meals! Streak is active. +50 XP bonus applied.")
    elif logged_count < 3:
        missing = 3 - logged_count
        st.warning(f"🟡 Under Daily Minimum: You logged {logged_count}/3 core meals. *You still need {missing} more meal(s) today to meet your daily minimum.*")
        
    st.write("")
    st.markdown("### 🤖 AI Wellness Advice & Suggested Timings")
    
    # Fetch suggested daily planner schedule to base meal advice on
    schedule = ai_engine.generate_ai_daily_planner(database.get_tasks())
    suggestions = ai_engine.get_meal_timing_suggestions(schedule)
    
    for sug in suggestions:
        st.markdown(sug)

# 4. ACHIEVEMENTS
with tab_badges:
    st.markdown("### 🏆 Gamification Center")
    st.markdown("Complete tasks, stay consistent, and eat healthy to earn XP, level up, and unlock rare badges!")
    
    col_a1, col_a2 = st.columns([1, 1])
    
    with col_a1:
        st.markdown("#### Unlocked Achievements")
        
        if earned_badges:
            for badge in earned_badges:
                st.markdown(
                    f"""
                    <div class="glass-card" style="display: flex; gap: 15px; align-items: center; padding: 12px 20px;">
                        <span style="font-size: 36px;">{badge['icon']}</span>
                        <div>
                            <h5 style="margin: 0; font-size: 16px;">{badge['badge_name']}</h5>
                            <p style="margin: 0; font-size: 13px; opacity: 0.7;">{badge['badge_description']}</p>
                            <span style="font-size: 11px; opacity: 0.5;">Earned: {badge['date_earned'][:10]}</span>
                        </div>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
        else:
            st.info("You haven't earned any achievements yet. Keep completing tasks to unlock your first badge!")
            
    with col_a2:
        st.markdown("#### All Possible Badges")
        
        for badge in all_possible_badges:
            is_earned = badge['name'] in earned_names
            status_text = "✅ UNLOCKED (+100 XP)" if is_earned else "🔒 LOCKED"
            g_style = "opacity: 1;" if is_earned else "opacity: 0.4;"
            
            st.markdown(
                f"""
                <div class="glass-card" style="{g_style} display: flex; gap: 15px; align-items: center; padding: 12px 20px;">
                    <span style="font-size: 36px;">{badge['icon']}</span>
                    <div>
                        <h5 style="margin: 0; font-size: 16px;">{badge['name']}</h5>
                        <p style="margin: 0; font-size: 13px; opacity: 0.8;">{badge['desc']}</p>
                        <span style="font-size: 11px; font-weight: 700; color: {'#00cc66' if is_earned else '#ffaa00'};">{status_text}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
