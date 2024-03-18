# Name: Zheng Zhao Student ID: 1153313#

from distutils.util import execute
from flask import Flask
from flask import render_template
from flask import session
from flask import request
from flask import redirect
from flask import url_for
import datetime
import mysql.connector
import connect


connection = None
dbconn = None

app = Flask(__name__)

def getCursor():
    global dbconn
    global connection
    if dbconn == None:
        connection = mysql.connector.connect(user=connect.dbuser, \
        password=connect.dbpass, host=connect.dbhost, \
        database=connect.dbname, autocommit=True)
        dbconn = connection.cursor()
        return dbconn
    else:
        return dbconn

def datenow():
    currentdate=datetime.datetime(2022,10,28).strftime('%Y-%m-%d')
    return currentdate

@app.route("/")
def home():
    return render_template("main.html")

@app.route("/airportlist")
def airport(): #display a list of available airports, customer can select one from the list#
    cur = getCursor()
    cur.execute("SELECT AirportCode, AirportName FROM airport;")
    select_result = cur.fetchall()
    column_names = [desc[0] for desc in cur.description]
    print(f"{column_names}")
    return render_template('airportlist.html',dbresult=select_result,dbcols=column_names)

#Below， these code will display for all departure and arrival flight in same page with selected airport#
@app.route('/airportlist/arrivalsDepartures', methods=['GET'])
def getOrder():
    print(request.args)
    Arrcode = request.args.get("ArrCode")
    currentdate=datenow()
    print(Arrcode)
    cur = getCursor()
    cur.execute("SELECT FlightID, f.FlightNum, a.AirportCode as Depcode, \
            a.AirportName AS DepAirport, FlightDate, DepTime, ArrTime, DepEstAct, ArrEstAct, FlightStatus\
            FROM airport AS a JOIN route AS r JOIN flight AS f ON a.AirportCode = r.DepCode\
                AND r.FlightNum = f.FlightNum WHERE ArrCode = %s AND FlightDate \
                    between DATE_ADD(%s, INTERVAL -2 DAY) AND date_add(%s, interval 5 day) order by f.FlightID;",(Arrcode,currentdate,currentdate,))
    select_result = cur.fetchall()
    column_names = [desc[0] for desc in cur.description]
    print(f"{column_names}")

    
    Depcode = request.args.get("ArrCode")
    print(Depcode)
    cur = getCursor()
    cur.execute("SELECT f.FlightID, f.FlightNum, a.AirportCode as Arrcode, a.AirportName AS ArrAirport,\
            FlightDate, DepTime, ArrTime, DepEstAct, ArrEstAct, FlightStatus \
                FROM airport AS a JOIN route AS r JOIN flight AS f\
             ON a.AirportCode = r.ArrCode AND r.FlightNum = f.FlightNum \
                WHERE DepCode = %s AND FlightDate BETWEEN DATE_ADD(%s, INTERVAL -2 DAY) AND date_add(%s, interval 5 day) order by f.FlightID;",(Depcode,currentdate,currentdate,))
    select_results = cur.fetchall()
    column_namess = [desc[0] for desc in cur.description]
    print(f"{column_namess}")
    return render_template('arrivalsDepartures.html',dbresult=select_result,dbcols=column_names, dbresults=select_results,dbcolss=column_namess)

@app.route("/booking")
def booking():
    return render_template("customerlogin.html")

@app.route("/customerlogin", methods=['POST'])
def customerlogin():
    print(request.form)
    email=request.form.get('username')
    cur = getCursor()
    cur.execute("SELECT count(*) FROM passenger WHERE EmailAddress = %s;", (email,))
    number=cur.fetchall()
    number=number[0][0]
    if number > 0:
        cur = getCursor()
        cur.execute("SELECT * FROM passenger WHERE EmailAddress = %s;", (email,))
        customerdetails =cur.fetchall()
        column_names=[desc[0] for desc in cur.description]
        print(f"{column_names}")
        currentdate=datenow()
        
        cur = getCursor()
        cur.execute("SELECT f.FlightID, p.PassengerID, FlightDate, AirportName AS DepAirport, r.ArrCode AS ArrAirport, DepEstAct AS Deptime,\
             ArrEstAct AS Arrtime, FlightStatus FROM passenger AS p JOIN passengerFlight AS pf JOIN flight AS f \
                JOIN route AS r JOIN airport AS a ON  p.PassengerID = pf.PassengerID AND pf.FlightID = f.FlightID \
                    AND f.FlightNum=r.FlightNum AND r.DepCode= a.AirportCode WHERE EmailAddress =%s AND\
                         FlightDate > %s order by f.FlightID;", (email,currentdate,))
        customerdetailss =cur.fetchall()
        column_namess=[desc[0] for desc in cur.description]
        print(f"{column_namess}")
        return render_template('customerform.html', dbresult=customerdetails,dbcols=column_names,dbresults=customerdetailss,dbcolss=column_namess)
    
    else:
        msg="Incorrect username. If you are a new customer, please register now"
        return render_template('customerlogin.html', Message=msg)  

