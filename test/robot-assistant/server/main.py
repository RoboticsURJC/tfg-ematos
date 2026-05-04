import subprocess

if __name__ == "__main__":
    subprocess.Popen(["python3", "face_server.py"])
    subprocess.Popen(["uvicorn", "llm_server:app", "--host", "0.0.0.0", "--port", "8000"])
    
    print("Todos los servicios levantados")
    
    while True:
        pass