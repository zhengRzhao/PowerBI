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
from datetime import date,datetime

bp = Blueprint("student", __name__, url_prefix="/student")

############ view student profile ################
@bp.route('/profile')
def profile_view():
    user_email = session['user_email']
    connection = getCursor()
    connection.execute("""select fname,lname,address,phone,student_type,scholarship,employment,student.student_email,
department_id,enrolment_date,thesis_title,main_superv_email,asst_superv_email  from student left join employment on student.student_email=employment.student_email
left join scholarship on employment.student_email=scholarship.student_email where student.student_email=%s;""",(user_email,))
    Profileinfo = connection.fetchall()
    return render_template('student/profile.html', profileinfo=Profileinfo)  

############# edit student profile ################
# @app.route('/edit_profile')
# def edit_profile():
#     return render_template('student/profile_edit.html', title='Profile')


@bp.route('/')
@login_required
def home():
    return redirect(url_for('student.student'))

@bp.route('/home')
def student():
    user_email=session['user_email']
    cur = getCursor()
    cur.execute('SELECT fname, lname FROM student WHERE student_email = %s', (user_email,))
    user_name=cur.fetchone()
    firstname=user_name[0]
    lastname=user_name[1]
    return render_template('student/student.html', title='Home', firstname=firstname,lastname=lastname)


@bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('student/dashboard.html', title='Dashboard')

@bp.route('/profile')
@login_required
def profile():
    return render_template('student/profile.html', title='Profile')

@bp.route('/settings')
@login_required
def settings():
    return render_template('student/settings.html', title='Settings')

@bp.route('/MR')
@login_required
def MR():
    user_email=session['user_email']
    cur = getCursor()
    cur.execute('SELECT fname, lname FROM student WHERE student_email = %s', (user_email,))
    user_name=cur.fetchone()
    firstname=user_name[0]
    lastname=user_name[1]
    
    today = date.today()
    if today.month <= 6:
        due_date = date(today.year, 6, 30)
    else:
        due_date = date(today.year, 12, 31)
    
    cur=getCursor()
    cur.execute('SELECT COUNT(*) FROM report WHERE due_date=%s AND student_email =%s',(due_date,user_email,))
    num_existing1=cur.fetchall()[0][0]

    
    if num_existing1 > 0:
        cur=getCursor()
        cur.execute('SELECT report_id FROM report WHERE student_email=%s AND due_date=%s',(user_email,due_date,))
        report_id=cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM progress WHERE report_id = %s AND action_type='Submitted';",(report_id,))
        num_existingsubmittion=cur.fetchall()[0][0]
        if num_existingsubmittion>0:
            return render_template('student/SUBMITTION.html', title='Submittion',firstname=firstname,lastname=lastname)
        else:
            return render_template('student/6MR.html', title='6MR', firstname=firstname,lastname=lastname)
    else:
        return render_template('student/6MR.html', title='6MR', firstname=firstname,lastname=lastname)

@bp.route('/A',methods=['POST','GET'])
@login_required
def A():
    if request.method == 'GET':
        user_email=session['user_email']
        today = date.today()
        if today.month <= 6:
            due_date = date(today.year, 6, 30)
        else:
            due_date = date(today.year, 12, 31)

        cur = getCursor()
        cur.execute('SELECT fname, lname FROM student WHERE student_email = %s', (user_email,))
        user_name=cur.fetchone()
        firstname=user_name[0]
        lastname=user_name[1]
        fullname=f'{firstname} {lastname}'

        cur=getCursor()
        cur.execute('SELECT COUNT(*) FROM report WHERE due_date=%s AND student_email =%s',(due_date,user_email,))
        num_existing1=cur.fetchall()[0][0]

        

        
        if num_existing1 > 0:
            cur=getCursor()
            cur.execute('SELECT report_id FROM report WHERE student_email=%s AND due_date=%s',(user_email,due_date,))
            report_id=cur.fetchall()[0][0]
            cur.execute("SELECT COUNT(*) FROM progress WHERE report_id = %s AND action_type='Submitted';",(report_id,))
            num_existingsubmittion=cur.fetchall()[0][0]
            if num_existingsubmittion>0:
                return render_template('student/SUBMITTION.html', title='Submittion',firstname=firstname,lastname=lastname)
                
            else:
                cur = getCursor()
                cur.execute('SELECT s.enrolment_date, s.address, s.phone,s.student_type,s.thesis_title,\
                                CONCAT(t1.fname," ", t1.lname) AS Supervisor, CONCAT(t2.fname," ", t2.lname)\
                                AS AssSupervisor, CONCAT(t3.fname," ", t3.lname) AS OtherSupervisor FROM student AS\
                                s LEFT JOIN staff AS t1 ON s.main_superv_email = t1.staff_email\
                                LEFT JOIN staff AS t2 ON s.asst_superv_email = t2.staff_email LEFT JOIN staff as t3\
                                ON s.other_superv_email = t3.staff_email WHERE s.student_email = %s',(user_email,))
                information=cur.fetchall()

                cur=getCursor()
                cur.execute('SELECT scholarship, scholarship_value, tenure, end_date FROM scholarship WHERE student_email = %s',(user_email,))
                scholarship=cur.fetchall()

                cur=getCursor()
                cur.execute('SELECT teaching_hours, research_hours, other_hours FROM employment WHERE student_email = %s',(user_email,))
                employment=cur.fetchall()
                return render_template('student/A.html', title='Section A', user_email=user_email,fullname=fullname, firstname=firstname,\
                                            lastname=lastname, information=information,scholarship=scholarship, employment= employment)
            
        else:
            flash('You have not been started your report progress, please reading the above clarification, then push the "Start" to start your report!')
            return redirect (url_for('student.MR'))

    
    if request.method == 'POST':
        user_email=session['user_email']
        cur = getCursor()
        cur.execute('SELECT fname, lname FROM student WHERE student_email = %s', (user_email,))
        user_name=cur.fetchone()
        firstname=user_name[0]
        lastname=user_name[1]
        fullname=f'{firstname} {lastname}'
        cur = getCursor()
        cur.execute('SELECT s.enrolment_date, s.address, s.phone,s.student_type,s.thesis_title,\
                    CONCAT(t1.fname," ", t1.lname) AS Supervisor, CONCAT(t2.fname," ", t2.lname)\
                    AS AssSupervisor, CONCAT(t3.fname," ", t3.lname) AS OtherSupervisor FROM student AS\
                    s LEFT JOIN staff AS t1 ON s.main_superv_email = t1.staff_email\
                    LEFT JOIN staff AS t2 ON s.asst_superv_email = t2.staff_email LEFT JOIN staff as t3\
                    ON s.other_superv_email = t3.staff_email WHERE s.student_email = %s',(user_email,))
        information=cur.fetchall()

        cur=getCursor()
        cur.execute('SELECT scholarship, scholarship_value, tenure, end_date FROM scholarship WHERE student_email = %s',(user_email,))
        scholarship=cur.fetchall()

        cur=getCursor()
        cur.execute('SELECT teaching_hours, research_hours, other_hours FROM employment WHERE student_email = %s',(user_email,))
        employment=cur.fetchall()

        today = date.today()

        if today.month <= 6:
            due_date = date(today.year, 6, 30)
        else:
            due_date = date(today.year, 12, 31)
      

        cur=getCursor()
        cur.execute('SELECT COUNT(*) FROM report WHERE due_date=%s AND student_email =%s',(due_date,user_email,))
        num_existing=cur.fetchall()[0][0]
        if num_existing < 1:
            cur=getCursor()
            cur.execute('SELECT COUNT(*) FROM report WHERE student_email =%s;',(user_email,))
            num_completed=cur.fetchall()[0][0]
          
            num_newmilstone=num_completed+1
            cur=getCursor()
            cur.execute('INSERT INTO report (student_email, due_date, milestone_num) VALUES (%s,%s,%s)',(user_email,due_date,num_newmilstone,))
            cur.execute('SELECT report_id FROM report ORDER BY report_id DESC LIMIT 1;')
            report_id=cur.fetchall()[0][0]
           
        
            return render_template('student/A.html', title='Section A', user_email=user_email,fullname=fullname, firstname=firstname,\
                                lastname=lastname, information=information,scholarship=scholarship, employment= employment)
        else:
            flash('Your report has been started, please click "Section A" in Navigator Bar to continue your report')
            return redirect (url_for('student.MR'))

