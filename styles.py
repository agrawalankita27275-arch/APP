def get_custom_css():
    """
    Returns custom CSS code to override Streamlit styling.
    Utilizes translucent colors and blur filters to create a modern, glassmorphic appearance
    that automatically blends beautifully with both Streamlit Light and Dark modes.
    """
    return """
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');

    /* Global Typography & Background Adjustments */
    html, body, [class*="css"], [class*="st-"] {
        font-family: 'Outfit', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }

    h1, h2, h3 {
        font-family: 'Outfit', sans-serif !important;
        font-weight: 600 !important;
        letter-spacing: -0.5px !important;
    }

    /* Glassmorphic Card Container */
    .glass-card {
        background: rgba(255, 255, 255, 0.06);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px border rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.15);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    .glass-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 40px 0 rgba(0, 0, 0, 0.25);
    }
    
    .glass-card.critical {
        border-left: 6px solid #ff4b4b;
    }
    .glass-card.high {
        border-left: 6px solid #ffaa00;
    }
    .glass-card.medium {
        border-left: 6px solid #00aaff;
    }
    .glass-card.low {
        border-left: 6px solid #00cc66;
    }

    /* Gamification Widgets in Sidebar */
    .sidebar-profile {
        text-align: center;
        padding: 20px 10px;
        background: rgba(255, 255, 255, 0.04);
        border-radius: 20px;
        margin-bottom: 20px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }

    .avatar-badge {
        font-size: 48px;
        line-height: 80px;
        width: 80px;
        height: 80px;
        background: linear-gradient(135deg, #7f00ff, #e100ff);
        border-radius: 50%;
        display: inline-block;
        margin-bottom: 12px;
        box-shadow: 0 4px 15px rgba(225, 0, 255, 0.4);
    }

    .level-text {
        font-size: 20px;
        font-weight: 700;
        margin-top: 5px;
        color: #e100ff;
    }

    /* Custom Gradient Progress Bar */
    .custom-progress-container {
        width: 100%;
        background-color: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        height: 10px;
        margin: 10px 0;
        overflow: hidden;
    }

    .custom-progress-bar {
        height: 100%;
        background: linear-gradient(90deg, #7f00ff, #e100ff);
        border-radius: 10px;
        transition: width 0.4s ease-out;
    }

    /* Stats Pill Container */
    .stats-pill-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px;
        margin-top: 15px;
    }

    .stats-pill {
        background: rgba(255, 255, 255, 0.04);
        padding: 10px;
        border-radius: 12px;
        text-align: center;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }

    .stats-pill-num {
        font-size: 18px;
        font-weight: 700;
        color: #ffaa00;
    }
    
    .stats-pill-label {
        font-size: 11px;
        color: #888888;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 2px;
    }

    /* Notification Tray Card */
    .notification-tray {
        background: rgba(255, 75, 75, 0.08);
        border: 1px solid rgba(255, 75, 75, 0.2);
        border-radius: 14px;
        padding: 15px;
        margin-bottom: 20px;
    }

    .notification-tray.info {
        background: rgba(0, 170, 255, 0.08);
        border: 1px solid rgba(0, 170, 255, 0.2);
    }
    
    .notification-tray.warning {
        background: rgba(255, 170, 0, 0.08);
        border: 1px solid rgba(255, 170, 0, 0.2);
    }

    /* Visual Timeline Styles */
    .timeline-item {
        position: relative;
        padding-left: 30px;
        border-left: 2px solid rgba(255, 255, 255, 0.1);
        margin-left: 10px;
        padding-bottom: 20px;
    }

    .timeline-item::before {
        content: '';
        position: absolute;
        left: -6px;
        top: 4px;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: #e100ff;
        box-shadow: 0 0 8px #e100ff;
    }

    .timeline-item.meal::before {
        background: #00cc66;
        box-shadow: 0 0 8px #00cc66;
    }

    .timeline-item.buffer::before {
        background: rgba(255, 255, 255, 0.3);
        box-shadow: none;
    }

    .timeline-time {
        font-size: 12px;
        color: #888888;
        font-weight: 500;
    }

    .timeline-title {
        font-size: 15px;
        font-weight: 600;
        margin-top: 2px;
    }

    /* Badges Showcase Grid */
    .badges-container {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        justify-content: center;
        padding: 10px 0;
    }

    .badge-icon {
        font-size: 32px;
        width: 60px;
        height: 60px;
        line-height: 60px;
        background: rgba(255, 255, 255, 0.06);
        border-radius: 50%;
        text-align: center;
        display: inline-block;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.15);
        transition: all 0.3s ease;
        position: relative;
        cursor: pointer;
    }

    .badge-icon:hover {
        transform: scale(1.15) rotate(5deg);
        background: linear-gradient(135deg, #7f00ff, #e100ff);
        border-color: #e100ff;
        box-shadow: 0 8px 20px rgba(225, 0, 255, 0.4);
    }
    
    .badge-icon.locked {
        opacity: 0.25;
        filter: grayscale(100%);
        cursor: not-allowed;
    }
    
    .badge-icon.locked:hover {
        transform: none;
        background: rgba(255, 255, 255, 0.06);
        border-color: rgba(255, 255, 255, 0.1);
        box-shadow: none;
        filter: grayscale(100%);
    }

    /* Clean Streamlit Widgets overriding default padding issues */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: rgba(0, 0, 0, 0.1);
        padding: 6px;
        border-radius: 12px;
    }

    .stTabs [data-baseweb="tab"] {
        height: 40px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 8px;
        color: inherit;
        border: none;
        padding: 0 16px;
        font-weight: 500;
        transition: background-color 0.2s ease;
    }

    .stTabs [aria-selected="true"] {
        background-color: rgba(255, 255, 255, 0.1) !important;
        font-weight: 600 !important;
    }
    
    /* Hover microanimations for standard buttons */
    div.stButton > button:first-child {
        border-radius: 10px;
        background-color: transparent;
        border: 1px solid rgba(255, 255, 255, 0.2);
        transition: all 0.2s ease;
        font-weight: 500;
    }
    
    div.stButton > button:first-child:hover {
        background: linear-gradient(135deg, #7f00ff, #e100ff);
        border-color: #e100ff;
        color: white !important;
        box-shadow: 0 4px 15px rgba(225, 0, 255, 0.3);
        transform: translateY(-1px);
    }
    
    /* Primary buttons */
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #7f00ff, #e100ff);
        border-color: #e100ff;
        color: white;
        font-weight: 600;
    }
    
    div.stButton > button[kind="primary"]:hover {
        filter: brightness(1.1);
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba(225, 0, 255, 0.4);
    }
    """
