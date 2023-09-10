from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
import re
from datetime import datetime
import mysql.connector
from mysql.connector import FieldType
import connect
# git push
app = Flask(__name__)

dbconn = None
connection = None

def getCursor():
    global dbconn
    global connection
    connection = mysql.connector.connect(user=connect.dbuser, \
    password=connect.dbpass, host=connect.dbhost, \
    database=connect.dbname, autocommit=True)
    dbconn = connection.cursor()
    return dbconn

@app.route("/")
def home():
    return render_template("borrower_search_interface.html")


@app.route("/staff")
def staffinterface():
    return render_template("staffsearchinterface.html")


@app.route("/searchbook", methods=["post"])
def searchbook():
    searchterm1 = request.form.get('Ftitle')
    if searchterm1 !='':
        searchterm1 = "%" + searchterm1 + "%"
        connection1 = getCursor()
        connection1.execute("SELECT bc.bookcopyid, bc.format, b.booktitle, b.author, l.loandate, l.returned,\
                       adddate(loandate,interval 28 day) AS daysdueback \
                       FROM bookcopies bc left join books b on bc.bookid=b.bookid \
                        left join loans l on bc.bookcopyid=l.bookcopyid WHERE b.booktitle LIKE %s;",(searchterm1,))
        pool_for_search1 = connection1.fetchall()
    else:
          pool_for_search1=False

    searchterm2 = request.form.get('Fauthor')
    if searchterm2 !='':
        searchterm2 = "%" + searchterm2 + "%"     
        connection2 = getCursor()                   
        connection2.execute("SELECT bc.bookcopyid, bc.format, b.booktitle, b.author, l.loandate, l.returned,\
                       adddate(loandate,interval 28 day) AS daysdueback \
                       FROM bookcopies bc left join books b on bc.bookid=b.bookid \
                        left join loans l on bc.bookcopyid=l.bookcopyid WHERE b.author LIKE %s;",(searchterm2,))
        pool_for_search2 = connection2.fetchall()

    else:
          pool_for_search2=False

    return render_template("listbooksearch.html", pool_for_search1 = pool_for_search1, pool_for_search2 = pool_for_search2) 



@app.route("/listborrower")
def listborrower():
    connection = getCursor()
    connection.execute("SELECT * FROM borrowers;")
    borrowerList = connection.fetchall()
    return render_template("borrowerlist.html", borrowerlist = borrowerList)

@app.route("/editborrower")
def editborrower():
    connection = getCursor()
    connection.execute("SELECT * FROM borrowers;")
    borrowerList = connection.fetchall()
    return render_template("borroweredit.html", borrowerlist = borrowerList)



@app.route("/edit/borrowerdetail",methods=["post"])
def borrowerdetailsubmit():
    borrowerid = request.form.get('borrower')
    borrowerfname = request.form.get('fname')
    borrowerlname = request.form.get('lname')
    birthdate = request.form.get('birthdate')
    housenumber = request.form.get('housenumber')
    postalcode = request.form.get('postal')
    street = request.form.get('street')
    town = request.form.get('town')
    city = request.form.get('city')
    cur = getCursor()
    cur.execute("UPDATE borrowers SET firstname=%s, familyname=%s, dateofbirth=%s, housenumbername=%s,street=%s,town=%s,city=%s,postalcode=%s WHERE borrowerid= %s;",(borrowerfname, borrowerlname, birthdate,housenumber,street,town,city,postalcode,borrowerid))
    return redirect("/listborrower/updated")


@app.route("/addborrower")
def addborrower():
    connection = getCursor()
    connection.execute("SELECT * FROM borrowers;")
    borrowerList = connection.fetchall()
    return render_template("addborrower.html", borrowerlist = borrowerList)


@app.route("/borrower/add",methods=["post"])
def borroweradd():
    borrowerfname = request.form.get('fname')
    borrowerlname = request.form.get('lname')
    birthdate = request.form.get('birthdate')
    housenumber = request.form.get('housenumber')
    postalcode = request.form.get('postal')
    street = request.form.get('street')
    town = request.form.get('town')
    city = request.form.get('city')
    cur = getCursor()
    cur.execute("INSERT INTO borrowers (firstname, familyname, dateofbirth, housenumbername,street,town,city,postalcode) VALUES (%s, %s, %s, %s,%s,%s,%s,%s);",(borrowerfname, borrowerlname, birthdate,housenumber,street,town,city,postalcode))
    return redirect("/listborrower/updated")



@app.route("/listborrower/updated")
def updatedlistborrower():
    connection = getCursor()
    connection.execute("SELECT * FROM borrowers;")
    borrowerList = connection.fetchall()
    return render_template("borrower_search-_result.html", borrowerlist = borrowerList)




