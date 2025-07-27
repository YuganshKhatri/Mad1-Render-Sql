*import os
from datetime import datetime
from collections import Counter
from flask import Flask
from flask import render_template
from flask import request,jsonify
from flask import url_for,flash,session
from flask import redirect
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key="Yugansh@12"
current_dir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://mad1_project_user:BuEZ8A6pbNKZU7jWrHQWetjUMhZHU8Aw@dpg-d22vepngi27c73fd9s7g-a/mad1_project"
db = SQLAlchemy()
db.init_app(app)
with app.app_context():
    db.create_all()
app.app_context().push()

class User_Details(db.Model):
    __tablename__='User_Details'
    User_id=db.Column(db.Integer,unique=True,autoincrement=True,primary_key=True,nullable=False)
    Username=db.Column(db.String,unique=True,nullable=False)
    Password=db.Column(db.String,nullable=False)
    Fullname=db.Column(db.String,nullable=False)
    Address=db.Column(db.String,nullable=False)
    Pincode=db.Column(db.Integer,nullable=False)

class Parking_lot(db.Model):
    __tablename__='Parking_Lot'
    Lot_Id=db.Column(db.Integer,unique=True,nullable=False,primary_key=True)
    Name=db.Column(db.String,nullable=True)
    Address=db.Column(db.String,nullable=True)
    Total_spots=db.Column(db.Integer,nullable=False)
    Available_spots=db.Column(db.Integer,nullable=True)
    Charges=db.Column(db.Integer,nullable=True)

class ParkingHistory(db.Model):
    __tablename__ = "parking_history"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('User_Details.User_id'))
    lot_id = db.Column(db.Integer, db.ForeignKey('Parking_Lot.Lot_Id'))
    spot_id = db.Column(db.Integer)
    vehicle_number = db.Column(db.String(20))
    start_time = db.Column(db.DateTime, nullable=True)
    end_time = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(10), default="Booked")
    cost=db.Column(db.Integer) 

    lot=db.relationship("Parking_lot",backref='bookings')

class Admin_Details(db.Model):
    __tablename__="admin_details"
    email=db.Column(db.String,primary_key=True)
    password=db.Column(db.String)
    fullname=db.Column(db.String)
    address=db.Column(db.String)
    pincode=db.Column(db.Integer)

@app.route("/",methods=["GET","POST"])
def about():
    return render_template("aboutus.html")
@app.route("/signup",methods=["GET","POST"])
def signup():
    if request.method=="POST":
        username=request.form["username"]
        password=request.form["pass"]
        fullname=request.form["name"]
        address=request.form["address"]
        pincode=request.form["pincode"]
        if User_Details.query.filter_by(Username=username).first():
            flash("User already exists. Please log in or use a different email.","userexist")
            return render_template("signup.html")
        new_user=User_Details(Username=username,Password=password,Fullname=fullname,Address=address,Pincode=pincode)
        db.session.add(new_user)
        db.session.commit()
        flash("Account created successfully! Please Login.","created")
        return render_template("login.html")
    return render_template("signup.html")
@app.route("/login",methods=["GET","POST"])
def login():
    if request.method=="POST":
        username=request.form["username"]
        password=request.form["pass"]
        logs=db.session.query(Admin_Details).all()
        for log in logs:
            if username==log.email and password==log.password:
                session["admin"]=username 
                return redirect(url_for('adminhome'))
        check=db.session.query(User_Details).filter((User_Details.Username==username) & (User_Details.Password==password)).first()
        if check:
            session["username"]=username
            return redirect(url_for('home',username=username))
        user=db.session.query(User_Details).filter(User_Details.Username==username).first()
        if user:
            flash("Incorrect Password! Try Again","InPass")
            return render_template("login.html")
        flash("Username/Email doesn't Exist. Please sign up first.","SignUP")
        return render_template("signup.html")
    return render_template("login.html")
@app.route("/user/<username>",methods=["GET","POST"])
def home(username):
    username=session.get("username")
    name=db.session.query(User_Details).filter(User_Details.Username==username).first()
    fullname=name.Fullname
    lots=db.session.query(Parking_lot).all()
    history=db.session.query(ParkingHistory).filter_by(user_id=name.User_id).order_by(ParkingHistory.id.desc()).limit(2).all()
    lot=db.session.query(ParkingHistory).filter(ParkingHistory.user_id==name.User_id).first()
    lot_id=lot.lot_id if lot else None
    return render_template("home.html",username=fullname,lots=lots,parking_history=history,lot_id=lot_id)

