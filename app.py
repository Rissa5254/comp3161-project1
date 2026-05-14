from flask import Flask, jsonify, request, make_response
from dotenv import load_dotenv
import os
import mysql.connector


load_dotenv()

app = Flask(__name__)

def get_db_connection():
     conn = mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )
     return conn


# 5. Register for Course
@app.route('/courses/<int:course_id>/assign-lecturer', methods=['POST'])
def assign_lecturer(course_id):
    """Assign a lecturer to a course."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        data = request.get_json()
        lecturer_id = data.get('lecturerID')
        
        if not lecturer_id:
            return jsonify({"message": "Please select a lecturer."}), 400
        
        # Check if course exists
        cursor.execute("SELECT * FROM course WHERE courseID=%s", (course_id,))
        course = cursor.fetchone()
        if not course:
            return jsonify({"error": "Course not found."}), 404
        
        # Check if a lecturer exists
        
        cursor.execute("SELECT * FROM course_maintainer WHERE courseID=%s", (course_id,))
        lecturer = cursor.fetchone()
        if not lecturer:
            return jsonify({"error": "Lecturer not found."}), 404
        
        # Check is a lecturer is already assigned to a course
        cursor.execute("SELECT * FROM course_maintainer WHERE lectuereID=%s AND courseID=%s", (lecturer_id, course_id,))
        teaches = cursor.fetchone()
        if teaches:
            return jsonify({"message": "Lecturer is already assigned."}), 400
        
        # Check is a lecturer is assigned to 3 or more courses
        cursor.execute("SELECT COUNT(courseID) FROM  course_maintainer WHERE lecturerID=%s", (lecturer_id,))
        course_count = cursor.fetchone()[0]
        
        if course_count >=3:
            return jsonify({"message": "Lecturer already assigned to 3 courses."}), 400
        
        # Assign lecturer
        cursor.execute("INSERT INTO course_maintainer(lecturerID, courseID) VALUES (%s, %s)", (lecturer_id, course_id))
        conn.commit()
        
        return make_response({"message": f"Lecturer successfully assigned to course {course_id}."}), 201
    except Exception as e:
        print(e)
        return make_response({'error': str(e)}, 500)
    
    finally:
        cursor.close()
        conn.close()
    
    
# @app.route('/courses/<int:course_id>/register-student', methods=['POST'])
# def register_student():
#     """Register students for a course."""
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor(dictionary=True)
#         
#         data = request.get_json()
#         student_id = data.get('userID')
        
    
    

# # 6. Retrieve Members
# @app.route()
# def members():
#     """Return members of a particular course."""
    
    
# # 7. Retrieve Calendar Events
# @app.route()
# def retrieve_calender():
#     """Retrieve all calendar events for a particular course."""
#     
#     
#     """Retrieve all calendar events for a particular date for a particular student.""" 


# 8. Create Calendar Events 
# @app.route()
# def create_calendar():
#     """Create a calendar event for a course."""
   
# 9. Forums
@app.route("/api/forums/course/<int:course_id>", methods=["GET"])
def get_forums(course_id):
    """Retrieve all forums for a particular course."""
    conn   = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT f.forumID, f.courseID, f.forumName, f.description,
                   c.courseCode, c.courseName
            FROM   discussion_forum f
            JOIN   course c ON c.courseID = f.courseID
            WHERE  f.courseID = %s
            """,
            (course_id,),
        )
        return jsonify({"success": True, "data": cursor.fetchall()}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
 
 
@app.route("/api/forums/course/<int:course_id>", methods=["POST"])
def create_forum(course_id):
    """Create a new forum for a particular course."""
    body        = request.get_json() or {}
    forum_name  = body.get("forumName")
    description = body.get("description")
 
    if not forum_name:
        return jsonify({"success": False, "message": "forumName is required."}), 400
 
    conn   = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT courseID FROM course WHERE courseID = %s", (course_id,))
        if not cursor.fetchone():
            return jsonify({"success": False, "message": "Course not found."}), 404
 
        cursor.execute(
            """
            INSERT INTO discussion_forum (courseID, forumName, description)
            VALUES (%s, %s, %s)
            """,
            (course_id, forum_name, description),
        )
        conn.commit()
        return jsonify({
            "success": True,
            "message": "Forum created successfully.",
            "data": {
                "forumID":     cursor.lastrowid,
                "courseID":    course_id,
                "forumName":   forum_name,
                "description": description,
            },
        }), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
 
 
# 10. Discussion Thread
@app.route("/api/threads/forum/<int:forum_id>", methods=["GET"])
def get_threads(forum_id):
    """Retrieve all discussion threads (nested) for a particular forum."""
    conn   = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT forumID FROM discussion_forum WHERE forumID = %s", (forum_id,)
        )
        if not cursor.fetchone():
            return jsonify({"success": False, "message": "Forum not found."}), 404
 
        cursor.execute(
            """
            SELECT t.threadID, t.forumID, t.parentThreadID,
                   t.title, t.content, t.createdAt,
                   u.userID AS authorID, u.username,
                   u.firstName, u.lastName
            FROM   thread t
            JOIN   user   u ON u.userID = t.authorID
            WHERE  t.forumID = %s
            ORDER  BY t.createdAt ASC
            """,
            (forum_id,),
        )
        rows = cursor.fetchall()
        for row in rows:
            if row.get("createdAt"):
                row["createdAt"] = str(row["createdAt"])
 
        return jsonify({"success": True, "data": nest_threads(rows)}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
 
 
@app.route("/api/threads/forum/<int:forum_id>", methods=["POST"])
def create_thread(forum_id):
    """Add a new top-level discussion thread to a forum."""
    body      = request.get_json() or {}
    author_id = body.get("authorID")
    title     = body.get("title")
    content   = body.get("content")
 
    if not all([author_id, title, content]):
        return jsonify({
            "success": False,
            "message": "authorID, title, and content are required.",
        }), 400
 
    conn   = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT forumID FROM discussion_forum WHERE forumID = %s", (forum_id,)
        )
        if not cursor.fetchone():
            return jsonify({"success": False, "message": "Forum not found."}), 404
 
        cursor.execute(
            """
            INSERT INTO thread (forumID, parentThreadID, authorID, title, content)
            VALUES (%s, NULL, %s, %s, %s)
            """,
            (forum_id, author_id, title, content),
        )
        conn.commit()
        return jsonify({
            "success": True,
            "message": "Thread created successfully.",
            "data": {
                "threadID":       cursor.lastrowid,
                "forumID":        forum_id,
                "parentThreadID": None,
                "authorID":       author_id,
                "title":          title,
                "content":        content,
            },
        }), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
 
 