########################################################################
########################################################################
#Below code to complete section A when click the "Confirm" button in Section A to fill the date in "progress table"

@bp.route('/B', methods=['POST','GET'])
@login_required
def B():
    if request.method == 'POST':
        user_email=session['user_email']
        cur = getCursor()
        cur.execute('SELECT fname, lname FROM student WHERE student_email = %s', (user_email,))
        user_name=cur.fetchone()
        firstname=user_name[0]
        lastname=user_name[1]
        todaydate = date.today()
        if todaydate.month <= 6:
            due_date = date(todaydate.year, 6, 30)
        else:
            due_date = date(todaydate.year, 12, 31)
        cur=getCursor()
        cur.execute('SELECT report_id FROM report WHERE student_email=%s AND due_date=%s',(user_email,due_date,))
        report_id=cur.fetchone()[0]
        cur.execute('SELECT milestone_num FROM report WHERE student_email=%s AND due_date=%s',(user_email,due_date,))
        milestone_num= cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM progress WHERE report_id=%s AND actioner_email=%s AND action_type='A Completed'",(report_id,user_email,))
        numofAcompleted=cur.fetchall()[0][0]
        cur=getCursor
        if numofAcompleted <1:
            cur=getCursor()
            cur.execute("INSERT INTO progress (report_id,actioner_email,actioner_role,action_date,action_type) VALUES (%s,%s,'PG Student',%s,'A Completed')",(report_id,user_email,todaydate,))
            
        
        return render_template('student/B.html', title='Section B',milestone_num=milestone_num,firstname=firstname,lastname=lastname)
    
    if request.method == 'GET':
        user_email=session['user_email']
        cur = getCursor()
        cur.execute('SELECT fname, lname FROM student WHERE student_email = %s', (user_email,))
        user_name=cur.fetchone()
        firstname=user_name[0]
        lastname=user_name[1]
        today = date.today()
        if today.month <= 6:
            due_date = date(today.year, 6, 30)
        else:
            due_date = date(today.year, 12, 31)

        cur=getCursor()
        cur.execute('SELECT COUNT(*) FROM report WHERE due_date=%s AND student_email =%s',(due_date,user_email,))
        num_existing1=cur.fetchall()[0][0]

        if num_existing1 > 0:
            cur.execute('SELECT report_id FROM report WHERE student_email=%s AND due_date=%s;',(user_email,due_date,))
            report_id=cur.fetchall()[0][0]
            cur.execute("SELECT COUNT(*) FROM progress WHERE report_id = %s AND action_type='Submitted';",(report_id,))
            num_existingsubmittion=cur.fetchall()[0][0]
            if num_existingsubmittion>0:
                return render_template('student/SUBMITTION.html', title='Submittion',firstname=firstname,lastname=lastname)
            else:
                cur=getCursor()
                cur.execute("SELECT COUNT(*) FROM progress WHERE report_id=%s AND action_type ='A Completed';",(report_id,))
                numofAcompletion=cur.fetchall()[0][0]
                if numofAcompletion>0:
                    cur=getCursor()
                    cur.execute('SELECT milestone_num FROM report Where report_id=%s;',(report_id,))
                    milestone_num = int(cur.fetchall()[0][0])
                    return render_template('student/B.html', title='Section B',milestone_num=milestone_num,firstname=firstname,lastname=lastname)
                else:
                    flash('You have not been completed your Section A, please complete Section A firstly!')
                    return redirect(url_for('student.A'))
        else:
            flash('You have not been started your report progress, please reading the above clarification, then push the "Start" to start your report!')
            return redirect (url_for('student.MR'))

