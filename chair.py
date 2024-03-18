from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for
from werkzeug.exceptions import abort
from flaskr.db import getCursor
from flaskr.auth import login_required

bp = Blueprint("chair", __name__, url_prefix="/chair")


@bp.route('/')
@login_required
def home():
    return redirect(url_for('chair.chair'))

@bp.route('/home')
def chair():
    user_email=session['user_email']
    cur = getCursor()
    cur.execute('SELECT fname, lname FROM staff WHERE staff_email = %s', (user_email,))
    user_name=cur.fetchone()
    firstname=user_name[0]
    lastname=user_name[1]
    return render_template('chair/chair.html', title='Home', firstname=firstname,lastname=lastname)



@bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('chair/dashboard.html', title='Dashboard')

@bp.route('/profile')
@login_required
def profile():
    return render_template('chair/profile.html', title='Profile')

@bp.route('/settings')
@login_required
def settings():
    return render_template('chair/settings.html', title='Settings')

@bp.route('/MR')
@login_required
def MR():
    return render_template('chair/6MR.html', title='6MR')

@bp.route('/A')
@login_required
def A():
    return render_template('chair/A.html', title='Section A')

@bp.route('/B')
@login_required
def B():
    return render_template('chair/report/B.html', title='Section B')

@bp.route('/C')
@login_required
def C():
    return render_template('chair/C.html', title='Section C')

@bp.route('/D')
@login_required
def D():
    return render_template('chair/D.html', title='Section D')

@bp.route('/E')
@login_required
def E():
    return render_template('chair/E.html', title='Section E')

@bp.route('/F')
@login_required
def F():
    return render_template('chair/F.html', title='Section F', )