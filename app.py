import streamlit as st
import mysql.connector
import json
import uuid
import time
import requests
from PIL import Image
import google.generativeai as genai
import streamlit.components.v1 as components
from datetime import datetime
import bcrypt
import os

# =============================================================================
# 0. MODEL CONFIGURATION
# =============================================================================
MODEL_CONFIG = {
    "FLASH": "gemini-2.0-flash",
    "ULTRA": "gemini-1.5-pro"
}

# =============================================================================
# 1. PAGE CONFIGURATION
# =============================================================================
st.set_page_config(
    page_title="Sorokin Portal",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =============================================================================
# 2. THEME CONFIGURATION
# =============================================================================
THEMES = {
    "Auto": {"bg": "#1a2a3a", "accent": "#f1c40f", "text": "#ffffff"},  # Defaults to Dark Ocean
    "Dark Ocean": {"bg": "#1a2a3a", "accent": "#f1c40f", "text": "#ffffff"},
    "Midnight Purple": {"bg": "#1a1a2e", "accent": "#e94560", "text": "#ffffff"},
    "Forest Green": {"bg": "#1a2e1a", "accent": "#4ecca3", "text": "#ffffff"},
    "Light Mode": {"bg": "#f5f5f5", "accent": "#3498db", "text": "#1a1a1a"},
    "Sunset": {"bg": "#2d1f3d", "accent": "#ff6b6b", "text": "#ffffff"},
}

def get_theme():
    return THEMES.get(st.session_state.get('theme', 'Auto'), THEMES['Auto'])

# =============================================================================
# 3. VISITOR TRACKING
# =============================================================================
if 'visit_counted' not in st.session_state:
    try:
        requests.get("https://script.google.com/macros/s/AKfycbyY3GUNUMJGxIufUNkmnncdvMklbQdr6s_VDZvsJZj-BnTcEW-7-7pNlAN8EchosAdCNw/exec", timeout=1)
        st.session_state.visit_counted = True
    except: pass

# =============================================================================
# 4. DYNAMIC CSS
# =============================================================================
def apply_css():
    t = get_theme()
    st.markdown(f"""<style>
    .stApp {{ background-color: {t['bg']} !important; }}
    h1,h2,h3,h4,h5,h6,p,label,span,div,li {{ color: {t['text']} !important; }}
    div[data-baseweb="popover"] {{ background-color: #fff !important; border-radius: 12px !important; }}
    div[data-baseweb="popover"] * {{ color: black !important; }}
    div[data-baseweb="select"] > div {{ background-color: #fff !important; border-radius: 8px !important; }}
    div[data-baseweb="select"] * {{ color: #1a2a3a !important; }}
    .stTextInput input {{ background-color: #fff !important; color: #1a2a3a !important; border-radius: 12px !important; }}
    button[kind="secondaryFormSubmit"] {{ background-color: {t['accent']} !important; border-radius: 12px !important; }}
    header, footer {{ visibility: hidden !important; }}
    .xp-bar {{ background: linear-gradient(90deg, {t['accent']}, #e74c3c); height: 20px; border-radius: 10px; }}
    .badge {{ display: inline-block; padding: 5px 10px; margin: 3px; border-radius: 15px; font-size: 12px; border: 1px solid {t['accent']}; }}
    .level-display {{ background: linear-gradient(135deg, {t['accent']}, #e74c3c); padding: 10px 20px; border-radius: 12px; text-align: center; }}
    .pomodoro-timer {{ font-size: 48px; font-weight: bold; text-align: center; padding: 20px; border-radius: 12px; border: 2px solid {t['accent']}; }}
    .beta-banner {{ background: linear-gradient(90deg, #9b59b6, #3498db); color: white; padding: 8px 15px; border-radius: 8px; text-align: center; font-weight: bold; }}
</style>""", unsafe_allow_html=True)
apply_css()

# =============================================================================
# 5. DATABASE CONNECTION
# =============================================================================
def get_db():
    try:
        ssl = {"ssl_verify_cert": True}
        if os.path.exists("/etc/ssl/certs/ca-certificates.crt"):
            ssl["ssl_ca"] = "/etc/ssl/certs/ca-certificates.crt"
        return mysql.connector.connect(
            host=st.secrets["DB_HOST"], port=4000,
            user=st.secrets["DB_USER"], password=st.secrets["DB_PASSWORD"],
            database=st.secrets["DB_NAME"], connection_timeout=10, **ssl
        )
    except Exception as e:
        st.error(f"DB Error: {e}")
        st.stop()

def init_db():
    conn = get_db()
    if conn:
        cur = conn.cursor()
        cur.execute(f"USE {st.secrets['DB_NAME']};")
        
        cur.execute("""CREATE TABLE IF NOT EXISTS Users (
            id INT AUTO_INCREMENT PRIMARY KEY, username VARCHAR(255) UNIQUE NOT NULL,
            hashed_password VARCHAR(255) NOT NULL, grade VARCHAR(50), subject VARCHAR(50) DEFAULT 'Gen',
            flash_usage INT DEFAULT 0, pro_usage INT DEFAULT 0, user_id VARCHAR(255) UNIQUE NOT NULL,
            session_id VARCHAR(255), last_active_date VARCHAR(20), ai_level VARCHAR(50) DEFAULT 'Grade-Level',
            theme VARCHAR(50) DEFAULT 'Dark Ocean', total_xp INT DEFAULT 0, level INT DEFAULT 1
        );""")
        
        cur.execute("""CREATE TABLE IF NOT EXISTS ChatLogs (
            id INT AUTO_INCREMENT PRIMARY KEY, session_id VARCHAR(255) NOT NULL,
            user_id VARCHAR(255) NOT NULL, title VARCHAR(255), messages JSON,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );""")
        
        cur.execute("""CREATE TABLE IF NOT EXISTS UserBadges (
            id INT AUTO_INCREMENT PRIMARY KEY, user_id VARCHAR(255) NOT NULL,
            badge_id VARCHAR(50) NOT NULL, earned_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, badge_id)
        );""")
        
        cur.execute("""CREATE TABLE IF NOT EXISTS UserLessonProgress (
            id INT AUTO_INCREMENT PRIMARY KEY, user_id VARCHAR(255) NOT NULL,
            lesson_key VARCHAR(100) NOT NULL, status VARCHAR(20) DEFAULT 'available',
            completed_date TIMESTAMP NULL, quiz_score INT DEFAULT 0,
            UNIQUE(user_id, lesson_key)
        );""")

        cur.execute("""CREATE TABLE IF NOT EXISTS SeasonalEvents (
            id INT AUTO_INCREMENT PRIMARY KEY,
            event_name VARCHAR(100),
            start_date DATE,
            end_date DATE,
            badge_id VARCHAR(50),
            is_active BOOLEAN DEFAULT FALSE
        );""")

        # Add columns if missing
        columns_to_add = [
            ("theme", "VARCHAR(50) DEFAULT 'Auto'"),
            ("total_xp", "INT DEFAULT 0"),
            ("level", "INT DEFAULT 1"),
            ("streak_count", "INT DEFAULT 0"),
            ("last_study_date", "DATE"),
            ("daily_goal", "INT DEFAULT 3"),
            ("daily_lessons_completed", "INT DEFAULT 0"),
            ("last_spin_date", "DATE"),
            ("streak_freezes", "INT DEFAULT 0"),
            ("pet_stage", "VARCHAR(20) DEFAULT 'egg'"),
            ("pet_mood", "VARCHAR(20) DEFAULT 'neutral'"),
            ("sounds_enabled", "BOOLEAN DEFAULT TRUE"),
            ("pomodoros_completed", "INT DEFAULT 0")
        ]
        for col_name, col_def in columns_to_add:
            try: cur.execute(f"ALTER TABLE Users ADD COLUMN {col_name} {col_def};")
            except: pass
        
        conn.commit()
        cur.close()
        conn.close()
init_db()

# =============================================================================
# 6. XP & LEVELING SYSTEM
# =============================================================================
LEVEL_THRESHOLDS = [0, 100, 250, 500, 1000, 1750, 2750, 4000, 5500, 7500, 10000]
LEVEL_NAMES = ["Novice", "Learner", "Student", "Scholar", "Adept", "Expert", "Master", "Sage", "Luminary", "Genius", "Transcendent"]

def get_level_info(xp):
    level = 1
    for i, th in enumerate(LEVEL_THRESHOLDS):
        if xp >= th: level = i + 1
    curr_th = LEVEL_THRESHOLDS[min(level-1, len(LEVEL_THRESHOLDS)-1)]
    next_th = LEVEL_THRESHOLDS[min(level, len(LEVEL_THRESHOLDS)-1)]
    progress = int(((xp - curr_th) / max(1, next_th - curr_th)) * 100) if level < len(LEVEL_THRESHOLDS) else 100
    return {"level": level, "name": LEVEL_NAMES[min(level-1, len(LEVEL_NAMES)-1)], "xp": xp, "progress": progress, "needed": max(0, next_th - xp)}

def award_xp(user_id, amount):
    conn = get_db()
    if conn:
        cur = conn.cursor()
        cur.execute(f"USE {st.secrets['DB_NAME']};")
        old_level = st.session_state.get('level', 1)
        cur.execute("UPDATE Users SET total_xp = total_xp + %s WHERE user_id = %s", (amount, user_id))
        cur.execute("SELECT total_xp FROM Users WHERE user_id = %s", (user_id,))
        new_xp = cur.fetchone()[0]
        lvl = get_level_info(new_xp)['level']
        cur.execute("UPDATE Users SET level = %s WHERE user_id = %s", (lvl, user_id))
        conn.commit()
        cur.close()
        conn.close()
        st.session_state.total_xp = new_xp
        st.session_state.level = lvl

        # Play appropriate sound and update pet on level up
        if lvl > old_level:
            play_sound("levelup")
            update_pet_status(user_id, lvl)
        else:
            play_sound("xp")
        return new_xp
    return 0

# =============================================================================
# 7. BADGES SYSTEM
# =============================================================================
BADGES = {
    "first_lesson": {"name": "First Steps", "icon": "🎯", "desc": "Complete first lesson", "xp": 50},
    "five_lessons": {"name": "Getting Started", "icon": "📚", "desc": "Complete 5 lessons", "xp": 100},
    "ten_lessons": {"name": "Dedicated", "icon": "🌟", "desc": "Complete 10 lessons", "xp": 200},
    "first_quiz": {"name": "Quiz Taker", "icon": "📝", "desc": "Complete first quiz", "xp": 50},
    "perfect_quiz": {"name": "Perfectionist", "icon": "💯", "desc": "Get 100% on quiz", "xp": 150},
    "night_owl": {"name": "Night Owl", "icon": "🦉", "desc": "Study after 10 PM", "xp": 50},
    "early_bird": {"name": "Early Bird", "icon": "🐦", "desc": "Study before 7 AM", "xp": 50},
    "pomodoro_5": {"name": "Focus Master", "icon": "🍅", "desc": "Complete 5 pomodoros", "xp": 100},
    "math_explorer": {"name": "Math Explorer", "icon": "🧮", "desc": "Complete math lesson", "xp": 50},
    "science_explorer": {"name": "Science Explorer", "icon": "🧬", "desc": "Complete science lesson", "xp": 50},
    "code_explorer": {"name": "Code Explorer", "icon": "💻", "desc": "Complete coding lesson", "xp": 50},
}

def award_badge(user_id, badge_id):
    if badge_id not in BADGES: return False
    conn = get_db()
    if conn:
        cur = conn.cursor()
        cur.execute(f"USE {st.secrets['DB_NAME']};")
        cur.execute("SELECT id FROM UserBadges WHERE user_id=%s AND badge_id=%s", (user_id, badge_id))
        if cur.fetchone():
            cur.close(); conn.close(); return False
        cur.execute("INSERT INTO UserBadges (user_id, badge_id) VALUES (%s, %s)", (user_id, badge_id))
        conn.commit()
        cur.close()
        conn.close()
        play_sound("badge")
        award_xp(user_id, BADGES[badge_id]['xp'])
        if 'badges' not in st.session_state: st.session_state.badges = []
        st.session_state.badges.append(badge_id)
        return True
    return False

def get_badges(user_id):
    conn = get_db()
    badges = []
    if conn:
        cur = conn.cursor()
        cur.execute(f"USE {st.secrets['DB_NAME']};")
        cur.execute("SELECT badge_id FROM UserBadges WHERE user_id = %s", (user_id,))
        badges = [r[0] for r in cur.fetchall()]
        cur.close()
        conn.close()
    return badges
# =============================================================================
# 8. COURSE DATA
# =============================================================================
COURSE_SYLLABI = {
    "Algebra I": [
        {"title": "1. Variables & Expressions", "desc": "Understanding symbols, evaluating expressions."},
        {"title": "2. Linear Equations", "desc": "Solving for X, multi-step equations."},
        {"title": "3. Inequalities", "desc": "Graphing inequalities, compound inequalities."},
        {"title": "4. Functions", "desc": "Domain, range, function notation."},
        {"title": "5. Slope & Intercepts", "desc": "y=mx+b, graphing lines."},
        {"title": "6. Systems of Equations", "desc": "Substitution, elimination."},
        {"title": "7. Exponents", "desc": "Laws of exponents, scientific notation."},
        {"title": "8. Polynomials", "desc": "Adding, subtracting, multiplying."},
        {"title": "9. Factoring", "desc": "GCF, difference of squares."},
        {"title": "10. Quadratics", "desc": "Quadratic formula, parabolas."},
        {"title": "11. Statistics", "desc": "Mean, median, mode."},
        {"title": "12. Final Review", "desc": "Comprehensive review."}
    ],
    "Geometry": [
        {"title": "1. Points & Lines", "desc": "Foundations of geometry."},
        {"title": "2. Proofs", "desc": "Two-column proofs."},
        {"title": "3. Parallel Lines", "desc": "Transversals, angle pairs."},
        {"title": "4. Triangles", "desc": "SSS, SAS, ASA postulates."},
        {"title": "5. Triangle Properties", "desc": "Bisectors, medians."},
        {"title": "6. Polygons", "desc": "Interior angles, parallelograms."},
        {"title": "7. Similarity", "desc": "Ratios, similar triangles."},
        {"title": "8. Right Triangles", "desc": "Pythagorean theorem."},
        {"title": "9. Circles", "desc": "Tangents, arcs, chords."},
        {"title": "10. Area", "desc": "Area of polygons."},
        {"title": "11. Volume", "desc": "Prisms, cylinders, spheres."},
        {"title": "12. Transformations", "desc": "Reflections, rotations."},
        {"title": "13. Circle Equations", "desc": "Equation of a circle."},
        {"title": "14. Final Review", "desc": "Comprehensive review."}
    ],
    "Algebra II": [
        {"title": "1. Linear Review", "desc": "Absolute value, piecewise."},
        {"title": "2. Quadratics", "desc": "Completing the square."},
        {"title": "3. Complex Numbers", "desc": "Imaginary numbers."},
        {"title": "4. Polynomials", "desc": "Synthetic division."},
        {"title": "5. Radicals", "desc": "Rational exponents."},
        {"title": "6. Exponentials", "desc": "Growth and decay."},
        {"title": "7. Logarithms", "desc": "Log properties."},
        {"title": "8. Rational Functions", "desc": "Asymptotes."},
        {"title": "9. Sequences", "desc": "Arithmetic, geometric."},
        {"title": "10. Conics", "desc": "Ellipses, hyperbolas."},
        {"title": "11. Probability", "desc": "Combinations, permutations."},
        {"title": "12. Trig Ratios", "desc": "SOH CAH TOA."},
        {"title": "13. Trig Graphs", "desc": "Sine, cosine waves."},
        {"title": "14. Identities", "desc": "Trig identities."},
        {"title": "15. Final Review", "desc": "Comprehensive review."}
    ],
    "Pre-Calculus": [
        {"title": "1. Functions", "desc": "Parent functions."},
        {"title": "2. Polynomials", "desc": "Zeros, end behavior."},
        {"title": "3. Exponentials", "desc": "Logistic models."},
        {"title": "4. Trig Functions", "desc": "Unit circle."},
        {"title": "5. Trig Equations", "desc": "Solving trig equations."},
        {"title": "6. Law of Sines/Cosines", "desc": "Triangle applications."},
        {"title": "7. Matrices", "desc": "Operations, inverses."},
        {"title": "8. Conics", "desc": "Rotated conics."},
        {"title": "9. Sequences", "desc": "Series, induction."},
        {"title": "10. Limits", "desc": "Intro to limits."},
        {"title": "11. Derivatives Intro", "desc": "Rates of change."},
        {"title": "12. Vectors", "desc": "Dot product."},
        {"title": "13. Polar Coords", "desc": "Polar graphing."},
        {"title": "14. Parametrics", "desc": "Parametric equations."},
        {"title": "15. 3D Space", "desc": "3D coordinates."},
        {"title": "16. Final Review", "desc": "Calculus prep."}
    ],
    "Calculus I": [
        {"title": "1. Limits", "desc": "Limit laws, continuity."},
        {"title": "2. Continuity", "desc": "IVT, discontinuities."},
        {"title": "3. Derivatives", "desc": "Definition as limit."},
        {"title": "4. Diff Rules", "desc": "Power, product, quotient."},
        {"title": "5. Chain Rule", "desc": "Composite functions."},
        {"title": "6. Implicit Diff", "desc": "Implicit differentiation."},
        {"title": "7. Applications", "desc": "Linear approximation."},
        {"title": "8. Optimization", "desc": "Max/min problems."},
        {"title": "9. Related Rates", "desc": "Rate problems."},
        {"title": "10. Antiderivatives", "desc": "Indefinite integrals."},
        {"title": "11. Riemann Sums", "desc": "Area estimation."},
        {"title": "12. Definite Integrals", "desc": "Area accumulation."},
        {"title": "13. FTC", "desc": "Fundamental theorem."},
        {"title": "14. Substitution", "desc": "u-substitution."},
        {"title": "15. Area", "desc": "Area between curves."},
        {"title": "16. Volume", "desc": "Disk/washer methods."},
        {"title": "17. Diff Equations", "desc": "Separation of variables."},
        {"title": "18. Final Review", "desc": "Comprehensive review."}
    ],
    "Biology": [
        {"title": "1. Scientific Method", "desc": "Characteristics of life."},
        {"title": "2. Chemistry of Life", "desc": "Macromolecules."},
        {"title": "3. Cells", "desc": "Prokaryotes, eukaryotes."},
        {"title": "4. Photosynthesis", "desc": "Light reactions, Calvin cycle."},
        {"title": "5. Respiration", "desc": "Glycolysis, Krebs, ETC."},
        {"title": "6. Mitosis", "desc": "Cell cycle."},
        {"title": "7. Meiosis", "desc": "Genetic variation."},
        {"title": "8. Genetics", "desc": "Punnett squares."},
        {"title": "9. DNA", "desc": "Replication, transcription."},
        {"title": "10. Evolution", "desc": "Natural selection."},
        {"title": "11. Ecology", "desc": "Ecosystems, food webs."},
        {"title": "12. Classification", "desc": "Taxonomy."},
        {"title": "13. Human Systems", "desc": "Organ systems."},
        {"title": "14. Final Review", "desc": "Comprehensive review."}
    ],
    "Chemistry": [
        {"title": "1. Matter", "desc": "States, changes."},
        {"title": "2. Atoms", "desc": "Subatomic particles."},
        {"title": "3. Periodic Table", "desc": "Trends."},
        {"title": "4. Bonding", "desc": "Ionic, covalent."},
        {"title": "5. Nomenclature", "desc": "Naming compounds."},
        {"title": "6. The Mole", "desc": "Avogadro's number."},
        {"title": "7. Reactions", "desc": "Balancing equations."},
        {"title": "8. Stoichiometry", "desc": "Limiting reactants."},
        {"title": "9. States of Matter", "desc": "IMF, phase diagrams."},
        {"title": "10. Gases", "desc": "Ideal gas law."},
        {"title": "11. Solutions", "desc": "Molarity, solubility."},
        {"title": "12. Thermochemistry", "desc": "Enthalpy, entropy."},
        {"title": "13. Kinetics", "desc": "Rate laws."},
        {"title": "14. Acids/Bases", "desc": "pH, titrations."},
        {"title": "15. Redox", "desc": "Oxidation-reduction."},
        {"title": "16. Nuclear", "desc": "Radioactive decay."}
    ],
    "Physics": [
        {"title": "1. Kinematics 1D", "desc": "Velocity, acceleration."},
        {"title": "2. Vectors", "desc": "Components, addition."},
        {"title": "3. Kinematics 2D", "desc": "Projectile motion."},
        {"title": "4. Newton's Laws", "desc": "F=ma."},
        {"title": "5. Friction", "desc": "Static, kinetic."},
        {"title": "6. Work & Energy", "desc": "KE, PE, conservation."},
        {"title": "7. Momentum", "desc": "Impulse, collisions."},
        {"title": "8. Circular Motion", "desc": "Centripetal force."},
        {"title": "9. Rotation", "desc": "Torque."},
        {"title": "10. Equilibrium", "desc": "Statics."},
        {"title": "11. Fluids", "desc": "Buoyancy, Bernoulli."},
        {"title": "12. Thermodynamics", "desc": "Heat, laws."},
        {"title": "13. Waves", "desc": "Frequency, wavelength."},
        {"title": "14. Sound", "desc": "Resonance."},
        {"title": "15. Light", "desc": "Optics."}
    ],
    "Intro to Python": [
        {"title": "1. Variables", "desc": "Strings, integers, floats."},
        {"title": "2. Data Types", "desc": "Type casting."},
        {"title": "3. Conditionals", "desc": "If/else, booleans."},
        {"title": "4. Loops", "desc": "For, while loops."},
        {"title": "5. Functions", "desc": "Def, return."},
        {"title": "6. Lists", "desc": "Indexing, slicing."},
        {"title": "7. Dictionaries", "desc": "Key-value pairs."},
        {"title": "8. File I/O", "desc": "Reading, writing files."},
        {"title": "9. Libraries", "desc": "Importing modules."},
        {"title": "10. Final Project", "desc": "Build something!"}
    ]
}

COURSE_ID_MAP = {
    "algebra1": "Algebra I", "geometry": "Geometry", "algebra2": "Algebra II",
    "precalc": "Pre-Calculus", "calc1": "Calculus I", "biology": "Biology",
    "chemistry": "Chemistry", "physics": "Physics", "python": "Intro to Python"
}

COURSE_CATEGORIES = {
    "🧮 Math": ["Algebra I", "Geometry", "Algebra II", "Pre-Calculus", "Calculus I"],
    "🧬 Science": ["Biology", "Chemistry", "Physics"],
    "💻 CS": ["Intro to Python"]
}
# =============================================================================
# 9. CONSTELLATION VISUAL
# =============================================================================
def render_constellation(grade, progress):
    t = get_theme()
    completed = len([k for k,v in progress.items() if v == 'completed'])
    pct = int((completed / 130) * 100)

    # Build progress data for each course
    course_progress = {}
    course_map = {
        "Algebra I": "algebra1", "Geometry": "geometry", "Algebra II": "algebra2",
        "Pre-Calc": "precalc", "Calc I": "calc1", "Biology": "biology",
        "Chemistry": "chemistry", "Physics": "physics", "Python": "python"
    }
    for display_name, course_id in course_map.items():
        total_lessons = len(COURSE_SYLLABI.get(COURSE_ID_MAP.get(course_id, ""), []))
        completed_count = sum(1 for i in range(1, total_lessons+1) if progress.get(f"{course_id}_L{i}") == 'completed')
        course_progress[display_name] = {
            "completed": completed_count,
            "total": total_lessons,
            "is_complete": completed_count == total_lessons and total_lessons > 0
        }

    progress_json = json.dumps(course_progress)

    html = f'''
    <!DOCTYPE html><html><head>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        *{{margin:0;padding:0;box-sizing:border-box;}}
        body{{background:{t['bg']};overflow:hidden;font-family:sans-serif;}}
        #c{{width:100vw;height:100vh;}}
        .legend{{position:fixed;top:10px;left:10px;background:rgba(0,0,0,0.8);border-radius:8px;padding:10px;color:white;font-size:11px;}}
        .stats{{position:fixed;bottom:10px;left:10px;background:rgba(0,0,0,0.8);border-radius:8px;padding:10px;color:white;}}
        .stats h4{{color:{t['accent']};}}
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; r: 22; }}
            50% {{ opacity: 0.7; r: 24; }}
        }}
        .completed-node {{
            filter: drop-shadow(0 0 8px currentColor);
            animation: pulse 2s ease-in-out infinite;
        }}
    </style></head><body>
    <div id="c"></div>
    <div class="legend">
        <div>🟡 You</div><div>🔵 Math</div><div>🟢 Science</div><div>🟣 CS</div>
        <div style="margin-top:5px">⭐ Complete</div><div>🔒 Incomplete</div>
    </div>
    <div class="stats"><h4>🎓 {grade}</h4><div>{pct}% • {completed}/130</div></div>
    <button id="resetBtn" style="position:fixed;top:10px;right:10px;background:{t['accent']};color:#1a2a3a;border:none;padding:8px 16px;border-radius:8px;cursor:pointer;font-weight:bold;">🔄 Reset View</button>
    <script>
        const w=innerWidth,h=innerHeight;
        const svg=d3.select("#c").append("svg").attr("width",w).attr("height",h);
        const g=svg.append("g");
        const progress={progress_json};
        const zoom=d3.zoom()
            .scaleExtent([0.5,2])
            .translateExtent([[-w,-h],[w*2,h*2]])
            .on("zoom",e=>g.attr("transform",e.transform));
        svg.call(zoom);
        const initialTransform=d3.zoomIdentity.translate(w/2,h/2).scale(0.7);
        svg.call(zoom.transform,initialTransform);
        document.getElementById('resetBtn').onclick=()=>svg.transition().duration(750).call(zoom.transform,initialTransform);
        g.append("circle").attr("cx",0).attr("cy",0).attr("r",50).attr("fill","{t['accent']}");
        g.append("text").attr("x",0).attr("y",5).attr("text-anchor","middle").attr("fill","#1a2a3a").attr("font-weight","bold").text("{grade}");
        g.append("text").attr("x",0).attr("y",-60).attr("text-anchor","middle").attr("fill","{t['accent']}").text("🎓 YOU");
        const subjs=[
            {{n:"Math",c:"#3498db",a:-Math.PI/2,courses:["Algebra I","Geometry","Algebra II","Pre-Calc","Calc I"]}},
            {{n:"Science",c:"#27ae60",a:Math.PI*5/6,courses:["Biology","Chemistry","Physics"]}},
            {{n:"CS",c:"#9b59b6",a:Math.PI/6,courses:["Python"]}}
        ];
        subjs.forEach(s=>{{
            const sx=Math.cos(s.a)*140,sy=Math.sin(s.a)*140;
            g.append("line").attr("x1",0).attr("y1",0).attr("x2",sx).attr("y2",sy).attr("stroke","rgba(255,255,255,0.3)");
            g.append("circle").attr("cx",sx).attr("cy",sy).attr("r",35).attr("fill",s.c);
            g.append("text").attr("x",sx).attr("y",sy-45).attr("text-anchor","middle").attr("fill","#fff").attr("font-size","12px").text(s.n);
            const span=Math.PI*0.8;
            s.courses.forEach((c,i)=>{{
                const ca=s.a-span/2+(span/s.courses.length)*(i+0.5);
                const cx=sx+Math.cos(ca)*100,cy=sy+Math.sin(ca)*100;
                const p=progress[c]||{{completed:0,total:1,is_complete:false}};
                const isComplete=p.is_complete||p.completed>0;
                const opacity=isComplete?1:0.3;
                g.append("line").attr("x1",sx).attr("y1",sy).attr("x2",cx).attr("y2",cy).attr("stroke","rgba(255,255,255,0.2)");
                const node=g.append("circle")
                    .attr("cx",cx).attr("cy",cy).attr("r",22)
                    .attr("fill",s.c).attr("opacity",opacity)
                    .attr("class",p.is_complete?"completed-node":"");
                if(p.is_complete){{
                    node.attr("filter","drop-shadow(0 0 8px "+s.c+")");
                    setInterval(()=>{{
                        node.transition().duration(1000).attr("r",24).attr("opacity",0.7)
                            .transition().duration(1000).attr("r",22).attr("opacity",1);
                    }},2000);
                }}
                g.append("text").attr("x",cx).attr("y",cy-30).attr("text-anchor","middle")
                    .attr("fill","#fff").attr("font-size","9px").attr("opacity",opacity).text(c);
                g.append("text").attr("x",cx).attr("y",cy+5).attr("text-anchor","middle")
                    .attr("fill","#fff").attr("font-size","8px").text(p.completed+"/"+p.total);
            }});
        }});
    </script></body></html>'''
    components.html(html, height=350, scrolling=False)

def render_lesson_buttons(progress, prefix="m"):
    tabs = st.tabs(list(COURSE_CATEGORIES.keys()))
    for tab, (cat, courses) in zip(tabs, COURSE_CATEGORIES.items()):
        with tab:
            for course in courses:
                cid = None
                for k,v in COURSE_ID_MAP.items():
                    if v == course: cid = k; break
                syllabus = COURSE_SYLLABI.get(course, [])
                done = sum(1 for i in range(1, len(syllabus)+1) if progress.get(f"{cid}_L{i}") == 'completed')
                with st.expander(f"📚 {course} ({done}/{len(syllabus)})", expanded=False):
                    for row in range(0, len(syllabus), 4):
                        cols = st.columns(4)
                        for i, col in enumerate(cols):
                            idx = row + i
                            if idx >= len(syllabus): break
                            info = syllabus[idx]
                            num = idx + 1
                            key = f"{cid}_L{num}"
                            is_done = progress.get(key) == 'completed'
                            with col:
                                lbl = f"✅ L{num}" if is_done else f"▶ L{num}"
                                if st.button(lbl, key=f"{prefix}_{cid}_{num}", type="secondary" if is_done else "primary", use_container_width=True, help=info['title']):
                                    st.session_state.show_modal = True
                                    st.session_state.lesson_data = {'course': course, 'cid': cid, 'num': num, 'title': info['title'], 'desc': info['desc']}
                                    st.rerun()
# =============================================================================
# 10. QUIZ SYSTEM
# =============================================================================
def generate_quiz(course, title, desc):
    prompt = f"""Generate 5 multiple choice questions for: {course} - {title} ({desc})
Return ONLY JSON: {{"questions":[{{"q":"question","opts":["A)...","B)...","C)...","D)..."],"ans":0,"why":"explanation"}}]}}"""
    try:
        genai.configure(api_key=st.secrets['GEMINI_API_KEY'])
        model = genai.GenerativeModel(MODEL_CONFIG["FLASH"])
        resp = model.generate_content(prompt)
        txt = resp.text.strip()
        if txt.startswith("```"): txt = txt.split("```")[1].replace("json","").strip()
        return json.loads(txt)
    except: return None

def render_quiz(quiz, lesson_key, user_id):
    if not quiz or 'questions' not in quiz: return
    st.markdown("### 📝 Quiz")
    qs = quiz['questions']
    ans = {}
    with st.form(f"quiz_{lesson_key}"):
        for i, q in enumerate(qs):
            st.markdown(f"**Q{i+1}: {q['q']}**")
            ans[i] = st.radio(f"Q{i+1}", q['opts'], key=f"q_{lesson_key}_{i}", label_visibility="collapsed")
            st.markdown("---")
        if st.form_submit_button("Submit", type="primary"):
            correct = 0
            for i, q in enumerate(qs):
                if ans[i] in q['opts'] and q['opts'].index(ans[i]) == q['ans']:
                    correct += 1
            score = int((correct/len(qs))*100)
            st.markdown(f"## Score: {score}%")
            xp = score//2 + (25 if score >= 80 else 0) + (25 if score == 100 else 0)
            play_sound("quiz")
            award_xp(user_id, xp)
            st.success(f"+{xp} XP!")
            award_badge(user_id, "first_quiz")
            if score == 100: award_badge(user_id, "perfect_quiz")
            return score
    return None

# =============================================================================
# 11. POMODORO TIMER
# =============================================================================
def render_pomodoro():
    st.markdown("### 🍅 Pomodoro Timer")
    if 'pomo_active' not in st.session_state: st.session_state.pomo_active = False
    if 'pomo_start' not in st.session_state: st.session_state.pomo_start = None
    if 'pomo_count' not in st.session_state: st.session_state.pomo_count = 0
    
    dur = st.select_slider("Duration", [15,20,25,30,45,60], value=25, format_func=lambda x:f"{x}min")
    
    if st.session_state.pomo_active and st.session_state.pomo_start:
        elapsed = (datetime.now() - st.session_state.pomo_start).total_seconds()
        remain = max(0, dur*60 - elapsed)
        m, s = int(remain//60), int(remain%60)
        st.markdown(f'<div class="pomodoro-timer">⏱️ {m:02d}:{s:02d}</div>', unsafe_allow_html=True)
        st.progress(1 - remain/(dur*60))
        if remain <= 0:
            st.session_state.pomo_active = False
            st.session_state.pomo_count += 1

            # Save lifetime pomodoro count to database
            conn = get_db()
            if conn:
                cur = conn.cursor()
                cur.execute(f"USE {st.secrets['DB_NAME']};")
                cur.execute("UPDATE Users SET pomodoros_completed = pomodoros_completed + 1 WHERE user_id=%s",
                           (st.session_state.user_id,))
                conn.commit()
                cur.close()
                conn.close()

            st.balloons()
            play_sound("xp")
            award_xp(st.session_state.user_id, 25)

            # Award badge after 5 total pomodoros
            if st.session_state.pomo_count >= 5:
                award_badge(st.session_state.user_id, "pomodoro_5")

            st.success("🎉 Pomodoro Complete! +25 XP")
        if st.button("⏹️ Stop"): st.session_state.pomo_active = False; st.rerun()
        time.sleep(1); st.rerun()
    else:
        st.markdown(f'<div class="pomodoro-timer">🍅 {dur}:00</div>', unsafe_allow_html=True)
        if st.button("▶️ Start", type="primary"):
            st.session_state.pomo_active = True
            st.session_state.pomo_start = datetime.now()
            st.rerun()
    st.caption(f"Today: {st.session_state.pomo_count} 🍅")
# =============================================================================
# 12. LEARNING MODE
# =============================================================================
def render_learning():
    ld = st.session_state.lesson_data
    if not ld:
        st.error("No lesson!")
        if st.button("Back"): st.session_state.learning = False; st.rerun()
        return
    
    t = get_theme()
    st.markdown(f'<div style="background:{t["bg"]};padding:20px;border-radius:12px;border:1px solid {t["accent"]}"><h2 style="color:{t["accent"]}">📚 {ld["course"]}</h2><h3>{ld["title"]}</h3><p style="color:#aaa">Section {st.session_state.section}/5 • {st.session_state.difficulty}</p></div>', unsafe_allow_html=True)
    st.progress(st.session_state.section / 5)
    
    c1,c2,c3 = st.columns([6,1,1])
    with c3:
        if st.button("❌ Exit"):
            st.session_state.learning = False
            st.session_state.lesson_msgs = []
            st.session_state.section = 1
            st.rerun()
    
    for m in st.session_state.lesson_msgs:
        with st.chat_message(m["role"]): st.markdown(m["content"])
    
    if not st.session_state.lesson_msgs: teach_lesson()
    
    if st.session_state.get('show_quiz') and st.session_state.section >= 5:
        if st.session_state.get('quiz_data'):
            render_quiz(st.session_state.quiz_data, f"{ld['cid']}_L{ld['num']}", st.session_state.user_id)
    
    st.markdown("---")
    q = st.text_input("Ask a question...", key="lesson_q")
    c1,c2,c3,c4 = st.columns([2,1,1,1])
    with c1:
        if st.button("🚀 Ask", type="primary") and q: ask_q(q)
    with c2:
        if st.button("⬅ Prev", disabled=st.session_state.section<=1):
            st.session_state.section -= 1; continue_lesson()
    with c3:
        if st.button("Next ➡", disabled=st.session_state.section>=5):
            st.session_state.section += 1; continue_lesson()
    with c4:
        if st.button("✓ Done", type="primary" if st.session_state.section>=5 else "secondary"):
            mark_done()

def teach_lesson():
    ld = st.session_state.lesson_data
    st.session_state.flash_usage += 1
    update_usage()
    
    diff_txt = {"Simple":"Explain like they're 10.","Standard":"Grade-appropriate.","Advanced":"Deep technical detail."}
    prompt = f"""Teach {ld['course']} - {ld['title']} to a {st.session_state.grade} student.
Topic: {ld['desc']}. Difficulty: {st.session_state.difficulty}. {diff_txt.get(st.session_state.difficulty,'')}
1. Welcome 2. Core concept with examples 3. Practice problem. Use emojis!"""
    
    try:
        genai.configure(api_key=st.secrets['GEMINI_API_KEY'])
        model = genai.GenerativeModel(MODEL_CONFIG["FLASH"])
        with st.spinner("🧠 Loading..."):
            resp = model.generate_content(prompt)
            st.session_state.lesson_msgs.append({"role":"assistant","content":resp.text})
        st.rerun()
    except Exception as e: st.error(str(e))

def continue_lesson():
    ld = st.session_state.lesson_data
    st.session_state.flash_usage += 1
    update_usage()
    
    prompt = f"""Continue {ld['course']} - {ld['title']}. Section {st.session_state.section}/5.
Sections: 1-Intro, 2-Examples, 3-Practice, 4-Common mistakes, 5-Summary. Difficulty: {st.session_state.difficulty}"""
    
    try:
        genai.configure(api_key=st.secrets['GEMINI_API_KEY'])
        model = genai.GenerativeModel(MODEL_CONFIG["FLASH"])
        with st.spinner(f"📖 Section {st.session_state.section}..."):
            resp = model.generate_content(prompt)
            st.session_state.lesson_msgs.append({"role":"assistant","content":f"## Section {st.session_state.section}\n\n{resp.text}"})
        st.rerun()
    except Exception as e: st.error(str(e))

def ask_q(q):
    ld = st.session_state.lesson_data
    st.session_state.flash_usage += 1
    update_usage()
    st.session_state.lesson_msgs.append({"role":"user","content":q})
    
    prompt = f"""Student learning {ld['course']} - {ld['title']} asked: {q}. Help them!"""
    try:
        genai.configure(api_key=st.secrets['GEMINI_API_KEY'])
        model = genai.GenerativeModel(MODEL_CONFIG["FLASH"])
        with st.spinner("🤔..."):
            resp = model.generate_content(prompt)
            st.session_state.lesson_msgs.append({"role":"assistant","content":resp.text})
        st.rerun()
    except Exception as e: st.error(str(e))

def mark_done():
    ld = st.session_state.lesson_data
    key = f"{ld['cid']}_L{ld['num']}"

    conn = get_db()
    if conn:
        cur = conn.cursor()
        cur.execute(f"USE {st.secrets['DB_NAME']};")
        cur.execute("INSERT INTO UserLessonProgress (user_id,lesson_key,status,completed_date) VALUES (%s,%s,'completed',NOW()) ON DUPLICATE KEY UPDATE status='completed',completed_date=NOW()", (st.session_state.user_id, key))
        conn.commit()
        cur.close()
        conn.close()

    st.session_state.progress[key] = 'completed'

    # Update streak and daily goals
    update_streak(st.session_state.user_id)
    increment_daily_lessons(st.session_state.user_id)

    award_xp(st.session_state.user_id, 50)

    done = len([k for k,v in st.session_state.progress.items() if v=='completed'])
    award_badge(st.session_state.user_id, "first_lesson")
    if done >= 5: award_badge(st.session_state.user_id, "five_lessons")
    if done >= 10: award_badge(st.session_state.user_id, "ten_lessons")

    if ld['course'] in ['Algebra I','Geometry','Algebra II','Pre-Calculus','Calculus I']:
        award_badge(st.session_state.user_id, "math_explorer")
    elif ld['course'] in ['Biology','Chemistry','Physics']:
        award_badge(st.session_state.user_id, "science_explorer")
    elif ld['course'] == 'Intro to Python':
        award_badge(st.session_state.user_id, "code_explorer")

    hr = datetime.now().hour
    if hr >= 22 or hr < 5: award_badge(st.session_state.user_id, "night_owl")
    if 5 <= hr < 7: award_badge(st.session_state.user_id, "early_bird")

    st.success("🎉 +50 XP!")

    if st.session_state.section >= 5:
        with st.spinner("Generating quiz..."):
            st.session_state.quiz_data = generate_quiz(ld['course'], ld['title'], ld['desc'])
            st.session_state.show_quiz = True
        st.rerun()

def update_usage():
    conn = get_db()
    if conn:
        cur = conn.cursor()
        cur.execute(f"USE {st.secrets['DB_NAME']};")
        cur.execute("UPDATE Users SET flash_usage=%s, pro_usage=%s WHERE user_id=%s",
                   (st.session_state.flash_usage, st.session_state.pro_usage, st.session_state.user_id))
        conn.commit()
        cur.close()
        conn.close()
# =============================================================================
# 13. SESSION STATE
# =============================================================================
defaults = {
    'authenticated': False, 'user_id': None, 'grade': '9th', 'flash_usage': 0, 'pro_usage': 0,
    'messages': [], 'session_id': None, 'theme': 'Auto', 'total_xp': 0, 'level': 1,
    'badges': [], 'progress': {}, 'beta_mode': False, 'learning': False, 'lesson_data': None,
    'difficulty': 'Standard', 'section': 1, 'lesson_msgs': [], 'show_modal': False,
    'show_quiz': False, 'quiz_data': None, 'pomo_count': 0, 'sounds_enabled': True,
    'streak_count': 0, 'daily_lessons_completed': 0, 'daily_goal': 3, 'pet_stage': 'egg', 'pet_mood': 'neutral'
}
for k,v in defaults.items():
    if k not in st.session_state: st.session_state[k] = v

GRADES = ["9th","10th","11th","12th","College"]
DIFFICULTIES = ["Simple","Standard","Advanced"]

def load_user(uid):
    conn = get_db()
    if conn:
        cur = conn.cursor(dictionary=True)
        cur.execute(f"USE {st.secrets['DB_NAME']};")
        cur.execute("SELECT lesson_key, status FROM UserLessonProgress WHERE user_id=%s", (uid,))
        st.session_state.progress = {r['lesson_key']:r['status'] for r in cur.fetchall()}
        st.session_state.badges = get_badges(uid)

        # Load streak, daily goal, and pet data
        cur.execute("SELECT streak_count, daily_lessons_completed, daily_goal, pet_stage, pet_mood FROM Users WHERE user_id=%s", (uid,))
        user_data = cur.fetchone()
        if user_data:
            st.session_state.streak_count = user_data.get('streak_count', 0) or 0
            st.session_state.daily_lessons_completed = user_data.get('daily_lessons_completed', 0) or 0
            st.session_state.daily_goal = user_data.get('daily_goal', 3) or 3
            st.session_state.pet_stage = user_data.get('pet_stage', 'egg') or 'egg'
            st.session_state.pet_mood = user_data.get('pet_mood', 'neutral') or 'neutral'

        cur.close()
        conn.close()

# =============================================================================
# 13A. SOUND EFFECTS
# =============================================================================
def play_sound(sound_type):
    """Play sound effect if enabled"""
    if not st.session_state.get('sounds_enabled', True):
        return

    # Using data URIs for simple beep sounds
    sounds = {
        "xp": "data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLaijcIGGa67OehUBELTKXh8LZkHAU6ktbzyn4qBSl+zPDajzsIFmO96+mjUxEKSKHe8bhkHwU4kdXzzHsrBCh7yO/fiD0IFl++7OqkVBEJSaPf8rhlHwU6k9bywHwqBCd5xvDdizwIFl296+mkUxELSKPd8LdlHwU3kdTzzHorBCd5yO/eiz0HFV3A7OmjUREMSKLd8LdlHwU3kdTyzHktBSd4yPDdiz0HFl3A7OqkURIOSKLd8LdlHwU2kNXzy3ktBSd4x/DdizsJFl286+mkUhEMSKPd8bhmHgU3kdXyy3ktBSd5yPDbiT0HFl+/7OqkUhELSKHe8LhlHwU3kdXzzHotBCh6yPDdiz0HFF2+7OqkUxEKR6Lf8bdlHwU4k9TyynotBCd5x/DdizwIFl++7OqkUhELR6Hf8bdlHgU4k9TzynwsBCh5x/DdizwHFl696+mlUhELRqLf8rZmHgU4ktXzynwsBCh5yPDciz0HFl696+mlUhELRqHf8rZlHgU4ktXzynwrBSh5yPDciz0HFl++6+mlURELRqHf8bZmHgU4k9TyynwrBSh5x/DdizwHFl286+mlUxELRqHf8bdlHgU4ktTzynwrBSh5yPDciz0HFl696+mlUhELRqHf8bdlHgU4k9XyyXwsBCh5yO/diz0HFV696+mlUhELR6Hf8rZmHgU4ktXzynwrBSh5yPDciz0HFl+96+mlUhELRqHf8rZlHgU4ktXzynwrBSh5yPDciz0HFl+96+mlUhELRqHf8rZlHgU4ktXzynwrBSh5yPDciz0HFl+96+mlUhELRqHf8rZlHgU4ktXzynwrBSh5yPDciz0HFl+96+mlUhELRqHf8rZlHgU4ktXzynwrBSh5yPDciz0HFl+96+mlUhELRqHf8rZlHgU4ktXzynwrBSh5yPDciz0HFl+96+mlUhELRqHf8rZlHgU4ktXzynwrBSh5yPDciz0HFl+96+mlUhELRqHf8rZlHgU4ktXzynwrBSh5yPDciz0HFl+96+mlUhELRqHf8rZlHgU4ktXzynwrBSh5yPDciz0HFl+96+mlUhELRqHf8rZlHgU4ktXzynwrBSh5yPDciz0HFl+96+mlUhELRqHf8rZlHgU4ktXzynwrBSh5yPDciz0HFl+96+mlUhELRqHf8rZlHgU4ktXzynwrBSh5yPDciz0HFl+96+mlUhELRqHf8Q==",
        "levelup": "data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLaijcIGGa67OehUBELTKXh8LZkHAU6ktbzyn4qBSl+zPDajzsIFmO96+mjUxEKSKHe8bhkHwU4kdXzzHsrBCh7yO/fiD0IFl++7OqkVBEJSaPf8rhlHwU6k9bywHwqBCd5xvDdizwIFl296+mkUxELSKPd8LdlHwU3kdTzzHorBCd5yO/eiz0HFV3A7OmjUREMSKLd8LdlHwU3kdTyzHktBSd4yPDdiz0HFl3A7OqkURIOSKLd8LdlHwU2kNXzy3ktBSd4x/DdizsJFl286+mkUhEMSKPd8bhmHgU3kdXyy3ktBSd5yPDbiT0HFl+/7OqkUhELSKHe8LhlHwU3kdXzzHotBCh6yPDdiz0HFF2+7OqkUxEKR6Lf8bdlHwU4k9TyynotBCd5x/DdizwIFl++7OqkUhELR6Hf8bdlHgU4k9TzynwsBCh5x/DdizwHFl696+mlUhELRqLf8rZmHgU4ktXzynwsBCh5yPDciz0HFl696+mlUhELRqHf8rZlHgU4ktXzynwrBSh5yPDciz0HFl++6+mlURELRqHf8bZmHgU4k9TyynwrBSh5x/DdizwHFl286+mlUxELRqHf8bdlHgU4ktTzynwrBSh5yPDciz0HFl696+mlUhELRqHf8bdlHgU4k9XyyXwsBCh5yO/diz0HFV696+mlUhELR6Hf8rZmHgU4ktXzynwrBSh5yPDciz0HFl+96+mlUhELRqHf8rZlHgU4ktXzynwrBSh5yPDciz0HFl+96+mlUhELRqHf8rZlHgU4ktXzynwrBSh5yPDciz0HFl+96+mlUhELRqHf8rZlHgU4ktXzynwrBSh5yPDciz0HFl+96+mlUhELRqHf8rZlHgU4ktXzynwrBSh5yPDciz0HFl+96+mlUhELRqHf8rZlHgU4ktXzynwrBSh5yPDciz0HFl+96+mlUhELRqHf8rZlHgU4ktXzynwrBSh5yPDciz0HFl+96+mlUhELRqHf8rZlHgU4ktXzynwrBSh5yPDciz0HFl+96+mlUhELRqHf8rZlHgU4ktXzynwrBSh5yPDciz0HFl+96+mlUhELRqHf8rZlHgU4ktXzynwrBSh5yPDciz0HFl+96+mlUhELRqHf8Q==",
        "badge": "data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLaijcIGGa67OehUBELTKXh8LZkHAU6ktbzyn4qBSl+zPDajzsIFmO96+mjUxEKSKHe8bhkHwU4kdXzzHsrBCh7yO/fiD0IFl++7OqkVBEJSaPf8rhlHwU6k9bywHwqBCd5xvDdizwIFl296+mkUxELSKPd8LdlHwU3kdTzzHorBCd5yO/eiz0HFV3A7OmjUREMSKLd8LdlHwU3kdTyzHktBSd4yPDdiz0HFl3A7OqkURIOSKLd8LdlHwU2kNXzy3ktBSd4x/DdizsJFl286+mkUhEMSKPd8bhmHgU3kdXyy3ktBSd5yPDbiT0HFl+/7OqkUhELSKHe8LhlHwU3kdXzzHotBCh6yPDdiz0HFF2+7OqkUxEKR6Lf8bdlHwU4k9TyynotBCd5x/DdizwIFl++7OqkUhELR6Hf8bdlHgU4k9TzynwsBCh5x/DdizwHFl696+mlUhELRqLf8rZmHgU4ktXzynwsBCh5yPDciz0HFl696+mlUhELRqHf8rZlHgU4ktXzynwrBSh5yPDciz0HFl++6+mlURELRqHf8bZmHgU4k9TyynwrBSh5x/DdizwHFl286+mlUxELRqHf8bdlHgU4ktTzynwrBSh5yPDciz0HFl696+mlUhELRqHf8bdlHgU4k9XyyXwsBCh5yO/diz0HFV696+mlUhELR6Hf8rZmHgU4ktXzynwrBSh5yPDciz0HFl+96+mlUhELRqHf8rZlHgU4ktXzynwrBSh5yPDciz0HFl+96+mlUhELRqHf8rZlHgU4ktXzynwrBSh5yPDciz0HFl+96+mlUhELRqHf8rZlHgU4ktXzynwrBSh5yPDciz0HFl+96+mlUhELRqHf8rZlHgU4ktXzynwrBSh5yPDciz0HFl+96+mlUhELRqHf8rZlHgU4ktXzynwrBSh5yPDciz0HFl+96+mlUhELRqHf8rZlHgU4ktXzynwrBSh5yPDciz0HFl+96+mlUhELRqHf8rZlHgU4ktXzynwrBSh5yPDciz0HFl+96+mlUhELRqHf8rZlHgU4ktXzynwrBSh5yPDciz0HFl+96+mlUhELRqHf8rZlHgU4ktXzynwrBSh5yPDciz0HFl+96+mlUhELRqHf8Q==",
        "quiz": "data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLaijcIGGa67OehUBELTKXh8LZkHAU6ktbzyn4qBSl+zPDajzsIFmO96+mjUxEKSKHe8bhkHwU4kdXzzHsrBCh7yO/fiD0IFl++7OqkVBEJSaPf8rhlHwU6k9bywHwqBCd5xvDdizwIFl296+mkUxELSKPd8LdlHwU3kdTzzHorBCd5yO/eiz0HFV3A7OmjUREMSKLd8LdlHwU3kdTyzHktBSd4yPDdiz0HFl3A7OqkURIOSKLd8LdlHwU2kNXzy3ktBSd4x/DdizsJFl286+mkUhEMSKPd8bhmHgU3kdXyy3ktBSd5yPDbiT0HFl+/7OqkUhELSKHe8LhlHwU3kdXzzHotBCh6yPDdiz0HFF2+7OqkUxEKR6Lf8bdlHwU4k9TyynotBCd5x/DdizwIFl++7OqkUhELR6Hf8bdlHgU4k9TzynwsBCh5x/DdizwHFl696+mlUhELRqLf8rZmHgU4ktXzynwsBCh5yPDciz0HFl696+mlUhELRqHf8rZlHgU4ktXzynwrBSh5yPDciz0HFl++6+mlURELRqHf8bZmHgU4k9TyynwrBSh5x/DdizwHFl286+mlUxELRqHf8bdlHgU4ktTzynwrBSh5yPDciz0HFl696+mlUhELRqHf8bdlHgU4k9XyyXwsBCh5yO/diz0HFV696+mlUhELR6Hf8rZmHgU4ktXzynwrBSh5yPDciz0HFl+96+mlUhELRqHf8rZlHgU4ktXzynwrBSh5yPDciz0HFl+96+mlUhELRqHf8rZlHgU4ktXzynwrBSh5yPDciz0HFl+96+mlUhELRqHf8rZlHgU4ktXzynwrBSh5yPDciz0HFl+96+mlUhELRqHf8rZlHgU4ktXzynwrBSh5yPDciz0HFl+96+mlUhELRqHf8rZlHgU4ktXzynwrBSh5yPDciz0HFl+96+mlUhELRqHf8rZlHgU4ktXzynwrBSh5yPDciz0HFl+96+mlUhELRqHf8rZlHgU4ktXzynwrBSh5yPDciz0HFl+96+mlUhELRqHf8rZlHgU4ktXzynwrBSh5yPDciz0HFl+96+mlUhELRqHf8rZlHgU4ktXzynwrBSh5yPDciz0HFl+96+mlUhELRqHf8Q=="
    }

    sound_html = f'<audio autoplay><source src="{sounds.get(sound_type, sounds["xp"])}" type="audio/wav"></audio>'
    components.html(sound_html, height=0)

# =============================================================================
# 13B. STREAK & DAILY GOALS
# =============================================================================
def update_streak(user_id):
    """Update user's study streak"""
    from datetime import datetime, timedelta
    conn = get_db()
    if conn:
        cur = conn.cursor(dictionary=True)
        cur.execute(f"USE {st.secrets['DB_NAME']};")
        cur.execute("SELECT streak_count, last_study_date FROM Users WHERE user_id=%s", (user_id,))
        row = cur.fetchone()

        if row:
            today = datetime.now().date()
            last_date = datetime.strptime(row['last_study_date'], "%Y-%m-%d").date() if row.get('last_study_date') else None
            current_streak = row.get('streak_count', 0) or 0

            if last_date:
                days_diff = (today - last_date).days
                if days_diff == 0:
                    # Already studied today
                    pass
                elif days_diff == 1:
                    # Consecutive day - increment streak
                    current_streak += 1
                    cur.execute("UPDATE Users SET streak_count=%s, last_study_date=%s WHERE user_id=%s",
                               (current_streak, today.strftime("%Y-%m-%d"), user_id))

                    # Award milestone bonuses
                    if current_streak == 7:
                        award_xp(user_id, 100)
                        st.success("🔥 7 Day Streak! +100 Bonus XP!")
                    elif current_streak == 14:
                        award_xp(user_id, 200)
                        st.success("🔥 14 Day Streak! +200 Bonus XP!")
                    elif current_streak == 30:
                        award_xp(user_id, 500)
                        st.success("🔥 30 Day Streak! +500 Bonus XP!")
                else:
                    # Streak broken - reset
                    current_streak = 1
                    cur.execute("UPDATE Users SET streak_count=1, last_study_date=%s WHERE user_id=%s",
                               (today.strftime("%Y-%m-%d"), user_id))
            else:
                # First time studying
                current_streak = 1
                cur.execute("UPDATE Users SET streak_count=1, last_study_date=%s WHERE user_id=%s",
                           (today.strftime("%Y-%m-%d"), user_id))

            conn.commit()
            st.session_state.streak_count = current_streak
        cur.close()
        conn.close()

def increment_daily_lessons(user_id):
    """Increment daily lesson count and check goal"""
    conn = get_db()
    if conn:
        cur = conn.cursor(dictionary=True)
        cur.execute(f"USE {st.secrets['DB_NAME']};")
        cur.execute("SELECT daily_lessons_completed, daily_goal FROM Users WHERE user_id=%s", (user_id,))
        row = cur.fetchone()

        if row:
            completed = (row.get('daily_lessons_completed', 0) or 0) + 1
            goal = row.get('daily_goal', 3) or 3

            cur.execute("UPDATE Users SET daily_lessons_completed=%s WHERE user_id=%s", (completed, user_id))
            conn.commit()

            st.session_state.daily_lessons_completed = completed
            st.session_state.daily_goal = goal

            # Award bonus when goal is met
            if completed == goal:
                award_xp(user_id, 50)
                st.success(f"🎯 Daily Goal Achieved! Completed {goal} lessons! +50 Bonus XP!")

        cur.close()
        conn.close()

# =============================================================================
# 13B2. STUDY PET SYSTEM
# =============================================================================
def update_pet_status(user_id, current_level):
    """Update pet evolution based on level and activity"""
    conn = get_db()
    if conn:
        cur = conn.cursor(dictionary=True)
        cur.execute(f"USE {st.secrets['DB_NAME']};")
        cur.execute("SELECT pet_stage, last_study_date FROM Users WHERE user_id=%s", (user_id,))
        row = cur.fetchone()

        if row:
            current_stage = row.get('pet_stage', 'egg')
            last_date = row.get('last_study_date')

            # Determine pet stage based on level
            new_stage = 'egg'
            if current_level >= 10:
                new_stage = 'adult'
            elif current_level >= 6:
                new_stage = 'teen'
            elif current_level >= 3:
                new_stage = 'baby'

            # Determine mood based on recent activity
            today = datetime.now().date()
            if last_date:
                last_study = datetime.strptime(last_date, "%Y-%m-%d").date()
                days_since = (today - last_study).days
                mood = 'happy' if days_since == 0 else ('neutral' if days_since == 1 else 'sad')
            else:
                mood = 'neutral'

            # Update if changed
            if new_stage != current_stage or mood != row.get('pet_mood', 'neutral'):
                cur.execute("UPDATE Users SET pet_stage=%s, pet_mood=%s WHERE user_id=%s",
                           (new_stage, mood, user_id))
                conn.commit()
                st.session_state.pet_stage = new_stage
                st.session_state.pet_mood = mood

        cur.close()
        conn.close()

def get_pet_display():
    """Return emoji and text for current pet state"""
    stage = st.session_state.get('pet_stage', 'egg')
    mood = st.session_state.get('pet_mood', 'neutral')

    pets = {
        'egg': {'emoji': '🥚', 'name': 'Mysterious Egg'},
        'baby': {'emoji': '🐣', 'name': 'Baby Scholar'},
        'teen': {'emoji': '🐥', 'name': 'Teen Genius'},
        'adult': {'emoji': '🦉', 'name': 'Wise Owl'}
    }

    moods = {
        'happy': '😊',
        'neutral': '😐',
        'sad': '😢'
    }

    pet = pets.get(stage, pets['egg'])
    return f"{pet['emoji']} {moods.get(mood, '😐')}", pet['name']

# =============================================================================
# 13C. AUTO CHAT TITLES
# =============================================================================
def generate_chat_title(first_message):
    """Generate a concise chat title from the first message"""
    # Try AI summary first
    try:
        genai.configure(api_key=st.secrets['GEMINI_API_KEY'])
        model = genai.GenerativeModel(MODEL_CONFIG["FLASH"])
        prompt = f"Generate a concise 3-5 word title for a chat that starts with: '{first_message[:100]}'. Return ONLY the title, nothing else."
        resp = model.generate_content(prompt)
        title = resp.text.strip().replace('"', '').replace("'", "")[:50]
        return title if title else first_message[:30]
    except:
        # Fallback to first 30 chars
        return first_message[:30]

def update_chat_title(session_id, title):
    """Update the title of a chat session"""
    conn = get_db()
    if conn:
        cur = conn.cursor()
        cur.execute(f"USE {st.secrets['DB_NAME']};")
        cur.execute("UPDATE ChatLogs SET title=%s WHERE session_id=%s", (title, session_id))
        conn.commit()
        cur.close()
        conn.close()

# =============================================================================
# 13D. CHAT MANAGEMENT
# =============================================================================
def delete_empty_chats(user_id, current_session_id=None):
    """Delete all empty chats (title='New' and empty messages) for a user"""
    conn = get_db()
    if conn:
        cur = conn.cursor()
        cur.execute(f"USE {st.secrets['DB_NAME']};")
        # Delete chats with title 'New' and empty or null messages
        if current_session_id:
            cur.execute("""DELETE FROM ChatLogs WHERE user_id=%s AND title='New'
                        AND (messages='[]' OR messages IS NULL OR messages='')
                        AND session_id=%s""", (user_id, current_session_id))
        else:
            cur.execute("""DELETE FROM ChatLogs WHERE user_id=%s AND title='New'
                        AND (messages='[]' OR messages IS NULL OR messages='')""", (user_id,))
        conn.commit()
        cur.close()
        conn.close()

# =============================================================================
# 14. AUTH PAGE
# =============================================================================
if not st.session_state.authenticated:
    c1,c2,c3 = st.columns([1,6,1])
    with c2:
        st.title("🔐 Sorokin Portal")
        t1,t2,t3,t4 = st.tabs(["Login","Register","Plans","🧪 Beta"])
        
        with t1:
            u = st.text_input("Username", key="lu")
            p = st.text_input("Password", type="password", key="lp")
            if st.button("Log In", type="primary", use_container_width=True):
                conn = get_db()
                if conn:
                    cur = conn.cursor(dictionary=True)
                    cur.execute(f"USE {st.secrets['DB_NAME']};")
                    cur.execute("SELECT * FROM Users WHERE username=%s", (u,))
                    user = cur.fetchone()
                    if user and bcrypt.checkpw(p.encode(), user['hashed_password'].encode()):
                        today = datetime.now().strftime("%Y-%m-%d")
                        if user['last_active_date'] != today:
                            cur.execute("UPDATE Users SET flash_usage=0,pro_usage=0,last_active_date=%s WHERE user_id=%s", (today,user['user_id']))
                            conn.commit()
                            user['flash_usage'] = user['pro_usage'] = 0
                        sid = f"S_{uuid.uuid4().hex[:4]}"
                        st.session_state.update({
                            'authenticated': True, 'user_id': user['user_id'], 'grade': user['grade'],
                            'session_id': sid, 'flash_usage': user['flash_usage'], 'pro_usage': user['pro_usage'],
                            'total_xp': user.get('total_xp',0) or 0, 'level': user.get('level',1) or 1,
                            'theme': user.get('theme','Auto') or 'Auto', 'beta_mode': False
                        })
                        cur.execute("UPDATE Users SET session_id=%s WHERE user_id=%s", (sid,user['user_id']))
                        cur.execute("INSERT INTO ChatLogs (session_id,user_id,title,messages) VALUES (%s,%s,'New','[]')", (sid,user['user_id']))
                        conn.commit()
                        load_user(user['user_id'])
                        st.rerun()
                    else: st.error("Invalid credentials")
                    cur.close()
                    conn.close()
        
        with t2:
            nu = st.text_input("Username", key="ru")
            np = st.text_input("Password", type="password", key="rp")
            ng = st.selectbox("Grade", GRADES, key="rg")
            if st.button("Register", type="primary", use_container_width=True):
                conn = get_db()
                if conn:
                    cur = conn.cursor()
                    cur.execute(f"USE {st.secrets['DB_NAME']};")
                    try:
                        h = bcrypt.hashpw(np.encode(), bcrypt.gensalt()).decode()
                        uid, sid = f"U_{uuid.uuid4().hex[:4]}", f"S_{uuid.uuid4().hex[:4]}"
                        cur.execute("INSERT INTO Users (username,hashed_password,grade,user_id,session_id,last_active_date,total_xp,level,theme) VALUES (%s,%s,%s,%s,%s,%s,0,1,'Auto')", (nu,h,ng,uid,sid,datetime.now().strftime("%Y-%m-%d")))
                        conn.commit()
                        st.success("Created! Log in now.")
                    except: st.error("Username taken")
                    cur.close()
                    conn.close()
        
        with t3:
            st.markdown("### Plans\n| Feature | Free | Pro |\n|---|---|---|\n| Flash | 100/day | ∞ |\n| Ultra | 5/day | 50/day |")
        
        with t4:
            st.markdown('<div class="beta-banner">🧪 Beta Features!</div>', unsafe_allow_html=True)
            st.markdown("- ⚡ XP & Leveling\n- 🏆 Badges\n- 📝 Quizzes\n- 🍅 Pomodoro\n- 🎨 Themes")
            bu = st.text_input("Username", key="bu")
            bp = st.text_input("Password", type="password", key="bp")
            if st.button("🚀 Enter Beta", type="primary", use_container_width=True):
                conn = get_db()
                if conn:
                    cur = conn.cursor(dictionary=True)
                    cur.execute(f"USE {st.secrets['DB_NAME']};")
                    cur.execute("SELECT * FROM Users WHERE username=%s", (bu,))
                    user = cur.fetchone()
                    if user and bcrypt.checkpw(bp.encode(), user['hashed_password'].encode()):
                        today = datetime.now().strftime("%Y-%m-%d")
                        if user['last_active_date'] != today:
                            cur.execute("UPDATE Users SET flash_usage=0,pro_usage=0,last_active_date=%s WHERE user_id=%s", (today,user['user_id']))
                            conn.commit()
                            user['flash_usage'] = user['pro_usage'] = 0
                        st.session_state.update({
                            'authenticated': True, 'beta_mode': True, 'user_id': user['user_id'],
                            'grade': user['grade'], 'flash_usage': user['flash_usage'], 'pro_usage': user['pro_usage'],
                            'total_xp': user.get('total_xp',0) or 0, 'level': user.get('level',1) or 1,
                            'theme': user.get('theme','Auto') or 'Auto'
                        })
                        load_user(user['user_id'])
                        st.rerun()
                    else: st.error("Invalid credentials")
                    cur.close()
                    conn.close()
    st.stop()
# =============================================================================
# 15. LESSON MODAL
# =============================================================================
if st.session_state.show_modal and st.session_state.lesson_data:
    ld = st.session_state.lesson_data
    t = get_theme()
    f_rem = max(0, 100 - st.session_state.flash_usage)
    
    if f_rem <= 0:
        st.error("⚠️ Daily limit reached!")
        if st.button("Back"): st.session_state.show_modal = False; st.rerun()
        st.stop()
    
    st.markdown(f'<div style="background:rgba(0,0,0,0.8);padding:30px;border-radius:16px;border:2px solid {t["accent"]};max-width:500px;margin:50px auto"><h2 style="color:{t["accent"]}">📚 {ld["title"]}</h2><p style="color:#aaa">{ld["course"]}</p><p>{ld["desc"]}</p><p style="color:#888;font-size:12px">⚡ Uses 1 Flash credit ({f_rem} left)</p></div>', unsafe_allow_html=True)
    
    diff = st.radio("Difficulty:", DIFFICULTIES, index=1, horizontal=True)
    c1,c2 = st.columns(2)
    with c1:
        if st.button("▶ START", type="primary", use_container_width=True):
            st.session_state.difficulty = diff
            st.session_state.learning = True
            st.session_state.show_modal = False
            st.session_state.section = 1
            st.session_state.lesson_msgs = []
            st.session_state.show_quiz = False
            st.rerun()
    with c2:
        if st.button("Cancel", use_container_width=True):
            st.session_state.show_modal = False
            st.session_state.lesson_data = None
            st.rerun()
    st.stop()

# =============================================================================
# 16. LEARNING MODE
# =============================================================================
if st.session_state.learning:
    render_learning()
    st.stop()

# =============================================================================
# 17. BETA MODE
# =============================================================================
if st.session_state.beta_mode:
    st.markdown('<div class="beta-banner">🧪 BETA MODE</div>', unsafe_allow_html=True)
    
    lvl = get_level_info(st.session_state.total_xp)
    c1,c2 = st.columns([3,1])
    with c1:
        st.markdown(f'<div class="level-display">⭐ Lv.{lvl["level"]}: {lvl["name"]} | {st.session_state.total_xp} XP</div>', unsafe_allow_html=True)
        st.progress(lvl['progress']/100)
        st.caption(f"{lvl['needed']} XP to next level")
    with c2:
        new_theme = st.selectbox("🎨", list(THEMES.keys()), index=list(THEMES.keys()).index(st.session_state.theme))
        if new_theme != st.session_state.theme:
            st.session_state.theme = new_theme
            conn = get_db()
            if conn:
                cur = conn.cursor()
                cur.execute(f"USE {st.secrets['DB_NAME']};")
                cur.execute("UPDATE Users SET theme=%s WHERE user_id=%s", (new_theme, st.session_state.user_id))
                conn.commit()
                cur.close()
                conn.close()
            st.rerun()
    
    st.caption(f"⚡ Flash: {100-st.session_state.flash_usage}/100 | 🧠 Ultra: {5-st.session_state.pro_usage}/5")
    st.markdown("---")
    
    tabs = st.tabs(["🌌 Learn", "🏆 Badges", "🍅 Pomodoro", "💬 Chat"])
    
    with tabs[0]:
        st.markdown("### 🌌 Learning Constellation")
        render_constellation(st.session_state.grade, st.session_state.progress)
        st.markdown("### 📖 Select a Lesson")
        render_lesson_buttons(st.session_state.progress, "beta")
    
    with tabs[1]:
        st.markdown(f"### 🏆 Badges ({len(st.session_state.badges)}/{len(BADGES)})")
        cols = st.columns(4)
        for i,(bid,b) in enumerate(BADGES.items()):
            with cols[i%4]:
                if bid in st.session_state.badges:
                    st.markdown(f'<div class="badge">{b["icon"]} {b["name"]}<br><small>+{b["xp"]} XP</small></div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="badge" style="opacity:0.3">🔒 {b["name"]}<br><small>{b["desc"]}</small></div>', unsafe_allow_html=True)
    
    with tabs[2]:
        render_pomodoro()
    
    with tabs[3]:
        st.markdown("### 💬 Chat")
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])
        msg = st.text_input("Ask anything...", key="beta_chat")
        if st.button("Send", type="primary") and msg and st.session_state.flash_usage < 100:
            st.session_state.messages.append({"role":"user","content":msg})
            st.session_state.flash_usage += 1
            update_usage()
            try:
                genai.configure(api_key=st.secrets['GEMINI_API_KEY'])
                model = genai.GenerativeModel(MODEL_CONFIG["FLASH"])
                with st.spinner("..."):
                    resp = model.generate_content(msg)
                    st.session_state.messages.append({"role":"assistant","content":resp.text})
                st.rerun()
            except Exception as e: st.error(str(e))
    
    st.markdown("---")
    if st.button("🚪 Exit Beta", use_container_width=True):
        st.session_state.beta_mode = False
        st.session_state.authenticated = False
        st.rerun()
    st.stop()
