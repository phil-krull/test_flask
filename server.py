from flask import Flask, render_template, request, redirect, session, flash, jsonify
from mysqlconnection import connectToMySQL
from flask_bcrypt import Bcrypt
import re

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$') 

app = Flask(__name__)
bcrypt = Bcrypt(app)

app.secret_key = 'My super secret key'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    form = request.form
    errors = []
    if(len(form['first_name']) < 2):
        errors.append('First Name is required!')
    if(len(form['last_name']) < 2):
        errors.append('Last Name is required!')
    if(len(form['email']) < 2):
        errors.append('Email is required!')
    elif not EMAIL_REGEX.match(request.form['email']):
        errors.append('Please enter a valid email address!')
    else:
        mysql = connectToMySQL('thought_dashboard')
        query = 'SELECT * FROM users WHERE email = %(email)s;'
        data = {'email': form['email']}
        user = mysql.query_db(query, data)
        if len(user) > 0:
            errors.append('Email is already in use!')
    if(len(form['password']) < 8):
        errors.append('Password must be at least 8 characters long!')
    if form['password'] != form['confirm_password']:
        errors.append('Passwords must match!')


    if len(errors) < 1:
        hashed_pw = bcrypt.generate_password_hash(form['password'])
        mysql = connectToMySQL('thought_dashboard')
        query = 'INSERT INTO `thought_dashboard`.`users` (`first_name`, `last_name`, `email`, `password`) VALUES (%(f_name)s, %(l_name)s, %(email)s, %(password)s);'
        data = {'f_name': form['first_name'], 'l_name': form['last_name'], 'email': form['email'], 'password': hashed_pw}
        user_id = mysql.query_db(query, data)
        session['user_id'] = user_id
        return redirect('/dashboard')
    else:
        for error in errors:
            flash(error)
        return redirect('/')

@app.route('/login', methods=['post'])
def login():
    form = request.form
    mysql = connectToMySQL('thought_dashboard')
    query = 'SELECT * FROM users WHERE email = %(email)s;'
    data = {'email': form['email']}
    user = mysql.query_db(query, data)
    if len(user) < 1:
        flash('Email does not exist, please register')
    else:
        if bcrypt.check_password_hash(user[0]['password'], request.form['password']):
            session['user_id'] = user[0]['id']
            return redirect('/dashboard')
        else:
            flash('Invalid email/password combination!')
    return redirect('/')

@app.route('/email_check', methods=['post'])
def email_check():
    mysql = connectToMySQL('thought_dashboard')
    query = 'SELECT * FROM users WHERE email=%(email)s;'
    data = {'email': request.form['email']}
    user = mysql.query_db(query, data)
    found = False
    if len(user) > 0:
        found = True

    return render_template('partials/email.html', found = found)


@app.route('/logout', methods=['post'])
def logout():
    session.clear()
    return redirect('/')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Must be logged in to continue')
        return redirect('/')
    mysql = connectToMySQL('thought_dashboard')
    query = 'SELECT * FROM users WHERE id = %(user_id)s;'
    data = {'user_id': session['user_id']}
    user = mysql.query_db(query, data)

    mysql = connectToMySQL('thought_dashboard')
    query = 'SELECT thoughts.id, thoughts.thought, users.id AS user_id, users.first_name AS user_name FROM thoughts JOIN users ON users.id = thoughts.user_id;'
    thoughts = mysql.query_db(query)

    return render_template('dashboard.html', user = user[0], thoughts = get_thoughts())

@app.route('/thoughts', methods=['post'])
def thoughts():
    if 'user_id' not in session:
        flash('Must be logged in to continue')
        return redirect('/')
    
    user_id = session['user_id']

    if len(request.form['thought']) < 5:
        flash('Your thought is too short!')
        return jsonify(status = False, data = render_template('partials/thought_errors.html'))
    else:
        mysql = connectToMySQL('thought_dashboard')
        query = 'INSERT INTO thoughts (thought, user_id) VALUES (%(thought)s, %(user_id)s);'
        data = {'thought': request.form['thought'], 'user_id': user_id}
        mysql.query_db(query, data)
        return jsonify(status = True, data = render_template('partials/thoughts.html', user = session['user_id'], thoughts = get_thoughts()))

@app.route('/thoughts/<thought_id>/delete')
def delete(thought_id):
    if 'user_id' not in session:
        flash('Must be logged in to continue')
        return redirect('/')

    mysql = connectToMySQL('thought_dashboard')
    query = 'DELETE FROM thoughts WHERE id = %(thought_id)s;'
    data = {'thought_id': thought_id}
    mysql.query_db(query, data)

    return render_template('partials/thoughts.html', user = session['user_id'], thoughts = get_thoughts())

@app.route('/users/<user_id>')
def show(user_id):
    if 'user_id' not in session:
        flash('Must be logged in to continue')
        return redirect('/')
    mysql = connectToMySQL('thought_dashboard')
    query = 'SELECT users.first_name, thoughts.thought FROM users JOIN thoughts ON users.id = thoughts.user_id WHERE users.id = %(user_id)s;'
    data = {'user_id': session['user_id']}
    thoughts = mysql.query_db(query, data)

    return render_template('show.html', thoughts = thoughts)


@app.route('/thoughts/<thought_id>/like')
def like(thought_id):
    if 'user_id' not in session:
        flash('Must be logged in to continue')
        return redirect('/')

    mysql = connectToMySQL('thought_dashboard')
    query = 'INSERT INTO likes (user_id, thought_id) VALUES (%(user)s, %(thought)s);'
    data = {'user': session['user_id'], 'thought': thought_id}
    mysql.query_db(query, data)

    return render_template('partials/thoughts.html', user = session['user_id'], thoughts = get_thoughts())

@app.route('/thoughts/<thought_id>/unlike')
def unlike(thought_id):
    if 'user_id' not in session:
        flash('Must be logged in to continue')
        return redirect('/')

    mysql = connectToMySQL('thought_dashboard')
    query = 'DELETE FROM likes WHERE user_id = %(user)s AND thought_id = %(thought)s;'
    data = {'user': session['user_id'], 'thought': thought_id}
    mysql.query_db(query, data)

    return render_template('partials/thoughts.html', user = session['user_id'], thoughts = get_thoughts())

def get_thoughts():
    mysql = connectToMySQL('thought_dashboard')
    query = 'SELECT thoughts.id, thoughts.thought, thoughts.user_id, users.first_name AS user_name, COUNT(likes.thought_id) AS num_of_likes FROM thoughts JOIN users ON users.id = thoughts.user_id LEFT JOIN likes on thoughts.id = likes.thought_id GROUP BY thoughts.id'
    thoughts =  mysql.query_db(query)

    updated_thoughts = []

    for thought in thoughts:
        likes = get_likes(thought['id'])
        thought['user_likes'] = []
        for like in likes:
            thought['user_likes'].append(like['user_id'])
        updated_thoughts.append(thought)

    return updated_thoughts

def get_likes(thought_id):
    mysql = connectToMySQL('thought_dashboard')
    query = 'SELECT * FROM likes WHERE thought_id = %(thought_id)s;'
    data = {'thought_id': thought_id}
    return mysql.query_db(query, data)




if __name__ == '__main__':
    app.run(debug=True, port=5001)