######################################################################################### 
@bp.route('/SectionBsubmit', methods=['POST'])
@login_required
def SectionBsubmit():
    user_email=session['user_email']
    todaydate = date.today()
    if todaydate.month <= 6:
        due_date = date(todaydate.year, 6, 30)
    else:
        due_date = date(todaydate.year, 12, 31)
    cur=getCursor()
    cur.execute('SELECT report_id FROM report WHERE student_email=%s AND due_date=%s',(user_email,due_date,))
    report_id=cur.fetchone()[0]

    induction_program = request.form.get('induction_program')
    induction_program_date = request.form.get('induction_program_date_input')
    induction_program_completed = 1 if induction_program == 'completed' else 0

    mutual_expectations = request.form.get('mutual_expectations')
    mutual_expectations_date = request.form.get('mutual_expectations_date_input')
    mutual_expectations_completed = 1 if mutual_expectations == 'completed' else 0

    kaupapa_maori = request.form.get('kaupapa_maori')
    kaupapa_maori_date = request.form.get('kaupapa_maori_date_input')
    kaupapa_maori_completed = 1 if kaupapa_maori == 'completed' else 0

    intellectual_property = request.form.get('intellectual_property')
    intellectual_property_date = request.form.get('intellectual_property_date_input')
    intellectual_property_completed = 1 if intellectual_property == 'completed' else 0

    thesis_proposal = request.form.get('thesis_proposal')
    thesis_proposal_date = request.form.get('thesis_proposal_date_input')
    thesis_proposal_completed = 1 if thesis_proposal == 'completed' else 0

    research_proposal = request.form.get('research_proposal')
    research_proposal_date = request.form.get('research_proposal_date_input')
    research_proposal_completed = 1 if research_proposal == 'completed' else 0

    presentation = request.form.get('presentation')
    presentation_date = request.form.get('presentation_date_input')
    presentation_completed = 1 if presentation == 'completed' else 0

    seminar = request.form.get('seminar')
    seminar_date = request.form.get('seminar_date_input')
    seminar_completed = 1 if seminar == 'completed' else 0

    cur=getCursor()
    cur.execute('SELECT COUNT(*) FROM b_step WHERE report_id=%s;',(report_id,))
    reportofstep=cur.fetchone()[0]
    if reportofstep < 1:

        cur=getCursor()
        cur.execute("INSERT INTO b_step VALUES (%s,'Induction Programme (Compulsory)', %s,%s),\
                    (%s,'Mutual Expectations Agreement (Compulsory)',%s,%s),\
                    (%s,'Kaupapa Māori Research MEA (Compulsory if relevant)',%s,%s),\
                    (%s,'Intellectual Property Agreement (Compulsory if relevant)',%s,%s),\
                    (%s,'Thesis proposal seminar (Compulsory)',%s,%s),\
                    (%s,'Research Proposal Approved by appropriate Faculty/Centre Postgraduate or equivalent Committee (Compulsory)',%s,%s),\
                    (%s,'Lincoln University PG conference presentation',%s,%s),\
                    (%s,'Thesis Results Seminar (Strongly recommended)',%s,%s);",(report_id,induction_program_completed,induction_program_date,report_id,mutual_expectations_completed,\
    mutual_expectations_date,report_id,kaupapa_maori_completed,kaupapa_maori_date,report_id,intellectual_property_completed,intellectual_property_date,\
            report_id,thesis_proposal_completed,thesis_proposal_date,report_id,research_proposal_completed,research_proposal_date,\
                report_id,presentation_completed,presentation_date,report_id,seminar_completed,seminar_date,))
        cur.close
    else:
        cur=getCursor()
        cur.execute("UPDATE b_step SET compulsory =%s, complete_date=%s WHERE report_id=%s AND step='Induction Programme (Compulsory)';",(induction_program_completed,induction_program_date,report_id,))
        cur.execute("UPDATE b_step SET compulsory =%s, complete_date=%s WHERE report_id=%s AND step='Mutual Expectations Agreement (Compulsory)';",(mutual_expectations_completed,mutual_expectations_date,report_id))
        cur.execute("UPDATE b_step SET compulsory =%s, complete_date=%s WHERE report_id=%s AND step='Kaupapa Māori Research MEA (Compulsory if relevant)';",(kaupapa_maori_completed,kaupapa_maori_date,report_id,))
        cur.execute("UPDATE b_step SET compulsory =%s, complete_date=%s WHERE report_id=%s AND step='Intellectual Property Agreement (Compulsory if relevant)';",(intellectual_property_completed,intellectual_property_date,report_id,))
        cur.execute("UPDATE b_step SET compulsory =%s, complete_date=%s WHERE report_id=%s AND step='Thesis proposal seminar (Compulsory)';",(thesis_proposal_completed,thesis_proposal_date,report_id,))
        cur.execute("UPDATE b_step SET compulsory =%s, complete_date=%s WHERE report_id=%s AND step='Research Proposal Approved by appropriate Faculty/Centre Postgraduate or equivalent Committee (Compulsory)';",(research_proposal_completed,research_proposal_date,report_id,))
        cur.execute("UPDATE b_step SET compulsory =%s, complete_date=%s WHERE report_id=%s AND step='Lincoln University PG conference presentation';",(presentation_completed,presentation_date,report_id,))
        cur.execute("UPDATE b_step SET compulsory =%s, complete_date=%s WHERE report_id=%s AND step='Thesis Results Seminar (Strongly recommended)';",(seminar_completed,seminar_date,report_id,))
        cur.close

    

