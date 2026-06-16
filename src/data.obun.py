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

def read_index(path):
    try:
        with open(path, 'r') as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return []


def get_date_ids(date_query):
    parts = date_query.split('-')
    if len(parts) == 1:
        return None, "Date is too unspecific. Please specify a month, and optionally a day."
    if not re.fullmatch(r'^[0-9-]+$', date_query):
        return None, "That is not a date."

    ids = []
    try:
        year = parts[0]
        month = parts[1]

        if len(parts) == 2:
            month_dir = os.path.join(INDEX_FOLDER, 'created', year, month)

            if not os.path.isdir(month_dir):
                return [], None

            for filename in os.listdir(month_dir):
                if filename.endswith('.txt'):
                    ids.extend(read_index(os.path.join(month_dir, filename)))

            return list(dict.fromkeys(ids)), None

        if len(parts) == 3:
            day = parts[2]
            path = os.path.join(INDEX_FOLDER, 'created', year, month, f'{day}.txt')

            return read_index(path), None

    except Exception:
        pass

    return None, "Invalid date format. Use an ISO 8601 (e.g. YYYY-MM or YYYY-MM-DD) date."


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

def search_levels(query=None, date_query=None):
    matched_ids = None

    # date-only
    if not query and date_query:
        date_ids, err = get_date_ids(date_query)

        if err:
            return {"message": err, "results": []}

        return {
            "results": [
                get_level_metadata(level_id)
                for level_id in date_ids
                if get_level_metadata(level_id)
            ]
        }

    # search by title
    if query:
        q = sanitize_name(query.strip().lower())

        first3 = q[:3]
        last3 = q[-3:]

        starts_path = os.path.join(INDEX_FOLDER, 'startswith', f'{first3}.txt')
        ends_path = os.path.join(INDEX_FOLDER, 'endswith', f'{last3}.txt')
        starts_ids = set(read_index(starts_path))
        ends_ids = set(read_index(ends_path))

        matched_ids = list(starts_ids & ends_ids)

        # fallback: use startswith list and match loosely
        if not matched_ids:
            loose_matches = []
            for level_id in starts_ids:
                meta = get_level_metadata(level_id)

                if not meta:
                    continue

                if query.strip().lower() in meta["name"].strip().lower():
                    loose_matches.append(level_id)

            matched_ids = loose_matches

        if not matched_ids:
            return {"message": "No matches found.", "results": []}

    # filter by date
    if query and date_query:
        date_ids, err = get_date_ids(date_query)

        if err:
            return {"message": err, "results": []}

        matched_ids = [
            lvl
            for lvl in matched_ids
            if lvl in set(date_ids)
        ]

        if not matched_ids:
            return {"message": "No matches found.", "results": []}

    if not query and not date_query:
        return {"message": "Please provide a search term.", "results": []}
    else:
        return {
            "results": [
                get_level_metadata(level_id)
                for level_id in matched_ids
                if get_level_metadata(level_id)
            ]
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


@app.route('/api/search-level/', methods=['GET', 'POST'])
def search_level():
    usageString = 'q=[...] optional:date=[YYYY-MM-DD or YYYY-MM]'
    query = request.values.get('q', '').strip()
    date_query = request.values.get('date', '').strip()

    if not query and not date_query:
        return jsonify({"message": f"Please enter a search query. Usage: {usageString}"}), 400

    result = search_levels(query=query if query else None, date_query=date_query if date_query else None)

    return jsonify(result), 200


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

    # path-specific handling
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

    elif filename == "search/index.html":
        query = request.values.get('q', '')
        date_query = request.values.get('date', '')
        results = search_levels(query=query if query else None, date_query=date_query if date_query else None)

        return render_template(
            "aroundtown/search/index.html",
            query=query,
            date=date_query,
            results=results.get("results", []),
            message=results.get("message")
        )

    if filename.endswith(".html"):
        return render_template(f"aroundtown/{filename}")

    abort(404)

