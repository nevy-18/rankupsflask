from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from textwrap import dedent
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# =========================================================
# DATABASE CONFIGURATION (Bagong Variable para Ma-bypass ang Cache)
# =========================================================
# Babasahin ang bagong variable 'AIVEN_DB_URI' para mapilitang mag-refresh ang Vercel container.
raw_uri = os.environ.get('AIVEN_DB_URI')

if raw_uri:
    # Siguraduhing gamit ang tamang protocol driver para sa SQLAlchemy
    if raw_uri.startswith('mysql://'):
        raw_uri = raw_uri.replace('mysql://', 'mysql+pymysql://', 1)
    
    # Direktang idugtong ang tamang parameter gamit ang underscore (_) para iwas sa TypeError
    if 'sslmode' not in raw_uri:
        if '?' in raw_uri:
            raw_uri += '&sslmode=REQUIRED'
        else:
            raw_uri += '?sslmode=REQUIRED'
            
    app.config['SQLALCHEMY_DATABASE_URI'] = raw_uri
else:
    # Fallback sa iyong lokal na XAMPP kapag tinakbo sa computer mo
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/finalrankup'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Walang kaakibat na 'SQLALCHEMY_ENGINE_OPTIONS' para permanenteng burado ang 'ssl-mode' keyword error
db = SQLAlchemy(app)

@app.route('/', methods=['GET', 'POST'])
def landing_page():
    error = None
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # =========================================
        # 1. CHECK STUDENT
        # =========================================
        student_query = db.session.execute(
            db.text("SELECT * FROM students WHERE username = :username"), 
            {"username": username}
        ).mappings().first()
        
        if student_query:
            if password == student_query['password']:
                session['student_id'] = student_query['student_id']
                session['role'] = 'student'
                session['name'] = student_query['full_name']
                return redirect(url_for('student_dashboard'))
        
        # =========================================
        # 2. CHECK TEACHER + ADMIN
        # =========================================
        teacher_query = db.session.execute(
            db.text("SELECT * FROM teachers WHERE username = :username"), 
            {"username": username}
        ).mappings().first()
        
        if teacher_query:
            if password == teacher_query['password']:
                session['user_id'] = teacher_query['teacher_id']
                session['role'] = teacher_query['role']
                session['name'] = teacher_query['username']
                
                if teacher_query['role'] == 'admin':
                    return redirect(url_for('admin_dashboard'))
                elif teacher_query['role'] == 'teacher':
                    return redirect(url_for('teacher_dashboard'))
        
        error = "Invalid username or password"
        
    return render_template('landingPage.html', error=error)

@app.route('/teacher/register', methods=['GET', 'POST'])
def teacher_register():
    if request.method == 'POST':
        full_name = request.form.get('fullName')
        department = request.form.get('department')
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        
        check_query = db.session.execute(
            db.text("SELECT * FROM teachers WHERE username = :username"),
            {"username": username}
        ).mappings().first()
        
        if check_query:
            flash('Username already exists', 'error')
            return redirect(url_for('teacher_register'))
        
        else:
            db.session.execute(
                db.text("""
                    INSERT INTO teachers (full_name, department, email, username, password)
                    VALUES (:full_name, :department, :email, :username, :password)
                """),
                {
                    "full_name": full_name, "department": department,
                    "email": email, "username": username, "password": password
                }
            )
            db.session.commit()
            
            flash('Registration Successful!', 'success')
            return redirect(url_for('teacher_login'))
            
    return render_template('teacherPages/teacherRegister.html')

@app.route('/student/register', methods=['GET', 'POST'])
def student_register():
    if request.method == 'POST':
        full_name = request.form.get('fullName')
        course = request.form.get('course')
        year = request.form.get('year')
        section = request.form.get('section')
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        
        check_query = db.session.execute(
            db.text("SELECT * FROM students WHERE username = :username"),
            {"username": username}
        ).mappings().first()
        
        if check_query:
            flash('Username already exists', 'error')
            return redirect(url_for('student_register'))
        
        else:
            db.session.execute(
                db.text("""
                    INSERT INTO students (full_name, course, year_level, section, email, username, password)
                    VALUES (:full_name, :course, :year, :section, :email, :username, :password)
                """),
                {
                    "full_name": full_name, "course": course, "year": year,
                    "section": section, "email": email, "username": username, "password": password
                }
            )
            db.session.commit()
            
            flash('Registration Successful!', 'success')
            return redirect(url_for('landing_page'))
            
    return render_template('studentPages/studentRegister.html')