@app.route("/api/threads/<int:thread_id>/reply", methods=["POST"])
def reply_to_thread(thread_id):
    """Reply to any thread or reply — unlimited depth, like Reddit."""
    body      = request.get_json() or {}
    author_id = body.get("authorID")
    title     = body.get("title")
    content   = body.get("content")
 
    if not all([author_id, title, content]):
        return jsonify({
            "success": False,
            "message": "authorID, title, and content are required.",
        }), 400
 
    conn   = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT threadID, forumID FROM thread WHERE threadID = %s", (thread_id,)
        )
        parent = cursor.fetchone()
        if not parent:
            return jsonify({"success": False, "message": "Parent thread not found."}), 404
 
        forum_id = parent["forumID"]
        cursor.execute(
            """
            INSERT INTO thread (forumID, parentThreadID, authorID, title, content)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (forum_id, thread_id, author_id, title, content),
        )
        conn.commit()
        return jsonify({
            "success": True,
            "message": "Reply posted successfully.",
            "data": {
                "threadID":       cursor.lastrowid,
                "forumID":        forum_id,
                "parentThreadID": thread_id,
                "authorID":       author_id,
                "title":          title,
                "content":        content,
            },
        }), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
 
 
# 11. Course Content
@app.route("/api/content/course/<int:course_id>", methods=["GET"])
def get_course_content(course_id):
    """Retrieve all sections and their items for a course."""
    conn   = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT courseID, courseCode, courseName FROM course WHERE courseID = %s",
            (course_id,),
        )
        course = cursor.fetchone()
        if not course:
            return jsonify({"success": False, "message": "Course not found."}), 404
 
        cursor.execute(
            """
            SELECT sectionID, sectionTitle, description, orderIndex
            FROM   section
            WHERE  courseID = %s
            ORDER  BY orderIndex ASC
            """,
            (course_id,),
        )
        sections = cursor.fetchall()
 
        if sections:
            section_ids  = [s["sectionID"] for s in sections]
            placeholders = ", ".join(["%s"] * len(section_ids))
            cursor.execute(
                f"""
                SELECT itemID, sectionID, itemTitle, itemType,
                       content, filePath, url, orderIndex
                FROM   section_item
                WHERE  sectionID IN ({placeholders})
                ORDER  BY sectionID, orderIndex ASC
                """,
                section_ids,
            )
            item_map = {}
            for item in cursor.fetchall():
                item_map.setdefault(item["sectionID"], []).append(item)
            for sec in sections:
                sec["items"] = item_map.get(sec["sectionID"], [])
 
        return jsonify({
            "success": True,
            "data": {"course": course, "sections": sections},
        }), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
 
 
@app.route("/api/content/course/<int:course_id>/sections", methods=["POST"])
def create_section(course_id):
    """Lecturer adds a new section to a course."""
    body          = request.get_json() or {}
    lecturer_id   = body.get("lecturerID")
    section_title = body.get("sectionTitle")
    description   = body.get("description")
    order_index   = body.get("orderIndex", 1)
 
    if not lecturer_id or not section_title:
        return jsonify({
            "success": False,
            "message": "lecturerID and sectionTitle are required.",
        }), 400
 
    conn   = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT maintainerID FROM course_maintainer
            WHERE  lecturerID = %s AND courseID = %s
            """,
            (lecturer_id, course_id),
        )
        if not cursor.fetchone():
            return jsonify({
                "success": False,
                "message": "You are not the lecturer for this course.",
            }), 403
 
        cursor.execute(
            """
            INSERT INTO section (courseID, sectionTitle, description, orderIndex)
            VALUES (%s, %s, %s, %s)
            """,
            (course_id, section_title, description, order_index),
        )
        conn.commit()
        return jsonify({
            "success": True,
            "message": "Section created successfully.",
            "data": {
                "sectionID":    cursor.lastrowid,
                "courseID":     course_id,
                "sectionTitle": section_title,
                "description":  description,
                "orderIndex":   order_index,
            },
        }), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
 
 
