def is_valid_username(username):
    # Valid user: no spaces, no special characters, can use uppercase letters and hyphens.
    return bool(re.match(r'^[A-Za-z0-9_-]+$', username))

def create_token(username):
    # Create a secure token for the user that will be used to log in via API requests.
    token = str(uuid.uuid4())
    token_path = os.path.join(TOKENS_DIR, f"{token}.token")
    with open(token_path, 'w') as token_file:
        token_file.write(username)
    return token

def user_by_token(token):
    # Retrieve username by token.
    token_path = os.path.join(TOKENS_DIR, f"{token}.token")

    if os.path.exists(token_path):
        if os.path.commonpath([TOKENS_DIR, os.path.abspath(token_path)]) != os.path.abspath(TOKENS_DIR):
            return None
        with open(token_path, 'r') as token_file:
            return token_file.read().strip()
    return None


@app.before_request
def log_request():
    ip_address = get_real_ip()
    user_agent = request.headers.get('User-Agent', 'Unknown')
    endpoint = request.endpoint

    with lock:
        active_users[ip_address] = time.time()

    estimated_active_users = len(active_users)
    print(f"\n[INFO] Received a request on {endpoint} from {ip_address} [{user_agent}] \n| Est. active users: {estimated_active_users} |")




@app.route('/api/register-account/', methods=['POST'])
@limiter.limit("1 per 3 seconds; 5 per day")
def register_account():
    ra_username = request.values.get('username')
    ra_email = request.values.get('email')
    ra_password = request.values.get('password')
    ra_isweb = request.form.get('isweb') == 'true'
    ra_initip = get_real_ip()

    if not all([ra_username, ra_email, ra_password]):
        if ra_isweb:
            return redirect(f'{SERVER_PROTOCOL}://{SERVER_DOMAIN}/login?e=missingreq')
        else:
            return 'Missing required fields', 400

    if not is_valid_username(ra_username):
        if ra_isweb:
            return redirect(f'{SERVER_PROTOCOL}://{SERVER_DOMAIN}/login?e=invuser')
        else:
            return 'Invalid username. It must contain letters, digits, hyphens, and underscores. It cannot contain spaces.', 400

    if len(ra_password) < 8:
        if ra_isweb:
            return redirect(f'{SERVER_PROTOCOL}://{SERVER_DOMAIN}/login?e=shortpwd')
        else:
            return jsonify({'message': 'Your password is too weak, try coming up with one that is at least 8 characters long and contains many different types of characters such as both uppercase and lowercase letters, numbers, and special symbols. Your account was not created.'}), 400

    hashed_password = generate_password_hash(ra_password)
    token = create_token(ra_username)

    data = {
        'username': ra_username,
        'email': ra_email,
        'password': hashed_password,
        'initialIP': ra_initip,
        'isWeb': ra_isweb,
        'canUpload': 'true'
    }

    # reject account creation if user file already exists
    json_file_path = os.path.join(ACCOUNTS_DIR, f'{ra_username}.json')
    if os.path.exists(json_file_path):
        if ra_isweb:
            return redirect(f'{SERVER_PROTOCOL}://{SERVER_DOMAIN}/login?e=userexists')
        else:
            return 'User already exists', 400

    try:
        with open(json_file_path, 'w') as json_file:
            json.dump(data, json_file, indent=4)
    except Exception as e:
        if ra_isweb:
            return redirect(f'{SERVER_PROTOCOL}://{SERVER_DOMAIN}/login?e=internal-error')
        else:
            print(f'--- OH NO! PROBLEMS! --- \n {e} \n')
            return f'Internal Server Error: Failed to save your account\'s data, server storage might be full.', 500

    # if account creation was successful
    if ra_isweb:
        response = make_response(redirect(f"{SERVER_PROTOCOL}://{SERVER_DOMAIN}/login/welcome-new-user.html"))
        response.set_cookie('web_login_token', token, httponly=True, secure=True, domain=f".{SERVER_DOMAIN}", samesite="Lax", max_age=90*24*60*60)  # expires in 90 days
        return response
    else:
        return jsonify({'message': f'Welcome to {SERVICE_NAME}! Users and bots will soon be required to verify their email to create an account. This is to help prevent spambot attacks.', 'token': token})

@app.route('/api/get-login-token/', methods=['POST'])
@limiter.limit("1 per 3 seconds; 10 per hour")
def login():
    username = request.values.get('username')
    password = request.values.get('password')

    if not username or not password:
        return jsonify({'message': 'Username and password are required'}), 400

    user_file_path = os.path.join(ACCOUNTS_DIR, f'{username}.json')

    if not os.path.exists(user_file_path):
        if request.form.get('isweb') == 'true':
            return redirect(f'{SERVER_PROTOCOL}://{SERVER_DOMAIN}/login?e=usernotfound')
        else:
            return jsonify({'message': 'User is seemingly non-existent'}), 401
    if os.path.commonpath([ACCOUNTS_DIR, os.path.abspath(user_file_path)]) != os.path.abspath(ACCOUNTS_DIR):
        return jsonify({'error': 'No.'}), 403

    with open(user_file_path, 'r') as user_file:
        user_data = json.load(user_file)

    # check the password
    if not check_password_hash(user_data['password'], password):
        if request.form.get('isweb') == 'true':
            return redirect(f'{SERVER_PROTOCOL}://{SERVER_DOMAIN}/login?e=wrongpwd')
        else:
            return jsonify({'message': 'Invalid password'}), 401

    # generate login token if password is correct
    token = create_token(username)

    # if client is a web browser, set token on cookie and redirect to homepage
    if request.form.get('isweb') == 'true':
        response = make_response(redirect(f"{SERVER_PROTOCOL}://{SERVER_DOMAIN}/aroundtown"))
        response.set_cookie('web_login_token', token, httponly=True, secure=True, domain=f".{SERVER_DOMAIN}", samesite="Lax", max_age=182*24*60*60)  # Expires in x days (set to about half a year here)
        return response

    # for api clients, return token as json
    return jsonify({'message': 'Login successful', 'token': token})

