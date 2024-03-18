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

bp = Blueprint("supervisor", __name__, url_prefix="/supervisor")


@bp.route('/')
@login_required
def home():
    return redirect(url_for('supervisor.supervisor'))

@bp.route('/home')
def supervisor():
    user_email=session['user_email']
    cur = getCursor()
    cur.execute('SELECT fname, lname FROM staff WHERE staff_email = %s', (user_email,))
    user_name=cur.fetchone()
    firstname=user_name[0]
    lastname=user_name[1]
    return render_template('supervisor/supervisor.html', title='Home', firstname=firstname,lastname=lastname)


@bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('supervisor/dashboard.html', title='Dashboard')

### View & Update Supervisor Profile ###
@bp.route('/profile',methods=['get','post'])
@login_required
def profile():
    cur = getCursor()
    user_email = session['user_email']  
    if request.method =='GET':       
        cur.execute('''SELECT fname, lname, staff_email, department_name, phone FROM PGmonitoring.staff
                    JOIN department on staff.department_id = department.department_id
                    WHERE staff_email = %s;''', (user_email,))
        spvs_profile = cur.fetchall()
        column_names = [desc[0] for desc in cur.description]
        return render_template('supervisor/profile.html', title='Profile', spvs_profile=spvs_profile, column_names=column_names)
    else:
        phone=request.form.get('phone')
        cur.execute('''UPDATE staff SET phone = %s WHERE staff_email = %s;''', (phone, user_email))
        cur.execute('''SELECT fname, lname, staff_email, department_name, phone FROM PGmonitoring.staff
                    JOIN department on staff.department_id = department.department_id
                    WHERE staff_email = %s;''', (user_email,))
        spvs_profile = cur.fetchall()
        column_names = [desc[0] for desc in cur.description]
        flash("Your phone number has been updated successfully!")
        return render_template('supervisor/profile.html', title='Profile', spvs_profile=spvs_profile, column_names=column_names)

@bp.route('/settings')
@login_required
def settings():
    return render_template('supervisor/settings.html', title='Settings')

@bp.route('/MR')
@login_required
def MR():
    return render_template('supervisor/6MR.html', title='6MR')

### View 6MR Report: Section A ### --- Will be combined with user story no.7 and updated user interface to form template ---
@bp.route('/A')
@login_required
def A():
    cur = getCursor()
    user_email = session['user_email']
    cur.execute('''SELECT concat(fname,' ',lname) as 'Name', student_email as 'Email', department_name as 'Department Name', enrolment_date as 'Enrolment Date', phone as 'Phone', 
                student_type as 'Student Type', thesis_title as 'Thesis Title', main_superv_email as 'Main Supervisor', asst_superv_email as 'Assistant Supervisor', other_superv_email as 'Other Supervisor' FROM PGmonitoring.student
                JOIN department on student.department_id = department.department_id
                WHERE main_superv_email = %s or asst_superv_email = %s or other_superv_email = %s;''', (user_email, user_email, user_email,))
    section_A = cur.fetchall()
    column_names = [desc[0] for desc in cur.description]
    return render_template('supervisor/A.html', title='A', section_A=section_A, column_names=column_names, user_email=user_email)

### View 6MR Report: Section B 
@bp.route('/B')
@login_required
def B():
    cur = getCursor()
    user_email = session['user_email']
    cur.execute('''SELECT report.student_email, step, compulsory, complete_date, due_date, milestone FROM PGmonitoring.b_step
                JOIN report on report.report_id = b_step.report_id
                JOIN b_milestone on b_milestone.milestone_num = report.milestone_num
                JOIN student on student.student_email = report.student_email
                WHERE main_superv_email = %s or asst_superv_email = %s or other_superv_email = %s;''', (user_email, user_email, user_email,))
    section_B_step = cur.fetchall()
    column_names_step = [desc[0] for desc in cur.description]
    cur.execute('''SELECT report.student_email, committee, needed, approval FROM PGmonitoring.b_research_approval
                JOIN report on report.report_id = b_research_approval.report_id
                JOIN student on student.student_email = report.student_email
                WHERE main_superv_email = %s or asst_superv_email = %s or other_superv_email = %s;''', (user_email, user_email, user_email,))
    section_B_approval = cur.fetchall()
    column_names_approval = [desc[0] for desc in cur.description]
    cur.execute('''SELECT student.student_email, milestone, months, due_date FROM PGmonitoring.b_milestone
                JOIN report on report.milestone_num = b_milestone.milestone_num
                JOIN student on student.student_email = report.student_email
                WHERE main_superv_email = %s or asst_superv_email = %s or other_superv_email = %s;''', (user_email, user_email, user_email,))
    section_B_milestone = cur.fetchall()
    column_names_milestone = [desc[0] for desc in cur.description]
    return render_template('supervisor/B.html', title='Section B', section_B_step=section_B_step, column_names_step=column_names_step, section_B_approval=section_B_approval, column_names_approval=column_names_approval, section_B_milestone=section_B_milestone, column_names_milestone=column_names_milestone)

@bp.route('/C')
@login_required
def C():
    return render_template('supervisor/C.html', title='Section C')

@bp.route('/D')
@login_required
def D():
    return render_template('supervisor/D.html', title='Section D')

@bp.route('/E')
@login_required
def E():
    return render_template('supervisor/E.html', title='Section E')


@bp.route('/ESupervisor_main')
@login_required
def Esupervisormain():
    return render_template('supervisor/Esupervisormain.html', title='Section E Main Supervisor')

@bp.route('/ESupervisor_asst')
@login_required
def Esupervisorasst():
    return render_template('supervisor/Esupervisorasst.html', title='Section E Associate Supervisor')

@bp.route('/ESupervisor_other')
@login_required
def Esupervisorother():
    return render_template('supervisor/Esupervisorother.html', title='Section E Other Supervisor')