-- =============================================================================
-- KNOWLEDGE TREE DATABASE UPDATES
-- Run these SQL statements to add new tables and columns for the Knowledge Tree
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. ADD NEW COLUMNS TO USERS TABLE
-- These track gamification progress
-- -----------------------------------------------------------------------------

-- Total XP earned by the user
ALTER TABLE Users ADD COLUMN IF NOT EXISTS total_xp INT DEFAULT 0;

-- Current level (calculated from total_xp, but cached for performance)
ALTER TABLE Users ADD COLUMN IF NOT EXISTS current_level INT DEFAULT 1;

-- Streak tracking - consecutive days of learning
ALTER TABLE Users ADD COLUMN IF NOT EXISTS streak_days INT DEFAULT 0;

-- Last streak date - to calculate if streak continues
ALTER TABLE Users ADD COLUMN IF NOT EXISTS last_streak_date DATE NULL;

-- Total lessons completed (denormalized for quick access)
ALTER TABLE Users ADD COLUMN IF NOT EXISTS total_lessons_completed INT DEFAULT 0;

-- Total learning time in minutes
ALTER TABLE Users ADD COLUMN IF NOT EXISTS total_learning_minutes INT DEFAULT 0;


-- -----------------------------------------------------------------------------
-- 2. CREATE LESSON PROGRESS TABLE
-- Tracks individual lesson progress for each user
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS LessonProgress (
    id INT AUTO_INCREMENT PRIMARY KEY,

    -- Foreign key to Users table
    user_id VARCHAR(255) NOT NULL,

    -- Lesson identifier (matches lesson IDs in tree_data.py)
    lesson_id VARCHAR(100) NOT NULL,

    -- Course identifier for easier querying
    course_id VARCHAR(100) NOT NULL,

    -- Status: locked, available, in_progress, completed, mastered
    status ENUM('locked', 'available', 'in_progress', 'completed', 'mastered') DEFAULT 'locked',

    -- Progress percentage (0-100) for in_progress lessons
    progress_percent INT DEFAULT 0,

    -- Timestamps
    started_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    mastered_at TIMESTAMP NULL,
    last_accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- XP earned from this lesson
    xp_earned INT DEFAULT 0,

    -- Time spent on this lesson in minutes
    time_spent_minutes INT DEFAULT 0,

    -- Number of times the lesson was reviewed (for mastery)
    review_count INT DEFAULT 0,

    -- Quiz/assessment score if applicable (0-100)
    assessment_score INT NULL,

    -- Notes or bookmarks the user made
    user_notes TEXT NULL,

    -- Unique constraint: one progress record per user per lesson
    UNIQUE KEY unique_user_lesson (user_id, lesson_id),

    -- Index for faster lookups
    INDEX idx_user_status (user_id, status),
    INDEX idx_lesson_id (lesson_id),
    INDEX idx_course_id (course_id)
);


-- -----------------------------------------------------------------------------
-- 3. CREATE COURSE PROGRESS TABLE
-- Aggregated course-level progress (denormalized for performance)
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS CourseProgress (
    id INT AUTO_INCREMENT PRIMARY KEY,

    -- Foreign key to Users table
    user_id VARCHAR(255) NOT NULL,

    -- Course identifier
    course_id VARCHAR(100) NOT NULL,

    -- Subject for filtering
    subject VARCHAR(50) NOT NULL,

    -- Progress tracking
    total_lessons INT NOT NULL,
    completed_lessons INT DEFAULT 0,
    mastered_lessons INT DEFAULT 0,

    -- Calculated completion percentage
    completion_percent DECIMAL(5,2) DEFAULT 0.00,

    -- Status: not_started, in_progress, completed, mastered
    status ENUM('not_started', 'in_progress', 'completed', 'mastered') DEFAULT 'not_started',

    -- Current active lesson order number
    current_lesson_order INT DEFAULT 1,

    -- Total XP earned in this course
    total_xp_earned INT DEFAULT 0,

    -- Total time spent in minutes
    total_time_spent INT DEFAULT 0,

    -- Timestamps
    started_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    last_accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- Unique constraint
    UNIQUE KEY unique_user_course (user_id, course_id),

    -- Indexes
    INDEX idx_user_subject (user_id, subject),
    INDEX idx_user_status (user_id, status)
);