# =============================================================================
# 18. MAIN APP (WITH CONSTELLATION)
# =============================================================================
lvl = get_level_info(st.session_state.total_xp)
c1,c2,c3 = st.columns([2,1,1])
with c1: st.info(f"🎓 {st.session_state.grade} Student | Sorokin AI")
with c2: st.markdown(f"⭐ Lv.{lvl['level']} | {st.session_state.total_xp} XP")
with c3:
    if st.session_state.streak_count > 0:
        st.markdown(f"🔥 {st.session_state.streak_count} day streak!")
    else:
        st.markdown("🔥 Start your streak!")

# Daily goal progress
daily_completed = st.session_state.get('daily_lessons_completed', 0)
daily_goal = st.session_state.get('daily_goal', 3)
col_a, col_b = st.columns([3, 1])
with col_a:
    if daily_completed < daily_goal:
        st.progress(daily_completed / daily_goal)
        st.caption(f"🎯 Daily Goal: {daily_completed}/{daily_goal} lessons")
    else:
        st.progress(1.0)
        st.caption(f"✅ Daily Goal Complete! {daily_completed}/{daily_goal} lessons")
with col_b:
    # Study Pet Display
    pet_emoji, pet_name = get_pet_display()
    st.markdown(f"<div style='text-align:center;font-size:32px'>{pet_emoji}</div>", unsafe_allow_html=True)
    st.caption(f"🐾 {pet_name}")

