from flask import Blueprint,Flask
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
from datetime import date,datetime
import smtplib
from email.message import EmailMessage
from flask_mail import Mail, Message

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



###### VIEW & UPDATE SUPERVISOR PROFILE ######

@bp.route('/profile',methods=['GET','POST'])
@login_required
def profile():
    cur = getCursor()
    user_email = session['user_email']  
    if request.method =='GET':       
        cur.execute('''SELECT fname, lname, staff_email, department_name, phone FROM staff
                    JOIN department on staff.department_id = department.department_id
                    WHERE staff_email = %s;''', (user_email,))
        spvs_profile = cur.fetchall()
        column_names = [desc[0] for desc in cur.description]
        return render_template('supervisor/profile.html', title='Profile', spvs_profile=spvs_profile, column_names=column_names)
    else:
        phone=request.form.get('phone')
        cur.execute('''UPDATE staff SET phone = %s WHERE staff_email = %s;''', (phone, user_email))
        cur.execute('''SELECT fname, lname, staff_email, department_name, phone FROM staff
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

#Lane's code START HERE!!!

################### view supervisee list######################

@bp.route('/supervisee')
@login_required
def supervisee():
    cur = getCursor()
    # cur.execute("""select concat(fname,' ',lname)as name,student.student_email, phone, milestone_num as 'Submission Period', 
    # concat(actioner_role,' ',action_type) as '6MR Report Status', action_date from student 
    # left join report on student.student_email=report.student_email
    # left join progress on report.report_id=progress.report_id;""")
    
    cur.execute("""select concat(fname,' ',lname)as name,student.student_email, phone, new.report_id, milestone_num, concat(actioner_role,' ',action_type) as status, action_date from student left join (
select report.report_id, milestone_num, event_id, report.student_email from (select max(event_id) as event_id, report_id from progress group by report_id) as p
right join report on report.report_id=p.report_id) as new on new.student_email=student.student_email
left join progress on progress.event_id=new.event_id
order by milestone_num AND new.report_id desc;""")

    superviseeinfo=cur.fetchall()
    
    return render_template('supervisor/viewsupervisee.html', title='supervisee',superviseeinfo=superviseeinfo)

###################### seach a specific supervisee #####################################
@bp.route('/superviseesearch', methods=('GET', 'POST'))
@login_required
def superviseesearch():
    searchterm = request.form.get("search")
    searchterm = "%" + searchterm + "%"
    connection = getCursor()
    sql = """select concat(fname,' ',lname)as name,student.student_email, phone, milestone_num as 'Submission Period', 
    concat(actioner_role,' ',action_type) as '6MR Report Status', action_date from student 
    left join report on student.student_email=report.student_email
    left join progress on report.report_id=progress.report_id 
    where fname like %s or lname like %s or student.student_email like %s;"""
    connection.execute(sql, (searchterm, searchterm, searchterm,))
    superviseeinfo = connection.fetchall()
    return render_template('supervisor/viewsupervisee.html', superviseeinfo=superviseeinfo)

###################### view supervisee details #####################################
@bp.route('/superviseedetails', methods=('GET', 'POST'))
@login_required
def superviseedetails():        
    student_email = request.form.get("studentemail")
    connection = getCursor()
    sql = """select concat(fname,' ',lname)as name,student.student_email, phone, address, student_type, 
    enrolment_date,department_id,main_superv_email,other_superv_email from student where student.student_email = %s;"""
    connection.execute(sql, (student_email,))
    superviseedetails = connection.fetchall()
    return render_template('supervisor/superviseedetails.html', superviseedetails=superviseedetails)

#Lane's code END HERE!!!

@bp.route('/MR')
@login_required
def MR():
    return render_template('supervisor/6MR.html', title='6MR')

###### VIEW MY SUPERVISEE ###### 

@bp.route('/mysupervisee',  methods=['GET','POST'])
@login_required
def mysupervisee():
    cur = getCursor()
    user_email = session['user_email']
    # print(user_email)
    report_id=request.args.get('report_id')
    # print(report_id)

    todaydate = date.today()
    if todaydate.month <= 6:
        due_date = date(todaydate.year, 6, 30)
        # print(due_date)
    else:
        due_date = date(todaydate.year, 12, 31)
     
    cur.execute("""SELECT p.report_id, concat(s.fname,' ', s.lname), s.student_email, main_superv_email, asst_superv_email, other_superv_email, action_date, p.action_type FROM student as s
                    JOIN progress as p on s.student_email=p.actioner_email
                    JOIN report as r on r.report_id = p.report_id
                    WHERE (s.main_superv_email = %s or asst_superv_email = %s or other_superv_email = %s) and p.action_type='Submitted' and due_date = %s
                    ;""", (user_email, user_email, user_email, due_date,))
    select_supervisee = cur.fetchall()
    # print(select_supervisee)

    cur = getCursor()
    cur.execute("""SELECT p.report_id FROM progress as p
                JOIN report as r on r.report_id=p.report_id
                WHERE actioner_email = %s and due_date = %s and p.report_id = %s and action_type Like '% Submitted';""", (user_email, due_date, report_id,))
    thisreportid = cur.fetchall()
    # print(thisreportid)

    cur = getCursor()
    cur.execute("""SELECT action_type FROM progress as p
                JOIN report as r on r.report_id=p.report_id
                WHERE actioner_email = %s and due_date = %s and p.report_id = %s and action_type Like '% Submitted';""", (user_email, due_date, report_id,))
    action_type = cur.fetchall()
    # print(action_type)

    # Check if this supervisor is a convenor as well
    cur = getCursor()
    cur.execute("""SELECT us.user_email FROM staff as st
                JOIN user as us on us.user_email = st.staff_email
                WHERE user_role = 'PG Convenor';""")
    convenors = cur.fetchall()
    # print(convenors)
        
    return render_template('supervisor/mysupervisee.html', title='mysupervisee', select_supervisee=select_supervisee, user_email=user_email, action_type=action_type, report_id=report_id, thisreportid=thisreportid, convenors=convenors)

###### SUPERVISEE CAN VIEW THE 6MR REPORT FROM SECTION A-D ######
    
@bp.route('/viewreport', methods=['GET', 'POST'])
@login_required
def viewreport():
    user_email = session['user_email']
    studentemail=request.args.get('studentemail')
    report_id=request.args.get('report_id')
    print(report_id)
    todaydate = date.today()
    if todaydate.month <= 6:
            due_date = date(todaydate.year, 6, 30)
            print(due_date)
    else:
            due_date = date(todaydate.year, 12, 31)

    cur=getCursor()
    cur.execute("SELECT report_id FROM report WHERE student_email=%s AND due_date = %s;",(studentemail,due_date,))
    reportid = cur.fetchone()
    if reportid:
        reportid = reportid[0]
    # print(reportid)

    #Check if the user is the main supervisor
    cur = getCursor()
    cur.execute("""SELECT main_superv_email FROM student
                WHERE student_email = %s;""", (studentemail,))
    main_supervisor_email = cur.fetchall()
    # print(main_supervisor_email[0][0])

    #Check if the report has already been approved by main supervisor
    cur = getCursor()
    cur.execute("""SELECT action_type FROM progress
                WHERE actioner_email = %s and report_id = %s and action_type = '1 Accepted';""", (main_supervisor_email[0][0], report_id,))
    main_accepted = cur.fetchall()
    # print(main_accepted)

    #Check if the report has been rejected by main supervisor
    cur = getCursor()
    cur.execute("""SELECT action_type FROM progress
                WHERE actioner_email = %s and report_id = %s and action_type = '1 Rejected';""", (main_supervisor_email[0][0], report_id,))
    main_rejected = cur.fetchall()
    # print(main_rejected)


    if request.method =='GET':

        #Section A
        cur.execute("""SELECT concat(s.fname,' ',s.lname) as 'Name', s.student_email, phone, address, 
                    enrolment_date, student_type, d.department_name, thesis_title, 
                    s.main_superv_email, s.asst_superv_email, s.other_superv_email FROM student as s
                    JOIN department as d on d.department_id = s.department_id
                    WHERE s.student_email = %s;""", (studentemail,))
        superviseedetails = cur.fetchall()
        # print(superviseedetails)
        cur.execute("""SELECT scholarship, scholarship_value, tenure, end_date FROM scholarship
                    WHERE student_email = %s;""", (studentemail,))
        scholarship = cur.fetchall()
        # print(scholarship)

        cur.execute("""SELECT teaching_hours, research_hours, other_hours FROM employment 
                    WHERE student_email = %s;""", (studentemail,))
        employment = cur.fetchall()
        # print(employment)

        #Section B_step
        cur.execute("""SELECT step as 'Step', compulsory as 'Status', complete_date as 'Complete Date' FROM b_step as bs
                    JOIN report as r on r.report_id = bs.report_id
                    WHERE student_email = %s and r.report_id = %s;""", (studentemail, report_id,))
        section_B_step = cur.fetchall()
        column_names1 = [desc[0] for desc in cur.description]
        # print(section_B_step)

        #Section B_research_approval
        cur.execute("""SELECT committee as 'Committee', needed as 'Status', approval as 'Approval' FROM b_research_approval as bra
                    JOIN report as r on r.report_id = bra.report_id
                    WHERE student_email = %s and r.report_id = %s;""", (studentemail, report_id,))
        section_B_research = cur.fetchall()
        column_names2 = [desc[0] for desc in cur.description]
        # print(section_B_research)

        #Section B_milestone
        cur.execute("""SELECT milestone, months, due_date FROM b_milestone as bm
                    JOIN report as r on r.milestone_num = bm.milestone_num
                    WHERE student_email = %s and r.report_id = %s;""", (studentemail, report_id,))
        section_B_milestone = cur.fetchall()
        # print(section_B_milestone)
        column_names3 = [desc[0] for desc in cur.description]

        #Section C_evaluation
        cur.execute("""SELECT evaluation_item as 'Item', evaluation_result as 'Evaluation Result', comments as 'Comments' FROM c_evaluation as ce
                    JOIN report as r on r.report_id = ce.report_id
                    WHERE student_email = %s and r.report_id = %s;""", (studentemail, report_id,))
        section_C_eval = cur.fetchall()
        # print(section_C_eval)
        column_names4 = [desc[0] for desc in cur.description]

        #Section C_feedback
        cur.execute("""SELECT frequency, feedback_received, feedback_method FROM c_feedback as cf
                    JOIN report as r on r.report_id = cf.report_id
                    WHERE student_email = %s and r.report_id = %s;""", (studentemail, report_id,))
        section_C_feed = cur.fetchall()
        # print(section_C_feed)

        #Section D_1
        cur.execute("""SELECT research_objective as 'Research Objectives', dp.status as 'Status', incomplete_comments as 'Comments', change_comments as 'Comments (Changed)' FROM d_research_progress as dp
                    JOIN report as r on r.report_id = dp.report_id
                    WHERE student_email = %s and r.report_id = %s;""", (studentemail, report_id,))
        section_D_1 = cur.fetchall()
        # print(section_D_1)

        #Section D_2
        cur.execute("""SELECT impact FROM d_covid as dc
                    JOIN report as r on r.report_id = dc.report_id
                    WHERE student_email = %s and r.report_id = %s;""", (studentemail, report_id,))
        section_D_2 = cur.fetchall()
        # print(section_D_2)

        #Section D_3
        cur.execute("""SELECT * FROM d_achievement as da
                    JOIN report as r on r.report_id = da.report_id
                    WHERE student_email = %s and r.report_id = %s;""", (studentemail, report_id,))
        section_D_3 = cur.fetchall()
        # print(section_D_3)

        #Section D_4
        cur.execute("""SELECT research_objective as 'Research Objectives', target_completion_date as 'Target Completion Date', anticipated_problems as 'Anticipated Problems' FROM d_research_progress as drp
                    JOIN report as r on r.report_id = drp.report_id
                    WHERE target_completion_date >= CURDATE() AND target_completion_date <= DATE_ADD(CURDATE(), INTERVAL 6 MONTH)
                    AND student_email = %s and r.report_id = %s;""", (studentemail, report_id,))
        section_D_4 = cur.fetchall()
        # print(section_D_4)

        #Section D_5
        cur.execute("""SELECT item, amount, notes FROM d_research_expense as dre
                    JOIN report as r on r.report_id = dre.report_id
                    WHERE student_email = %s and r.report_id = %s;""", (studentemail, report_id,))
        section_D_5 = cur.fetchall()
        # print(section_D_5)

        #Section D_5_total
        cur.execute("""SELECT sum(amount) as 'Total Expenditure' FROM d_research_expense as dre
                    JOIN report as r on r.report_id = dre.report_id
                    WHERE student_email = %s and r.report_id = %s;""", (studentemail, report_id,))
        section_D_total = cur.fetchall()
        # print(section_D_total)

        if user_email == main_supervisor_email[0][0]:
            # Check if the report has already been approved by the main supervisor
                if main_accepted and main_accepted[0][0] == '1 Accepted':
                    cur=getCursor()
                    cur.execute("SELECT asst_superv_email FROM student where student_email=%s",(studentemail,))
                    emailaddress=cur.fetchall()
                    emailaddress=emailaddress[0][0]
                    flash("The report has already been approved, please go to section E")
                   
                    return render_template('supervisor/viewreport_others.html', title='viewreport_others', 
                            column_names1=column_names1, column_names2=column_names2, column_names3=column_names3, column_names4=column_names4, 
                            superviseedetails=superviseedetails, scholarship=scholarship, employment=employment, section_B_step=section_B_step, section_B_research=section_B_research, section_B_milestone=section_B_milestone, 
                            section_C_eval=section_C_eval, section_C_feed=section_C_feed, section_D_1=section_D_1, section_D_2=section_D_2, section_D_3=section_D_3,
                            section_D_4=section_D_4, section_D_5=section_D_5, section_D_total=section_D_total, studentemail=studentemail, report_id=report_id)
                elif main_rejected and main_rejected[0][0] == '1 Rejected':
                     return render_template('supervisor/report_rejected.html')
                else:
                    return render_template('supervisor/viewreport.html', title='viewreport', 
                            column_names1=column_names1, column_names2=column_names2, column_names3=column_names3, column_names4=column_names4, 
                            superviseedetails=superviseedetails, scholarship=scholarship, employment=employment, section_B_step=section_B_step, section_B_research=section_B_research, section_B_milestone=section_B_milestone, 
                            section_C_eval=section_C_eval, section_C_feed=section_C_feed, section_D_1=section_D_1, section_D_2=section_D_2, section_D_3=section_D_3,
                            section_D_4=section_D_4, section_D_5=section_D_5, section_D_total=section_D_total, studentemail=studentemail, report_id=report_id)
        elif user_email != main_supervisor_email[0][0] and main_accepted:
                flash("The report has already been approved, please go to section E")
                return render_template('supervisor/viewreport_others.html', title='viewreport_others', 
                            column_names1=column_names1, column_names2=column_names2, column_names3=column_names3, column_names4=column_names4, 
                            superviseedetails=superviseedetails, scholarship=scholarship, employment=employment, section_B_step=section_B_step, section_B_research=section_B_research, section_B_milestone=section_B_milestone, 
                            section_C_eval=section_C_eval, section_C_feed=section_C_feed, section_D_1=section_D_1, section_D_2=section_D_2, section_D_3=section_D_3,
                            section_D_4=section_D_4, section_D_5=section_D_5, section_D_total=section_D_total, studentemail=studentemail, report_id=report_id)
        else:
            return render_template('supervisor/not_authorized.html')

    else:

        #Section A
        cur.execute("""SELECT concat(s.fname,' ',s.lname) as 'Name', s.student_email, phone, address, 
                    enrolment_date, student_type, d.department_name, thesis_title, 
                    s.main_superv_email, s.asst_superv_email, s.other_superv_email FROM student as s
                    JOIN department as d on d.department_id = s.department_id
                    WHERE s.student_email = %s;""", (studentemail,))
        superviseedetails = cur.fetchall()
        # print(superviseedetails)
        cur.execute("""SELECT scholarship, scholarship_value, tenure, end_date FROM scholarship
                    WHERE student_email = %s;""", (studentemail,))
        scholarship = cur.fetchall()
        # print(scholarship)

        cur.execute("""SELECT teaching_hours, research_hours, other_hours FROM employment 
                    WHERE student_email = %s;""", (studentemail,))
        employment = cur.fetchall()
        # print(employment)

        #Section B_step
        cur.execute("""SELECT step as 'Step', compulsory as 'Status', complete_date as 'Complete Date' FROM b_step as bs
                    JOIN report as r on r.report_id = bs.report_id
                    WHERE student_email = %s and r.report_id = %s;""", (studentemail, report_id,))
        section_B_step = cur.fetchall()
        column_names1 = [desc[0] for desc in cur.description]
        # print(section_B_step)

        #Section B_research_approval
        cur.execute("""SELECT committee as 'Committee', needed as 'Status', approval as 'Approval' FROM b_research_approval as bra
                    JOIN report as r on r.report_id = bra.report_id
                    WHERE student_email = %s and r.report_id = %s;""", (studentemail, report_id,))
        section_B_research = cur.fetchall()
        column_names2 = [desc[0] for desc in cur.description]
        # print(section_B_research)

        #Section B_milestone
        cur.execute("""SELECT milestone, months, due_date FROM b_milestone as bm
                    JOIN report as r on r.milestone_num = bm.milestone_num
                    WHERE student_email = %s and r.report_id = %s;""", (studentemail, report_id,))
        section_B_milestone = cur.fetchall()
        # print(section_B_milestone)
        column_names3 = [desc[0] for desc in cur.description]

        #Section C_evaluation
        cur.execute("""SELECT evaluation_item as 'Item', evaluation_result as 'Evaluation Result', comments as 'Comments' FROM c_evaluation as ce
                    JOIN report as r on r.report_id = ce.report_id
                    WHERE student_email = %s and r.report_id = %s;""", (studentemail, report_id,))
        section_C_eval = cur.fetchall()
        # print(section_C_eval)
        column_names4 = [desc[0] for desc in cur.description]

        #Section C_feedback
        cur.execute("""SELECT frequency, feedback_received, feedback_method FROM c_feedback as cf
                    JOIN report as r on r.report_id = cf.report_id
                    WHERE student_email = %s and r.report_id = %s;""", (studentemail, report_id,))
        section_C_feed = cur.fetchall()
        # print(section_C_feed)

        #Section D_1
        cur.execute("""SELECT research_objective as 'Research Objectives', dp.status as 'Status', incomplete_comments as 'Comments', change_comments as 'Comments (Changed)' FROM d_research_progress as dp
                    JOIN report as r on r.report_id = dp.report_id
                    WHERE student_email = %s and r.report_id = %s;""", (studentemail, report_id,))
        section_D_1 = cur.fetchall()
        # print(section_D_1)

        #Section D_2
        cur.execute("""SELECT impact FROM d_covid as dc
                    JOIN report as r on r.report_id = dc.report_id
                    WHERE student_email = %s and r.report_id = %s;""", (studentemail, report_id,))
        section_D_2 = cur.fetchall()
        # print(section_D_2)

        #Section D_3
        cur.execute("""SELECT * FROM d_achievement as da
                    JOIN report as r on r.report_id = da.report_id
                    WHERE student_email = %s and r.report_id = %s;""", (studentemail, report_id,))
        section_D_3 = cur.fetchall()
        # print(section_D_3)

        #Section D_4
        cur.execute("""SELECT research_objective as 'Research Objectives', target_completion_date as 'Target Completion Date', anticipated_problems as 'Anticipated Problems' FROM d_research_progress as drp
                    JOIN report as r on r.report_id = drp.report_id
                    WHERE target_completion_date >= CURDATE() AND target_completion_date <= DATE_ADD(CURDATE(), INTERVAL 6 MONTH)
                    AND student_email = %s and r.report_id = %s;""", (studentemail, report_id,))
        section_D_4 = cur.fetchall()
        # print(section_D_4)

        #Section D_5
        cur.execute("""SELECT item, amount, notes FROM d_research_expense as dre
                    JOIN report as r on r.report_id = dre.report_id
                    WHERE student_email = %s and r.report_id = %s;""", (studentemail, report_id,))
        section_D_5 = cur.fetchall()
        # print(section_D_5)

        #Section D_5_total
        cur.execute("""SELECT sum(amount) as 'Total Expenditure' FROM d_research_expense as dre
                    JOIN report as r on r.report_id = dre.report_id
                    WHERE student_email = %s and r.report_id = %s;""", (studentemail, report_id,))
        section_D_total = cur.fetchall()
        # print(section_D_total)

        accept = request.form.get('accept')
        # print(accept)
        reject = request.form.get('reject')
        # print(reject)
        if accept:
            if user_email == main_supervisor_email[0][0]:

            # Check if the report has already been approved by the main supervisor
                if main_accepted and main_accepted[0][0] == '1 Accepted':
                    flash("The report has already been approved, please go to section E")
                    return render_template('supervisor/viewreport_others.html', title='viewreport_others', 
                            column_names1=column_names1, column_names2=column_names2, column_names3=column_names3, column_names4=column_names4, 
                            superviseedetails=superviseedetails, scholarship=scholarship, employment=employment, section_B_step=section_B_step, section_B_research=section_B_research, section_B_milestone=section_B_milestone, 
                            section_C_eval=section_C_eval, section_C_feed=section_C_feed, section_D_1=section_D_1, section_D_2=section_D_2, section_D_3=section_D_3,
                            section_D_4=section_D_4, section_D_5=section_D_5, section_D_total=section_D_total, studentemail=studentemail, report_id=report_id)
                elif main_rejected and main_rejected[0][0] == '1 Rejected':
                     return render_template('supervisor/not_authorized.html')
                else:
                #Supervisor review and 'ACCEPT' their supervisee's report section A-D
                    cur.execute("""INSERT into progress (report_id, actioner_email, actioner_role, action_date, action_type) 
                            VALUES (%s,%s, 'PG Supevisor', %s, %s);""",(report_id, user_email, todaydate, accept,))
                    
                    ### IT'S WORKING!!!### Email sending to other supervisors when the report has been approved by main supervisor
                    cur=getCursor()
                    cur.execute("SELECT asst_superv_email FROM PGmonitoring.student where student_email=%s",(studentemail,))
                    emailaddress=cur.fetchall()
                    emailaddress=emailaddress[0][0]
                    msg = EmailMessage()
                    msg['Subject'] = 'Reminder: Your supervisee 6-Monthly Report has been approved!'
                    msg['From'] = 'comp639project@gmail.com'
                    msg['To'] = emailaddress
                    msg.set_content('\n This is a reminder that your supervisee 6-Monthly Report has been approved by main supervisor. \n \n Please complete section E - Assessment of Student by Supervisor(s).')
                    smtp = smtplib.SMTP('smtp.gmail.com', 587)
                    smtp.starttls()
                    smtp.login('comp639project@gmail.com', 'yncrimbapjfiawdw')  # login
                    text = msg.as_string()
                    smtp.sendmail('comp639project@gmail.com', emailaddress, text)
                    smtp.quit()
                    # print(msg['To'], msg['Bcc'])
                    # print('email sent')
                    flash("The report has already been approved, please go to section E")
                   
                    
                    return render_template('supervisor/viewreport_others.html', title='viewreport', 
                            column_names1=column_names1, column_names2=column_names2, column_names3=column_names3, column_names4=column_names4, 
                            superviseedetails=superviseedetails, scholarship=scholarship, employment=employment, section_B_step=section_B_step, section_B_research=section_B_research, section_B_milestone=section_B_milestone, 
                            section_C_eval=section_C_eval, section_C_feed=section_C_feed, section_D_1=section_D_1, section_D_2=section_D_2, section_D_3=section_D_3,
                            section_D_4=section_D_4, section_D_5=section_D_5, section_D_total=section_D_total, studentemail=studentemail, report_id=report_id)
               
            elif user_email != main_supervisor_email[0][0] and main_accepted:
                flash("The report has already been approved, please go to section E")
                return render_template('supervisor/viewreport_others.html', title='viewreport_others', 
                            column_names1=column_names1, column_names2=column_names2, column_names3=column_names3, column_names4=column_names4, 
                            superviseedetails=superviseedetails, scholarship=scholarship, employment=employment, section_B_step=section_B_step, section_B_research=section_B_research, section_B_milestone=section_B_milestone, 
                            section_C_eval=section_C_eval, section_C_feed=section_C_feed, section_D_1=section_D_1, section_D_2=section_D_2, section_D_3=section_D_3,
                            section_D_4=section_D_4, section_D_5=section_D_5, section_D_total=section_D_total, studentemail=studentemail, report_id=report_id)
            else:
                return render_template('supervisor/not_authorized.html')
            
        else:
        #Supervisor can review and 'REJECT' their supervisee's report section A-D
            studentemail = request.form.get('studentemail')
            # print(studentemail)
            cur.execute("""INSERT into progress (report_id, actioner_email, actioner_role, action_date, action_type) 
                        VALUES (%s,%s, 'PG Supevisor', %s, %s);""",(report_id, user_email, todaydate, reject,))
                
            return render_template('supervisor/reject.html', title='reject', reject=reject, studentemail=studentemail, report_id=report_id)
    
@bp.route('/reject', methods = ('GET','POST'))
@login_required
def reject():
    if request.method =='GET':
        cur = getCursor()
        user_email = session['user_email']
        # print(user_email)

        studentemail = request.form.get('studentemail')
        # print(studentemail)

        todaydate = date.today()
        if todaydate.month <= 6:
                due_date = date(todaydate.year, 6, 30)
                # print(due_date)
        else:
                due_date = date(todaydate.year, 12, 31)

        cur=getCursor()
        cur.execute("SELECT report_id FROM report WHERE student_email=%s AND due_date = %s;",(studentemail,due_date,))
        report_id = cur.fetchone()
        if report_id:
            report_id = report_id[0]
        # print(report_id) 

        cur=getCursor()
        cur.execute("""SELECT event_id FROM progress
                    WHERE report_id = %s and actioner_email = %s and action_type = '1 Rejected';""",(report_id,user_email,))
        event_id = cur.fetchone()
        if event_id:
            event_id = event_id[0]
        # print(event_id)
        
        return render_template('supervisor/reject.html', title='reject')

    else: 

        cur = getCursor()
        user_email = session['user_email']
        # print(user_email)

        studentemail = request.form.get('studentemail')
        # print(studentemail)

        todaydate = date.today()
        if todaydate.month <= 6:
                due_date = date(todaydate.year, 6, 30)
                # print(due_date)
        else:
                due_date = date(todaydate.year, 12, 31)

        cur=getCursor()
        cur.execute("SELECT report_id FROM report WHERE student_email=%s AND due_date = %s;",(studentemail,due_date,))
        report_id = cur.fetchone()
        if report_id:
            report_id = report_id[0]
        # print(report_id) 

        cur=getCursor()
        cur.execute("""SELECT event_id FROM progress
                    WHERE report_id = %s and actioner_email = %s and action_type = '1 Rejected';""",(report_id,user_email,))
        event_id = cur.fetchone()
        if event_id:
            event_id = event_id[0]
        # print(event_id)

        reject_comment = request.form.get('reject_comment')
        # print(reject_comment)
        cur.execute("""INSERT into rejected_comments (event_id, rejected_comments)
                VALUES (%s,%s);""", (event_id, reject_comment))
        flash("Your comments have been submitted successfully!")
    return render_template('supervisor/supervisor.html', title='reject')

#################################################################################



@bp.route('/E', methods = ['GET','POST'])
@login_required
def E():
    if request.method =='GET': 
        # print("I'm here")
        user_email = session['user_email']
        # print(user_email)
        studentemail = request.args.get('studentemail')
        # print(studentemail)

        cur = getCursor()
        cur.execute("""SELECT concat(fname,' ',lname), student_email FROM student
                        WHERE student_email = %s;""", (studentemail,))
        supervisee = cur.fetchall()

        todaydate = date.today()
        if todaydate.month <= 6:
                due_date = date(todaydate.year, 6, 30)
                # print(due_date)
        else:
                due_date = date(todaydate.year, 12, 31)

        cur=getCursor()
        cur.execute("SELECT report_id FROM report WHERE student_email=%s AND due_date = %s;",(studentemail,due_date,))
        report_id = cur.fetchone()
        if report_id:
            report_id = report_id[0]
        # print(report_id)

        #Check if the user is the main supervisor
        cur = getCursor()
        cur.execute("""SELECT main_superv_email FROM student
                    WHERE student_email = %s;""", (studentemail,))
        main_supervisor_email = cur.fetchall()
        main = main_supervisor_email[0][0]
        # print(main)

        #Check if the user is the associate supervisor
        cur = getCursor()
        cur.execute("""SELECT asst_superv_email FROM student
                    WHERE student_email = %s;""", (studentemail,))
        asst_supervisor_email = cur.fetchall()
        asst = asst_supervisor_email[0][0]
        # print(asst)

        #Check if the user is the other supervisor
        cur = getCursor()
        cur.execute("""SELECT other_superv_email FROM student
                    WHERE student_email = %s;""", (studentemail,))
        other_supervisor_email = cur.fetchall()
        other = other_supervisor_email[0][0]
        # print(other)

        return render_template('supervisor/E.html', title='Section E', supervisee=supervisee, studentemail=studentemail, report_id=report_id)

    else:

        user_email = session['user_email']
        # print(user_email)
        studentemail = request.form.get('studentemail')
        # print(studentemail)

        cur = getCursor()
        cur.execute("""SELECT concat(fname,' ',lname), student_email FROM student
                        WHERE student_email = %s;""", (studentemail,))
        supervisee = cur.fetchall()

        todaydate = date.today()
        if todaydate.month <= 6:
                due_date = date(todaydate.year, 6, 30)
                # print(due_date)
        else:
                due_date = date(todaydate.year, 12, 31)

        cur=getCursor()
        cur.execute("SELECT report_id FROM report WHERE student_email=%s AND due_date = %s;",(studentemail,due_date,))
        report_id = cur.fetchone()
        if report_id:
            report_id = report_id[0]
        # print(report_id)

        #Check if the user is the main supervisor
        cur = getCursor()
        cur.execute("""SELECT main_superv_email FROM student
                    WHERE student_email = %s;""", (studentemail,))
        main_supervisor_email = cur.fetchall()
        main = main_supervisor_email[0][0]
        # print(main)

        #Check if the user is the associate supervisor
        cur = getCursor()
        cur.execute("""SELECT asst_superv_email FROM student
                    WHERE student_email = %s;""", (studentemail,))
        asst_supervisor_email = cur.fetchall()
        asst = asst_supervisor_email[0][0]
        # print(asst)

        #Check if the user is the other supervisor
        cur = getCursor()
        cur.execute("""SELECT other_superv_email FROM student
                    WHERE student_email = %s;""", (studentemail,))
        other_supervisor_email = cur.fetchall()
        other = other_supervisor_email[0][0]
        # print(other)

        A1 = request.form['A1']
        A2 = request.form['A2']
        B1 = request.form['B1']
        B2 = request.form['B2']
        C1 = request.form['C1']
        C2 = request.form['C2']
        D1 = request.form['D1']
        D2 = request.form['D2']
        E1 = request.form['E1']
        E2 = request.form['E2']
        F = request.form['F']

        if user_email == main:
            cur=getCursor()
            cur.execute("""INSERT INTO e_assessment (staff_email, assess_item, performance, report_id, comments, status) VALUES (%s,'How do you rate the students overall progress in the last 6 months',%s,%s,%s,%s),\
                (%s,'How do you rate the students overall progress in terms of the 3-year PhD track',%s,%s,%s,%s),\
                (%s,'How would you rate the quality of the students academic work e.g. research writing',%s,%s,%s,%s),\
                (%s,'Students technical skill/s to complete the project',%s,%s,%s,%s),\
                (%s,'How would you rate the students likelihood of achieving the next 6-months objectives',%s,%s,%s,%s);""",(main,A1,report_id,A2,F,\
                main,B1,report_id,B2,F,main,C1,report_id,C2,F,main,D1,report_id,D2,F,main,E1,report_id,E2,F,))
    
            cur.execute("INSERT INTO progress (report_id,actioner_email,actioner_role,action_date,action_type) VALUES (%s,%s,'PG Supervisor',%s,'1 Submitted')",(report_id,main,todaydate,))

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
            for reportid in submit11:
                if reportid in submit22:
                    #Email sending to department convenor when the section E has been submitted by supervisors
                    cur=getCursor()
                    cur.execute("SELECT department_id FROM student WHERE student_email = %s ;",(studentemail,))
                    department=cur.fetchall()
                    departmentid=department[0][0]
                    cur.execute("""SELECT user_email FROM staff as s
                                JOIN user as u on u.user_email = s.staff_email
                                WHERE department_id = %s and user_role = 'PG Convenor'""",(departmentid,))
                    convenor=cur.fetchall()
                    convenoremail=convenor[0][0]
                    # print(convenoremail)
                    msg = EmailMessage()
                    msg['Subject'] = 'Reminder: Your student 6-Monthly Report - section E has been submitted by supervisors!'
                    msg['From'] = 'comp639project@gmail.com'
                    msg['To'] = convenoremail
                    msg.set_content('\n This is a reminder that your student 6-Monthly Report section E has been submitted by supervisors. \n \n Please review the 6-Monthly report and update student status.')
                    smtp = smtplib.SMTP('smtp.gmail.com', 587)
                    smtp.starttls()
                    smtp.login('comp639project@gmail.com', 'yncrimbapjfiawdw')  # login
                    text = msg.as_string()
                    smtp.sendmail('comp639project@gmail.com', convenoremail, text)
                    smtp.quit()
                    # print(msg['To'], msg['Bcc'])
                    # print('email sent')
                    
            return render_template('supervisor/E_submitted.html', title='E submitted', supervisee=supervisee, studentemail=studentemail, report_id=report_id)

        elif user_email == asst:

            cur=getCursor()
            cur.execute("""INSERT INTO e_assessment (staff_email, assess_item, performance, report_id, comments, status) VALUES (%s,'How do you rate the students overall progress in the last 6 months',%s,%s,%s,%s),\
                        (%s,'How do you rate the students overall progress in terms of the 3-year PhD track',%s,%s,%s,%s),\
                        (%s,'How would you rate the quality of the students academic work e.g. research writing',%s,%s,%s,%s),\
                        (%s,'Students technical skill/s to complete the project',%s,%s,%s,%s),\
                        (%s,'How would you rate the students likelihood of achieving the next 6-months objectives',%s,%s,%s,%s);""",(asst,A1,report_id,A2,F,\
                        asst,B1,report_id,B2,F,asst,C1,report_id,C2,F,asst,D1,report_id,D2,F,asst,E1,report_id,E2,F,))
            
            cur.execute("INSERT INTO progress (report_id,actioner_email,actioner_role,action_date,action_type) VALUES (%s,%s,'PG Supervisor',%s,'2 Submitted')",(report_id,asst,todaydate,))
            
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
            for reportid in submit11:
                if reportid in submit22:
                    # Email sending to department convenor when the section E has been submitted by supervisors
                    cur=getCursor()
                    cur.execute("SELECT department_id FROM student WHERE student_email = %s ;",(studentemail,))
                    department=cur.fetchall()
                    departmentid=department[0][0]
                    cur.execute("""SELECT user_email FROM staff as s
                                JOIN user as u on u.user_email = s.staff_email
                                WHERE department_id = %s and user_role = 'PG Convenor'""",(departmentid,))
                    convenor=cur.fetchall()
                    convenoremail=convenor[0][0]
                    print(convenoremail)
                    msg = EmailMessage()
                    msg['Subject'] = 'Reminder: Your student 6-Monthly Report - section E has been submitted by supervisors!'
                    msg['From'] = 'comp639project@gmail.com'
                    msg['To'] = convenoremail
                    msg.set_content('\n This is a reminder that your student 6-Monthly Report section E has been submitted by supervisors. \n \n Please review the 6-Monthly report and update student status.')
                    smtp = smtplib.SMTP('smtp.gmail.com', 587)
                    smtp.starttls()
                    smtp.login('comp639project@gmail.com', 'yncrimbapjfiawdw')  # login
                    text = msg.as_string()
                    smtp.sendmail('comp639project@gmail.com', convenoremail, text)
                    smtp.quit()
                    # print(msg['To'], msg['Bcc'])
                    # print('email sent')
                
                    
                    
            return render_template('supervisor/E_submitted.html', title='E submitted', supervisee=supervisee, studentemail=studentemail, report_id=report_id)

        else:
            
            cur=getCursor()
            cur.execute("""INSERT INTO e_assessment (staff_email, assess_item, performance, report_id, comments, status) VALUES (%s,'How do you rate the students overall progress in the last 6 months',%s,%s,%s,%s),\
                        (%s,'How do you rate the students overall progress in terms of the 3-year PhD track',%s,%s,%s,%s),\
                        (%s,'How would you rate the quality of the students academic work e.g. research writing',%s,%s,%s,%s),\
                        (%s,'Students technical skill/s to complete the project',%s,%s,%s,%s),\
                        (%s,'How would you rate the students likelihood of achieving the next 6-months objectives',%s,%s,%s,%s);""",(other,A1,report_id,A2,F,\
                        other,B1,report_id,B2,F,other,C1,report_id,C2,F,other,D1,report_id,D2,F,other,E1,report_id,E2,F,))
            
            cur.execute("INSERT INTO progress (report_id,actioner_email,actioner_role,action_date,action_type) VALUES (%s,%s,'PG Supervisor',%s,'3 Submitted')",(report_id,other,todaydate,))
            return render_template('supervisor/E_submitted.html', title='E submitted', supervisee=supervisee, studentemail=studentemail, report_id=report_id)
    
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