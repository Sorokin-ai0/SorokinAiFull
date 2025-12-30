# =============================================================================
# KNOWLEDGE TREE - STREAMLIT INTEGRATION
# Handles rendering, database operations, and user interactions
# =============================================================================

import streamlit as st
import streamlit.components.v1 as components
import json
import os
from datetime import datetime, date
from tree_data import (
    KNOWLEDGE_TREE,
    SUBJECTS,
    LEVELS,
    build_d3_graph_data,
    get_lesson_by_id,
    get_course_by_id,
    calculate_user_level,
    get_next_level_xp
)

# =============================================================================
# DATABASE OPERATIONS
# =============================================================================

def get_user_progress(conn, user_id):
    """
    Fetch all lesson progress for a user from the database.
    Returns a dict mapping lesson_id -> status
    """
    progress = {}

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT lesson_id, status
            FROM LessonProgress
            WHERE user_id = %s
        """, (user_id,))

        for row in cursor.fetchall():
            progress[row['lesson_id']] = row['status']

        cursor.close()
    except Exception as e:
        st.error(f"Error loading progress: {e}")

    return progress


def get_user_stats(conn, user_id):
    """
    Get user's gamification stats (XP, level, streak).
    Returns a dict with user stats.
    """
    stats = {
        "total_xp": 0,
        "current_level": 1,
        "streak_days": 0,
        "total_lessons_completed": 0
    }

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT total_xp, current_level, streak_days, total_lessons_completed
            FROM Users
            WHERE user_id = %s
        """, (user_id,))

        row = cursor.fetchone()
        if row:
            stats["total_xp"] = row.get("total_xp", 0) or 0
            stats["current_level"] = row.get("current_level", 1) or 1
            stats["streak_days"] = row.get("streak_days", 0) or 0
            stats["total_lessons_completed"] = row.get("total_lessons_completed", 0) or 0

        cursor.close()
    except Exception as e:
        # Columns might not exist yet - return defaults
        pass

    return stats


def initialize_user_lessons(conn, user_id):
    """
    Initialize lesson progress for a new user.
    Sets first 3 lessons of each course to 'available', rest to 'locked'.
    """
    try:
        cursor = conn.cursor()

        for course_id, course in KNOWLEDGE_TREE["courses"].items():
            for lesson in course["lessons"]:
                # Determine initial status
                if lesson["visible_by_default"]:
                    status = "available"
                else:
                    status = "locked"

                # Insert with ON DUPLICATE KEY to avoid duplicates
                cursor.execute("""
                    INSERT INTO LessonProgress (user_id, lesson_id, course_id, status)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE lesson_id = lesson_id
                """, (user_id, lesson["id"], course_id, status))

        conn.commit()
        cursor.close()
    except Exception as e:
        st.error(f"Error initializing lessons: {e}")


def update_lesson_status(conn, user_id, lesson_id, new_status, xp_earned=0):
    """
    Update a lesson's status and optionally add XP.
    Also handles unlocking the next lesson.
    """
    try:
        cursor = conn.cursor()
        now = datetime.now()

        # Update the lesson status
        if new_status == "in_progress":
            cursor.execute("""
                UPDATE LessonProgress
                SET status = %s, started_at = COALESCE(started_at, %s), last_accessed_at = %s
                WHERE user_id = %s AND lesson_id = %s
            """, (new_status, now, now, user_id, lesson_id))

        elif new_status == "completed":
            cursor.execute("""
                UPDATE LessonProgress
                SET status = %s, completed_at = %s, xp_earned = %s, last_accessed_at = %s
                WHERE user_id = %s AND lesson_id = %s
            """, (new_status, now, xp_earned, now, user_id, lesson_id))

            # Update user's total XP
            cursor.execute("""
                UPDATE Users
                SET total_xp = COALESCE(total_xp, 0) + %s,
                    total_lessons_completed = COALESCE(total_lessons_completed, 0) + 1
                WHERE user_id = %s
            """, (xp_earned, user_id))

            # Unlock next lesson
            unlock_next_lesson(conn, user_id, lesson_id)

            # Log XP transaction
            cursor.execute("""
                INSERT INTO XPTransactions (user_id, xp_amount, source_type, source_id, description)
                VALUES (%s, %s, 'lesson_complete', %s, %s)
            """, (user_id, xp_earned, lesson_id, f"Completed lesson: {lesson_id}"))

        elif new_status == "mastered":
            cursor.execute("""
                UPDATE LessonProgress
                SET status = %s, mastered_at = %s, review_count = review_count + 1, last_accessed_at = %s
                WHERE user_id = %s AND lesson_id = %s
            """, (new_status, now, now, user_id, lesson_id))

        conn.commit()
        cursor.close()

        # Update user level if needed
        update_user_level(conn, user_id)

    except Exception as e:
        st.error(f"Error updating lesson: {e}")


