from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for
import smtplib
from email.message import EmailMessage
from werkzeug.exceptions import abort
from flaskr.db import getCursor
from flaskr.auth import login_required
from datetime import date,datetime

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
    cur = getCursor()
    cur.execute("""SELECT student.fname, student.lname, student.student_email, user.user_email, report.report_id, report.due_date, progress.actioner_email, progress.action_date, progress.action_type, completed_report_status.orange, completed_report_status.red, completed_report_status.green, completed_report_status.no_indicator, f_stud_assessment.comments, e_assessment.performance, e_assessment.comments, e_assessment.status FROM student left outer join user on student_email = user_email left outer join report on student.student_email = report.student_email left outer join completed_report_status ON report.report_id = completed_report_status.report_id left outer join progress ON report.report_id = progress.report_id left outer join e_assessment ON report.report_id = e_assessment.report_id left outer join f_stud_assessment on report.report_id = f_stud_assessment.report_id WHERE student.student_email IS NOT NULL""")
    results = cur.fetchall()
    return render_template('chair/dashboard.html', title='Dashboard', results=results)


@bp.route('/profile')
@login_required
def profile():
    return render_template('chair/profile.html', title='Profile')

@bp.route('/settings')
@login_required
def settings():
    return render_template('chair/settings.html', title='Settings')

@bp.route('/F', methods=["GET","POST"])
@login_required
def F():
    user_email=session['user_email']
    cur = getCursor()
    cur.execute('SELECT fname, lname FROM staff WHERE staff_email = %s', (user_email,))
    user_name=cur.fetchone()
    firstname=user_name[0]
    lastname=user_name[1]

    if request.method == "GET":        
        cur = getCursor()
        cur.execute ("select f_stud_assessment.report_id as 'Report ID',actioner_email as 'Reporter Email',\
                     action_date as 'Reported Date' from progress left join f_stud_assessment\
                     on progress.report_id = f_stud_assessment.report_id where action_type='F Completed';")
        reportlist = cur.fetchall()
        if reportlist == None: #if no reports (Section F)are found
            flash('No action is needed on any reports.')
            return redirect(url_for('chair.home'))
        else:
            return render_template('chair/F.html', title='Section F', reportlist=reportlist, firstname=firstname,lastname=lastname)
    

    if request.method == "POST":        
        reporter_email = request.form.get('actioner_email')
        cur = getCursor()
        cur.execute ("SELECT fname, lname FROM student WHERE student_email = %s;", (reporter_email,))
        user_name2=cur.fetchone()       
        firstname=user_name2[0]       
        lastname=user_name2[1]       
        fullname=f'{firstname} {lastname}'
        cur.execute('SELECT CONCAT(t1.fname," ", t1.lname) AS Supervisor, CONCAT(t2.fname," ", t2.lname)\
                                AS AssSupervisor, CONCAT(t3.fname," ", t3.lname) AS OtherSupervisor FROM student AS\
                                s LEFT JOIN staff AS t1 ON s.main_superv_email = t1.staff_email\
                                LEFT JOIN staff AS t2 ON s.asst_superv_email = t2.staff_email LEFT JOIN staff as t3\
                                ON s.other_superv_email = t3.staff_email WHERE s.student_email = %s;',(reporter_email,))
        supervisors=cur.fetchall()       
        cur.execute("select comments from progress left join f_stud_assessment on progress.report_id = f_stud_assessment.report_id\
                    where action_type='F Completed' and actioner_email = %s;",(reporter_email,))
        comments=cur.fetchall()
        print(comments)
        return render_template('chair/report_details.html', title='Section F', reporter_email=reporter_email,fullname=fullname,firstname=firstname,lastname=lastname,supervisors=supervisors,comments=comments)
    
@bp.route('/sendreminder', methods=["GET","POST"])
@login_required
def sendreminder():
    reporter_email = request.form.get('reporter_email')
    print(reporter_email)
    if sendreminder:
        msg = EmailMessage()
        msg['Subject'] = 'Reminder: Feedback on your section F of 6MR.'
        msg['From'] = 'ccomp639project@gmail.com'
        msg['To'] = 'comp639project@gmail.com'
        msg['Bcc'] = reporter_email
        text_content = request.form.get('comments')
        msg.set_content('This is a reminder: Your section F of 6MR has been provided with feedback as follows: \n' + text_content + 
                        '\n Thank you!')
        smtp=smtplib.SMTP('smtp.gmail.com', 587)
        smtp.starttls()
        smtp.login('comp639project@gmail.com', 'yncrimbapjfiawdw') ## login
        text=msg.as_string()
        smtp.sendmail('ccomp639project@gmail.com', reporter_email, text)
        smtp.quit()
        print(msg['To'],msg['Bcc'])
        print('email sent')
    flash('The reminder email has been sent to the student who got the feedback from the chairperson.')
    return redirect(url_for('chair.home'))