st.caption(f"⚡ Flash: {100-st.session_state.flash_usage}/100 | 🧠 Ultra: {5-st.session_state.pro_usage}/5")

tabs = st.tabs(["🌌 Learn", "💬 Chat", "📂 History", "⚙️ Settings"])

with tabs[0]:
    st.markdown("### 🌌 Learning Constellation")
    st.caption("Click any lesson to start! Each uses 1 Flash credit.")
    render_constellation(st.session_state.grade, st.session_state.progress)
    st.markdown("### 📖 Select a Lesson")
    render_lesson_buttons(st.session_state.progress, "main")

with tabs[1]:
    st.markdown("### 💬 AI Chat")

    # Chat options
    col1, col2, col3 = st.columns([2,2,1])
    with col1:
        chat_model = st.selectbox("🤖 Model", ["Flash", "Ultra"],
                                  help=f"Flash: {100-st.session_state.flash_usage}/100 | Ultra: {5-st.session_state.pro_usage}/5")
    with col2:
        chat_subject = st.selectbox("📚 Subject", ["General", "Math", "Science", "English", "Code", "History"])
    with col3:
        uploaded_image = st.file_uploader("🖼️", type=['png', 'jpg', 'jpeg'], help="Upload image for vision questions")

    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    msg = st.chat_input("Ask anything...")
    if msg:
        # Check usage limits
        if chat_model == "Flash" and st.session_state.flash_usage >= 100:
            st.error("⚠️ Flash daily limit reached!")
        elif chat_model == "Ultra" and st.session_state.pro_usage >= 5:
            st.error("⚠️ Ultra daily limit reached!")
        else:
            st.session_state.messages.append({"role":"user","content":msg})

            # Update usage
            if chat_model == "Flash":
                st.session_state.flash_usage += 1
            else:
                st.session_state.pro_usage += 1
            update_usage()

            try:
                genai.configure(api_key=st.secrets['GEMINI_API_KEY'])
                model_name = MODEL_CONFIG["FLASH"] if chat_model == "Flash" else MODEL_CONFIG["ULTRA"]

                # Build prompt with subject context
                subject_context = {
                    "Math": "You are a math tutor. Explain concepts clearly with examples.",
                    "Science": "You are a science tutor. Use scientific reasoning and examples.",
                    "English": "You are an English tutor. Focus on grammar, writing, and literature.",
                    "Code": "You are a programming tutor. Provide code examples and explanations.",
                    "History": "You are a history tutor. Provide historical context and analysis.",
                    "General": ""
                }
                context = subject_context.get(chat_subject, "")
                full_prompt = f"{context}\n\n{msg}" if context else msg

                # Handle image if uploaded
                if uploaded_image:
                    image = Image.open(uploaded_image)
                    model = genai.GenerativeModel(model_name)
                    with st.chat_message("assistant"):
                        with st.spinner("Analyzing image..."):
                            resp = model.generate_content([full_prompt, image])
                            st.markdown(resp.text)
                            st.session_state.messages.append({"role":"assistant","content":resp.text})
                else:
                    model = genai.GenerativeModel(model_name)
                    with st.chat_message("assistant"):
                        with st.spinner("Thinking..."):
                            resp = model.generate_content(full_prompt)
                            st.markdown(resp.text)
                            st.session_state.messages.append({"role":"assistant","content":resp.text})

                # Generate title for first message
                if len(st.session_state.messages) == 2:  # First user+assistant exchange
                    title = generate_chat_title(msg)
                    update_chat_title(st.session_state.session_id, title)

                st.rerun()
            except Exception as e:
                st.error(f"Error: {str(e)}")

