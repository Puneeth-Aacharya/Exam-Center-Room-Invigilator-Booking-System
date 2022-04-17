from flask import Flask
from flask import request, jsonify,render_template,request
import json
from flask_admin.contrib.sqla import ModelView
from flask_admin import Admin
import mongoengine as me
from flask_wtf import Form
from wtforms import TextField, IntegerField, TextAreaField, SubmitField, PasswordField
from wtforms import validators, ValidationError
from wtforms.validators import DataRequired,InputRequired,Email
from wtforms.fields.html5 import EmailField
from werkzeug.security import generate_password_hash, check_password_hash
from passlib.hash import pbkdf2_sha256


from flask_mongoengine import MongoEngine

import requests,random

app = Flask(__name__)
app.secret_key = 'development key'


app.config['FLASK_ADMIN_SWATCH']='cerulean'

"""
DB_URI = "<your mongodb atals link>"
app.config["MONGODB_HOST"] = DB_URI
"""
app.config['MONGODB_SETTINGS'] = {
'db': 'INTERNSHIP_PROJECT',
'host': 'localhost',
'port': 27017
}


db = MongoEngine()
db.init_app(app)
admin=Admin(app,name='microblog')



@app.route('/')
def nav():
    return render_template("home.html")

@app.route('/home')
def home():
    return render_template("home.html")

@app.route('/exam_center')
def exam_center():
    return render_template("add.html")

@app.route('/admin_dashboard')
def admin():
    return render_template("admin.html")


class add_exam_center(db.Document):
    center_name = db.StringField(required=True)
    center_id = db.StringField(required=True)
    room_no=db.IntField(required=True)
    address=db.StringField(required=True)
    contatct_no=db.IntField(required=True)


class booking(db.Document):
    center_name=db.StringField()
    center_id=db.StringField()
    room_no=db.StringField()
    address=db.StringField()
    staff_id=db.StringField()
    staff_name=db.StringField()
    staff_ph_no=db.IntField()
    date=db.StringField()
    time=db.StringField()

class staff(db.Document):
    full_name = db.StringField(required=True)
    emp_id = db.StringField(primary_key=True,required=True)
    ph_no=db.IntField(required=True)
    email=db.EmailField()
    address=db.StringField(required=True)
    password=db.StringField()

class booked(db.Document):
    center_name=db.StringField()
    center_id=db.StringField()
    room_no=db.StringField()
    address=db.StringField()
    staff_id=db.StringField()
    staff_name=db.StringField()
    staff_ph_no=db.IntField()
    date=db.StringField()
    time=db.StringField()


class StaffRegisterForm(Form):
    full_name = TextField('Full Name ',[DataRequired()])
    emp_id=TextField('Employee ID',[DataRequired()])
    ph_no=IntegerField('Phone No',[DataRequired()])
    email = EmailField("Email",validators=[InputRequired(),Email("Please enter email")])
    address = TextAreaField("Address", [DataRequired()])
    password = PasswordField('Password', [DataRequired()])
    c_password = PasswordField('Confirm', [DataRequired()])
    submit = SubmitField("Submit")

class LoginForm(Form):
    email = EmailField("Email",validators=[InputRequired(),Email("Please enter email")])
    password=PasswordField('Password',[DataRequired()])
    login=SubmitField("Login")



@app.route('/', methods=['POST'])
def create_record():
    record = json.loads(request.data)
    c = add_exam_center(center_name=record['center_name'],
        center_id=record['center_id'],
        room_no=record['room_no'],
        address=record['address'],
        contatct_no=record['contatct_no'])
    c.save()
    return render_template("admin_success.html",data="Exam center added successfully")


@app.route('/staff_create_record', methods=['POST'])
def staff_create_record():
    record = json.loads(request.data)
    password=record['password']
    c_password=record['c_password']

    staff_data=staff.objects(emp_id=record['emp_id'])
    staff_email=staff.objects(email=record['email'])

    

    if staff_data or staff_email:
        return render_template("error.html",data="Invigilator details already exists")
    else:
        if password==c_password:
            hash_password=pbkdf2_sha256.using(rounds=8000, salt_size=10).hash(record['password'])
            c = staff( full_name=record['full_name'],
                emp_id=record['emp_id'],
                ph_no=record['ph_no'],
                address=record['address'],
                email=record['email'],
                password=hash_password)
        
            c.save()
            return render_template("success.html",data="Invigilator added successfully . Please Login to continue")
        else:
            return render_template("error.html",data="Not a valid credentials")

