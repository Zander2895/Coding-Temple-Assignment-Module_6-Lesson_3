from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from datetime import datetime
import pytz

# Initialize Flask app
app = Flask(__name__)

# Configure the SQLAlchemy part of the app instance
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:your_password@localhost/fitness_center_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Create the SQLAlchemy db instance and Marshmallow instance
db = SQLAlchemy(app)
ma = Marshmallow(app)

# Define the Member model
class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    join_date = db.Column(db.DateTime, default=datetime.utcnow)  # Use UTC as the default join date

# Define the WorkoutSession model
class WorkoutSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)
    workout_type = db.Column(db.String(100), nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # Duration in minutes
    session_date = db.Column(db.DateTime, default=datetime.utcnow)  # Use UTC as the default session date

    # Relationship to access member information easily
    member = db.relationship('Member', backref=db.backref('workouts', lazy=True))

# Define Marshmallow Schemas for serialization
class MemberSchema(ma.SQLAlchemyAutoSchema):
    join_date = ma.auto_field(format='%Y-%m-%d %H:%M:%S')  # Format join_date

    class Meta:
        model = Member

class WorkoutSessionSchema(ma.SQLAlchemyAutoSchema):
    session_date = ma.auto_field(format='%Y-%m-%d %H:%M:%S')  # Format session_date
    
    class Meta:
        model = WorkoutSession
        include_fk = True  # Include foreign key fields

# Instantiate schemas
member_schema = MemberSchema()
members_schema = MemberSchema(many=True)
workout_schema = WorkoutSessionSchema()
workouts_schema = WorkoutSessionSchema(many=True)

# Utility function to get current time in a specific time zone
def get_current_time_in_timezone(timezone_str='UTC'):
    tz = pytz.timezone(timezone_str)
    return datetime.now(tz)

# Routes for Member CRUD Operations

# Add a new member
@app.route('/members', methods=['POST'])
def add_member():
    data = request.json
    new_member = Member(
        first_name=data['first_name'],
        last_name=data['last_name'],
        email=data['email'],
        join_date=get_current_time_in_timezone(data.get('timezone', 'UTC'))  # Handle time zone
    )
    try:
        db.session.add(new_member)
        db.session.commit()
        return member_schema.jsonify(new_member), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# Get all members
@app.route('/members', methods=['GET'])
def get_members():
    members = Member.query.all()
    return members_schema.jsonify(members), 200

# Update a member
@app.route('/members/<int:id>', methods=['PUT'])
def update_member(id):
    member = Member.query.get(id)
    if not member:
        return jsonify({'message': 'Member not found!'}), 404

    data = request.json
    member.first_name = data.get('first_name', member.first_name)
    member.last_name = data.get('last_name', member.last_name)
    member.email = data.get('email', member.email)
    db.session.commit()
    return member_schema.jsonify(member), 200

# Delete a member
@app.route('/members/<int:id>', methods=['DELETE'])
def delete_member(id):
    member = Member.query.get(id)
    if not member:
        return jsonify({'message': 'Member not found!'}), 404

    db.session.delete(member)
    db.session.commit()
    return jsonify({'message': 'Member deleted successfully!'}), 200

# Routes for WorkoutSession CRUD Operations

# Add a new workout session
@app.route('/workouts', methods=['POST'])
def add_workout():
    data = request.json
    new_session = WorkoutSession(
        member_id=data['member_id'],
        workout_type=data['workout_type'],
        duration=data['duration'],
        session_date=get_current_time_in_timezone(data.get('timezone', 'UTC'))  # Handle time zone
    )
    try:
        db.session.add(new_session)
        db.session.commit()
        return workout_schema.jsonify(new_session), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# Get all workout sessions
@app.route('/workouts', methods=['GET'])
def get_workouts():
    sessions = WorkoutSession.query.all()
    return workouts_schema.jsonify(sessions), 200

# Update a workout session
@app.route('/workouts/<int:id>', methods=['PUT'])
def update_workout(id):
    session = WorkoutSession.query.get(id)
    if not session:
        return jsonify({'message': 'Workout session not found!'}), 404

    data = request.json
    session.workout_type = data.get('workout_type', session.workout_type)
    session.duration = data.get('duration', session.duration)
    db.session.commit()
    return workout_schema.jsonify(session), 200

# Delete a workout session
@app.route('/workouts/<int:id>', methods=['DELETE'])
def delete_workout(id):
    session = WorkoutSession.query.get(id)
    if not session:
        return jsonify({'message': 'Workout session not found!'}), 404

    db.session.delete(session)
    db.session.commit()
    return jsonify({'message': 'Workout session deleted successfully!'}), 200

# Get all workout sessions for a specific member
@app.route('/members/<int:member_id>/workouts', methods=['GET'])
def get_member_workouts(member_id):
    sessions = WorkoutSession.query.filter_by(member_id=member_id).all()
    return workouts_schema.jsonify(sessions), 200

# Initialize the database and create tables
db.create_all()

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)