with tabs[2]:
    st.markdown("### 📂 Chat History")

    # Show current chat messages if any
    if st.session_state.messages:
        st.info(f"💬 Current Chat: {len(st.session_state.messages)} messages - Switch to Chat tab to continue or select another chat below")
        with st.expander("Preview Current Chat", expanded=False):
            for m in st.session_state.messages[:5]:  # Show first 5 messages
                with st.chat_message(m["role"]):
                    st.markdown(m["content"][:200] + ("..." if len(m["content"]) > 200 else ""))
            if len(st.session_state.messages) > 5:
                st.caption(f"... and {len(st.session_state.messages) - 5} more messages")

    conn = get_db()
    if conn:
        cur = conn.cursor(dictionary=True)
        cur.execute(f"USE {st.secrets['DB_NAME']};")

        if st.button("➕ New Chat", type="primary"):
            # Delete current chat if it's empty
            if len(st.session_state.messages) == 0 and st.session_state.get('session_id'):
                delete_empty_chats(st.session_state.user_id, st.session_state.session_id)

            sid = f"S_{uuid.uuid4().hex[:4]}"
            st.session_state.session_id = sid
            st.session_state.messages = []
            cur.execute("UPDATE Users SET session_id=%s WHERE user_id=%s", (sid, st.session_state.user_id))
            cur.execute("INSERT INTO ChatLogs (session_id,user_id,title,messages) VALUES (%s,%s,'New','[]')", (sid, st.session_state.user_id))
            conn.commit()
            st.success("✅ New chat created! Go to Chat tab to start.")
            st.rerun()

        cur.execute("SELECT * FROM ChatLogs WHERE user_id=%s ORDER BY timestamp DESC LIMIT 20", (st.session_state.user_id,))
        for row in cur.fetchall():
            is_current = row['session_id'] == st.session_state.get('session_id')
            btn_label = f"{'📌' if is_current else '📄'} {row['title'][:30]}"
            if st.button(btn_label, key=f"h_{row['session_id']}", use_container_width=True, type="secondary" if is_current else "primary"):
                # Delete current chat if it's empty before switching
                if len(st.session_state.messages) == 0 and st.session_state.get('session_id'):
                    delete_empty_chats(st.session_state.user_id, st.session_state.session_id)

                st.session_state.session_id = row['session_id']
                st.session_state.messages = json.loads(row['messages']) if row['messages'] else []
                st.success(f"✅ Loaded chat: {row['title'][:30]} - Go to Chat tab to continue")
                st.rerun()
        cur.close()
        conn.close()

