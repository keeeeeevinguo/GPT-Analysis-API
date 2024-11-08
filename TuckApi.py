# author: Kevin Guo
# date: 11/08/2024

from flask import Flask, jsonify, request, g
import sqlite3
import json

app = Flask(__name__) # initialize Flask web application
DATABASE = 'GPTAnalysis.db' # define SQLite database name

# connect to the database or initialize it if it doesn't exist
def get_db():
    db = getattr(g, '_database', None) # get the existing database connection

    # if there's no exisitng connection, create a new one
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)

    return db

# initialize the database with the required table and initial data
def init_db():
    # run this function in the application context to access the database
    with app.app_context():
        db = get_db()
        cursor = db.cursor()

        # create analysis table if it doesn't already exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis (
                id INTEGER PRIMARY KEY,
                gptOutput TEXT
            )
        ''')

        # open JSON data generated by custom GPT
        with open('data.json', 'r') as file:
            initial_data = json.load(file)
        
        initial_content = initial_data.get("gptOutput", "") # get content from gptOutput field
        
        # insert initial data into the analysis table if it's empty
        cursor.execute('SELECT COUNT(*) FROM analysis')
        if cursor.fetchone()[0] == 0:
            cursor.execute('INSERT INTO analysis (id, gptOutput) VALUES (1, ?)', (initial_content,))
            db.commit()

# get the gptOutput from the database
def get_gptOutput():
    db = get_db()
    cursor = db.cursor()

    # select the gptOutput content from the analysis table
    cursor.execute('SELECT gptOutput FROM analysis WHERE id = 1')
    result = cursor.fetchone()
    return result[0] if result else ""

# API endpoint to retrieve the current gptOutput
@app.route('/api/tuckapi', methods=['GET'])
def get_analysis():
    gptOutput = get_gptOutput()
    return jsonify({'gptOutput': gptOutput})

# API endpoint to update the gptOutput by adding new text
@app.route('/api/tuckapi', methods=['POST'])
def update_analysis():
    # get new text from the request's JSON data
    new_text = request.json.get('text', '').strip()

    # if no text was provided, return an error
    if not new_text:
        return jsonify({'error': 'No text provided'}), 400

    db = get_db()
    cursor = db.cursor()

    # get the current gptOutput and add new text 
    current_gptOutput = get_gptOutput()
    updated_gptOutput = current_gptOutput + " " + new_text if current_gptOutput else new_text

    # update the gptOutput in the database
    cursor.execute('''
        INSERT OR REPLACE INTO analysis (id, gptOutput)
        VALUES (1, ?)
    ''', (updated_gptOutput,))
    db.commit()

    # return success message and updated gptOutput
    return jsonify({'message': 'gptOutput updated successfully with new text: ' + new_text})

# close the database connection when the app is torn down
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# run the app
if __name__ == '__main__':
    init_db() # initialize the database structure and data
    app.run(port=5000) # run the app on port 5000
