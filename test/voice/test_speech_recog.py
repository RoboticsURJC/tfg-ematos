import speech_recognition as sr

r = sr.Recognizer()
r.energy_threshold = 100           # más sensible
r.pause_threshold = 0.8            # silencio que corta frase
r.dynamic_energy_threshold = True  # ajusta energía automáticamente

# #index 2 es el microfono
mic = sr.Microphone(device_index=2)  

with mic as source:
    r.adjust_for_ambient_noise(source, duration=0.5)
    print("Escuchando...")

    # timeout = tiempo máximo que espera a que empieces a hablar
    # phrase_time_limit = duración máxima de la grabación
    audio = r.listen(source, timeout=5, phrase_time_limit=4)

# Guarda el audio
with open("input.wav", "wb") as f:
    f.write(audio.get_wav_data())
    print("Audio guardado en input.wav")


# Carga audio grabado
with sr.AudioFile("input.wav") as source:
    audio = r.record(source)

try:
    # usar Google STT (Speech to Text)
    text = r.recognize_google(audio, language="es-ES")
    print("Texto transcrito:", text)
except sr.UnknownValueError:
    print("Google no pudo entender el audio")
except sr.RequestError as e:
    print("Error al conectarse a Google STT;", e)