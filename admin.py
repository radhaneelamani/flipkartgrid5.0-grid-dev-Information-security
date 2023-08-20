import os
import time

from flask import Blueprint, render_template, request, redirect, session
import sqlite3
import openai

admin_routes = Blueprint('admin', __name__)

# logs_contents = []
# rules_contents = []


@admin_routes.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    error_message = None
    if request.method == 'POST':
        # Get the form data
        username = request.form['username']
        password = request.form['password']

        # Connect to the SQLite database
        conn = sqlite3.connect('flightreservationdb.db')
        cursor = conn.cursor()

        # Retrieve the admin information from the admindetails table
        cursor.execute("SELECT * FROM admindetails WHERE username = ? AND password = ?", (username, password))
        admin = cursor.fetchone()

        if admin:
            # Admin login successful
            # Implement admin authentication logic here
            conn.close()
            return redirect('/admin/home')  # Redirect to the admin home page
        else:
            # Admin login failed
            conn.close()
            error_message = "Invalid credentials. Please try again."

    return render_template('/admin/login.html', error_message=error_message)


@admin_routes.route('/logout', methods=['GET'])
def logout():
    return redirect('/')


@admin_routes.route('/admin/home')
def admin_home():
    # Connect to the SQLite database
    conn = sqlite3.connect('flightreservationdb.db')
    cursor = conn.cursor()

    # Retrieve the current flights from the flights table
    cursor.execute("SELECT * FROM flights")
    flights = cursor.fetchall()

    conn.close()

    return render_template('/admin/home.html', flights=flights)


# Add Flight route
@admin_routes.route('/admin/addflight', methods=['GET', 'POST'])
def add_flight():
    if request.method == 'POST':
        # Get flight details from the form
        flight_number = request.form['flight_number']
        departure_city = request.form['departure_city']
        departure_date = request.form['departure_date']
        departure_time = request.form['departure_time']
        arrival_city = request.form['arrival_city']
        arrival_date = request.form['arrival_date']
        arrival_time = request.form['arrival_time']
        available_seats = request.form['available_seats']

        # Connect to the SQLite database
        conn = sqlite3.connect('flightreservationdb.db')
        cursor = conn.cursor()

        # Insert flight details into the database
        cursor.execute(
            "INSERT INTO flights "
            "(flight_number, departure_city, departure_date, departure_time, "
            "arrival_city, arrival_date, arrival_time, available_seats) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (flight_number, departure_city, departure_date, departure_time,
             arrival_city, arrival_date, arrival_time, available_seats))
        conn.commit()
        return redirect('/admin/home')
    return render_template('/admin/addflight.html')

    # return redirect('/admin/home')


# Remove Flight route
@admin_routes.route('/admin/removeflight', methods=['GET', 'POST'])
def remove_flight():
    if request.method == 'POST':
        # Get flight ID from the form
        flight_number = request.form['flight_number']

        # Connect to the SQLite database
        conn = sqlite3.connect('flightreservationdb.db')
        cursor = conn.cursor()

        # Delete flight from the database
        cursor.execute("DELETE FROM flights WHERE flight_number = ?", (flight_number,))
        conn.commit()
        return redirect('/admin/home')

    return render_template('/admin/removeflight.html')


@admin_routes.route('/admin/passengerdetails/<flight_number>')
def passenger_details(flight_number):
    # Connect to the SQLite database
    conn = sqlite3.connect('flightreservationdb.db')
    cursor = conn.cursor()

    # Retrieve the passenger details from the bookings table
    cursor.execute("SELECT * FROM bookings WHERE flight_number = ?", (flight_number,))
    passengers = cursor.fetchall()

    conn.close()

    return render_template('/admin/passengerdetails.html', passengers=passengers, flight_number=flight_number)


@admin_routes.route('/admin/compliance')
def compliance_check_page():
    return render_template('/admin/compliance.html')


openai.api_key = "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"


UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


