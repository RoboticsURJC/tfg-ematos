# app/ui/apps/games/base_pygame_qt_screen.py

"""
@file base_pygame_qt_screen.py
@brief Clase base unificada para integrar bucles gráficos de Pygame dentro de interfaces PyQt5.
@details Abstrae el ciclo de vida y la renderización en hardware embebido (Raspberry Pi),
evitando fugas de memoria o fallos de segmentación (`Segmentation Fault`) al puentear de forma asíncrona
los búferes de píxeles mediante matrices contiguas de NumPy hacia un control QLabel de Qt.
"""

import numpy as np
import pygame

from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QSizePolicy
from PyQt5.QtCore    import QTimer, Qt
from PyQt5.QtGui     import QImage, QPixmap

from app.core.logger import logger


# =========================================================================
# INICIALIZACIÓN PARCIAL DE SUBSISTEMAS PYGAME
# =========================================================================
# NOTA CRÍTICA RASPBERRY PI: Nunca invocar 'pygame.display.init()'. El control de ventanas
# lo asume el motor gráfico de Qt; inicializar el driver de vídeo de Pygame en entornos sin
# servidor X completo o con framebuffers solapados rompe el bus de memoria causando un volcado de núcleo.
pygame.font.init()
pygame.mixer.init()   ## Inicialización del mezclador de audio de bajo nivel.