@app.route("/logout")
def logout():
    return render_template("customerlogin.html")

@app.route("/register")
def register():
    return render_template("register.html")
    
@app.route("/register/form",methods=['GET','POST'])
def registerform():
    if request.method == 'POST':
        print(request.form)
        firstname = request.form.get('firstname').capitalize()
        lastname = request.form.get('lastname').capitalize()
        email = request.form.get('email')
        phone = request.form.get('phone')
        passport = request.form.get('passport')
        birthdate = request.form.get('birthdate')
        cur = getCursor()
        cur.execute("SELECT count(*) FROM passenger WHERE EmailAddress =%s and PassportNumber=%s;",(email,passport,))

        number=cur.fetchall()
        number=number[0][0]
        if number < 1:
            cur = getCursor()
            cur.execute("INSERT INTO passenger(FirstName, LastName, EmailAddress,PhoneNumber,PassportNumber,DateOfBirth)\
                VALUES (%s,%s,%s,%s,%s,%s);",(firstname,lastname,email,phone,passport,birthdate,))
            cur.execute("SELECT * FROM passenger where EmailAddress = %s",(email,))
            select_result = cur.fetchall()
            column_names = [desc[0] for desc in cur.description]
            return render_template('customerform.html',dbresult=select_result,dbcols=column_names)
        else:
            msg="This email has been registered!"
            return render_template('register.html', Message=msg) 
    else:
        return render_template('register.html')

    
@app.route("/customerlogin/update",methods=['GET'])
def update():
    print(request.args)
    passengerid = request.args.get("PassengerID")
    return render_template("update.html", passengerid=passengerid)

@app.route("/customerlogin/update/form",methods=['GET','POST'])
def updateform():
    print(request.form)
    passengerid= request.form.get('passengerid')
    firstname = request.form.get('firstname').capitalize()
    lastname = request.form.get('lastname').capitalize()
    email = request.form.get('email')
    phone = request.form.get('phone')
    passport = request.form.get('passport')
    birthdate = request.form.get('birthdate')

    cur = getCursor()
    cur.execute("UPDATE passenger SET FirstName=%s, LastName=%s, EmailAddress=%s,PhoneNumber=%s,PassportNumber=%s,\
        DateOfBirth=%s WHERE PassengerID=%s;",(firstname,lastname,email,phone,passport,birthdate,passengerid ))
    cur.execute("SELECT * FROM passenger WHERE PassengerID = %s;", (passengerid, ))
    select_result = cur.fetchall()
    column_names = [desc[0] for desc in cur.description]
    

    print(request.form)
    passengerid= request.form.get('passengerid')
    email = request.form.get('email')
    currentdate=datenow()
    cur.execute("SELECT f.FlightID, p.PassengerID, FlightDate, AirportName AS DepAirport, r.ArrCode AS ArrAirport, DepEstAct AS Deptime,\
             ArrEstAct AS Arrtime, FlightStatus FROM passenger AS p JOIN passengerFlight AS pf JOIN flight AS f \
                JOIN route AS r JOIN airport AS a ON  p.PassengerID = pf.PassengerID AND pf.FlightID = f.FlightID \
                    AND f.FlightNum=r.FlightNum AND r.DepCode= a.AirportCode WHERE EmailAddress = %s AND\
                         FlightDate > %s order by f.FlightID;",(email,currentdate,))
    customerdetailss =cur.fetchall()
    column_namess=[desc[0] for desc in cur.description]
    
    return render_template('customerform.html',dbresult=select_result,dbcols=column_names,dbresults=customerdetailss,dbcolss=column_namess)

