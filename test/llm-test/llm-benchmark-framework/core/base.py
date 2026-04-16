import time

class LLMModel:
    def __init__(self, name):
        self.name = name

    def generate(self, prompt):
        raise NotImplementedError

    def benchmark(self, prompt):
        print(f"DEBUG -> {self.__class__.__name__}")
        response, extra = self.generate(prompt)
        return response, extra