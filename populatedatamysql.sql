

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS user (
    userID     INT AUTO_INCREMENT PRIMARY KEY,
    username   VARCHAR(50)  NOT NULL UNIQUE,
    password   VARCHAR(100) NOT NULL,
    email      VARCHAR(100) NOT NULL UNIQUE,
    firstName  VARCHAR(50),
    lastName   VARCHAR(50),
    userType   VARCHAR(20)  NOT NULL,   -- 'admin','lecturer','student'
    createdAt  DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS course (
    courseID    INT AUTO_INCREMENT PRIMARY KEY,
    courseCode  VARCHAR(20)  NOT NULL UNIQUE,
    courseName  VARCHAR(100) NOT NULL,
    description TEXT,
    semester    VARCHAR(10),
    year        INT,
    createdBy   INT,
    FOREIGN KEY (createdBy) REFERENCES user(userID)
);

CREATE TABLE IF NOT EXISTS enrollment (
    enrollmentID   INT AUTO_INCREMENT PRIMARY KEY,
    studentID      INT NOT NULL,
    courseID       INT NOT NULL,
    enrollmentDate DATE,
    UNIQUE KEY uq_enrollment (studentID, courseID),
    FOREIGN KEY (studentID) REFERENCES user(userID),
    FOREIGN KEY (courseID)  REFERENCES course(courseID)
);

CREATE TABLE IF NOT EXISTS course_maintainer (
    maintainerID INT AUTO_INCREMENT PRIMARY KEY,
    lecturerID   INT NOT NULL,
    courseID     INT NOT NULL,
    role         VARCHAR(50) DEFAULT 'lecturer',
    UNIQUE KEY uq_maintainer (courseID),   -- enforces 1 lecturer per course
    FOREIGN KEY (lecturerID) REFERENCES user(userID),
    FOREIGN KEY (courseID)   REFERENCES course(courseID)
);

CREATE TABLE IF NOT EXISTS discussion_forum (
    forumID    INT AUTO_INCREMENT PRIMARY KEY,
    courseID   INT NOT NULL,
    forumName  VARCHAR(100) NOT NULL,
    description TEXT,
    FOREIGN KEY (courseID) REFERENCES course(courseID)
);

CREATE TABLE IF NOT EXISTS thread (
    threadID       INT AUTO_INCREMENT PRIMARY KEY,
    forumID        INT  NOT NULL,
    parentThreadID INT,
    authorID       INT  NOT NULL,
    title          VARCHAR(200) NOT NULL,
    content        TEXT NOT NULL,
    createdAt      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (forumID)        REFERENCES discussion_forum(forumID),
    FOREIGN KEY (parentThreadID) REFERENCES thread(threadID),
    FOREIGN KEY (authorID)       REFERENCES user(userID)
);

CREATE TABLE IF NOT EXISTS calendar_event (
    eventID     INT AUTO_INCREMENT PRIMARY KEY,
    courseID    INT          NOT NULL,
    eventTitle  VARCHAR(100) NOT NULL,
    description TEXT,
    eventType   VARCHAR(20),    -- 'Lecture','Assignment','Exam','Other'
    eventDate   DATETIME,
    dueDate     DATETIME,
    createdBy   INT,
    FOREIGN KEY (courseID)   REFERENCES course(courseID),
    FOREIGN KEY (createdBy)  REFERENCES user(userID)
);

CREATE TABLE IF NOT EXISTS section (
    sectionID    INT AUTO_INCREMENT PRIMARY KEY,
    courseID     INT          NOT NULL,
    sectionTitle VARCHAR(100) NOT NULL,
    description  TEXT,
    orderIndex   INT NOT NULL DEFAULT 1,
    FOREIGN KEY (courseID) REFERENCES course(courseID)
);

CREATE TABLE IF NOT EXISTS section_item (
    itemID     INT AUTO_INCREMENT PRIMARY KEY,
    sectionID  INT          NOT NULL,
    itemTitle  VARCHAR(100) NOT NULL,
    itemType   VARCHAR(20),     -- 'link','file','slide','assignment'
    content    TEXT,
    filePath   VARCHAR(255),
    url        VARCHAR(255),
    orderIndex INT NOT NULL DEFAULT 1,
    FOREIGN KEY (sectionID) REFERENCES section(sectionID)
);


CREATE TABLE IF NOT EXISTS submission (
    submissionID   INT AUTO_INCREMENT PRIMARY KEY,
    studentID      INT NOT NULL,
    eventID        INT NOT NULL,
    submissionDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    filePath       VARCHAR(255),
    comments       TEXT,
    grade          DECIMAL(5,2),
    feedback       TEXT,
    UNIQUE KEY uq_submission (studentID, eventID),
    FOREIGN KEY (studentID) REFERENCES user(userID),
    FOREIGN KEY (eventID)   REFERENCES calendar_event(eventID)
);

CREATE TABLE IF NOT EXISTS announcement (
    announcementID INT AUTO_INCREMENT PRIMARY KEY,
    courseID       INT          NOT NULL,
    title          VARCHAR(100) NOT NULL,
    content        TEXT,
    priority       VARCHAR(20) DEFAULT 'Normal',  -- 'Low','Normal','High'
    postedBy       INT,
    postedAt       DATETIME DEFAULT CURRENT_TIMESTAMP,
    expiresAt      DATETIME,
    FOREIGN KEY (courseID)  REFERENCES course(courseID),
    FOREIGN KEY (postedBy)  REFERENCES user(userID)
);

CREATE TABLE IF NOT EXISTS notification (
    notificationID   INT AUTO_INCREMENT PRIMARY KEY,
    userID           INT  NOT NULL,
    message          TEXT,
    notificationType VARCHAR(20),  -- 'Assignment','Grade','Announcement','Forum'
    isRead           TINYINT(1) DEFAULT 0,
    createdAt        DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (userID) REFERENCES user(userID)
);



CREATE OR REPLACE VIEW vw_courses_50_plus_students AS
SELECT c.courseID, c.courseCode, c.courseName, COUNT(e.studentID) AS studentCount
FROM course c
JOIN enrollment e ON e.courseID = c.courseID
GROUP BY c.courseID, c.courseCode, c.courseName
HAVING COUNT(e.studentID) >= 50;

CREATE OR REPLACE VIEW vw_students_5_plus_courses AS
SELECT u.userID, u.username, u.firstName, u.lastName,
       COUNT(e.courseID) AS courseCount
FROM user u
JOIN enrollment e ON e.studentID = u.userID
WHERE u.userType = 'student'
GROUP BY u.userID, u.username, u.firstName, u.lastName
HAVING COUNT(e.courseID) >= 5;

CREATE OR REPLACE VIEW vw_lecturers_3_plus_courses AS
SELECT u.userID, u.username, u.firstName, u.lastName,
       COUNT(cm.courseID) AS courseCount
FROM user u
JOIN course_maintainer cm ON cm.lecturerID = u.userID
WHERE u.userType = 'lecturer'
GROUP BY u.userID, u.username, u.firstName, u.lastName
HAVING COUNT(cm.courseID) >= 3;

CREATE OR REPLACE VIEW vw_top10_enrolled_courses AS
SELECT c.courseID, c.courseCode, c.courseName,
       COUNT(e.studentID) AS enrollmentCount
FROM course c
LEFT JOIN enrollment e ON e.courseID = c.courseID
GROUP BY c.courseID, c.courseCode, c.courseName
ORDER BY enrollmentCount DESC 
LIMIT 10;


CREATE OR REPLACE VIEW vw_top10_students_by_average AS
SELECT u.userID, u.username, u.firstName, u.lastName,
       ROUND(AVG(s.grade), 2) AS overallAverage
FROM user u
JOIN submission s ON s.studentID = u.userID
WHERE u.userType = 'student'
  AND s.grade IS NOT NULL
GROUP BY u.userID, u.username, u.firstName, u.lastName
ORDER BY overallAverage DESC
LIMIT 10;

-- Creates the default admin account used for system management and course creation.
INSERT IGNORE INTO user (username, password, email, firstName, lastName, userType)
VALUES ('admin01', 'hashedpassword_admin', 'admin@university.edu', 'System', 'Admin', 'admin');


-- Generates 200 lecturer accounts using a loop with unique usernames and emails.
-- Ensures lecturers are available to be assigned to courses.
DROP PROCEDURE IF EXISTS insert_lecturers;
DELIMITER $$
CREATE PROCEDURE insert_lecturers()
BEGIN
    DECLARE i INT DEFAULT 1;
    WHILE i <= 200 DO
        INSERT IGNORE INTO user (username, password, email, firstName, lastName, userType)
        VALUES (
            CONCAT('lecturer', LPAD(i, 3, '0')),
            CONCAT('hashedpassword_lec', i),
            CONCAT('lecturer', i, '@university.edu'),
            CONCAT('LecFirst', i),
            CONCAT('LecLast', i),
            'lecturer'
        );
        SET i = i + 1;
    END WHILE;
END$$
DELIMITER ;
CALL insert_lecturers();


-- Generates 100,000 student accounts using a stored procedure loop.
-- Satisfies the requirement for large-scale student data population.
DROP PROCEDURE IF EXISTS insert_students;
DELIMITER $$
CREATE PROCEDURE insert_students()
BEGIN
    DECLARE i INT DEFAULT 1;
    DECLARE start_from INT;
    SELECT COUNT(*) + 1 INTO start_from FROM user WHERE userType = 'student';
    SET i = start_from;
    WHILE i <= 100000 DO
        INSERT IGNORE INTO user (username, password, email, firstName, lastName, userType)
        VALUES (
            CONCAT('student', LPAD(i, 6, '0')),
            CONCAT('hashedpassword_stu', i),
            CONCAT('student', i, '@university.edu'),
            CONCAT('StuFirst', i),
            CONCAT('StuLast', i),
            'student'
        );
        SET i = i + 1;
    END WHILE;
END$$
DELIMITER ;
CALL insert_students();


-- Creates 200 courses with unique course codes and metadata.
-- Forms the core dataset for enrollment and teaching assignments.
DROP PROCEDURE IF EXISTS insert_courses;
DELIMITER $$
CREATE PROCEDURE insert_courses()
BEGIN
    DECLARE i INT DEFAULT 1;
    WHILE i <= 200 DO
        INSERT IGNORE INTO course (courseCode, courseName, description, semester, year, createdBy)
        VALUES (
            CONCAT('CRS', LPAD(i, 4, '0')),
            CONCAT('Course ', i),
            CONCAT('Description for Course ', i),
            'Semester 1',
            2025,
            1
        );
        SET i = i + 1;
    END WHILE;
END$$
DELIMITER ;
CALL insert_courses();


-- Assigns one lecturer to each course using course_maintainer table.
-- Enforces the constraint that each course has exactly one lecturer.
DROP PROCEDURE IF EXISTS assign_lecturers;
DELIMITER $$
CREATE PROCEDURE assign_lecturers()
BEGIN
    DECLARE i INT DEFAULT 1;
    DECLARE lec_id INT;
    DECLARE crs_id INT;
    WHILE i <= 200 DO
        SET lec_id = 1 + i;
        SELECT courseID INTO crs_id FROM course WHERE courseCode = CONCAT('CRS', LPAD(i, 4, '0')) LIMIT 1;
        INSERT IGNORE INTO course_maintainer (lecturerID, courseID, role)
        VALUES (lec_id, crs_id, 'lecturer');
        SET i = i + 1;
    END WHILE;
END$$
DELIMITER ;
CALL assign_lecturers();


-- Enrolls students into courses while enforcing 3–6 course constraints per student.
-- Uses temporary tables to evenly distribute enrollments across courses.
DROP PROCEDURE IF EXISTS enroll_students;
DELIMITER $$
CREATE PROCEDURE enroll_students()
BEGIN
    DROP TEMPORARY TABLE IF EXISTS tmp_students;
    CREATE TEMPORARY TABLE tmp_students AS
        SELECT userID, (ROW_NUMBER() OVER (ORDER BY userID) - 1) AS rn
        FROM user WHERE userType = 'student';

    DROP TEMPORARY TABLE IF EXISTS tmp_courses;
    CREATE TEMPORARY TABLE tmp_courses AS
        SELECT courseID, (ROW_NUMBER() OVER (ORDER BY courseID) - 1) AS rn
        FROM course;

    -- Pass A: slots 1-3 (all students)
    INSERT IGNORE INTO enrollment (studentID, courseID, enrollmentDate)
    SELECT s.userID, c.courseID, CURDATE()
    FROM tmp_students s JOIN tmp_courses c ON c.rn = (s.rn % 200);

    INSERT IGNORE INTO enrollment (studentID, courseID, enrollmentDate)
    SELECT s.userID, c.courseID, CURDATE()
    FROM tmp_students s JOIN tmp_courses c ON c.rn = ((s.rn + 67) % 200);

    INSERT IGNORE INTO enrollment (studentID, courseID, enrollmentDate)
    SELECT s.userID, c.courseID, CURDATE()
    FROM tmp_students s JOIN tmp_courses c ON c.rn = ((s.rn + 133) % 200);

    -- Pass B: slots 4-6 (every other student, max 6 total)
    INSERT IGNORE INTO enrollment (studentID, courseID, enrollmentDate)
    SELECT s.userID, c.courseID, CURDATE()
    FROM tmp_students s JOIN tmp_courses c ON c.rn = ((s.rn + 50) % 200)
    WHERE s.rn % 2 = 0;

    INSERT IGNORE INTO enrollment (studentID, courseID, enrollmentDate)
    SELECT s.userID, c.courseID, CURDATE()
    FROM tmp_students s JOIN tmp_courses c ON c.rn = ((s.rn + 100) % 200)
    WHERE s.rn % 2 = 0;

    INSERT IGNORE INTO enrollment (studentID, courseID, enrollmentDate)
    SELECT s.userID, c.courseID, CURDATE()
    FROM tmp_students s JOIN tmp_courses c ON c.rn = ((s.rn + 150) % 200)
    WHERE s.rn % 2 = 0;

    DROP TEMPORARY TABLE IF EXISTS tmp_students;
    DROP TEMPORARY TABLE IF EXISTS tmp_courses;
END$$
DELIMITER ;
CALL enroll_students();

-- Automatically generates academic events (assignments, exams) for each course.
-- Ensures all courses have scheduled learning activities.
INSERT IGNORE INTO calendar_event (courseID, eventTitle, description, eventType, eventDate, dueDate, createdBy)
SELECT courseID, 'Midterm Exam', 'Midterm examination', 'Exam',
       DATE_ADD(NOW(), INTERVAL 30 DAY), DATE_ADD(NOW(), INTERVAL 30 DAY), 1
FROM course;

INSERT IGNORE INTO calendar_event (courseID, eventTitle, description, eventType, eventDate, dueDate, createdBy)
SELECT courseID, 'Assignment 1', 'First assignment submission', 'Assignment',
       DATE_ADD(NOW(), INTERVAL 14 DAY), DATE_ADD(NOW(), INTERVAL 21 DAY), 1
FROM course;

INSERT IGNORE INTO calendar_event (courseID, eventTitle, description, eventType, eventDate, dueDate, createdBy)
SELECT courseID, 'Final Exam', 'Final examination', 'Exam',
       DATE_ADD(NOW(), INTERVAL 90 DAY), DATE_ADD(NOW(), INTERVAL 90 DAY), 1
FROM course;

-- Creates assignment submissions and assigns computed grades to students.
-- Simulates realistic grading data for evaluation purposes.
DROP PROCEDURE IF EXISTS insert_submissions;
DELIMITER $$
CREATE PROCEDURE insert_submissions()
BEGIN
    DROP TEMPORARY TABLE IF EXISTS tmp_assignments;
    CREATE TEMPORARY TABLE tmp_assignments AS
        SELECT ce.eventID, ce.courseID
        FROM calendar_event ce
        WHERE ce.eventType = 'Assignment';

    INSERT IGNORE INTO submission (studentID, eventID, submissionDate, filePath, grade, feedback)
    SELECT
        e.studentID,
        a.eventID,
        NOW(),
        CONCAT('uploads/sub_', e.studentID, '_', a.eventID, '.pdf'),
        ((e.studentID + a.eventID) % 41) + 60,
        'Graded'
    FROM enrollment e
    JOIN tmp_assignments a ON a.courseID = e.courseID;

    DROP TEMPORARY TABLE IF EXISTS tmp_assignments;
END$$
DELIMITER ;
CALL insert_submissions();


-- Adds structured course sections and learning materials (slides, files, links).
-- Organizes course content into accessible learning units.
INSERT IGNORE INTO section (courseID, sectionTitle, description, orderIndex)
SELECT courseID, 'Week 1 - Introduction', 'Introductory material', 1 FROM course;

INSERT IGNORE INTO section (courseID, sectionTitle, description, orderIndex)
SELECT courseID, 'Week 2 - Core Concepts', 'Core course material', 2 FROM course;


INSERT IGNORE INTO section_item (sectionID, itemTitle, itemType, url, orderIndex)
SELECT sectionID, CONCAT('Lecture Slides - ', sectionTitle), 'slide',
       CONCAT('https://university.edu/slides/', sectionID), 1
FROM section;

INSERT IGNORE INTO section_item (sectionID, itemTitle, itemType, filePath, orderIndex)
SELECT sectionID, CONCAT('Reading Material - ', sectionTitle), 'file',
       CONCAT('uploads/reading_', sectionID, '.pdf'), 2
FROM section;


-- Creates discussion forums and initial threads for each course.
-- Enables student and lecturer interaction similar to online discussion boards.
INSERT IGNORE INTO discussion_forum (courseID, forumName, description)
SELECT courseID, 'General Discussion', 'General course discussion' FROM course;

INSERT IGNORE INTO discussion_forum (courseID, forumName, description)
SELECT courseID, 'Assignment Help', 'Ask questions about assignments' FROM course;



INSERT IGNORE INTO thread (forumID, parentThreadID, authorID, title, content)
SELECT forumID, NULL, 1,
       CONCAT('Welcome to ', forumName),
       'This is the opening thread. Feel free to post here.'
FROM discussion_forum;


-- Inserts course announcements and system notifications for students.
-- Supports communication of updates and course-related information.
INSERT IGNORE INTO announcement (courseID, title, content, priority, postedBy, expiresAt)
SELECT courseID, 'Welcome to the course',
       'Welcome! Please review the course outline in Week 1.',
       'Normal', 1, DATE_ADD(NOW(), INTERVAL 30 DAY)
FROM course;


INSERT IGNORE INTO notification (userID, message, notificationType, isRead)
SELECT userID, 'A new announcement has been posted in your course.', 'Announcement', 0
FROM user WHERE userType = 'student';

SET FOREIGN_KEY_CHECKS = 1;

