# Importar módulo lex de PLY para crear el analizador léxico
import ply.lex as lex

# Definir listas vacías para almacenar descripciones de errores y errores léxicos
errores_Desc = []
lista_errores_lexicos = []

# Definir un método para limpiar las listas de errores
def limpiar_errores_lex():
    global errores_Desc
    global lista_errores_lexicos
    errores_Desc = []  # Limpiar lista de descripciones de errores
    lista_errores_lexicos = []  # Limpiar lista de errores léxicos

# Definir la lista de tokens que serán reconocidos por el analizador léxico
tokens = [
    'SUMA', 'RESTA', 'DIVISION', 'MULTIPLICACION',
    'ASIGNACION', 'IGUAL', 'DIFERENTE', 'MAYORQUE', 'MENORQUE', 
    'MENORIGUAL', 'MAYORIGUAL', 'PUNTO', 'COMA', 'PUNTOCOMA',
    'COMILLASIMPLE', 'COMILLADOBLE', 'PARENTESIS_A', 'PARENTESIS_B', 'LLAVE_A',
    'LLAVE_C', 'CORCHETE_A', 'CORCHETE_B', 'MASMAS', 'MENOSMENOS', 'AND', 'OR', 'NOT', 
    'BEGIN', 'END', 'TRUE', 'FALSE', 'IMPORT', 'FUN', 'FROM', 
    'WHILE', 'FOR', 'IF', 'ELSE', 'RETURN', 
    'INT', 'BOOL', 'STG', 'REAL', 'ID', 'NUMERO', 'CADENA',
    # Definir tokens para movimientos
    'MOVERADELANTE','MOVERATRAS', 'GIRARIZQUIERDA', 'GIRARDERECHA', 'DETENER', 'VELOCIDAD', 
    # Definir tokens para sensores y datos obtenidos
    'SENSORTEMPERATURA', 'SENSORHUMEDAD', 'SENSORPH', 'SENSORPESO',  'SENSORCONTADOR',
    'GIRASENSORES', 'MEDIRALTURA', 'MEDIRGLOSOR', 'MEDIRCE', 'REVISARCOLOR', 'REVISARTAMANO',
    'TEMPERATURA', 'HUMEDAD', 'PH', 'PESO', 'CE', 'COLOR', 'COLORRGB', 'COLORHEX', 'TAMANO', 'RANGOTEMP', 'RANGOHUMEDAD', 'RANGOPH',
    # Definir tokens para comparaciones
    'COMPARARTEMP', 'COMPARARHUMEDAD', 'COMPARARPH', 
    # Definir tokens para control y cuidado
    'CONTROLPLAGAS', 'INSECTICIDA', 'FUNGICIDA', 'ASPERSION', 'APLICAR', 'REGISTRAR',
    # Definir tokens para fertilización
    'FERTILIZANTE', 'COMPOSTA', 'CAL', 'AZUFRE', 'CENIZAS', 'TURBA',
    # Definir tokens para monitoreo
    'MUESTRATIERRA', 'PLANTA', 'ALERTA',
]

# Método para manejar identificadores no válidos
def t_IDError(t):
    # Expresión regular para identificar un patrón incorrecto en los identificadores
    r'\d+[a-zA-ZñÑ][a-zA-Z0-9ñÑ]*'
    global errores_Desc
    # Calcular la columna donde se encuentra el error
    columna = t.lexpos - t.lexer.lexdata.rfind('\n', 0, t.lexpos)
    # Agregar la descripción del error a la lista de errores
    errores_Desc.append("Identificador NO válido en la línea " + str(t.lineno) + ", en columna " + str(columna))

# Ignorar espacios y tabulaciones
t_ignore = ' \t'

