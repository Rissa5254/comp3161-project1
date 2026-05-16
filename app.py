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
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        data = request.get_json()
        lecturer_id = data.get('lecturerID')
        
        if not lecturer_id:
            return jsonify({"message": "Lecturer ID required."}), 400
        
        # Check if course exists
        cursor.execute("SELECT * FROM course WHERE courseID=%s", (course_id,))
        course = cursor.fetchone()
        if not course:
            return jsonify({"error": "Course not found."}), 404
        
        # Check if a lecturer exists and is a lecturer
        cursor.execute("SELECT * FROM user WHERE userID=%s AND userType = 'lecturer'", (lecturer_id,))
        lecturer = cursor.fetchone()
        if not lecturer:
            return jsonify({"error": "Lecturer not found."}), 404
        
        # Check is a lecturer is already assigned to a course
        cursor.execute("SELECT * FROM course_maintainer WHERE courseID=%s", (course_id,))
        exists = cursor.fetchone()
        if exists:
            return jsonify({"message": "Course already has a lecturer."}), 400
        
        # Check is a lecturer is assigned to 5 or more courses
        cursor.execute("SELECT COUNT(courseID) AS total FROM  course_maintainer WHERE lecturerID=%s", (lecturer_id,))
        course_count = cursor.fetchone()['total']
        
        if course_count >=5:
            return jsonify({"message": "Lecturer already assigned to 5 courses."}), 400
        
        # Assign lecturer
        cursor.execute("INSERT INTO course_maintainer (lecturerID, courseID) VALUES (%s, %s)", (lecturer_id, course_id))
        conn.commit()
        
        return jsonify({"message": f"Lecturer successfully assigned to course {course_id}."}), 201
    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500
    
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    
    
@app.route('/courses/<int:course_id>/register-student', methods=['POST'])
def register_student(course_id):
    """Register students for a course."""
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        data = request.get_json()
        student_id = data.get('userID')
        
        if not student_id:
            return jsonify({"message": "Student ID required."}), 400
        
        # Check if course exists
        cursor.execute("SELECT * FROM course WHERE courseID=%s", (course_id,))
        course = cursor.fetchone()
        if not course:
            return jsonify({"error": "Course not found."}), 404
        
        # Check if a student exists
        cursor.execute("SELECT * FROM user WHERE userID=%s AND userType = 'student'", (student_id,))
        student = cursor.fetchone()
        if not student:
            return jsonify({"error": "Student not found."}), 404
        
        # Check is a student is already enrolled in a course
        cursor.execute("SELECT * FROM enrollment WHERE studentID=%s AND courseID=%s", (student_id, course_id,))
        enroll = cursor.fetchone()
        if enroll:
            return jsonify({"message": "Already enrolled in this course."}), 400
        
        # Enroll student
        cursor.execute("INSERT INTO enrollment(studentID, courseID) VALUES (%s, %s)", (student_id, course_id))
        conn.commit()
        
        return jsonify({"message": f"Student successfully enrolled in the course {course_id}."}), 201
    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500
    
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    
    
# 6. Retrieve Members
@app.route('/members/<int:course_id>', methods=['GET'])
def get_members(course_id):
    """Return members of a particular course.""" 
    conn = None
    cursor = None
      
    try:   
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Lecturers
        query = """
        SELECT u.firstname, u.lastname, u.userID
        FROM user u 
        JOIN course_maintainer cm ON u.userID = cm.lecturerID
        WHERE cm.courseID=%s;
        """
        cursor.execute(query, (course_id,))
        lecturer = cursor.fetchone()
        
        # Students     
        query = """
        SELECT u.firstname, u.lastname, u.userID
        FROM user u 
        JOIN enrollment e ON u.userID = e.studentID
        WHERE e.courseID=%s;
        """
        cursor.execute(query, (course_id,))
        students = cursor.fetchall()
        
        return jsonify({
            "course_id": course_id,
            "lecturer": lecturer,
            "students": students
        }), 200
    
    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500
    
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    
    
# 7. Retrieve Calendar Events
@app.route('/courses/<int:course_id>/events', methods=['GET'])
def course_calendar(course_id):
    """Retrieve all calendar events for a particular course."""
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query="""
        SELECT eventID, courseID, eventTitle, description, eventType, eventDate, dueDate
        FROM calendar_event
        WHERE courseID = %s
        ORDER BY eventDate ASC
        """
    
        cursor.execute(query, (course_id,))
        events = cursor.fetchall()
        
        return jsonify({
            "course_id": course_id,
            "events" : events
        }), 200
    
    except Exception as e:
        print(e)
        
        return jsonify({
            "success": False,
            "message": "Failed to fetch events" 
        }), 500
    
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    
@app.route('/student/<int:student_id>/events', methods=['GET'])
def student_calendar(student_id):
    """Retrieve all calendar events for a particular date for a particular student.""" 
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        date = request.args.get('date')
        
        if not date:
            return jsonify({"error": "Date is required (YYYY-MM-DD)"}), 400
        
        query="""
        SELECT ce.eventID, ce.courseID, ce.eventTitle, ce.description, ce.eventType, ce.eventDate, ce.dueDate
        FROM calendar_event ce
        JOIN enrollment e ON ce.courseID = e.courseID
        WHERE e.studentID = %s
        AND ce.eventDate = %s
        ORDER BY ce.eventDate ASC
        """
    
        cursor.execute(query, (student_id, date))
        events = cursor.fetchall()
        
        return jsonify({
            "student_id": student_id,
            "date": date,
            "events": events
        }), 200
    
    except Exception as e:
        print(e)
        
        return jsonify({
            "success": False,
            "message": "Failed to fetch events" 
        }), 500
    
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# 8. Create Calendar Events 
@app.route('/courses/<int:course_id>/events', methods=['POST'])
def create_calendar(course_id):
    """Create a calendar event for a course."""
    conn = None
    cursor = None
    try:   
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        data = request.get_json()
        
        eventTitle = data.get('eventTitle')
        description = data.get('description')
        eventType = data.get('eventType')
        eventDate = data.get('eventDate')
        dueDate = data.get('dueDate')
        
        if not all([eventTitle, eventDate]):
            return jsonify({"error": "Missing required fields."}), 400
        
        # Check if course exists
        cursor.execute("SELECT * FROM course WHERE courseID=%s", (course_id,))
        course = cursor.fetchone()
        
        if not course:
            return jsonify({"error": "Course not found."}), 404
        
        # Insert events
        query = """
        INSERT INTO calendar_event
        (courseID, eventTitle, description, eventType, eventDate, dueDate)
        VALUES(%s, %s, %s, %s, %s, %s)
        """
        values = (course_id, eventTitle, description, eventType, eventDate, dueDate)
        
        cursor.execute(query, values)
        conn.commit()
        
        return jsonify({"message": "Calendar event created successfully."}), 201
    
    except Exception as e:
        print(e)
        return jsonify({"message": "Failed to create calendar.", "error": str(e)}), 500
    
    finally:
       if cursor:
            cursor.close()
       if conn:
            conn.close()
    