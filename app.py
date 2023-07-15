from flask import Flask, render_template, jsonify, request, redirect, session, flash
from pymongo import MongoClient
from bson import ObjectId
from babel.numbers import format_decimal
from pymongo.operations import InsertOne, DeleteMany
from jsonschema import validate, ValidationError
from flask_json_schema import JsonSchema , JsonValidationError
from pymongo.errors import BulkWriteError

app = Flask(__name__)
app.secret_key = 'harissofyan'
schema = JsonSchema(app)

# Connect to the MongoDB server
uri ="mongodb+srv://haris:haris@cluster0.c4chfsx.mongodb.net/?retryWrites=true&w=majority"
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
    total_count = collection.count_documents({})

    pipeline = [
        {
            '$group': {
                '_id': None,
                'total': {'$sum': '$nominal'}
            }
        }
    ]

    result = list(collection.aggregate(pipeline))

    total_sum = 0
    if result:
        total_sum = result[0]['total']

    # Comparison Query
    comparison_pipeline = [
        {
            '$match': {
                'transaksi': 'Pemasukan',  # Filter transaksi pemasukan
                'nominal': {'$gt': 0}  # Filter nominal yang lebih besar dari 0
            }
        },
        {
            '$group': {
                '_id': None,
                'avg_nominal': {'$avg': '$nominal'}  # Menghitung rata-rata nominal
            }
        }
    ]

    comparison_result = list(collection.aggregate(comparison_pipeline))

    avg_nominal = 0
    if comparison_result:
        avg_nominal = comparison_result[0]['avg_nominal']
        avg_nominal_formatted = format_decimal(avg_nominal, format='#,##0.00')
    else:
        avg_nominal_formatted = '0.00'


    return render_template('data.html', username_pengguna=username_pengguna, data_input=data_input, int=int,
                           total_count=total_count, total_sum=total_sum, avg_nominal_formatted=avg_nominal_formatted)

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
            'Username or password is incorrect'
            return redirect('/')
    else:
        if 'user_id' in session:
            return redirect('/data')
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

        if transaksi == 'Pemasukan':
            nominal = abs(nominal)  # Mengubah nilai nominal menjadi positif
        elif transaksi == 'Pengeluaran':
            nominal = -abs(nominal)  # Mengubah nilai nominal menjadi negatif

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
                    'nominal': {'type': 'number'}
                },
                'required': ['tanggal', 'transaksi', 'nama', 'ukm', 'email', 'nomor_hp', 'nominal']
            })
        except ValidationError as e:    
            return jsonify({'message': 'Invalid data', 'error': str(e)}), 400

        collection.insert_one(data)

        return redirect('/data')

    return render_template('tambah_data.html')
@app.route('/hapus/<data_id>', methods=['POST'])
def hapus_data(data_id):
    data = collection.find_one({'_id': ObjectId(data_id)})
    if data is not None:
        collection.delete_one({'_id': ObjectId(data_id)})
        return redirect('/data')
    else:
        return render_template('data.html', data_id=data_id)

@app.route('/update/<data_id>', methods=['POST', 'GET'])
def update_data(data_id):
    perbaiki_data = collection.find_one({'_id': ObjectId(data_id)})
    if perbaiki_data is None:
        return render_template('data.html', data_id=data_id)

    if request.method == 'POST':
        updated_data = request.form
        new_name = updated_data.get('updateName')
        new_ukm = updated_data.get('updateUkm')
        new_jenis = updated_data.get('updateJenis')
        new_tanggal = updated_data.get('updateTanggal')
        new_nominal = int(updated_data.get('updateNominal'))
        if new_jenis == 'Pemasukan':
            new_nominal = abs(new_nominal)  # Mengubah nilai nominal menjadi positif
        elif new_jenis == 'Pengeluaran':
            new_nominal = -abs(new_nominal)  # Mengubah nilai nominal menjadi negatif

        collection.update_one(
            {'_id': ObjectId(data_id)},
            {'$set': {
                'nama': new_name,
                'ukm': new_ukm,
                'transaksi': new_jenis,
                'tanggal': new_tanggal,
                'nominal': new_nominal
            }}
        )

        return redirect('/data')

    return render_template('data.html', perbaiki_data=perbaiki_data)
@app.route('/data_banyak')
def tambah_banyak():
    return render_template('tambah_banyak.html')

@app.route('/proses', methods=['POST'])
def proses():
    nama = request.form.getlist('nama[]')
    ukm = request.form.getlist('ukm[]')
    jenis = request.form.getlist('jenis[]')
    tanggal = request.form.getlist('tanggal[]')
    nominal = request.form.getlist('nominal[]')

    bulk_operations = []
    for i in range(len(nama)):
        if jenis[i] == 'Pemasukan':
            nominal[i] = abs(int(nominal[i]))  # Mengubah nilai nominal menjadi positif
        elif jenis[i] == 'Pengeluaran':
            nominal[i] = -abs(int(nominal[i]))  # Mengubah nilai nominal menjadi negatif

        data = {
            'nama': nama[i],
            'ukm': ukm[i],
            'transaksi': jenis[i],
            'tanggal': tanggal[i],
            'nominal': nominal[i]
        }
        bulk_operations.append(data)

    try:
        # Membangun query untuk filtering data
        query = {
            '$and': [
                {'transaksi': 'Pengeluaran'},  # Filter jenis transaksi pengeluaran
                {'nominal': {'$lte': -500000}}  # Filter pengeluaran tidak boleh melebihi -500000 (negatif karena pengeluaran)
            ]
        }
        # Melakukan operasi logical query dengan menggunakan bulk_write
        requests = [InsertOne(data) for data in bulk_operations]
        requests.append(DeleteMany(query))  # Contoh operasi logical query: menghapus data yang memenuhi kondisi logika
        result = collection.bulk_write(requests)

        if result.deleted_count > 0:
            flash('Beberapa data pengeluaran melebihi 500.000 dan telah dihapus.', 'warning')
        else:
            flash('Data berhasil disimpan dan diproses.', 'success')

        return redirect('/data')
    except BulkWriteError as e:
        return "Terjadi kesalahan saat menyimpan data"
    
@app.route('/search', methods=['GET'])
def logic():
    return render_template('search_logic.html')

if __name__ == '__main__':
    check_database_connection()
    app.run(host='10.34.1.225', port=5000, debug=True)

