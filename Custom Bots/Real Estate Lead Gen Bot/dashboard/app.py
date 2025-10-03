from flask import Flask, render_template, request, redirect, url_for, flash
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from models import Base, Property, Owner
import os
from dotenv import load_dotenv
import subprocess

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'supersecret')

load_dotenv()
database_url = os.getenv('DATABASE_URL', 'sqlite:///data/properties.db')
engine = create_engine(database_url)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

@app.route('/')
def index():
    session = Session()
    # Filtering
    source = request.args.get('source')
    min_score = request.args.get('min_score', type=int, default=0)
    sort_by = request.args.get('sort_by', 'distress_score')
    order = request.args.get('order', 'desc')
    query = session.query(Property)
    if source:
        query = query.filter(Property.source == source)
    if min_score:
        query = query.filter(Property.distress_score >= min_score)
    if order == 'desc':
        query = query.order_by(desc(getattr(Property, sort_by)))
    else:
        query = query.order_by(getattr(Property, sort_by))
    leads = query.limit(100).all()
    session.close()
    return render_template('index.html', leads=leads, source=source, min_score=min_score, sort_by=sort_by, order=order)

@app.route('/lead/<int:lead_id>')
def lead_detail(lead_id):
    session = Session()
    lead = session.query(Property).get(lead_id)
    session.close()
    return render_template('lead_detail.html', lead=lead)

@app.route('/run_now', methods=['POST'])
def run_now():
    # Run cleaning and deduplication, then rescoring
    try:
        subprocess.run(['python', 'scripts/clean_and_dedupe.py'], check=True)
        subprocess.run(['python', 'scripts/rescore_leads.py'], check=True)
        flash('Cleaning, deduplication, and rescoring completed!', 'success')
    except subprocess.CalledProcessError:
        flash('Error running cleaning/deduplication or rescoring.', 'danger')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True) 