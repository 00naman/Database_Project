from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MySQL configurations
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'namanjay',
    'database': 'travel'
}

def connect_to_database():
    return mysql.connector.connect(**db_config)

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_validation():
    email = request.form['email']
    password = request.form['password']

    try:
        conn = connect_to_database()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_3 WHERE email=%s AND password=%s", (email, password))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            session['user_id'] = user[0]  # Store user_id in session
            return redirect(url_for('select_package'))
        else:
            flash("Invalid username or password", "error")
            return redirect(url_for('login'))
    except mysql.connector.Error as err:
        flash(f"Database Error: {err}", "error")
        return redirect(url_for('login'))
    
@app.route('/select_package')
def select_package():
    if 'user_id' in session:
        # Fetch departure cities
        try:
            conn = connect_to_database()
            cursor = conn.cursor()
            cursor.execute("SELECT city_name FROM departure")
            departure_cities = [row[0] for row in cursor.fetchall()]
            cursor.close()
            conn.close()
        except mysql.connector.Error as err:
            departure_cities = []
            flash(f"Error fetching departure cities: {err}", "error")

        # Fetch arrival cities
        try:
            conn = connect_to_database()
            cursor = conn.cursor()
            cursor.execute("SELECT city_name FROM arrival")
            arrival_cities = [row[0] for row in cursor.fetchall()]
            cursor.close()
            conn.close()
        except mysql.connector.Error as err:
            arrival_cities = []
            flash(f"Error fetching arrival cities: {err}", "error")

        return render_template('select_package.html', departure_cities=departure_cities, arrival_cities=arrival_cities)
    else:
        return redirect(url_for('login'))

@app.route('/transport_options', methods=['POST','GET'])
def transport_options():
    if 'user_id' in session:
        departure_city = request.form['departure']
        arrival_city = request.form['arrival']

        # Fetch transport options based on departure and arrival cities
        try:
            conn = connect_to_database()
            cursor = conn.cursor()
            cursor.execute("SELECT td.dofd, td.dep_time, td.arrival_time, td.price, td.seats_rem, c.company_name, tm.mode_name, td.tm_id FROM transit_details td JOIN company c ON td.company_id = c.company_id JOIN t_mode tm ON td.mode_id = tm.mode_id WHERE td.dep_id=(SELECT dep_id FROM departure WHERE city_name=%s) AND td.arr_id=(SELECT arr_id FROM arrival WHERE city_name=%s)", (departure_city, arrival_city))
            transport_options = cursor.fetchall()
            cursor.close()
            conn.close()
        except mysql.connector.Error as err:
            transport_options = []
            flash(f"Error fetching transport options: {err}", "error")

        return render_template('transport_options.html', transport_options=transport_options)
    else:
        return redirect(url_for('login'))
    


from string import ascii_uppercase

@app.route('/book_ticket', methods=['POST'])
def book_ticket():
    if 'user_id' in session:
        try:
            # Extract data from the form submission
            tm_id = request.form['tm_id']
            user_id = session['user_id']

            # Fetch existing seat numbers for the selected transport mode
            conn = connect_to_database()
            cursor = conn.cursor()
            cursor.execute("SELECT seat_no FROM ticket WHERE tm_id = %s", (tm_id,))
            existing_seat_numbers = [row[0] for row in cursor.fetchall()]

            # Find the next available seat number
            available_seat_number = None
            for row in range(1, 21):  # Assuming there are 20 rows of seats
                for letter in ascii_uppercase:  # Assuming seats are labeled A, B, C, ...
                    seat_number = f"{row}{letter}"
                    if seat_number not in existing_seat_numbers:
                        available_seat_number = seat_number
                        break
                if available_seat_number:
                    break

            # If no available seat found, inform the user
            if not available_seat_number:
                flash("No available seats for this transport mode.", "error")
                return redirect(url_for('select_package'))

            # Insert a new record into the ticket table with the available seat number
            cursor.execute("INSERT INTO ticket (seat_no, user_id, tm_id) VALUES (%s, %s, %s)", (available_seat_number, user_id, tm_id))

            # Decrease the remaining seats count
            cursor.execute("UPDATE transit_details SET seats_rem = seats_rem - 1 WHERE tm_id = %s", (tm_id,))
            
            conn.commit()
            cursor.close()
            conn.close()

            flash(f"Ticket booked successfully! Your seat number is {available_seat_number}.", "success")
            return redirect(url_for('select_package'))
        except mysql.connector.Error as err:
            flash(f"Error booking ticket: {err}", "error")
            return redirect(url_for('select_package'))
    else:
        return redirect(url_for('login'))

    
@app.route('/view_bookings')
def view_bookings():
    if 'user_id' in session:
        try:
            user_id = session['user_id']
            
            # Fetch the user's bookings from the database with additional details
            conn = connect_to_database()
            cursor = conn.cursor()
            cursor.execute("""SELECT t.ticket_id, t.seat_no, d.city_name AS departure_city, a.city_name AS arrival_city, 
                              td.dep_time, td.arrival_time, c.company_name
                              FROM ticket t
                              JOIN transit_details td ON t.tm_id = td.tm_id
                              JOIN departure d ON td.dep_id = d.dep_id
                              JOIN arrival a ON td.arr_id = a.arr_id
                              JOIN company c ON td.company_id = c.company_id
                              WHERE t.user_id = %s""", (user_id,))
            bookings = cursor.fetchall()
            cursor.close()
            conn.close()
            
            return render_template('view_bookings.html', bookings=bookings)
        except mysql.connector.Error as err:
            flash(f"Error fetching bookings: {err}", "error")
            return redirect(url_for('select_package'))
    else:
        return redirect(url_for('login'))



@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)