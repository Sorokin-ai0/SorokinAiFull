# =============================================================================
# KNOWLEDGE TREE DATA STRUCTURE
# Complete hierarchical data for the interactive Knowledge Tree visualization
# =============================================================================

# Subject configuration with colors and icons
SUBJECTS = {
    "math": {
        "id": "math",
        "name": "Mathematics",
        "icon": "calculator",
        "color": "#3498db",
        "gradient": ["#3498db", "#2980b9"],
        "glow": "rgba(52, 152, 219, 0.6)"
    },
    "science": {
        "id": "science",
        "name": "Science",
        "icon": "flask",
        "color": "#27ae60",
        "gradient": ["#27ae60", "#1e8449"],
        "glow": "rgba(39, 174, 96, 0.6)"
    },
    "cs": {
        "id": "cs",
        "name": "Computer Science",
        "icon": "code",
        "color": "#9b59b6",
        "gradient": ["#9b59b6", "#8e44ad"],
        "glow": "rgba(155, 89, 182, 0.6)"
    }
}

# XP values for different lesson types
XP_VALUES = {
    "intro": 50,
    "standard": 75,
    "advanced": 100,
    "exam": 150,
    "project": 125
}

# Level thresholds
LEVELS = {
    1: 0,
    2: 200,
    3: 500,
    4: 1000,
    5: 1800,
    6: 3000,
    7: 4500,
    8: 6500,
    9: 9000,
    10: 12000
}

def get_lesson_type(title):
    """Determine lesson type based on title for XP calculation"""
    title_lower = title.lower()
    if "final" in title_lower or "exam" in title_lower:
        return "exam"
    elif "project" in title_lower:
        return "project"
    elif "1." in title or "intro" in title_lower:
        return "intro"
    elif any(x in title_lower for x in ["adv", "complex", "advanced"]):
        return "advanced"
    return "standard"

