@app.route('/api/post-comment/', methods=['POST'])
@limiter.limit("4 per 25 seconds; 20 per 5 minutes")
def post_comment():
    COMMENTS_PATH = f'{SERVER_DIR}/messageboard/comments'
    token = request.values.get('token')
    if not token:
        token = request.cookies.get('web_login_token')

    comments_file = request.values.get('page_id')
    comment_body = request.values.get('comment_body', '').strip()

    username = user_by_token(token) if token else None
    if not username:
        return f'You must be either logged in or provide an API token in order to comment.', 401

    comments_file_path = os.path.join(COMMENTS_PATH, comments_file)
    if os.path.commonpath([COMMENTS_PATH, os.path.abspath(comments_file_path)]) != os.path.abspath(COMMENTS_PATH):
        return jsonify({'error': 'No.'}), 403
    if not os.path.exists(comments_file_path):
        if os.path.exists(f'{SERVER_DIR}/levels/{comments_file}.odslvl'):
            open(f"{comments_file_path}", "w").close()
        else:
            return f'Page does not exist or is not commentable.', 404

    if len(comment_body) > 1440:
        return f'Sorry, either the comment thread combined or your comment exceeds the limit of 1440 characters. Your comment was not posted.', 400

    # Load the forbidden cheese
    try:
        with open(f'{SERVER_DIR}/messageboard/watchyourmouth.txt', 'r') as f:
            prohibited_words = [line.strip().lower() for line in f if line.strip()]
    except FileNotFoundError:
        print(f'--- OH NO! PROBLEMS! --- \n watchyourmouth.txt: No such file or directory \n')
        return f'Internal Server Error: Profanity filter is not set up correctly. Please contact the server maintainers.', 500

    for word in prohibited_words:
        if word in comment_body.lower():
            return f'Comment contains prohibited language: "{word}"', 400

    def sanitize_comment_body(body):
        # escape HTML characters
        body = html.unescape(body)
        body = html.escape(body)

        # allow simple tags (e.g., <b>, <i>, <u>, <br>)
        body = body.replace('&lt;b&gt;', '<b>').replace('&lt;/b&gt;', '</b>')
        body = body.replace('&lt;i&gt;', '<i>').replace('&lt;/i&gt;', '</i>')
        body = body.replace('&lt;u&gt;', '<u>').replace('&lt;/u&gt;', '</u>')
        body = body.replace('&lt;br&gt;', '<br>').replace('&lt;/br&gt;', '</br>')

        # Convert URLs into HTML links
        # url_pattern = re.compile(r'(https?://[^\s]+)')
        # body = url_pattern.sub(r'<a href="\1" target="_blank">\1</a>', body)

        # convert line breaks to <br>
        body = body.replace('\n', '<br>')

        return body

    sanitized_body = sanitize_comment_body(comment_body)

    formatted_comment = f'{{{username}}} {sanitized_body}\n'

    # insert at the top of the file
    try:
        with open(comments_file_path, 'r+') as f:
            existing_content = f.read()
            f.seek(0, 0)
            f.write(formatted_comment + existing_content)
    except Exception as e:
        print(f'--- OH NO! PROBLEMS! --- \n {e} \n')
        return f'Failed to write comment: Internal Server Error', 500

    return 'Comment posted successfully!'