with tabs[3]:
    st.markdown("### ⚙️ Settings")
    
    new_grade = st.selectbox("Grade Level", GRADES, index=GRADES.index(st.session_state.grade))
    if new_grade != st.session_state.grade:
        st.session_state.grade = new_grade
        conn = get_db()
        if conn:
            cur = conn.cursor()
            cur.execute(f"USE {st.secrets['DB_NAME']};")
            cur.execute("UPDATE Users SET grade=%s WHERE user_id=%s", (new_grade, st.session_state.user_id))
            conn.commit()
            cur.close()
            conn.close()
        st.rerun()
    
    new_theme = st.selectbox("Theme", list(THEMES.keys()), index=list(THEMES.keys()).index(st.session_state.theme))
    if new_theme != st.session_state.theme:
        st.session_state.theme = new_theme
        conn = get_db()
        if conn:
            cur = conn.cursor()
            cur.execute(f"USE {st.secrets['DB_NAME']};")
            cur.execute("UPDATE Users SET theme=%s WHERE user_id=%s", (new_theme, st.session_state.user_id))
            conn.commit()
            cur.close()
            conn.close()
        st.rerun()
    
    st.markdown("---")
    sounds_toggle = st.toggle("🔊 Sound Effects", value=st.session_state.get('sounds_enabled', True))
    if sounds_toggle != st.session_state.sounds_enabled:
        st.session_state.sounds_enabled = sounds_toggle
        st.rerun()

    st.markdown("---")
    new_goal = st.slider("🎯 Daily Lesson Goal", min_value=1, max_value=10, value=st.session_state.get('daily_goal', 3))
    if new_goal != st.session_state.daily_goal:
        st.session_state.daily_goal = new_goal
        conn = get_db()
        if conn:
            cur = conn.cursor()
            cur.execute(f"USE {st.secrets['DB_NAME']};")
            cur.execute("UPDATE Users SET daily_goal=%s WHERE user_id=%s", (new_goal, st.session_state.user_id))
            conn.commit()
            cur.close()
            conn.close()
        st.rerun()

    st.markdown("---")
    st.markdown(f"**Your Stats:**")
    st.markdown(f"- Level: {lvl['level']} ({lvl['name']})")
    st.markdown(f"- Total XP: {st.session_state.total_xp}")
    st.markdown(f"- Badges: {len(st.session_state.badges)}/{len(BADGES)}")
    st.markdown(f"- Lessons Done: {len([k for k,v in st.session_state.progress.items() if v=='completed'])}")

    st.markdown("---")
    if st.button("🚪 Log Out", use_container_width=True):
        # Clean up empty chats before logout
        if len(st.session_state.messages) == 0 and st.session_state.get('session_id'):
            delete_empty_chats(st.session_state.user_id, st.session_state.session_id)
        st.session_state.authenticated = False
        st.rerun()
