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

bp = Blueprint("convenor", __name__, url_prefix="/convenor")

@bp.route('/')
@login_required
def home():
    return redirect(url_for('convenor.convenor'))

@bp.route('/home')
def convenor():
    user_email=session['user_email']
    cur = getCursor()
    cur.execute('SELECT fname, lname FROM staff WHERE staff_email = %s', (user_email,))
    user_name=cur.fetchone()
    firstname=user_name[0]
    lastname=user_name[1]
    return render_template('convenor/convenor.html', title='Home', firstname=firstname,lastname=lastname)

@bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('convenor/dashboard.html', title='Dashboard')

@bp.route('/profile')
@login_required
def profile():
    return render_template('convenor/profile.html', title='Profile')

@bp.route('/settings')
@login_required
def settings():
    return render_template('convenor/settings.html', title='Settings')

@bp.route('/MR')
@login_required
def MR():
    return render_template('convenor/6MR.html', title='6MR')

@bp.route('/A')
@login_required
def A():
    return render_template('convenor/A.html', title='Section A')

@bp.route('/B')
@login_required
def B():
    return render_template('convenor/B.html', title='Section B')

@bp.route('/C')
@login_required
def C():
    return render_template('convenor/C.html', title='Section C')

@bp.route('/D')
@login_required
def D():
    return render_template('convenor/D.html', title='Section D')

@bp.route('/E')
@login_required
def E():
    return render_template('convenor/E.html', title='Section E')


@bp.route('/ESupervisor_main')
@login_required
def Esupervisormain():
    return render_template('convenor/Esupervisormain.html', title='Section E Main Supervisor')

@bp.route('/ESupervisor_asst')
@login_required
def Esupervisorasst():
    return render_template('convenor/Esupervisorasst.html', title='Section E Associate Supervisor')

@bp.route('/ESupervisor_other')
@login_required
def Esupervisorother():
    return render_template('convenor/Esupervisorother.html', title='Section E Other Supervisor')

@bp.route('/EConvenor')
@login_required
def Econvenor():
    return render_template('convenor/Econvenor.html', title='Section E Convenor')