@app.route("/customerlogin/cancel",methods=['GET'])
def cancel():
    print(request.args)
    flightid = request.args.get("FlightID")
    return render_template("cancelconfirmation.html", flight_id=flightid)

@app.route("/customerlogin/cancel/confirm",methods=['GET','POST'])
def cancelconfirm():
    print(request.form)
    flightid=request.form.get("flight_id")
    passengerid=request.form.get("passengerid")
    email=request.form.get("email")
    currentdate=datenow()
    cur = getCursor()
    cur.execute("DELETE FROM passengerFlight WHERE PassengerID=%s AND FlightID=%s;",(passengerid,flightid, ))
    cur.execute("SELECT * FROM passenger WHERE PassengerID = %s;", (passengerid,))
    customerdetails =cur.fetchall()
    column_names=[desc[0] for desc in cur.description]

    cur = getCursor()
    cur.execute("SELECT f.FlightID, p.PassengerID, FlightDate, AirportName AS DepAirport, r.ArrCode AS ArrAirport, DepEstAct AS Deptime,\
             ArrEstAct AS Arrtime, FlightStatus FROM passenger AS p JOIN passengerFlight AS pf JOIN flight AS f \
                JOIN route AS r JOIN airport AS a ON  p.PassengerID = pf.PassengerID AND pf.FlightID = f.FlightID \
                    AND f.FlightNum=r.FlightNum AND r.DepCode= a.AirportCode WHERE EmailAddress=%s AND\
                         FlightDate > %s order by f.FlightID;",(email,currentdate,))

    customerdetailss =cur.fetchall()
    column_namess=[desc[0] for desc in cur.description]
    
    return render_template('customerform.html',dbresult=customerdetails,dbcols=column_names,dbresults=customerdetailss,dbcolss=column_namess)


# add a new booking from customer information form after customer logins#
@app.route("/addbooking")
def addbooking():
    cur = getCursor()
    cur.execute("SELECT AirportCode, AirportName FROM Airport;")
    select_result = cur.fetchall()
    column_names = [desc[0] for desc in cur.description]
    print(f"{column_names}")
    return render_template('bookingairportlist.html',dbresult=select_result,dbcols=column_names)

@app.route("/addbooking/airport",methods=['GET'])
def selectairport():
    print(request.args)
    depcode=request.args.get("DepCode")
    currentdate=datenow()
    cur = getCursor()
    cur.execute("SELECT f.FlightID,f.FlightNum,a.AirportName AS ArrAirport, f.FlightDate,\
         f.DepEstAct AS Deptime, f.ArrEstAct AS Arrtime, f.Duration,f.FlightStatus \
            FROM airport AS a JOIN route AS r JOIN flight AS f JOIN aircraft as af \
                ON r.ArrCode=a.AirportCode AND r.FlightNum = f.FlightNum AND f.Aircraft = af.RegMark\
                     WHERE f.FlightDate between %s AND date_add(%s, interval 7 day)\
                         and r.DepCode=%s;",(currentdate,currentdate,depcode,))
    
    select_result = cur.fetchall()
    print(select_result)
    column_names = [desc[0] for desc in cur.description]
    print(f"{column_names}")
    return render_template('flightlist.html',dbresult=select_result,dbcols=column_names)

@app.route("/addbooking/airport/booking",methods=['GET'])
def Seatavailable():
    print(request.args)
    flightid=request.args.get("FlightID")
    
    cur = getCursor()
    cur.execute("SELECT p.FlightID, (SELECT distinct (af.Seating-(SELECT count(*) FROM airport AS a JOIN route AS r\
         JOIN flight AS f JOIN aircraft as af JOIN passengerflight AS p ON r.ArrCode=a.AirportCode\
             AND r.FlightNum = f.FlightNum AND f.Aircraft = af.RegMark AND f.FlightID = p.FlightID\
                 WHERE p.FlightID=%s))) as AvailableSeats FROM airport AS a JOIN route AS r\
                     JOIN flight AS f JOIN aircraft as af  JOIN passengerflight AS p ON r.ArrCode=a.AirportCode\
                         AND r.FlightNum = f.FlightNum AND f.Aircraft = af.RegMark AND f.FlightID = p.FlightID\
                             WHERE p.FlightID=%s;",(flightid,flightid,))
    
    select_result = cur.fetchone()
    column_names = [desc[0] for desc in cur.description]
    print(f"{column_names}")
    return render_template('availableseat.html',results=select_result,dbcols=column_names)
    
