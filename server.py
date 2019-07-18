import os
from flask import Flask, render_template, redirect, flash, session, request
from mysqlconnection import connectToMySQL
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename
import datetime
import formatter
import re

UPLOAD_FOLDER = 'C:/Users/scamu/Desktop/CodingDojo/python_stack/flask/flask_project/static/images/'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$') 

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'shh'
bcrypt = Bcrypt(app)

#################################### functions ##############################

#--------------------------------------------------------- exists_in_database()
def exists_in_database(value, column):
    mysql = connectToMySQL("my_library")

    if column == "password":
        query = "SELECT password FROM users WHERE email = %(v)s;"
        data = { "v": value }
        passLib = mysql.query_db(query, data)
        pw = passLib[0]['password']
        return pw
    elif column == "email":
        query = "SELECT * FROM users WHERE email = %(val)s;"
        data = {
            "val": value
        }
        dataLib = mysql.query_db(query, data)
        
        if dataLib == False or len(dataLib) == 0:
            print("empty")
            return False # value does not exist in db
        else:
            return True # value does exist in db
    else:
        flash("An error has occured", 'must_login')
        return redirect('/')

#--------------------------------------------------------- hash_pass()
def hash_pass(password):
    password = bcrypt.generate_password_hash(password)
    return password

#--------------------------------------------------------- store_user()
def store_user(obj, user_pass):
    mysql = connectToMySQL("my_library")
    query = "INSERT INTO users (first_name, last_name, email, password, user_group, balance, created_at, updated_at) VALUES(%(fn)s, %(ln)s, %(em)s, %(pw)s, 'user', 0.00, NOW(), NOW());"
    data = {
        "fn": obj['fname'],
        "ln": obj['lname'],
        "em": obj['email'],
        "pw": user_pass
    }
    success = mysql.query_db(query, data)
    if success > 0:
        return True
    else:
        return False

#--------------------------------------------------------- get_user()
def get_user(value):
    mysql = connectToMySQL("my_library")
    query = "SELECT * FROM users WHERE email = %(v)s;"
    data = { "v": value }
    user = mysql.query_db(query, data)
    return user

#--------------------------------------------------------- validate_input()
def validate_input(obj, arr):
    for i in range(len(arr)):
        if len(obj[arr[i]]) < 3:
            flash(f"{arr[i]} must contain 3 or more characters", arr[i])
            return False

    return True

#--------------------------------------------------------- validate_pass()
def validate_pass(pw):
    if len(pw) < 8 or len(pw) > 15:
        return False

    if pw.isalpha():
        return False

    if pw.isnumeric():
        return False

    if pw.islower():
        return False

    return True

#--------------------------------------------------------- allowed_file
def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS



#################################### log & reg ##############################

#--------------------------------------------------------- /
@app.route('/')
def home():
    if 'user' in session:
        pass
    else:
        session['user'] = ""
    return render_template("index.html")

#--------------------------------------------------------- /validate_reg
@app.route('/validate_reg', methods=['POST'])
def validate_reg():
    is_valid = True # Error toggle
    
    if len(request.form['fname']) < 2 or not str.isalpha(request.form['fname']):
        flash("First name must contain at least two letters and contain only letters", 'fname')
        is_valid = False

    if len(request.form['lname']) < 2 or not str.isalpha(request.form['lname']):
        flash("Last name must contain at least two letters and contain only letters", 'lname')
        is_valid = False

    if not EMAIL_REGEX.match(request.form['email']) or (exists_in_database(request.form['email'], "email")): # or does exist in database
        flash("Invalid email address", 'email')
        is_valid = False

    if not validate_pass(request.form['pass']):
        flash("Password must contain a number, a capital letter, and be between 8-15 characters", 'pass')
        is_valid = False

    if len(request.form['pass_confirm']) < 8 or request.form['pass_confirm'] != request.form['pass']:
        flash("Passwords must match", 'pass_confirm')
        is_valid = False

    if is_valid == False:
        return redirect('/')
    else:
        user_pass = hash_pass(request.form['pass'])
        success = store_user(request.form, user_pass)
        if success:
            session['user'] = get_user(request.form['email'])
            flash("Your account has successfully been registered!", 'success')
            return redirect('/home')
        else:
            flash("An error has occurred", 'must_login')
            return redirect('/')

