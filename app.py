from flask import Flask, render_template, jsonify, request, redirect, session
from pymongo import MongoClient
from bson import ObjectId
from jsonschema import validate, ValidationError
from flask_json_schema import JsonSchema , JsonValidationError

app = Flask(__name__)
app.secret_key = 'harissofyan'
schema = JsonSchema(app)

# Connect to the MongoDB server
uri = "mongodb+srv://haris:haris@cluster0.c4chfsx.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(uri)

# Select the database and collections
db = client['kasuang']
collection = db['kas']
user_collection = db['user']

# Check the database connection
def check_database_connection():
    try:
        client.admin.command('ismaster')
        print('Successfully connected to the database!')
    except Exception as e:
        print('Error connecting to MongoDB:', str(e))

@app.before_request
def before_request():
    session.permanent = True

@app.route('/data')
@app.route('/data/<user_id>')
def data(user_id=None):
    if user_id:
        session['user_id'] = user_id

    user_id = session.get('user_id')

    if user_id:
        user = user_collection.find_one({'_id': ObjectId(user_id)})
        if user and 'username' in user:
            username_pengguna = user['username']
        else:
            username_pengguna = 'Guest'
    else:
        username_pengguna = 'Guest'

    if not user_id:
        return redirect('/')

    data_input = list(collection.find())
    return render_template('data.html', username_pengguna=username_pengguna, data_input=data_input)

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.form
        username = data.get('email')
        password = data.get('password')

        user = user_collection.find_one({'username': username, 'password': password})
        if user:
            session['user_id'] = str(user['_id'])
            return redirect('/data')
        else:
            return jsonify({'message': 'Login failed'})
    else:
        return render_template('index.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect('/')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.form
        username = data.get('email')
        password = data.get('password')

        existing_user = user_collection.find_one({'username': username})
        if existing_user:
            return jsonify({'message': 'User already exists'})

        user_collection.insert_one({'username': username, 'password': password})
        return redirect('/')
    else:
        return render_template('register.html')

@app.route('/tambah_data', methods=['POST', 'GET'])
def add_data():
    if request.method == 'POST':
        data = request.form
        tanggal = data.get('bdate')
        transaksi = data.get('jenis')
        nama = data.get('name')
        ukm = data.get('ukm')
        email = data.get('email')
        nomor_hp = data.get('nomor_hp')
        nominal = int(data.get('nominal'))  # Konversi ke float

        data = {
            'tanggal': tanggal,
            'transaksi': transaksi,
            'nama': nama,
            'ukm': ukm,
            'email': email,
            'nomor_hp': nomor_hp,
            'nominal': nominal
        }

        try:
            validate(data, {
                'type': 'object',
                'properties': {
                    'tanggal': {'type': 'string'},
                    'transaksi': {'type': 'string'},
                    'nama': {'type': 'string'},
                    'ukm': {'type': 'string'},
                    'email': {'type': 'string', 'format': 'email'},
                    'nomor_hp': {'type': 'string'},
                    'nominal': {'type': 'number', 'minimum': 0}
                },
                'required': ['tanggal', 'transaksi', 'nama', 'ukm', 'email', 'nomor_hp', 'nominal']
            })
        except ValidationError as e:
            return jsonify({'message': 'Invalid data', 'error': str(e)}), 400

        collection.insert_one(data)

        return redirect('/data')

    return render_template('tambah_data.html')

if __name__ == '__main__':
    check_database_connection()
    app.run(debug=True)