@app.route('/api/get-user-by-token/', methods=['POST'])
@limiter.exempt
def get_user_by_token():
    token = request.values.get('token')
    if not token:
        token = request.cookies.get('web_login_token')
    username = user_by_token(token)
    if username:
        return jsonify({'username': username})
    return jsonify({'message': 'Invalid token'}), 401

@app.route('/api/logout/', methods=['POST'])
@limiter.exempt
def logout():
    token = request.values.get('token')
    if not token:
        token = request.cookies.get('web_login_token')
    token_path = os.path.join(TOKENS_DIR, f"{token}.token")
    if os.path.exists(token_path):
        if os.path.commonpath([TOKENS_DIR, os.path.abspath(token_path)]) != os.path.abspath(TOKENS_DIR):
            return jsonify({'error': 'No.'}), 403
        os.remove(token_path)

        if request.form.get('isweb') == 'true':
            response = make_response(redirect(f"{SERVER_PROTOCOL}://{SERVER_DOMAIN}/"))
            response.delete_cookie('web_login_token')
            return response
        else:
            return jsonify({'message': 'Logout successful'})

    return jsonify({'message': 'Invalid token'}), 400

@app.route('/api/change-pwd/', methods=['POST'])
@limiter.limit("4 per hour")
def change_password():
    username = request.values.get('username')
    current_password = request.values.get('current_password')
    new_password = request.values.get('new_password')

    user_file_path = os.path.join(ACCOUNTS_DIR, f'{username}.json')
    if not os.path.exists(user_file_path):
        return jsonify({'message': 'User not found'}), 404
    if os.path.commonpath([ACCOUNTS_DIR, os.path.abspath(user_file_path)]) != os.path.abspath(ACCOUNTS_DIR):
        return jsonify({'error': 'No.'}), 403

    with open(user_file_path, 'r') as user_file:
        user_data = json.load(user_file)

    if not check_password_hash(user_data['password'], current_password):
        return jsonify({'message': 'Incorrect password'}), 401

    if len(new_password) < 8:
        return jsonify({'message': 'New password is too weak, try coming up with one that is at least 8 characters long and contains many different types of characters such as both uppercase and lowercase letters, numbers, and special symbols.'}), 400

    user_data['password'] = generate_password_hash(new_password)
    with open(user_file_path, 'w') as user_file:
        json.dump(user_data, user_file, indent=4)

    for token_file in os.listdir(TOKENS_DIR):
        if user_by_token(token_file.replace('.token', '')) == username:
            os.remove(os.path.join(TOKENS_DIR, token_file))

    if request.form.get('isweb') == 'true':
        response = make_response(redirect(f"{SERVER_PROTOCOL}://{SERVER_DOMAIN}/login?ref=pwd_change"))
        response.delete_cookie('web_login_token')
        return response

    return jsonify({'message': 'Password changed successfully'})

@app.route('/api/delete-account/', methods=['POST'])
@limiter.limit("1 per 3 seconds; 3 per day")
def delete_account():
    username = request.values.get('username')
    email = request.values.get('email')
    password = request.values.get('password')
    confirmation = request.values.get('confirmation')

    if confirmation != f"goodbye, {SERVER_DOMAIN}.":
        return jsonify({'message': 'Invalid confirmation'}), 400

    user_file_path = os.path.join(ACCOUNTS_DIR, f'{username}.json')
    if not os.path.exists(user_file_path):
        return jsonify({'message': 'User not found'}), 404
    if os.path.commonpath([ACCOUNTS_DIR, os.path.abspath(user_file_path)]) != os.path.abspath(ACCOUNTS_DIR):
        return jsonify({'error': 'No.'}), 403

    with open(user_file_path, 'r') as user_file:
        user_data = json.load(user_file)

    if user_data['email'] != email or not check_password_hash(user_data['password'], password):
        return jsonify({'message': 'Invalid credentials'}), 401

    os.remove(user_file_path)
    for token_file in os.listdir(TOKENS_DIR):
        if user_by_token(token_file.replace('.token', '')) == username:
            os.remove(os.path.join(TOKENS_DIR, token_file))

    if request.form.get('isweb') == 'true':
        response = make_response(redirect(f"{SERVER_PROTOCOL}://{SERVER_DOMAIN}/"))
        response.delete_cookie('web_login_token')
        return response

    return jsonify({'message': 'Account deleted successfully'})

@app.route('/api/get-site-bar/', methods=['POST', 'GET'])
@limiter.exempt
def get_account_data():
    token = request.cookies.get('web_login_token')

    username = user_by_token(token) if token else None
    if not username:
        return jsonify({'error': 'Unauthorized or does not have an account'}), 401

    user_file_path = os.path.join(ACCOUNTS_DIR, f'{username}.json')

    # placeholder message count. TODO: implement some sort of message system
    messages = '0'

    if os.path.exists(user_file_path):
        with open(user_file_path, 'r') as user_file:
            user_data = json.load(user_file)
    else:
        return jsonify({'error': 'User data not found'}), 404

    return jsonify({
        'username': username,
        'messages': messages,
        'canUpload': user_data.get('canUpload', True)
    })