#################################################### Section B Part Two  ###################################   
    ethics = request.form.get('ethics')
    ethics_need= 1 if ethics == 'needed' else 0
    heapproval = request.form.get('heapproval')
    heapproval_ed= 1 if heapproval == 'on' else 0
    

    health = request.form.get('health')
    health_need = 1 if health == 'needed' else 0
    hsapproval = request.form.get('hsapproval')
    hsapproval_ed = 1 if hsapproval == 'on' else 0

    animal = request.form.get('animal')
    animal_need = 1 if animal == 'needed' else 0
    aeapproval = request.form.get('aeapproval')
    aeapproval_ed = 1 if aeapproval == 'on' else 0

    bio = request.form.get('bio')
    bio_need = 1 if bio == 'needed' else 0
    ibapproval = request.form.get('ibapproval')
    ibapproval_ed = 1 if ibapproval == 'on' else 0

    radiation = request.form.get('radiation')
    radiation_need = 1 if radiation == 'needed' else 0
    rpapproval = request.form.get('rpapproval')
    rpapproval_ed = 1 if rpapproval == 'on' else 0

    cur=getCursor()
    cur.execute('SELECT COUNT(*) FROM b_research_approval WHERE report_id=%s;',(report_id,))
    reportofresearch=cur.fetchone()[0]

    if reportofresearch < 1:
        cur=getCursor()
        cur.execute("INSERT INTO b_research_approval VALUES (%s,'Human Ethics Commitee',%s,%s),\
                    (%s,'Health and Safety Committee',%s,%s),\
                    (%s,'Animal Ethics Committee',%s,%s),\
                    (%s,'Institutional Biological Safety Committee',%s,%s),\
                    (%s,'Radiation Protection Officer',%s,%s);",\
                        (report_id,ethics_need,heapproval_ed,report_id,health_need,hsapproval_ed,report_id,animal_need,aeapproval_ed,\
                        report_id,bio_need,ibapproval_ed,report_id,radiation_need,rpapproval_ed,))
        

    else:
        cur=getCursor()
        cur.execute("UPDATE b_research_approval SET needed=%s, approval=%s WHERE report_id=%s AND committee='Human Ethics Commitee';",(ethics_need,heapproval_ed,report_id,))
        cur.execute("UPDATE b_research_approval SET needed=%s, approval=%s WHERE report_id=%s AND committee='Health and Safety Committee';",(health_need,hsapproval_ed,report_id,))
        cur.execute("UPDATE b_research_approval SET needed=%s, approval=%s WHERE report_id=%s AND committee='Animal Ethics Committee';",(animal_need,aeapproval_ed,report_id,))
        cur.execute("UPDATE b_research_approval SET needed=%s, approval=%s WHERE report_id=%s AND committee='Institutional Biological Safety Committee';",(bio_need,ibapproval_ed,report_id,))
        cur.execute("UPDATE b_research_approval SET needed=%s, approval=%s WHERE report_id=%s AND committee='Radiation Protection Officer';",(radiation_need,rpapproval_ed,report_id,))
        



############################################### Below Section B Part Three########################
    milestone_num_update=int(request.form['milestone_num'])
    cur=getCursor()
    cur.execute('UPDATE report SET milestone_num=%s WHERE report_id=%s;',(milestone_num_update,report_id,))
   
    
    cur = getCursor()
    cur.execute('SELECT fname, lname FROM student WHERE student_email = %s', (user_email,))
    user_name=cur.fetchone()
    firstname=user_name[0]
    lastname=user_name[1]
    todaydate = date.today()
    cur=getCursor()
    cur.execute("INSERT INTO progress (report_id,actioner_email,actioner_role,action_date,action_type) VALUES (%s,%s,'PG Student',%s,'B Completed')",(report_id,user_email,todaydate,))
    

    return render_template('student/C.html', title='Section C',firstname=firstname,lastname=lastname)



##########################################################################
#########################################################################Below for Section C############################

@bp.route('/C', methods=['POST','GET'])
@login_required
def C():
    if request.method == 'GET':
        user_email=session['user_email']
        cur = getCursor()
        cur.execute('SELECT fname, lname FROM student WHERE student_email = %s', (user_email,))
        user_name=cur.fetchone()
        firstname=user_name[0]
        lastname=user_name[1]
        today = date.today()
        if today.month <= 6:
            due_date = date(today.year, 6, 30)
        else:
            due_date = date(today.year, 12, 31)

        cur=getCursor()
        cur.execute('SELECT COUNT(*) FROM report WHERE due_date=%s AND student_email =%s',(due_date,user_email,))
        num_existing1=cur.fetchall()[0][0]
        if num_existing1 > 0:
            cur.execute('SELECT report_id FROM report WHERE student_email=%s AND due_date=%s;',(user_email,due_date,))
            report_id=cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM progress WHERE report_id = %s AND action_type='Submitted';",(report_id,))
            num_existingsubmittion1=cur.fetchall()[0][0]
        
            if num_existingsubmittion1>0:
                return render_template('student/SUBMITTION.html', title='Submittion',firstname=firstname,lastname=lastname)
            else:
                cur=getCursor()    
                cur.execute("SELECT COUNT(*) FROM progress WHERE report_id=%s AND action_type ='A Completed';",(report_id,))
                numofAcompletion=cur.fetchall()[0][0]
                cur.execute("SELECT COUNT(*) FROM progress WHERE report_id=%s AND action_type ='B Completed';",(report_id,))
                numofBcompletion=cur.fetchall()[0][0]
                if numofAcompletion>0 and numofBcompletion<1:
                    cur=getCursor()
                    cur.execute('SELECT milestone_num FROM report Where report_id=%s;',(report_id,))
                    milestone_num = int(cur.fetchall()[0][0])
                    flash('You have not been completed your Section B, please complete Section B firstly!')
                    return render_template('student/B.html', title='Section B',milestone_num=milestone_num,firstname=firstname,lastname=lastname)
                elif numofAcompletion<1:
                    flash('You have not been completed your Section A, please complete Section A firstly!')
                    return redirect(url_for('student.A'))

                else:
                    return render_template('student/C.html', title='Section C',firstname=firstname,lastname=lastname)
        else:
            flash('You have not been started your report progress, please reading the above clarification, then push the "Start" to start your report!')
            return redirect (url_for('student.MR'))
    
    if request.method == 'POST':
        user_email=session['user_email']
        cur = getCursor()
        cur.execute('SELECT fname, lname FROM student WHERE student_email = %s', (user_email,))
        user_name=cur.fetchone()
        firstname=user_name[0]
        lastname=user_name[1]

        return render_template('student/C.html', title='Section C',firstname=firstname,lastname=lastname)
    
####################################################Section C Form submittion###########################################

