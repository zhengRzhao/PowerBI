import functools

from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for
from flaskr.db import getCursor
from flask import jsonify
from flask import abort
from datetime import datetime
import json
import re, os, time
import threading

from flask import app
bp = Blueprint("auth", __name__, url_prefix="/auth")

def login_required(view):
    """View decorator that redirects anonymous user to the login page."""
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if session.get("user_email") is None:
            return redirect(url_for("auth.login"))
        return view(**kwargs)
    return wrapped_view


@bp.route("/login", methods= ["GET","POST"])
def login():
    session.clear()
    if session.get("user_email") is not None:
        flash("You are already logged in! Please logout to login as a different user.")
    else:
        session.clear()
        if request.method =='POST' and "user_email" in request.form and "password" in request.form:
            # Create variables for easy access
            user_email = request.form.get('user_email')
            password = request.form.get('password')
            # print(user_email)
            # print(password)
            # Check if account exists using MySQL
            cursor = getCursor()
            cursor.execute('select * from user where user_email = %s and password = %s', (user_email, password))
            # Fetch one record and return result
            account=cursor.fetchone()
            # print(account)
            if account is not None and account[3] == 'active' :
                password = account[2]
                if password == password:

                    session['loggedin'] = True
                    session['user_email'] = account[0]
                    session['user_role'] = account[1]

                    if session['user_role'] == 'PG Admin':
                        return redirect(url_for('admin.home'))
                
                    elif session['user_role'] == 'PG Student':
                        return redirect(url_for('student.home'))
                    
                    elif session['user_role'] == 'PG Supervisor':
                        return redirect(url_for('supervisor.home'))
                    
                    elif session['user_role'] == 'PG Convenor':
                        return redirect(url_for('convenor.home'))
                                
                    elif session['user_role'] == 'PG Chair':
                        return redirect(url_for('chair.home'))

                    else:
                        #password incorrect
                        # Show the login form with flash message (if any)
                        flash('Incorrect password! Login unsuccessful', 'danger')
                        
                else:
                    # Account doesnt exist or username incorrect
                    # Show the login form with flash message (if any)
                    flash('Incorrect username! Login unsuccessful', 'danger')
            
    return render_template('auth/login.html', title='Login')

    
@bp.route("/register", methods=["GET","POST"])
def register():
    session.clear()

    if request.method == 'POST' and 'user_email' in request.form and 'fname' in request.form and 'lname' in request.form:
        # Create variables for easy access
        user_email = request.form['user_email']
        fname = request.form['fname']
        lname = request.form['lname']
        
        # Check if account exists using MySQL
        cursor = getCursor()
        cursor.execute('select * from user where user_email = %s', (user_email, ))
        account = cursor.fetchone()
        if account:
            user_status=account[3]
    
        cursor = getCursor()
        cursor.execute('select * from register_request where user_email = %s', (user_email, ))
        register_request = cursor.fetchone()
        if register_request:
            request_status=register_request[4]
            
        # If account exists show error and validation checks
        if register_request and request_status == "pending":
            flash('Account registration is awaiting approval. Please contact administrator.')
        elif account and user_status == "inactive":
            flash('Account is inactive. Please contact administrator.')
        elif account and user_status == 'active':
            flash('Account already exists!')
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', user_email):
            flash('Invalid email address!')
        elif not account and not user_email and not fname and not lname:
            # Form is empty... (no POST data)
            flash('If you want to register a student account, please fill out the form and submit to administrator for approval. Otherwise, please contact administrator to register.')
        elif not account and not register_request:
            # Account doesnt exists and the form data is valid, now insert new account into the register request table
            cursor.execute ('INSERT INTO register_request (user_email, fname, lname, approval_status) VALUES (%s, %s, %s, "pending")', (user_email, fname, lname,))
            flash('Your student account registration request has been submitted to administrator for approval!')
            return redirect(url_for('homepage'))
        
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        flash('Please fill out the form!')
    return render_template('auth/register.html', title='Register')

@bp.route("/logout")
def logout():
    session.pop('loggedin', None)
    session.pop('user_email', None)
    session.pop('user_role', None)
    session.clear()
    return redirect(url_for('homepage'))


@bp.route("/reset_password", methods=["GET","POST"])
def reset_password():
    session.pop('loggedin', None)
    session.pop('user_email', None)
    session.pop('user_role', None)
    session.clear()
    if request.method == 'POST' and 'user_email' in request.form and 'password' in request.form:
        # Create variables for easy access
        user_email = request.form['user_email']
        password = request.form['password']
        # Check if account exists using MySQL
        cursor = getCursor()
        cursor.execute('select * from user where user_email = %s', (user_email, ))
        account = cursor.fetchone()
        # If account exists show error and validation checks
        if account:
            cursor.execute('UPDATE user SET password = %s WHERE user_email = %s', (password, user_email,))
            flash('Password reset successfully! Please login.')
            return redirect(url_for('auth.login'))
            
        else:
            flash('Account does not exist!')
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        flash('Please fill out the form!')
    # Show registration form with message (if any)
    return render_template('auth/reset_password.html', title='Reset Password')


# def get_reset_token(user_email, expires_sec=1800):
#     s = Serializer(app.config['SECRET_KEY'], expires_sec)
#     return s.dumps({'user_email': user_email}).decode('utf-8')