from flask import Flask, render_template, request, redirect, url_for, session, flash, Response
from database import db, User, Class, Attendee, init_db
import csv
from io import StringIO
from datetime import datetime

app = Flask(__name__)
app.secret_key = "your-secret-key"  # Change this to a secure key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

init_db(app)

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session["user_id"] = user.id
            session["role"] = user.role
            if user.role == "frontdesk":
                return redirect(url_for("frontdesk"))
            elif user.role == "teacher":
                return redirect(url_for("teacher"))
            elif user.role == "admin":
                return redirect(url_for("admin"))
        flash("Invalid credentials")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("role", None)
    return redirect(url_for("login"))

@app.route("/frontdesk", methods=["GET", "POST"])
def frontdesk():
    if session.get("role") not in ["frontdesk", "admin"]:
        return redirect(url_for("login"))
    
    if request.method == "POST":
        if "add_class" in request.form:
            new_class = Class(
                name=request.form["class_name"],
                date=request.form["date"],
                time=request.form["time"],
                teacher=request.form["teacher"],
                location=request.form["location"],
                group=request.form["group"]
            )
            db.session.add(new_class)
            db.session.commit()
            flash("Class added successfully!")
        elif "add_attendee" in request.form:
            new_attendee = Attendee(
                name=request.form["name"],
                date=request.form["date"],
                time_in=request.form["time_in"],
                time_out=request.form["time_out"],
                class_id=request.form["class_id"],
                location=request.form["location"],
                group=request.form["group"],
                stipend=request.form["stipend"] == "yes"
            )
            db.session.add(new_attendee)
            db.session.commit()
            flash("Attendee added successfully!")
    
    today = datetime.now().strftime("%Y-%m-%d")
    today_classes = Class.query.filter_by(date=today).all()
    today_class_ids = [class_.id for class_ in today_classes]
    today_attendees = Attendee.query.filter(Attendee.class_id.in_(today_class_ids)).all()
    classes = Class.query.all()
    attendees = Attendee.query.all()
    return render_template(
        "frontdesk.html",
        classes=classes,
        attendees=attendees,
        role=session.get("role"),
        today_classes=today_classes,
        today_attendees=today_attendees,
        today=today
    )

@app.route("/teacher", methods=["GET", "POST"])
def teacher():
    if session.get("role") not in ["teacher", "admin"]:
        return redirect(url_for("login"))
    
    if request.method == "POST":
        if "confirm_attendance" in request.form:
            attendee = Attendee.query.get(request.form["attendee_id"])
            attendee.time_out = request.form["time_out"]
            db.session.commit()
            flash("Attendance confirmed!")
        elif "add_comment" in request.form:
            attendee = Attendee.query.get(request.form["attendee_id"])
            attendee.comments = request.form["comment"]
            db.session.commit()
            flash("Comment added!")
        elif "search_class" in request.form:
            search_term = request.form["search_term"]
            classes = Class.query.filter(Class.name.like(f"%{search_term}%") | Class.date.like(f"%{search_term}%")).all()
            attendees = Attendee.query.all()
            return render_template("teacher.html", classes=classes, attendees=attendees, role=session.get("role"))
    
    classes = Class.query.all()
    attendees = Attendee.query.all()
    return render_template("teacher.html", classes=classes, attendees=attendees, role=session.get("role"))

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if session.get("role") != "admin":
        return redirect(url_for("login"))
    
    if request.method == "POST":
        print("POST request to /admin:", request.form)
        if "add_class" in request.form:
            new_class = Class(
                name=request.form["class_name"],
                date=request.form["date"],
                time=request.form["time"],
                teacher=request.form["teacher"],
                location=request.form["location"],
                group=request.form["group"]
            )
            db.session.add(new_class)
            db.session.commit()
            flash("Class added successfully!")
        elif "modify_class" in request.form:
            class_ = Class.query.get(request.form["class_id"])
            class_.name = request.form["class_name"]
            class_.date = request.form["date"]
            class_.time = request.form["time"]
            class_.teacher = request.form["teacher"]
            class_.location = request.form["location"]
            class_.group = request.form["group"]
            db.session.commit()
            flash("Class modified successfully!")
        elif "modify_attendee" in request.form:
            attendee = Attendee.query.get(request.form["attendee_id"])
            attendee.name = request.form["name"]
            attendee.date = request.form["date"]
            attendee.time_in = request.form["time_in"]
            attendee.time_out = request.form["time_out"]
            attendee.class_id = request.form["class_id"]
            attendee.location = request.form["location"]
            attendee.group = request.form["group"]
            attendee.stipend = request.form["stipend"] == "yes"
            attendee.comments = request.form.get("comments", "")
            db.session.commit()
            flash("Attendee modified successfully!")
        elif "delete_class" in request.form:
            class_ = Class.query.get(request.form["class_id"])
            db.session.delete(class_)
            db.session.commit()
            flash("Class deleted successfully!")
        elif "delete_attendee" in request.form:
            attendee = Attendee.query.get(request.form["attendee_id"])
            db.session.delete(attendee)
            db.session.commit()
            flash("Attendee deleted successfully!")
        elif "generate_report" in request.form:
            print("Generating report for:", request.form["month"], request.form["year"])
            month = request.form["month"]
            year = request.form["year"]
            classes = Class.query.filter(Class.date.like(f"{year}-{month}%")).all()
            attendees = Attendee.query.filter(Attendee.date.like(f"{year}-{month}%")).all()
            return render_template("admin.html", classes=classes, attendees=attendees, report=True, role=session.get("role"))
    
    classes = Class.query.all()
    attendees = Attendee.query.all()
    return render_template("admin.html", classes=classes, attendees=attendees, role=session.get("role"))

@app.route("/export_csv", methods=["POST"])
def export_csv():
    if session.get("role") != "admin":
        return redirect(url_for("login"))
    
    print("POST request to /export_csv:", request.form)
    month = request.form.get("month")
    year = request.form.get("year")
    if not month or not year:
        print("Missing month or year parameters")
        return "Missing month or year parameters", 400
    
    print("Exporting CSV for:", month, year)
    
    try:
        output = StringIO()
        writer = csv.writer(output, lineterminator='\n')
        writer.writerow(["Classes"])
        writer.writerow(["Name", "Date", "Time", "Teacher", "Location", "Group"])
        classes = Class.query.filter(Class.date.like(f"{year}-{month}%")).all()
        for class_ in classes:
            writer.writerow([class_.name, class_.date, class_.time, class_.teacher, class_.location, class_.group])
        writer.writerow([])
        writer.writerow(["Attendees"])
        writer.writerow(["Name", "Date", "Time In", "Time Out", "Class", "Location", "Group", "Stipend", "Comments"])
        attendees = Attendee.query.filter(Attendee.date.like(f"{year}-{month}%")).all()
        for attendee in attendees:
            class_name = Class.query.get(attendee.class_id).name if attendee.class_id else "N/A"
            writer.writerow([attendee.name, attendee.date, attendee.time_in, attendee.time_out, class_name, attendee.location, attendee.group, "Yes" if attendee.stipend else "No", attendee.comments or ""])
        
        csv_data = output.getvalue()
        output.close()
        
        print("Sending CSV file...")
        return Response(
            csv_data,
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment; filename=report_{year}_{month}.csv"}
        )
    except Exception as e:
        print("Error generating CSV:", str(e))
        return f"Error: {str(e)}", 500

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)