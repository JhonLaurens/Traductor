import sys
import os
import requests
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
                             QPushButton, QLabel, QProgressBar, QComboBox, QFileDialog)
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QClipboard
from transformers import pipeline

class TranslationWorker(QThread):
    finished = pyqtSignal(str)
    progress = pyqtSignal(int)

    def __init__(self, traductor, texto):
        super().__init__()
        self.traductor = traductor
        self.texto = texto

    def run(self):
        try:
            fragmentos = [self.texto[i:i+100] for i in range(0, len(self.texto), 100)]
            traduccion_completa = ""
            
            for i, fragmento in enumerate(fragmentos):
                traduccion = self.traductor(fragmento, max_length=200)[0]['translation_text']
                traduccion_completa += traduccion + " "
                self.progress.emit(int((i + 1) / len(fragmentos) * 100))
            
            self.finished.emit(traduccion_completa.strip())
        except Exception as e:
            self.finished.emit(f"Error: {str(e)}")

class TraductorInfantil(QWidget):
    def __init__(self):
        super().__init__()
        self.modelos_traduccion = {
            "Español a Inglés": "Helsinki-NLP/opus-mt-es-en",
            "Inglés a Español": "Helsinki-NLP/opus-mt-en-es",
            "Francés a Español": "Helsinki-NLP/opus-mt-fr-es",
            "Español a Francés": "Helsinki-NLP/opus-mt-es-fr"
        }
        self.traductor = None
        self.initUI()
        self.cambiar_modelo(0)

    def initUI(self):
        self.setWindowTitle('Traductor Mágico para Niños')
        self.setStyleSheet("background-color: #F0F8FF;")
        
        layout = QVBoxLayout()

        titulo = QLabel('¡Bienvenido al Traductor Mágico!')
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setFont(QFont('Arial', 18))
        titulo.setStyleSheet("color: #4B0082;")
        layout.addWidget(titulo)

        # Selector de idiomas
        self.combo_idiomas = QComboBox()
        self.combo_idiomas.addItems(self.modelos_traduccion.keys())
        self.combo_idiomas.currentIndexChanged.connect(self.cambiar_modelo)
        layout.addWidget(self.combo_idiomas)

        self.texto_entrada = QTextEdit()
        self.texto_entrada.setPlaceholderText("Escribe aquí el texto a traducir...")
        self.texto_entrada.setStyleSheet("background-color: #E6E6FA; border-radius: 10px; padding: 10px;")
        layout.addWidget(self.texto_entrada)

        self.boton_traducir = QPushButton('¡Traducir!')
        self.boton_traducir.setStyleSheet("""
            background-color: #9370DB;
            color: white;
            border-radius: 15px;
            padding: 10px;
            font-size: 16px;
        """)
        self.boton_traducir.clicked.connect(self.traducir)
        layout.addWidget(self.boton_traducir)

        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #9370DB;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #9370DB;
            }
        """)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.texto_traducido = QTextEdit()
        self.texto_traducido.setPlaceholderText("La traducción aparecerá aquí...")
        self.texto_traducido.setStyleSheet("background-color: #E6E6FA; border-radius: 10px; padding: 10px;")
        self.texto_traducido.setReadOnly(True)
        layout.addWidget(self.texto_traducido)

        # Botones de copiar y exportar
        boton_layout = QHBoxLayout()
        
        self.boton_copiar = QPushButton('Copiar Traducción')
        self.boton_copiar.clicked.connect(self.copiar_traduccion)
        boton_layout.addWidget(self.boton_copiar)
        
        self.boton_exportar = QPushButton('Exportar a TXT')
        self.boton_exportar.clicked.connect(self.exportar_a_txt)
        boton_layout.addWidget(self.boton_exportar)
        
        layout.addLayout(boton_layout)

        self.setLayout(layout)
        self.resize(400, 600)

    def cambiar_modelo(self, index):
        modelo = list(self.modelos_traduccion.values())[index]
        self.traductor = pipeline("translation", model=modelo)

    def traducir(self):
        texto = self.texto_entrada.toPlainText()
        if (texto):
            self.texto_traducido.setText("Traduciendo...")
            self.boton_traducir.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            
            self.worker = TranslationWorker(self.traductor, texto)
            self.worker.finished.connect(self.traduccion_finalizada)
            self.worker.progress.connect(self.actualizar_progreso)
            self.worker.start()
        else:
            self.texto_traducido.setText("Por favor, escribe algo para traducir primero.")

    def traduccion_finalizada(self, resultado):
        self.texto_traducido.setText(resultado)
        self.boton_traducir.setEnabled(True)
        self.progress_bar.setVisible(False)

    def actualizar_progreso(self, valor):
        self.progress_bar.setValue(valor)

    def copiar_traduccion(self):
        traduccion = self.texto_traducido.toPlainText()
        if traduccion:
            clipboard = QApplication.clipboard()
            clipboard.setText(traduccion)
            self.texto_traducido.append("\n[Texto copiado al portapapeles]")
        else:
            self.texto_traducido.setText("No hay texto para copiar.")

    def exportar_a_txt(self):
        traduccion = self.texto_traducido.toPlainText()
        if traduccion:
            dialogo = QFileDialog(self)
            opciones = dialogo.options()
            nombre_archivo, _ = dialogo.getSaveFileName(self, "Guardar Traducción", "", 
                                                        "Archivos de Texto (*.txt);;Todos los Archivos (*)", 
                                                        options=opciones)
            if nombre_archivo:
                if not nombre_archivo.endswith('.txt'):
                    nombre_archivo += '.txt'
                with open(nombre_archivo, 'w', encoding='utf-8') as archivo:
                    archivo.write(traduccion)
                self.texto_traducido.append(f"\n[Texto exportado a {nombre_archivo}]")
        else:
            self.texto_traducido.setText("No hay texto para exportar.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = TraductorInfantil()
    ex.show()
    sys.exit(app.exec())