@app.route("/api/content/sections/<int:section_id>/items", methods=["POST"])
def create_section_item(section_id):
    """Lecturer adds a content item (link, file, slide, assignment) to a section."""
    body        = request.get_json() or {}
    lecturer_id = body.get("lecturerID")
    item_title  = body.get("itemTitle")
    item_type   = body.get("itemType")
    content     = body.get("content")
    file_path   = body.get("filePath")
    url         = body.get("url")
    order_index = body.get("orderIndex", 1)
 
    if not lecturer_id or not item_title or not item_type:
        return jsonify({
            "success": False,
            "message": "lecturerID, itemTitle, and itemType are required.",
        }), 400
 
    valid_types = {"link", "file", "slide", "assignment"}
    if item_type not in valid_types:
        return jsonify({
            "success": False,
            "message": f"itemType must be one of: {', '.join(valid_types)}.",
        }), 400
 
    conn   = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT courseID FROM section WHERE sectionID = %s", (section_id,)
        )
        section = cursor.fetchone()
        if not section:
            return jsonify({"success": False, "message": "Section not found."}), 404
 
        cursor.execute(
            """
            SELECT maintainerID FROM course_maintainer
            WHERE  lecturerID = %s AND courseID = %s
            """,
            (lecturer_id, section["courseID"]),
        )
        if not cursor.fetchone():
            return jsonify({
                "success": False,
                "message": "You are not the lecturer for this course.",
            }), 403
 
        cursor.execute(
            """
            INSERT INTO section_item
                (sectionID, itemTitle, itemType, content, filePath, url, orderIndex)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (section_id, item_title, item_type, content, file_path, url, order_index),
        )
        conn.commit()
        return jsonify({
            "success": True,
            "message": "Content item added successfully.",
            "data": {
                "itemID":     cursor.lastrowid,
                "sectionID":  section_id,
                "itemTitle":  item_title,
                "itemType":   item_type,
                "content":    content,
                "filePath":   file_path,
                "url":        url,
                "orderIndex": order_index,
            },
        }), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
 
 
# 12. Assignments
@app.route("/api/assignments/course/<int:course_id>", methods=["GET"])
def get_course_assignments(course_id):
    """List all assignment events for a course with submission counts."""
    conn   = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT ce.eventID, ce.eventTitle, ce.description,
                   ce.eventDate, ce.dueDate,
                   COUNT(s.submissionID) AS submissionCount
            FROM   calendar_event ce
            LEFT JOIN submission s ON s.eventID = ce.eventID
            WHERE  ce.courseID = %s AND ce.eventType = 'Assignment'
            GROUP  BY ce.eventID
            """,
            (course_id,),
        )
        rows = cursor.fetchall()
        for row in rows:
            for key in ("eventDate", "dueDate"):
                if row.get(key):
                    row[key] = str(row[key])
        return jsonify({"success": True, "data": rows}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
 
 
@app.route("/api/assignments/<int:event_id>/submit", methods=["POST"])
def submit_assignment(event_id):
    """A student submits an assignment."""
    body       = request.get_json() or {}
    student_id = body.get("studentID")
    file_path  = body.get("filePath")
    comments   = body.get("comments")
 
    if not student_id:
        return jsonify({"success": False, "message": "studentID is required."}), 400
 
    conn   = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT eventID, courseID FROM calendar_event
            WHERE  eventID = %s AND eventType = 'Assignment'
            """,
            (event_id,),
        )
        event = cursor.fetchone()
        if not event:
            return jsonify({"success": False, "message": "Assignment event not found."}), 404
 
        cursor.execute(
            "SELECT enrollmentID FROM enrollment WHERE studentID = %s AND courseID = %s",
            (student_id, event["courseID"]),
        )
        if not cursor.fetchone():
            return jsonify({
                "success": False,
                "message": "Student is not enrolled in this course.",
            }), 403
 
        # Upsert — update if already submitted
        cursor.execute(
            "SELECT submissionID FROM submission WHERE studentID = %s AND eventID = %s",
            (student_id, event_id),
        )
        existing = cursor.fetchone()
        if existing:
            cursor.execute(
                """
                UPDATE submission
                SET    submissionDate = NOW(), filePath = %s, comments = %s
                WHERE  studentID = %s AND eventID = %s
                """,
                (file_path, comments, student_id, event_id),
            )
            conn.commit()
            return jsonify({
                "success": True,
                "message": "Submission updated successfully.",
                "data": {"submissionID": existing["submissionID"]},
            }), 200
 
        cursor.execute(
            """
            INSERT INTO submission (studentID, eventID, submissionDate, filePath, comments)
            VALUES (%s, %s, NOW(), %s, %s)
            """,
            (student_id, event_id, file_path, comments),
        )
        conn.commit()
        return jsonify({
            "success": True,
            "message": "Assignment submitted successfully.",
            "data": {
                "submissionID": cursor.lastrowid,
                "studentID":    student_id,
                "eventID":      event_id,
            },
        }), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
 
 
@app.route("/api/assignments/<int:event_id>/grade/<int:student_id>", methods=["PATCH"])
def grade_assignment(event_id, student_id):
    """A lecturer submits a grade for a student's assignment submission."""
    body        = request.get_json() or {}
    lecturer_id = body.get("lecturerID")
    grade       = body.get("grade")
    feedback    = body.get("feedback")
 
    if lecturer_id is None or grade is None:
        return jsonify({
            "success": False,
            "message": "lecturerID and grade are required.",
        }), 400
 
    try:
        grade = float(grade)
        if not (0 <= grade <= 100):
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({
            "success": False,
            "message": "grade must be a number between 0 and 100.",
        }), 400
 
    conn   = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT courseID FROM calendar_event WHERE eventID = %s", (event_id,)
        )
        event = cursor.fetchone()
        if not event:
            return jsonify({"success": False, "message": "Assignment event not found."}), 404
 
        cursor.execute(
            """
            SELECT maintainerID FROM course_maintainer
            WHERE  lecturerID = %s AND courseID = %s
            """,
            (lecturer_id, event["courseID"]),
        )
        if not cursor.fetchone():
            return jsonify({
                "success": False,
                "message": "You are not the lecturer for this course.",
            }), 403
 
        cursor.execute(
            "SELECT submissionID FROM submission WHERE studentID = %s AND eventID = %s",
            (student_id, event_id),
        )
        submission = cursor.fetchone()
        if not submission:
            return jsonify({
                "success": False,
                "message": "No submission found for this student and assignment.",
            }), 404
 
        cursor.execute(
            "UPDATE submission SET grade = %s, feedback = %s WHERE studentID = %s AND eventID = %s",
            (grade, feedback, student_id, event_id),
        )
        conn.commit()
        return jsonify({
            "success": True,
            "message": "Grade recorded successfully.",
            "data": {
                "submissionID": submission["submissionID"],
                "studentID":    student_id,
                "eventID":      event_id,
                "grade":        grade,
            },
        }), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
 
 
