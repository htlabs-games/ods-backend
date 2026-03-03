# Config

#/api/search-level (search-by[text/date], query[...])
#/api/search-user (search-by[text/date], query[...])
#/api/get-frontpage (data-category[newest/bestrated/mostplayed])

def get_level_metadata(level_id):
    data_path = os.path.join(UPLOAD_FOLDER, f"{level_id}.odslvl")
    thumb_path = os.path.join(THUMB_FOLDER, f"{level_id}.webp")

    if os.path.commonpath([UPLOAD_FOLDER, os.path.abspath(data_path)]) != os.path.abspath(UPLOAD_FOLDER):
        return None

    if not os.path.exists(data_path):
        data_path = os.path.join(UPLOAD_FOLDER, f"{level_id}.stage")

    if not os.path.exists(data_path):
        return None

    try:
        with open(data_path, 'r') as f:
            json_data = json.load(f)

        if not is_valid_data_file(json_data):
            return None

        metadata_raw = json_data[2]
        metadata = json.loads(metadata_raw) if isinstance(metadata_raw, str) else metadata_raw

        # Fallbacks just in case
        name = metadata.get("name", "Unknown")
        desc = metadata.get("description", "")
        author = metadata.get("author", "Anonymous")

        thumbnail_url = f"/levels/gen-pict/{level_id}.webp" if os.path.exists(thumb_path) else None

        return {
            "id": level_id,
            "thumbnail": thumbnail_url,
            "name": name,
            "description": desc,
            "author": author,
            "download": f"/levels/{level_id}.odslvl"
        }

    except Exception as e:
        print(f"Error reading metadata for {level_id}: {e}")
        return None


def process_frontpage():
    nfp = os.path.join(INDEX_FOLDER, 'newest.txt')

    try:
        with open(nfp, 'r') as f:
            newest_ids = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        newest_ids = []

    newest_data = [
        get_level_metadata(level_id)
        for level_id in newest_ids
    ]

    newest_data = [lvl for lvl in newest_data if lvl]

    bestrated_data = []
    mostplayed_data = []

    return {
        "newest": newest_data,
        "bestrated": bestrated_data,
        "mostplayed": mostplayed_data
    }

@app.route('/api/get-frontpage/', methods=['POST', 'GET'])
def get_frontpage():
    usageString = 'data-category=[newest/bestrated/mostplayed]'
    datacat = request.values.get('data-category')

    data = process_frontpage()

    if not datacat:
        return jsonify(data), 200

    if datacat in data:
        return jsonify({datacat: data[datacat]}), 200

    return jsonify({
        'message': f'That is not a valid data category. Usage: {usageString}'
    }), 400


@app.route('/api/level-info/', methods=['POST', 'GET'])
def level_info():
    lvl = request.values.get('level')
    data_path = os.path.join(UPLOAD_FOLDER, f"{lvl}.odslvl")

    if os.path.commonpath([UPLOAD_FOLDER, os.path.abspath(data_path)]) != os.path.abspath(UPLOAD_FOLDER):
        return jsonify({'error': 'No.'}), 403
    if not lvl:
        return jsonify({'message': f'Please provide a valid level UUID to look up.'}), 400
    if not os.path.exists(data_path):
        return jsonify({'error': f'Level does not exist or is not available.'}), 404

    return get_level_metadata(lvl), 200


@app.route('/aroundtown/', defaults={'filename': 'index.html'})
@app.route('/aroundtown/<path:filename>')
def aroundtown(filename):
    AROUNDTOWN_ROOT = os.path.join(SERVER_DIR, "aroundtown")
    full_path = os.path.abspath(os.path.join(AROUNDTOWN_ROOT, filename))

    if not full_path.startswith(os.path.abspath(AROUNDTOWN_ROOT)):
        abort(403)

    if os.path.isdir(full_path):
        filename = os.path.join(filename, "index.html")
        full_path = os.path.join(AROUNDTOWN_ROOT, filename)

    if not os.path.exists(full_path):
        abort(404)

    if filename == "index.html":
        data = process_frontpage()
        return render_template(
            "aroundtown/index.html",
            newest=data["newest"],
            bestrated=data["bestrated"],
            mostplayed=data["mostplayed"]
        )
    elif filename == "play/index.html":
        level_id = request.values.get('l')
        if not level_id:
            abort(400)
        data = get_level_metadata(level_id)
        if not data:
            abort(404)
        return render_template(
            "aroundtown/play/index.html",
            banner=data["thumbnail"],
            name=data["name"],
            author=data["author"],
            description=data["description"],
            download=data["download"],
            lvlid=data["id"]
        )

    if filename.endswith(".html"):
        return render_template(f"aroundtown/{filename}")

    abort(404)

