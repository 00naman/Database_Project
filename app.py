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

@app.route('/goback', methods=['POST','GET'])
def goback():
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
            return redirect(url_for('confirm_select_package'))
        else:
            flash("Invalid username or password", "error")
            return redirect(url_for('login'))
    except mysql.connector.Error as err:
        flash(f"Database Error: {err}", "error")
        return redirect(url_for('login'))

@app.route('/adminlogin', methods=['POST','GET'])
def adminlogin():
    return render_template('adminlogin.html')

@app.route('/register', methods=['POST','GET'])
def register():
    return render_template('register.html')

@app.route('/register_user', methods=['POST','GET'])
def register_user():
    name = request.form['name']
    address = request.form['address']
    dob = request.form['dob']
    email = request.form['email']
    password = request.form['password']

    try:
        conn = connect_to_database()
        cursor = conn.cursor()

        # Fetch the maximum user_id from the user_3 table
        cursor.execute("SELECT MAX(user_id) FROM user_3")
        max_user_id = cursor.fetchone()[0]

        # Increment the maximum user_id by 1 to generate the new user_id
        new_user_id = max_user_id + 1 if max_user_id else 1

        # Insert the new user with the generated user_id
        cursor.execute("INSERT INTO user_3 (user_id, name, address, dob, email, password) VALUES (%s, %s, %s, %s, %s, %s)", (new_user_id, name, address, dob, email, password))
        conn.commit()
        cursor.close()
        conn.close()
        
        flash("Registration successful! You can now login.", "success")
        return redirect(url_for('login'))
    except mysql.connector.Error as err:
        flash(f"Error registering user: {err}", "error")
        return redirect(url_for('register'))

@app.route('/admin_page', methods=['POST','GET'])
def admin_login_validation():
    email = request.form['email']
    password = request.form['password']

    try:
        conn = connect_to_database()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ad_min WHERE a_email=%s AND a_password=%s", (email, password))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            session['a_id'] = user[0]  # Store a_id in session
            return render_template('admin_page.html')
        else:
            flash("Invalid username or password", "error")
            return redirect(url_for('adminlogin'))
    except mysql.connector.Error as err:
        flash(f"Database Error: {err}", "error")
        return redirect(url_for('adminlogin'))
    

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
        
        # Fetch travel modes
        try:
            conn = connect_to_database()
            cursor = conn.cursor()
            cursor.execute("SELECT mode_name FROM t_mode")
            travel_modes = [row[0] for row in cursor.fetchall()]  # Fixed typo: travel_modes instead of travel_mode
            cursor.close()
            conn.close()
        except mysql.connector.Error as err:
            travel_modes = []
            flash(f"Error fetching travel modes: {err}", "error")

        return render_template('select_package.html', departure_cities=departure_cities, arrival_cities=arrival_cities, travel_modes=travel_modes)
    else:
        return redirect(url_for('login'))

@app.route('/transport_options', methods=['POST','GET'])
def transport_options():
    if 'user_id' in session:
        departure_city = request.form['departure']
        arrival_city = request.form['arrival']
        travel_mode = request.form['t_mode']

        # Fetch transport options based on departure and arrival cities
        try:
            conn = connect_to_database()
            cursor = conn.cursor()
            cursor.execute("SELECT td.dofd, td.dep_time, td.arrival_time, td.price, td.seats_rem, c.company_name, tm.mode_name, td.tm_id FROM transit_details td JOIN company c ON td.company_id = c.company_id JOIN t_mode tm ON td.mode_id = tm.mode_id WHERE td.dep_id=(SELECT dep_id FROM departure WHERE city_name=%s) AND td.arr_id=(SELECT arr_id FROM arrival WHERE city_name=%s) AND tm.mode_name = %s", (departure_city, arrival_city, travel_mode))
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
            return redirect(url_for('confirm_select_package'))
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

@app.route('/confirm_select_package')
def confirm_select_package():
    return render_template('confirm_select_package.html')