# ---------------- UPDATE -----------------
@app.route('/update_Exam', methods=['PUT'])
def update_exam():
    record = json.loads(request.data)
    c = add_exam_center.objects(center_id=record['center_id']).first()
    if not c:
        return jsonify({'error': 'data not found'})
    else:
        c.update(center_name=record['center_name'])
        c.update(room_no=record['room_no'])
        c.update(address=record['address'])
    return render_template("admin_success.html",data="Exam center updated successfully")
#----------------------------------
@app.route('/add',methods=['GET','POST'])
def add():

    if request.method=="GET":
        return render_template("add.html")
    else:
        x={"center_name":request.form['center_name'],
        "center_id":request.form['center_id'],
        "room_no":request.form['room_no'],
        "address":request.form['address'],
        "contatct_no":request.form['contatct_no']
        }
        x=json.dumps(x)
        response = requests.post(url="http://127.0.0.1:5000/",data=x)
#------------------------------------------------------------------------
    return render_template("admin_success.html",data="Exam center added successfully")

@app.route('/staff_register', methods = ['GET', 'POST'])
def staff_register():
    form = StaffRegisterForm()
    total_exam_centers=add_exam_center.objects().count({})
    total_staff=staff.objects().count({})

    if total_staff>=total_exam_centers:
        return render_template("error.html",data="Invigilator Registration is Closed !!") 
    else:
        return render_template('staff_add.html', form = form)


@app.route('/staff_add',methods=['GET','POST'])
def staff_add():
    form=StaffRegisterForm(request.form)
    if request.method=="GET":
        return render_template("staff_add.html")
    else:
        x={"full_name":form.full_name.data,
        "ph_no":form.ph_no.data,
        "emp_id":form.emp_id.data,
        "email":form.email.data,
        "password":form.password.data,
        "c_password":form.c_password.data,
        "address":form.address.data
        }
        x=json.dumps(x)
        response = requests.post(url="http://127.0.0.1:5000/staff_create_record",data=x)
#-----------------------------------------------
    return (response.text)



@app.route('/update_exam_center',methods=['GET','POST'])
def update_exam_center():
    if request.method=="GET":
        return render_template("update_exam_center.html")
    else:
        x={"center_id":request.form['center_id'],
            "center_name":request.form['center_name'],
            "room_no":request.form['room_no'],
            "address":request.form['address']}
        x=json.dumps(x)
        response = requests.put(url="http://127.0.0.1:5000/update_Exam",data=x)
    return response.text





#------------------------------ MAIN ACTIVITY PART ---------------------

@app.route('/booked',methods=['GET','POST'])
def res():

    if request.method=="GET":
        return render_template("staff_allot.html")
    else:
        date=str(request.form['date'])
        time1=str(request.form['time1'])
        time2=str(request.form['time2'])

        time_1=time1.split(":")
        t1=time_1[0]
        t2=time_1[1]
        if int(t1)>12:
            t1=str(int(t1)-12)
            time_1=t1+":"+t2+" "+"PM"
        elif int(t1)==12:
            time_1=t1+":"+t2+" "+"PM"
        else:
            time_1=t1+":"+t2+" "+"AM"


        time_2=time2.split(":")
        t3=time_2[0]
        t4=time_2[1]
        if int(t3)>12:
            t3=str(int(t1)-12)
            time_2=t3+":"+t4+" "+"PM"
        elif int(t1)==12:
            time_2=t4+":"+t4+" "+"PM"
        else:
            time_2=t3+":"+t4+" "+"AM"

        time=time_1+" - "+time_2

        #return jsonify(time)

        m=add_exam_center.objects()
        s=staff.objects()

   # room=list([str(i.room_no) for i in m])
   # cn=list([str(i.center_name) for i in m])
   # sid=list([int(j.emp_id) for j in s])
    
        for i,n in zip(m,s):
            c = booking(center_name=i.center_name,
            center_id=i.center_id,
            room_no=str(i.room_no),
            address=i.address,
            staff_id=n.emp_id,
            staff_name=n.full_name,
            staff_ph_no=int(n.ph_no),
            date=date,time=str(time))

            b = booked(center_name=i.center_name,
            center_id=i.center_id,
            room_no=str(i.room_no),
            address=i.address,
            staff_id=n.emp_id,
            staff_name=n.full_name,
            staff_ph_no=int(n.ph_no),
            date=date,time=time)
            c.save()
            b.save()
        return render_template("admin_success.html",data="Invigilator Alloted successfully")

    #c=m.count({})