@app.route("/search/<username>",methods=["GET","POST"])
def search(username):
    search=request.form.get("search","").strip()
    username=session.get("username")
    user = db.session.query(User_Details).filter(User_Details.Username==username).first()
    fullname = user.Fullname
    lots=db.session.query(Parking_lot).filter((Parking_lot.Name.ilike(f"%{search}%")) | (Parking_lot.Address.ilike(f"%{search}%"))).all()
    history=db.session.query(ParkingHistory).filter_by(user_id=user.User_id).order_by(ParkingHistory.id.desc()).limit(2).all()
    return render_template("home.html",username=fullname,lots=lots,parking_history=history)
@app.route("/book/<username>/<int:lot_id>",methods=["GET","POST"])
def book(username,lot_id):
    username=session.get("username")
    user=db.session.query(User_Details).filter_by(Username=username).first()
    lot=db.session.query(Parking_lot).filter_by(Lot_Id=lot_id).first()
    if not lot:
        return "Parking Lot not found",404
    if request.method=="POST":
        vehicle=request.form.get("veh")
        new_booking=ParkingHistory(user_id=user.User_id,lot_id=lot.Lot_Id,spot_id=(lot.Total_spots-lot.Available_spots+1),vehicle_number=vehicle,status="Booked")
        db.session.add(new_booking)
        lot.Available_spots-=1
        db.session.commit()
        session["lot_id"]=lot.Lot_Id
        return redirect(url_for("home", username=username))
    return render_template("book.html", user_id=user.User_id, lot=lot, username=username,spot_id=(lot.Total_spots-lot.Available_spots+1))

@app.route("/start/<int:history_id>",methods=["GET","POST"])
def start_parking(history_id):
    username=session.get("username")
    record=db.session.get(ParkingHistory, history_id)
    if record and record.status=="Booked":
        record.start_time=datetime.now()
        record.status="Started"
        db.session.commit()
    return redirect(url_for("home", username=username))

@app.route("/release/<int:history_id>",methods=["GET","POST"])
def release_parking(history_id):
    username=session.get("username")
    record = db.session.get(ParkingHistory,history_id)
    if record and record.status == "Started":
        lot = db.session.query(Parking_lot).filter_by(Lot_Id=record.lot_id).first()
        record.end_time = datetime.now()
        record.status = "Released"
        lot.Available_spots+=1
        duration_second=(record.end_time-record.start_time).total_seconds()
        cost=round((duration_second/3600)*lot.Charges,2)
        record.cost=cost
        db.session.commit()
        return render_template("Release.html",Spot_id=record.spot_id,vehicle=record.vehicle_number,start_time=record.start_time,end_time=record.end_time,total_cost=cost)
    return redirect(url_for("home", username=username))

@app.route("/user/<username>/edit",methods=["GET","POST"])
def edit(username):
    username=session.get("username")
    user=db.session.query(User_Details).filter(User_Details.Username==username).first()
    if request.method=="POST":
        user.Password=request.form["pass"]
        user.Fullname=request.form["name"]
        user.Address=request.form["add"]
        user.Pincode=request.form["pin"]
        db.session.commit()
        return redirect(url_for('home',username=session.get('username')))
    return render_template("edit.html",user=user,username=username)

@app.route("/user/<username>/summary",methods=["GET","POST"])
def summary(username):
    username=session.get("username")
    user = db.session.query(User_Details).filter(User_Details.Username==username).first()
    history=db.session.query(ParkingHistory).filter_by(user_id=user.User_id).order_by(ParkingHistory.id.desc()).all()
    locations = [f"{entry.lot.Name} - {entry.lot.Address}" for entry in history]
    counter = Counter(locations)
    location_labels = list(counter.keys())
    booking_counts = list(counter.values())
    return render_template("summary.html",parking_history=history,location_labels=location_labels,booking_counts=booking_counts,username=username)

@app.route("/user/admin",methods=["GET","POST"])
def adminhome():
    parking_lot=db.session.query(Parking_lot).all()
    parking=db.session.query(ParkingHistory).all()
    latest_status={}
    for record in parking:
        key=(record.lot_id,record.spot_id)
        latest_status[key]=record
    return render_template("adminhome.html",parking_lot=parking_lot,spot_status=latest_status)

@app.route("/user/admin/editparkinglots/<int:lot_id>",methods=["GET","POST"])
def adminedit(lot_id):
    lot=db.session.query(Parking_lot).filter(Parking_lot.Lot_Id==lot_id).first()
    if request.method=="POST":
        lot.Name=request.form.get("loc")
        lot.Address=request.form.get("add")
        lot.Total_spots=request.form.get("total")
        lot.Available_spots=request.form.get("avai")
        lot.Charges=request.form.get("charges")
        db.session.commit()
        return redirect(url_for('adminhome'))
    return render_template("adminedit.html",lot=lot)

