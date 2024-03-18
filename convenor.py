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

# @bp.route('/dashboard')
# @login_required
# def dashboard():
#     cur = getCursor()
#     cur.execute("""SELECT student.fname, student.lname, student.student_email, user.user_email, report.report_id, report.due_date, progress.actioner_email, progress.action_date, progress.action_type, completed_report_status.orange, completed_report_status.red, completed_report_status.green, completed_report_status.no_indicator, f_stud_assessment.comments, e_assessment.performance, e_assessment.comments, e_assessment.status FROM student left outer join user on student_email = user_email left outer join report on student.student_email = report.student_email left outer join completed_report_status ON report.report_id = completed_report_status.report_id left outer join progress ON report.report_id = progress.report_id left outer join e_assessment ON report.report_id = e_assessment.report_id left outer join f_stud_assessment on report.report_id = f_stud_assessment.report_id WHERE student.student_email IS NOT NULL""")
#     results = cur.fetchall()
#     return render_template('convenor/dashboard copy.html', title='Dashboard', results=results)

@bp.route('/dashboard')
@login_required
def dashboard():
        return render_template('convenor/dashboard.html')
    
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


@bp.route('/reportchecks')
@login_required
def reportchecks():
    cur = getCursor()
    cur.execute("SELECT student.fname, student.lname, student.student_email, user.user_email, report.report_id, report.due_date, progress.actioner_email, progress.action_date, progress.action_type, completed_report_status.orange, completed_report_status.red, completed_report_status.green, completed_report_status.no_indicator, f_stud_assessment.comments, e_assessment.performance, e_assessment.comments, e_assessment.status FROM student inner join user on student_email = user_email inner join report on student.student_email = report.student_email inner join completed_report_status ON report.report_id = completed_report_status.report_id inner join progress ON report.report_id = progress.report_id inner join e_assessment ON report.report_id = e_assessment.report_id inner join f_stud_assessment on report.report_id = f_stud_assessment.report_id WHERE student.student_email IS NOT NULL")
    results = cur.fetchall()
    return render_template('convenor/reportchecks.html', title='Report Checks', results=results)

@bp.route('/logstatus')
@login_required
def logstatus():
    reportNo = request.form.get("reportno")
    convComments = request.form.get("convcomments")
    statusupdate = request.form.get("logstatus")
    cur = getCursor()
    cur.execute("INSERT INTO e_convenor (comments) VALUES (%s,%s) WHERE reportid = %s;", (convComments, statusupdate, reportNo))
    return render_template('convenor/reportchecks.html')

@bp.route('/E', methods = ['GET','POST'])
@login_required
def E():
    if request.method == 'GET':
        studentemail=request.args.get('studentemail')
        print(studentemail)
        reportid=request.args.get('reportid')
        print(reportid)
        return render_template('convenor/E.html', title='Section E', studentemail=studentemail, reportid=reportid)
    else:
        studentemail=request.form.get('studentemail')
        print(studentemail)
        reportid=request.form.get('reportid')
        print(reportid)
        comment=request.form.get('comment')
        print(comment)
        status=request.form.get('status')
        if status == 'Green':
            green = 1
        else:
            green = 0
        if status == 'Orange':
            orange = 1
        else:
            orange = 0
        if status == 'Red':
            red = 1
        else: 
            red = 0
        cur = getCursor()
        cur.execute("""INSERT into e_convenor (report_id, comments)
                VALUES (%s,%s);""", (reportid, comment,))
        cur.execute("""INSERT into completed_report_status (report_id, orange, red, green, no_indicator)
                VALUES (%s,%s,%s,%s,0);""", (reportid, orange, red, green,))
        flash("You have updated student's status successfully!")
        
        return render_template('convenor/convenor.html', title='Section E', studentemail=studentemail, reportid=reportid)


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

