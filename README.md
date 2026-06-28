# TRABAJO DE FIN DE GRADO ELISA MATOS 

## 🧠 ESTIMULACIÓN COGNITIVA PARA PERSONAS MAYORES MEDIANTE UN ROBOT HUMANOIDE DE BAJO COSTE 

<br>

<img width="653" height="214" alt="logo" src="https://github.com/user-attachments/assets/e7dc7091-1681-443b-8a8e-35d8848d3251" />

<br>
<br>


## 🚧 Objetivos del trabajo

Este trabajo se centra en:

- 💰 Desarrollo de una solución accesible y de bajo coste.
- 🤖 Uso de un robot humanoide para la interacción humano-robot.
- 🤔 Implementación de actividades cognitivas (memoria, atención, etc.).

<br>


## 📚 Documentación 
Toda la documentación detallada (desarrollo, experimentos y resultados) está disponible en la Wiki:

**[Ver wiki del proyecto](https://github.com/RoboticsURJC/tfg-ematos/wiki)**.


La documentación del código puede consultarse en:

- **[Documentación pdf](https://github.com/RoboticsURJC/tfg-ematos/blob/main/documentacion/latex/refman.pdf)**
- **[Documentación web](https://rawcdn.githack.com/RoboticsURJC/tfg-ematos/fe2533c2c13020a1a856db6251947b0481ad50e4/documentacion/html/index.html)** 

<br>


## 🎯 Ejecucción del sistema

### Iniciar servidor backend

``` bash
uvicorn assistant.app.api_getway.main:app --reload --host 0.0.0.0 --port 3000
```

### Ejecutar la aplicación en la Raspberry Pi

``` bash
python -m app.main
```
