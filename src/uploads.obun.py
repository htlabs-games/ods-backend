# Config
UPLOAD_FOLDER = os.path.join(SERVER_DIR, 'levels')
THUMB_FOLDER = os.path.join(UPLOAD_FOLDER, 'gen-pict')
INDEX_FOLDER = os.path.join(SERVER_DIR, 'data-index/levels')
MAX_DATAINDEX_ITEMS = 100

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 33 * 1024 * 1024

os.makedirs(THUMB_FOLDER, exist_ok=True)

for subdir in ['startswith', 'endswith', 'created']:
    os.makedirs(os.path.join(INDEX_FOLDER, subdir), exist_ok=True)

ALLOWED_DATA_EXTENSIONS = {'json', 'stage', 'odslvl', 'odsmx'}
ALLOWED_THUMB_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}

def allowed_file(filename, allowed_exts):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_exts

def is_valid_data_file(data):
    if not isinstance(data, list): return False
    if len(data) < 4: return False
    if not isinstance(data[3], (int, float)): return False
    if not isinstance(data[-1], str) or not data[-1].startswith(('b', 'g', 'f', 'n')): return False
    return True

def process_thumbnail(thumb_file, dest_path):
    img = Image.open(thumb_file)
    w, h = img.size
    new_height = 128
    new_width = int(w * (new_height / h))
    img = img.resize((new_width, new_height))
    img = img.convert("RGB")
    img.save(dest_path, format='WEBP')

def sanitize_name(s):
    return re.sub(r'\W+', '_', s)

def append_to_index_files(file_id, name):
    namelower = name.strip().lower()
    safename = sanitize_name(namelower)
    first3 = safename[:3] if len(safename) >= 3 else name
    last3 = safename[-3:] if len(safename) >= 3 else name

    today = datetime.utcnow()
    created_path = os.path.join(
        INDEX_FOLDER, 'created', today.strftime('%Y'), today.strftime('%m')
    )
    os.makedirs(created_path, exist_ok=True)

    index_files = [
        os.path.join(INDEX_FOLDER, 'startswith', f'{first3}.txt'),
        os.path.join(INDEX_FOLDER, 'endswith', f'{last3}.txt'),
        os.path.join(INDEX_FOLDER, 'newest.txt'),
        os.path.join(created_path, today.strftime('%d') + '.txt')
    ]

    for path in index_files:
        try:
            with open(path, 'r') as f:
                old_lines = list(islice(f, MAX_DATAINDEX_ITEMS-1))
        except FileNotFoundError:
            old_lines = []
        new_lines = [file_id + '\n'] + old_lines
        with open(path, 'w') as f:
            f.writelines(new_lines)



@app.route('/api/upload-level/', methods=['POST'])
def upload_file():
    name = request.values.get('name')
    desc = request.values.get('description')
    token = request.values.get('token') or request.cookies.get('web_login_token')
    author = user_by_token(token)

    if not name or not desc:
        return "Missing name or description", 400

    if 'data_file' not in request.files:
        return "Missing data file", 400

    data_file = request.files['data_file']
    if data_file.filename == '' or not allowed_file(data_file.filename, ALLOWED_DATA_EXTENSIONS):
        return "Invalid data file", 400

    data_content = data_file.read()
    try:
        json_data = json.loads(data_content)
        if not is_valid_data_file(json_data):
            return "Invalid data file content", 400
    except Exception:
        return "Data file is not valid JSON", 400

    # inject metadata
    metadata = {
        "name": name,
        "description": desc,
        "author": author
    }
    json_data[2] = json.dumps(metadata, separators=(',', ':'))

    file_id = str(uuid.uuid4())
    data_path = os.path.join(UPLOAD_FOLDER, f"{file_id}.odslvl")
    with open(data_path, 'w') as f:
        json.dump(json_data, f, separators=(',', ':'))

    # thumbnail (optional)
    thumb_file = request.files.get('thumbnail')
    if thumb_file and thumb_file.filename != '':
        if not allowed_file(thumb_file.filename, ALLOWED_THUMB_EXTENSIONS):
            return "Invalid thumbnail type", 400
        thumb_path = os.path.join(THUMB_FOLDER, f"{file_id}.webp")
        try:
            process_thumbnail(thumb_file, thumb_path)
        except Exception as e:
            print(f'--- OH NO! PROBLEMS! --- \n {e} \n')
            return f"Something went wrong while processing your thumbnail :(", 500

    # index the file in data_index
    append_to_index_files(file_id, name)

    return f"Upload successful. ID: {file_id}", 200


@app.route('/api/speedtest/', methods=['POST'])
def speedtest():
    if 'file' not in request.files:
        return jsonify({'error': 'Please upload a file below 32MB to begin the speed test.'}), 400

    uploaded_file = request.files['file']

    if uploaded_file.filename == '':
        return jsonify({'error': 'Please upload a file below 32MB to begin the speed test.'}), 400

    file_data = uploaded_file.read()
    file_size = len(file_data)

    return jsonify({
        'filename': uploaded_file.filename,
        'size_bytes': file_size,
        'size_kb': round(file_size / 1024, 2),
        'message': 'File received and discarded successfully.'
    }), 200