# Definir la expresión regular para cada token
t_SUMA = r'\+'  # Operador suma
t_RESTA = r'\-'  # Operador resta
t_DIVISION = r'\/'  # Operador división
t_MULTIPLICACION = r'\*'  # Operador multiplicación
t_ASIGNACION = r'\='  # Operador asignación
t_IGUAL = r'\=='  # Operador igual
t_DIFERENTE = r'\!='  # Operador diferente
t_MAYORQUE = r'\>'  # Operador mayor que
t_MENORQUE = r'\<'  # Operador menor que
t_MENORIGUAL = r'\<='  # Operador menor o igual
t_MAYORIGUAL = r'\>='  # Operador mayor o igual
t_PUNTO = r'\.'  # Punto
t_COMA = r'\,'  # Coma
t_PUNTOCOMA = r'\;'  # Punto y coma
t_COMILLASIMPLE = r'\''  # Comillas simples
t_COMILLADOBLE = r'\"'  # Comillas dobles
t_PARENTESIS_A = r'\('  # Paréntesis izquierdo
t_PARENTESIS_B = r'\)'  # Paréntesis derecho
t_LLAVE_A = r'\{'  # Llave izquierda
t_LLAVE_C = r'\}'  # Llave derecha
t_CORCHETE_A = r'\['  # Corchete izquierdo
t_CORCHETE_B = r'\]'  # Corchete derecho
t_MASMAS = r'\+{2}'  # Operador incremento
t_MENOSMENOS = r'\-{2}'  # Operador decremento
t_AND = r'\&{2}'  # Operador lógico AND
t_OR = r'\|{2}'  # Operador lógico OR
t_NOT = r'\!'  # Operador lógico NOT

# Lista de palabras reservadas
palabras_reservadas = [
    'begin', 'end', 'true', 'false', 'import', 'fun', 'from', 
    'while', 'for', 'if', 'else', 'return', 
    'int', 'bool', 'stg', 'real', 'id', 'numero', 'cadena', 'moveradelante',
    'moveratras', 'girarizquierda', 'girarderecha', 'detener', 'velocidad', 'girasensores', 'sensortemperatura', 'sensorhumedad',
    'sensorph', 'sensorpeso', 'revisarcolor', 'revisartamano', 'controlplagas', 'insecticida', 'fungicida', 'comparar', 'planta',
    'ph', 'rangoph', 'color', 'peso', 'tamano', 'compararph', 'cal', 'azufre', 'cenizas', 'turba',
    'alerta', 'mediraltura', 'medirglosor', 'sensorcontador', 'aspersion', 'composta', 'registrar',
    'aplicar', 'fertilizante', 'temperatura', 'rangotemp', 'humedad', 'rangohumedad', 'medirce', 'ce', 'muestratierrra'
]

# Método para identificar identificadores
def t_IDENTIFICADOR(t): 
    r'[a-zA-Z][a-zA-Z0-9_]*'  # Expresión regular para identificadores válidos
    valor = t.value.lower()  # Convertir el valor del identificador a minúsculas
    if valor in palabras_reservadas:  # Verificar si el identificador es una palabra reservada
        t.type = valor.upper()  # Asignar el tipo del token a la palabra reservada
    else: 
        if any(palabra.startswith(valor) for palabra in palabras_reservadas):  # Verificar errores en palabras reservadas mal escritas
            global errores_Desc
            columna = t.lexpos - t.lexer.lexdata.rfind('\n', 0, t.lexpos)  # Calcular la columna donde se encuentra el error
            errores_Desc.append(f"Error léxico: palabra reservada mal escrita '{t.value}' en la línea {t.lineno}, en columna {columna}") 
        t.type = 'ID'  # Asignar el tipo ID si no es una palabra reservada
    return t

# Ignorar saltos de línea y actualizar el número de línea
def t_SALTOLINEA(t):
    r'\n+'  # Expresión regular para saltos de línea
    t.lexer.lineno += len(t.value)  # Incrementar el número de línea

# Método para reconocer cadenas
def t_CADENA(t):
    r'\".*?\"'  # Expresión regular para cadenas de texto
    t.lineno += t.value.count('\n')  # Incrementar por los saltos de línea dentro del token
    #t.type = 'CADENA'  # Asignar el tipo CADENA
    return t

# Método para escribir comentarios (no hacer nada)
def t_COMENTARIO(t):
    r'\#(.*?)\#'  # Expresión regular para comentarios
    pass  # No hacer nada al encontrar un comentario