def estimate_duration(desc):
    """Estimate lesson duration based on description complexity"""
    base_time = 15
    complexity_bonus = min(7, len(desc) // 15)
    return base_time + complexity_bonus

def generate_lesson_id(course_id, lesson_num):
    """Generate unique lesson ID"""
    return f"{course_id}_L{lesson_num:02d}"

# =============================================================================
# COMPLETE KNOWLEDGE TREE
# =============================================================================

KNOWLEDGE_TREE = {
    "root": {
        "id": "student",
        "type": "student",
        "name": "My Learning Journey"
    },
    "subjects": SUBJECTS,
    "courses": {
        # =====================================================================
        # MATHEMATICS COURSES
        # =====================================================================
        "algebra1": {
            "id": "algebra1",
            "subject": "math",
            "name": "Algebra I",
            "grade_level": "9th",
            "description": "Foundation of algebraic thinking - variables, equations, and functions",
            "prerequisites": [],
            "total_xp": 900,
            "lessons": [
                {
                    "id": "algebra1_L01",
                    "title": "Variables & Expressions",
                    "description": "Understanding symbols, evaluating algebraic expressions.",
                    "xp_value": XP_VALUES["intro"],
                    "estimated_minutes": 15,
                    "visible_by_default": True,
                    "prerequisites": [],
                    "order": 1
                },
                {
                    "id": "algebra1_L02",
                    "title": "Solving Linear Equations",
                    "description": "Balancing equations, solving for X, multi-step equations.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 18,
                    "visible_by_default": True,
                    "prerequisites": ["algebra1_L01"],
                    "order": 2
                },
                {
                    "id": "algebra1_L03",
                    "title": "Inequalities",
                    "description": "Graphing inequalities on a number line, compound inequalities.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 17,
                    "visible_by_default": True,
                    "prerequisites": ["algebra1_L02"],
                    "order": 3
                },
                {
                    "id": "algebra1_L04",
                    "title": "Intro to Functions",
                    "description": "Domain, range, function notation f(x).",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 18,
                    "visible_by_default": False,
                    "prerequisites": ["algebra1_L03"],
                    "order": 4
                },
                {
                    "id": "algebra1_L05",
                    "title": "Slope & Intercepts",
                    "description": "Rate of change, y=mx+b, graphing lines.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 20,
                    "visible_by_default": False,
                    "prerequisites": ["algebra1_L04"],
                    "order": 5
                },
                {
                    "id": "algebra1_L06",
                    "title": "Systems of Equations",
                    "description": "Substitution, elimination, graphing systems.",
                    "xp_value": XP_VALUES["advanced"],
                    "estimated_minutes": 22,
                    "visible_by_default": False,
                    "prerequisites": ["algebra1_L05"],
                    "order": 6
                },
                {
                    "id": "algebra1_L07",
                    "title": "Exponents",
                    "description": "Laws of exponents, scientific notation.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 16,
                    "visible_by_default": False,
                    "prerequisites": ["algebra1_L06"],
                    "order": 7
                },
                {
                    "id": "algebra1_L08",
                    "title": "Polynomials",
                    "description": "Adding, subtracting, and multiplying polynomials.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 18,
                    "visible_by_default": False,
                    "prerequisites": ["algebra1_L07"],
                    "order": 8
                },
                {
                    "id": "algebra1_L09",
                    "title": "Factoring",
                    "description": "GCF, difference of squares, trinomials.",
                    "xp_value": XP_VALUES["advanced"],
                    "estimated_minutes": 20,
                    "visible_by_default": False,
                    "prerequisites": ["algebra1_L08"],
                    "order": 9
                },
                {
                    "id": "algebra1_L10",
                    "title": "Quadratics",
                    "description": "Quadratic formula, parabolas, vertex form.",
                    "xp_value": XP_VALUES["advanced"],
                    "estimated_minutes": 22,
                    "visible_by_default": False,
                    "prerequisites": ["algebra1_L09"],
                    "order": 10
                },
                {
                    "id": "algebra1_L11",
                    "title": "Statistics",
                    "description": "Mean, median, mode, box plots, standard deviation.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 18,
                    "visible_by_default": False,
                    "prerequisites": ["algebra1_L10"],
                    "order": 11
                },
                {
                    "id": "algebra1_L12",
                    "title": "Final Exam",
                    "description": "Comprehensive review of Algebra I concepts.",
                    "xp_value": XP_VALUES["exam"],
                    "estimated_minutes": 30,
                    "visible_by_default": False,
                    "prerequisites": ["algebra1_L11"],
                    "order": 12
                }
            ]
        },
        "geometry": {
            "id": "geometry",
            "subject": "math",
            "name": "Geometry",
            "grade_level": "10th",
            "description": "Shapes, proofs, and spatial reasoning",
            "prerequisites": ["algebra1"],
            "total_xp": 1050,
            "lessons": [
                {
                    "id": "geometry_L01",
                    "title": "Points & Planes",
                    "description": "Foundations of Euclidean geometry, rays, segments.",
                    "xp_value": XP_VALUES["intro"],
                    "estimated_minutes": 15,
                    "visible_by_default": True,
                    "prerequisites": [],
                    "order": 1
                },
                {
                    "id": "geometry_L02",
                    "title": "Logical Proofs",
                    "description": "Inductive vs deductive reasoning, two-column proofs.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 20,
                    "visible_by_default": True,
                    "prerequisites": ["geometry_L01"],
                    "order": 2
                },
                {
                    "id": "geometry_L03",
                    "title": "Perpendicular Lines",
                    "description": "Transversals, parallel lines, angle pairs.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 18,
                    "visible_by_default": True,
                    "prerequisites": ["geometry_L02"],
                    "order": 3
                },
                {
                    "id": "geometry_L04",
                    "title": "Congruent Triangles",
                    "description": "SSS, SAS, ASA, AAS, HL postulates.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 20,
                    "visible_by_default": False,
                    "prerequisites": ["geometry_L03"],
                    "order": 4
                },
                {
                    "id": "geometry_L05",
                    "title": "Triangle Relationships",
                    "description": "Bisectors, medians, altitudes, midsegments.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 18,
                    "visible_by_default": False,
                    "prerequisites": ["geometry_L04"],
                    "order": 5
                },
                {
                    "id": "geometry_L06",
                    "title": "Polygons",
                    "description": "Sum of interior angles, parallelograms, trapezoids.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 17,
                    "visible_by_default": False,
                    "prerequisites": ["geometry_L05"],
                    "order": 6
                },
                {
                    "id": "geometry_L07",
                    "title": "Similarity",
                    "description": "Ratios, proportions, similar triangles.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 18,
                    "visible_by_default": False,
                    "prerequisites": ["geometry_L06"],
                    "order": 7
                },
                {
                    "id": "geometry_L08",
                    "title": "Right Triangles",
                    "description": "Pythagorean theorem, special right triangles.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 20,
                    "visible_by_default": False,
                    "prerequisites": ["geometry_L07"],
                    "order": 8
                },
                {
                    "id": "geometry_L09",
                    "title": "Circles",
                    "description": "Tangents, arcs, chords, inscribed angles.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 18,
                    "visible_by_default": False,
                    "prerequisites": ["geometry_L08"],
                    "order": 9
                },
                {
                    "id": "geometry_L10",
                    "title": "Area",
                    "description": "Area of polygons and circles.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 16,
                    "visible_by_default": False,
                    "prerequisites": ["geometry_L09"],
                    "order": 10
                },
                {
                    "id": "geometry_L11",
                    "title": "Volume",
                    "description": "Prisms, cylinders, pyramids, cones, spheres.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 18,
                    "visible_by_default": False,
                    "prerequisites": ["geometry_L10"],
                    "order": 11
                },
                {
                    "id": "geometry_L12",
                    "title": "Transformations",
                    "description": "Reflections, rotations, translations, dilations.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 17,
                    "visible_by_default": False,
                    "prerequisites": ["geometry_L11"],
                    "order": 12
                },
                {
                    "id": "geometry_L13",
                    "title": "Advanced Circles",
                    "description": "Equation of a circle, secants.",
                    "xp_value": XP_VALUES["advanced"],
                    "estimated_minutes": 20,
                    "visible_by_default": False,
                    "prerequisites": ["geometry_L12"],
                    "order": 13
                },
                {
                    "id": "geometry_L14",
                    "title": "Final Exam",
                    "description": "Comprehensive review of Geometry concepts.",
                    "xp_value": XP_VALUES["exam"],
                    "estimated_minutes": 30,
                    "visible_by_default": False,
                    "prerequisites": ["geometry_L13"],
                    "order": 14
                }
            ]
        },
        "algebra2": {
            "id": "algebra2",
            "subject": "math",
            "name": "Algebra II",
            "grade_level": "11th",
            "description": "Advanced algebraic concepts and trigonometry introduction",
            "prerequisites": ["geometry"],
            "total_xp": 1125,
            "lessons": [
                {
                    "id": "algebra2_L01",
                    "title": "Linear Review",
                    "description": "Absolute value equations, piecewise functions.",
                    "xp_value": XP_VALUES["intro"],
                    "estimated_minutes": 15,
                    "visible_by_default": True,
                    "prerequisites": [],
                    "order": 1
                },
                {
                    "id": "algebra2_L02",
                    "title": "Quadratic Functions",
                    "description": "Complex numbers, completing the square.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 18,
                    "visible_by_default": True,
                    "prerequisites": ["algebra2_L01"],
                    "order": 2
                },
                {
                    "id": "algebra2_L03",
                    "title": "Complex Numbers",
                    "description": "Operations with imaginary numbers.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 17,
                    "visible_by_default": True,
                    "prerequisites": ["algebra2_L02"],
                    "order": 3
                },
                {
                    "id": "algebra2_L04",
                    "title": "Polynomials",
                    "description": "Synthetic division, remainder theorem, end behavior.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 20,
                    "visible_by_default": False,
                    "prerequisites": ["algebra2_L03"],
                    "order": 4
                },
                {
                    "id": "algebra2_L05",
                    "title": "Radicals",
                    "description": "Square roots, cube roots, rational exponents.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 17,
                    "visible_by_default": False,
                    "prerequisites": ["algebra2_L04"],
                    "order": 5
                },
                {
                    "id": "algebra2_L06",
                    "title": "Exponentials",
                    "description": "Growth and decay models.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 18,
                    "visible_by_default": False,
                    "prerequisites": ["algebra2_L05"],
                    "order": 6
                },
                {
                    "id": "algebra2_L07",
                    "title": "Logarithms",
                    "description": "Properties of logs, solving logarithmic equations.",
                    "xp_value": XP_VALUES["advanced"],
                    "estimated_minutes": 22,
                    "visible_by_default": False,
                    "prerequisites": ["algebra2_L06"],
                    "order": 7
                },
                {
                    "id": "algebra2_L08",
                    "title": "Rational Functions",
                    "description": "Vertical and horizontal asymptotes.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 18,
                    "visible_by_default": False,
                    "prerequisites": ["algebra2_L07"],
                    "order": 8
                },
                {
                    "id": "algebra2_L09",
                    "title": "Sequences",
                    "description": "Arithmetic and geometric sequences and series.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 17,
                    "visible_by_default": False,
                    "prerequisites": ["algebra2_L08"],
                    "order": 9
                },
                {
                    "id": "algebra2_L10",
                    "title": "Conics",
                    "description": "Parabolas, circles, ellipses, hyperbolas.",
                    "xp_value": XP_VALUES["advanced"],
                    "estimated_minutes": 22,
                    "visible_by_default": False,
                    "prerequisites": ["algebra2_L09"],
                    "order": 10
                },
                {
                    "id": "algebra2_L11",
                    "title": "Probability",
                    "description": "Permutations, combinations, binomial probability.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 18,
                    "visible_by_default": False,
                    "prerequisites": ["algebra2_L10"],
                    "order": 11
                },
                {
                    "id": "algebra2_L12",
                    "title": "Trig Ratios",
                    "description": "SOH CAH TOA, unit circle basics.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 17,
                    "visible_by_default": False,
                    "prerequisites": ["algebra2_L11"],
                    "order": 12
                },
                {
                    "id": "algebra2_L13",
                    "title": "Trig Graphs",
                    "description": "Sine, cosine, tangent waves.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 18,
                    "visible_by_default": False,
                    "prerequisites": ["algebra2_L12"],
                    "order": 13
                },
                {
                    "id": "algebra2_L14",
                    "title": "Identities",
                    "description": "Pythagorean identities, sum and difference formulas.",
                    "xp_value": XP_VALUES["advanced"],
                    "estimated_minutes": 20,
                    "visible_by_default": False,
                    "prerequisites": ["algebra2_L13"],
                    "order": 14
                },
                {
                    "id": "algebra2_L15",
                    "title": "Final Exam",
                    "description": "Comprehensive review of Algebra II.",
                    "xp_value": XP_VALUES["exam"],
                    "estimated_minutes": 30,
                    "visible_by_default": False,
                    "prerequisites": ["algebra2_L14"],
                    "order": 15
                }
            ]
        },
        "precalc": {
            "id": "precalc",
            "subject": "math",
            "name": "Pre-Calculus",
            "grade_level": "12th",
            "description": "Bridge to calculus - advanced functions and limits",
            "prerequisites": ["algebra2"],
            "total_xp": 1200,
            "lessons": [
                {
                    "id": "precalc_L01",
                    "title": "Graphs",
                    "description": "Analyzing 12 basic parent functions.",
                    "xp_value": XP_VALUES["intro"],
                    "estimated_minutes": 15,
                    "visible_by_default": True,
                    "prerequisites": [],
                    "order": 1
                },
                {
                    "id": "precalc_L02",
                    "title": "Polynomials",
                    "description": "Real and complex zeros, fundamental theorem of algebra.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 20,
                    "visible_by_default": True,
                    "prerequisites": ["precalc_L01"],
                    "order": 2
                },
                {
                    "id": "precalc_L03",
                    "title": "Exponentials",
                    "description": "Logistic growth models.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 17,
                    "visible_by_default": True,
                    "prerequisites": ["precalc_L02"],
                    "order": 3
                },
                {
                    "id": "precalc_L04",
                    "title": "Trig Functions",
                    "description": "Radian measure, unit circle in depth.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 20,
                    "visible_by_default": False,
                    "prerequisites": ["precalc_L03"],
                    "order": 4
                },
                {
                    "id": "precalc_L05",
                    "title": "Analytic Trigonometry",
                    "description": "Proving identities, solving trig equations.",
                    "xp_value": XP_VALUES["advanced"],
                    "estimated_minutes": 22,
                    "visible_by_default": False,
                    "prerequisites": ["precalc_L04"],
                    "order": 5
                },
                {
                    "id": "precalc_L06",
                    "title": "Applications",
                    "description": "Law of Sines, Law of Cosines.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 18,
                    "visible_by_default": False,
                    "prerequisites": ["precalc_L05"],
                    "order": 6
                },
                {
                    "id": "precalc_L07",
                    "title": "Matrices",
                    "description": "Operations, determinants, inverses.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 20,
                    "visible_by_default": False,
                    "prerequisites": ["precalc_L06"],
                    "order": 7
                },
                {
                    "id": "precalc_L08",
                    "title": "Conics",
                    "description": "Rotated conics, parametric definitions.",
                    "xp_value": XP_VALUES["advanced"],
                    "estimated_minutes": 22,
                    "visible_by_default": False,
                    "prerequisites": ["precalc_L07"],
                    "order": 8
                },
                {
                    "id": "precalc_L09",
                    "title": "Discrete Math",
                    "description": "Induction, binomial theorem.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 18,
                    "visible_by_default": False,
                    "prerequisites": ["precalc_L08"],
                    "order": 9
                },
                {
                    "id": "precalc_L10",
                    "title": "Limits",
                    "description": "Intuitive definition, one-sided limits.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 20,
                    "visible_by_default": False,
                    "prerequisites": ["precalc_L09"],
                    "order": 10
                },
                {
                    "id": "precalc_L11",
                    "title": "Derivatives Intro",
                    "description": "Tangent lines, rates of change.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 20,
                    "visible_by_default": False,
                    "prerequisites": ["precalc_L10"],
                    "order": 11
                },
                {
                    "id": "precalc_L12",
                    "title": "Vectors",
                    "description": "Dot product, cross product, projection.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 18,
                    "visible_by_default": False,
                    "prerequisites": ["precalc_L11"],
                    "order": 12
                },
                {
                    "id": "precalc_L13",
                    "title": "Polar Coords",
                    "description": "Graphing polar equations.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 17,
                    "visible_by_default": False,
                    "prerequisites": ["precalc_L12"],
                    "order": 13
                },
                {
                    "id": "precalc_L14",
                    "title": "Parametrics",
                    "description": "Motion in a plane.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 17,
                    "visible_by_default": False,
                    "prerequisites": ["precalc_L13"],
                    "order": 14
                },
                {
                    "id": "precalc_L15",
                    "title": "3D Space",
                    "description": "Coordinates in 3 dimensions.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 18,
                    "visible_by_default": False,
                    "prerequisites": ["precalc_L14"],
                    "order": 15
                },
                {
                    "id": "precalc_L16",
                    "title": "Final Exam",
                    "description": "Review for Calculus readiness.",
                    "xp_value": XP_VALUES["exam"],
                    "estimated_minutes": 30,
                    "visible_by_default": False,
                    "prerequisites": ["precalc_L15"],
                    "order": 16
                }
            ]
        },
        "calculus1": {
            "id": "calculus1",
            "subject": "math",
            "name": "Calculus I",
            "grade_level": "College",
            "description": "Limits, derivatives, and introduction to integrals",
            "prerequisites": ["precalc"],
            "total_xp": 1350,
            "lessons": [
                {
                    "id": "calculus1_L01",
                    "title": "Limits",
                    "description": "Limit laws, sandwich theorem, continuity.",
                    "xp_value": XP_VALUES["intro"],
                    "estimated_minutes": 18,
                    "visible_by_default": True,
                    "prerequisites": [],
                    "order": 1
                },
                {
                    "id": "calculus1_L02",
                    "title": "Continuity",
                    "description": "IVT, types of discontinuities.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 17,
                    "visible_by_default": True,
                    "prerequisites": ["calculus1_L01"],
                    "order": 2
                },
                {
                    "id": "calculus1_L03",
                    "title": "Derivatives",
                    "description": "Definition as a limit.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 20,
                    "visible_by_default": True,
                    "prerequisites": ["calculus1_L02"],
                    "order": 3
                },
                {
                    "id": "calculus1_L04",
                    "title": "Differentiation Rules",
                    "description": "Power, product, quotient rules.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 20,
                    "visible_by_default": False,
                    "prerequisites": ["calculus1_L03"],
                    "order": 4
                },
                {
                    "id": "calculus1_L05",
                    "title": "Chain Rule",
                    "description": "Composite functions.",
                    "xp_value": XP_VALUES["advanced"],
                    "estimated_minutes": 22,
                    "visible_by_default": False,
                    "prerequisites": ["calculus1_L04"],
                    "order": 5
                },
                {
                    "id": "calculus1_L06",
                    "title": "Implicit Differentiation",
                    "description": "Finding dy/dx without solving for y.",
                    "xp_value": XP_VALUES["advanced"],
                    "estimated_minutes": 22,
                    "visible_by_default": False,
                    "prerequisites": ["calculus1_L05"],
                    "order": 6
                },
                {
                    "id": "calculus1_L07",
                    "title": "Applications",
                    "description": "Tangent line approximation.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 18,
                    "visible_by_default": False,
                    "prerequisites": ["calculus1_L06"],
                    "order": 7
                },
                {
                    "id": "calculus1_L08",
                    "title": "Optimization",
                    "description": "Maximizing volume, minimizing cost.",
                    "xp_value": XP_VALUES["advanced"],
                    "estimated_minutes": 25,
                    "visible_by_default": False,
                    "prerequisites": ["calculus1_L07"],
                    "order": 8
                },
                {
                    "id": "calculus1_L09",
                    "title": "Related Rates",
                    "description": "Time-dependent rates of change.",
                    "xp_value": XP_VALUES["advanced"],
                    "estimated_minutes": 25,
                    "visible_by_default": False,
                    "prerequisites": ["calculus1_L08"],
                    "order": 9
                },
                {
                    "id": "calculus1_L10",
                    "title": "Antiderivatives",
                    "description": "Indefinite integrals.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 18,
                    "visible_by_default": False,
                    "prerequisites": ["calculus1_L09"],
                    "order": 10
                },
                {
                    "id": "calculus1_L11",
                    "title": "Riemann Sums",
                    "description": "Area under a curve estimation.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 20,
                    "visible_by_default": False,
                    "prerequisites": ["calculus1_L10"],
                    "order": 11
                },
                {
                    "id": "calculus1_L12",
                    "title": "Definite Integrals",
                    "description": "Exact area accumulation.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 20,
                    "visible_by_default": False,
                    "prerequisites": ["calculus1_L11"],
                    "order": 12
                },
                {
                    "id": "calculus1_L13",
                    "title": "Fundamental Theorem of Calculus",
                    "description": "Connecting derivatives and integrals.",
                    "xp_value": XP_VALUES["advanced"],
                    "estimated_minutes": 25,
                    "visible_by_default": False,
                    "prerequisites": ["calculus1_L12"],
                    "order": 13
                },
                {
                    "id": "calculus1_L14",
                    "title": "Substitution",
                    "description": "u-substitution technique.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 18,
                    "visible_by_default": False,
                    "prerequisites": ["calculus1_L13"],
                    "order": 14
                },
                {
                    "id": "calculus1_L15",
                    "title": "Area Between Curves",
                    "description": "Area between two curves.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 18,
                    "visible_by_default": False,
                    "prerequisites": ["calculus1_L14"],
                    "order": 15
                },
                {
                    "id": "calculus1_L16",
                    "title": "Volume",
                    "description": "Disk and washer methods.",
                    "xp_value": XP_VALUES["advanced"],
                    "estimated_minutes": 22,
                    "visible_by_default": False,
                    "prerequisites": ["calculus1_L15"],
                    "order": 16
                },
                {
                    "id": "calculus1_L17",
                    "title": "Differential Equations",
                    "description": "Separation of variables.",
                    "xp_value": XP_VALUES["advanced"],
                    "estimated_minutes": 22,
                    "visible_by_default": False,
                    "prerequisites": ["calculus1_L16"],
                    "order": 17
                },
                {
                    "id": "calculus1_L18",
                    "title": "Final Exam",
                    "description": "Comprehensive Calculus I review.",
                    "xp_value": XP_VALUES["exam"],
                    "estimated_minutes": 35,
                    "visible_by_default": False,
                    "prerequisites": ["calculus1_L17"],
                    "order": 18
                }
            ]
        },
        # =====================================================================
        # SCIENCE COURSES
        # =====================================================================
        "biology": {
            "id": "biology",
            "subject": "science",
            "name": "Biology",
            "grade_level": "9th-10th",
            "description": "The study of life - cells, genetics, and ecosystems",
            "prerequisites": [],
            "total_xp": 1050,
            "lessons": [
                {
                    "id": "biology_L01",
                    "title": "Science of Biology",
                    "description": "Scientific method, characteristics of life.",
                    "xp_value": XP_VALUES["intro"],
                    "estimated_minutes": 15,
                    "visible_by_default": True,
                    "prerequisites": [],
                    "order": 1
                },
                {
                    "id": "biology_L02",
                    "title": "Chemistry of Life",
                    "description": "Macromolecules: carbs, lipids, proteins, nucleic acids.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 20,
                    "visible_by_default": True,
                    "prerequisites": ["biology_L01"],
                    "order": 2
                },
                {
                    "id": "biology_L03",
                    "title": "Cells",
                    "description": "Prokaryotes vs Eukaryotes, organelles.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 18,
                    "visible_by_default": True,
                    "prerequisites": ["biology_L02"],
                    "order": 3
                },
                {
                    "id": "biology_L04",
                    "title": "Photosynthesis",
                    "description": "Light reactions, Calvin cycle.",
                    "xp_value": XP_VALUES["advanced"],
                    "estimated_minutes": 22,
                    "visible_by_default": False,
                    "prerequisites": ["biology_L03"],
                    "order": 4
                },
                {
                    "id": "biology_L05",
                    "title": "Cellular Respiration",
                    "description": "Glycolysis, Krebs cycle, ETC.",
                    "xp_value": XP_VALUES["advanced"],
                    "estimated_minutes": 25,
                    "visible_by_default": False,
                    "prerequisites": ["biology_L04"],
                    "order": 5
                },
                {
                    "id": "biology_L06",
                    "title": "Mitosis",
                    "description": "Cell cycle, somatic cell division.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 18,
                    "visible_by_default": False,
                    "prerequisites": ["biology_L05"],
                    "order": 6
                },
                {
                    "id": "biology_L07",
                    "title": "Meiosis",
                    "description": "Gamete formation, genetic variation.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 20,
                    "visible_by_default": False,
                    "prerequisites": ["biology_L06"],
                    "order": 7
                },
                {
                    "id": "biology_L08",
                    "title": "Genetics",
                    "description": "Punnett squares, Mendel's laws.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 20,
                    "visible_by_default": False,
                    "prerequisites": ["biology_L07"],
                    "order": 8
                },
                {
                    "id": "biology_L09",
                    "title": "DNA",
                    "description": "Replication, transcription, translation.",
                    "xp_value": XP_VALUES["advanced"],
                    "estimated_minutes": 25,
                    "visible_by_default": False,
                    "prerequisites": ["biology_L08"],
                    "order": 9
                },
                {
                    "id": "biology_L10",
                    "title": "Evolution",
                    "description": "Natural selection, evidence for evolution.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 18,
                    "visible_by_default": False,
                    "prerequisites": ["biology_L09"],
                    "order": 10
                },
                {
                    "id": "biology_L11",
                    "title": "Ecology",
                    "description": "Ecosystems, food webs, trophic levels.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 18,
                    "visible_by_default": False,
                    "prerequisites": ["biology_L10"],
                    "order": 11
                },
                {
                    "id": "biology_L12",
                    "title": "Classification",
                    "description": "Taxonomy, phylogeny.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 16,
                    "visible_by_default": False,
                    "prerequisites": ["biology_L11"],
                    "order": 12
                },
                {
                    "id": "biology_L13",
                    "title": "Human Systems",
                    "description": "Organ systems overview.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 20,
                    "visible_by_default": False,
                    "prerequisites": ["biology_L12"],
                    "order": 13
                },
                {
                    "id": "biology_L14",
                    "title": "Final Exam",
                    "description": "Biology comprehensive review.",
                    "xp_value": XP_VALUES["exam"],
                    "estimated_minutes": 30,
                    "visible_by_default": False,
                    "prerequisites": ["biology_L13"],
                    "order": 14
                }
            ]
        },
        "chemistry": {
            "id": "chemistry",
            "subject": "science",
            "name": "Chemistry",
            "grade_level": "11th",
            "description": "Matter, atoms, reactions, and chemical principles",
            "prerequisites": ["algebra1"],
            "total_xp": 1200,
            "lessons": [
                {
                    "id": "chemistry_L01",
                    "title": "Matter",
                    "description": "States of matter, physical vs chemical changes.",
                    "xp_value": XP_VALUES["intro"],
                    "estimated_minutes": 15,
                    "visible_by_default": True,
                    "prerequisites": [],
                    "order": 1
                },
                {
                    "id": "chemistry_L02",
                    "title": "Atoms",
                    "description": "Protons, neutrons, electrons, isotopes.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 17,
                    "visible_by_default": True,
                    "prerequisites": ["chemistry_L01"],
                    "order": 2
                },
                {
                    "id": "chemistry_L03",
                    "title": "Periodic Table",
                    "description": "Trends: electronegativity, radius, ionization energy.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 20,
                    "visible_by_default": True,
                    "prerequisites": ["chemistry_L02"],
                    "order": 3
                },
                {
                    "id": "chemistry_L04",
                    "title": "Bonding",
                    "description": "Ionic vs covalent, Lewis structures.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 20,
                    "visible_by_default": False,
                    "prerequisites": ["chemistry_L03"],
                    "order": 4
                },
                {
                    "id": "chemistry_L05",
                    "title": "Naming Compounds",
                    "description": "IUPAC nomenclature.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 16,
                    "visible_by_default": False,
                    "prerequisites": ["chemistry_L04"],
                    "order": 5
                },
                {
                    "id": "chemistry_L06",
                    "title": "The Mole",
                    "description": "Avogadro's number, molar mass.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 18,
                    "visible_by_default": False,
                    "prerequisites": ["chemistry_L05"],
                    "order": 6
                },
                {
                    "id": "chemistry_L07",
                    "title": "Chemical Reactions",
                    "description": "Balancing equations, types of reactions.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 20,
                    "visible_by_default": False,
                    "prerequisites": ["chemistry_L06"],
                    "order": 7
                },
                {
                    "id": "chemistry_L08",
                    "title": "Stoichiometry",
                    "description": "Limiting reactants, percent yield.",
                    "xp_value": XP_VALUES["advanced"],
                    "estimated_minutes": 25,
                    "visible_by_default": False,
                    "prerequisites": ["chemistry_L07"],
                    "order": 8
                },
                {
                    "id": "chemistry_L09",
                    "title": "States of Matter",
                    "description": "IMF, phase diagrams.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 18,
                    "visible_by_default": False,
                    "prerequisites": ["chemistry_L08"],
                    "order": 9
                },
                {
                    "id": "chemistry_L10",
                    "title": "Gases",
                    "description": "Ideal gas law PV=nRT.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 18,
                    "visible_by_default": False,
                    "prerequisites": ["chemistry_L09"],
                    "order": 10
                },
                {
                    "id": "chemistry_L11",
                    "title": "Solutions",
                    "description": "Molarity, molality, solubility.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 18,
                    "visible_by_default": False,
                    "prerequisites": ["chemistry_L10"],
                    "order": 11
                },
                {
                    "id": "chemistry_L12",
                    "title": "Thermochemistry",
                    "description": "Enthalpy, entropy, Gibbs free energy.",
                    "xp_value": XP_VALUES["advanced"],
                    "estimated_minutes": 22,
                    "visible_by_default": False,
                    "prerequisites": ["chemistry_L11"],
                    "order": 12
                },
                {
                    "id": "chemistry_L13",
                    "title": "Kinetics",
                    "description": "Rate laws, collision theory.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 18,
                    "visible_by_default": False,
                    "prerequisites": ["chemistry_L12"],
                    "order": 13
                },
                {
                    "id": "chemistry_L14",
                    "title": "Acids & Bases",
                    "description": "pH, pOH, titrations, buffers.",
                    "xp_value": XP_VALUES["advanced"],
                    "estimated_minutes": 22,
                    "visible_by_default": False,
                    "prerequisites": ["chemistry_L13"],
                    "order": 14
                },
                {
                    "id": "chemistry_L15",
                    "title": "Redox Reactions",
                    "description": "Oxidation numbers, galvanic cells.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 18,
                    "visible_by_default": False,
                    "prerequisites": ["chemistry_L14"],
                    "order": 15
                },
                {
                    "id": "chemistry_L16",
                    "title": "Nuclear Chemistry",
                    "description": "Alpha, beta, gamma decay.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 17,
                    "visible_by_default": False,
                    "prerequisites": ["chemistry_L15"],
                    "order": 16
                }
            ]
        },
        "physics": {
            "id": "physics",
            "subject": "science",
            "name": "Physics",
            "grade_level": "12th",
            "description": "Forces, motion, energy, waves, and light",
            "prerequisites": ["algebra2"],
            "total_xp": 1125,
            "lessons": [
                {
                    "id": "physics_L01",
                    "title": "1D Kinematics",
                    "description": "Displacement, velocity, acceleration.",
                    "xp_value": XP_VALUES["intro"],
                    "estimated_minutes": 18,
                    "visible_by_default": True,
                    "prerequisites": [],
                    "order": 1
                },
                {
                    "id": "physics_L02",
                    "title": "Vectors",
                    "description": "Vector addition, components.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 17,
                    "visible_by_default": True,
                    "prerequisites": ["physics_L01"],
                    "order": 2
                },
                {
                    "id": "physics_L03",
                    "title": "2D Kinematics",
                    "description": "Projectile motion.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 20,
                    "visible_by_default": True,
                    "prerequisites": ["physics_L02"],
                    "order": 3
                },
                {
                    "id": "physics_L04",
                    "title": "Newton's Laws",
                    "description": "F=ma, inertia, action-reaction.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 20,
                    "visible_by_default": False,
                    "prerequisites": ["physics_L03"],
                    "order": 4
                },
                {
                    "id": "physics_L05",
                    "title": "Friction",
                    "description": "Static vs kinetic friction.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 17,
                    "visible_by_default": False,
                    "prerequisites": ["physics_L04"],
                    "order": 5
                },
                {
                    "id": "physics_L06",
                    "title": "Work & Energy",
                    "description": "KE, PE, conservation of energy.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 20,
                    "visible_by_default": False,
                    "prerequisites": ["physics_L05"],
                    "order": 6
                },
                {
                    "id": "physics_L07",
                    "title": "Momentum",
                    "description": "Impulse, elastic vs inelastic collisions.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 18,
                    "visible_by_default": False,
                    "prerequisites": ["physics_L06"],
                    "order": 7
                },
                {
                    "id": "physics_L08",
                    "title": "Circular Motion",
                    "description": "Centripetal force, gravity.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 18,
                    "visible_by_default": False,
                    "prerequisites": ["physics_L07"],
                    "order": 8
                },
                {
                    "id": "physics_L09",
                    "title": "Rotation",
                    "description": "Torque, moment of inertia.",
                    "xp_value": XP_VALUES["advanced"],
                    "estimated_minutes": 22,
                    "visible_by_default": False,
                    "prerequisites": ["physics_L08"],
                    "order": 9
                },
                {
                    "id": "physics_L10",
                    "title": "Equilibrium",
                    "description": "Statics, sum of forces/torques = 0.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 18,
                    "visible_by_default": False,
                    "prerequisites": ["physics_L09"],
                    "order": 10
                },
                {
                    "id": "physics_L11",
                    "title": "Fluids",
                    "description": "Buoyancy, Bernoulli's principle.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 18,
                    "visible_by_default": False,
                    "prerequisites": ["physics_L10"],
                    "order": 11
                },
                {
                    "id": "physics_L12",
                    "title": "Thermodynamics",
                    "description": "Heat transfer, laws of thermodynamics.",
                    "xp_value": XP_VALUES["advanced"],
                    "estimated_minutes": 22,
                    "visible_by_default": False,
                    "prerequisites": ["physics_L11"],
                    "order": 12
                },
                {
                    "id": "physics_L13",
                    "title": "Waves",
                    "description": "Frequency, wavelength, Doppler effect.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 18,
                    "visible_by_default": False,
                    "prerequisites": ["physics_L12"],
                    "order": 13
                },
                {
                    "id": "physics_L14",
                    "title": "Sound",
                    "description": "Resonance, harmonics.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 17,
                    "visible_by_default": False,
                    "prerequisites": ["physics_L13"],
                    "order": 14
                },
                {
                    "id": "physics_L15",
                    "title": "Light & Optics",
                    "description": "Reflection, refraction, optics.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 18,
                    "visible_by_default": False,
                    "prerequisites": ["physics_L14"],
                    "order": 15
                }
            ]
        },
        # =====================================================================
        # COMPUTER SCIENCE COURSES
        # =====================================================================
        "python_intro": {
            "id": "python_intro",
            "subject": "cs",
            "name": "Intro to Python",
            "grade_level": "9th-College",
            "description": "Learn programming fundamentals with Python",
            "prerequisites": [],
            "total_xp": 750,
            "lessons": [
                {
                    "id": "python_intro_L01",
                    "title": "Variables",
                    "description": "Strings, integers, floats.",
                    "xp_value": XP_VALUES["intro"],
                    "estimated_minutes": 15,
                    "visible_by_default": True,
                    "prerequisites": [],
                    "order": 1
                },
                {
                    "id": "python_intro_L02",
                    "title": "Data Types",
                    "description": "Type casting, dynamic typing.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 16,
                    "visible_by_default": True,
                    "prerequisites": ["python_intro_L01"],
                    "order": 2
                },
                {
                    "id": "python_intro_L03",
                    "title": "Conditionals",
                    "description": "Booleans, if/else, logic gates.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 18,
                    "visible_by_default": True,
                    "prerequisites": ["python_intro_L02"],
                    "order": 3
                },
                {
                    "id": "python_intro_L04",
                    "title": "Loops",
                    "description": "For loops, while loops, break/continue.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 20,
                    "visible_by_default": False,
                    "prerequisites": ["python_intro_L03"],
                    "order": 4
                },
                {
                    "id": "python_intro_L05",
                    "title": "Functions",
                    "description": "Def, arguments, return values.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 20,
                    "visible_by_default": False,
                    "prerequisites": ["python_intro_L04"],
                    "order": 5
                },
                {
                    "id": "python_intro_L06",
                    "title": "Lists",
                    "description": "Indexing, slicing, appending.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 18,
                    "visible_by_default": False,
                    "prerequisites": ["python_intro_L05"],
                    "order": 6
                },
                {
                    "id": "python_intro_L07",
                    "title": "Dictionaries",
                    "description": "Key-value pairs.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 17,
                    "visible_by_default": False,
                    "prerequisites": ["python_intro_L06"],
                    "order": 7
                },
                {
                    "id": "python_intro_L08",
                    "title": "File I/O",
                    "description": "Reading and writing txt/csv.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 18,
                    "visible_by_default": False,
                    "prerequisites": ["python_intro_L07"],
                    "order": 8
                },
                {
                    "id": "python_intro_L09",
                    "title": "Libraries",
                    "description": "Importing math, random, time.",
                    "xp_value": XP_VALUES["standard"],
                    "estimated_minutes": 16,
                    "visible_by_default": False,
                    "prerequisites": ["python_intro_L08"],
                    "order": 9
                },
                {
                    "id": "python_intro_L10",
                    "title": "Final Project",
                    "description": "Building a simple calculator or game.",
                    "xp_value": XP_VALUES["project"],
                    "estimated_minutes": 45,
                    "visible_by_default": False,
                    "prerequisites": ["python_intro_L09"],
                    "order": 10
                }
            ]
        }
    }
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_all_lessons():
    """Get flat list of all lessons across all courses"""
    lessons = []
    for course_id, course in KNOWLEDGE_TREE["courses"].items():
        for lesson in course["lessons"]:
            lesson_copy = lesson.copy()
            lesson_copy["course_id"] = course_id
            lesson_copy["course_name"] = course["name"]
            lesson_copy["subject"] = course["subject"]
            lessons.append(lesson_copy)
    return lessons

def get_lesson_by_id(lesson_id):
    """Get a specific lesson by its ID"""
    for course_id, course in KNOWLEDGE_TREE["courses"].items():
        for lesson in course["lessons"]:
            if lesson["id"] == lesson_id:
                lesson_copy = lesson.copy()
                lesson_copy["course_id"] = course_id
                lesson_copy["course_name"] = course["name"]
                lesson_copy["subject"] = course["subject"]
                return lesson_copy
    return None

def get_course_by_id(course_id):
    """Get a specific course by its ID"""
    return KNOWLEDGE_TREE["courses"].get(course_id)

def get_courses_by_subject(subject_id):
    """Get all courses for a specific subject"""
    return [
        course for course in KNOWLEDGE_TREE["courses"].values()
        if course["subject"] == subject_id
    ]

def calculate_user_level(total_xp):
    """Calculate user level based on total XP"""
    level = 1
    for lvl, threshold in sorted(LEVELS.items()):
        if total_xp >= threshold:
            level = lvl
    return level

def get_next_level_xp(current_xp):
    """Get XP needed for next level"""
    current_level = calculate_user_level(current_xp)
    next_level = current_level + 1
    if next_level in LEVELS:
        return LEVELS[next_level] - current_xp
    return 0  # Max level reached

def build_d3_graph_data(user_progress=None):
    """
    Build the node/link data structure for D3.js visualization.
    user_progress should be a dict with lesson_id -> status mapping
    """
    if user_progress is None:
        user_progress = {}

    nodes = []
    links = []

    # Add student (root) node
    nodes.append({
        "id": "student",
        "type": "student",
        "name": "You",
        "color": "#f1c40f",
        "size": 45
    })

    # Add subject nodes
    for subject_id, subject in KNOWLEDGE_TREE["subjects"].items():
        nodes.append({
            "id": subject_id,
            "type": "subject",
            "name": subject["name"],
            "color": subject["color"],
            "glow": subject["glow"],
            "size": 35
        })
        links.append({
            "source": "student",
            "target": subject_id,
            "strength": 0.8
        })

    # Add course and lesson nodes
    for course_id, course in KNOWLEDGE_TREE["courses"].items():
        subject = course["subject"]
        subject_color = KNOWLEDGE_TREE["subjects"][subject]["color"]

        # Calculate course completion
        completed_lessons = sum(
            1 for lesson in course["lessons"]
            if user_progress.get(lesson["id"]) in ["completed", "mastered"]
        )
        total_lessons = len(course["lessons"])
        completion_pct = (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0

        nodes.append({
            "id": course_id,
            "type": "course",
            "name": course["name"],
            "color": subject_color,
            "size": 25,
            "completion": completion_pct,
            "grade_level": course["grade_level"],
            "total_lessons": total_lessons,
            "completed_lessons": completed_lessons
        })
        links.append({
            "source": subject,
            "target": course_id,
            "strength": 0.6
        })

        # Add lesson nodes
        for lesson in course["lessons"]:
            status = user_progress.get(lesson["id"], "locked")

            # Determine if visible
            is_visible = lesson["visible_by_default"] or status != "locked"

            nodes.append({
                "id": lesson["id"],
                "type": "lesson",
                "name": lesson["title"],
                "description": lesson["description"],
                "color": subject_color,
                "size": 12,
                "status": status,
                "visible": is_visible,
                "xp_value": lesson["xp_value"],
                "estimated_minutes": lesson["estimated_minutes"],
                "order": lesson["order"],
                "course_id": course_id,
                "course_name": course["name"]
            })
            links.append({
                "source": course_id,
                "target": lesson["id"],
                "strength": 0.4
            })

    return {"nodes": nodes, "links": links}
