from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Enum
import random
import time
import smbus
import threading

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # SQLite DB
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Import models after initializing db
# from models import sensor

# reading sensor data
# I2C Address and Commands for SHT20 Sensor
SHT20_ADDR = 0x40
TEMP_MEASURE_NO_HOLD = 0xF3
HUMI_MEASURE_NO_HOLD = 0xF5
bus = smbus.SMBus(1)

def read_temperature():
    """Reads temperature from the SHT20 sensor."""
    try:
        bus.write_byte(SHT20_ADDR, TEMP_MEASURE_NO_HOLD)
        time.sleep(0.5)  # Wait for measurement

        temp_msb = bus.read_byte(SHT20_ADDR)
        temp_lsb = bus.read_byte(SHT20_ADDR)
        temp_raw = (temp_msb << 8) | temp_lsb

        temperature = -46.85 + (175.72 * temp_raw / 65536)
        return round(temperature, 2)

    except OSError as e:
        print("I2C Communication Error:", e)
        return None

def read_humidity():
    """Reads humidity from the SHT20 sensor."""
    try:
        bus.write_byte(SHT20_ADDR, HUMI_MEASURE_NO_HOLD)
        time.sleep(0.5)  # Wait for measurement

        humi_msb = bus.read_byte(SHT20_ADDR)
        humi_lsb = bus.read_byte(SHT20_ADDR)
        humi_raw = (humi_msb << 8) | humi_lsb

        humidity = -6 + (125 * humi_raw / 65536)
        return round(humidity, 2)

    except OSError as e:
        print("I2C Communication Error:", e)
        return None

class sensor(db.Model):
    __tablename__ = 'sensor' # tells sql_alchemy to name the table in your database as sensor

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(50), nullable=False)

    fertility = db.Column(Enum('Low', 'Moderate', 'High', name='fertility_levels'), nullable=False)
    photoperiod = db.Column(Enum('Short Day Period', 'Day Neutral', name='photoperiod_types'), nullable=False)

    temperature = db.Column(db.Float)
    rainfall = db.Column(db.Float, nullable=False)
    ph = db.Column(db.Float, nullable=False)
    light_hours = db.Column(db.Float, nullable=False)
    light_intensity = db.Column(db.Float, nullable=False)
    rh = db.Column(db.Float, nullable=False)
    nitrogen = db.Column(db.Float, nullable=False)
    phosphorus = db.Column(db.Float, nullable=False)
    potassium = db.Column(db.Float, nullable=False)
    yield_field = db.Column(db.String(100), nullable=False)

    category_ph = db.Column(Enum('low_acidic', 'neutral', name='categories'), nullable=False)
    soil_type = db.Column(Enum('sandy', 'loam', name='soil_types'), nullable=False)
    season = db.Column(Enum('Summer', 'Spring', 'Fall', name='seasons'), nullable=False)

    n_ratio = db.Column(db.Float, nullable=False)
    p_ratio = db.Column(db.Float, nullable=False)
    k_ratio = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"sensor('{self.id}', '{self.name}', '{self.fertility}', '{self.photoperiod}', '{self.temperature}', '{self.rainfall}', '{self.ph}', '{self.light_hours}', '{self.light_intensity}', '{self.light_intensity}', '{self.rh}', '{self.nitrogen}', '{self.phosphorus}', '{self.potassium}', '{self.yield_field}', '{self.category_ph}', '{self.soil_type}', '{self.season}', '{self.n_ratio}', '{self.p_ratio}', '{self.k_ratio}')"
    
input_list = [555, 'Strawberry', 'Moderate', 'Day Neutral', 21, 747, 7, 13, 533, 91, 170, 118, 243, 20, 'low_acidic', 'loam', 'Summer', 10, 10, 10]

# Input for base values
input_list = [555, 'Strawberry', 'Moderate', 'Day Neutral', 21, 747, 7, 13, 533, 91, 170, 118, 243, 20, 'low_acidic', 'loam', 'Summer', 10, 10, 10]
fertility = ['Low', 'Moderate', 'High']
photoperiod = ['Short Day Period', 'Day Neutral']
category_ph = ['low_acidic', 'neutral']
soil_type = ['sandy', 'loam']
season = ['Summer', 'Spring', 'Fall']

# Background thread to read sensor and insert data every 5s
def sensor_loop():
    while True:
        with app.app_context():
            temp = read_temperature()
            hum = read_humidity()
            if temp is None or hum is None:
                continue  # skip if sensor fails
            new_entry = sensor(
                name=input_list[1],
                fertility=random.choice(fertility),
                photoperiod=random.choice(photoperiod),
                temperature=temp,
                rainfall=round(input_list[5] * random.random(), 2),
                ph=round(input_list[6] * random.random(), 2),
                light_hours=round(input_list[7] * random.random(), 2),
                light_intensity=round(input_list[8] * random.random(), 2),
                rh=hum,
                nitrogen=round(input_list[10] * random.random(), 2),
                phosphorus=round(input_list[11] * random.random(), 2),
                potassium=round(input_list[12] * random.random(), 2),
                yield_field=str(round(input_list[13] * random.random(), 2)),
                category_ph=random.choice(category_ph),
                soil_type=random.choice(soil_type),
                season=random.choice(season),
                n_ratio=round(input_list[17] * random.random(), 2),
                p_ratio=round(input_list[18] * random.random(), 2),
                k_ratio=round(input_list[19] * random.random(), 2)
            )
            db.session.add(new_entry)
            db.session.commit()
        time.sleep(5)

@app.route('/')
@app.route('/home', endpoint='home')
def index():
    sensor_data = sensor.query.all()
    return render_template('index.html', sensor_data=sensor_data)

@app.route('/monitering')
def monitering():
    last_sensor = sensor.query.order_by(sensor.id.desc()).first()
    return render_template('monitering.html', sensor_data=last_sensor)

@app.route('/weather')
def weather():
    users = sensor.query.all()
    return render_template('weather.html', users=users)

@app.route('/alerts')
def alerts():
    users = sensor.query.all()
    return render_template('alerts.html', users=users)

@app.route('/resources')
def resources():
    users = sensor.query.all()
    return render_template('resources.html', users=users)

@app.route('/api/latest')
def get_latest_data():
    last = sensor.query.order_by(sensor.id.desc()).first()
    return {
            'temperature': last.temperature,
            'humidity': last.rh,
            'ph': last.ph,
            'nitrogen': last.nitrogen,
            'phosphorus': last.phosphorus,
            'potassium': last.potassium,
            'timestamp': time.time()
    }

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    threading.Thread(target=sensor_loop, daemon=True).start()

    app.run(host='0.0.0.0', port=5000, debug=True)

