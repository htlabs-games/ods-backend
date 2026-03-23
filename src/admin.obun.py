# --- ADMIN PANEL ENDPOINT RANDOMIZER ---
words1 = ["sigma", "stinky", "epic", "swizzly", "small", "orange", "purple", "good", "bad", "ugly"]
words2 = ["bycicle", "toothbrush", "backpack", "wallet", "pillow", "calculator", "fridge", "toilet", "helicopter"]

def gen_admin_endpoint():
    return "/api/" + "-".join([
        random.choice(words1),
        random.choice(words2),
        str(random.randint(10, 99))
    ]) + "/"

ADMIN_ENDPOINT = gen_admin_endpoint()

@app.route(f'{ADMIN_ENDPOINT}', methods=['GET'])
def admin_panel():
    return f"Admin panel test. Active users: {estimated_active_users}", 200
