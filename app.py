from flask import Flask, jsonify, request, make_response
from dotenv import load_dotenv
import os
import mysql.connector


load_dotenv()

app = Flask(__name__)



# 5. Register for Course
@app.route('/courses/<int:course_id>', methods=['POST'])
def assign_lecturer():
    """Assign a lecturer to a course."""
    
    
@app.route('/courses/<int:course_id>', methods=['POST'])
def register_student():
    """Register students for a course."""
    
    

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
   
