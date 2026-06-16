# app/core/runner.py

import time
from assistant.app.llm_package.core.storage import save_result

##
# @file runner.py
# @brief Orquestador de pruebas de rendimiento (benchmarking) automatizadas para modelos LLM.
# @details Diseñado para evaluar de forma secuencial y repetitiva una batería de instrucciones 
# (prompts) sobre un conjunto parametrizable de modelos de lenguaje, recopilando telemetría de latencias.
#

class BenchmarkRunner:
    """
    @brief Clase encargada de coordinar, medir y persistir los tests de estrés y velocidad de las IA.
    """

    def __init__(self, models):
        """
        @brief Constructor del ejecutor de benchmarks.
        
        @param models Lista de objetos instanciados que heredan de la interfaz base `LLMModel`.
        """
        ## Colección de modelos de lenguaje que participarán activamente en la ronda de evaluación.
        self.models = models

    def safe_run(self, model, prompt):
        """
        @brief Ejecuta de forma segura una inferencia controlando excepciones y calculando latencias.
        @details Captura marcas de tiempo Unix de alta precisión inmediatamente antes y después del 
        proceso de generación para deducir la latencia total del viaje de red (Round-Trip Time). 
        Si el modelo genera un timeout o una excepción de API, la función la encapsula limpiamente.
        
        @param model Instancia concreta del modelo de lenguaje que se va a testear.
        @param prompt Texto explícito de la instrucción o comando enviado al modelo.
        
        @return dict Diccionario estructurado con el estado de la inferencia, texto generado y telemetría.
        """
        try:
            # Captura de marca de tiempo inicial de alta resolución
            start = time.time()

            # Delegación en la interfaz nativa del modelo bajo prueba
            response, extra = model.benchmark(prompt)

            # Captura de marca de tiempo final al finalizar la descarga de la respuesta
            end = time.time()

            # Cálculo de la latencia total del subproceso en segundos
            latency = end - start

            return {
                "model": model.name,
                "prompt": prompt,
                "response": response,
                "latency_total": latency,
                "status": "OK",
            }

        except Exception as e:
            # Cláusula de salvaguarda: Previene el colapso (crash) del script ante caídas de sockets locales
            return {
                "model": model.name,
                "prompt": prompt,
                "response": None,
                "latency_total": None,
                "status": "FAILED",
                "error": str(e)
            }

    def run(self, prompts, repeats=1):
        """
        @brief Lanza y orquesta el ciclo de evaluación masiva sobre todos los prompts y modelos configurados.
        @details Estructura la ejecución mediante tres bucles anidados (`Rondas -> Prompts -> Modelos`), 
        guarda atómicamente cada resultado parcial en disco delegando en `save_result` y aplica una pausa 
        controlada (cooldown) de 500 milisegundos entre llamadas.
        
        @note El retraso de `time.sleep(0.5)` se introduce de forma estratégica para mitigar el riesgo de 
        bloqueo de IP en servidores remotos por Rate Limiting (peticiones concurrentes excesivas / RPM).
        
        @param prompts Lista de cadenas de texto con las preguntas o tests de evaluación sintáctica.
        @param repeats Número total de iteraciones completas (rondas) que se realizarán para promediar métricas.
        
        @return list Lista consolidada con todos los diccionarios de resultados generados durante la prueba.
        """
        results = []

        for i in range(repeats):
            # Trazabilidad informativa de la ronda en ejecución
            print(f"\n ROUND {i+1}/{repeats}")

            for prompt in prompts:
                # Recorta la visualización del texto en consola para no saturar los logs físicos
                print(f"\n Prompt: {prompt[:60]}...")

                for model in self.models:
                    print(f"▶ {model.name}")

                    # Ejecución aislada tolerante a fallos
                    result = self.safe_run(model, prompt)

                    # Acumular en la estructura de datos volátil en memoria
                    results.append(result)

                    # Persistencia incremental inmediata en disco (archivo JSONL)
                    save_result(result)

                    # Pequeño cooldown de seguridad para estabilizar la temperatura de la CPU o mitigar Rate Limiting
                    time.sleep(0.5)

        return results