from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Blueprint
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
import secrets as pysecrets
from datetime import datetime
from flask_autoindex import AutoIndexBlueprint

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data/scoreboard.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

CONFIGS_DIR = os.path.join(app.root_path, 'client_configs')
ovpn_bp = Blueprint('ovpn_bp', __name__)
AutoIndexBlueprint(ovpn_bp, browse_root=CONFIGS_DIR)
app.register_blueprint(ovpn_bp, url_prefix='/ovpn_clients')

# Shared secret the ScoreBot must present when reporting poll results.
# Set this to something real via env var in docker-compose.yml — the
# default here is only for first-run local testing.
SCOREBOT_SECRET = os.environ.get('SCOREBOT_SECRET', 'change-me-scorebot-secret')

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class Team(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    # The secret string this team plants on machines they control. Never
    # shown to anyone but the team itself -- this is effectively their
    # "ownership proof", planted via whatever access the vuln grants
    # (echo $TOKEN > /opt/koth/tag).
    token = db.Column(db.String(64), unique=True, nullable=False)
    points = db.Column(db.Integer, default=0)


class Holding(db.Model):
    """Live snapshot of who currently holds each machine, per the most
    recent ScoreBot poll. Used only for display -- points themselves are
    already committed to Team.points at poll time."""
    machine = db.Column(db.String(80), primary_key=True)
    team_name = db.Column(db.String(80), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)


@login_manager.user_loader
def load_user(team_id):
    return Team.query.get(int(team_id))


@app.route('/')
def index():
    teams = Team.query.order_by(Team.points.desc()).all()
    holdings = {h.machine: h.team_name for h in Holding.query.all()}
    return render_template('index.html', teams=teams, holdings=holdings)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('username')
        password = request.form.get('password')

        if Team.query.filter_by(name=name).first():
            flash('Team name already exists')
            return redirect(url_for('register'))

        token = pysecrets.token_hex(16)
        team = Team(
            name=name,
            password_hash=generate_password_hash(password),
            token=token,
        )
        db.session.add(team)
        db.session.commit()

        # Shown exactly once. The team must copy this down before leaving
        # this page -- it's what they plant on machines to claim them.
        flash(f'Team created. YOUR TOKEN (save this, shown only once): {token}')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form.get('username')
        password = request.form.get('password')
        team = Team.query.filter_by(name=name).first()

        if team and check_password_hash(team.password_hash, password):
            login_user(team)
            return redirect(url_for('dashboard'))

        flash('Invalid team name or password')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/dashboard')
@login_required
def dashboard():
    held_by_us = [h.machine for h in Holding.query.filter_by(team_name=current_user.name)]
    all_holdings = {h.machine: h.team_name for h in Holding.query.all()}
    return render_template(
        'dashboard.html',
        token=current_user.token,
        held_by_us=held_by_us,
        all_holdings=all_holdings,
    )


@app.route('/internal/poll_result', methods=['POST'])
def poll_result():
    """Called by the ScoreBot after every polling interval. Not meant to
    be reachable by players -- protect this at the network layer too
    (internal-only network); the shared secret is defense in depth, not
    the only control."""
    if request.headers.get('X-Scorebot-Secret') != SCOREBOT_SECRET:
        return jsonify(error='unauthorized'), 403

    data = request.get_json(force=True, silent=True) or {}
    results = data.get('results', {})

    for machine, info in results.items():
        token = info.get('token')
        points = info.get('points', 1)

        team = Team.query.filter_by(token=token).first() if token else None

        holding = Holding.query.get(machine)
        if holding is None:
            holding = Holding(machine=machine)
            db.session.add(holding)
        holding.team_name = team.name if team else None
        holding.updated_at = datetime.utcnow()

        if team:
            team.points += points

    db.session.commit()
    return jsonify(status='ok')


def init_db():
    with app.app_context():
        db.create_all()


if __name__ == '__main__':
    db_path = os.path.join('data', 'scoreboard.db')
    init_db()  # create_all() is a safe no-op against existing tables
    app.run(host='0.0.0.0', port=8000)