# ----------------------------------------------------------

@app.route('/staff_allotment_list')
def staff_allotment_list():
    allot=booking.objects()
    #details=list(allot.staff_name,allot.staff_id)
    return render_template("staff_allotment_list.html",data=allot)

@app.route('/prev_allotment_list')
def prev_allotment_list():
    allot=booked.objects()
    #details=list(allot.staff_name,allot.staff_id)
    return render_template("staff_allotment_list.html",data=allot)
    
@app.route('/exam_center_details')
def exam_center_details():
    details=add_exam_center.objects()
    total_rooms=add_exam_center.objects().count({})

    return render_template("exam_center_details.html",data=details,count=total_rooms)

@app.route('/staff_details')
def staff_details():
    details=staff.objects()
    return render_template("staff_details.html",data=details)

#------------------------ LOGIN -----------------------------

@app.route('/login_redirect', methods = ['GET', 'POST'])
def login_redirect():
    form = LoginForm()
    return render_template('login.html', form = form)


@app.route('/login',methods=['GET','POST'])
def login():
    form=LoginForm(request.form)
    flag=True
    if request.method=='GET':
        return render_template("login.html")
    else:
        if form.email.data=="admin@mail.com" and form.password.data=="123456":
            user="USER"
            email="admin@mail.com"
            x={"name":user,
            "email":email}
            return render_template("admin.html",data=x)

        else:
            email=form.email.data
            get_password=form.password.data

            user=staff.objects(email=email)
            user_password=[str(u.password) for u in user]
            #id=pbkdf2_sha256.identify(user_password[0])

            if user:
                g_pass=user_password[0]
                decrypt=pbkdf2_sha256.verify(get_password,g_pass)
                if decrypt!=True:
                    flag=False
                if flag==True:
                    emp_id=[u.emp_id for u in user]
                    if emp_id:
                        emp_id=emp_id[0]
                        data=booking.objects(staff_id=emp_id)
                        if data:
                            return render_template("staff_dashboard.html",data=data,message=" ")
                        else:
                            return render_template("staff_dashboard.html",data=data,message="No Exam Center is Alloted Yet ...")
                else:
                    return render_template("error.html",data="Not valid credentials")
            else:
                return render_template("error.html",data="User Not Found !!!!")
    

@app.route('/update_staff_details',methods=['PUT'])
def update_staff_details():
    record = json.loads(request.data)
    data=staff.objects(emp_id=record['emp_id'])
    if data:
        password=record['password']
        c_password=record['c_password']
        if password==c_password:
            hash_password=pbkdf2_sha256.using(rounds=8000, salt_size=10).hash(record['password'])
            data.update(full_name=record['full_name'])
            data.update(emp_id=record['emp_id'])
            data.update(ph_no=record['ph_no'])
            data.update(address=record['address'])
            data.update(email=record['email'])
            data.update(password=hash_password)
        
            return jsonify(data.to_json())
    else:
        return render_template("error.html",data="User not Found")

@app.route('/update_staff_redirect',methods=['GET','POST'])
def update_staff_redirect():
    form = StaffRegisterForm()
    return render_template('update_staff.html', form = form)



@app.route('/update_staff',methods=['GET','POST'])
def update_staff():
    form=StaffRegisterForm(request.form)
    if request.method=="GET":
        return render_template("update_staff.html")
    else:
        x={"full_name":form.full_name.data,
        "ph_no":form.ph_no.data,
        "emp_id":form.emp_id.data,
        "email":form.email.data,
        "password":form.password.data,
        "c_password":form.c_password.data,
        "address":form.address.data
        }
        x=json.dumps(x)

        response = requests.put(url="http://127.0.0.1:5000/update_staff_details",data=x)

    return (response.text)


@app.route('/delete_staff_allot_record', methods=['DELETE','GET','POST'])
def delete_staff_allot_record():
    c = booking.objects()
    if not c:
        return render_template("error.html",data="There are no records to delete !!")
    else:
        c.delete()
        return render_template("admin_success.html",data="All records are Deleted ..")

    


#admin.add_view(ModelView(add_exam_center,db.session))


if __name__ == "__main__":
    app.run(debug=True)
