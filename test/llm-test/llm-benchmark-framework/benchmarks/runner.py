from infra.llama_controller import ModelManager
from models.serv_llama import LlamaServer
import json
import time

with open("prompts/dataset.json") as f:
    prompts = json.load(f)

models = {
    "llama": "/home/elisa/Downloads/llama-2-7b-chat.Q4_K_M.gguf",
    "mistral": "/home/elisa/Downloads/mistral-7b-v0.1.Q4_K_M.gguf"
}

manager = ModelManager()
client = LlamaServer()

results = []

for name, path in models.items():

    manager.start_model(path)

    for prompt in prompts:

        start = time.time()
        output = client.generate(prompt)
        latency = time.time() - start

        results.append({
            "model": name,
            "prompt": prompt,
            "output": output,
            "latency": latency
        })

        print(f"{name} → {latency:.2f}s")

# guardar
with open("results.json", "w") as f:
    json.dump(results, f, indent=2)

print("Benchmark terminado")