#--------------------------------------------------------- /validate_log
@app.route('/validate_log', methods=['POST'])
def validate_log():
    is_valid = True

    if exists_in_database(request.form['email'], 'email') == False:
        flash("Invalid email", 'invalid_email')
        is_valid = False
        

    if not bcrypt.check_password_hash(exists_in_database(request.form['email'], "password"), request.form['pass']):
        flash("Invalid password", 'invalid_pass')
        is_valid = False

    if not is_valid:
        return redirect('/')
    else:
        session['user'] = get_user(request.form['email'])
        return redirect('/home')

#--------------------------------------------------------- /home
@app.route('/home')
def success():
    if session['user'] != "":
        mysql = connectToMySQL("my_library")
        query = "SELECT book_id, title, author, description, genre, featured, image FROM books WHERE featured = 1;"
        results = mysql.query_db(query)
        mysql = connectToMySQL("my_library")
        query = "SELECT event_name, date, time, description, cost FROM events WHERE date > %(today)s;"
        data = { "today": datetime.datetime.now() }
        results2 = mysql.query_db(query, data)
        print(results2)
        return render_template("home.html", name = session['user'][0]['first_name'], featured_books = results, all_events = results2)
    else:
        flash("User must be logged in to view home page", 'must_login')
        return redirect('/')

#--------------------------------------------------------- /logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

#################################### library app ##############################

#--------------------------------------------------------- /search
@app.route('/search')
def search():
    return render_template("search.html")

#--------------------------------------------------------- /results
@app.route('/results', methods=['POST'])
def results():
    mysql = connectToMySQL("my_library")
    query = f"SELECT * FROM books WHERE {request.form['searchBy_list']} LIKE '%{request.form['keyword']}%';"
    # data = {
    #     "col": request.form['searchBy_list'],
    #     "term": request.form['keyword']
    # }
    results = mysql.query_db(query)
    return render_template("results.html", all_results = results, searchTerm = request.form['keyword'])

#--------------------------------------------------------- /show_all
@app.route('/show_all')
def show_all():
    mysql = connectToMySQL("my_library")
    query = "SELECT * FROM books"
    all_books = mysql.query_db(query)
    return render_template("show_all.html", all_books = all_books)

#--------------------------------------------------------- /show_book/<id>
@app.route('/show_book/<id>')
def show_book(id):
    mysql = connectToMySQL("my_library")
    query = "SELECT title, author, description, status FROM books WHERE book_id = %(id)s;"
    data = { "id": id }
    result = mysql.query_db(query, data)
    return render_template("show_book.html", book = result[0])

#--------------------------------------------------------- /add_book
@app.route('/add_book')
def add_book():
    if session['user'][0]['user_group'] == "admin":
        return render_template("add_book.html")
    else:
        return redirect("/home")

#--------------------------------------------------------- /process_book
@app.route('/process_book/<filename>', methods=['POST'])
def process_book(filename):
    arr = ['title', 'author', 'description', 'genre']
    is_valid = validate_input(request.form, arr)

    if not is_valid:
        return redirect('/add_book')


    mysql = connectToMySQL("my_library")
    query = "INSERT INTO books (title, author, description, genre, status, featured, created_at, updated_at, image) VALUES (%(t)s, %(a)s, %(d)s, %(g)s, 'available', false, NOW(), NOW(), %(f)s);"
    data = {
        "t": request.form['title'],
        "a": request.form['author'],
        "d": request.form['description'],
        "g": request.form['genre'],
        "f": filename, 
    }
    mysql.query_db(query, data)
    
    flash("Book has successfully been added!", 'success')
    
    return redirect('/add_book')

#--------------------------------------------------------- /checkout
@app.route('/checkout')
def checkout():
    return render_template("checkout.html")

#--------------------------------------------------------- /process_checkout
@app.route('/process_checkout', methods=['POST'])
def process_checkout():
    if len(request.form['user_id']) > 0 and len(request.form['book_id']) > 0:
        mysql = connectToMySQL("my_library")
        query = "UPDATE books SET status = 'unavailable' WHERE book_id = %(id)s;"
        data = { "id": request.form['book_id'] }
        mysql.query_db(query, data)

        mysql = connectToMySQL("my_library")
        query = "INSERT INTO orders (user_id, book_id, created_at, returned_at) VALUES (%(uid)s, %(bid)s, NOW(), null);"
        data = {
            "uid": request.form['user_id'],
            "bid": request.form['book_id'],
        }
        mysql.query_db(query, data)
        flash("Book has successfully been checked out!", 'success')
    else:
        flash("An error has occured", 'error')
    
    
    return redirect('/checkout')