@app.route("/addbooking/airport/booking/makeabook",methods=['POST','GET'])
def startabooking():
    print(request.form)
    
    flightid=request.form.get('flightid')
    print(flightid)

    passengerid=request.form.get('passengerid')
   
    print(passengerid)
    currentdate=datenow()
    
    cur = getCursor()

    cur.execute("INSERT INTO passengerflight(FlightID,PassengerID) VALUES(%s,(SELECT PassengerID from passenger WHERE PassengerID = %s));",(flightid,passengerid))

    # resutl=cur.fetchall()
    # print(resutl)

    cur = getCursor()
    cur.execute("SELECT f.FlightID, p.PassengerID, FlightDate, AirportName AS DepAirport, r.ArrCode AS ArrAirport, DepEstAct AS Deptime,\
             ArrEstAct AS Arrtime, FlightStatus FROM passenger AS p JOIN passengerFlight AS pf JOIN flight AS f \
                JOIN route AS r JOIN airport AS a ON  p.PassengerID = pf.PassengerID AND pf.FlightID = f.FlightID \
                    AND f.FlightNum=r.FlightNum AND r.DepCode= a.AirportCode WHERE p.PassengerID = %s AND\
                         FlightDate > %s order by f.FlightID;",(passengerid,currentdate,))
    customerdetailss =cur.fetchall()
    column_namess=[desc[0] for desc in cur.description]
    return render_template('customerform.html',dbresult=customerdetailss,dbcols=column_namess)

    
    











# the staff system start from below#

@app.route("/admin")
def admin():
    cur = getCursor()
    cur.execute("SELECT StaffID, CONCAT(FirstName, LastName) AS StaffName, IsManager FROM staff;")
    select_result = cur.fetchall()
    column_names = [desc[0] for desc in cur.description]
    print(f"{column_names}")
    return render_template('admin.html',dbresult=select_result,dbcols=column_names)

@app.route("/admin/stafflogin", methods=['POST'])
def stafflogin():
    print(request.form)
    staffid=request.form.get("staffid")
    staffid=staffid[0][0]
    cur = getCursor()
    cur.execute("SELECT IsManager FROM staff WHERE StaffID = %s;",(staffid,))
    ismanager=cur.fetchall()
    ismanager=ismanager[0][0]
    cur = getCursor()
    cur.execute("SELECT FirstName FROM staff WHERE StaffID = %s;",(staffid,))
    firstname=cur.fetchall()
    firstname=firstname[0][0]
    
    return render_template("staffsystem.html",firstname=firstname,ismanager=ismanager)
    
###########################
@app.route("/admin/stafflogin/passengers")
def passengers():
    cur = getCursor()
    cur.execute("SELECT LastName, FirstName, PassengerID, EmailAddress, PhoneNumber,\
        PassportNumber,DateOfBirth,LoyaltyTier FROM passenger  order by LastName,FirstName;")
    select_result = cur.fetchall()
    column_names = [desc[0] for desc in cur.description]
    return render_template('passengerslist.html',dbresult=select_result,dbcols=column_names)

@app.route("/admin/stafflogin/passengers/search", methods=['POST'])
def search():
    print(request.form)
    lastname=request.form.get("lastname")
    lastname=lastname.capitalize()
    cur = getCursor()
    cur.execute("SELECT LastName, FirstName, PassengerID, EmailAddress, PhoneNumber,\
        PassportNumber,DateOfBirth,LoyaltyTier FROM passenger WHERE LastName =%s \
            order by LastName,FirstName;",(lastname,))
    select_result = cur.fetchall()
    column_names = [desc[0] for desc in cur.description]
    return render_template('passengerslist.html',dbresult=select_result,dbcols=column_names)