@app.route("/api/assignments/student/<int:student_id>/average", methods=["GET"])
def get_student_average(student_id):
    """Get a student's overall grade average across all graded submissions."""
    conn   = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT u.userID, u.username, u.firstName, u.lastName,
                   ROUND(AVG(s.grade), 2) AS overallAverage,
                   COUNT(s.submissionID)  AS gradedSubmissions
            FROM   user u
            JOIN   submission s ON s.studentID = u.userID
            WHERE  u.userID = %s AND s.grade IS NOT NULL
            GROUP  BY u.userID
            """,
            (student_id,),
        )
        row = cursor.fetchone()
        if not row:
            return jsonify({
                "success": False,
                "message": "No graded submissions found for this student.",
            }), 404
        return jsonify({"success": True, "data": row}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
 
 
# 13. Reports
@app.route("/api/reports/courses-50-plus-students", methods=["GET"])
def courses_50_plus_students():
    """All courses with 50 or more students. (vw_courses_50_plus_students)"""
    conn   = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT courseID, courseCode, courseName, studentCount
            FROM   vw_courses_50_plus_students
            ORDER  BY studentCount DESC
            """
        )
        rows = cursor.fetchall()
        return jsonify({"success": True, "count": len(rows), "data": rows}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
 
 
@app.route("/api/reports/students-5-plus-courses", methods=["GET"])
def students_5_plus_courses():
    """All students enrolled in 5 or more courses. (vw_students_5_plus_courses)"""
    conn   = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT userID, username, firstName, lastName, courseCount
            FROM   vw_students_5_plus_courses
            ORDER  BY courseCount DESC
            """
        )
        rows = cursor.fetchall()
        return jsonify({"success": True, "count": len(rows), "data": rows}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
 
 
@app.route("/api/reports/lecturers-3-plus-courses", methods=["GET"])
def lecturers_3_plus_courses():
    """All lecturers teaching 3 or more courses. (vw_lecturers_3_plus_courses)"""
    conn   = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT userID, username, firstName, lastName, courseCount
            FROM   vw_lecturers_3_plus_courses
            ORDER  BY courseCount DESC
            """
        )
        rows = cursor.fetchall()
        return jsonify({"success": True, "count": len(rows), "data": rows}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
 
 
@app.route("/api/reports/top-10-enrolled-courses", methods=["GET"])
def top_10_enrolled_courses():
    """The 10 most enrolled courses. (vw_top10_enrolled_courses)"""
    conn   = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT courseID, courseCode, courseName, enrollmentCount
            FROM   vw_top10_enrolled_courses
            """
        )
        rows = cursor.fetchall()
        return jsonify({"success": True, "data": rows}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
 
 
@app.route("/api/reports/top-10-students-by-average", methods=["GET"])
def top_10_students_by_average():
    """Top 10 students by overall grade average. (vw_top10_students_by_average)"""
    conn   = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT userID, username, firstName, lastName, overallAverage
            FROM   vw_top10_students_by_average
            """
        )
        rows = cursor.fetchall()
        return jsonify({"success": True, "data": rows}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()