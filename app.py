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
import pandas as pd
import altair as alt

# =============================================================================
# 0. MODEL CONFIGURATION
# =============================================================================
MODEL_CONFIG = {
    "FLASH": "gemini-2.0-flash-exp",
    "ULTRA": "gemini-exp-1206"
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
# 2. VISITOR TRACKING
# =============================================================================
if 'visit_counted' not in st.session_state:
    try:
        requests.get(
            "https://script.google.com/macros/s/AKfycbyY3GUNUMJGxIufUNkmnncdvMklbQdr6s_VDZvsJZj-BnTcEW-7-7pNlAN8EchosAdCNw/exec",
            timeout=1
        )
        st.session_state.visit_counted = True
    except Exception:
        pass

# =============================================================================
# 3. ADVANCED CSS STYLING
# =============================================================================
st.markdown("""<style>
    /* Main Background */
    .stApp { background-color: #1a2a3a !important; }

    /* Typography */
    h1, h2, h3, h4, h5, h6, p, label, span, div, li {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }

    /* Popovers */
    div[data-baseweb="popover"] {
        background-color: #ffffff !important;
        border: 1px solid #dcdcdc !important;
        border-radius: 12px !important;
    }
    div[data-baseweb="popover"] > div {
        background-color: #ffffff !important;
    }
    div[data-baseweb="popover"] * {
        color: black !important;
        -webkit-text-fill-color: black !important;
    }

    /* Select Boxes */
    div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        border-radius: 8px !important;
    }
    div[data-baseweb="select"] * {
        color: #1a2a3a !important;
        -webkit-text-fill-color: #1a2a3a !important;
        background-color: transparent !important;
    }
    div[data-baseweb="select"] svg {
        fill: #1a2a3a !important;
    }
    ul[data-baseweb="menu"] {
        background-color: #ffffff !important;
    }
    li[data-baseweb="option"] {
        background-color: #ffffff !important;
        color: #1a2a3a !important;
    }
    li[data-baseweb="option"]:hover {
        background-color: #f0f2f6 !important;
    }

    /* Input Fields */
    .stTextInput input {
        background-color: #ffffff !important;
        color: #1a2a3a !important;
        -webkit-text-fill-color: #1a2a3a !important;
        border-radius: 12px 0px 0px 12px !important;
        height: 50px !important;
        padding-left: 15px !important;
    }

    /* Buttons */
    button[kind="secondaryFormSubmit"] {
        background-color: #f1c40f !important;
        border: 1px solid #f1c40f !important;
        border-radius: 0px 12px 12px 0px !important;
        height: 50px !important;
        width: 100% !important;
        font-weight: bold !important;
    }

    /* Internal Buttons */
    div[data-baseweb="popover"] button {
        background-color: #2980b9 !important;
        border: none !important;
        border-radius: 8px !important;
        margin: 5px 0 !important;
        height: 2.5em !important;
    }
    div[data-baseweb="popover"] button * {
        color: white !important;
        -webkit-text-fill-color: white !important;
    }

    /* Fixed Footer (Chat Input) */
    div[data-testid="stBottom"] {
        position: fixed !important;
        bottom: 0 !important;
        left: 0 !important;
        right: 0 !important;
        background-color: #1a2a3a !important;
        padding: 15px !important;
        border-top: 1px solid #4a5568 !important;
        z-index: 999999 !important;
    }

    /* CLEAN UI */
    header { visibility: hidden !important; }
    footer { visibility: hidden !important; }

    /* Mobile Toggle Fix */
    [data-testid="collapsedControl"] {
        position: fixed !important;
        top: 15px !important;
        left: 15px !important;
        z-index: 10000000 !important;
        background-color: #ffffff !important;
        border: 2px solid #f1c40f !important;
        border-radius: 8px !important;
        width: 45px !important;
        height: 45px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    [data-testid="collapsedControl"] svg {
        fill: #1a2a3a !important;
    }
</style>""", unsafe_allow_html=True)

# =============================================================================
# 4. DATABASE CONNECTION
# =============================================================================
def get_db_connection():
    try:
        if os.path.exists("/etc/ssl/certs/ca-certificates.crt"):
            ssl_args = {
                "ssl_verify_cert": True,
                "ssl_ca": "/etc/ssl/certs/ca-certificates.crt"
            }
            use_pure_mode = False 
        else:
            ssl_args = {
                "ssl_verify_cert": False
            }
            use_pure_mode = True 
            
        conn = mysql.connector.connect(
            host=st.secrets["DB_HOST"],
            port=4000,
            user=st.secrets["DB_USER"],
            password=st.secrets["DB_PASSWORD"],
            database=st.secrets["DB_NAME"],
            connection_timeout=10,
            use_pure=use_pure_mode,
            **ssl_args
        )
        return conn
    except Exception as e:
        st.error(f"FATAL DATABASE ERROR: {e}")
        st.stop()

def check_and_create_tables():
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            db_name = st.secrets["DB_NAME"]
            cursor.execute(f"USE {db_name};")

            cursor.execute("""CREATE TABLE IF NOT EXISTS Users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                hashed_password VARCHAR(255) NOT NULL,
                grade VARCHAR(50),
                subject VARCHAR(50) DEFAULT 'Gen',
                flash_usage INT DEFAULT 0,
                pro_usage INT DEFAULT 0,
                user_id VARCHAR(255) UNIQUE NOT NULL,
                session_id VARCHAR(255),
                last_active_date VARCHAR(20),
                ai_level VARCHAR(50) DEFAULT 'Grade-Level',
                total_xp INT DEFAULT 0,
                current_level INT DEFAULT 1,
                streak_days INT DEFAULT 0
            );""")

            cursor.execute("""CREATE TABLE IF NOT EXISTS ChatLogs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                session_id VARCHAR(255) NOT NULL,
                user_id VARCHAR(255) NOT NULL,
                title VARCHAR(255),
                messages JSON,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );""")

            cursor.execute("""CREATE TABLE IF NOT EXISTS LearningPaths (
                id INT AUTO_INCREMENT PRIMARY KEY,
                subject VARCHAR(255) NOT NULL,
                course_title VARCHAR(255) NOT NULL,
                grade_level VARCHAR(255) NOT NULL,
                total_lessons INT NOT NULL,
                description TEXT
            );""")

            cursor.execute("""CREATE TABLE IF NOT EXISTS UserPathProgress (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL,
                path_id INT NOT NULL,
                current_lesson INT DEFAULT 1,
                completed_lessons JSON,
                UNIQUE(user_id, path_id),
                FOREIGN KEY (path_id) REFERENCES LearningPaths(id)
            );""")

            # NEW: Lesson Progress table for Knowledge Tree
            cursor.execute("""CREATE TABLE IF NOT EXISTS LessonProgress (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL,
                lesson_id VARCHAR(100) NOT NULL,
                status VARCHAR(50) DEFAULT 'locked',
                started_at TIMESTAMP NULL,
                completed_at TIMESTAMP NULL,
                xp_earned INT DEFAULT 0,
                UNIQUE(user_id, lesson_id)
            );""")

            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            st.error(f"DB Init Error: {e}")

check_and_create_tables()

# =============================================================================
# 5. SYLLABUS DATA (EXPANDED)
# =============================================================================
COURSE_SYLLABI = {
    "Algebra I": [
        {"title": "1. Variables & Expressions", "desc": "Understanding symbols, evaluating algebraic expressions."},
        {"title": "2. Solving Linear Equations", "desc": "Balancing equations, solving for X, multi-step equations."},
        {"title": "3. Inequalities", "desc": "Graphing inequalities on a number line, compound inequalities."},
        {"title": "4. Intro to Functions", "desc": "Domain, range, function notation f(x)."},
        {"title": "5. Slope & Intercepts", "desc": "Rate of change, y=mx+b, graphing lines."},
        {"title": "6. Systems of Equations", "desc": "Substitution, elimination, graphing systems."},
        {"title": "7. Exponents", "desc": "Laws of exponents, scientific notation."},
        {"title": "8. Polynomials", "desc": "Adding, subtracting, and multiplying polynomials."},
        {"title": "9. Factoring", "desc": "GCF, difference of squares, trinomials."},
        {"title": "10. Quadratics", "desc": "Quadratic formula, parabolas, vertex form."},
        {"title": "11. Statistics", "desc": "Mean, median, mode, box plots, standard deviation."},
        {"title": "12. Final Exam", "desc": "Comprehensive review of Algebra I concepts."}
    ],
    "Geometry": [
        {"title": "1. Points & Planes", "desc": "Foundations of Euclidean geometry, rays, segments."},
        {"title": "2. Logical Proofs", "desc": "Inductive vs deductive reasoning, two-column proofs."},
        {"title": "3. Perpendicular Lines", "desc": "Transversals, parallel lines, angle pairs."},
        {"title": "4. Congruent Triangles", "desc": "SSS, SAS, ASA, AAS, HL postulates."},
        {"title": "5. Triangle Relationships", "desc": "Bisectors, medians, altitudes, midsegments."},
        {"title": "6. Polygons", "desc": "Sum of interior angles, parallelograms, trapezoids."},
        {"title": "7. Similarity", "desc": "Ratios, proportions, similar triangles."},
        {"title": "8. Right Triangles", "desc": "Pythagorean theorem, special right triangles."},
        {"title": "9. Circles", "desc": "Tangents, arcs, chords, inscribed angles."},
        {"title": "10. Area", "desc": "Area of polygons and circles."},
        {"title": "11. Volume", "desc": "Prisms, cylinders, pyramids, cones, spheres."},
        {"title": "12. Transformations", "desc": "Reflections, rotations, translations, dilations."},
        {"title": "13. Adv. Circles", "desc": "Equation of a circle, secants."},
        {"title": "14. Final Exam", "desc": "Comprehensive review of Geometry concepts."}
    ],
    "Algebra II": [
        {"title": "1. Linear Review", "desc": "Absolute value equations, piecewise functions."},
        {"title": "2. Quadratic Functions", "desc": "Complex numbers, completing the square."},
        {"title": "3. Complex Numbers", "desc": "Operations with imaginary numbers."},
        {"title": "4. Polynomials", "desc": "Synthetic division, remainder theorem, end behavior."},
        {"title": "5. Radicals", "desc": "Square roots, cube roots, rational exponents."},
        {"title": "6. Exponentials", "desc": "Growth and decay models."},
        {"title": "7. Logarithms", "desc": "Properties of logs, solving logarithmic equations."},
        {"title": "8. Rational Functions", "desc": "Vertical and horizontal asymptotes."},
        {"title": "9. Sequences", "desc": "Arithmetic and geometric sequences and series."},
        {"title": "10. Conics", "desc": "Parabolas, circles, ellipses, hyperbolas."},
        {"title": "11. Probability", "desc": "Permutations, combinations, binomial probability."},
        {"title": "12. Trig Ratios", "desc": "SOH CAH TOA, unit circle basics."},
        {"title": "13. Trig Graphs", "desc": "Sine, cosine, tangent waves."},
        {"title": "14. Identities", "desc": "Pythagorean identities, sum and difference formulas."},
        {"title": "15. Final Exam", "desc": "Comprehensive review of Algebra II."}
    ],
    "Pre-Calculus": [
        {"title": "1. Graphs", "desc": "Analyzing 12 basic parent functions."},
        {"title": "2. Polynomials", "desc": "Real and complex zeros, fundamental theorem of algebra."},
        {"title": "3. Exponentials", "desc": "Logistic growth models."},
        {"title": "4. Trig Functions", "desc": "Radian measure, unit circle in depth."},
        {"title": "5. Analytic Trigonometry", "desc": "Proving identities, solving trig equations."},
        {"title": "6. Applications", "desc": "Law of Sines, Law of Cosines."},
        {"title": "7. Matrices", "desc": "Operations, determinants, inverses."},
        {"title": "8. Conics", "desc": "Rotated conics, parametric definitions."},
        {"title": "9. Discrete Math", "desc": "Induction, binomial theorem."},
        {"title": "10. Limits", "desc": "Intuitive definition, one-sided limits."},
        {"title": "11. Derivatives Intro", "desc": "Tangent lines, rates of change."},
        {"title": "12. Vectors", "desc": "Dot product, cross product, projection."},
        {"title": "13. Polar Coords", "desc": "Graphing polar equations."},
        {"title": "14. Parametrics", "desc": "Motion in a plane."},
        {"title": "15. 3D Space", "desc": "Coordinates in 3 dimensions."},
        {"title": "16. Final Exam", "desc": "Review for Calculus readiness."}
    ],
    "Calculus I": [
        {"title": "1. Limits", "desc": "Limit laws, sandwich theorem, continuity."},
        {"title": "2. Continuity", "desc": "IVT, types of discontinuities."},
        {"title": "3. Derivatives", "desc": "Definition as a limit."},
        {"title": "4. Diff Rules", "desc": "Power, product, quotient rules."},
        {"title": "5. Chain Rule", "desc": "Composite functions."},
        {"title": "6. Implicit Diff", "desc": "Finding dy/dx without solving for y."},
        {"title": "7. Applications", "desc": "Tangent line approximation."},
        {"title": "8. Optimization", "desc": "Maximizing volume, minimizing cost."},
        {"title": "9. Related Rates", "desc": "Time-dependent rates of change."},
        {"title": "10. Antiderivatives", "desc": "Indefinite integrals."},
        {"title": "11. Riemann Sums", "desc": "Area under a curve estimation."},
        {"title": "12. Definite Integrals", "desc": "Exact area accumulation."},
        {"title": "13. Fund. Thm of Calc", "desc": "Connecting derivatives and integrals."},
        {"title": "14. Substitution", "desc": "u-substitution technique."},
        {"title": "15. Area", "desc": "Area between two curves."},
        {"title": "16. Volume", "desc": "Disk and washer methods."},
        {"title": "17. Diff Eq", "desc": "Separation of variables."},
        {"title": "18. Final Exam", "desc": "Comprehensive Calculus I review."}
    ],
    "Biology": [
        {"title": "1. Science of Bio", "desc": "Scientific method, characteristics of life."},
        {"title": "2. Chemistry of Life", "desc": "Macromolecules: carbs, lipids, proteins, nucleic acids."},
        {"title": "3. Cells", "desc": "Prokaryotes vs Eukaryotes, organelles."},
        {"title": "4. Photosynthesis", "desc": "Light reactions, Calvin cycle."},
        {"title": "5. Respiration", "desc": "Glycolysis, Krebs cycle, ETC."},
        {"title": "6. Mitosis", "desc": "Cell cycle, somatic cell division."},
        {"title": "7. Meiosis", "desc": "Gamete formation, genetic variation."},
        {"title": "8. Genetics", "desc": "Punnett squares, Mendel's laws."},
        {"title": "9. DNA", "desc": "Replication, transcription, translation."},
        {"title": "10. Evolution", "desc": "Natural selection, evidence for evolution."},
        {"title": "11. Ecology", "desc": "Ecosystems, food webs, trophic levels."},
        {"title": "12. Classification", "desc": "Taxonomy, phylogeny."},
        {"title": "13. Humans", "desc": "Organ systems overview."},
        {"title": "14. Final Exam", "desc": "Biology comprehensive review."}
    ],
    "Chemistry": [
        {"title": "1. Matter", "desc": "States of matter, physical vs chemical changes."},
        {"title": "2. Atoms", "desc": "Protons, neutrons, electrons, isotopes."},
        {"title": "3. Periodic Table", "desc": "Trends: electronegativity, radius, ionization energy."},
        {"title": "4. Bonding", "desc": "Ionic vs covalent, Lewis structures."},
        {"title": "5. Naming", "desc": "IUPAC nomenclature."},
        {"title": "6. The Mole", "desc": "Avogadro's number, molar mass."},
        {"title": "7. Reactions", "desc": "Balancing equations, types of reactions."},
        {"title": "8. Stoichiometry", "desc": "Limiting reactants, percent yield."},
        {"title": "9. States", "desc": "IMF, phase diagrams."},
        {"title": "10. Gases", "desc": "Ideal gas law PV=nRT."},
        {"title": "11. Solutions", "desc": "Molarity, molality, solubility."},
        {"title": "12. Thermochem", "desc": "Enthalpy, entropy, Gibbs free energy."},
        {"title": "13. Kinetics", "desc": "Rate laws, collision theory."},
        {"title": "14. Acids/Bases", "desc": "pH, pOH, titrations, buffers."},
        {"title": "15. Redox", "desc": "Oxidation numbers, galvanic cells."},
        {"title": "16. Nuclear", "desc": "Alpha, beta, gamma decay."}
    ],
    "Physics": [
        {"title": "1. 1D Kinematics", "desc": "Displacement, velocity, acceleration."},
        {"title": "2. Vectors", "desc": "Vector addition, components."},
        {"title": "3. 2D Kinematics", "desc": "Projectile motion."},
        {"title": "4. Newton's Laws", "desc": "F=ma, inertia, action-reaction."},
        {"title": "5. Friction", "desc": "Static vs kinetic friction."},
        {"title": "6. Work & Energy", "desc": "KE, PE, conservation of energy."},
        {"title": "7. Momentum", "desc": "Impulse, elastic vs inelastic collisions."},
        {"title": "8. Circular Motion", "desc": "Centripetal force, gravity."},
        {"title": "9. Rotation", "desc": "Torque, moment of inertia."},
        {"title": "10. Equilibrium", "desc": "Statics, sum of forces/torques = 0."},
        {"title": "11. Fluids", "desc": "Buoyancy, Bernoulli's principle."},
        {"title": "12. Thermo", "desc": "Heat transfer, laws of thermodynamics."},
        {"title": "13. Waves", "desc": "Frequency, wavelength, Doppler effect."},
        {"title": "14. Sound", "desc": "Resonance, harmonics."},
        {"title": "15. Light", "desc": "Reflection, refraction, optics."}
    ],
    "Intro to Python": [
        {"title": "1. Variables", "desc": "Strings, integers, floats."},
        {"title": "2. Types", "desc": "Type casting, dynamic typing."},
        {"title": "3. If/Else", "desc": "Booleans, logic gates."},
        {"title": "4. Loops", "desc": "For loops, while loops, break/continue."},
        {"title": "5. Functions", "desc": "Def, arguments, return values."},
        {"title": "6. Lists", "desc": "Indexing, slicing, appending."},
        {"title": "7. Dictionaries", "desc": "Key-value pairs."},
        {"title": "8. Files", "desc": "Reading and writing txt/csv."},
        {"title": "9. Libraries", "desc": "Importing math, random, time."},
        {"title": "10. Project", "desc": "Building a simple calculator or game."}
    ]
}

def sync_learning_paths():
    if 'paths_synced' in st.session_state:
        return
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute(f"USE {st.secrets['DB_NAME']};")

        paths = [
            ("Math", "Algebra I", "9th", 12, "Linear equations"),
            ("Math", "Geometry", "10th", 14, "Proofs & Shapes"),
            ("Math", "Algebra II", "11th", 15, "Quadratics"),
            ("Math", "Pre-Calculus", "12th", 16, "Trig & Limits"),
            ("Math", "Calculus I", "College", 18, "Derivatives"),
            ("Science", "Biology", "9th-10th", 14, "Cells & Life"),
            ("Science", "Chemistry", "11th", 16, "Atoms & Matter"),
            ("Science", "Physics", "12th", 15, "Forces & Motion"),
            ("Computer Science", "Intro to Python", "9th-College", 10, "Coding Basics")
        ]

        for p in paths:
            cursor.execute("SELECT id FROM LearningPaths WHERE course_title = %s", (p[1],))
            if not cursor.fetchone():
                cursor.execute("INSERT INTO LearningPaths (subject, course_title, grade_level, total_lessons, description) VALUES (%s,%s,%s,%s,%s)", p)
                conn.commit()
        cursor.close()
        conn.close()
        st.session_state.paths_synced = True

sync_learning_paths()

# =============================================================================
# 6. KNOWLEDGE TREE COMPONENT (NEW!)
# =============================================================================
def render_knowledge_tree(user_id, grade, conn):
    """Render the full-screen Knowledge Tree visualization"""
    
    # Get user's lesson progress from database
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM LessonProgress WHERE user_id = %s", (user_id,))
    progress_rows = cursor.fetchall()
    cursor.close()
    
    # Convert to dict for easy lookup
    user_progress = {}
    for row in progress_rows:
        user_progress[row['lesson_id']] = row['status']
    
    # Convert progress to JSON for JavaScript
    progress_json = json.dumps(user_progress)
    
    # The full-screen D3.js Knowledge Tree HTML
    tree_html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <script src="https://d3js.org/d3.v7.min.js"></script>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                background: #1a2a3a;
                overflow: hidden;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }}
            
            #tree-container {{
                width: 100vw;
                height: 100vh;
                position: relative;
            }}
            
            svg {{
                width: 100%;
                height: 100%;
            }}
            
            /* Close Button */
            .close-btn {{
                position: fixed;
                top: 20px;
                right: 20px;
                width: 50px;
                height: 50px;
                background: rgba(255, 255, 255, 0.1);
                border: 2px solid #ffffff;
                border-radius: 50%;
                color: #ffffff;
                font-size: 24px;
                cursor: pointer;
                z-index: 10000;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.3s ease;
            }}
            
            .close-btn:hover {{
                background: #e74c3c;
                border-color: #e74c3c;
                transform: scale(1.1);
            }}
            
            /* Stats Panel */
            .stats-panel {{
                position: fixed;
                bottom: 20px;
                left: 20px;
                background: rgba(0, 0, 0, 0.7);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 12px;
                padding: 15px 20px;
                color: white;
                z-index: 9999;
            }}
            
            .stats-panel h3 {{
                margin-bottom: 10px;
                color: #f1c40f;
            }}
            
            .stat-row {{
                display: flex;
                justify-content: space-between;
                margin: 5px 0;
            }}
            
            /* Legend */
            .legend {{
                position: fixed;
                top: 20px;
                left: 20px;
                background: rgba(0, 0, 0, 0.7);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 12px;
                padding: 15px;
                color: white;
                z-index: 9999;
                font-size: 12px;
            }}
            
            .legend-item {{
                display: flex;
                align-items: center;
                margin: 5px 0;
            }}
            
            .legend-dot {{
                width: 12px;
                height: 12px;
                border-radius: 50%;
                margin-right: 8px;
            }}
            
            /* Tooltip */
            .tooltip {{
                position: absolute;
                background: rgba(0, 0, 0, 0.9);
                border: 1px solid #f1c40f;
                border-radius: 8px;
                padding: 10px 15px;
                color: white;
                font-size: 14px;
                pointer-events: none;
                opacity: 0;
                transition: opacity 0.2s;
                z-index: 10001;
                max-width: 250px;
            }}
            
            .tooltip.visible {{
                opacity: 1;
            }}
            
            .tooltip h4 {{
                color: #f1c40f;
                margin-bottom: 5px;
            }}
            
            .tooltip p {{
                color: #ccc;
                font-size: 12px;
            }}
            
            /* Node styles */
            .node-center {{
                filter: drop-shadow(0 0 20px rgba(241, 196, 15, 0.8));
            }}
            
            .node-subject {{
                filter: drop-shadow(0 0 15px rgba(255, 255, 255, 0.3));
            }}
            
            .node-course {{
                cursor: pointer;
                transition: transform 0.2s;
            }}
            
            .node-lesson {{
                cursor: pointer;
            }}
            
            .node-lesson.locked {{
                opacity: 0.3;
                filter: blur(2px);
                pointer-events: none;
            }}
            
            .node-lesson.available {{
                animation: pulse 2s infinite;
            }}
            
            .node-lesson.completed {{
                filter: drop-shadow(0 0 10px rgba(0, 230, 118, 0.8));
            }}
            
            @keyframes pulse {{
                0%, 100% {{ opacity: 1; }}
                50% {{ opacity: 0.7; }}
            }}
            
            /* Links */
            .link {{
                fill: none;
                stroke: rgba(255, 255, 255, 0.2);
                stroke-width: 2px;
            }}
            
            .link-subject {{
                stroke: rgba(255, 255, 255, 0.4);
                stroke-width: 3px;
            }}
            
            /* Fog overlay for locked content */
            .fog-overlay {{
                fill: url(#fog-gradient);
                pointer-events: none;
            }}
            
            /* Instructions */
            .instructions {{
                position: fixed;
                bottom: 20px;
                right: 20px;
                background: rgba(0, 0, 0, 0.7);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 12px;
                padding: 15px;
                color: white;
                z-index: 9999;
                font-size: 12px;
            }}
        </style>
    </head>
    <body>
        <div id="tree-container"></div>
        
        <button class="close-btn" id="close-btn">✕</button>
        
        <div class="legend">
            <div class="legend-item"><div class="legend-dot" style="background: #f1c40f;"></div> You</div>
            <div class="legend-item"><div class="legend-dot" style="background: #3498db;"></div> Math</div>
            <div class="legend-item"><div class="legend-dot" style="background: #27ae60;"></div> Science</div>
            <div class="legend-item"><div class="legend-dot" style="background: #9b59b6;"></div> CS</div>
            <div class="legend-item"><div class="legend-dot" style="background: #00E676;"></div> Completed</div>
            <div class="legend-item"><div class="legend-dot" style="background: #37474F;"></div> Locked</div>
        </div>
        
        <div class="stats-panel">
            <h3>🎓 {grade} Student</h3>
            <div class="stat-row"><span>Progress:</span><span id="progress-pct">0%</span></div>
            <div class="stat-row"><span>Lessons:</span><span id="lessons-done">0/0</span></div>
        </div>
        
        <div class="instructions">
            <strong>Controls:</strong><br>
            🖱️ Scroll to zoom<br>
            ✋ Drag to pan<br>
            👆 Click lesson to start
        </div>
        
        <div class="tooltip" id="tooltip"></div>
        
        <script>
            // User progress from database
            const userProgress = {progress_json};
            const userGrade = "{grade}";
            
            // Tree data structure
            const treeData = {{
                id: "center",
                name: "YOU",
                grade: userGrade,
                type: "center",
                children: [
                    {{
                        id: "math",
                        name: "Mathematics",
                        icon: "🧮",
                        type: "subject",
                        color: "#3498db",
                        children: [
                            {{ id: "algebra1", name: "Algebra I", type: "course", lessons: 12 }},
                            {{ id: "geometry", name: "Geometry", type: "course", lessons: 14 }},
                            {{ id: "algebra2", name: "Algebra II", type: "course", lessons: 15 }},
                            {{ id: "precalc", name: "Pre-Calculus", type: "course", lessons: 16 }},
                            {{ id: "calc1", name: "Calculus I", type: "course", lessons: 18 }}
                        ]
                    }},
                    {{
                        id: "science",
                        name: "Science",
                        icon: "🧬",
                        type: "subject",
                        color: "#27ae60",
                        children: [
                            {{ id: "biology", name: "Biology", type: "course", lessons: 14 }},
                            {{ id: "chemistry", name: "Chemistry", type: "course", lessons: 16 }},
                            {{ id: "physics", name: "Physics", type: "course", lessons: 15 }}
                        ]
                    }},
                    {{
                        id: "cs",
                        name: "Computer Science",
                        icon: "💻",
                        type: "subject",
                        color: "#9b59b6",
                        children: [
                            {{ id: "python", name: "Intro to Python", type: "course", lessons: 10 }}
                        ]
                    }}
                ]
            }};
            
            // Add lessons to courses
            treeData.children.forEach(subject => {{
                subject.children.forEach(course => {{
                    course.children = [];
                    for (let i = 1; i <= course.lessons; i++) {{
                        const lessonId = `${{course.id}}_L${{i}}`;
                        const isVisible = i <= 3; // First 3 lessons visible
                        const status = userProgress[lessonId] || (isVisible ? 'available' : 'locked');
                        course.children.push({{
                            id: lessonId,
                            name: `Lesson ${{i}}`,
                            type: "lesson",
                            lessonNum: i,
                            status: status,
                            visible: isVisible || status !== 'locked',
                            courseId: course.id,
                            courseName: course.name
                        }});
                    }}
                }});
            }});
            
            // Setup SVG
            const width = window.innerWidth;
            const height = window.innerHeight;
            
            const svg = d3.select("#tree-container")
                .append("svg")
                .attr("width", width)
                .attr("height", height);
            
            // Add fog gradient
            const defs = svg.append("defs");
            const fogGradient = defs.append("radialGradient")
                .attr("id", "fog-gradient")
                .attr("cx", "50%")
                .attr("cy", "50%")
                .attr("r", "50%");
            
            fogGradient.append("stop")
                .attr("offset", "60%")
                .attr("stop-color", "transparent");
            
            fogGradient.append("stop")
                .attr("offset", "100%")
                .attr("stop-color", "#1a2a3a")
                .attr("stop-opacity", "0.9");
            
            // Main group for zoom/pan
            const g = svg.append("g");
            
            // Zoom behavior
            const zoom = d3.zoom()
                .scaleExtent([0.3, 3])
                .on("zoom", (event) => {{
                    g.attr("transform", event.transform);
                }});
            
            svg.call(zoom);
            
            // Initial transform to center
            svg.call(zoom.transform, d3.zoomIdentity.translate(width/2, height/2).scale(0.8));
            
            // Create hierarchical layout
            const root = d3.hierarchy(treeData);
            
            // Custom radial layout
            const radius = Math.min(width, height) / 2.5;
            
            // Position nodes
            function positionNodes(node, angle = 0, level = 0, parentAngle = 0, angleSpan = Math.PI * 2) {{
                if (level === 0) {{
                    node.x = 0;
                    node.y = 0;
                }} else {{
                    const r = level * 150;
                    node.x = Math.cos(angle) * r;
                    node.y = Math.sin(angle) * r;
                }}
                
                if (node.children) {{
                    const childCount = node.children.length;
                    const childSpan = level === 0 ? Math.PI * 2 : angleSpan * 0.8;
                    const startAngle = level === 0 ? 0 : angle - childSpan / 2;
                    
                    node.children.forEach((child, i) => {{
                        const childAngle = startAngle + (childSpan / (childCount)) * (i + 0.5);
                        positionNodes(child, childAngle, level + 1, angle, childSpan / childCount);
                    }});
                }}
            }}
            
            positionNodes(root);
            
            // Draw links
            const links = root.links();
            
            g.selectAll(".link")
                .data(links)
                .enter()
                .append("path")
                .attr("class", d => `link ${{d.source.data.type === 'center' ? 'link-subject' : ''}}`)
                .attr("d", d => {{
                    return `M${{d.source.x}},${{d.source.y}} Q${{(d.source.x + d.target.x) / 2}},${{(d.source.y + d.target.y) / 2}} ${{d.target.x}},${{d.target.y}}`;
                }})
                .style("stroke", d => {{
                    if (d.target.data.type === 'lesson' && d.target.data.status === 'locked') {{
                        return 'rgba(255,255,255,0.05)';
                    }}
                    return d.source.data.color || 'rgba(255,255,255,0.2)';
                }});
            
            // Draw nodes
            const nodes = root.descendants();
            
            const nodeGroups = g.selectAll(".node")
                .data(nodes)
                .enter()
                .append("g")
                .attr("class", d => `node node-${{d.data.type}} ${{d.data.status || ''}}`)
                .attr("transform", d => `translate(${{d.x}},${{d.y}})`);
            
            // Node circles
            nodeGroups.append("circle")
                .attr("r", d => {{
                    switch(d.data.type) {{
                        case 'center': return 60;
                        case 'subject': return 45;
                        case 'course': return 30;
                        case 'lesson': return 15;
                        default: return 20;
                    }}
                }})
                .attr("fill", d => {{
                    if (d.data.type === 'center') return '#f1c40f';
                    if (d.data.type === 'subject') return d.data.color;
                    if (d.data.type === 'course') return d.parent.data.color;
                    if (d.data.type === 'lesson') {{
                        if (d.data.status === 'completed') return '#00E676';
                        if (d.data.status === 'available') return d.parent.parent.data.color;
                        return '#37474F';
                    }}
                    return '#fff';
                }})
                .attr("stroke", d => {{
                    if (d.data.type === 'lesson' && d.data.status === 'available') {{
                        return '#fff';
                    }}
                    return 'none';
                }})
                .attr("stroke-width", 2)
                .style("opacity", d => {{
                    if (d.data.type === 'lesson' && d.data.status === 'locked') return 0.3;
                    return 1;
                }})
                .style("filter", d => {{
                    if (d.data.type === 'lesson' && d.data.status === 'locked') return 'blur(2px)';
                    return 'none';
                }});
            
            // Node labels
            nodeGroups.append("text")
                .attr("dy", d => {{
                    if (d.data.type === 'center') return 5;
                    if (d.data.type === 'subject') return -55;
                    if (d.data.type === 'course') return -40;
                    return 30;
                }})
                .attr("text-anchor", "middle")
                .attr("fill", "#fff")
                .attr("font-size", d => {{
                    switch(d.data.type) {{
                        case 'center': return '14px';
                        case 'subject': return '16px';
                        case 'course': return '12px';
                        case 'lesson': return '10px';
                        default: return '12px';
                    }}
                }})
                .attr("font-weight", d => d.data.type === 'subject' ? 'bold' : 'normal')
                .text(d => {{
                    if (d.data.type === 'center') return userGrade;
                    if (d.data.type === 'subject') return d.data.icon + ' ' + d.data.name;
                    if (d.data.type === 'course') return d.data.name;
                    if (d.data.type === 'lesson') {{
                        if (d.data.status === 'locked') return '???';
                        return d.data.lessonNum;
                    }}
                    return d.data.name;
                }})
                .style("opacity", d => {{
                    if (d.data.type === 'lesson' && d.data.status === 'locked') return 0.3;
                    return 1;
                }});
            
            // Center node special label
            nodeGroups.filter(d => d.data.type === 'center')
                .append("text")
                .attr("dy", -70)
                .attr("text-anchor", "middle")
                .attr("fill", "#f1c40f")
                .attr("font-size", "20px")
                .attr("font-weight", "bold")
                .text("🎓 YOU");
            
            // Tooltip
            const tooltip = d3.select("#tooltip");
            
            nodeGroups
                .on("mouseover", (event, d) => {{
                    if (d.data.type === 'lesson' && d.data.status !== 'locked') {{
                        tooltip.classed("visible", true)
                            .style("left", (event.pageX + 15) + "px")
                            .style("top", (event.pageY - 10) + "px")
                            .html(`
                                <h4>${{d.data.courseName}} - Lesson ${{d.data.lessonNum}}</h4>
                                <p>Status: ${{d.data.status}}</p>
                                <p>Click to start learning!</p>
                            `);
                    }} else if (d.data.type === 'course') {{
                        tooltip.classed("visible", true)
                            .style("left", (event.pageX + 15) + "px")
                            .style("top", (event.pageY - 10) + "px")
                            .html(`
                                <h4>${{d.data.name}}</h4>
                                <p>${{d.data.lessons}} lessons</p>
                            `);
                    }}
                }})
                .on("mouseout", () => {{
                    tooltip.classed("visible", false);
                }})
                .on("click", (event, d) => {{
                    if (d.data.type === 'lesson' && d.data.status !== 'locked') {{
                        // Store in sessionStorage for Streamlit to read
                        const lessonData = {{
                            action: 'start_lesson',
                            lessonId: d.data.id,
                            lessonNum: d.data.lessonNum,
                            courseId: d.data.courseId,
                            courseName: d.data.courseName
                        }};
                        sessionStorage.setItem('tree_action', JSON.stringify(lessonData));
                        // Trigger page reload to let Streamlit handle it
                        window.parent.location.reload();
                    }}
                }});
            
            // Calculate stats
            let totalLessons = 0;
            let completedLessons = 0;
            nodes.forEach(n => {{
                if (n.data.type === 'lesson') {{
                    totalLessons++;
                    if (n.data.status === 'completed') completedLessons++;
                }}
            }});
            
            document.getElementById('progress-pct').textContent = Math.round((completedLessons / totalLessons) * 100) + '%';
            document.getElementById('lessons-done').textContent = completedLessons + '/' + totalLessons;
            
            // Close button handler
            document.getElementById('close-btn').addEventListener('click', function() {{
                sessionStorage.setItem('tree_action', JSON.stringify({{action: 'close'}}));
                window.parent.location.reload();
            }});
        </script>
    </body>
    </html>
    '''
    
    # Render the tree full-screen
    components.html(tree_html, height=800, scrolling=False)
    
    # Add a Streamlit close button as backup
    if st.button("← Back to Chat", key="tree_back_btn"):
        st.session_state.tree_view_open = False
        st.rerun()

# =============================================================================
# 7. SESSION STATE INIT
# =============================================================================
if 'authenticated' not in st.session_state: st.session_state.authenticated = False
if 'messages' not in st.session_state: st.session_state.messages = []
if 'user_id' not in st.session_state: st.session_state.user_id = None
if 'current_path' not in st.session_state: st.session_state.current_path = None
if 'current_lesson' not in st.session_state: st.session_state.current_lesson = 1
if 'prompt_to_process' not in st.session_state: st.session_state.prompt_to_process = None
if 'grade' not in st.session_state: st.session_state.grade = "9th"
if 'ai_level' not in st.session_state: st.session_state.ai_level = "Grade-Level"
if 'flash_usage' not in st.session_state: st.session_state.flash_usage = 0
if 'pro_usage' not in st.session_state: st.session_state.pro_usage = 0
if 'session_id' not in st.session_state: st.session_state.session_id = None
if 'main_session_id' not in st.session_state: st.session_state.main_session_id = None
if 'active_model_mode' not in st.session_state: st.session_state.active_model_mode = "⚡ Flash"
if 'global_model_index' not in st.session_state: st.session_state.global_model_index = 0
if 'tree_view_open' not in st.session_state: st.session_state.tree_view_open = False
if 'selected_tree_lesson' not in st.session_state: st.session_state.selected_tree_lesson = None

SUBJECT_OPTIONS = ["📜 History", "🧮 Math", "🧬 Science", "📚 English", "💻 Code", "🧠 General"]
SUBJECT_VALUES = ["History", "Math", "Sci", "Eng", "Code", "Gen"]
MODEL_OPTIONS = ["⚡ Flash", "🧠 Ultra"]
GRADE_OPTIONS = ["9th", "10th", "11th", "12th", "College"]
AI_LEVEL_OPTIONS = ["Simple", "Grade-Level", "Expert"]

# =============================================================================
# 8. AUTHENTICATION
# =============================================================================
if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 6, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.title("🔐 Sorokin Access")
        t1, t2, t3 = st.tabs(["Log In", "Create Account", "Plans"])
        with t1:
            st.markdown("### Welcome Back")
            u = st.text_input("Username", key="l_u")
            p = st.text_input("Password", type="password", key="l_p")
            if st.button("Log In", type="primary", use_container_width=True):
                conn = get_db_connection()
                if conn:
                    cur = conn.cursor(dictionary=True)
                    cur.execute(f"USE {st.secrets['DB_NAME']};")
                    cur.execute("SELECT * FROM Users WHERE username = %s", (u,))
                    res = cur.fetchone()
                    if res and bcrypt.checkpw(p.encode('utf-8'), res['hashed_password'].encode('utf-8')):

                        today_str = datetime.now().strftime("%Y-%m-%d")
                        if res['last_active_date'] != today_str:
                            cur.execute("UPDATE Users SET flash_usage=0, pro_usage=0, last_active_date=%s WHERE user_id=%s", (today_str, res['user_id']))
                            conn.commit()
                            res['flash_usage'] = 0
                            res['pro_usage'] = 0

                        new_sid = f"S_{str(uuid.uuid4())[:4]}"
                        st.session_state.update({
                            "authenticated": True, "user_id": res['user_id'], "grade": res['grade'],
                            "session_id": new_sid, "main_session_id": new_sid,
                            "ai_level": res['ai_level'], "flash_usage": res['flash_usage'],
                            "pro_usage": res['pro_usage'], "messages": []
                        })
                        cur.execute("UPDATE Users SET session_id=%s WHERE user_id=%s", (new_sid, res['user_id']))
                        cur.execute("INSERT INTO ChatLogs (session_id, user_id, title, messages) VALUES (%s, %s, %s, %s)", (new_sid, res['user_id'], "New Session", "[]"))
                        conn.commit()
                        st.rerun()
                    else: st.error("Invalid Credentials")
                    cur.close(); conn.close()
        with t2:
            st.markdown("### New Account")
            nu, np = st.text_input("New User"), st.text_input("New Pass", type="password")
            ng = st.selectbox("Grade", GRADE_OPTIONS)
            if st.button("Register", type="primary", use_container_width=True):
                conn = get_db_connection()
                if conn:
                    cur = conn.cursor()
                    cur.execute(f"USE {st.secrets['DB_NAME']};")
                    try:
                        h = bcrypt.hashpw(np.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                        uid, sid = f"U_{uuid.uuid4().hex[:4]}", f"S_{uuid.uuid4().hex[:4]}"
                        today_str = datetime.now().strftime("%Y-%m-%d")
                        cur.execute("INSERT INTO Users (username,hashed_password,grade,user_id,session_id,last_active_date,flash_usage,pro_usage) VALUES (%s,%s,%s,%s,%s,%s,0,0)", (nu,h,ng,uid,sid,today_str))
                        cur.execute("INSERT INTO ChatLogs (session_id,user_id,title,messages) VALUES (%s,%s,%s,%s)", (sid,uid,"Welcome","[]"))
                        conn.commit()
                        st.success("Created! Login now.")
                    except: st.error("Username taken")
                    cur.close(); conn.close()
    st.stop()

# =============================================================================
# 9. KNOWLEDGE TREE FULL-SCREEN HANDLER (NEW!)
# =============================================================================
if st.session_state.tree_view_open:
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(f"USE {st.secrets['DB_NAME']};")
        
        # Render the full-screen tree
        render_knowledge_tree(
            user_id=st.session_state.user_id,
            grade=st.session_state.grade,
            conn=conn
        )
        
        cursor.close()
        conn.close()
    
    st.stop()  # CRITICAL: Don't render anything else when tree is open

# =============================================================================
# 10. HANDLE LESSON SELECTED FROM TREE (NEW!)
# =============================================================================
if st.session_state.selected_tree_lesson:
    lesson = st.session_state.selected_tree_lesson
    st.session_state.selected_tree_lesson = None
    
    # Map course IDs to full names and get syllabus
    course_map = {
        'algebra1': 'Algebra I',
        'geometry': 'Geometry', 
        'algebra2': 'Algebra II',
        'precalc': 'Pre-Calculus',
        'calc1': 'Calculus I',
        'biology': 'Biology',
        'chemistry': 'Chemistry',
        'physics': 'Physics',
        'python': 'Intro to Python'
    }
    
    course_name = course_map.get(lesson['courseId'], lesson['courseName'])
    lesson_num = lesson['lessonNum']
    
    # Get lesson details from syllabus
    syllabus = COURSE_SYLLABI.get(course_name, [])
    if lesson_num <= len(syllabus):
        lesson_info = syllabus[lesson_num - 1]
        st.session_state.prompt_to_process = f"Teach {course_name} Lesson {lesson_num}: {lesson_info['title']}. {lesson_info['desc']}"
    else:
        st.session_state.prompt_to_process = f"Teach {course_name} Lesson {lesson_num}"

# =============================================================================
# 11. MAIN UI ENGINE
# =============================================================================
conn = get_db_connection()
if conn:
    cursor = conn.cursor(dictionary=True)
    cursor.execute(f"USE {st.secrets['DB_NAME']};")

    # Determine layout
    chat_is_empty = (len(st.session_state.messages) == 0) and (not st.session_state.current_path)

    # --- TOP HEADER ---
    c_top_info, c_top_scroll = st.columns([8, 2])
    with c_top_info:
        if st.session_state.current_path:
            pid = st.session_state.current_path
            cursor.execute("SELECT * FROM LearningPaths WHERE id = %s", (pid,))
            p_data = cursor.fetchone()
            if p_data:
                st.info(f"**Course:** {p_data['course_title']} | **Active Session**")
        else:
            st.info("Sorokin AI - Ready")

    with c_top_scroll:
        st.write("")

    # --- LAYOUT A: NEW CHAT ---
    if chat_is_empty:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.title(f"Welcome, {st.session_state.grade} Student")

        f_rem = max(0, 100 - st.session_state.flash_usage)
        p_rem = max(0, 5 - st.session_state.pro_usage)
        st.caption(f"⚡ Flash: {f_rem}/100 | 🧠 Ultra: {p_rem}/5")

        def submit_top():
            st.session_state.prompt_to_process = st.session_state.top_input
            st.session_state.top_input = ""
            st.session_state.active_model_mode = st.session_state.model_selector_top
            if "Ultra" in st.session_state.model_selector_top:
                st.session_state.global_model_index = 1
            else:
                st.session_state.global_model_index = 0

        with st.form("top_chat", clear_on_submit=False):
            c1, c2 = st.columns([8.5, 1.5])
            c1.text_input("Message", key="top_input", placeholder="Ask Sorokin...", label_visibility="collapsed")
            c2.form_submit_button("🚀", on_click=submit_top)

            c_s, c_m, c_st_t, c_a = st.columns([1, 1, 1, 0.4])
            with c_s: st.selectbox("Sub", SUBJECT_OPTIONS, index=5, label_visibility="collapsed")
            with c_m: st.selectbox("Mod", MODEL_OPTIONS, key="model_selector_top", label_visibility="collapsed")
            with c_st_t:
                with st.popover("⚙️", use_container_width=True):
                    st.markdown("### Settings")
                    st.selectbox("Grade", GRADE_OPTIONS, key="st_gr_t", index=GRADE_OPTIONS.index(st.session_state.grade))
                    st.radio("AI", AI_LEVEL_OPTIONS, key="st_ai_t", index=AI_LEVEL_OPTIONS.index(st.session_state.ai_level))
            with c_a:
                 with st.popover("📸"): st.file_uploader("Img", key="top_up", label_visibility="collapsed")

        # --- REPLACED: Learning Paths expander with Knowledge Tree button ---
        col_h, col_p = st.columns(2)
        with col_h:
            with st.expander("📂 Recent Chats", expanded=False):
                cursor.execute("SELECT * FROM ChatLogs WHERE user_id=%s AND session_id NOT LIKE 'LP_%' ORDER BY timestamp DESC LIMIT 50", (st.session_state.user_id,))
                for row in cursor.fetchall():
                    if st.button(f"📄 {row['title'][:35]}", key=f"top_hist_{row['session_id']}", use_container_width=True):
                        st.session_state.session_id = row['session_id']
                        st.session_state.messages = json.loads(row['messages'])
                        st.rerun()
        with col_p:
            # NEW: Knowledge Tree Button!
            if st.button("🌳 Knowledge Tree", type="primary", use_container_width=True):
                st.session_state.tree_view_open = True
                st.rerun()

    # --- LAYOUT B: ACTIVE CHAT ---
    else:
        st.markdown("<br>", unsafe_allow_html=True)
        for m in st.session_state.messages:
            with st.chat_message(m["role"]):
                if "image_indicator" in m: st.caption("📷 Image Attached")
                st.markdown(m["content"])

        st.markdown('<div style="height: 380px;"></div>', unsafe_allow_html=True)

        with st.container():
            if st.session_state.current_path:
                cursor.execute("SELECT * FROM LearningPaths WHERE id = %s", (st.session_state.current_path,))
                p_data = cursor.fetchone()
                
                if p_data:
                    title = p_data['course_title']
                    total = p_data['total_lessons']
                    curr = st.session_state.current_lesson
                    syl_list = COURSE_SYLLABI.get(title, [])

                    if curr <= len(syl_list):
                        c_info = syl_list[curr-1]
                        t_title = c_info['title']
                        t_desc = c_info['desc']
                    else:
                        t_title = "Complete"; t_desc = "Review"

                    st.caption(f"🎓 **{title}**: {t_title}")

                    # Progress bar
                    bar_data = []
                    total_mins_left = 0
                    completed_count = 0

                    for i in range(1, total+1):
                        l_meta = syl_list[i-1] if i <= len(syl_list) else {"title": f"L{i}", "desc": ""}
                        stat = "Completed" if i < curr else ("Current" if i == curr else "Upcoming")
                        desc_complexity = len(l_meta.get('desc', ''))
                        est_duration = 15 + min(7, int(desc_complexity / 10))

                        if stat == "Completed":
                            color = "#00E676"
                            completed_count += 1
                        elif stat == "Current":
                            color = "#FFD700"
                            total_mins_left += est_duration
                        else:
                            color = "#37474F"
                            total_mins_left += est_duration

                        bar_data.append({
                            "Lesson": i, "Topic": l_meta['title'], "Status": stat,
                            "Color": color, "Value": 1, "Duration": f"{est_duration} min"
                        })

                    percent_done = int((completed_count / total) * 100) if total > 0 else 0
                    time_str = f"{total_mins_left // 60}h {total_mins_left % 60}m" if total_mins_left > 60 else f"{total_mins_left}m"

                    st.markdown(f"""
                    <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 8px;">
                        <span style="font-size: 1.1em; font-weight: 700; color: #00E676;">🚀 {percent_done}% Complete</span>
                        <span style="font-size: 0.95em; font-weight: 600; color: #FFD700;">⏱️ {time_str} Left</span>
                    </div>
                    """, unsafe_allow_html=True)

                    chart = alt.Chart(pd.DataFrame(bar_data)).mark_bar(
                        cornerRadius=12, stroke='transparent', height=45, cursor='pointer'
                    ).encode(
                        x=alt.X('Lesson:O', axis=None),
                        color=alt.Color('Color', scale=None, legend=None),
                        tooltip=['Lesson', 'Topic', 'Status', 'Duration'],
                        order=alt.Order('Lesson', sort='ascending')
                    ).configure_scale(bandPaddingInner=0.25).configure_view(stroke=None).properties(height=65, width='container')
                    st.altair_chart(chart, use_container_width=True)

                    b1, b2, b3 = st.columns([1, 1, 0.5])
                    with b1:
                        if st.button(f"▶ Start Lesson {curr}", key=f"s_{curr}", type="primary", use_container_width=True):
                            st.session_state.prompt_to_process = f"Teach {title} Lesson {curr}: {t_title}. {t_desc}"
                            st.rerun()
                    with b2:
                        if st.button("✔ Next", key=f"c_{curr}", use_container_width=True):
                            cursor.execute("SELECT completed_lessons FROM UserPathProgress WHERE user_id=%s AND path_id=%s", (st.session_state.user_id, st.session_state.current_path))
                            exists = cursor.fetchone()
                            done = json.loads(exists['completed_lessons']) if exists else []
                            if curr not in done:
                                done.append(curr)
                                nxt = curr + 1 if curr < total else curr
                                cursor.execute("INSERT INTO UserPathProgress (user_id, path_id, current_lesson, completed_lessons) VALUES (%s,%s,%s,%s) ON DUPLICATE KEY UPDATE current_lesson=%s, completed_lessons=%s", (st.session_state.user_id, st.session_state.current_path, nxt, json.dumps(done), nxt, json.dumps(done)))
                                conn.commit()
                                st.session_state.current_lesson = nxt
                                st.session_state.messages = []
                                st.rerun()
                    with b3:
                        if st.button("❌"):
                            st.session_state.current_path = None
                            st.session_state.messages = []
                            st.rerun()

            f_rem = max(0, 100 - st.session_state.flash_usage)
            p_rem = max(0, 5 - st.session_state.pro_usage)
            st.caption(f"⚡ Flash: {f_rem}/100 | 🧠 Ultra: {p_rem}/5")

            def submit_bottom():
                st.session_state.prompt_to_process = st.session_state.bot_input
                st.session_state.bot_input = ""
                st.session_state.active_model_mode = st.session_state.model_selector
                if "Ultra" in st.session_state.model_selector:
                    st.session_state.global_model_index = 1
                else:
                    st.session_state.global_model_index = 0

            with st.form("bot_chat", clear_on_submit=False):
                c_in, c_btn = st.columns([8.5, 1.5])
                c_in.text_input("Msg", key="bot_input", placeholder="Ask Sorokin...", label_visibility="collapsed")
                c_btn.form_submit_button("🚀", on_click=submit_bottom)

            c_h, c_t, c_s, c_m, c_st, c_a = st.columns([1, 0.6, 1, 1, 1, 0.4])

            with c_h:
                with st.popover("📂", use_container_width=True):
                    if st.button("➕ New Chat"):
                        nid = f"S_{uuid.uuid4().hex[:4]}"
                        st.session_state.session_id = nid
                        st.session_state.messages = []
                        cursor.execute("UPDATE Users SET session_id=%s WHERE user_id=%s", (nid, st.session_state.user_id))
                        cursor.execute("INSERT INTO ChatLogs (session_id, user_id, title, messages) VALUES (%s,%s,%s,%s)", (nid, st.session_state.user_id, "New Chat", "[]"))
                        conn.commit()
                        st.rerun()
                    st.markdown("---")
                    cursor.execute("SELECT * FROM ChatLogs WHERE user_id=%s AND session_id NOT LIKE 'LP_%' ORDER BY timestamp DESC LIMIT 50", (st.session_state.user_id,))
                    for row in cursor.fetchall():
                        if st.button(f"📄 {row['title'][:30]}", key=row['session_id'], use_container_width=True):
                            st.session_state.session_id = row['session_id']
                            st.session_state.messages = json.loads(row['messages'])
                            st.rerun()
                    if st.button("Log Out"): st.session_state.authenticated = False; st.rerun()
            
            # NEW: Tree button in bottom bar
            with c_t:
                if st.button("🌳", use_container_width=True, help="Knowledge Tree"):
                    st.session_state.tree_view_open = True
                    st.rerun()
                    
            with c_s: st.selectbox("S", SUBJECT_OPTIONS, index=5, label_visibility="collapsed")
            with c_m: st.selectbox("M", MODEL_OPTIONS, key="model_selector", index=st.session_state.global_model_index, label_visibility="collapsed")

            with c_st:
                with st.popover("⚙️", use_container_width=True):
                    st.markdown("### Settings")
                    ng = st.selectbox("Grade", GRADE_OPTIONS, index=GRADE_OPTIONS.index(st.session_state.grade))
                    if ng != st.session_state.grade:
                        cursor.execute("UPDATE Users SET grade=%s WHERE user_id=%s", (ng, st.session_state.user_id))
                        conn.commit()
                        st.session_state.grade = ng
                        st.rerun()
                    nai = st.radio("AI Level", AI_LEVEL_OPTIONS, index=AI_LEVEL_OPTIONS.index(st.session_state.ai_level))
                    if nai != st.session_state.ai_level:
                        cursor.execute("UPDATE Users SET ai_level=%s WHERE user_id=%s", (nai, st.session_state.user_id))
                        conn.commit()
                        st.session_state.ai_level = nai
                        st.rerun()
            with c_a:
                 with st.popover("📸", use_container_width=True):
                     st.file_uploader("Up", key="up_bot")

    # AI PROCESSOR
    if st.session_state.prompt_to_process:
        txt = st.session_state.prompt_to_process
        st.session_state.prompt_to_process = None

        sel_mod = st.session_state.active_model_mode
        is_u = "Ultra" in sel_mod
        lim = 5 if is_u else 100
        cur = st.session_state.pro_usage if is_u else st.session_state.flash_usage

        if cur >= lim:
            st.error(f"Limit reached for {sel_mod}")
        else:
            st.session_state.messages.append({"role": "user", "content": txt})
            genai.configure(api_key=st.secrets['GEMINI_API_KEY'])

            with st.chat_message("assistant"):
                try:
                    m_name = MODEL_CONFIG["ULTRA"] if is_u else MODEL_CONFIG["FLASH"]
                    model = genai.GenerativeModel(m_name)
                    with st.spinner("Thinking..."):
                        u_file = st.session_state.get("top_up") or st.session_state.get("up_bot")
                        if u_file:
                            resp = model.generate_content([txt, Image.open(u_file)])
                        else:
                            resp = model.generate_content(txt)

                        st.markdown(resp.text)
                    st.session_state.messages.append({"role": "assistant", "content": resp.text})

                    if is_u: st.session_state.pro_usage += 1
                    else: st.session_state.flash_usage += 1

                    cursor.execute("UPDATE Users SET flash_usage=%s, pro_usage=%s WHERE user_id=%s", (st.session_state.flash_usage, st.session_state.pro_usage, st.session_state.user_id))

                    cln = [{k:v for k,v in m.items() if k!="image_indicator"} for m in st.session_state.messages[-20:]]
                    cursor.execute("UPDATE ChatLogs SET messages=%s WHERE session_id=%s", (json.dumps(cln), st.session_state.session_id))
                    conn.commit()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
    cursor.close(); conn.close()
