# =============================================================================
# KNOWLEDGE TREE - APP.PY INTEGRATION GUIDE
# =============================================================================
#
# This file contains the exact code modifications needed to integrate the
# Knowledge Tree into your existing app.py. Follow the instructions below.
#
# =============================================================================

"""
================================================================================
STEP 1: ADD NEW IMPORTS (at the top of app.py, after existing imports)
================================================================================
"""

# Add these imports after your existing imports (around line 14):
NEW_IMPORTS = """
# Knowledge Tree imports
from knowledge_tree import (
    init_tree_session_state,
    render_knowledge_tree,
    handle_tree_callback,
    complete_current_lesson,
    open_knowledge_tree,
    close_knowledge_tree,
    render_tree_button,
    get_user_progress,
    get_user_stats,
    update_lesson_status
)
from tree_data import KNOWLEDGE_TREE, get_lesson_by_id
"""

"""
================================================================================
STEP 2: INITIALIZE TREE SESSION STATE (after line 472)
================================================================================
Add this after your existing session state initializations.
"""

INIT_SESSION_STATE = """
# Knowledge Tree session state
if 'tree_view_open' not in st.session_state:
    st.session_state.tree_view_open = False
if 'tree_closed' not in st.session_state:
    st.session_state.tree_closed = False
if 'selected_lesson' not in st.session_state:
    st.session_state.selected_lesson = None
"""

"""
================================================================================
STEP 3: ADD FULL-SCREEN TREE HANDLER (after authentication check, before main UI)
================================================================================
This goes right after the authentication block ends (after line 541: st.stop())
and BEFORE the main UI code starts.
"""

FULL_SCREEN_TREE_HANDLER = '''
# =============================================================================
# KNOWLEDGE TREE - FULL SCREEN MODE
# =============================================================================
# Check if Knowledge Tree should be displayed full-screen
if st.session_state.get('tree_view_open', False):
    # Get database connection
    conn = get_db_connection()

    if conn:
        # Render the full-screen tree
        render_knowledge_tree(
            user_id=st.session_state.user_id,
            user_grade=st.session_state.grade,
            conn=conn
        )

        # Add a hidden close button that uses native Streamlit
        # This is a fallback in case the JS close button doesn't work
        st.markdown("""
            <style>
                /* Make the tree take up full screen */
                section.main > div {
                    padding: 0 !important;
                    max-width: 100% !important;
                }
                /* Hide other elements */
                header, footer, .stDeployButton {
                    display: none !important;
                }
            </style>
        """, unsafe_allow_html=True)

        # Create columns for fallback controls
        col1, col2, col3 = st.columns([1, 6, 1])
        with col3:
            if st.button("❌ Exit Tree", key="exit_tree_fallback"):
                st.session_state.tree_view_open = False
                st.rerun()

        # Check if user closed the tree or selected a lesson
        # Note: The JavaScript will set these via the callback system

        # Handle close action
        if st.session_state.get('tree_closed', False):
            st.session_state.tree_view_open = False
            st.session_state.tree_closed = False
            conn.close()
            st.rerun()

        # Handle lesson selection
        if st.session_state.get('selected_lesson'):
            lesson = st.session_state.selected_lesson
            st.session_state.tree_view_open = False

            # Update lesson to in_progress
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE LessonProgress
                    SET status = 'in_progress', started_at = COALESCE(started_at, NOW())
                    WHERE user_id = %s AND lesson_id = %s
                """, (st.session_state.user_id, lesson['id']))
                conn.commit()
                cursor.close()
            except Exception as e:
                pass  # Table might not exist yet

            conn.close()
            st.rerun()

        conn.close()

        # CRITICAL: Stop here - don't render anything else when tree is open
        st.stop()
'''

"""
================================================================================
STEP 4: REPLACE THE LEARNING PATHS EXPANDER
================================================================================
In the "LAYOUT A: NEW CHAT" section (around line 613), REPLACE the learning
paths expander with the Knowledge Tree button.

FIND THIS CODE (around lines 613-622):
--------------------------------------------------------------------------------
        with col_p:
            with st.expander("📚 Learning Paths", expanded=False):
                sub_cats = ["Math", "Science", "Computer Science"]
                for cat in sub_cats:
                    with st.expander(f"📖 {cat}"):
                        cursor.execute("SELECT * FROM LearningPaths WHERE subject=%s", (cat,))
                        paths = cursor.fetchall()
                        for p in paths:
                            if st.button(p['course_title'], key=f"top_p_{p['id']}", use_container_width=True):
                                st.session_state.current_path = p['id']
                                st.rerun()
--------------------------------------------------------------------------------

REPLACE WITH:
--------------------------------------------------------------------------------
"""