@admin_routes.route('/admin/generate_logs', methods=['POST'])
def generate_logs():
    conn = sqlite3.connect('flightreservationdb.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM logs")
    logs = cursor.fetchall()
    conn.close()

    logs_text = '\n'.join([f"{log[1]}|{log[2]}|{log[3]}|{log[4]}" for log in logs])

    logs_file_path = os.path.join(UPLOAD_FOLDER, 'logs.txt')
    with open(logs_file_path, 'w') as logs_file:
        logs_file.write(logs_text)

    return "Logs generated and saved to logs.txt."


@admin_routes.route('/admin/upload_logs', methods=['POST'])
def upload_logs():
    # global logs_contents
    log_file = request.files['log_file']
    log_file.save(f"{UPLOAD_FOLDER}/logs.txt")

    # Read the uploaded log file
    # log_contents = []
    with open(f"{UPLOAD_FOLDER}/logs.txt", 'r') as file:
        session['logs_contents'] = file.readlines()
    print(session['logs_contents'])

    return render_template('/admin/compliance.html')


@admin_routes.route('/admin/upload_rules', methods=['POST'])
def upload_rules():
    # global rules_contents
    rules_file = request.files['rules_file']
    rules_file.save(f"{UPLOAD_FOLDER}/rules.txt")

    # Read the uploaded rules file
    # rules_contents = []
    with open(f"{UPLOAD_FOLDER}/rules.txt", 'r') as file:
        session['rules_contents'] = file.readlines()
    print(session['rules_contents'])

    return render_template('/admin/compliance.html')


# Assuming you have a function to perform the compliance check using OpenAI API
def perform_compliance_check(logs, rules):
    # Call OpenAI API to get compliance check report
    # Replace this with your actual OpenAI API call
    logs_lines = logs.strip().split('\n')
    rules_lines = rules.strip().split('\n')
    print("after strp", rules_lines)
    compliance_breaches = []
    # Loop through each rule and check for breaches in the logs
    for rule_line in rules_lines:
        rule_parts = rule_line.strip().split("|")
        if len(rule_parts) < 3:
            continue
        rule_number = rule_parts[0]
        rule = rule_parts[1]
        description = rule_parts[2]
        print("rule:", rule, "des:", description)

        for log_line in logs_lines:
            log_parts = log_line.split("|")
            # activity = log_parts[3]
            log_full_line = log_parts  # Store the full log line
            print("logs:",log_full_line)
            if log_full_line == ['']:
                continue
            else:
                if rule not in log_full_line:
                    # Add the breach to the list
                    compliance_breaches.append({
                        "rule": rule,
                        "description": description,
                        "log_line": log_full_line
                    })
            print("complbre", compliance_breaches)

    # Generate the compliance report with citations and actionable insights
    compliance_report = []
    for breach in compliance_breaches:
        # compliance_report += f"Breach: {breach['rule']} | {breach['description']} | Line: {breach['log_line']}\n"

        # Use OpenAI to generate actionable insights
        prompt = f"Actionable insight for breach: {breach['description']}"
        response = openai.Completion.create(
            engine="davinci",  # Choose the engine
            prompt=prompt,
            max_tokens=30,  # Choose an appropriate number of tokens
        )
        time.sleep(30)
        actionable_insight = response.choices[0].text.strip()
        breach_info = f"Breach: {breach['rule']} | {breach['description']} | Line: {breach['log_line']}"
        actionable_insight = f"Actionable Insight: {actionable_insight}"
        # compliance_report += f"Actionable Insight: {actionable_insight}\n"
        compliance_report.append({
            'breach_info': breach_info,
            'actionable_insight': actionable_insight
        })

        print(f"Generated breach: {breach['rule']} | {breach['description']} | Line: {breach['log_line']}")
        print(f"Generated actionable insight: {actionable_insight}")

    return compliance_report


@admin_routes.route('/admin/generate_compliance_report', methods=['GET'])
def generate_compliance_report():
    # You can add your logic here to generate the compliance report

    # Fetch the logs and rules contents from the global variables
    logs = '\n'.join(session.get('logs_contents', []))
    rules = '\n'.join(session.get('rules_contents', []))
    print("in generate", logs)
    print("in generate rules", rules )

    # Perform compliance check using OpenAI API
    compliance_report = perform_compliance_check(logs, rules)
    print(compliance_report)

    return render_template('/admin/compliancereport.html', compliance_report=compliance_report)