@bp.route('/SectionCsubmit', methods=['POST'])
@login_required
def SectionCsubmit():
    user_email=session['user_email']
    cur = getCursor()
    cur.execute('SELECT fname, lname FROM student WHERE student_email = %s', (user_email,))
    user_name=cur.fetchone()
    firstname=user_name[0]
    lastname=user_name[1]
    todaydate = date.today()
    if todaydate.month <= 6:
        due_date = date(todaydate.year, 6, 30)
    else:
        due_date = date(todaydate.year, 12, 31)
    cur=getCursor()
    cur.execute('SELECT report_id FROM report WHERE student_email=%s AND due_date=%s',(user_email,due_date,))
    report_id=cur.fetchone()[0]

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
    F1 = request.form['F1']
    F2 = request.form['F2']
    G1 = request.form['G1']
    G2 = request.form['G2']
    H1 = request.form['H1']
    H2 = request.form['H2']
    I1 = request.form['I1']
    I2 = request.form['I2']
    J1 = request.form['J1']
    J2 = request.form['J2']
    K1 = request.form['K1']
    K2 = request.form['K2']
    L1 = request.form['L1']
    L2 = request.form['L2']
    M1 = request.form['M1']
    M2 = request.form['M2']
    N1 = request.form['N1']
    N2 = request.form['N2']
    O1 = request.form['O1']
    O2 = request.form['O2']
    P1 = request.form['P1']
    P2 = request.form['P2']
    Q1 = request.form['Q1']
    Q2 = request.form['Q2']
    R1 = request.form['R1']
    R2 = request.form['R2']
    S1 = request.form['S1']
    S2 = request.form['S2']
    T1 = request.form['T1']
    T2 = request.form['T2']
    U1 = request.form['U1']
    V1 = request.form['V1']
    W1 = request.form.getlist('W1')
   
    NEW_W1 = " "
    for i in W1:
        NEW_W1 += i+","
    
    NEW_W1 = NEW_W1[:-1]
  
    

    cur=getCursor()
    cur.execute('SELECT COUNT(*) FROM c_evaluation WHERE report_id=%s;',(report_id,))
    reportofc_evaluation=cur.fetchone()[0]
    if reportofc_evaluation < 1:
        cur=getCursor()
        cur.execute("INSERT INTO c_evaluation VALUES (1,%s,'Access_to_supervisors_principal',%s,%s),\
                    (2,%s,'Access_to_supervisors_associate_and_others',%s,%s),\
                    (3,%s,'Supervisor_expertise_principal',%s,%s),\
                    (4,%s,'Supervisor_expertise_associate_and_others',%s,%s),\
                    (5,%s,'Quality_of_supervisor_feedback_principal',%s,%s),\
                    (6,%s,'Quality_of_supervisor_feedback_associate_and_others',%s,%s),\
                    (7,%s,'Timeliness_of_supervisor_feedback_principal',%s,%s),\
                    (8,%s,'Timeliness_of_supervisor_feedback_associate_and_others',%s,%s),\
                    (9,%s,'Courses_available',%s,%s),\
                    (10,%s,'Workspace',%s,%s),\
                    (11,%s,'Computer_facilities',%s,%s),\
                    (12,%s,'ITS_support',%s,%s),\
                    (13,%s,'Research_software',%s,%s),\
                    (14,%s,'Library_facilities',%s,%s),\
                    (15,%s,'Teaching_Learning_Centre_support',%s,%s),(16,%s,'Statistical_support',%s,%s), (17,%s,'Research_equipment',%s,%s),\
                    (18,%s,'Technical_support',%s,%s),(19,%s,'Financial_resources',%s,%s),(20,%s,'Other_comments',%s,%s);",(report_id,A1,A2,\
                    report_id,B1,B2,report_id,C1,C2,report_id,D1,D2,report_id,E1,E2,report_id,F1,F2,report_id,G1,G2,report_id,H1,H2,\
                        report_id,I1,I2,report_id,J1,J2,report_id,K1,K2,report_id,L1,L2,report_id,M1,M2,report_id,N1,N2,report_id,O1,O2,\
                            report_id,P1,P2,report_id,Q1,Q2,report_id,R1,R2,report_id,S1,S2,report_id,T1,T2,))
        
        cur.execute('INSERT INTO c_feedback VALUES (%s,%s,%s,%s);',(report_id,U1,V1,NEW_W1,))
        

    else:
        cur=getCursor()
        cur.execute("UPDATE c_evaluation SET evaluation_result=%s,comments=%s WHERE report_id=%s AND evaluation_item='Access_to_supervisors_principal';", (A1, A2, report_id,))
        cur.execute("UPDATE c_evaluation SET evaluation_result=%s,comments=%s WHERE report_id=%s AND evaluation_item='Access_to_supervisors_associate_and_others';", (B1, B2, report_id,))
        cur.execute("UPDATE c_evaluation SET evaluation_result=%s,comments=%s WHERE report_id=%s AND evaluation_item='Supervisor_expertise_principal';", (C1, C2, report_id,))
        cur.execute("UPDATE c_evaluation SET evaluation_result=%s,comments=%s WHERE report_id=%s AND evaluation_item='Supervisor_expertise_associate_and_others';", (D1, D2, report_id,))
        cur.execute("UPDATE c_evaluation SET evaluation_result=%s,comments=%s WHERE report_id=%s AND evaluation_item='Quality_of_supervisor_feedback_principal';", (E1, E2, report_id,))
        cur.execute("UPDATE c_evaluation SET evaluation_result=%s,comments=%s WHERE report_id=%s AND evaluation_item='Quality_of_supervisor_feedback_associate_and_others';", (F1, F2, report_id,))
        cur.execute("UPDATE c_evaluation SET evaluation_result=%s,comments=%s WHERE report_id=%s AND evaluation_item='Timeliness_of_supervisor_feedback_principal';", (G1, G2, report_id,))
        cur.execute("UPDATE c_evaluation SET evaluation_result=%s,comments=%s WHERE report_id=%s AND evaluation_item='Timeliness_of_supervisor_feedback_associate_and_others';", (H1, H2, report_id,))
        cur.execute("UPDATE c_evaluation SET evaluation_result=%s,comments=%s WHERE report_id=%s AND evaluation_item='Courses_available';", (I1, I2, report_id,))
        cur.execute("UPDATE c_evaluation SET evaluation_result=%s,comments=%s WHERE report_id=%s AND evaluation_item='Workspace';", (J1, J2, report_id,))
        cur.execute("UPDATE c_evaluation SET evaluation_result=%s,comments=%s WHERE report_id=%s AND evaluation_item='Computer_facilities';", (K1, K2, report_id,))
        cur.execute("UPDATE c_evaluation SET evaluation_result=%s,comments=%s WHERE report_id=%s AND evaluation_item='ITS_support';", (L1, L2, report_id,))
        cur.execute("UPDATE c_evaluation SET evaluation_result=%s,comments=%s WHERE report_id=%s AND evaluation_item='Research_software';", (M1, M2, report_id,))
        cur.execute("UPDATE c_evaluation SET evaluation_result=%s,comments=%s WHERE report_id=%s AND evaluation_item='Library_facilities';", (N1, N2, report_id,))
        cur.execute("UPDATE c_evaluation SET evaluation_result=%s,comments=%s WHERE report_id=%s AND evaluation_item='Teaching_Learning_Centre_support';", (O1, O2, report_id,))
        cur.execute("UPDATE c_evaluation SET evaluation_result=%s,comments=%s WHERE report_id=%s AND evaluation_item='Statistical_support';", (P1, P2, report_id,))
        cur.execute("UPDATE c_evaluation SET evaluation_result=%s,comments=%s WHERE report_id=%s AND evaluation_item='Research_equipment';", (Q1, Q2, report_id,))
        cur.execute("UPDATE c_evaluation SET evaluation_result=%s,comments=%s WHERE report_id=%s AND evaluation_item='Technical_support';", (R1, R2,report_id,))
        cur.execute("UPDATE c_evaluation SET evaluation_result=%s,comments=%s WHERE report_id=%s AND evaluation_item='Financial_resources';", (S1, S2, report_id,))
        cur.execute("UPDATE c_evaluation SET evaluation_result=%s,comments=%s WHERE report_id=%s AND evaluation_item='Other_comments';", (T1, T2,report_id,))
        
        cur.execute('UPDATE c_feedback SET frequency=%s,feedback_received=%s,feedback_method=%s WHERE report_id=%s;',(U1,V1,NEW_W1,report_id,))
        
    
    cur=getCursor()
    cur.execute("INSERT INTO progress (report_id,actioner_email,actioner_role,action_date,action_type) VALUES (%s,%s,'PG Student',%s,'C Completed')",(report_id,user_email,todaydate,))
    return redirect (url_for('student.D'))



