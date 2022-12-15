from flask import Flask, make_response, render_template, url_for, redirect, jsonify, request
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length
from flask_bcrypt import Bcrypt
import jwt 
import datetime 
from functools import wraps
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
db_url=os.getenv("DATABASE_URL")
host = "rosie.db.elephantsql.com"
databae = "uibtguct"
user = "uibtguct"
password = "qCbrrW0C4yVjdE9cJEpgq-j-Y1hu3Tx7"

connection = psycopg2.connect(host=host, database=databae, user=user, password=password)


bcrypt = Bcrypt(app)
app.config['SECRET_KEY'] = 'thisisasecretkey'


class RegisterForm(FlaskForm):
    username = StringField(validators=[
                           InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})

    password = PasswordField(validators=[
                             InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})

    submit = SubmitField('Register')


class LoginForm(FlaskForm):
    username = StringField(validators=[
                           InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})

    password = PasswordField(validators=[
                             InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})

    submit = SubmitField('Login')


# decorator untuk kunci endpoint / authentikasi
def token_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        # token akan diparsing melalui parameter di endpoint
        token = request.args.get('token')

        # cek token ada atau tidak
        if not token:
            return jsonify({'Alert!': 'Token is missing!'}), 401

        # decode token yang diterima 
        try:
            output = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        except:
             return jsonify({'Message': 'Invalid token'}), 403
        return f(*args, **kwargs)
    return decorator



@app.route('/')
def home():
    return render_template('home.html')


@app.get('/login')
def login():
    form = LoginForm()
    return render_template('login.html', form=form)

@app.post('/login')
def login_post():
    username = str(request.form['username'])
    password = request.form['password']
    user = []
    with connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
            user = list(cursor.fetchone())
            
    if len(user) > 0 :
        if bcrypt.check_password_hash(user[1],password):
            token = jwt.encode(
                {
                    "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=5)
                }, app.config['SECRET_KEY'], algorithm="HS256"
            )
            resp = make_response(redirect(url_for('dashboard', token=token)))
            resp.set_cookie('access_token_cookie', token)
            return resp
    return redirect('/login')

@app.get('/logout')
def logout():
    resp = make_response(redirect('/login'))
    resp.set_cookie('access_token_cookie', '', max_age=0)
    return resp

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        with connection:
            with connection.cursor() as cursor:
                cursor.execute("INSERT INTO users VALUES (%s, %s)", (form.username.data, hashed_password))
                return redirect('/login')
    return render_template('register.html', form=form)


@app.route('/dashboard', methods=['GET'])
@token_required
def dashboard():  
    return render_template('dashboard.html')

@app.post('/list-kost')
def list_kost_post():
    budget = int(request.form['budget'])
    persen = int(request.form['persen'])
    kota = str(request.form['kota'])
    real_budget = (budget*persen)/100

    with connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT  nama_kost, alamat, harga_per_bulan FROM data_kost WHERE kota=%s and harga_per_bulan<=%s", (kota, real_budget))
            kosts = cursor.fetchall()
            return (kosts)

@app.post('/list-10-kost')
def list_ten_kosts():
    budget = int(request.form['budget'])
    persen = int(request.form['persen'])
    kota = str(request.form['kota'])
    real_budget = (budget*persen)/100

    with connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT  nama_kost, alamat, harga_per_bulan FROM data_kost WHERE kota=%s and harga_per_bulan<=%s LIMIT 10", (kota, real_budget))
            ten_kosts = cursor.fetchall()
    return (ten_kosts)

@app.post('/recommended-kost')
def recommended_kost():
    # luas kamar 7, fasilitas_kamar 8, fasilitas_kamar_mandi 9, fasilitas_gedung 11
    budget = int(request.form['budget'])
    kota = str(request.form['kota'])

    with connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM data_kost WHERE kota=%s and harga_per_bulan<=%s", (kota, budget))
            kosts = cursor.fetchall()

    max_area = 0
    idx_max_area = 0
    max_fas_kamar = 0
    idx_max_fas_kamar = 0
    max_fas_kamarMandi = 0
    idx_max_fas_kamarMandi = 0
    max_fas_gedung = 0
    idx_max_fas_gedung = 0

    for i in range(len(kosts)):
        kost = kosts[i]
        kamar_area = float(kost[7])
        fas_kamar = kost[8].split(',')
        fas_kamarMandi = kost[9].split(',')
        fas_gedung = kost[11].split(',')

        if kamar_area > max_area:
            max_area = kamar_area
            idx_max_area = i
        if len(fas_kamar) > max_fas_kamar:
            max_fas_kamar = len(fas_kamar)
            idx_max_fas_kamar = i
        if len(fas_kamarMandi) > max_fas_kamarMandi:
            max_fas_kamarMandi = len(fas_kamarMandi)
            idx_max_fas_kamarMandi = i
        if len(fas_gedung) > max_fas_gedung:
            max_fas_gedung = len(fas_gedung)
            idx_max_fas_gedung = i
        
    areaBased = kosts[idx_max_area]
    fasKamarBased = kosts[idx_max_fas_kamar]
    fasKamarmandiBased = kosts[idx_max_fas_kamarMandi]
    fasGedungBased = kosts[idx_max_fas_gedung]

    candidates = []
    candidates.append(areaBased)
    candidates.append(fasKamarBased)
    candidates.append(fasKamarmandiBased)
    candidates.append(fasGedungBased)

    counter = 0
    recc = candidates[0]
    for item in candidates:
        curr_freq = candidates.count(item)
        if(curr_freq > counter):
            counter = curr_freq
            recc = item

    return jsonify({
        'recc':recc,
    })


@app.get('/average-kost-city')
def avg_kost_city():
    with connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT kota, avg(harga_per_bulan) FROM data_kost GROUP BY daerah")
            data_avg = cursor.fetchall()
            return jsonify({'data':data_avg})


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5002)
