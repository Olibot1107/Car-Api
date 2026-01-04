import subprocess
import sys

tests = [
    ('test_camera.py', 'Camera Test'),
    ('test_movement.py', 'Movement Test'),
    ('test_tcp.py', 'Network Test'),
]

print("Running connectivity tests...")

for script, name in tests:
    print(f"\n--- {name} ---")
    try:
        result = subprocess.run([sys.executable, script], cwd='test', capture_output=True, text=True, timeout=10)
        print(result.stdout.strip())
        if result.returncode != 0:
            print(result.stderr.strip())
    except subprocess.TimeoutExpired:
        print("TIMEOUT")
    except Exception as e:
        print(f"ERROR: {e}")

print("\nDone.")