#--------------------------------------------------------- /checkin
@app.route('/checkin')
def checkin():
    return render_template("checkin.html")

#--------------------------------------------------------- /process_checkin
@app.route('/process_checkin', methods=['POST'])
def process_checkin():
    if len(request.form['user_id']) > 0 and len(request.form['book_id']) > 0:
        mysql = connectToMySQL("my_library")
        query = "UPDATE books SET status = 'available' WHERE book_id = %(id)s;"
        data = { "id": request.form['book_id'] }
        mysql.query_db(query, data)

        mysql = connectToMySQL("my_library")
        query = "UPDATE orders SET returned_at = NOW() WHERE book_id = %(bid)s and user_id = %(uid)s and returned_at IS NULL;"
        data = {
            "bid": int(request.form['book_id']),
            "uid": int(request.form['user_id']),
        }
        mysql.query_db(query, data)
        flash("Book has successfully been checked in!", 'success')
    else:
        flash("An error has occured", 'error')

    return redirect('/checkin')

#--------------------------------------------------------- /get_user
@app.route('/get_user')
def find_user_by_email(): 
    if session['user'][0]['user_group'] == "admin":
        return render_template("get_user.html")
    else:
        return redirect("/home")

#--------------------------------------------------------- /update_user
@app.route('/update_user', methods = ['POST'])
def update_user():
    if not exists_in_database(request.form['email'], 'email'):
        flash("This account does not exist", "error")
        return redirect("/get_user")
    else:
        mysql = connectToMySQL("my_library")
        query = "SELECT * FROM users WHERE email=%(em)s;"
        data = { "em": request.form['email'] }
        result = mysql.query_db(query, data)
        return render_template("update_user.html", user = result[0])
        

#--------------------------------------------------------- /process_user_update
@app.route('/process_user_update/<email>', methods=['POST'])
def process_user_update(email):
    arr = ['fname', 'lname', 'email', 'password', 'bal']
    is_valid = validate_input(request.form, arr)
    valid_pass = validate_pass(request.form['password'])
    if not is_valid or not valid_pass:
        return redirect('/update_user')
    else:
        mysql = connectToMySQL("my_library")
        if len(request.form['password']) > 0:
            query = "UPDATE users SET first_name = %(fn)s, last_name = %(ln)s, email = %(em)s, password = %(pw)s, user_group = %(g)s, balance = %(b)s WHERE email = %(em)s"
            data = {
                "fn": request.form['fname'],
                "ln": request.form['lname'],
                "em": request.form['email'],
                "pw": hash_pass(request.form['password']),
                "g": request.form['group'],
                "b": request.form['bal'],
            }
        else:
            query = "UPDATE users SET first_name = %(fn)s, last_name = %(ln)s, email = %(em)s, user_group = %(g)s, balance = %(b)s WHERE email = %(em)s"
            data = {
                "fn": request.form['fname'],
                "ln": request.form['lname'],
                "em": request.form['email'],
                "g": request.form['group'],
                "b": request.form['bal'],
            }

        mysql.query_db(query, data)
        flash("User has been successfully updated!", 'success')
        return redirect('/get_user')

#--------------------------------------------------------- /user_profile
@app.route('/user_profile')
def user_profile():
    mysql = connectToMySQL("my_library")
    query = "SELECT * FROM orders JOIN books ON orders.book_id = books.book_id WHERE orders.user_id = %(id)s AND returned_at IS NULL;"
    data = { "id": session['user'][0]['user_id'] }
    results = mysql.query_db(query, data)
    return render_template("profile.html", all_books = results)

#--------------------------------------------------------- /order_history
@app.route('/order_history')
def order_history():
    mysql = connectToMySQL("my_library")
    query = "SELECT title, author, orders.created_at, orders.returned_at FROM books JOIN orders on books.book_id = orders.book_id WHERE orders.user_id = %(id)s;"
    data = { "id": session['user'][0]['user_id'] }
    results = mysql.query_db(query, data)
    return render_template("history.html", books_history = results)