class BasePygameQtScreen(QWidget):
    """
    @brief Componente contenedor intermedio que hospeda un bucle de ejecución (Game Loop) de Pygame en Qt.
    """

    def __init__(self, controller=None, width=1024, height=600):
        """
        @brief Constructor de la clase BasePygameQtScreen.
        @details Configura los layouts geométricos de estiramiento y parametriza el temporizador
        de alta precisión (`QTimer`) que asume las funciones de pulso del reloj gráfico.
        
        @param controller Instancia del controlador central o máquina de estados de la UI.
        @param width Resolución horizontal virtual nativa deseada para la lógica del juego.
        @param height Resolución vertical virtual nativa deseada para la lógica del juego.
        """
        super().__init__()

        ## Referencia al coordinador o máquina de estados de pantallas de la interfaz.
        self.controller  = controller
        
        ## Dimensión de anchura de trabajo real asignada a la superficie virtual.
        self.game_width  = width
        
        ## Dimensión de altura de trabajo real asignada a la superficie virtual.
        self.game_height = height

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        ## Superficie física de Pygame (Canvas de memoria en bruto) para el dibujado de primitivas.
        self.surface = pygame.Surface((self.game_width, self.game_height))
        
        ## Reloj interno auxiliar de Pygame utilizado exclusivamente para calcular deltas o limitar FPS lógicos.
        self.clock   = pygame.time.Clock()
        
        ## Bandera booleana de estado operativo del Game Loop.
        self.running = False
        
        ## Vector dinámico de eventos sintéticos inyectados desde el subsistema táctil de Qt hacia el juego.
        self.events  = []

        # Configuración del layout de empaquetado atómico para el estiramiento al 100%
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        ## Elemento gráfico de Qt que actúa como viewport o pantalla de proyección de los píxeles renderizados.
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.label.setStyleSheet("background: black;")
        layout.addWidget(self.label)

        ## Temporizador asíncrono de Qt que orquesta los ticks fijos del frame rate.
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)

    # ── Gestión del Ciclo de Vida ─────────────────────────────────────────────

    def start(self):
        """
        @brief Inicializa el temporizador de fotogramas y arranca la máquina de refresco lógico.
        @details Sincroniza las superficies previas y setea el intervalo a 16 milisegundos 
        (frecuencia equivalente a una tasa de refresco estándar de ~60 FPS).
        """
        self._sync_surface_size()
        self.running = True
        self.timer.start(16)
        logger.debug("[BASE PYGAME] start() - Game loop activado.")

    def stop(self):
        """
        @brief Detiene y congela de inmediato el temporizador y el procesado del juego.
        """
        self.running = False
        self.timer.stop()
        logger.debug("[BASE PYGAME] stop() - Game loop pausado.")

    # ── Rutinas de Redimensionado Adaptativo ──────────────────────────────────

    def resizeEvent(self, event):
        """
        @brief Captura las variaciones de escala físicas asignadas por el gestor de ventanas de Qt.
        
        @param event Instancia del evento nativo de tipo QResizeEvent.
        """
        super().resizeEvent(event)
        self._sync_surface_size()

    def showEvent(self, event):
        """
        @brief Intercepta la visualización inicial de la pantalla para reajustar los búferes de memoria.
        
        @param event Instancia del evento nativo de tipo QShowEvent.
        """
        super().showEvent(event)
        self._sync_surface_size()

    def _sync_surface_size(self):
        """
        @brief Reasigna y recrea de forma atómica la superficie interna de Pygame si las cotas geométricas cambian.
        """
        w = self.width()  if self.width()  > 0 else self.game_width
        h = self.height() if self.height() > 0 else self.game_height
        if w != self.game_width or h != self.game_height:
            self.game_width  = w
            self.game_height = h
            self.surface = pygame.Surface((w, h))
            logger.debug(f"[BASE PYGAME] surface redimensionada → {w}x{h}")

    # ── Núcleo del Game Loop Principal (Orquestación por Hilos de Qt) ──────────

    def _tick(self):
        """
        @brief Ejecuta una iteración unificada del ciclo del juego (Fase lógica + Fase gráfica).
        @details Se ejecuta secuencialmente bajo el hilo principal de Qt. Sincroniza y vacía el vector de 
        eventos de entrada al finalizar cada fotograma para impedir acumulaciones fantasmas de clicks táctiles.
        """
        if not self.running:
            return
        self.update_logic()
        self.render()
        self._blit_to_label()
        self.events = []   # Purgado atómico de la cola de eventos tras el render del frame
        self.clock.tick(60)

    def _blit_to_label(self):
        """
        @brief Transfiere los píxeles de la memoria de Pygame hacia el backend de dibujado de Qt.
        @details **Optimización crítica ARM:** Recupera la matriz en 3D mediante `surfarray.array3d`,
        aplica una transposición de ejes ortogonales y fuerza la copia de manera contigua en memoria 
        RAM mediante NumPy. Esto elude las corrupciones y cuelgues que provoca la rutina nativa 
        `image.tostring` bajo arquitecturas Linux aarch64.
        """
        try:
            arr = pygame.surfarray.array3d(self.surface)  # Matriz origen: (W, H, 3)
            arr = np.ascontiguousarray(np.transpose(arr, (1, 0, 2)))  # Transposición destino: (H, W, 3)
            h, w, ch = arr.shape
            
            # Envoltura directa sin copia del puntero de datos binarios
            image  = QImage(arr.data, w, h, w * ch, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(image).scaled(
                self.label.width(), self.label.height(),
                Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.label.setPixmap(pixmap)
        except Exception as exc:
            logger.error(f"[BASE PYGAME] Error crítico en la rutina _blit_to_label: {exc}")

    # ── Puertos de Entrada: Traducción de Señales Qt a Estructuras Pygame ──────

    def mousePressEvent(self, qt_event):
        """
        @brief Intercepta la pulsación táctil/ratón de Qt y genera un evento sintético homólogo para Pygame.
        
        @param qt_event Instancia del evento nativo de tipo QMouseEvent.
        """
        pos = (qt_event.x(), qt_event.y())
        # Corrección de desfase geométrico por bandas negras en el escalado (Letterbox)
        pos = self._qt_to_game_pos(pos)
        pg_event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            {"pos": pos, "button": qt_event.button()}
        )
        self.events.append(pg_event)
        super().mousePressEvent(qt_event)

    def keyPressEvent(self, qt_event):
        """
        @brief Mapea y traduce las pulsaciones del teclado del core de Qt a flags constantes de Pygame.
        
        @param qt_event Instancia del evento nativo de tipo QKeyEvent.
        """
        from PyQt5.QtCore import Qt as QtConst
        key_map = {
            QtConst.Key_Escape: pygame.K_ESCAPE,
            QtConst.Key_Return: pygame.K_RETURN,
            QtConst.Key_Space:  pygame.K_SPACE,
        }
        pg_key = key_map.get(qt_event.key(), 0)
        if pg_key:
            pg_event = pygame.event.Event(pygame.KEYDOWN, {"key": pg_key})
            self.events.append(pg_event)
        super().keyPressEvent(qt_event)

    def _qt_to_game_pos(self, pos):
        """
        @brief Ejecuta una transformación lineal inversa para corregir las coordenadas físicas del widget.
        @details Si el contenedor QLabel activa el modo de escalado manteniendo la relación de aspecto 
        (`KeepAspectRatio`), se calculan los offsets espaciales (márgenes muertos o bandas negras) para 
        calcular el píxel real exacto sobre la superficie virtual interna de Pygame.
        
        @param pos Tupla numérica `(x, y)` con las coordenadas brutas recogidas del widget de Qt.
        @return tupla Coordenadas equivalentes calculadas en la matriz interna de dibujo `(x_game, y_game)`.
        """
        lw = self.label.width()
        lh = self.label.height()
        gw = self.game_width
        gh = self.game_height

        # Ratio de escala calculado por el algoritmo de Qt
        scale = min(lw / gw, lh / gh)
        rendered_w = int(gw * scale)
        rendered_h = int(gh * scale)

        # Cálculo de los márgenes muertos superiores y laterales (Offsets)
        ox = (lw - rendered_w) // 2
        oy = (lh - rendered_h) // 2

        x = int((pos[0] - ox) / scale)
        y = int((pos[1] - oy) / scale)

        # Restricción por acotamiento (Clamp) para mitigar desbordamientos fuera de la superficie útil
        x = max(0, min(x, gw - 1))
        y = max(0, min(y, gh - 1))
        return (x, y)

    # ── Métodos Virtuales Puros (Interfaces de Extensión) ─────────────────────

    def update_logic(self):
        """
        @brief Método virtual. Debe ser sobrescrito por la subclase para procesar la lógica, físicas o colisiones del juego.
        """
        pass

    def render(self):
        """
        @brief Método virtual. Debe ser sobrescrito por la subclase para inyectar los comandos de dibujo sobre `self.surface`.
        """
        pass