NEW_LEARNING_PATHS_SECTION = '''
        with col_p:
            # Knowledge Tree Button - Opens full screen visualization
            st.markdown("### 🌳 Learning")
            if st.button("🌳 Open Knowledge Tree", key="open_tree_main", use_container_width=True, type="primary"):
                st.session_state.tree_view_open = True
                st.rerun()

            # Quick access to continue current lesson
            if st.session_state.get('selected_lesson'):
                lesson = st.session_state.selected_lesson
                st.info(f"📖 Continue: {lesson.get('title', 'Unknown')}")
                if st.button("▶ Resume Lesson", key="resume_lesson", use_container_width=True):
                    st.session_state.prompt_to_process = f"Continue teaching me: {lesson.get('title', '')}. {lesson.get('description', '')}"
                    st.rerun()
'''

"""
================================================================================
STEP 5: ADD LESSON COMPLETION HANDLER
================================================================================
After a lesson is taught successfully (when the AI responds), you should offer
to mark it complete. Add this in the AI response section (after line 856).

FIND THIS CODE (around lines 846-856):
--------------------------------------------------------------------------------
                    st.session_state.messages.append({"role": "assistant", "content": resp.text})

                    if is_u: st.session_state.pro_usage += 1
                    else: st.session_state.flash_usage += 1
--------------------------------------------------------------------------------

ADD AFTER IT (but before the cursor.execute that updates usage):
--------------------------------------------------------------------------------
"""

LESSON_COMPLETION_HANDLER = '''
                    # Check if this was a lesson from Knowledge Tree
                    if st.session_state.get('selected_lesson'):
                        lesson = st.session_state.selected_lesson

                        # Show completion option
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("✅ Mark Lesson Complete", key="complete_lesson_btn"):
                                try:
                                    xp_earned = lesson.get('xp_value', 75)
                                    cursor.execute("""
                                        UPDATE LessonProgress
                                        SET status = 'completed', completed_at = NOW(), xp_earned = %s
                                        WHERE user_id = %s AND lesson_id = %s
                                    """, (xp_earned, st.session_state.user_id, lesson['id']))

                                    # Update user XP
                                    cursor.execute("""
                                        UPDATE Users
                                        SET total_xp = COALESCE(total_xp, 0) + %s,
                                            total_lessons_completed = COALESCE(total_lessons_completed, 0) + 1
                                        WHERE user_id = %s
                                    """, (xp_earned, st.session_state.user_id))

                                    conn.commit()

                                    st.success(f"🎉 Lesson Complete! +{xp_earned} XP")
                                    st.session_state.selected_lesson = None
                                    st.rerun()
                                except Exception as e:
                                    st.warning("Could not update progress. XP tables may not exist yet.")

                        with col2:
                            if st.button("📚 Back to Tree", key="back_to_tree_btn"):
                                st.session_state.selected_lesson = None
                                st.session_state.tree_view_open = True
                                st.rerun()
'''

"""
================================================================================
STEP 6: ADD TREE BUTTON TO BOTTOM BAR (in active chat layout)
================================================================================
In the "LAYOUT B: ACTIVE CHAT" section, add a button to access the tree.

FIND THIS CODE (around line 776):
--------------------------------------------------------------------------------
            c_h, c_s, c_m, c_st, c_a = st.columns([1, 1, 1, 1, 0.4])
--------------------------------------------------------------------------------

REPLACE THE COLUMNS WITH:
--------------------------------------------------------------------------------
"""

NEW_BOTTOM_BAR = '''
            c_h, c_tree, c_s, c_m, c_st, c_a = st.columns([0.8, 0.8, 1, 1, 1, 0.4])

            # Add tree button
            with c_tree:
                if st.button("🌳", key="tree_btn_bottom", use_container_width=True, help="Open Knowledge Tree"):
                    st.session_state.tree_view_open = True
                    st.rerun()
'''

"""
================================================================================
STEP 7: CSS ADDITIONS FOR FULL-SCREEN TREE
================================================================================
Add this CSS to your existing st.markdown CSS block (after line 165):
"""

ADDITIONAL_CSS = '''
    /* Knowledge Tree Full Screen Mode */
    .tree-fullscreen {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        width: 100vw !important;
        height: 100vh !important;
        z-index: 999999 !important;
        background: #1a2a3a !important;
    }

    /* Hide Streamlit UI when tree is open */
    .tree-mode header,
    .tree-mode footer,
    .tree-mode [data-testid="stSidebar"],
    .tree-mode [data-testid="stToolbar"] {
        display: none !important;
    }

    /* Tree button styling */
    button[kind="secondary"]:has(span:contains("🌳")) {
        background: linear-gradient(135deg, #27ae60, #2ecc71) !important;
        border: none !important;
    }
'''

"""
================================================================================
COMPLETE MODIFIED APP.PY EXAMPLE
================================================================================
Below is a complete working example showing how all the pieces fit together.
You can use this as a reference.
"""