@bp.route('/mystudent')
@login_required
def mystudent():
    user_email=session['user_email']
    cur = getCursor()
    cur.execute('SELECT fname, lname FROM staff WHERE staff_email = %s', (user_email,))
    user_name=cur.fetchone()
    firstname=user_name[0]
    lastname=user_name[1]
    
    cur=getCursor()
    cur.execute("""SELECT p.report_id FROM progress p join report r on r.report_id=p.report_id
    join student s on s.student_email=r.student_email where p.action_type='1 Submitted' """)
    submit1=cur.fetchall()
    cur=getCursor()
    cur.execute("""SELECT p.report_id FROM progress p join report r on r.report_id=p.report_id
    join student s on s.student_email=r.student_email where p.action_type='2 Submitted' """)
    submit2=cur.fetchall()
    submit11=[]
    for i in submit1:
        submit11.append(i[0])
    submit22=[]
    for item in submit2:
        submit22.append(item[0])
    reportlist=[]
    reportname=[]
    reportemail=[]
    for reportid in submit11:
        if reportid in submit22:
            cur=getCursor()
            cur.execute("SELECT r.report_id, concat(s.fname,' ', s.lname), r.student_email FROM report r join student s on r.student_email=s.student_email where r.report_id=%s",(reportid,))
            reportnamid=cur.fetchall()
            reportlist.append(reportid)
            reportname.append(reportnamid[0][1])
            reportemail.append(reportnamid[0][2])
    print(reportlist,reportname,reportemail)
    data=[[reportlist[i],reportname[i], reportemail[i]]for i in range(0,len(reportlist))]
    print(data)
    return render_template('convenor/mystudent.html', title='mystudent',reportlist=reportlist,data=data, firstname=firstname, lastname=lastname)

