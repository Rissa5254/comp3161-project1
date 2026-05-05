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
    
    
@app.route('/courses/<int:course_id>/register-student', methods=['POST'])
def register_student():
    """Register students for a course."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        data = request.get_json()
        student_id = data.get('userID')
        
    
    

# 6. Retrieve Members
@app.route()
def members():
    """Return members of a particular course."""
    
    
# 7. Retrieve Calendar Events
@app.route()
def retrieve_calender():
    """Retrieve all calendar events for a particular course."""
    
    
    """Retrieve all calendar events for a particular date for a particular student.""" 


# 8. Create Calendar Events 
@app.route()
def create_calendar():
    """Create a calendar event for a course."""
   
