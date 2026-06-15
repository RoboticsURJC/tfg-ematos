import time
from assistant.app.llm_package.core.storage import save_result


class BenchmarkRunner:
    def __init__(self, models):
        self.models = models

    # 🔥 función segura para evitar crashes
    def safe_run(self, model, prompt):
        try:
            start = time.time()

            response, extra = model.benchmark(prompt)

            end = time.time()

            latency = end - start

            return {
                "model": model.name,
                "prompt": prompt,
                "response": response,
                "latency_total": latency,
                "status": "OK",
            }

        except Exception as e:
            return {
                "model": model.name,
                "prompt": prompt,
                "response": None,
                "latency_total": None,
                "status": "FAILED",
                "error": str(e)
            }

    # 🔁 ejecución del benchmark completo
    def run(self, prompts, repeats=1):
        results = []

        for i in range(repeats):
            print(f"\n🔁 ROUND {i+1}/{repeats}")

            for prompt in prompts:
                print(f"\n📝 Prompt: {prompt[:60]}...")

                for model in self.models:
                    print(f"▶ {model.name}")

                    result = self.safe_run(model, prompt)

                    results.append(result)

                    save_result(result)

                    # 🧠 pequeño cooldown para evitar saturación
                    time.sleep(0.5)

        return results