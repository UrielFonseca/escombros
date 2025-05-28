import ply.lex as lex
import ply.yacc as yacc
from tkinter import *
from tkinter import filedialog,scrolledtext, ttk, messagebox
import tkinter.font as tkFont
import AnalizadorLexico as AL
from AnalizadorLexico import limpiar_errores_lex
import AnalizadorSintactico as AS
from AnalizadorSintactico import limpiar_errores
from PIL import Image, ImageTk  # Importar Pillow
import re
import os
import codigo_objeto as CO
import subprocess
import shutil

intermedio = []
parametros_unicos = []
identificadores = {}
resultados = []
resultadosSintactico = [] 

class VentanaTokens(Tk):
    def __init__(self):
        super().__init__()
        self.title("Ventana de tokens")
        # Crear Treeview
        self.tree = ttk.Treeview(self)
        self.tree["columns"] = ("Lexema", "Token", "Linea", "Columna")

        # Configurar columnas
        self.tree.column("#0", width=0, stretch=False)  # columna de índice
        self.tree.column("Lexema", anchor='center', width=100)
        self.tree.column("Token", anchor='center', width=100)
        self.tree.column("Linea", anchor='center', width=100)
        self.tree.column("Columna", anchor='center', width=100)

        # Encabezados de columnas
        self.tree.heading("#0", text="", anchor='w')
        self.tree.heading("Lexema", text="Lexema", anchor='center')
        self.tree.heading("Token", text="Token", anchor='center')
        self.tree.heading("Linea", text="Linea", anchor='center')
        self.tree.heading("Columna", text="Columna", anchor='center')

        # Insertar datos
        global resultados
        for resultado in resultados:
            self.tree.insert("", "end", text="1", values=(resultado[0], resultado[1], resultado[2], resultado[3], resultado[4]))

        # Añadir Treeview a la ventana
        self.tree.pack(expand=True, fill='both')

class VentanaIdent(Tk):
    def __init__(self):
        super().__init__()
        self.centrar_ventana1(1000, 500)
        self.title("Ventana de Identificadores")

        # Crear Treeview
        # Crear Treeview con columnas dinámicas
        global parametros_unicos
        columnas = ["Identificador", "Tipo", "Valor"] + parametros_unicos
        self.tree = ttk.Treeview(self, columns=columnas, show="headings")

        # Configurar columnas
        for col in columnas:
            self.tree.column(col, anchor='center', width=100)
            self.tree.heading(col, text=col.capitalize(), anchor='center')

        # Insertar datos en la tabla
        for var, data in identificadores.items():
            if data["tipo"] == "planta":
                valores = [var, data["tipo"], ""] + [data["parametros"].get(p, "") for p in parametros_unicos]
            else:
                valores = [var, data["tipo"], data["valor"]] + [""] * len(parametros_unicos)
            self.tree.insert("", "end", values=valores)

        # Añadir Treeview a la ventana
        self.tree.pack(expand=True, fill='both')

    def centrar_ventana1(self, ancho, alto):
        # Obtener las dimensiones de la pantalla
        pantalla_ancho = self.winfo_screenwidth()
        pantalla_alto = self.winfo_screenheight()

        # Calcular la posición x e y para centrar la ventana
        x = (pantalla_ancho - ancho) // 2
        y = (pantalla_alto - alto) // 2

        # Establecer las dimensiones de la ventana y posicionarla
        self.geometry(f'{ancho}x{alto}+{x}+{y}')

    def centrar_ventana2(self, ancho, alto):
        # Obtener las dimensiones de la pantalla
        pantalla_ancho = self.winfo_screenwidth()
        pantalla_alto = self.winfo_screenheight()

        # Calcular la posición x e y para centrar la ventana
        x = (pantalla_ancho - ancho) // 2
        y = (pantalla_alto - alto) // 2

        # Establecer las dimensiones de la ventana y posicionarla
        self.geometry(f'{ancho}x{alto}+{x}+{y}')

class VentanaIntermedio(Tk):
    def __init__(self):
        super().__init__()
        global intermedio
        self.title("Ventana de codigo intermedio")
        codigo = ttk.Label(self, text=intermedio)
        codigo.pack(expand=True)