@bp.route('/viewreport', methods = ['GET', 'POST'])
@login_required
def viewreport():
    user_email = session['user_email']
    studentemail=request.args.get('studentemail')
    reportid=request.args.get('reportid')
    cur = getCursor()

    if request.method =='GET':

        #Section A
        cur.execute("""SELECT concat(s.fname,' ',s.lname) as 'Name', s.student_email, phone, address, 
                    enrolment_date, student_type, d.department_name, thesis_title, 
                    s.main_superv_email, s.asst_superv_email, s.other_superv_email FROM student as s
                    JOIN department as d on d.department_id = s.department_id
                    WHERE s.student_email = %s;""", (studentemail,))
        superviseedetails = cur.fetchall()

        cur.execute("""SELECT scholarship, scholarship_value, tenure, end_date FROM scholarship
                    WHERE student_email = %s;""", (studentemail,))
        scholarship = cur.fetchall()

        cur.execute("""SELECT teaching_hours, research_hours, other_hours FROM employment 
                    WHERE student_email = %s;""", (studentemail,))
        employment = cur.fetchall()

        #Section B_step
        cur.execute("""SELECT step as 'Step', compulsory as 'Status', complete_date as 'Complete Date' FROM b_step as bs
                    JOIN report as r on r.report_id = bs.report_id
                    WHERE student_email = %s and r.report_id = %s;""", (studentemail,reportid,))
        section_B_step = cur.fetchall()
        column_names1 = [desc[0] for desc in cur.description]

        #Section B_research_approval
        cur.execute("""SELECT committee as 'Committee', needed as 'Status', approval as 'Approval' FROM b_research_approval as bra
                    JOIN report as r on r.report_id = bra.report_id
                    WHERE student_email = %s and r.report_id = %s;""", (studentemail,reportid,))
        section_B_research = cur.fetchall()
        column_names2 = [desc[0] for desc in cur.description]

        #Section B_milestone
        cur.execute("""SELECT milestone, months, due_date FROM b_milestone as bm
                    JOIN report as r on r.milestone_num = bm.milestone_num
                    WHERE student_email = %s and r.report_id = %s ;""", (studentemail,reportid,))
        section_B_milestone = cur.fetchall()
        column_names3 = [desc[0] for desc in cur.description]

        #Section C_evaluation
        cur.execute("""SELECT evaluation_item as 'Item', evaluation_result as 'Evaluation Result', comments as 'Comments' FROM c_evaluation as ce
                    JOIN report as r on r.report_id = ce.report_id
                    WHERE student_email = %s and r.report_id = %s;""", (studentemail,reportid,))
        section_C_eval = cur.fetchall()
        column_names4 = [desc[0] for desc in cur.description]

        #Section C_feedback
        cur.execute("""SELECT frequency, feedback_received, feedback_method FROM c_feedback as cf
                    JOIN report as r on r.report_id = cf.report_id
                    WHERE student_email = %s and r.report_id = %s;""", (studentemail,reportid,))
        section_C_feed = cur.fetchall()

        #Section D_1
        cur.execute("""SELECT research_objective as 'Research Objectives', dp.status as 'Status', incomplete_comments as 'Comments', change_comments as 'Comments (Changed)' FROM d_research_progress as dp
                    JOIN report as r on r.report_id = dp.report_id
                    WHERE student_email = %s and r.report_id = %s;""", (studentemail,reportid,))
        section_D_1 = cur.fetchall()

        #Section D_2
        cur.execute("""SELECT impact FROM d_covid as dc
                    JOIN report as r on r.report_id = dc.report_id
                    WHERE student_email = %s and r.report_id = %s;""", (studentemail,reportid,))
        section_D_2 = cur.fetchall()

        #Section D_3
        cur.execute("""SELECT * FROM d_achievement as da
                    JOIN report as r on r.report_id = da.report_id
                    WHERE student_email = %s and r.report_id = %s;""", (studentemail,reportid,))
        section_D_3 = cur.fetchall()

        #Section D_4
        cur.execute("""SELECT research_objective as 'Research Objectives', target_completion_date as 'Target Completion Date', anticipated_problems as 'Anticipated Problems' FROM d_research_progress as drp
                    JOIN report as r on r.report_id = drp.report_id
                    WHERE target_completion_date >= CURDATE() AND target_completion_date <= DATE_ADD(CURDATE(), INTERVAL 6 MONTH)
                    AND student_email = %s and r.report_id = %s;""", (studentemail,reportid,))
        section_D_4 = cur.fetchall()

        #Section D_5
        cur.execute("""SELECT item, amount, notes FROM d_research_expense as dre
                    JOIN report as r on r.report_id = dre.report_id
                    WHERE student_email = %s and r.report_id = %s;""", (studentemail,reportid,))
        section_D_5 = cur.fetchall()

        #Section D_5_total
        cur.execute("""SELECT sum(amount) as 'Total Expenditure' FROM d_research_expense as dre
                    JOIN report as r on r.report_id = dre.report_id
                    WHERE student_email = %s and r.report_id = %s
                    GROUP BY item;""", (studentemail,reportid,))
        section_D_total = cur.fetchall()

        #Section E
        cur.execute("""SELECT concat(s.fname,' ',s.lname), ea.staff_email, assess_item, performance, comments, ea.status FROM e_assessment as ea
                    JOIN staff as s on s.staff_email = ea.staff_email
                    WHERE report_id = %s;""",(reportid,))
        section_E = cur.fetchall()

        data = section_E
        grouped_data = {}
        for item in data:
            staff_name = item[0]
            if staff_name in grouped_data:
                grouped_data[staff_name].append(item)
            else:
                grouped_data[staff_name] = [item]


    return render_template('convenor/viewreport.html', title='viewreport', column_names1=column_names1, column_names2=column_names2, column_names3=column_names3, column_names4=column_names4, 
                            superviseedetails=superviseedetails, scholarship=scholarship, employment=employment, section_B_step=section_B_step, section_B_research=section_B_research, section_B_milestone=section_B_milestone, 
                            section_C_eval=section_C_eval, section_C_feed=section_C_feed, section_D_1=section_D_1, section_D_2=section_D_2, section_D_3=section_D_3,
                            section_D_4=section_D_4, section_D_5=section_D_5, section_D_total=section_D_total, section_E=section_E, studentemail=studentemail, sectionE=grouped_data, reportid=reportid)

