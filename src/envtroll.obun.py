@app.route('/api/env', methods=['GET']) # env troll to send fake data to hax0rz >:D
def env_troll():
    mirrored_data = {
        "method": request.method,
        "url": request.url,
        "headers": dict(request.headers),
        "args": request.args.to_dict(),
        "form_data": request.form.to_dict(),
        "json_data": request.get_json(silent=True),
        "cookies": request.cookies,
        "remote_addr": request.remote_addr,
        "user_agent": request.user_agent.string,
    }

    print("\n--- INTRUDER ALERT! INTRUDER ALERT! THIS IS NOT A DRILL- IT'S A TEAPOT! ---")
    print(f"Method: {mirrored_data['method']}")
    print(f"URL: {mirrored_data['url']}")
    print(f"Headers: {mirrored_data['headers']}")
    print(f"Query Parameters: {mirrored_data['args']}")
    print(f"Form Data: {mirrored_data['form_data']}")
    print(f"JSON Data: {mirrored_data['json_data']}")
    print(f"Cookies: {mirrored_data['cookies']}")
    print(f"Client IP: {mirrored_data['remote_addr']}")
    print(f"User-Agent: {mirrored_data['user_agent']}")
    print("-----------------------------------------------------------------------------\n")

    try:
        with open('envtroll.txt', 'r') as f:
            content = f.read()
        return Response(content, mimetype='text/plain')
    except Exception as e:
        return f'no', 418

@app.route('/api/.env', methods=['GET'])
def env_troll_dot():
    mirrored_data = {
        "method": request.method,
        "url": request.url,
        "headers": dict(request.headers),
        "args": request.args.to_dict(),
        "form_data": request.form.to_dict(),
        "json_data": request.get_json(silent=True),
        "cookies": request.cookies,
        "remote_addr": request.remote_addr,
        "user_agent": request.user_agent.string,
    }

    print("\n--- INTRUDER ALERT! INTRUDER ALERT! THIS IS NOT A DRILL- IT'S A TEAPOT! ---")
    print(f"Method: {mirrored_data['method']}")
    print(f"URL: {mirrored_data['url']}")
    print(f"Headers: {mirrored_data['headers']}")
    print(f"Query Parameters: {mirrored_data['args']}")
    print(f"Form Data: {mirrored_data['form_data']}")
    print(f"JSON Data: {mirrored_data['json_data']}")
    print(f"Cookies: {mirrored_data['cookies']}")
    print(f"Client IP: {mirrored_data['remote_addr']}")
    print(f"User-Agent: {mirrored_data['user_agent']}")
    print("-----------------------------------------------------------------------------\n")

    try:
        with open('envtroll.txt', 'r') as f:
            content = f.read()
        return Response(content, mimetype='text/plain')
    except Exception as e:
        return f'no', 418

@app.route('/api/actuator/env', methods=['GET'])
def rickandroll():
    mirrored_data = {
        "method": request.method,
        "url": request.url,
        "headers": dict(request.headers),
        "args": request.args.to_dict(),
        "form_data": request.form.to_dict(),
        "json_data": request.get_json(silent=True),
        "cookies": request.cookies,
        "remote_addr": request.remote_addr,
        "user_agent": request.user_agent.string,
    }

    print("\n--- INTRUDER ALERT! INTRUDER ALERT! THIS IS NOT A DRILL- IT'S A TEAPOT! ---")
    print(f"Method: {mirrored_data['method']}")
    print(f"URL: {mirrored_data['url']}")
    print(f"Headers: {mirrored_data['headers']}")
    print(f"Query Parameters: {mirrored_data['args']}")
    print(f"Form Data: {mirrored_data['form_data']}")
    print(f"JSON Data: {mirrored_data['json_data']}")
    print(f"Cookies: {mirrored_data['cookies']}")
    print(f"Client IP: {mirrored_data['remote_addr']}")
    print(f"User-Agent: {mirrored_data['user_agent']}")
    print("-----------------------------------------------------------------------------\n")

    return redirect("https://www.youtube.com/watch?v=dQw4w9WgXcQ", code=302)
