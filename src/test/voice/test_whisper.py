import whisper

model = whisper.load_model("base")
result = model.transcribe("test.wav", language="en")

print("Texto detectado:")
print(result["text"])