@app.route("/admin/stafflogin/passengers/search/edit", methods=['GET'])
def staffedit():
    print(request.args)
    email=request.args.get('EmailAddress')
    cur = getCursor()
    cur.execute("SELECT * FROM passenger WHERE EmailAddress = %s;", (email,))
    customerdetails =cur.fetchall()
    column_names=[desc[0] for desc in cur.description]
    print(f"{column_names}")
    currentdate=datenow()
        
    cur = getCursor()
    cur.execute("SELECT f.FlightID, p.PassengerID, FlightDate, AirportName AS DepAirport, r.ArrCode AS ArrAirport, DepEstAct AS Deptime,\
             ArrEstAct AS Arrtime, FlightStatus FROM passenger AS p JOIN passengerFlight AS pf JOIN flight AS f \
                JOIN route AS r JOIN airport AS a ON  p.PassengerID = pf.PassengerID AND pf.FlightID = f.FlightID \
                    AND f.FlightNum=r.FlightNum AND r.DepCode= a.AirportCode WHERE EmailAddress =%s and FlightDate > %s \
                        order by f.FlightID;", (email,currentdate,))
    customerdetailss =cur.fetchall()
    column_namess=[desc[0] for desc in cur.description]
    print(f"{column_namess}")
    return render_template('customerform.html', dbresult=customerdetails,dbcols=column_names,dbresults=customerdetailss,dbcolss=column_namess)


@app.route("/admin/stafflogin/allflights")
def admin_flights():
    currentdate=datenow()
    cur = getCursor()
    cur.execute("SELECT f.FlightID,f.FlightNum,r.DepCode, r.ArrCode, f.FlightDate, f.DepEstAct AS Deptime,\
         f.ArrEstAct AS Arrtime, f.Duration,f.FlightStatus, (af.Seating-b.BookedSeats) AS AvailableSeats\
         FROM airport AS a JOIN route AS r JOIN flight AS f JOIN aircraft as af JOIN passengerflight AS p JOIN\
             (SELECT FlightID, COUNT(*) AS BookedSeats  FROM passengerflight GROUP BY FlightID) AS b\
             ON r.ArrCode=a.AirportCode AND r.FlightNum = f.FlightNum AND f.Aircraft = af.RegMark AND\
                 f.FlightID = p.FlightID AND f.FlightID=b.FlightID WHERE f.FlightDate BETWEEN %s AND\
                     DATE_ADD(%s, INTERVAL 7 DAY) GROUP BY f.FlightID ORDER BY f.FlightID;", (currentdate,currentdate,))
    
    select_result = cur.fetchall()
    print(select_result)
    column_names = [desc[0] for desc in cur.description]
    cur = getCursor()
    cur.execute("SELECT AirportCode FROM airport")
    airportcodes=cur.fetchall()
    print(airportcodes)

    cur = getCursor()
    cur.execute("SELECT FlightStatus FROM status")
    statuss=cur.fetchall()
    print(statuss)

    return render_template('admin_flights.html',dbresult=select_result,dbcols=column_names,airportcodes=airportcodes,statuss=statuss)

@app.route("/admin/stafflogin/allflights/search",methods=['POST'])
def admin_flights_search():
    print(request.form)
    datefrom=request.form.get('datefrom')
    dateto=request.form.get('dateto')
    depcode=request.form.get('depairport')
    arrcode=request.form.get('arrairport')
    
    if datefrom !='' and dateto !='':
        cur = getCursor()
        cur.execute("SELECT f.FlightID,f.FlightNum,r.DepCode, r.ArrCode, f.FlightDate, f.DepEstAct AS Deptime, f.ArrEstAct AS Arrtime, f.Duration,f.FlightStatus, (af.Seating-b.BookedSeats) AS AvailableSeats\
         FROM airport AS a JOIN route AS r JOIN flight AS f JOIN aircraft as af JOIN passengerflight AS p JOIN (SELECT FlightID, COUNT(*) AS BookedSeats  FROM passengerflight group by FlightID) AS b\
             ON r.ArrCode=a.AirportCode AND r.FlightNum = f.FlightNum AND f.Aircraft = af.RegMark AND f.FlightID = p.FlightID AND f.FlightID=b.FlightID\
                 WHERE f.FlightDate BETWEEN %s AND %s AND r.DepCode=%s AND r.ArrCode=%s GROUP BY\
                     f.FlightID ORDER BY f.FlightID;", (datefrom,dateto,depcode,arrcode,))
    
        select_result = cur.fetchall()
        print(select_result)
        column_names = [desc[0] for desc in cur.description]
        cur = getCursor()
        cur.execute("SELECT AirportCode FROM airport")
        airportcodes=cur.fetchall()
        print(airportcodes)
        return render_template('admin_flights.html',dbresult=select_result,dbcols=column_names,airportcodes=airportcodes)
    
    else:
        return redirect("/admin/stafflogin/allflights")