#--------------------------------------------------------- /process_featured/<id>/<featured>
@app.route('/process_feature/<id>/<featured>')
def process_feature(id, featured):
    mysql = connectToMySQL("my_library")

    if featured == "1":
        query = "UPDATE books SET featured = 0 WHERE book_id = %(id)s;"
    else:        
        query = "UPDATE books SET featured = 1 WHERE book_id = %(id)s;"

    data = { "id": id }
    mysql.query_db(query, data)
    return redirect('/home')

#--------------------------------------------------------- /upload_file
@app.route('/upload_file', methods=['GET', 'POST'])
def upload_file():
    filename = ''
    if request.method == 'POST':
        print("Inside post if")
        if 'file' not in request.files:
            print("Inside first if")
            flash("No file part", 'file')
            return redirect('/home')
        file = request.files['file']
        if file.filename == '':
            print("inside second if")
            flash("No selected file", 'file')
            return redirect('/add_book')
        if file and allowed_file(file.filename):
            print("inside third if")
            filename = secure_filename(file.filename)
            print(filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return render_template("add_book.html", file_name = filename)

#--------------------------------------------------------- /add_event
@app.route('/add_event')
def add_event():
    if session['user'][0]['user_group'] == "admin":
        return render_template("add_event.html")
    else:
        return redirect('/home')

#--------------------------------------------------------- /process_event
@app.route('/process_event', methods=['POST'])
def process_event():
    if session['user'][0]['user_group'] == "admin":
        mysql = connectToMySQL("my_library")
        query = "INSERT INTO events (event_name, date, time, description, cost, hosted_by, contact_name, contact_phone, contact_address, contact_email, created_at, updated_at) VALUES (%(ename)s, %(date)s, %(time)s, %(descr)s, %(cost)s, %(host)s, %(cname)s, %(cphone)s, %(cadd)s, %(cemail)s, NOW(), NOW());"
        data = {
            "ename": request.form['event_name'],
            "date": request.form['date'],
            "time": request.form['time'],
            "descr": request.form['description'],
            "cost": request.form['cost'],
            "host": request.form['hosted_by'],
            "cname": request.form['contact_name'],
            "cphone": request.form['contact_phone'],
            "cadd": request.form['contact_address'],
            "cemail": request.form['contact_email'],
        }
        mysql.query_db(query, data)
        flash("Event successfully added!", 'success')
        return redirect('/add_event')
    return redirect('/home')

#--------------------------------------------------------- /update_event
@app.route('/update_event', methods=['POST'])
def update_event():
    if session['user'][0]['user_group'] == "admin":
        mysql = connectToMySQL("my_library")
        query = "SELECT * FROM events WHERE event_id = %(id)s;"
        data = { "id": request.form['event'] }
        result = mysql.query_db(query, data)
        print(id)
        print(result)
        return render_template("update_event.html", event_info = result[0])
    else:
        return redirect('/home')

#--------------------------------------------------------- /choose_event
@app.route('/choose_event')
def choose_event():
    if session['user'][0]['user_group'] == "admin":
        mysql = connectToMySQL("my_library")
        query = "SELECT event_id, event_name FROM events;"
        results = mysql.query_db(query)
        return render_template("choose_event.html", all_events = results)
    return redirect('/home')

#--------------------------------------------------------- /process_update_event
@app.route('/process_update_event', methods=['POST'])
def process_update_event():
    if session['user'][0]['user_group'] == "admin":
        mysql = connectToMySQL("my_library")
        query = "UPDATE events SET event_name = %(ename)s, date = %(date)s, time = %(time)s, description = %(descr)s, cost = %(cost)s, hosted_by = %(host)s, contact_name = %(cname)s, contact_phone = %(phone)s, contact_address = %(caddress)s, contact_email = %(e)s WHERE event_id = %(id)s;"
        data = { 
            "ename": request.form['event_name'],
            "date": request.form['date'],
            "time": request.form['time'],
            "descr": request.form['description'],
            "cost": request.form['cost'],
            "host": request.form['hosted_by'],
            "cname": request.form['contact_name'],
            "phone": request.form['contact_phone'],
            "caddress": request.form['contact_address'],
            "e": request.form['contact_email'],
            "id": request.form['id']
        }
        mysql.query_db(query, data)
        flash("Event successfully updated", 'success')
        return redirect('/choose_event')
    return redirect('/home')
    



#################################### end ##############################

if __name__=="__main__":
    app.run(debug=True)