COMPLETE_EXAMPLE = '''
# =============================================================================
# COMPLETE INTEGRATION EXAMPLE
# =============================================================================
# This shows the key sections of app.py with Knowledge Tree integrated.
# Copy the relevant sections to your actual app.py

import streamlit as st
# ... other imports ...
from knowledge_tree import (
    init_tree_session_state,
    render_knowledge_tree,
    open_knowledge_tree,
    close_knowledge_tree,
)
from tree_data import KNOWLEDGE_TREE

# ... page config, CSS, database connection ...

# Session State (add tree states)
if 'tree_view_open' not in st.session_state:
    st.session_state.tree_view_open = False
if 'selected_lesson' not in st.session_state:
    st.session_state.selected_lesson = None

# ... authentication code ...

# =============================================================================
# FULL SCREEN TREE MODE - Must come BEFORE normal UI
# =============================================================================
if st.session_state.get('tree_view_open', False):
    conn = get_db_connection()
    if conn:
        render_knowledge_tree(
            user_id=st.session_state.user_id,
            user_grade=st.session_state.grade,
            conn=conn
        )

        # Fallback close button
        if st.button("❌ Exit", key="exit_tree"):
            st.session_state.tree_view_open = False
            st.rerun()

        # Check for lesson selection
        if st.session_state.get('selected_lesson'):
            st.session_state.tree_view_open = False
            lesson = st.session_state.selected_lesson
            st.session_state.prompt_to_process = f"Teach: {lesson['title']}"
            st.rerun()

        conn.close()
        st.stop()  # Don't render anything else!

# =============================================================================
# NORMAL UI (only renders when tree is NOT open)
# =============================================================================
conn = get_db_connection()
# ... rest of your normal app code ...

# In the "New Chat" layout:
if st.button("🌳 Knowledge Tree", type="primary"):
    st.session_state.tree_view_open = True
    st.rerun()

# ... rest of app ...
'''

"""
================================================================================
DATABASE MIGRATION
================================================================================
Before using the Knowledge Tree, you need to run the database updates.

1. Open your TiDB Cloud console
2. Connect to your database
3. Run the SQL statements from database_updates.sql

Note: If you encounter errors about columns already existing, you can ignore them.
The IF NOT EXISTS clauses should handle most cases.
"""

"""
================================================================================
TESTING CHECKLIST
================================================================================

1. [ ] Database tables created successfully
2. [ ] Knowledge Tree button appears on home screen
3. [ ] Clicking button opens full-screen tree
4. [ ] Tree displays all subjects, courses, and lessons
5. [ ] Locked lessons appear as shadows
6. [ ] First 3 lessons of each course are available
7. [ ] Clicking available lesson sends you back to chat
8. [ ] Lesson prompt appears in chat
9. [ ] "Mark Complete" button appears after AI response
10. [ ] Completing lesson awards XP
11. [ ] Next lesson unlocks after completion
12. [ ] X button closes tree successfully
13. [ ] Mobile view works (zoom/pan)
14. [ ] User XP and level display correctly
"""

"""
================================================================================
TROUBLESHOOTING
================================================================================

Issue: Tree doesn't appear when clicking button
Solution: Check that tree_view_open session state is being set

Issue: Lessons don't unlock
Solution: Run database migrations, check LessonProgress table exists

Issue: JavaScript errors in tree
Solution: Check browser console, ensure D3.js loads from CDN

Issue: XP not updating
Solution: Check Users table has total_xp column (run ALTER TABLE)

Issue: Tree appears but looks broken
Solution: Check tree_component.html is in same directory as app.py
"""

# =============================================================================
# QUICK START FUNCTION
# =============================================================================

def print_integration_guide():
    """Print a quick integration guide to the console."""
    print("""
    ╔═══════════════════════════════════════════════════════════════════╗
    ║               KNOWLEDGE TREE INTEGRATION GUIDE                     ║
    ╠═══════════════════════════════════════════════════════════════════╣
    ║                                                                    ║
    ║  1. Run database_updates.sql on your TiDB Cloud database          ║
    ║                                                                    ║
    ║  2. Add imports to app.py (see NEW_IMPORTS above)                 ║
    ║                                                                    ║
    ║  3. Add session state init (see INIT_SESSION_STATE above)         ║
    ║                                                                    ║
    ║  4. Add full-screen handler BEFORE main UI                        ║
    ║     (see FULL_SCREEN_TREE_HANDLER above)                          ║
    ║                                                                    ║
    ║  5. Replace Learning Paths expander with tree button              ║
    ║     (see NEW_LEARNING_PATHS_SECTION above)                        ║
    ║                                                                    ║
    ║  6. Test! Click the tree button and explore.                      ║
    ║                                                                    ║
    ╚═══════════════════════════════════════════════════════════════════╝
    """)

if __name__ == "__main__":
    print_integration_guide()