# Método para reconocer números reales
def t_REAL(t):
    r'(\d+\.\d+ | \.\d+)'  # Expresión regular para números reales
    t.value = float(t.value)  # Convertir el valor a un número flotante
    return t

# Método para reconocer números enteros
def t_NUMERO(t):
    r'\d+'  # Expresión regular para números enteros
    t.value = int(t.value)  # Convertir el valor a un número entero
    return t

# Método para reconocer colores en formato RGB
def t_COLORRGB(t):
    r'rgb\(\s*(?P<R>\d{1,3})\s*,\s*(?P<G>\d{1,3})\s*,\s*(?P<B>\d{1,3})\s*\)'  # Expresión regular para colores RGB
    t.value = (int(t.lexer.match.group('R')), int(t.lexer.match.group('G')), int(t.lexer.match.group('B')))  # Extraer valores de color
    return t

# Método para reconocer colores en formato hexadecimal
def t_COLORHEX(t):
    r'\#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})'  # Expresión regular para colores hexadecimales
    t.value = t.value  # Devolver el valor tal cual
    return t

# Función para calcular la columna en la que se encuentra un token dado en el texto fuente
def calcular_columna(lexdata, lexpos):
    # Encuentra la posición de la última nueva línea ('\n') antes de la posición actual del token
    ultima_linea = lexdata.rfind('\n', 0, lexpos)
    # Si no se encuentra una nueva línea, significa que el token está en la primera línea
    if ultima_linea < 0:
        ultima_linea = -1  # Se ajusta a -1 para que el cálculo de la columna funcione correctamente
    # Retorna la posición relativa del token dentro de la línea actual
    return (lexpos - ultima_linea)

# Función que se ejecuta cuando se detecta un error léxico
def t_error(t):
    global errores_Desc  # Variable global para almacenar los errores encontrados
    # Calcula la columna donde ocurrió el error usando la función `calcular_columna`
    columna = calcular_columna(t.lexer.lexdata, t.lexpos)
    # Añade un mensaje de error descriptivo a la lista de errores
    errores_Desc.append(f"Símbolo no válido '{t.value[0]}' en la línea {t.lineno}, columna {columna}")
    # Salta el carácter no válido para que el analizador pueda continuar con el análisis
    t.lexer.skip(1)

# Construir el analizador léxico usando una lista predefinida de tokens
lexer = lex.lex()
# Inicializa el número de línea del analizador léxico en 1
lexer.lineno = 1

ambito_actual = 'global'
# Método para analizar una cadena de entrada
def analisis(cadena):
    global ambito_actual
    lexer.input(cadena)  # Proveer la cadena al analizador léxico
    tokens = []  # Lista para almacenar los tokens generados
    lexer.lineno = 1  # Iniciar en la línea 1
    for tok in lexer:  # Iterar sobre los tokens generados
        columna = tok.lexpos - cadena.rfind('\n', 0, tok.lexpos)  # Calcular la columna
        tokens.append((tok.value, tok.type, tok.lineno, columna, ambito_actual))  # Agregar el token a la lista incluyendo el ámbito
        if tok.type == 'BEGIN':
            ambito_actual = 'local'  # Cambiar el ámbito cuando se encuentra un bloque BEGIN
        elif tok.type == 'END':
            ambito_actual = 'global'  # Cambiar el ámbito cuando se encuentra un bloque END
    return tokens  

# Función para depurar el analizador léxico procesando un texto de entrada
def depurar_lexer(data):
    # Alimenta el texto de entrada al analizador léxico
    lexer.input(data)
    # Bucle infinito para procesar los tokens generados por el analizador léxico
    while True:
        # Obtiene el siguiente token del analizador
        tok = lexer.token()
        # Si no hay más tokens, se detiene el bucle
        if not tok:
            break
        # Imprime información detallada del token encontrado: tipo, valor, línea y columna
        print(f"Token: {tok.type}, Valor: {tok.value}, Línea: {tok.lineno}, Columna: {calcular_columna(lexer.lexdata, tok.lexpos)}")