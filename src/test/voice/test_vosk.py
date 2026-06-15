import sounddevice as sd
import vosk
import queue
import json

q = queue.Queue()

def callback(indata, frames, time, status):
    if status:
        print(status)
    q.put(bytes(indata))

model = vosk.Model("/home/eli/tfg-ematos/test/voice/vosk-model-small-es-0.42")
rec = vosk.KaldiRecognizer(model, 16000)

with sd.RawInputStream(
    samplerate=48000,
    blocksize=8000,
    dtype='int16',
    channels=1,
    device=2,
    callback=callback
):
    print("🤖 Escuchando...")
    while True:
        data = q.get()

        # 48k → 16k
        data_16k = data[::3]

        if rec.AcceptWaveform(data_16k):
            result = json.loads(rec.Result())
            if result["text"]:
                print("🧠", result["text"])
        else:
            partial = json.loads(rec.PartialResult())
            if partial["partial"]:
                print("👂", partial["partial"])

