TOKEN_EXPIRY_DAYS = 30 # max token unused time
CLEANUP_INTERVAL_SECONDS = 24 * 60 * 60 # how often cleanup runs

def cleanup_process():
    while True:
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=TOKEN_EXPIRY_DAYS)
        
        # --- TOKEN CLEANUP ---
        print("[CLEAN] Performing token cleanup now!")
        for filename in os.listdir(TOKENS_DIR):
            if not filename.endswith(".token"):
                continue

            path = os.path.join(TOKENS_DIR, filename)

            try:
                with open(path, "r") as f:
                    lines = f.read().splitlines()

                if len(lines) < 2:
                    # os.remove(path)
                    continue

                last_used = datetime.fromisoformat(lines[1])

                if last_used < cutoff:
                    os.remove(path)

            except Exception:
                # if file is corrupted, delete it
                try:
                    os.remove(path)
                except:
                    pass

        time.sleep(CLEANUP_INTERVAL_SECONDS)

def init_cleanupworker():
    thread = threading.Thread(target=cleanup_process, daemon=True)
    thread.start()