@bp.route('/MR')
@login_required
def MR():
    return render_template('chair/6MR.html', title='6MR')

@bp.route('/mystudent')
@login_required
def mystudent():
    user_email = session['user_email']
    studentemail=request.args.get('studentemail')
    todaydate = date.today()
    if todaydate.month <= 6:
            due_date = date(todaydate.year, 6, 30)
            print(due_date)
    else:
            due_date = date(todaydate.year, 12, 31)

    cur = getCursor()
    cur.execute("""SELECT r.report_id, student_email, due_date, action_date FROM report as r
                JOIN progress as p on p.report_id = r.report_id
                WHERE action_type = 'Submitted' and due_date = %s;"""(due_date,))
    students = cur.fetchall()

    return render_template('chair/mystudent.html', title='mystudent', students=students)


@bp.route("/reportprogress")
@login_required
def reportprogress():
    today = date.today()
    if today.month <= 6:
        due_date = date(today.year, 6, 30)
    else:
        due_date = date(today.year, 12, 31)

    cur=getCursor()
    cur.execute("SELECT s.student_email, s.fname, s.lname, s.department_id, IFNULL(r.report_id, NULL)\
                 AS report_id, IFNULL(r.milestone_num,1),IFNULL(r.due_date,%s) AS due_date\
                 FROM student AS s JOIN user AS u ON u.user_email = s.student_email\
                LEFT JOIN (SELECT student_email, MAX(report_id) AS max_report_id FROM report GROUP BY student_email)\
                 AS r1 ON r1.student_email = s.student_email LEFT JOIN report AS r ON r.student_email = s.student_email\
                 AND r.report_id = r1.max_report_id WHERE u.status = 'active' ORDER BY s.student_email;",(due_date,))
    studentlist=cur.fetchall()
    
    status_list = []
    incompletedactioneremail_list = []

    for student in studentlist:
        studentemail=student[0]
        cur=getCursor()
        studentreportid=student[4]
        cur.execute('SELECT action_type FROM progress WHERE report_id=%s ORDER BY event_id DESC limit 1;',(studentreportid,))
        statuses=cur.fetchall()
        
        if len(statuses) > 0 and statuses[0][0]=='Submitted':
            cur=getCursor()
            cur.execute('SELECT main_superv_email from student WHERE student_email=%s;',(studentemail,))
            status=statuses[0][0]
            incompletedactioneremail=cur.fetchall()[0][0]
        elif len(statuses) > 0 and statuses[0][0]=='1 Rejected':
            status=statuses[0][0]
            incompletedactioneremail=studentemail
        elif len(statuses) > 0 and statuses[0][0]=='1 Submitted':
            cur=getCursor()
            cur.execute('SELECT asst_superv_email from student WHERE student_email=%s;',(studentemail,))
            incompletedactioneremail=cur.fetchall()[0][0]
            status=statuses[0][0]
        elif len(statuses) > 0 and statuses[0][0]=='2 Submitted':
            cur=getCursor()
            cur.execute('SELECT other_superv_email from student WHERE student_email=%s;',(studentemail,))
            othersuperv=cur.fetchall()[0][0]
            status=statuses[0][0]
            if othersuperv:
                incompletedactioneremail=cur.fetchall()[0][0]
            else:
                cur=getCursor()
                cur.execute("SELECT n.user_email FROM (SELECT * FROM user JOIN staff ON user_email=staff_email WHERE user_role = 'PG Convenor' and status='active')\
                                AS n JOIN student AS s ON n.department_id=s.department_id WHERE s.student_email=%s;",(studentemail,))
                incompletedactioneremail=cur.fetchall()[0][0]
            
        elif len(statuses) > 0 and statuses[0][0]=='3 Submitted':
            cur=getCursor()
            cur.execute("SELECT n.user_email FROM (SELECT * FROM user JOIN staff ON user_email=staff_email WHERE user_role = 'PG Convenor' and status='active')\
                                AS n JOIN student AS s ON n.department_id=s.department_id WHERE s.student_email=%s;",(studentemail,))
            incompletedactioneremail=cur.fetchall()[0][0]
            status=statuses[0][0]
        elif len(statuses) > 0 and statuses[0][0]=='10 Submitted':
            incompletedactioneremail=None
            status=statuses[0][0]
        else:
            status='Unsubmitted'
            incompletedactioneremail=studentemail
                
        status_list.append(status)
        incompletedactioneremail_list.append(incompletedactioneremail)

    # print(status_list)
    # print(incompletedactioneremail_list)

    return render_template('chair/reportprogress.html', title='Report Progress',studentlist=studentlist,status_list=status_list, incompletedactioneremail_list=incompletedactioneremail_list)

    