@app.route('/teacher/login', methods=['GET', 'POST'])
def teacher_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        teacher_query = db.session.execute(
            db.text("SELECT * FROM teachers WHERE username = :username"), 
            {"username": username}
        ).mappings().first()
        
        if teacher_query:
            if password == teacher_query['password']:
                session['user_id'] = teacher_query['teacher_id']
                session['role'] = teacher_query['role']
                session['name'] = teacher_query['username']
                
                flash('Login Successful!', 'success')
                
                if teacher_query['role'] == 'admin':
                    return redirect(url_for('admin_dashboard'))
                else:
                    return redirect(url_for('teacher_dashboard'))
            else:
                flash('Wrong password', 'error')
                return redirect(url_for('teacher_login'))
        else:
            flash('User not found', 'error')
            return redirect(url_for('teacher_login'))
            
    return render_template('teacherPages/teacherLogin.html')

@app.route('/student/login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        student_query = db.session.execute(
            db.text("SELECT * FROM students WHERE username = :username"), 
            {"username": username}
        ).mappings().first()
        
        if student_query:
            if password == student_query['password']:
                session['student_id'] = student_query['student_id']
                session['username'] = student_query['username']
                session['role'] = 'student'
                
                flash('Login Successful!', 'success')
                return redirect(url_for('student_dashboard'))
            else:
                flash('Wrong password', 'error')
                return redirect(url_for('student_login'))
        else:
            flash('User not found', 'error')
            return redirect(url_for('student_login'))
            
    return render_template('studentPages/studentLogin.html')

@app.route('/teacher/dashboard')
def teacher_dashboard():
    if 'user_id' not in session or session.get('role') == 'student':
        flash('Please login first', 'error')
        return redirect(url_for('teacher_login'))
        
    search_query = request.args.get('query', '')
    search_results = []
    
    if search_query:
        search_results = db.session.execute(
            db.text("SELECT * FROM students WHERE full_name LIKE :search"),
            {"search": f"%{search_query}%"}
        ).mappings().all()
        
    leaderboard_results = db.session.execute(
        db.text("""
            SELECT s.full_name, sa.gwa 
            FROM student_averages sa 
            INNER JOIN students s ON sa.student_id = s.student_id 
            ORDER BY sa.gwa ASC
        """)
    ).mappings().all()
    
    return render_template(
        'teacherPages/teacherDashboard.html', 
        search_results=search_results, 
        search_query=search_query,
        leaderboard_results=leaderboard_results
    )

@app.route('/logout')
def logout():
    session.clear()
    flash('You have successfully logged in', 'success')
    return redirect(url_for('landing_page'))

@app.route('/student/dashboard')
def student_dashboard():
    if 'student_id' not in session:
        flash('Please login first', 'error')
        return redirect(url_for('student_login'))
        
    student_id = session['student_id']
    
    student_info = db.session.execute(
        db.text("SELECT * FROM students WHERE student_id = :student_id"),
        {"student_id": student_id}
    ).mappings().first()
    
    leaderboard_results = db.session.execute(
        db.text("""
            SELECT s.full_name, s.course, s.year_level, sa.gwa
            FROM student_averages sa
            INNER JOIN students s ON sa.student_id = s.student_id
            ORDER BY sa.gwa ASC
        """)
    ).mappings().all()
    
    return render_template(
        'studentPages/studentDashboard.html', 
        student=student_info, 
        leaderboard_results=leaderboard_results
    )