def unlock_next_lesson(conn, user_id, completed_lesson_id):
    """
    After completing a lesson, unlock the next lesson in the course.
    """
    try:
        # Get the lesson info
        lesson = get_lesson_by_id(completed_lesson_id)
        if not lesson:
            return

        course = get_course_by_id(lesson["course_id"])
        if not course:
            return

        # Find the next lesson
        current_order = lesson["order"]
        next_lesson = None

        for l in course["lessons"]:
            if l["order"] == current_order + 1:
                next_lesson = l
                break

        if next_lesson:
            cursor = conn.cursor()

            # Check if it exists and is locked
            cursor.execute("""
                SELECT status FROM LessonProgress
                WHERE user_id = %s AND lesson_id = %s
            """, (user_id, next_lesson["id"]))

            row = cursor.fetchone()

            if row and row[0] == "locked":
                # Unlock it
                cursor.execute("""
                    UPDATE LessonProgress
                    SET status = 'available'
                    WHERE user_id = %s AND lesson_id = %s
                """, (user_id, next_lesson["id"]))
                conn.commit()

            elif not row:
                # Insert as available
                cursor.execute("""
                    INSERT INTO LessonProgress (user_id, lesson_id, course_id, status)
                    VALUES (%s, %s, %s, 'available')
                """, (user_id, next_lesson["id"], lesson["course_id"]))
                conn.commit()

            cursor.close()

    except Exception as e:
        st.error(f"Error unlocking next lesson: {e}")


def update_user_level(conn, user_id):
    """
    Recalculate and update user's level based on total XP.
    """
    try:
        cursor = conn.cursor(dictionary=True)

        # Get current XP
        cursor.execute("SELECT total_xp FROM Users WHERE user_id = %s", (user_id,))
        row = cursor.fetchone()

        if row:
            total_xp = row.get("total_xp", 0) or 0
            new_level = calculate_user_level(total_xp)

            cursor.execute("""
                UPDATE Users SET current_level = %s WHERE user_id = %s
            """, (new_level, user_id))
            conn.commit()

        cursor.close()
    except Exception:
        pass  # Columns might not exist


def update_streak(conn, user_id):
    """
    Update user's daily streak.
    """
    try:
        cursor = conn.cursor(dictionary=True)
        today = date.today()

        # Get current streak info
        cursor.execute("""
            SELECT last_streak_date, streak_days FROM Users WHERE user_id = %s
        """, (user_id,))
        row = cursor.fetchone()

        if row:
            last_date = row.get("last_streak_date")
            current_streak = row.get("streak_days", 0) or 0

            if last_date is None:
                # First time
                new_streak = 1
            elif last_date == today:
                # Already logged today
                new_streak = current_streak
            elif last_date == today - timedelta(days=1):
                # Consecutive day
                new_streak = current_streak + 1
            else:
                # Streak broken
                new_streak = 1

            cursor.execute("""
                UPDATE Users SET streak_days = %s, last_streak_date = %s WHERE user_id = %s
            """, (new_streak, today, user_id))
            conn.commit()

        cursor.close()
    except Exception:
        pass


def log_daily_activity(conn, user_id, lessons_completed=0, xp_earned=0, time_spent=0):
    """
    Log daily activity for analytics.
    """
    try:
        cursor = conn.cursor()
        today = date.today()

        cursor.execute("""
            INSERT INTO DailyActivity (user_id, activity_date, lessons_completed, total_xp_earned, time_spent_minutes)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                lessons_completed = lessons_completed + %s,
                total_xp_earned = total_xp_earned + %s,
                time_spent_minutes = time_spent_minutes + %s,
                session_count = session_count + 1,
                last_activity_at = CURRENT_TIMESTAMP
        """, (user_id, today, lessons_completed, xp_earned, time_spent,
              lessons_completed, xp_earned, time_spent))

        conn.commit()
        cursor.close()
    except Exception:
        pass