#############################################################################################################
#############################################################################################################
@bp.route('/D', methods=['POST','GET'])
@login_required
def D():
    if request.method == 'GET':
        user_email=session['user_email']
        cur = getCursor()
        cur.execute('SELECT fname, lname FROM student WHERE student_email = %s', (user_email,))
        user_name=cur.fetchone()
        firstname=user_name[0]
        lastname=user_name[1]
        today = date.today()
        if today.month <= 6:
            due_date = date(today.year, 6, 30)
        else:
            due_date = date(today.year, 12, 31)

        cur=getCursor()
        cur.execute('SELECT COUNT(*) FROM report WHERE due_date=%s AND student_email =%s',(due_date,user_email,))
        num_existing1=cur.fetchall()[0][0]


        
        if num_existing1 > 0:
            cur.execute('SELECT report_id FROM report WHERE student_email=%s AND due_date=%s;',(user_email,due_date,))
            report_id=cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM progress WHERE report_id = %s AND action_type='C Completed';",(report_id,))
            numofCcompletion=cur.fetchall()[0][0]
            cur.execute("SELECT COUNT(*) FROM progress WHERE report_id = %s AND action_type='Submitted';",(report_id,))
            numofcompletion=cur.fetchall()[0][0]
            if numofcompletion>0:
               return render_template('student/SUBMITTION.html', title='Submittion',firstname=firstname,lastname=lastname) 
            
            else:
                if numofCcompletion>0:
                    cur=getCursor()
                
                    cur.execute('SELECT milestone_num FROM report WHERE student_email=%s AND due_date=%s',(user_email,due_date,))
                    milestone_num= cur.fetchone()[0]
                    cur.execute('SELECT report_id FROM report WHERE milestone_num=%s;',(milestone_num,))
                    this_milestone_number=cur.fetchone()[0]
                    if this_milestone_number > 1:
                        last_milestone_number=this_milestone_number-1
                        cur.execute('SELECT report_id FROM report WHERE milestone_num=%s;',(last_milestone_number,))
                        last_report_id=cur.fetchone()[0]


                        cur=getCursor()
                        cur.execute('SELECT research_objective FROM d_research_progress WHERE report_id=%s;',(last_report_id,) )
                        r_objectives=cur.fetchall()
                    
                        cur.execute('SELECT COUNT(*) FROM d_research_progress WHERE report_id=%s;',(last_report_id,))
                        num_objectives=cur.fetchall()[0][0]
                    else:
                        r_objectives=None
                        num_objectives=0
                        last_report_id=0
                

                    flash('Please make sure you have discussed with your Supervisors before filling the Section D')
                    return render_template('student/D.html', title='Section D',firstname=firstname,lastname=lastname,r_objectives=r_objectives,num_objectives=num_objectives,last_report_id=last_report_id)
                else:
                    cur=getCursor()    
                    cur.execute("SELECT COUNT(*) FROM progress WHERE report_id=%s AND action_type ='A Completed';",(report_id,))
                    numofAcompletion=cur.fetchall()[0][0]
                    cur.execute("SELECT COUNT(*) FROM progress WHERE report_id=%s AND action_type ='B Completed';",(report_id,))
                    numofBcompletion=cur.fetchall()[0][0]
                    cur.execute("SELECT COUNT(*) FROM progress WHERE report_id=%s AND action_type ='C Completed';",(report_id,))
                    numofCcompletion=cur.fetchall()[0][0]
                    if numofAcompletion>0 and numofBcompletion<1:
                        cur=getCursor()
                        cur.execute('SELECT milestone_num FROM report Where report_id=%s;',(report_id,))
                        milestone_num = int(cur.fetchall()[0][0])
                        flash('You have not been completed your Section B, please complete Section B firstly!')
                        return render_template('student/B.html', title='Section B',milestone_num=milestone_num,firstname=firstname,lastname=lastname)
                    elif numofAcompletion<1:
                        flash('You have not been completed your Section A, please complete Section A firstly!')
                        return redirect(url_for('student.A'))

                    elif numofBcompletion>0 and numofCcompletion<1:
                        flash('You have not been completed your Section C, please complete Section C firstly!')
                        return render_template('student/C.html', title='Section C',firstname=firstname,lastname=lastname)

        else:
            flash('You have not been started your report progress, please reading the above clarification, then push the "Start" to start your report!')
            return redirect (url_for('student.MR'))

    if request.method == 'POST':
        user_email=session['user_email']
        cur = getCursor()
        cur.execute('SELECT fname, lname FROM student WHERE student_email = %s', (user_email,))
        user_name=cur.fetchone()
        firstname=user_name[0]
        lastname=user_name[1]
        today = date.today()
        if today.month <= 6:
            due_date = date(today.year, 6, 30)
        else:
            due_date = date(today.year, 12, 31)

        cur=getCursor()
        cur.execute('SELECT COUNT(*) FROM report WHERE due_date=%s AND student_email =%s',(due_date,user_email,))
        num_existing1=cur.fetchall()[0][0]

        cur.execute('SELECT milestone_num FROM report WHERE student_email=%s AND due_date=%s',(user_email,due_date,))
        milestone_num= cur.fetchone()[0]

        cur.execute('SELECT report_id FROM report WHERE student_email=%s AND due_date=%s;',(user_email,due_date,))
        report_id=cur.fetchone()[0]
   

        last_report_id = request.form.get('last_report_id')
        num_objectives=int(request.form['num_objectives'])

        cur=getCursor()
        cur.execute('SELECT research_objective FROM d_research_progress WHERE report_id=%s;',(last_report_id,) )
        r_objectives=cur.fetchall()
       
 #####################Section D table one#############################       
        for i in range(num_objectives):
            status = request.form.get(f'objective{i}')
            comment = request.form.get(f'comment{i}')
            change=request.form.get(f'change{i}')
            cur=getCursor()
            cur.execute('UPDATE d_research_progress SET status=%s,incomplete_comments=%s,change_comments=%s\
                         WHERE report_id=%s AND research_objective=%s;',(status,comment,change,last_report_id,r_objectives[i][0],))