@app.route('/teacher/join-subject', methods=['GET', 'POST'])
def join_subject():
    if 'user_id' not in session or session.get('role') == 'student':
        flash('Please login first', 'error')
        return redirect(url_for('teacher_login'))

    student = None
    enrolled_subjects = []

    if request.method == 'POST' and 'join_subject' in request.form:
        student_id = request.form.get('student_id')
        subject_id = request.form.get('subject_id')

        check_enroll = db.session.execute(
            db.text("SELECT * FROM student_subjects WHERE student_id = :student_id AND subject_id = :subject_id"),
            {"student_id": student_id, "subject_id": subject_id}
        ).mappings().first()

        if check_enroll:
            flash('Student already enrolled in this subject', 'error')
        else:
            db.session.execute(
                db.text("INSERT INTO student_subjects (student_id, subject_id) VALUES (:student_id, :subject_id)"),
                {"student_id": student_id, "subject_id": subject_id}
            )
            db.session.commit()
            flash('Student successfully joined to subject', 'success')
        
        return redirect(url_for('join_subject', student_id=student_id))

    search_query = request.args.get('search', '')
    url_student_id = request.args.get('student_id', '')

    if search_query:
        student = db.session.execute(
            db.text("SELECT * FROM students WHERE full_name LIKE :search"),
            {"search": f"%{search_query}%"}
        ).mappings().first()
        if not student:
            flash('Student not found.', 'error')
            
    elif url_student_id:
        student = db.session.execute(
            db.text("SELECT * FROM students WHERE student_id = :student_id"),
            {"student_id": url_student_id}
        ).mappings().first()

    if student:
        enrolled_subjects = db.session.execute(
            db.text("""
                SELECT s.* FROM student_subjects ss 
                INNER JOIN subjects s ON ss.subject_id = s.subject_id 
                WHERE ss.student_id = :student_id
            """),
            {"student_id": student['student_id']}
        ).mappings().all()

    all_subjects = db.session.execute(
        db.text("SELECT * FROM subjects ORDER BY subject_name ASC")
    ).mappings().all()

    all_students = db.session.execute(
        db.text("SELECT * FROM students ORDER BY full_name ASC")
    ).mappings().all()

    return render_template(
        'teacherPages/joinSub.html',
        student=student,
        search_query=search_query,
        enrolled_subjects=enrolled_subjects,
        all_subjects=all_subjects,
        all_students=all_students
    )

@app.route('/teacher/create-subject', methods=['GET', 'POST'])
def create_subject():
    if 'user_id' not in session or session.get('role') == 'student':
        flash('Please login first', 'error')
        return redirect(url_for('teacher_login'))

    if request.method == 'POST':
        subject_code = request.form.get('subject_code')
        subject_name = request.form.get('subject_name')
        units = request.form.get('units')
        semester = request.form.get('semester')
        year_level = request.form.get('year_level')
        course = request.form.get('course')

        check_duplicate = db.session.execute(
            db.text("SELECT * FROM subjects WHERE subject_code = :subject_code"),
            {"subject_code": subject_code}
        ).mappings().first()

        if check_duplicate:
            flash('Subject already exists', 'error')
        else:
            db.session.execute(
                db.text("""
                    INSERT INTO subjects (subject_code, subject_name, units, semester, year_level, course) 
                    VALUES (:subject_code, :subject_name, :units, :semester, :year_level, :course)
                """),
                {
                    "subject_code": subject_code, "subject_name": subject_name,
                    "units": units, "semester": semester, "year_level": year_level, "course": course
                }
            )
            db.session.commit()
            flash('Subject created successfully', 'success')
        
        return redirect(url_for('create_subject'))

    subjects_list = db.session.execute(
        db.text("SELECT * FROM subjects ORDER BY subject_name ASC")
    ).mappings().all()

    return render_template('teacherPages/createsubject.html', subjects=subjects_list)