@app.route("/user/admin/deleteparkinglots/<int:lot_id>",methods=["GET","POST"])
def admindelete(lot_id):
    lot=db.session.query(Parking_lot).filter(Parking_lot.Lot_Id==lot_id).first()
    if lot.Total_spots==lot.Available_spots:
        db.session.query(ParkingHistory).filter(ParkingHistory.lot_id==lot_id).delete()
        db.session.delete(lot)
        db.session.commit()
        flash("Parking lot deleted successfully!")
    else:
        flash("Unable to delete Parking Lot because the Spots in the Parking Lot are Currently Booked!")
    return redirect(url_for("adminhome"))
@app.route("/admin/addlot",methods=["GET","POST"])
def addlot():
    if request.method=="POST":
        lot_id=request.form.get("lot")
        name=request.form.get("loc")
        address=request.form.get("add")
        total=request.form.get("total")
        charges=request.form.get("charges")
        new_lot=Parking_lot(Lot_Id=lot_id,Name=name,Address=address,Total_spots=total,Available_spots=total,Charges=charges)
        db.session.add(new_lot)
        db.session.commit()
        return redirect(url_for("adminhome")) 
    return render_template("addlot.html")

@app.route("/user/details",methods=["GET","POST"])
def userdetails():
    user=db.session.query(User_Details).all()
    return render_template("userdetails.html",user=user)

@app.route("/search",methods=["GET","POST"])
def adminsearch():
    category=request.args.get("search_by")
    search_value=request.args.get("search")
    if category=="user_id":
        result=db.session.query(User_Details).filter(User_Details.User_id==search_value).all()
        return render_template("searchuser.html",user=result,search_by=category,search=search_value)
    if category in ["location","lot_name"]:
        if category=="location":
            result=db.session.query(Parking_lot).filter(Parking_lot.Address.ilike(f"%{search_value}%")).all()
        else:
            result=db.session.query(Parking_lot).filter(Parking_lot.Name.ilike(f"%{search_value}%")).all()
        parking=db.session.query(ParkingHistory).order_by(ParkingHistory.id.desc()).all()
        latest_status={}
        for record in parking:
            key=(record.lot_id,record.spot_id)
            if key not in latest_status and record.status in ["Started","Booked"]:
                latest_status[key]=record
        return render_template("searchparkinglot.html",parking_lot=result,spot_status=latest_status)
    return redirect (url_for("adminhome"))

@app.route("/spot/<int:lot_id>/<int:spot_id>",methods=["GET","POST"])
def spotdetails(lot_id,spot_id):
    user=db.session.query(ParkingHistory).filter((ParkingHistory.lot_id==lot_id) & (ParkingHistory.spot_id==spot_id)).order_by(ParkingHistory.id.desc()).first()
    if user and user.status in ["Booked","Started"]:
            user_id=user.user_id
            vehicle=user.vehicle_number
            start=user.start_time
            cost=user.cost
            return render_template("spotdetails.html",lot_id=lot_id,spot_id=spot_id,user_id=user_id,vehicle=vehicle,start=start,cost=cost)
    else:
        return render_template("spotdet.html",lot_id=lot_id,spot_id=spot_id)
    

@app.route("/admin/summary", methods=["GET", "POST"])
def adminsummary():
    total=0
    occupied=0
    available=0
    histories = db.session.query(ParkingHistory).order_by(ParkingHistory.id.desc()).all()
    parking=db.session.query(Parking_lot).all()
    for park in parking:
        total+=park.Total_spots
    enriched_histories = []
    for history in histories:
        user = db.session.query(User_Details).filter_by(User_id=history.user_id).first()
        lot = db.session.query(Parking_lot).filter_by(Lot_Id=history.lot_id).first()
        if history.status in ["Started","Booked"]:
            occupied+=1
        enriched_histories.append({"history": history,"username": user.Username if user else "Unknown","lotname": lot.Name if lot else "Unknown"})
    available=total-occupied
    data = db.session.query(Parking_lot.Name,db.func.sum(ParkingHistory.cost).label('total_revenue')).join(ParkingHistory, ParkingHistory.lot_id == Parking_lot.Lot_Id).group_by(Parking_lot.Name).all()
    lot_names = [row[0] for row in data]
    revenues = [row[1] for row in data]
    return render_template("adminsummary.html", enriched_histories=enriched_histories,occupied=occupied,available=available,lot_names=lot_names,revenues=revenues)

@app.route("/admin/editprofile",methods=["GET","POST"])
def admineditprofile():
    email=session.get("admin")
    admin=db.session.query(Admin_Details).filter(Admin_Details.email==email).first()
    if request.method=="POST":
        admin.fullname=request.form.get("name")
        admin.address=request.form.get("add")
        admin.pincode=request.form.get("pin")
        db.session.commit()
        return redirect(url_for("adminhome"))
    return render_template("admineditprofile.html",admin=admin)



if __name__=='__main__':
    app.run(host='0.0.0.0',port=7000,debug=True)