@bp.route('/send_email', methods=["GET","POST"])
@login_required
def send_email():
    emails = request.form.getlist('emails')
    # print (emails)
    # recipients = recipients.append(recipients.pop())
    if send_email:
        msg = EmailMessage()
        msg['Subject'] = 'Reminder: Please complete your 6-Monthly Report!'
        msg['From'] = 'comp639project@gmail.com'
        msg['To'] = 'comp639project@gmail.com'
        msg['Bcc'] = emails
        msg.set_content('\n This is a reminder to complete and submit your 6-monthly report. \n \n Please submit section A, B, C, and D of the 6MR Report Form by the due date. \n \n Section F is optional but if it is submitted, it will be received and viewable only by the Chair of the Department.')
        smtp=smtplib.SMTP('smtp.gmail.com', 587)
        smtp.starttls()
        smtp.login('comp639project@gmail.com', 'yncrimbapjfiawdw') ## login
        text=msg.as_string()
        smtp.sendmail('comp639project@gmail.com', emails, text)
        smtp.quit()
        # print(msg['To'],msg['Bcc'])
        # print('email sent')
        flash('Reminders have been sent to students who have not submitted their 6-monthly report.')
        return redirect(url_for('chair.reportprogress'))

####################    
@bp.route('/searchreportprogress', methods=["POST"])
def searchreportprogress():
    current_date=date.today()
    if current_date.month <= 6:
        due_date = date(current_date.year, 6, 30)
    else:
        due_date = date(current_date.year, 12, 31)
    cur = getCursor() 
    searchitem = request.form.get("searchitem")
    today = date.today()
    if today.month <= 6:
        due_date = date(today.year, 6, 30)
    else:
        due_date = date(today.year, 12, 31)

    cur.execute("SELECT * FROM student WHERE student_email=%s or department_id=%s;",(searchitem,searchitem,))
    rightstudent=cur.fetchall()

    if rightstudent:
        cur=getCursor()
        cur.execute("SELECT * FROM (SELECT s.student_email AS semail, s.fname, s.lname, s.department_id AS deptid, IFNULL(r.report_id, NULL)\
                    AS report_id, IFNULL(r.milestone_num,1),IFNULL(r.due_date,%s) AS due_date\
                    FROM student AS s JOIN user AS u ON u.user_email = s.student_email\
                    LEFT JOIN (SELECT student_email, MAX(report_id) AS max_report_id FROM report GROUP BY student_email)\
                    AS r1 ON r1.student_email = s.student_email LEFT JOIN report AS r ON r.student_email = s.student_email\
                    AND r.report_id = r1.max_report_id WHERE u.status = 'active' ORDER BY s.student_email) AS tx WHERE tx.semail=%s or tx.deptid=%s;",(due_date, searchitem, searchitem))
        studentlist=cur.fetchall()
        
        
        status_list = []
        incompletedactioneremail_list = []

        for student in studentlist:
            studentemail=student[0]
            cur=getCursor()
            studentreportid=student[4]
            cur.execute('SELECT action_type FROM progress WHERE report_id=%s ORDER BY event_id DESC limit 1;',(studentreportid,))
            statuses=cur.fetchall()
            
            if len(statuses) > 0 and statuses[0][0]=='Submitted':
                cur=getCursor()
                cur.execute('SELECT main_superv_email from student WHERE student_email=%s;',(studentemail,))
                status=statuses[0][0]
                incompletedactioneremail=cur.fetchall()[0][0]
            elif len(statuses) > 0 and statuses[0][0]=='1 Rejected':
                status=statuses[0][0]
                incompletedactioneremail=studentemail
            elif len(statuses) > 0 and statuses[0][0]=='1 Submitted':
                cur=getCursor()
                cur.execute('SELECT asst_superv_email from student WHERE student_email=%s;',(studentemail,))
                incompletedactioneremail=cur.fetchall()[0][0]
                status=statuses[0][0]
            elif len(statuses) > 0 and statuses[0][0]=='2 Submitted':
                cur=getCursor()
                cur.execute('SELECT other_superv_email from student WHERE student_email=%s;',(studentemail,))
                othersuperv=cur.fetchall()[0][0]
                status=statuses[0][0]
                if othersuperv:
                    incompletedactioneremail=othersuperv
                else:
                    cur=getCursor()
                    cur.execute("SELECT n.user_email FROM (SELECT * FROM user JOIN staff ON user_email=staff_email WHERE user_role = 'PG Convenor' and status='active')\
                                    AS n JOIN student AS s ON n.department_id=s.department_id WHERE s.student_email=%s;",(studentemail,))
                    incompletedactioneremail=cur.fetchall()[0][0]
     
            elif len(statuses) > 0 and statuses[0][0]=='3 Submitted':
                cur=getCursor()
                cur.execute("SELECT n.user_email FROM (SELECT * FROM user JOIN staff ON user_email=staff_email WHERE user_role = 'PG Convenor' and status='active')\
                                    AS n JOIN student AS s ON n.department_id=s.department_id WHERE s.student_email=%s;",(studentemail,))
                incompletedactioneremail=cur.fetchall()[0][0]
                status=statuses[0][0]
            elif len(statuses) > 0 and statuses[0][0]=='10 Submitted':
                incompletedactioneremail=None
                status=statuses[0][0]
            else:
                status='Unsubmitted'
                incompletedactioneremail=studentemail
                    
            status_list.append(status)
            incompletedactioneremail_list.append(incompletedactioneremail)

        print(status_list)
        print(incompletedactioneremail_list)

        return render_template('chair/reportprogress.html', title='Report Progress',studentlist=studentlist,status_list=status_list, incompletedactioneremail_list=incompletedactioneremail_list)

    else:
        cur=getCursor()
        cur.execute("SELECT s.student_email, s.fname, s.lname, s.department_id, IFNULL(r.report_id, NULL)\
                    AS report_id, IFNULL(r.milestone_num,1),IFNULL(r.due_date,%s) AS due_date\
                    FROM student AS s JOIN user AS u ON u.user_email = s.student_email\
                    LEFT JOIN (SELECT student_email, MAX(report_id) AS max_report_id FROM report GROUP BY student_email)\
                    AS r1 ON r1.student_email = s.student_email LEFT JOIN report AS r ON r.student_email = s.student_email\
                    AND r.report_id = r1.max_report_id WHERE u.status = 'active' ORDER BY s.student_email;",(due_date,))
        studentlist=cur.fetchall()
        
        
        status_list = []
        incompletedactioneremail_list = []

        for student in studentlist:
            studentemail=student[0]
            cur=getCursor()
            studentreportid=student[4]
            cur.execute('SELECT action_type FROM progress WHERE report_id=%s ORDER BY event_id DESC limit 1;',(studentreportid,))
            statuses=cur.fetchall()
            
            if len(statuses) > 0 and statuses[0][0]=='Submitted':
                cur=getCursor()
                cur.execute('SELECT main_superv_email from student WHERE student_email=%s;',(studentemail,))
                status=statuses[0][0]
                incompletedactioneremail=cur.fetchall()[0][0]
            elif len(statuses) > 0 and statuses[0][0]=='1 Rejected':
                status=statuses[0][0]
                incompletedactioneremail=studentemail
            elif len(statuses) > 0 and statuses[0][0]=='1 Submitted':
                cur=getCursor()
                cur.execute('SELECT asst_superv_email from student WHERE student_email=%s;',(studentemail,))
                incompletedactioneremail=cur.fetchall()[0][0]
                status=statuses[0][0]
            elif len(statuses) > 0 and statuses[0][0]=='2 Submitted':
                cur=getCursor()
                cur.execute('SELECT other_superv_email from student WHERE student_email=%s;',(studentemail,))
                othersuperv=cur.fetchall()[0][0]
                status=statuses[0][0]
                if othersuperv:
                    incompletedactioneremail=othersuperv
                else:
                    cur=getCursor()
                    cur.execute("SELECT n.user_email FROM (SELECT * FROM user JOIN staff ON user_email=staff_email WHERE user_role = 'PG Convenor' and status='active')\
                                AS n JOIN student AS s ON n.department_id=s.department_id WHERE s.student_email=%s;",(studentemail,))
                    incompletedactioneremail=cur.fetchall()[0][0]
            elif len(statuses) > 0 and statuses[0][0]=='3 Submitted':
                cur=getCursor()
                cur.execute("SELECT n.user_email FROM (SELECT * FROM user JOIN staff ON user_email=staff_email WHERE user_role = 'PG Convenor' and status='active')\
                                    AS n JOIN student AS s ON n.department_id=s.department_id WHERE s.student_email=%s;",(studentemail,))
                incompletedactioneremail=cur.fetchall()[0][0]
                status=statuses[0][0]
            elif len(statuses) > 0 and statuses[0][0]=='10 Submitted':
                incompletedactioneremail=None
                status=statuses[0][0]
            else:
                status='Unsubmitted'
                incompletedactioneremail=studentemail
                    
            status_list.append(status)
            incompletedactioneremail_list.append(incompletedactioneremail)

        print(status_list)
        print(incompletedactioneremail_list)

        flash('Please put a vaild stduent email or department id to search again!')
        return render_template('chair/reportprogress.html', title='Report Progress',studentlist=studentlist,status_list=status_list, incompletedactioneremail_list=incompletedactioneremail_list)