-- -----------------------------------------------------------------------------
-- 4. CREATE ACHIEVEMENTS TABLE
-- Track badges and achievements earned
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS UserAchievements (
    id INT AUTO_INCREMENT PRIMARY KEY,

    user_id VARCHAR(255) NOT NULL,

    -- Achievement identifier
    achievement_id VARCHAR(100) NOT NULL,

    -- Achievement details (denormalized for display)
    achievement_name VARCHAR(255) NOT NULL,
    achievement_description TEXT,
    achievement_icon VARCHAR(50),

    -- XP bonus awarded
    xp_bonus INT DEFAULT 0,

    -- When earned
    earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Unique constraint
    UNIQUE KEY unique_user_achievement (user_id, achievement_id),

    INDEX idx_user_id (user_id)
);


-- -----------------------------------------------------------------------------
-- 5. CREATE XP TRANSACTIONS LOG
-- Audit trail of all XP earned
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS XPTransactions (
    id INT AUTO_INCREMENT PRIMARY KEY,

    user_id VARCHAR(255) NOT NULL,

    -- XP amount (positive for earned, negative for spent if applicable)
    xp_amount INT NOT NULL,

    -- Source of XP
    source_type ENUM('lesson_complete', 'lesson_mastery', 'achievement', 'streak_bonus', 'daily_bonus', 'other') NOT NULL,

    -- Reference to the source (lesson_id, achievement_id, etc.)
    source_id VARCHAR(100) NULL,

    -- Description
    description VARCHAR(255) NULL,

    -- Timestamp
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at)
);


-- -----------------------------------------------------------------------------
-- 6. CREATE DAILY ACTIVITY LOG
-- Track daily engagement for streaks and analytics
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS DailyActivity (
    id INT AUTO_INCREMENT PRIMARY KEY,

    user_id VARCHAR(255) NOT NULL,

    -- Activity date
    activity_date DATE NOT NULL,

    -- Engagement metrics
    lessons_started INT DEFAULT 0,
    lessons_completed INT DEFAULT 0,
    total_xp_earned INT DEFAULT 0,
    time_spent_minutes INT DEFAULT 0,

    -- Session count
    session_count INT DEFAULT 1,

    -- First and last activity timestamps
    first_activity_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- Unique constraint
    UNIQUE KEY unique_user_date (user_id, activity_date),

    INDEX idx_user_date (user_id, activity_date DESC)
);


-- -----------------------------------------------------------------------------
-- 7. SAMPLE ACHIEVEMENTS DATA
-- Insert default achievements
-- -----------------------------------------------------------------------------

-- Note: Run this INSERT only once, or use INSERT IGNORE
INSERT IGNORE INTO UserAchievements (user_id, achievement_id, achievement_name, achievement_description, achievement_icon, xp_bonus, earned_at)
SELECT 'TEMPLATE', 'first_lesson', 'First Step', 'Complete your first lesson', 'rocket', 25, NULL
FROM dual WHERE NOT EXISTS (SELECT 1 FROM UserAchievements WHERE achievement_id = 'first_lesson' AND user_id = 'TEMPLATE');

-- Achievement definitions (stored as templates with user_id='TEMPLATE')
-- These serve as a reference for the application code


-- -----------------------------------------------------------------------------
-- 8. STORED PROCEDURE: Update User Level
-- Automatically calculates and updates user level based on XP
-- -----------------------------------------------------------------------------

DELIMITER //

CREATE PROCEDURE IF NOT EXISTS UpdateUserLevel(IN p_user_id VARCHAR(255))
BEGIN
    DECLARE v_total_xp INT;
    DECLARE v_new_level INT;

    -- Get current total XP
    SELECT COALESCE(total_xp, 0) INTO v_total_xp FROM Users WHERE user_id = p_user_id;

    -- Calculate level based on XP thresholds
    SET v_new_level = CASE
        WHEN v_total_xp >= 12000 THEN 10
        WHEN v_total_xp >= 9000 THEN 9
        WHEN v_total_xp >= 6500 THEN 8
        WHEN v_total_xp >= 4500 THEN 7
        WHEN v_total_xp >= 3000 THEN 6
        WHEN v_total_xp >= 1800 THEN 5
        WHEN v_total_xp >= 1000 THEN 4
        WHEN v_total_xp >= 500 THEN 3
        WHEN v_total_xp >= 200 THEN 2
        ELSE 1
    END;

    -- Update user level
    UPDATE Users SET current_level = v_new_level WHERE user_id = p_user_id;
END //

DELIMITER ;