@app.route("/admin/stafflogin/allflights/manifest", methods=['GET'])
def manifest():
    print(request.args)
    flightid=request.args.get('FlightID')
    cur=getCursor()
    cur.execute("SELECT p.PassengerID,p.EmailAddress,p.LastName, p.FirstName FROM passenger as p JOIN passengerflight as pf\
         ON p.PassengerID=pf.PassengerID WHERE pf.FlightID=%s ORDER BY p.LastName,p.FirstName;",(flightid,))
    select_result = cur.fetchall()
    print(select_result)
    column_names = [desc[0] for desc in cur.description]
    cur = getCursor()
    cur.execute("SELECT COUNT(*) FROM passenger as p JOIN passengerflight as pf ON\
         p.PassengerID=pf.PassengerID WHERE pf.FlightID=%s;",(flightid,))
    number=cur.fetchall()
    number=number[0][0]
   

    cur=getCursor()
    cur.execute("SELECT f.FlightNum,af.RegMark,af.Manufacturer,af.Model,af.Seating as SeatingCapacity FROM flight as f JOIN aircraft as\
         af on f.Aircraft=af.RegMark WHERE FlightID=%s",(flightid,))
    dbresulta=getCursor()
    dbcolsa = [desc[0] for desc in cur.description]
    return render_template('admin_manifest.html',dbresulta=dbresulta,dbcolsa=dbcolsa,dbresult=select_result,dbcols=column_names,number=number,flightid=flightid)

@app.route("/admin/stafflogin/allflights/updates", methods=['POST'])
def admin_staff_flight_updates():
    print(request.form)
    flightid=request.form.get('flightid')
    deptime=request.form.get('deptime')
    arrtime=request.form.get('arrtime')
    status=request.form.get('status')
    if status=='Cancelled': 
        cur=getCursor()
        cur.execute("UPDATE flight SET DepEstAct = NULL, ArrEstAct= NULL ,FlightStatus=%s WHERE FlightID=%s", (status,flightid,))
        cur.execute("select * from flight WHERE FlightID=%s",(flightid,))
        select_result = cur.fetchall()
        column_names = [desc[0] for desc in cur.description]
        cur = getCursor()
        cur.execute("SELECT FlightStatus FROM status")
        statuss=cur.fetchall()
        print(statuss)
        return render_template('admin_flights_NULL.html',dbresult=select_result,dbcols=column_names,statuss=statuss)
        
    else:
        cur=getCursor()
        cur.execute("UPDATE flight SET DepEstAct=%s, ArrEstAct=%s,FlightStatus=%s WHERE FlightID=%s", (deptime,arrtime,status,flightid,))
        cur.execute("select * from flight WHERE FlightID=%s",(flightid,))
    
        select_result = cur.fetchall()
        column_names = [desc[0] for desc in cur.description]
        cur = getCursor()
        cur.execute("SELECT FlightStatus FROM status")
        statuss=cur.fetchall()
        return render_template('admin_flights.html',dbresult=select_result,dbcols=column_names,statuss=statuss)








#below all fpr the management level permission#
@app.route("/manager/addflights")
def manager_addflights():
    cur=getCursor()
    cur.execute("INSERT INTO flight(FlightNum, WeekNum, FlightDate, DepTime, ArrTime, Duration, DepEstAct, ArrEstAct, FlightStatus, Aircraft)\
         SELECT FlightNum, WeekNum+1, date_add(FlightDate, interval 7 day), DepTime, ArrTime, Duration, DepTime, ArrTime, 'On time', Aircraft\
             FROM flight WHERE WeekNum = (SELECT MAX(WeekNum) FROM flight)")
    cur.execute("SELECT * FROM flight")
    select_result = cur.fetchall()
    column_names = [desc[0] for desc in cur.description]
    print(f"{column_names}")
    return render_template('admin_addflights.html',dbresult=select_result,dbcols=column_names)

@app.route("/manager/addflights/search", methods=['POST'])
def manager_search():
    print(request.form)
    weeknum=request.form.get('weeknum')
    cur=getCursor()
    cur.execute("SELECT * FROM flight WHERE WeekNum=%s",(weeknum,))
    select_result = cur.fetchall()
    column_names = [desc[0] for desc in cur.description]
    print(f"{column_names}")
    return render_template('admin_addflights.html',dbresult=select_result,dbcols=column_names)

@app.route("/manager/add")
def manager_add():
    cur=getCursor()
    cur.execute("SELECT RegMark FROM aircraft")
    select_result = cur.fetchall()

    return render_template("admin_addsingleflight.html", aircrafts=select_result)