# =============================================================================
# TREE RENDERING
# =============================================================================

def render_knowledge_tree(user_id, user_grade, conn=None):
    """
    Render the full-screen Knowledge Tree visualization.
    This function should be called when tree_view_open is True.
    """

    # Load user progress from database
    user_progress = {}
    user_stats = {"total_xp": 0, "current_level": 1, "streak_days": 0}

    if conn:
        user_progress = get_user_progress(conn, user_id)
        user_stats = get_user_stats(conn, user_id)

    # If no progress exists, initialize with defaults
    if not user_progress:
        # Set first 3 lessons of each course as available
        for course_id, course in KNOWLEDGE_TREE["courses"].items():
            for lesson in course["lessons"]:
                if lesson["visible_by_default"]:
                    user_progress[lesson["id"]] = "available"
                else:
                    user_progress[lesson["id"]] = "locked"

        # Initialize in database if connection available
        if conn:
            initialize_user_lessons(conn, user_id)

    # Build D3 graph data
    graph_data = build_d3_graph_data(user_progress)

    # Add user info to the data
    graph_data["userInfo"] = {
        "grade": user_grade,
        "level": user_stats.get("current_level", 1),
        "currentXP": user_stats.get("total_xp", 0),
        "nextLevelXP": get_next_level_xp(user_stats.get("total_xp", 0)),
        "streak": user_stats.get("streak_days", 0)
    }

    # Read the HTML template
    html_path = os.path.join(os.path.dirname(__file__), "tree_component.html")

    try:
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
    except FileNotFoundError:
        st.error("tree_component.html not found!")
        return

    # Inject the data into the HTML
    data_script = f"""
    <script>
        window.TREE_DATA = {json.dumps(graph_data)};
    </script>
    """

    # Insert data script before closing </head> tag
    html_with_data = html_content.replace("</head>", data_script + "</head>")

    # Add CSS to hide Streamlit's UI elements when tree is open
    hide_streamlit_css = """
    <style>
        /* Hide all Streamlit elements when tree is fullscreen */
        .stApp > header,
        .stApp > footer,
        section[data-testid="stSidebar"],
        div[data-testid="stToolbar"],
        div[data-testid="stDecoration"],
        div[data-testid="stStatusWidget"],
        .stDeployButton {
            display: none !important;
        }
    </style>
    """

    html_with_data = html_with_data.replace("</head>", hide_streamlit_css + "</head>")

    # Add callback handling script
    callback_script = """
    <script>
        // Handle messages from the tree
        window.addEventListener('message', function(event) {
            if (event.data && event.data.type === 'streamlit:setComponentValue') {
                // Store for Streamlit to read
                window.parent.postMessage({
                    type: 'streamlit:componentReady',
                    value: event.data.value
                }, '*');
            }
        });

        // Also check periodically for TREE_CALLBACK
        setInterval(function() {
            if (window.TREE_CALLBACK) {
                const callback = window.TREE_CALLBACK;
                window.TREE_CALLBACK = null;

                // Post to parent
                window.parent.postMessage({
                    type: 'streamlit:setComponentValue',
                    value: callback
                }, '*');
            }
        }, 100);
    </script>
    """

    html_with_data = html_with_data.replace("</body>", callback_script + "</body>")

    # Render the component full screen
    # Use a large height to fill the viewport
    components.html(
        html_with_data,
        height=800,
        scrolling=False
    )

    # Check for callbacks via JavaScript
    # We'll use a hidden component to receive messages
    callback_receiver = """
    <script>
        window.addEventListener('message', function(event) {
            if (event.data && event.data.action) {
                // Store in sessionStorage for Streamlit to read
                sessionStorage.setItem('tree_callback', JSON.stringify(event.data));
            }
        });
    </script>
    """
    components.html(callback_receiver, height=0)


def handle_tree_callback(callback_data, conn, user_id):
    """
    Process callbacks from the Knowledge Tree.
    Returns True if tree should close, False otherwise.
    """
    if not callback_data:
        return False

    action = callback_data.get("action")

    if action == "close":
        return True

    elif action == "select_lesson":
        lesson = callback_data.get("lesson", {})

        if lesson:
            # Store selected lesson in session state
            st.session_state.selected_lesson = lesson

            # Update lesson status to in_progress
            if conn:
                update_lesson_status(conn, user_id, lesson["id"], "in_progress")

            # Set prompt to process
            course_name = lesson.get("course_name", "")
            lesson_title = lesson.get("title", "")
            lesson_desc = lesson.get("description", "")

            st.session_state.prompt_to_process = f"Teach me {course_name}: {lesson_title}. {lesson_desc}"

            return True

    return False