#####################Section D Table Two #############################        
        cur=getCursor()
        cur.execute('DELETE FROM d_covid WHERE report_id=%s;',(report_id,)) 
        for x in range(1,7):
            impact=request.form.get(f'covid-effect{x}')
            cur=getCursor()
            cur.execute('INSERT INTO d_covid VALUES (%s,%s);',(report_id,impact,)) 
            cur.execute("DELETE FROM d_covid WHERE report_id=%s AND impact='';",(report_id,))

###################### Section D Table Three #############################     
        cur=getCursor()
        cur.execute('DELETE FROM d_achivement WHERE report_id=%s;',(report_id,)) 
        for y in range(1,7):
            achieve=request.form.get(f'achieve{y}')
            cur=getCursor()
            cur.execute('INSERT INTO d_achivement VALUES (%s,%s);',(report_id,achieve,)) 
            cur.execute("DELETE FROM d_achivement WHERE report_id=%s AND achivement='';",(report_id,))

#####################Section D table Four #############################
        cur=getCursor()
        cur.execute('DELETE FROM d_research_progress WHERE report_id=%s;',(report_id,)) 
        for z in range(1,7):
            new_objective=request.form.get(f'newobjective{z}')
            target_completion_date=request.form.get(f'completion{z}')
            problem=request.form.get(f'problems{z}')
            research_id=z
            if new_objective != '':
                if target_completion_date != None:
                    target_completion_date = datetime.strptime(target_completion_date, '%Y-%m-%d').date()
                else:
                    target_completion_date = None

                cur = getCursor()
                cur.execute("INSERT INTO d_research_progress (research_id, report_id, research_objective, target_completion_date, anticipated_problems, status) VALUES (%s, %s, %s, %s, %s, 'not completed');",
                            (research_id, report_id, new_objective, target_completion_date, problem))
                cur.execute("DELETE FROM d_research_progress WHERE report_id = %s AND research_objective IS NULL;", (report_id,))
            else:
                cur = getCursor()
                cur.execute("INSERT INTO d_research_progress (research_id, report_id, research_objective, target_completion_date, anticipated_problems, status) VALUES (%s, %s,NULL,NULL,NULL,NULL);", (research_id, report_id,))
                cur.execute("DELETE FROM d_research_progress WHERE report_id = %s AND research_objective IS NULL;", (report_id,))

##################### Section D Table Five #############################
        cur=getCursor()
        cur.execute('DELETE FROM d_research_expense WHERE report_id=%s;',(report_id,))
        for a in range(1,7):
            item=request.form.get(f'item{a}')
            amount=request.form.get(f'amount{a}')
            if amount=='':
                amount=0.00
            else:
                amount=amount
                amount=int(amount)
                
            note=request.form.get(f'note{a}')
          

            cur = getCursor()
            cur.execute('INSERT INTO d_research_expense (report_id,item,amount,notes) VALUES (%s,%s,%s,%s);',(report_id,item,amount,note,))
            cur.execute("DELETE FROM d_research_expense WHERE report_id=%s AND item='';",(report_id,))

                
          
        cur=getCursor()
        cur.execute("INSERT INTO progress (report_id,actioner_email,actioner_role,action_date,action_type) VALUES (%s,%s,'PG Student',%s,'D Completed')",(report_id,user_email,today,))
        return redirect (url_for('student.F'))
                        

        
        






###################################################################################################
@bp.route('/E')
@login_required
def E():
    return render_template('student/E.html', title='Section E')

######################################################################################