@app.route("/searchborrower", methods=["post"])
def searchborrower():
    searchterm = request.form.get('borrowersearch')
    searchterm = "%" + searchterm + "%"
    connection = getCursor()
    connection.execute("SELECT * FROM borrowers WHERE borrowerid LIKE %s OR firstname LIKE %s OR familyname LIKE %s;",(searchterm,searchterm,searchterm))
    borrowersearch = connection.fetchall()

    return render_template("borrower_search-_result.html", borrowerlist=borrowersearch)



@app.route("/issuebook")
def issuebook():
    todaydate = datetime.now().date()
    connection = getCursor()
    connection.execute("SELECT * FROM borrowers;")
    borrowerList = connection.fetchall()
    sql = """SELECT * FROM bookcopies
inner join books on books.bookid = bookcopies.bookid
 WHERE bookcopyid not in (SELECT bookcopyid from loans where returned <> 1 or returned is NULL) 
 or bookcopyid not in (SELECT bookcopyid from bookcopies where format <> 'eBook' and format <> 'Audio Book');"""
    connection.execute(sql)
    bookList = connection.fetchall()
    return render_template("issuebook.html", loandate = todaydate,borrowers = borrowerList, books= bookList)



@app.route("/book/issue", methods=["POST"])
def bookissue():
    bookidcopy = request.form.get('bookcopyid')
    borrowerid = request.form.get('borrower')
    loandate = request.form.get('loandate')
    cur = getCursor()
    cur.execute("INSERT INTO loans (borrowerid, bookcopyid, loandate, returned) VALUES(%s,%s,%s,0);",(borrowerid, bookidcopy, str(loandate),))
    return redirect("/currentloans")


@app.route("/currentloans")
def currentloans():
    connection = getCursor()
    sql=""" select br.borrowerid, br.firstname, br.familyname,  
                l.borrowerid, l.bookcopyid, l.loandate, l.returned, b.bookid, b.booktitle, b.author, 
                b.category, b.yearofpublication, bc.format 
            from books b
                inner join bookcopies bc on b.bookid = bc.bookid
                    inner join loans l on bc.bookcopyid = l.bookcopyid
                        inner join borrowers br on l.borrowerid = br.borrowerid
            order by br.familyname, br.firstname, l.loandate;"""
    connection.execute(sql)
    loanList = connection.fetchall()
    return render_template("currentloans.html", loanlist = loanList)




@app.route("/returnbook")
def returnbook():
    connection = getCursor()
    connection.execute("select * from loans where returned=0 order by bookcopyid;")
    loanList = connection.fetchall()
    return render_template("returnbook.html", books= loanList)



@app.route("/book/return", methods=["POST"])
def bookreturn():
    nloanid = request.form.get('bookcopyid')
    cur = getCursor()
    cur.execute("UPDATE loans SET returned = 1 WHERE loanid =%s;",(nloanid,))
    return redirect("/currentloans")



@app.route("/overduereport")
def overduereport():
    connection = getCursor()
    sql=""" select br.firstname, br.familyname, L.borrowerid, bc.bookcopyid, L.loandate, bk.booktitle, bc.format, datediff(curdate(),loandate) AS daysonloan from loans AS L 
    inner join borrowers AS br on L.borrowerid=br.borrowerid 
    inner join bookcopies AS bc on bc.bookcopyid=L.bookcopyid 
    inner join books AS bk on bk.bookid=bc.bookid where datediff(curdate(),loandate)>35 and L.returned=0 order by L.borrowerid"""
    connection.execute(sql)
    loanList = connection.fetchall()
    return render_template("overduereport.html", loanlist = loanList)


@app.route("/loansummaryreport")
def loansummaryreport():
    connection = getCursor()
    sql=""" SELECT bk.booktitle, count(l.bookcopyid) AS loantimes FROM loans l inner join  bookcopies bc on l.bookcopyid=bc.bookcopyid
         inner join books bk on bc.bookid=bk.bookid GROUP BY bk.booktitle ORDER BY count(l.bookcopyid) DESC;"""
    connection.execute(sql)
    loanList = connection.fetchall()
    return render_template("loansummaryreport.html", loanlist = loanList)


@app.route("/borrowersummaryreport")
def borrowersummaryreport():
    connection = getCursor()
    sql="""SELECT br.borrowerid, br.firstname, br.familyname, count(l.bookcopyid) AS loantimes FROM loans l inner join  borrowers br on l.borrowerid=br.borrowerid
          GROUP BY br.borrowerid ORDER BY count(l.bookcopyid) DESC;"""
    connection.execute(sql)
    loanList = connection.fetchall()
    return render_template("borrowersummaryreport.html", loanlist = loanList)