def complete_current_lesson(conn, user_id):
    """
    Mark the current lesson as completed and award XP.
    Call this when user finishes a lesson.
    """
    if "selected_lesson" not in st.session_state:
        return

    lesson = st.session_state.selected_lesson
    lesson_id = lesson.get("id")
    xp_value = lesson.get("xp_value", 75)

    if conn and lesson_id:
        update_lesson_status(conn, user_id, lesson_id, "completed", xp_value)
        update_streak(conn, user_id)
        log_daily_activity(conn, user_id, lessons_completed=1, xp_earned=xp_value)

        # Clear selected lesson
        st.session_state.selected_lesson = None

        # Show success message
        st.success(f"Lesson completed! +{xp_value} XP")


# =============================================================================
# STREAMLIT SESSION STATE HELPERS
# =============================================================================

def init_tree_session_state():
    """
    Initialize session state variables for the Knowledge Tree.
    """
    if 'tree_view_open' not in st.session_state:
        st.session_state.tree_view_open = False

    if 'tree_closed' not in st.session_state:
        st.session_state.tree_closed = False

    if 'selected_lesson' not in st.session_state:
        st.session_state.selected_lesson = None

    if 'tree_callback' not in st.session_state:
        st.session_state.tree_callback = None


def open_knowledge_tree():
    """
    Open the Knowledge Tree full-screen view.
    """
    st.session_state.tree_view_open = True
    st.session_state.tree_closed = False


def close_knowledge_tree():
    """
    Close the Knowledge Tree and return to main view.
    """
    st.session_state.tree_view_open = False
    st.session_state.tree_closed = True


# =============================================================================
# ALTERNATIVE RENDER (For environments where components.html has issues)
# =============================================================================

def render_tree_button():
    """
    Render a button to open the Knowledge Tree.
    Use this in the main UI.
    """
    if st.button("🌳 Knowledge Tree", key="open_tree_btn", use_container_width=True):
        open_knowledge_tree()
        st.rerun()


def render_simple_tree_view(user_id, user_grade, conn=None):
    """
    A simplified tree view using native Streamlit components.
    Use this as a fallback if the D3.js version has issues.
    """
    st.markdown("## 🌳 Knowledge Tree")

    # Get user progress
    user_progress = {}
    if conn:
        user_progress = get_user_progress(conn, user_id)

    # Close button
    col1, col2 = st.columns([8, 1])
    with col2:
        if st.button("✕ Close", key="close_tree"):
            close_knowledge_tree()
            st.rerun()

    # Display subjects
    for subject_id, subject in SUBJECTS.items():
        with st.expander(f"{subject['name']}", expanded=True):
            # Get courses for this subject
            courses = [c for c in KNOWLEDGE_TREE["courses"].values() if c["subject"] == subject_id]

            for course in courses:
                st.markdown(f"### {course['name']}")
                st.caption(f"Grade: {course['grade_level']}")

                # Display lessons
                cols = st.columns(4)
                for i, lesson in enumerate(course["lessons"]):
                    status = user_progress.get(lesson["id"], "locked")
                    visible = lesson["visible_by_default"] or status != "locked"

                    with cols[i % 4]:
                        if visible:
                            status_icon = {
                                "available": "🔵",
                                "in_progress": "🟡",
                                "completed": "✅",
                                "mastered": "⭐"
                            }.get(status, "⚫")

                            if st.button(
                                f"{status_icon} {lesson['title'][:15]}...",
                                key=f"lesson_{lesson['id']}",
                                disabled=(status == "locked")
                            ):
                                st.session_state.selected_lesson = {
                                    "id": lesson["id"],
                                    "title": lesson["title"],
                                    "description": lesson["description"],
                                    "course_id": course["id"],
                                    "course_name": course["name"],
                                    "xp_value": lesson["xp_value"]
                                }
                                st.session_state.prompt_to_process = f"Teach me {course['name']}: {lesson['title']}. {lesson['description']}"
                                close_knowledge_tree()
                                st.rerun()
                        else:
                            st.button(
                                "🔒 ???",
                                key=f"locked_{lesson['id']}",
                                disabled=True
                            )