@bp.route('/F',methods=['POST','GET'])
@login_required
def F():
    if request.method == 'GET': 
        
        user_email=session['user_email']
        today = date.today()
        if today.month <= 6:
            due_date = date(today.year, 6, 30)
        else:
            due_date = date(today.year, 12, 31)

        cur = getCursor()
        cur.execute('SELECT fname, lname FROM student WHERE student_email = %s', (user_email,))
        user_name=cur.fetchone()
        firstname=user_name[0]
        lastname=user_name[1]
        fullname=f'{firstname} {lastname}'

        cur=getCursor()
        cur.execute('SELECT COUNT(*) FROM report WHERE due_date=%s AND student_email =%s',(due_date,user_email,))
        num_existing1=cur.fetchall()[0][0]

        
        if num_existing1 > 0:
            cur=getCursor()
            cur.execute('SELECT report_id FROM report WHERE student_email=%s AND due_date=%s;',(user_email,due_date,))
            report_id=cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM progress WHERE report_id = %s AND action_type='D Completed';",(report_id,))
            numofDcompletion=cur.fetchall()[0][0]
            cur.execute("SELECT COUNT(*) FROM progress WHERE report_id = %s AND action_type='Submitted';",(report_id,))
            num_existingsubmittion=cur.fetchall()[0][0]
            if num_existingsubmittion>0:
                return render_template('student/SUBMITTION.html', title='Submittion',firstname=firstname,lastname=lastname)
            else:
                if numofDcompletion>0:
                    cur = getCursor()
                    cur.execute('SELECT CONCAT(t1.fname," ", t1.lname) AS Supervisor, CONCAT(t2.fname," ", t2.lname)\
                                AS AssSupervisor, CONCAT(t3.fname," ", t3.lname) AS OtherSupervisor FROM student AS\
                                s LEFT JOIN staff AS t1 ON s.main_superv_email = t1.staff_email\
                                LEFT JOIN staff AS t2 ON s.asst_superv_email = t2.staff_email LEFT JOIN staff as t3\
                                ON s.other_superv_email = t3.staff_email WHERE s.student_email = %s',(user_email,))
                    supervisors=cur.fetchall()
                    print(supervisors)
                    flash("Section F is an optional form, if you are not confortable to fill Section F, please push the button 'Submit without Section F' to complete your 6-month report")
                    return render_template('student/F.html', title='Section F', fullname=fullname,firstname=firstname,lastname=lastname,supervisors=supervisors)
            
                else: 
                    cur=getCursor()    
                    cur.execute("SELECT COUNT(*) FROM progress WHERE report_id=%s AND action_type ='A Completed';",(report_id,))
                    numofAcompletion=cur.fetchall()[0][0]
                    cur.execute("SELECT COUNT(*) FROM progress WHERE report_id=%s AND action_type ='B Completed';",(report_id,))
                    numofBcompletion=cur.fetchall()[0][0]
                    cur.execute("SELECT COUNT(*) FROM progress WHERE report_id=%s AND action_type ='C Completed';",(report_id,))
                    numofCcompletion=cur.fetchall()[0][0]
                    if numofAcompletion>0 and numofBcompletion<1:
                        cur=getCursor()
                        cur.execute('SELECT milestone_num FROM report Where report_id=%s;',(report_id,))
                        milestone_num = int(cur.fetchall()[0][0])
                        flash('You have not been completed your Section B, please complete Section B firstly!')
                        return render_template('student/B.html', title='Section B',milestone_num=milestone_num,firstname=firstname,lastname=lastname)
                    elif numofAcompletion<1:
                        flash('You have not been completed your Section A, please complete Section A firstly!')
                        return redirect(url_for('student.A'))

                    elif numofBcompletion>0 and numofCcompletion<1:
                        flash('You have not been completed your Section C, please complete Section C firstly!')
                        return render_template('student/C.html', title='Section C',firstname=firstname,lastname=lastname)
                    elif numofCcompletion>0 and numofDcompletion<1:
                        cur=getCursor()
                        cur.execute('SELECT milestone_num FROM report WHERE student_email=%s AND due_date=%s',(user_email,due_date,))
                        milestone_num= cur.fetchone()[0]
                        cur.execute('SELECT report_id FROM report WHERE milestone_num=%s;',(milestone_num,))
                        this_milestone_number=cur.fetchone()[0]
                        if this_milestone_number > 1:
                            last_milestone_number=this_milestone_number-1
                            cur.execute('SELECT report_id FROM report WHERE milestone_num=%s;',(last_milestone_number,))
                            last_report_id=cur.fetchone()[0]


                            cur=getCursor()
                            cur.execute('SELECT research_objective FROM d_research_progress WHERE report_id=%s;',(last_report_id,) )
                            r_objectives=cur.fetchall()
                        
                            cur.execute('SELECT COUNT(*) FROM d_research_progress WHERE report_id=%s;',(last_report_id,))
                            num_objectives=cur.fetchall()[0][0]
                        else:
                            r_objectives=None
                            num_objectives=0
                            last_report_id=0
                    

                        flash('Your Section D has been not completed yet, please complete your Section B firstly. Please make sure you have discussed with your Supervisors before filling the Section D')
                        return render_template('student/D.html', title='Section D',firstname=firstname,lastname=lastname,r_objectives=r_objectives,num_objectives=num_objectives,last_report_id=last_report_id)

        else:
            flash('You have not been started your report progress, please reading the above clarification, then push the "Start" to start your report!')
            return redirect (url_for('student.MR'))
        

    if request.method == 'POST':
        user_email=session['user_email']
        cur = getCursor()
        cur.execute('SELECT fname, lname FROM student WHERE student_email = %s', (user_email,))
        user_name=cur.fetchone()
        firstname=user_name[0]
        lastname=user_name[1]
        today = date.today()
        if today.month <= 6:
            due_date = date(today.year, 6, 30)
        else:
            due_date = date(today.year, 12, 31)

        cur=getCursor()
        cur.execute('SELECT COUNT(*) FROM report WHERE due_date=%s AND student_email =%s',(due_date,user_email,))
        num_existing1=cur.fetchall()[0][0]
        
        cur.execute('SELECT report_id FROM report WHERE student_email=%s AND due_date=%s;',(user_email,due_date,))
        report_id=cur.fetchone()[0]

        comments = request.form.get('comments')
        contact_person = request.form.get('contact_person')

        if comments =='':
            cur=getCursor()
            cur.execute('UPDATE INTO f_stud_assssment SET comments=%s, talk_to=%s WHERE report_id=%s;',(comments,contact_person,report_id,))
            cur.execute("INSERT INTO progress (report_id,actioner_email,actioner_role,action_date,action_type) VALUES (%s,%s,'PG Student',%s,'F Completed')",(report_id,user_email,today,))
            cur.execute("INSERT INTO progress (report_id,actioner_email,actioner_role,action_date,action_type) VALUES (%s,%s,'PG Student',%s,'Submitted')",(report_id,user_email,today,))
            flash('Thanks for your submittion')
            return render_template('student/SUBMITTION.html', title='Submittion',firstname=firstname,lastname=lastname)
        else:
            cur=getCursor()
            cur.execute("INSERT INTO progress (report_id,actioner_email,actioner_role,action_date,action_type) VALUES (%s,%s,'PG Student',%s,'Submitted')",(report_id,user_email,today,)) 
            flash('Thanks for your submittion')
            return render_template('student/SUBMITTION.html', title='Submittion',firstname=firstname,lastname=lastname)