-- -----------------------------------------------------------------------------
-- 9. STORED PROCEDURE: Update Streak
-- Manages daily streak logic
-- -----------------------------------------------------------------------------

DELIMITER //

CREATE PROCEDURE IF NOT EXISTS UpdateStreak(IN p_user_id VARCHAR(255))
BEGIN
    DECLARE v_last_streak DATE;
    DECLARE v_current_streak INT;
    DECLARE v_today DATE;

    SET v_today = CURDATE();

    -- Get current streak info
    SELECT last_streak_date, COALESCE(streak_days, 0)
    INTO v_last_streak, v_current_streak
    FROM Users WHERE user_id = p_user_id;

    -- Update streak logic
    IF v_last_streak IS NULL OR v_last_streak < DATE_SUB(v_today, INTERVAL 1 DAY) THEN
        -- Streak broken or first time - reset to 1
        UPDATE Users
        SET streak_days = 1, last_streak_date = v_today
        WHERE user_id = p_user_id;
    ELSEIF v_last_streak = DATE_SUB(v_today, INTERVAL 1 DAY) THEN
        -- Consecutive day - increment streak
        UPDATE Users
        SET streak_days = streak_days + 1, last_streak_date = v_today
        WHERE user_id = p_user_id;
    END IF;
    -- If v_last_streak = v_today, do nothing (already logged today)
END //

DELIMITER ;


-- -----------------------------------------------------------------------------
-- 10. TRIGGER: Auto-update course progress on lesson completion
-- -----------------------------------------------------------------------------

DELIMITER //

CREATE TRIGGER IF NOT EXISTS after_lesson_progress_update
AFTER UPDATE ON LessonProgress
FOR EACH ROW
BEGIN
    DECLARE v_total INT;
    DECLARE v_completed INT;
    DECLARE v_mastered INT;
    DECLARE v_percent DECIMAL(5,2);
    DECLARE v_status VARCHAR(20);

    -- Only process if status changed to completed or mastered
    IF NEW.status IN ('completed', 'mastered') AND OLD.status NOT IN ('completed', 'mastered') THEN

        -- Count lessons for this course
        SELECT COUNT(*) INTO v_total
        FROM LessonProgress WHERE user_id = NEW.user_id AND course_id = NEW.course_id;

        SELECT COUNT(*) INTO v_completed
        FROM LessonProgress
        WHERE user_id = NEW.user_id AND course_id = NEW.course_id AND status IN ('completed', 'mastered');

        SELECT COUNT(*) INTO v_mastered
        FROM LessonProgress
        WHERE user_id = NEW.user_id AND course_id = NEW.course_id AND status = 'mastered';

        -- Calculate percentage
        IF v_total > 0 THEN
            SET v_percent = (v_completed / v_total) * 100;
        ELSE
            SET v_percent = 0;
        END IF;

        -- Determine course status
        IF v_completed = v_total AND v_mastered = v_total THEN
            SET v_status = 'mastered';
        ELSEIF v_completed = v_total THEN
            SET v_status = 'completed';
        ELSEIF v_completed > 0 THEN
            SET v_status = 'in_progress';
        ELSE
            SET v_status = 'not_started';
        END IF;

        -- Update course progress
        INSERT INTO CourseProgress (user_id, course_id, subject, total_lessons, completed_lessons, mastered_lessons, completion_percent, status)
        VALUES (NEW.user_id, NEW.course_id, '', v_total, v_completed, v_mastered, v_percent, v_status)
        ON DUPLICATE KEY UPDATE
            completed_lessons = v_completed,
            mastered_lessons = v_mastered,
            completion_percent = v_percent,
            status = v_status,
            last_accessed_at = CURRENT_TIMESTAMP;

    END IF;
END //

DELIMITER ;


-- =============================================================================
-- MIGRATION NOTES
-- =============================================================================
--
-- To run these updates on your TiDB Cloud database:
--
-- 1. Connect to your database using the TiDB Cloud console or MySQL client
-- 2. Run each section one at a time to ensure no errors
-- 3. The ALTER TABLE statements use "IF NOT EXISTS" for safety
-- 4. Stored procedures may need to be created without the IF NOT EXISTS
--    depending on your MySQL/TiDB version
--
-- For TiDB Cloud specifically:
-- - Triggers are supported but may have limitations
-- - Stored procedures work similarly to MySQL
-- - The DELIMITER command may not be needed in some clients
--
-- =============================================================================