class Compilador(Tk):
    contadorLinea = 0

    def __init__(self):
        super().__init__()
        self.centrar_ventana(800, 600)
        limpiar_errores_lex()
        self.title("Compilador => Los Escom-bros <=")
        # Cargar la imagen del logo para la barra de título
        self.create_widgets()
        self.filename = None  # Variable para almacenar el nombre del archivo actual
        self.text_editor.bind("<KeyRelease>", self.update_line_numbers_and_highlight)

        # Crear el estilo
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TButton", background="#44475a", foreground="white", borderwidth=1)
        style.configure("TFrame", background="#282c34")
        style.configure("TLabel", background="#282c34", foreground="white")
        style.configure("Treeview", background="#383c44", foreground="white", fieldbackground="#383c44")

        # Editor y consola
        self.text_editor.config(bg="#282c34", fg="white", insertbackground="white")
        self.output_console.config(bg="#282c34", fg="white")
        self.line_numbers_text.config(bg="#383c44", fg="white")
    
    def centrar_ventana(self, ancho, alto):
        # Obtener las dimensiones de la pantalla
        pantalla_ancho = self.winfo_screenwidth()
        pantalla_alto = self.winfo_screenheight()

        # Calcular la posición x e y para centrar la ventana
        x = (pantalla_ancho - ancho) // 2
        y = (pantalla_alto - alto) // 2

        # Establecer las dimensiones de la ventana y posicionarla
        self.geometry(f'{ancho}x{alto}+{x}+{y}')
    
    def create_widgets(self):
        
        imagen_mas_original = Image.open("images/mas.png")  # Abre la imagen
        imagen_mas_redimensionada = imagen_mas_original.resize((15, 15))  # Ajusta el tamaño (ancho, alto)
        
        imagen_menos_original = Image.open("images/menos.png")  # Abre la imagen
        imagen_menos_redimensionada = imagen_menos_original.resize((15, 15))  # Ajusta el tamaño (ancho, alto)

        # Convierte la imagen redimensionada a un formato compatible con Tkinter
        self.imagen_menos = ImageTk.PhotoImage(imagen_menos_redimensionada)
        self.imagen_mas = ImageTk.PhotoImage(imagen_mas_redimensionada)

        # Frame principal
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(expand=True, fill="both")

        # Frame para los botones
        self.buttons_frame = ttk.Frame(self.main_frame)
        self.buttons_frame.pack(side="top", fill="x")

        # Crear la barra de menú
        self.menu_bar = Menu(self)
        self.config(menu=self.menu_bar)  # Asignar la barra de menú a la ventana

        # Crear la pestaña "File"
        file_menu = Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=file_menu)

        # Añadir comandos a la pestaña "File"
        file_menu.add_command(label="Nuevo", command=self.nuevo_archivo)
        file_menu.add_command(label="Abrir", command=self.abrir_archivo)
        file_menu.add_command(label="Guardar", command=self.guardar_archivo)
        file_menu.add_command(label="Guardar como", command=self.guardar_como_archivo)
        file_menu.add_separator()  # Línea separadora opcional
        file_menu.add_command(label="Salir", command=self.quit)

        # Botones para compilar y ejecutar
        # self.buttons_compiler_panel = ttk.Frame(self.main_frame)
        # self.buttons_compiler_panel.pack(side="bottom", fill="x")

        self.btn_compilar = ttk.Button(self.buttons_frame, text="Compilar", command=self.compilar)
        self.btn_compilar.pack(side="left", padx=5)
        self.btn_tokens = ttk.Button(self.buttons_frame, text="Tokens", command=self.Tokens)
        self.btn_tokens.pack(side="left", padx=5)
        self.btn_ident = ttk.Button(self.buttons_frame, text="Identificadores", command=self.Ident)
        self.btn_ident.pack(side="left", padx=5)
        self.btn_inter = ttk.Button(self.buttons_frame, text="Intermedio", command=self.Intermedio)
        self.btn_inter.pack(side="left", padx=5)
        #self.btn_tokens = ttk.Button(self.buttons_frame, text="Árbol", command=self.Arbol)
        #self.btn_tokens.pack(side="left", padx=5)

        # Botones con imágenes
        self.btn_tamañoMas = ttk.Button(self.buttons_frame, image=self.imagen_mas, command=self.tamañoMas) 
        self.btn_tamañoMas.pack(side="left", padx=5)
        self.btn_tamañoMenos = ttk.Button(self.buttons_frame, image=self.imagen_menos, command=self.tamañoMenos)
        self.btn_tamañoMenos.pack(side="left", padx=5)

        # Frame para el editor de código y los números de línea
        self.editor_frame = ttk.Frame(self.main_frame)
        self.editor_frame.pack(expand=True, fill="both")

        # Editor de código
        self.text_editor = scrolledtext.ScrolledText(self.editor_frame, wrap=WORD)
        self.text_editor.pack(expand=True, fill="both", side="right")

        # Frame para los números de línea
        self.line_numbers_frame = ttk.Frame(self.editor_frame, width=30)
        self.line_numbers_frame.pack(side="left", fill="y")

        self.line_numbers_text = Text(self.line_numbers_frame, width=4, padx=5, pady=5, wrap="none", state="disabled")
        self.line_numbers_text.pack(side="left", fill="y", expand=True)

        # Consola de salida
        self.console_frame = ttk.Frame(self, width=30)
        self.console_frame.pack(expand=True, fill="both", padx=10, pady=10)

        self.output_console = scrolledtext.ScrolledText(self.console_frame, wrap=WORD)
        self.output_console.pack(expand=True, fill="both")

        # Asociar eventos
        self.text_editor.bind("<KeyRelease>", self.update_line_numbers)
        self.text_editor.bind("<MouseWheel>", self.update_line_numbers)
        self.text_editor.bind("<Button-4>", self.update_line_numbers)
        self.text_editor.bind("<Button-5>", self.update_line_numbers)
        self.text_editor.bind("<Configure>", self.update_line_numbers)
        
        # Configuración del tag antes de usarlo
        self.text_editor.tag_configure('reservadas', foreground='#00CED1')
        self.text_editor.tag_configure('reservadasproyecto', foreground='#D980F9')
        self.text_editor.tag_configure('comentarios', foreground='#2E8B57')
        self.text_editor.tag_configure('tipodato', foreground='#FF5232')
        self.text_editor.tag_configure('identificadores', foreground='#00BFFF')
        self.text_editor.tag_configure('operadores', foreground='#ADD8E6')

        self.text_editor.bind("<<Modified>>", self.resaltar_comentarios)
        self.text_editor.bind("<KeyRelease>", self.update_line_numbers_and_highlight)

    def update_line_numbers_and_highlight(self, event=None):
        self.update_line_numbers()
        self.resaltar_palabras_reservadas()
        self.resaltar_comentarios()  # Llama a la función de comentarios
        self.resaltar_operadores()  # Resalta los operadores



    def nuevo_archivo(self):
        if self.text_editor.get("1.0", END).strip():
            if self.text_editor.edit_modified():
                respuesta = messagebox.askyesnocancel("Guardar", "¿Desea guardar el archivo antes de crear uno nuevo?")
                if respuesta:
                    if not self.guardar_como_archivo():
                        return  # Si el usuario cancela el diálogo de guardado, se detiene la ejecución
                elif respuesta is None:
                    return  # Si elige cancelar en el mensaje, se detiene la ejecución
        self.text_editor.delete(1.0, END)
        self.filename = None
        self.update_line_numbers()

    def guardar_como_archivo(self):
        filename = filedialog.asksaveasfilename(defaultextension=".esc",
                                                filetypes=[("Text files", "*.esc"), ("All files", "*.*")])
        if filename:
            with open(filename, "w") as file:
                content = self.text_editor.get(1.0, END)
                file.write(content)
            self.filename = filename
            self.text_editor.edit_modified(False)
            return True
        return False  # Devuelve False si el usuario cancela el diálogo de guardado

    def abrir_archivo(self):
        filename = filedialog.askopenfilename(filetypes=[("Text files", "*.esc"), ("All files", "*.*")])
        if filename:
            with open(filename, "r") as file:
                content = file.read()
                self.text_editor.delete(1.0, END)
                self.text_editor.insert(1.0, content)
            self.filename = filename
        self.update_line_numbers()
        self.resaltar_palabras_reservadas()

    def guardar_archivo(self):
        if self.filename:
            with open(self.filename, "w") as file:
                content = self.text_editor.get(1.0, END)
                file.write(content)
            self.text_editor.edit_modified(False)
        else:
            self.guardar_como_archivo()

    def guardar_codigo_objeto(self, codigo_objeto):
        print("AVRA en:", shutil.which("avra"))
        
        if self.filename:
            nombre_base = os.path.splitext(self.filename)[0]
            archivo_asm = nombre_base + ".asm"

            # Guardar archivo ASM
            with open(archivo_asm, "w") as file:
                file.write(codigo_objeto)

            # Paso 1: Ensamblar usando AVRA
            cmd_avra = [
                "avra",
                archivo_asm
            ]
            print(f"Ejecutando: {' '.join(cmd_avra)}")
            subprocess.run(cmd_avra, check=True)

            hex_file = nombre_base + ".hex"
            if not os.path.exists(hex_file):
                # AVRA normalmente genera: nombre_base.hex en el mismo directorio
                generado = nombre_base.upper() + ".HEX"
                if os.path.exists(generado):
                    os.rename(generado, hex_file)

            print(f"HEX generado correctamente: {hex_file}")

            cmd_upload = [
                "avrdude",
                "-c", "arduino",
                "-p", "m328p",
                "-P", "COM5",
                "-b", "115200",
                "-U", f"flash:w:{hex_file}"
            ]
            print(f"Subiendo con: {' '.join(cmd_upload)}")
            subprocess.run(cmd_upload, check=True)
        else:
            self.guardar_como_archivo()
        
    def tamañoMas(self):
         # Obtiene la fuente actual del editor de texto
        font_str = app.text_editor.cget("font")
        # Crea un objeto de fuente Tkinter a partir de la cadena de la fuente
        font = tkFont.Font(font=font_str)
        # Incrementa el tamaño de la fuente
        font.configure(size=font.actual()["size"] + 2)
        # Aplica la nueva fuente al editor de texto
        app.text_editor.config(font=font)
        app.line_numbers_text.config(font=font)
        app.output_console.config(font=font)
        
        self.text_editor.config(height=1, width=1)
        self.line_numbers_text.config(height=1, width=4)
        self.console_frame.config(width=30)
        self.output_console.config(height=0.1, width=1)
        

    def tamañoMenos(self):
         # Obtiene la fuente actual del editor de texto
        font_str = app.text_editor.cget("font")
        # Crea un objeto de fuente Tkinter a partir de la cadena de la fuente
        font = tkFont.Font(font=font_str)
        # Incrementa el tamaño de la fuente
        font.configure(size=font.actual()["size"] - 2)
        # Aplica la nueva fuente al editor de texto
        app.text_editor.config(font=font)
        app.line_numbers_text.config(font=font)
        app.output_console.config(font=font)
        
        self.text_editor.config(height=1, width=1)
        self.line_numbers_text.config(height=1, width=2)
        self.output_console.config(height=0.1, width=1)

    def Tokens(self):
        app2 = VentanaTokens()
        app2.mainloop()

    def Ident(self):
        app3 = VentanaIdent()
        app3.mainloop()

    def Intermedio(self):
        app4 = VentanaIntermedio()
        app4.mainloop()

    def update_line_numbers(self, event=None):
        # Accede a lista_errores_lexicos a través de una instancia de Compilador
        error_line = AL.lista_errores_lexicos
        # Actualiza los números de línea en función del número de líneas en el editor
        lines = self.text_editor.get(1.0, "end-1c").count("\n")
        #AL.contador = self.text_editor.get(1.0, "end-1c").count("\n")+1
        #print(contador)
        self.line_numbers_text.config(state="normal")
        self.line_numbers_text.delete(1.0, "end")
        if not error_line:
            for line in range(1, lines + 2):
                self.line_numbers_text.insert("end", str(line) + "\n")
        else:
            for line in range(1, lines + 2):
                if line in error_line:
                    # Si la línea es la línea del error, establecer el color de fondo en rojo
                    self.line_numbers_text.insert("end", str(line) + "\n", 'error_line')
                else:
                    self.line_numbers_text.insert("end", str(line) + "\n")
        self.line_numbers_text.tag_configure('error_line', foreground='red')
        self.line_numbers_text.config(state="disabled")

        # Sincronizar los scrolls de los números de línea con el editor de código
        self.line_numbers_text.yview_moveto(self.text_editor.yview()[0])
        #Pinta las palabras reservadas de un color
        self.resaltar_palabras_reservadas()
    
    reservadas = ["if", "else", "while", "for", "return"]  # Palabras reservadas 
    reservadasproyecto = [#MOVIMIENTOS
    'MOVERADELANTE','MOVERATRAS', 'GIRARIZQUIERDA', 'GIRARDERECHA', 'DETENER', 'VELOCIDAD', 
    #SENSORES - DE AMBIENTE - ESPECÍFICOS - DATOS OBTENIDOS
    'SENSORTEMPERATURA', 'SENSORHUMEDAD', 'SENSORPH', 'SENSORPESO',  'SENSORCONTADOR',
    'GIRASENSORES', 'MEDIRALTURA', 'MEDIRGLOSOR', 'MEDIRCE', 'REVISARCOLOR', 'REVISARTAMANO',
    'TEMPERATURA', 'HUMEDAD', 'PH', 'PESO', 'CE', 'COLOR', 'COLORRGB', 'COLORHEX', 'TAMANO', 'RANGOTEMP', 'RANGOHUMEDAD', 'RANGOPH',
    #COMPARACIONES
    'COMPARARTEMP', 'COMPARARHUMEDAD', 'COMPARARPH', 
    #CONTROL Y CUIDADO
    'CONTROLPLAGAS', 'INSECTICIDA', 'FUNGICIDA', 'ASPERSION', 'APLICAR', 'REGISTRAR',
    #FERTILIZACIÓN
    'FERTILIZANTE', 'COMPOSTA', 'CAL', 'AZUFRE', 'CENIZAS', 'TURBA',
    #MONITOREO
    'MUESTRATIERRA', 'PLANTA', 'ALERTA',
    ]  # Categoría de palabras reservadas que tienen función con el proyecto

    identificadores = [ 'AND', 'OR', 'NOT', 'BEGIN', 'END', 'TRUE', 'FALSE', 'IMPORT', 'FUN', 'FROM']

    tipodato = ["INT", "BOOL", "STG", "REAL", "ID", "NUMERO", "CADENA", "int", "bool", "stg", "real", "id", "numero", "cadena"]
    
    def resaltar_palabras_reservadas(self, event=None):
        # Eliminar resaltado previo
        self.text_editor.tag_remove('reservadas', '1.0', 'end')
        self.text_editor.tag_remove('reservadasproyecto', '1.0', 'end')
        self.text_editor.tag_remove('tipodato', '1.0', 'end')
        self.text_editor.tag_remove('identificadores', '1.0', 'end')

        # Obtener el contenido actual del editor de texto
        codigo = self.text_editor.get("1.0", 'end-1c')
        palabras = re.finditer(r'\b\w+\b', codigo)

        for palabra_match in palabras:
            palabra = palabra_match.group()
            palabra_lower = palabra.casefold()  # Comparación insensible a mayúsculas y minúsculas
            start = f"1.0 + {palabra_match.start()} chars"
            end = f"1.0 + {palabra_match.end()} chars"

            if palabra_lower in map(str.casefold, self.reservadas):
                self.text_editor.tag_add('reservadas', start, end)

            elif palabra_lower in map(str.casefold, self.reservadasproyecto):
                self.text_editor.tag_add('reservadasproyecto', start, end)

            elif palabra_lower in map(str.casefold, self.tipodato):
                self.text_editor.tag_add('tipodato', start, end)

            elif palabra_lower in map(str.casefold, self.identificadores):
                self.text_editor.tag_add('identificadores', start, end)


    def resaltar_comentarios(self, event=None):
        # Eliminar resaltado previo
        self.text_editor.tag_remove('comentarios', '1.0', 'end')

        # Obtener el texto completo del editor
        texto = self.text_editor.get("1.0", "end-1c")

        # Define el patrón para los comentarios válidos (que comienzan y terminan con "#")
        patron_comentarios = r'#.*?#'  # Comentarios entre "#"

        # Busca los comentarios en el texto y verifica su validez
        for match in re.finditer(patron_comentarios, texto):
            # Verificar que el texto capturado por el patrón efectivamente tiene barras dobles al inicio y final
            comentario = match.group(0)
            if comentario.startswith("#") and comentario.endswith("#"):
                # Calcular las posiciones en el texto
                start = f"1.0 + {match.start()} chars"
                end = f"1.0 + {match.end()} chars"
                
                try:
                    # Agregar la etiqueta para resaltar el comentario
                    self.text_editor.tag_add('comentarios', start, end)
                except Exception as e:
                    print(f"Error al agregar etiqueta: {e}")

    def resaltar_operadores(self):
        # Limpiar resaltados previos
        self.text_editor.tag_remove('operadores', '1.0', END)
        
        # Lista de operadores a resaltar
        operadores = r'[\+\-\*/%<>=!&|^]'
        
        # Buscar operadores en el texto
        texto = self.text_editor.get("1.0", "end-1c")
        for match in re.finditer(operadores, texto):
            start_index = f"1.0 + {match.start()} chars"
            end_index = f"1.0 + {match.end()} chars"
            self.text_editor.tag_add('operadores', start_index, end_index)

    def compilar(self):
        lin = self.text_editor.get(1.0, "end-1c").count("\n")+1
        # Limpia la lista de errores antes de cada compilación
        limpiar_errores_lex()
        # Limpiar la salida de consola
        self.output_console.delete(1.0, END)

        # Obtiene todo el código del editor
        codigo = self.text_editor.get("1.0", END)

        # Reset intermediate code before compilation
        import AnalizadorSintactico as AS
        AS.codigo_intermedio.clear()

        # Realiza la compilación utilizando el analizador léxico
        global resultados
        resultados = AL.analisis(codigo)
        # Llama a update_line_numbers y pasa la lista de errores léxicos
        self.update_line_numbers()

        # Mostrar los errores léxicos en la consola de salida
        errores_lexicos = AL.errores_Desc
        for error in errores_lexicos:
            self.output_console.insert(END, error + "\n")

        # Análisis Sintáctico
        limpiar_errores()
        restSint = AS.test_parser(codigo)

        # Mostrar los errores sintácticos en la consola de salida
        errores_Sinc_Desc = AS.errores_Sinc_Desc
        for error in errores_Sinc_Desc:
            self.output_console.insert(END, error + "\n")

        errores_semanticos = AS.errores_semanticos
        for error in errores_semanticos:
            self.output_console.insert(END, error + "\n")

        global identificadores
        global parametros_unicos
        parametros_unicos = set()
        for var, data in restSint.items():
            if "parametros" in data:
                parametros_unicos.update(data["parametros"].keys())  # Agregar parámetros encontrados

        global intermedio
        intermedio = AS.codigo_intermedio.obtener_codigo()


        # Convertir a lista ordenada para mantener consistencia
        parametros_unicos = sorted(parametros_unicos)

        # Recorrer la tabla de símbolos generada por el análisis sintáctico
        for var, data in restSint.items():
            if "parametros" in data:  # Es una planta
                # Obtener valores de los parámetros (si no tiene, poner None)
                valores_parametros = {p: data["parametros"].get(p, {}).get("valor", None) for p in parametros_unicos}
                identificadores[var] = {"tipo": "planta", "parametros": valores_parametros}
            else:  # Es una variable normal
                identificadores[var] = {"tipo": data["tipo"], "valor": data["valor"]}

        objeto = CO.generar_codigo_objeto(intermedio)
        self.guardar_codigo_objeto(objeto)
        intermedio = None


if __name__ == "__main__":
    app = Compilador()
    app.mainloop()