@app.route("/manager/add/aflight", methods=['POST'])
def manager_add_a_flight():
    print(request.form)
    flightnum=request.form.get('flightnum')
    weeknum=request.form.get('WeekNum')
    flightdate=request.form.get('flightdate')
    deptime=request.form.get('deptime')
    arrtime=request.form.get('arrtime')
    aircraft=request.form.get('aircraft')
    cur=getCursor()
    cur.execute("INSERT INTO flight(FlightNum,WeekNum,FlightDate,DepTime,Arrtime,Duration,DepEstAct,\
        ArrEstAct,FlightStatus,Aircraft) VALUES (%s,%s,%s,%s,%s,TIMEDIFF(%s,%s),%s,%s,%s,%s)", (flightnum,weeknum,flightdate,deptime,arrtime,arrtime,deptime,deptime,arrtime,'On time', aircraft))
    currentdate=datenow()
    cur = getCursor()
    cur.execute("SELECT f.FlightID,f.FlightNum,r.DepCode, r.ArrCode, f.FlightDate, f.DepEstAct AS Deptime, f.ArrEstAct AS Arrtime, f.Duration,f.FlightStatus, (af.Seating-b.BookedSeats) AS AvailableSeats\
         FROM airport AS a JOIN route AS r JOIN flight AS f JOIN aircraft as af JOIN passengerflight AS p JOIN (SELECT FlightID, COUNT(*) AS BookedSeats  FROM passengerflight group by FlightID) AS b\
             ON r.ArrCode=a.AirportCode AND r.FlightNum = f.FlightNum AND f.Aircraft = af.RegMark AND f.FlightID = p.FlightID AND f.FlightID=b.FlightID\
                 WHERE f.FlightDate > %s AND date_add(%s, interval 7 day) GROUP BY f.FlightID ORDER BY f.FlightID;", (currentdate,currentdate,))
    
    select_result = cur.fetchall()
    print(select_result)
    column_names = [desc[0] for desc in cur.description]


    cur = getCursor()
    cur.execute("SELECT FlightStatus FROM status")
    statuss=cur.fetchall()

    cur=getCursor()
    cur.execute("SELECT RegMark FROM aircraft")
    regmarks = cur.fetchall()
    return render_template('admin_manager_flights.html',dbresult=select_result,dbcols=column_names,statuss=statuss,regmarks=regmarks)


@app.route("/admin/manager_update_a_flight", methods=['POST'])
def manager_update():
    flightid=request.form.get('flightid')
    deptime=request.form.get('deptime')
    arrtime=request.form.get('arrtime')
    status=request.form.get('status')
    regmark=request.form.get('regmark')
    if status=='Cancelled': 
        cur=getCursor()
        cur.execute("UPDATE flight SET DepEstAct = NULL, ArrEstAct= NULL ,FlightStatus=%s, Aircraft=%s WHERE FlightID=%s", (status,regmark,flightid,))
        cur.execute("select * from flight WHERE FlightID=%s",(flightid,))
        select_result = cur.fetchall()
        column_names = [desc[0] for desc in cur.description]
        cur = getCursor()
        cur.execute("SELECT FlightStatus FROM status")
        statuss=cur.fetchall()
        print(statuss)
        cur=getCursor()
        cur.execute("SELECT RegMark FROM aircraft")
        regmarks = cur.fetchall()
        return render_template('admin_manager_flights.html',dbresult=select_result,dbcols=column_names,statuss=statuss,regmarks=regmarks)
        
    else:
        cur=getCursor()
        cur.execute("UPDATE flight SET DepEstAct=%s, ArrEstAct=%s,FlightStatus=%s, Aircraft=%s WHERE FlightID=%s", (deptime,arrtime,status,regmark,flightid,))
        cur.execute("select * from flight WHERE FlightID=%s",(flightid,))
    
        select_result = cur.fetchall()
        column_names = [desc[0] for desc in cur.description]
        cur = getCursor()
        cur.execute("SELECT FlightStatus FROM status")
        statuss=cur.fetchall()
        cur=getCursor()
        cur.execute("SELECT RegMark FROM aircraft")
        regmarks = cur.fetchall()
        return render_template('admin_manager_flights.html',dbresult=select_result,dbcols=column_names,statuss=statuss,regmarks=regmarks)








    