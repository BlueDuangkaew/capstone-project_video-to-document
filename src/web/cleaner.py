import os, time, shutil

TTL = 24 * 3600

def cleanup():
    now = time.time()
    for base in ["uploads", "output", "/tmp/jobs"]:
        if not os.path.exists(base):
            continue
        for f in os.listdir(base):
            path = os.path.join(base, f)
            if now - os.path.getmtime(path) > TTL:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)

if __name__ == "__main__":
    cleanup()