@app.route('/select_hotel_location')
def select_hotel_location():
    try:
        # Fetch all available hotel locations from the database
        conn = connect_to_database()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT location FROM hotel")
        locations = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()

        return render_template('select_hotel_location.html', locations=locations)
    except mysql.connector.Error as err:
        flash(f"Error fetching hotel locations: {err}", "error")
        return redirect(url_for('login'))

@app.route('/display_hotels', methods=['POST'])
def display_hotels():
    selected_location = request.form['hotel_location']
    try:
        # Fetch hotels available at the selected location from the database
        conn = connect_to_database()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM hotel WHERE location = %s", (selected_location,))
        hotels = cursor.fetchall()
        cursor.close()
        conn.close()

        return render_template('display_hotels.html', hotels=hotels, location=selected_location)
    except mysql.connector.Error as err:
        flash(f"Error fetching hotels: {err}", "error")
        return redirect(url_for('login'))

import random 

@app.route('/book_hotel', methods=['POST'])
def book_hotel():
    if 'user_id' in session:
        try:
            # Extract data from the form submission
            hotel_id = request.form['hotel_id']
            user_id = session['user_id']
            checkin_date = request.form['checkin_date']
            checkout_date = request.form['checkout_date']
            room_type = request.form['room_type']
            ac = True if request.form.get('ac') == 'on' else False  # Convert checkbox value to boolean
            
            # Generate a random room number between 100 and 500
            room_no = random.randint(100, 500)

            # Insert a new record into the hotel_reservation table
            conn = connect_to_database()
            cursor = conn.cursor()
            cursor.execute("""INSERT INTO hotel_reservation (checkindate, checkoutdate, room_no, room_type, ac, user_id, hotel_id)
                              VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                           (checkin_date, checkout_date, room_no, room_type, ac, user_id, hotel_id))
            conn.commit()
            cursor.close()
            conn.close()

            flash("Hotel booked successfully!", "success")
            return redirect(url_for('confirm_select_package'))
        except mysql.connector.Error as err:
            flash(f"Error booking hotel: {err}", "error")
            return redirect(url_for('confirm_select_package'))  # Redirect to confirm_select_package on error
    else:
        return redirect(url_for('login'))

@app.route('/view_hotel_bookings')
def view_hotel_bookings():
    if 'user_id' in session:
        try:
            user_id = session['user_id']
            
            # Fetch the user's hotel bookings from the database with additional details
            conn = connect_to_database()
            cursor = conn.cursor()
            cursor.execute("""SELECT hr.booking_id, hr.checkindate, hr.checkoutdate, hr.room_no, hr.room_type, hr.ac,
                                     h.h_name, h.location
                              FROM hotel_reservation hr
                              JOIN hotel h ON hr.hotel_id = h.hotel_id
                              WHERE hr.user_id = %s""", (user_id,))
            hotel_bookings = cursor.fetchall()
            cursor.close()
            conn.close()
            
            return render_template('view_hotel_bookings.html', hotel_bookings=hotel_bookings)
        except mysql.connector.Error as err:
            flash(f"Error fetching hotel bookings: {err}", "error")
            return redirect(url_for('select_package'))
    else:
        return redirect(url_for('login'))
    


@app.route('/insert_departure_city', methods=['POST'])
def insert_departure_city():
    city_name = request.form['city_name']
    pincode = request.form['pincode']
    dep_id = request.form['dep_id']

    try:
        conn = connect_to_database()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO departure (dep_id, city_name, pincode) VALUES (%s, %s, %s)", (dep_id, city_name, pincode))
        conn.commit()
        cursor.close()
        conn.close()
        flash("New departure city added successfully!", "success")
    except mysql.connector.Error as err:
        flash(f"Error adding departure city: {err}", "error")
    return render_template('admin_page.html')

# Route to handle insertion of new arrival city
@app.route('/insert_arrival_city', methods=['POST'])
def insert_arrival_city():
    city_name = request.form['city_name']
    pincode = request.form['pincode']
    arr_id = request.form['arr_id']

    try:
        conn = connect_to_database()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO arrival (arr_id, city_name, pincode) VALUES (%s, %s, %s)", (arr_id, city_name, pincode))
        conn.commit()
        cursor.close()
        conn.close()
        flash("New arrival city added successfully!", "success")
    except mysql.connector.Error as err:
        flash(f"Error adding arrival city: {err}", "error")
    return render_template('admin_page.html')

# Route to handle insertion of new location for hotel
@app.route('/insert_hotel_location', methods=['POST'])
def insert_hotel_location():
    hotel_id = request.form['hotel_id']
    h_name = request.form['h_name']
    location = request.form['location']
    h_rating = request.form['h_rating']

    try:
        conn = connect_to_database()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO hotel (hotel_id,h_name,location,h_rating) VALUES (%s,%s,%s,%s)", (hotel_id,h_name,location,h_rating))
        conn.commit()
        cursor.close()
        conn.close()
        flash("New hotel location added successfully!", "success")
    except mysql.connector.Error as err:
        flash(f"Error adding hotel location: {err}", "error")
    return render_template('admin_page.html')

# Route to handle insertion of new company for transport
@app.route('/insert_transport_company', methods=['POST'])
def insert_transport_company():
    company_name = request.form['company_name']
    contact_info = request.form['contact_info']

    try:
        conn = connect_to_database()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO company (company_name, contact_info) VALUES (%s, %s)", (company_name, contact_info))
        conn.commit()
        cursor.close()
        conn.close()
        flash("New transport company added successfully!", "success")
    except mysql.connector.Error as err:
        flash(f"Error adding transport company: {err}", "error")
    return render_template('admin_page.html')


@app.route('/go_review', methods=['POST','GET'])
def go_review():
    return render_template('reviews.html')
    

@app.route('/add_review', methods=['POST','GET'])
def add_review():
    if 'user_id' in session:
        # Extract data from the form submission
        ratings = request.form['ratings']  # Corrected form field name
        remarks = request.form['remarks']
        user_id = session['user_id']

        try:
            # Connect to the database
            conn = connect_to_database()
            cursor = conn.cursor()

            # Insert the review into the database
            cursor.execute("INSERT INTO reviews (user_id, ratings, remarks) VALUES (%s, %s, %s)", (user_id, ratings, remarks))
            conn.commit()

            # Close database connection
            cursor.close()
            conn.close()

            flash("Review added successfully!", "success")
            return redirect(url_for('confirm_select_package'))
        except mysql.connector.Error as err:
            # Log the error for debugging
            app.logger.error("Error adding review:", err)

            return redirect(url_for('confirm_select_package'))
    else:
        flash("Please log in to add a review.", "error")
        return redirect(url_for('login'))

@app.route('/insert_transit_details', methods=['POST','GET'])
def insert_transit_details():
    try:
        # Extract data from the form submission
        tm_id = request.form['tm_id']
        dofd = request.form['dofd']
        dep_time = request.form['dep_time']
        arrival_time = request.form['arrival_time']
        price = request.form['price']
        seats_rem = request.form['seats_rem']
        dep_id = request.form['dep_id']
        arr_id = request.form['arr_id']
        company_name = request.form['company_name']
        mode_name = request.form['mode_name']

        # Connect to the database
        conn = connect_to_database()
        cursor = conn.cursor()

        # Get company_id based on company_name
        cursor.execute("SELECT company_id FROM company WHERE company_name = %s", (company_name,))
        company_id = cursor.fetchone()[0]

        # Get mode_id based on mode_name
        cursor.execute("SELECT mode_id FROM t_mode WHERE mode_name = %s", (mode_name,))
        mode_id = cursor.fetchone()[0]

        # Insert transit details into the database
        cursor.execute("INSERT INTO transit_details (tm_id, dofd, dep_time, arrival_time, price, seats_rem, dep_id, arr_id, company_id, mode_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (tm_id, dofd, dep_time, arrival_time, price, seats_rem, dep_id, arr_id, company_id, mode_id))
        conn.commit()

        # Close database connection
        cursor.close()
        conn.close()

        flash("Transit details added successfully!", "success")
        return render_template('admin_page.html')
    except mysql.connector.Error as err:
        flash(f"Error adding transit details: {err}", "error")
        return render_template('admin_page.html')



@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)