from flask import Flask, request, render_template, redirect, url_for, session, jsonify
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import random
from datetime import datetime

from shapely.geometry import Point, Polygon


app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this to a random string for security.

questions_bank = [
    {"question": "Which planet is known as the Red Planet?", "options": ["Mars", "Venus", "Jupiter"], "correct": "Mars"},
    {"question": "Which metal is heavier, silver or gold?", "options": ["Silver", "Gold", "They're the same"], "correct": "Gold"},
    {"question": "How many points does a compass have?", "options": ["2", "4", "8"], "correct": "4"},
    {"question": "Which animal is known as the ‘King of the Jungle’?", "options": ["Lion", "Tiger", "Elephant"], "correct": "Lion"},
    {"question": "How many continents are there?", "options": ["5", "6", "7"], "correct": "7"},
    {"question": "In which direction does the sun rise?", "options": ["East", "West", "North"], "correct": "East"},
    {"question": "What is the capital of Japan?", "options": ["Shanghai", "Seoul", "Tokyo"], "correct": "Tokyo"},
    {"question": "Which gas do plants absorb from the atmosphere?", "options": ["Carbon Dioxide", "Oxygen", "Nitrogen"], "correct": "Carbon Dioxide"},
    {"question": "Which country is known as the Land of the Rising Sun?", "options": ["China", "Japan", "South Korea"], "correct": "Japan"},
    {"question": "In what year did World War II end?", "options": ["1942", "1945", "1950"], "correct": "1945"},
    {"question": "Who wrote 'Romeo and Juliet'?", "options": ["Charles Dickens", "William Shakespeare", "Jane Austen"], "correct": "William Shakespeare"},
    {"question": "What is the primary ingredient in guacamole?", "options": ["Tomatoes", "Peppers", "Avocados"], "correct": "Avocados"},
    {"question": "Which planet is closest to the sun?", "options": ["Mars", "Earth", "Mercury"], "correct": "Mercury"},
    {"question": "Which ocean is the largest?", "options": ["Atlantic Ocean", "Indian Ocean", "Pacific Ocean"], "correct": "Pacific Ocean"},
    {"question": "What is the currency used in the United Kingdom?", "options": ["Euro", "Pound Sterling", "Dollar"], "correct": "Pound Sterling"},
    {"question": "Which artist painted the Mona Lisa?", "options": ["Vincent van Gogh", "Pablo Picasso", "Leonardo da Vinci"], "correct": "Leonardo da Vinci"},
    {"question": "What is the world's largest desert?", "options": ["Sahara", "Arctic", "Gobi"], "correct": "Arctic"},
    {"question": "Which blood group is known as the universal donor?", "options": ["O-", "AB+", "A+"], "correct": "O-"},
    {"question": "How many bones does an adult human have?", "options": ["206", "300", "187"], "correct": "206"},
    {"question": "Which country is the origin of the cocktail Mojito?", "options": ["Brazil", "Mexico", "Cuba"], "correct": "Cuba"},
]

random.shuffle(questions_bank)

# Boundaries of the College of Staten Island. 
college_polygon = Polygon([(40.607864, -74.155098), (40.607962, -74.146686), (40.596232, -74.145570), (40.596199, -74.153424)])

@app.route('/verify-location', methods=['POST'])
def verify_location():
    data = request.get_json()
    user_location = Point(data['lat'], data['lng'])

    if college_polygon.contains(user_location):
        return jsonify(allowed=True)
    else:
        return jsonify(allowed=False)
    
@app.route('/', methods=['GET', 'POST'])
def index():
    message = None  # This will hold our success or error message

    # If the location hasn't been verified yet
    if 'location_verified' not in session or not session['location_verified']:
        return render_template('verify_location.html')

    if 'questions' not in session:
        session['questions'] = random.sample(questions_bank, 20)  # Select 20 random questions
        session['score'] = 0
        session['asked_questions'] = []  # Track questions that have already been asked
        session['answered'] = 0


    if request.method == 'POST':
        answer = request.form['answer']
        correct_answer = session['questions'][session['answered']]['correct']

        if answer == correct_answer:
            session['score'] += 1
            message = "Great, keep going!"
            session['asked_questions'].append(session['answered'])  # Add the question to the list of asked questions

        else:
            message = "Wrong, try another!"
            session['asked_questions'].append(session['answered'])  # Add the question to the list of asked questions

        # Choose another question 
        remaining_questions = [i for i in range(len(session['questions'])) if i not in session['asked_questions']]
        if remaining_questions:
            session['answered'] = random.choice(remaining_questions)
        else:
            session['answered'] = len(session['questions'])

    # If they're still answering questions
    if 'answered' in session and session['answered'] < len(session['questions']):
        return render_template('index.html', 
                               question=session['questions'][session['answered']], 
                               score=session['score'], 
                               total=len(session['questions']),
                               message=message, # Pass the message to the template
                               quiz_complete=False) 
    else:
        # If they've answered all questions, render the same template but in quiz_complete mode
        return render_template('index.html',
                               quiz_complete=True, 
                               message=None)  

def add_to_sheet(user_id, score, time):
    """
    Add data to Google Sheets.
    """
    # Use creds to create a client to interact with the Google Drive API
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('cred.json', scope) # Put json into parent directory(same as this one)
    client = gspread.authorize(creds)

    # Google Sheet's name 
    sheet = client.open("CSI Quiz").sheet1  # Make sure to replace with your Google Sheet's name

    # Extract and print all of the values
    list_of_hashes = sheet.get_all_records()

    # Add a new row with user_id, score, and time
    sheet.append_row([user_id, score, time])

@app.route('/submit-id', methods=['POST'])
def submit_id():
    user_id = request.form.get('user_id')
    # Date & Time when the user completed the quiz
    completion_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Function to save to Google Sheets (implement this!)
    add_to_sheet(user_id, session['score'], completion_time)
    
    session.clear()  # Clearing the session to ensure the quiz restarts for the next user
    return "Thank you! Your ID and score have been recorded."

@app.route('/location-verified', methods=['GET'])
def location_verified():
    session['location_verified'] = True
    return redirect(url_for('index'))

@app.route('/not-on-campus', methods=['GET'])
def not_on_campus():
    return render_template('not_on_campus.html')

if __name__ == '__main__':
    app.run(debug=True)
