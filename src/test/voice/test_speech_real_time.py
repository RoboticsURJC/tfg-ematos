import speech_recognition as sr

r = sr.Recognizer()
r.energy_threshold = 100
r.pause_threshold = 0.8
r.dynamic_energy_threshold = True

mic = sr.Microphone(device_index=2)

print("🎤 Escucha continua activada (Ctrl+C para salir)")

with mic as source:
    r.adjust_for_ambient_noise(source, duration=0.5)

    while True:
        try:
            print("🟢 Escuchando...")
            audio = r.listen(
                source,
                timeout=5,
                phrase_time_limit=4
            )

            text = r.recognize_google(audio, language="es-ES")
            print("📝 Tú:", text)

        except sr.WaitTimeoutError:
            # nadie habló
            pass

        except sr.UnknownValueError:
            print("🤷 No entendí eso")

        except sr.RequestError as e:
            print("❌ Error con Google STT:", e)

        except KeyboardInterrupt:
            print("\n👋 Saliendo...")
            break