@app.route('/teacher/student-grades', methods=['GET', 'POST'])
def student_grades():
    if 'user_id' not in session or session.get('role') != 'admin' and session.get('role') != 'teacher':
        flash('Please login first', 'error')
        return redirect(url_for('teacher_login'))

    delete_id = request.args.get('delete_avg')
    if delete_id:
        db.session.execute(db.text("DELETE FROM student_grades WHERE student_id = :id"), {"id": delete_id})
        db.session.execute(db.text("DELETE FROM student_averages WHERE student_id = :id"), {"id": delete_id})
        db.session.commit()
        flash('Deleted successfully', 'success')
        return redirect(url_for('student_grades'))

    student = None
    subjects_with_grades = []

    if request.method == 'POST' and 'update_grades' in request.form:
        student_id = request.form.get('student_id')
        subject_ids = request.form.getlist('subject_id[]')
        grades = request.form.getlist('grade[]')

        db.session.execute(db.text("DELETE FROM student_grades WHERE student_id = :id"), {"id": student_id})

        total = 0.0
        count = 0

        for i in range(len(grades)):
            if grades[i]:
                sub_id = subject_ids[i]
                grade_val = float(grades[i])
                remarks = 'Passed' if grade_val <= 3.0 else 'Failed'
                
                total += grade_val
                count += 1

                db.session.execute(
                    db.text("""
                        INSERT INTO student_grades (student_id, subject_id, grade, remarks) 
                        VALUES (:student_id, :subject_id, :grade, :remarks)
                    """),
                    {"student_id": student_id, "subject_id": sub_id, "grade": grade_val, "remarks": remarks}
                )

        if count > 0:
            gwa = total / count
            
            if gwa <= 1.50:
                status = 'President List'
            elif gwa <= 2.00:
                status = 'Dean List'
            else:
                status = 'Regular'

            check_avg = db.session.execute(
                db.text("SELECT * FROM student_averages WHERE student_id = :id"), {"id": student_id}
            ).mappings().first()

            if check_avg:
                db.session.execute(
                    db.text("UPDATE student_averages SET gwa = :gwa, academic_status = :status WHERE student_id = :id"),
                    {"gwa": gwa, "status": status, "id": student_id}
                )
            else:
                db.session.execute(
                    db.text("INSERT INTO student_averages (student_id, gwa, academic_status) VALUES (:id, :gwa, :status)"),
                    {"id": student_id, "gwa": gwa, "status": status}
                )
            
            db.session.commit()
            flash('Grades updated successfully', 'success')
        
        return redirect(url_for('student_grades'))

    search_query = request.args.get('search', '')
    if search_query:
        student = db.session.execute(
            db.text("SELECT * FROM students WHERE full_name LIKE :search"),
            {"search": f"%{search_query}%"}
        ).mappings().first()

        if student:
            subjects_with_grades = db.session.execute(
                db.text("""
                    SELECT s.subject_id, s.subject_code, s.subject_name, s.units, g.grade
                    FROM student_subjects ss
                    INNER JOIN subjects s ON ss.subject_id = s.subject_id
                    LEFT JOIN student_grades g ON g.subject_id = s.subject_id AND g.student_id = :student_id
                    WHERE ss.student_id = :student_id
                """),
                {"student_id": student['student_id']}
            ).mappings().all()
        else:
            flash('Student not found', 'error')

    all_students = db.session.execute(
        db.text("""
            SELECT s.*, sa.gwa, sa.academic_status 
            FROM students s
            LEFT JOIN student_averages sa ON s.student_id = sa.student_id
            ORDER BY s.full_name ASC
        """)
    ).mappings().all()

    return render_template(
        'teacherPages/createStudentGrades.html',
        student=student,
        subjects=subjects_with_grades,
        all_students=all_students,
        search_query=search_query
    )

@app.route('/about')
def about_system():
    return render_template('aboutSystem.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Access denied. Admins only.', 'error')
        return redirect(url_for('landing_page'))

    teachers_list = db.session.execute(
        db.text("SELECT * FROM teachers ORDER BY full_name ASC")
    ).mappings().all()

    students_list = db.session.execute(
        db.text("SELECT * FROM students ORDER BY full_name ASC")
    ).mappings().all()

    subjects_list = db.session.execute(
        db.text("SELECT * FROM subjects ORDER BY subject_name ASC")
    ).mappings().all()

    return render_template(
        'adminDashboard.html', 
        teachers=teachers_list, 
        students=students_list, 
        subjects=subjects_list
    )

