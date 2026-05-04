import subprocess

# Face server
face = subprocess.Popen([
    "python", "server.py"
], cwd="face_server")

# Assistant
assistant = subprocess.Popen([
    "python", "assistant.py"
], cwd="assistant")

face.wait()
assistant.wait()

