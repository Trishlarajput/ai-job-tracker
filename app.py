from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///jobs.db'
db = SQLAlchemy(app)

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company = db.Column(db.String(100))
    role = db.Column(db.String(100))
    status = db.Column(db.String(50), default='Applied')
    applied_date = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text, default='')

@app.route('/')
def index():
    jobs = Job.query.all()
    total = len(jobs)
    status_counts = {}
    for job in jobs:
        status_counts[job.status] = status_counts.get(job.status, 0) + 1
    return render_template('index.html', jobs=jobs, total=total, status_counts=status_counts)

@app.route('/add', methods=['GET', 'POST'])
def add_job():
    if request.method == 'POST':
        job = Job(
            company = request.form['company'],
            role    = request.form['role'],
            status  = request.form['status'],
            notes   = request.form.get('notes', '')
        )
        db.session.add(job)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('add_job.html')

@app.route('/analyze', methods=['GET', 'POST'])
def analyze():
    result = None
    if request.method == 'POST':
        resume_text = request.form['resume']
        job_desc = request.form['job_description']

        model = genai.GenerativeModel('gemini-flash-latest')
        prompt = f"""
        Compare this resume with the job description below.
        Give:
        1. A match percentage (0-100)
        2. Top 3 missing skills/keywords
        3. Two suggestions to improve the resume for this specific job

        Resume:
        {resume_text}

        Job Description:
        {job_desc}
        """
        response = model.generate_content(prompt)
        result = response.text

    return render_template('analyze.html', result=result)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)