@app.route('/admin/delete/<string:data_type>/<int:data_id>', methods=['GET'])
def admin_delete_record(data_type, data_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('landing_page'))

    if data_type == 'teacher':
        db.session.execute(db.text("DELETE FROM teachers WHERE teacher_id = :id"), {"id": data_id})
        flash('Teacher deleted successfully', 'success')

    elif data_type == 'student':
        db.session.execute(db.text("DELETE FROM students WHERE student_id = :id"), {"id": data_id})
        flash('Student deleted successfully', 'success')

    elif data_type == 'subject':
        db.session.execute(db.text("DELETE FROM subjects WHERE subject_id = :id"), {"id": data_id})
        flash('Subject deleted successfully', 'success')

    else:
        flash('Invalid delete request', 'error')

    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/edit-student/<int:student_id>', methods=['GET', 'POST'])
def edit_student(student_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('landing_page'))

    if request.method == 'POST':
        full_name = request.form.get('full_name')
        course = request.form.get('course')
        year_level = request.form.get('year_level')
        section = request.form.get('section')
        email = request.form.get('email')
        username = request.form.get('username')

        db.session.execute(
            db.text("""
                UPDATE students SET 
                    full_name = :full_name,
                    course = :course,
                    year_level = :year_level,
                    section = :section,
                    email = :email,
                    username = :username
                WHERE student_id = :id
            """),
            {
                "full_name": full_name, "course": course, "year_level": year_level,
                "section": section, "email": email, "username": username, "id": student_id
            }
        )
        db.session.commit()
        flash('Student updated successfully', 'success')
        return redirect(url_for('admin_dashboard'))

    row = db.session.execute(
        db.text("SELECT * FROM students WHERE student_id = :id"), {"id": student_id}
    ).mappings().first()

    if not row:
        flash('Student record not found.', 'error')
        return redirect(url_for('admin_dashboard'))

    return render_template('editStudent.html', row=row)

@app.route('/admin/edit-subject/<int:subject_id>', methods=['GET', 'POST'])
def edit_subject(subject_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('landing_page'))

    if request.method == 'POST':
        subject_code = request.form.get('subject_code')
        subject_name = request.form.get('subject_name')
        units = request.form.get('units')
        semester = request.form.get('semester')
        year_level = request.form.get('year_level')
        course = request.form.get('course')

        db.session.execute(
            db.text("""
                UPDATE subjects SET 
                    subject_code = :subject_code,
                    subject_name = :subject_name,
                    units = :units,
                    semester = :semester,
                    year_level = :year_level,
                    course = :course
                WHERE subject_id = :id
            """),
            {
                "subject_code": subject_code, "subject_name": subject_name, 
                "units": units, "semester": semester, "year_level": year_level, 
                "course": course, "id": subject_id
            }
        )
        db.session.commit()
        flash('Subject updated successfully', 'success')
        return redirect(url_for('admin_dashboard'))

    row = db.session.execute(
        db.text("SELECT * FROM subjects WHERE subject_id = :id"), {"id": subject_id}
    ).mappings().first()

    if not row:
        flash('Subject record not found.', 'error')
        return redirect(url_for('admin_dashboard'))

    return render_template('editSubject.html', row=row)

@app.route('/admin/edit-teacher/<int:teacher_id>', methods=['GET', 'POST'])
def edit_teacher(teacher_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('landing_page'))

    if request.method == 'POST':
        full_name = request.form.get('full_name')
        department = request.form.get('department')
        email = request.form.get('email')
        username = request.form.get('username')

        db.session.execute(
            db.text("""
                UPDATE teachers SET 
                    full_name = :full_name,
                    department = :department,
                    email = :email,
                    username = :username
                WHERE teacher_id = :id
            """),
            {
                "full_name": full_name, "department": department,
                "email": email, "username": username, "id": teacher_id
            }
        )
        db.session.commit()
        flash('Teacher updated successfully', 'success')
        return redirect(url_for('admin_dashboard'))

    row = db.session.execute(
        db.text("SELECT * FROM teachers WHERE teacher_id = :id"), {"id": teacher_id}
    ).mappings().first()

    if not row:
        flash('Teacher record not found.', 'error')
        return redirect(url_for('admin_dashboard'))

    return render_template('editTeacher.html', row=row)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)