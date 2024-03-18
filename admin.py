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
                       
bp = Blueprint("admin", __name__, url_prefix="/admin")



@bp.route("/check_register_request", methods=["GET","POST"])
def check_register_request():
    cursor = getCursor()
    # Check if any pending regstration requests exist
    cursor.execute('select * from register_request where approval_status = "pending"')
    requestlist = cursor.fetchall()
    if requestlist and request.method == 'GET':
        flash('Some student account registration requests are awaiting approval. Please select a student and add more information for the student to approve the registration.')
        return render_template('admin/check_register_request.html', requestlist=requestlist)  
    
    elif requestlist and request.method=='POST':
        user_email = request.form.get('user_email')
        cursor.execute('select * from register_request where user_email = %s', (user_email, ))
        requestlist = cursor.fetchone()
        fname = requestlist[2]
        lname = requestlist[3]

        print(fname, lname)
        cursor.execute ('select staff_email, fname, lname from staff join user on user_email=staff_email where user_role = "PG Supervisor"')
        superv_list = cursor.fetchall()
        
        return render_template('admin/approve_register.html', requestlist=requestlist, user_email = user_email, fname=fname, lname=lname, superv_list=superv_list)
    
    else:
        flash('There are no pending registration requests!')
        return redirect(url_for('admin.home'))
    
    
@bp.route('/approve_register', methods=["GET","POST"])
def approve_register():
    cursor = getCursor()  
    if request.method == 'POST':
        user_email = request.form.get('user_email')
        cursor.execute('select * from register_request where user_email = %s', (user_email, ))
        requestlist = cursor.fetchone()
        fname = request.form.get('fname')
        lname = request.form.get('lname')
        user_role= 'PG Student'
        password = request.form.get('password') 
        department_id = request.form.get('department_id')
        enrolment_date = request.form.get('enrolment_date')
        phone = request.form.get('phone')
        address = request.form.get('address')
        student_type = request.form.get('student_type')
        thesis_title = request.form.get('thesis_title')
        main_superv_email = request.form.get('main_superv_email')
        asst_superv_email = request.form.get('asst_superv_email')
        other_superv_email = request.form.get('other_superv_email')

        cursor.execute ('UPDATE register_request SET approval_status = "approved" where user_email = %s', (user_email, ))

        cursor.execute('INSERT INTO user VALUES (%s, %s, %s, "active")', (user_email, user_role, password, ))
        
        if other_superv_email:
            cursor.execute('INSERT INTO student VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', (user_email, fname, lname, department_id, enrolment_date, phone, address, student_type, thesis_title, main_superv_email, asst_superv_email, other_superv_email, ))
        else:
            cursor.execute('INSERT INTO student VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NULL)', (user_email, fname, lname, department_id, enrolment_date, phone, address, student_type, thesis_title, main_superv_email, asst_superv_email, ))
            
        flash("Student account for " + fname + " " + lname + " has been approveded!")
        
        cursor.execute('select student_email, student.fname, student.lname, approval_status, enrolment_date, department_name from student join department on student.department_id=department.department_id join register_request on student.student_email = register_request.user_email where student_email = %s', (user_email, ))
        requestlist = cursor.fetchone()

        return render_template('admin/approved_list.html', requestlist=requestlist)

    if request.method == 'GET':
        return render_template('admin/approved_list.html')

    
@bp.route('/')
@login_required
def home():
    return render_template('admin/admin.html', title='Home')

@bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('admin/dashboard.html', title='Dashboard')
    

@bp.route("/<user_email>/update", methods=("GET", "POST"))
@login_required
def update(user_email):
    pass


@bp.route('/profile')
@login_required
def profile():
    return render_template('admin/profile.html', title='Profile')

@bp.route('/settings')
@login_required
def settings():
    return render_template('admin/settings.html', title='Settings')

@bp.route('/MR')
@login_required
def MR():
    return render_template('admin/6MR.html', title='6MR')

@bp.route('/A')
@login_required
def A():
    return render_template('admin/A.html', title='Section A')

@bp.route('/B')
@login_required
def B():
    return render_template('admin/B.html', title='Section B')

@bp.route('/C')
@login_required
def C():
    return render_template('admin/C.html', title='Section C')

@bp.route('/D')
@login_required
def D():
    return render_template('admin/D.html', title='Section D')

@bp.route('/E')
@login_required
def E():
    return render_template('admin/E.html', title='Section E')


@bp.route('/F')
@login_required
def F():
    return render_template('admin/F.html', title='Section F', )

@bp.route('/ESupervisor_main')
@login_required
def Esupervisormain():
    return render_template('admin/Esupervisormain.html', title='Section E Main Supervisor')

@bp.route('/ESupervisor_asst')
@login_required
def Esupervisorasst():
    return render_template('admin/Esupervisorasst.html', title='Section E Associate Supervisor')

@bp.route('/ESupervisor_other')
@login_required
def Esupervisorother():
    return render_template('admin/Esupervisorother.html', title='Section E Other Supervisor')

@bp.route("/adminadduser", methods=["GET", "POST"])
@login_required
def adminadduser():
    return render_template('admin/addminadduser.html', title='Admin Add User')

@bp.route("/reportconcerns")
@login_required
def reportconcern():
    cur = getCursor()
    cur.execute("SELECT * FROM completed_report_status INNER JOIN report ON completed_report_status.report_id = report.report_id INNER JOIN e_assessment ON completed_report_status.report_id = e_assessment.report_id WHERE completed_report_status.orange IS NOT NULL OR completed_report_status.red IS NOT NULL")
    return render_template('admin/reportconcern.html', title='Report Concerns')

@bp.route('/adduser', methods=["GET", "POST"])
def adduser():
    Firstname = request.form.get("firstname")
    Surname = request.form.get("surname")
    Email = request.form.get("email")
    Phone = request.form.get("phone")
    Street = request.form.get("street")
    studenttype = request.form.get("studenttype")
    thesistitle = request.form.get("thesis")
    cur = getCursor()
    cur.execute("INSERT INTO student (fname, lname, student_email, phone, address, student_type, thesis_title) VALUES(%s,%s,%s,%s,%s,%s,%s);",(Firstname, Surname, Email, Phone, Street, studenttype, thesistitle))
    return redirect('addminadduser.html')


@bp.route('/addsuperv', methods=["GET", "POST"])
def addsuperv():
    StaffFname = request.form.get("supfname")
    StaffSname = request.form.get("supsname")
    StaffEmail = request.form.get("staffemail")
    StaffPhone = request.form.get("staffphone")
    cur = getCursor()
    cur.execute("INSERT INTO staff (fname, lname, staff_email, phone) VALUES(%s,%s,%s,%s);",(StaffFname, StaffSname, StaffEmail, StaffPhone))
    return redirect('addminadduser.html')

@bp.route('/sendadminemail', methods=["GET", "POST"])
def sendadminemail():
    AdmComments = request.form.get("admincomments")
    admemail = request.form.get("studentemailadd")
    staffmail = request.form.get("staffemailadd")
    rptnum = request.form.get("reportno")
    cur = getCursor()
    cur.execute("INSERT INTO e_assessment comments VALUES(%s,%s) WHERE reportid = %s;",(AdmComments, admemail,staffmail, rptnum))
    return redirect('reportconcern.html')
