#Import módulo Sintact
import ply.yacc as yacc

#Importar lista de tokens de analizados léxico
from AnalizadorLexico import tokens
import ast

class GeneradorCodigo:
    def __init__(self):
        self.codigo = []
        self.etiquetas = 0
        self.temporales = 0
        self.plantas = {}  # Almacena información de las plantas definidas
        
    def clear(self):
        """Limpia el código intermedio y reinicia contadores"""
        self.codigo = []
        self.etiquetas = 0
        self.temporales = 0
        self.plantas = {}

    def agregar(self, instruccion, comentario=None):
        """Agrega una instrucción al código intermedio"""
        if comentario:
            self.codigo.append(f"{instruccion.ljust(30)} # {comentario}")
        else:
            self.codigo.append(instruccion)
            
    def generar_instruccion(self, op, arg1=None, arg2=None, arg3=None):
        """Genera instrucción de tres direcciones"""
        instr = f"{op}"
        if arg1 is not None: instr += f" {arg1}"
        if arg2 is not None: instr += f", {arg2}"
        if arg3 is not None: instr += f", {arg3}"
        self.agregar(instr)

    def nueva_etiqueta(self):
        """Genera una nueva etiqueta única"""
        self.etiquetas += 1
        return f"L{self.etiquetas}"

    def nuevo_temporal(self):
        """Genera un nuevo temporal único"""
        self.temporales += 1
        return f"t{self.temporales}"

    def declarar_planta(self, nombre, parametros):
        """Registra una planta con sus parámetros"""
        self.plantas[nombre.lower()] = parametros
        self.agregar(f"PLANTA {nombre}")
        
        # Generar instrucciones para cada parámetro
        for param, valor in parametros.items():
            valor_real = valor['valor']
            self.agregar(f"  {param.upper()} {valor_real}")
            
    def declaracion(self, tipo, id, valor=None):
        """Genera código para declaración de variables"""
        temp = None
        if valor is not None:
            # Si el valor es una expresión compleja, podría necesitar un temporal
            if isinstance(valor, str) and '.' in valor:  # Acceso a propiedad de planta
                partes = valor.split('.')
                planta = partes[0].lower()
                propiedad = partes[1].lower()
                temp = self.nuevo_temporal()
                self.agregar(f"{temp} = {planta}.{propiedad}")
                self.agregar(f"{tipo} {id} = {temp}")
            else:
                self.agregar(f"{tipo} {id} = {valor}")
        else:
            self.agregar(f"{tipo} {id}")
        
        return temp
            
    def asignacion(self, id, expresion):
        """Genera código para asignación de variables"""
        self.agregar(f"{id} = {expresion}")

    def condicion(self, condicion):
        """Genera código para evaluar una condición"""
        temp = self.nuevo_temporal()
        self.agregar(f"{temp} = {condicion}")
        return temp
        
    def if_inicio(self, condicion):
        """Genera código para el inicio de una estructura IF"""
        # Determinar el tipo de condición y procesarla adecuadamente
        if isinstance(condicion, bool):
            # Condición booleana directa
            cond_valor = "TRUE" if condicion else "FALSE"
            self.agregar(f"# Condición directa: {cond_valor}")
            cond_temp = self.nuevo_temporal()
            self.agregar(f"{cond_temp} = {cond_valor}")
        elif isinstance(condicion, str):
            # Condición como expresión (podría ser acceso a prop. planta o comparación)
            if '.' in condicion and ('>' in condicion or '<' in condicion or '==' in condicion or '!=' in condicion):
                # Parsear la condición
                for op in ['>', '<', '>=', '<=', '==', '!=']:
                    if op in condicion:
                        partes = condicion.split(op)
                        izq = partes[0].strip()
                        der = partes[1].strip()
                        
                        # Manejar acceso a propiedad si existe
                        if '.' in izq:
                            izq = ast.literal_eval(izq)
                            izq = "".join(izq)
                        condicion = (f"{izq} {op} {der}")
                        break
            
        etiqueta_falsa = self.nueva_etiqueta()
        self.agregar(f"IF {condicion} GOTO {etiqueta_falsa}")
        return etiqueta_falsa
        
    def if_else(self, etiqueta_falsa):
        """Genera código para la parte ELSE de una estructura IF"""
        etiqueta_fin = self.nueva_etiqueta()
        self.agregar(f"GOTO {etiqueta_fin}")
        self.agregar(f"{etiqueta_falsa}:")
        return etiqueta_fin
        
    def if_fin(self, etiqueta_fin):
        """Genera código para el final de una estructura IF"""
        self.agregar(f"{etiqueta_fin}:")
        
    def while_inicio(self, condicion):
        """Genera código para el inicio de un bucle WHILE"""
        etiq_inicio = self.nueva_etiqueta()
        etiq_fin = self.nueva_etiqueta()
        self.agregar(f"{etiq_inicio}:", f"Inicio de bucle WHILE")
        
        # Procesar condición como en if_inicio
        if isinstance(condicion, str) and ('.' in condicion):
            # Condición con acceso a propiedad de planta
            for op in ['>', '<', '>=', '<=', '==', '!=']:
                if op in condicion:
                    partes = condicion.split(op)
                    izq = partes[0].strip()
                    der = partes[1].strip()
                    
                    if '.' in izq:
                        planta_prop = izq.split('.')
                        planta = planta_prop[0].lower()
                        propiedad = planta_prop[1].lower()
                        temp_izq = self.nuevo_temporal()
                        self.agregar(f"{temp_izq} = {planta}.{propiedad}", f"Acceso a propiedad de planta")
                        izq = temp_izq
                    
                    cond_temp = self.nuevo_temporal()
                    self.agregar(f"{cond_temp} = {izq} {op} {der}", f"Evaluación de condición WHILE")
                    break
        else:
            cond_temp = self.condicion(condicion)
            
        self.agregar(f"IF {cond_temp} == FALSE GOTO {etiq_fin}", f"Evaluación de condición WHILE")
        return (etiq_inicio, etiq_fin)
        
    def while_fin(self, etiquetas):
        """Genera código para el final de un bucle WHILE"""
        etiq_inicio, etiq_fin = etiquetas
        self.agregar(f"GOTO {etiq_inicio}", f"Volver al inicio del bucle WHILE")
        self.agregar(f"{etiq_fin}:", f"Fin de bucle WHILE")
        
    def for_inicio(self, inicializacion, condicion, actualizacion):
        """Genera código para el inicio de un bucle FOR"""
        # Código de inicialización
        if inicializacion[0] == 'init':
            if 'tipo' in inicializacion[1]:
                self.declaracion(inicializacion[1]['tipo'], inicializacion[1]['id'], inicializacion[1]['valor'])
            else:
                self.asignacion(inicializacion[1]['id'], inicializacion[1]['valor'])
                
        # Etiquetas para el bucle
        etiq_inicio = self.nueva_etiqueta()
        etiq_fin = self.nueva_etiqueta()
        etiq_actu = self.nueva_etiqueta()
        
        self.agregar(f"{etiq_inicio}:", f"Inicio de bucle FOR")
        
        # Condición con manejo similar a if_inicio y while_inicio
        if isinstance(condicion[1], str) and ('.' in condicion[1]):
            # Procesamiento especial para condiciones con acceso a propiedades
            for op in ['>', '<', '>=', '<=', '==', '!=']:
                if op in condicion[1]:
                    partes = condicion[1].split(op)
                    izq = partes[0].strip()
                    der = partes[1].strip()
                    
                    if '.' in izq:
                        planta_prop = izq.split('.')
                        planta = planta_prop[0].lower()
                        propiedad = planta_prop[1].lower()
                        temp_izq = self.nuevo_temporal()
                        self.agregar(f"{temp_izq} = {planta}.{propiedad}", f"Acceso a propiedad de planta")
                        izq = temp_izq
                    
                    cond_temp = self.nuevo_temporal()
                    self.agregar(f"{cond_temp} = {izq} {op} {der}", f"Evaluación de condición FOR")
                    break
        else:
            cond_temp = self.condicion(condicion[1])
            
        self.agregar(f"IF {cond_temp} == FALSE GOTO {etiq_fin}", f"Evaluación de condición FOR")
        
        # Guardar las etiquetas y la actualización para usarlas al final
        return (etiq_inicio, etiq_actu, etiq_fin, actualizacion)
        
    def for_fin(self, info_for):
        """Genera código para el final de un bucle FOR"""
        etiq_inicio, etiq_actu, etiq_fin, actualizacion = info_for
        
        self.agregar(f"{etiq_actu}:", f"Actualización del FOR")
        
        # Código de actualización
        if actualizacion[0] == 'asignacion':
            self.asignacion(actualizacion[1], actualizacion[2])
        elif actualizacion[0] == 'incremento':
            self.agregar(f"{actualizacion[1]} = {actualizacion[1]} + 1", f"Incremento")
        elif actualizacion[0] == 'decremento':
            self.agregar(f"{actualizacion[1]} = {actualizacion[1]} - 1", f"Decremento")
            
        self.agregar(f"GOTO {etiq_inicio}", f"Volver al inicio del bucle FOR")
        self.agregar(f"{etiq_fin}:", f"Fin de bucle FOR")
        
    def mover_adelante(self, distancia):
        """Genera código para el comando MOVERADELANTE"""
        self.generar_instruccion('call', 'MOVERADELANTE', distancia)
        
    def mover_atras(self, distancia):
        """Genera código para el comando MOVERATRAS"""
        self.generar_instruccion('call', 'MOVERATRAS', distancia)
        
    def girar_izquierda(self, grados):
        """Genera código para el comando GIRARIZQUIERDA"""
        self.generar_instruccion('call', 'GIRARIZQUIERDA', grados)
        
    def girar_derecha(self, grados):
        """Genera código para el comando GIRARDERECHA"""
        self.generar_instruccion('call', 'GIRARDERECHA', grados)
        
    def girar_sensores(self, grados):
        """Genera código para el comando GIRASENSORES"""
        self.generar_instruccion('call', 'GIRASENSORES', grados)
        
    def velocidad(self, valor):
        """Genera código para el comando VELOCIDAD"""
        self.generar_instruccion('call', 'VELOCIDAD', valor)
        
    def aplicar(self, compuesto):
        """Genera código para el comando APLICAR"""
        self.generar_instruccion('call', 'APLICAR', compuesto)
        
    def aspersion(self):
        """Genera código para el comando ASPERSION"""
        self.generar_instruccion('call', 'ASPERSION')
        
    def detener(self):
        """Genera código para el comando DETENER"""
        self.generar_instruccion('call', 'DETENER')
        
    def alerta(self, mensaje):
        """Genera código para el comando ALERTA"""
        self.generar_instruccion('call', 'ALERTA', mensaje)
        
    def registrar(self, valor):
        """Genera código para el comando REGISTRAR"""
        self.generar_instruccion('call', 'REGISTRAR', valor)
        
    def acceso_propiedad_planta(self, planta, propiedad):
        """Genera código para acceso a propiedades de planta"""
        temp = self.nuevo_temporal()
        self.agregar(f"{temp} = {planta}.{propiedad}", f"Acceso a propiedad de planta")
        return temp
        
    def operacion(self, op1, operador, op2):
        """Genera código para operaciones aritméticas/lógicas"""
        temp = self.nuevo_temporal()
        self.agregar(f"{temp} = {op1} {operador} {op2}", f"Operación {operador}")
        return temp
        
    def obtener_codigo(self):
        """Devuelve el código intermedio generado"""
        return "\n".join(self.codigo)


ts = {}
codigo_intermedio = []
codigo_intermedio = GeneradorCodigo()
errores_semanticos = []
errores_Sinc_Desc = []
en_si = False
#Método para limpiar los errores
def limpiar_errores():
    global errores_Sinc_Desc
    errores_Sinc_Desc = []
    global errores_semanticos
    errores_semanticos = []
    global ts
    ts = {}
lineno = 0

precedence = (
    ('left', 'IGUAL', 'DIFERENTE'),
    ('left', 'MENORQUE', 'MENORIGUAL', 'MAYORQUE', 'MAYORIGUAL'),
    ('left', 'SUMA', 'RESTA'),
    ('left', 'MULTIPLICACION', 'DIVISION')
)

#Grámatica inicial
def p_programa(p):
    """
    programa : BEGIN bloque_codigo END
             | plantas BEGIN bloque_codigo END
    """
    if len(p) == 4:
        p[0] = ('programa', p[2])
    else:
        p[0] = (p[1], p[3])

def p_programa_error_sin_begin_o_end(p):
    """
    programa : bloque_codigo
    """
    errores_Sinc_Desc.append(f"Error: Falta declaración 'BEGIN' o 'END' en la línea: {p.lineno(1)}" )

def p_programa_error_falta_llave(p):
    """
    programa : BEGIN bloque_codigo
    """
    errores_Sinc_Desc.append("Error: Bloque de código sin cierre 'END' en la línea: " + str(p.lineno(3)))

def p_programa_error_falta_llaveinicio(p):
    """
    programa : bloque_codigo END
    """
    errores_Sinc_Desc.append("Error: Bloque de código sin inicio 'BEGIN' en la línea: " + str(p.lineno(2)))

def p_bloque_codigo(p):
    """
    bloque_codigo : LLAVE_A lista_declaraciones LLAVE_C
    """
    #Para saber qué hay dentro de las llaves
    p[0] = ("bloque_codigo",p[2])

def p_bloque_codigo_vacio(p):
    """
    bloque_codigo : LLAVE_A LLAVE_C
    """
    errores_Sinc_Desc.append("Error: Bloque de código vacío en la línea: " + str(p.lineno(1)))

#Método para lista de declaraciones
# len : obtiene longitud
def p_lista_declaraciones(p):
    """
    lista_declaraciones : declaracion
                        | si
                        | mientras
                        | FOR
                        | comando
                        | lista_declaraciones lista_declaraciones
    """
    #la última es para hacer recursiva, llamarse a sí misma
    if len(p) == 3:
        #puede haber de 2 a más declaraciones
        p[0] = p[1] + [p[2]]
    else:
        p[0] = [p[1]]

def p_declaracion(p):
    """
    declaracion : tipo ID ASIGNACION expresion PUNTOCOMA
    """
    var_type = p[1].lower()
    var_name = p[2].lower()
    value = p[4]
    global ts
    if var_name in ts:
        errores_semanticos.append(f"Error: La variable '{var_name}' ya ha sido declarada.")
    else:
        ts[var_name] = {'tipo': var_type, 'valor': value}
    
    # Verificar compatibilidad de tipos
    if isinstance(value, int) and var_type != 'int' and var_type != 'real':
        errores_semanticos.append(f"Error de tipo: '{var_name}' es {var_type}, no puede asignarse un entero.")
    elif isinstance(value, float) and var_type != 'real':
        errores_semanticos.append(f"Error de tipo: '{var_name}' es {var_type}, no puede asignarse un número real.")
    elif isinstance(value, str) and value.startswith("#") and var_type != 'color': 
        errores_semanticos.append(f"Error de tipo: '{var_name}' es {var_type}, no puede asignarse un color hexadecimal.")
    elif isinstance(value, str) and var_type != 'stg':
        errores_semanticos.append(f"Error de tipo: '{var_name}' es {var_type}, no puede asignarse una cadena.")
    elif isinstance(value, bool) and var_type != 'bool':   
        errores_semanticos.append(f"Error de tipo: '{var_name}' es {var_type}, no puede asignarse valores booleanos.")

    codigo_intermedio.declaracion(p[1], p[2], p[4])
    p[0] = ('declaracion', var_type, var_name, value)

def p_asignacion(p):
    """
    declaracion : ID ASIGNACION expresion PUNTOCOMA
    """
    var_name = p[1].lower()
    value = p[3]
    global ts
    
    # Verificar si la variable está declarada
    if var_name not in ts:
        errores_semanticos.append(f"Error: La variable '{var_name}' no ha sido declarada antes de la asignación.")
    else:
        var_type = ts[var_name]['tipo']
        
        # Verificar compatibilidad de tipos
        if isinstance(value, int) and var_type != 'int' and var_type != 'real':
            errores_semanticos.append(f"Error de tipo: '{var_name}' es {var_type}, no puede asignarse un entero.")
        elif isinstance(value, float) and var_type != 'real':
            errores_semanticos.append(f"Error de tipo: '{var_name}' es {var_type}, no puede asignarse un número real.")
        elif isinstance(value, str) and value.startswith("#") and var_type != 'color': 
            errores_semanticos.append(f"Error de tipo: '{var_name}' es {var_type}, no puede asignarse un color hexadecimal.")
        elif isinstance(value, str) and var_type != 'stg':
            errores_semanticos.append(f"Error de tipo: '{var_name}' es {var_type}, no puede asignarse una cadena.")
        elif isinstance(value, bool) and var_type != 'bool':   
            errores_semanticos.append(f"Error de tipo: '{var_name}' es {var_type}, no puede asignarse valores booleanos.")
        else:
            # Actualizar el valor de la variable en la tabla de símbolos
            ts[var_name]['valor'] = value

    p[0] = ('asignacion', var_name, value)


# ERRORES EN DECLARACIONES
def p_declaracion_error1(p):
    """
    declaracion : tipo ID ASIGNACION expresion
    """
    errores_Sinc_Desc.append("Error: Falta -> Punto y coma en la línea: " + str(p.lineno(4)))

def p_declaracion_error2(p):
    """
    declaracion : tipo ID ASIGNACION PUNTOCOMA
    """
    errores_Sinc_Desc.append("Error: Falta -> La expresión a asignar en la línea: " + str(p.lineno(2)))

def p_declaracion_error_asignacion(p):
    """
    declaracion : tipo ID expresion PUNTOCOMA
    """
    errores_Sinc_Desc.append("Error: Falta -> Operador de asignación '=' en la línea: " + str(p.lineno(3)))

def p_declaracion_error_asignacion_puntocoma(p):
    """
    declaracion : tipo ID expresion 
    """
    errores_Sinc_Desc.append("Error: Falta -> La asignación y cierre ';' en la línea: " + str(p.lineno(2)))

def p_declaracion_vacia(p):
    """
    declaracion : tipo ID
    """
    errores_Sinc_Desc.append("Error: Declaración vacía, falta asignación o punto y coma en la línea: " + str(p.lineno(2)))

# ERRORES IF - ELSE
def p_si_error(p):
    """
    si : IF PARENTESIS_A PARENTESIS_B bloque_codigo
    """
    errores_Sinc_Desc.append("Error: Falta -> Condición en la declaración 'if' en la línea: " + str(p.lineno(2)))

def p_si_error_bloque(p):
    """
    si : IF PARENTESIS_A expresion PARENTESIS_B
    """
    errores_Sinc_Desc.append("Error: Falta -> Bloque de código después de la condición en 'if' en la línea: " + str(p.lineno(1)))

def p_si_error_inicio(p):
    """
    si : PARENTESIS_A expresion PARENTESIS_B
    """
    errores_Sinc_Desc.append("Error: Falta -> Declaración IF antes de la condición en la línea: "+ str(p.lineno(1)))


def p_si_falta_else(p):
    """
    si : IF PARENTESIS_A expresion PARENTESIS_B bloque_codigo ELSE
    """
    errores_Sinc_Desc.append("Error: Falta -> Bloque de código después de 'else' en la línea: " + str(p.lineno(5)))

def p_si_falta_parentesis(p):
    """
    si : IF expresion bloque_codigo
    """
    errores_Sinc_Desc.append("Error: Falta -> Paréntesis en la condición 'if' en la línea: " + str(p.lineno(1)))

# ERRORES WHILE
def p_mientras_error(p):
    """
    mientras : WHILE PARENTESIS_A PARENTESIS_B bloque_codigo
    """
    errores_Sinc_Desc.append("Error: Falta -> Condición en la declaración 'while' en la línea: " + str(p.lineno(2)))

# Error: Falta paréntesis de apertura
def p_mientras_error_sin_parentesis_apertura(p):
    """
    mientras : WHILE expresion PARENTESIS_B bloque_codigo
    """
    errores_Sinc_Desc.append(
        "Error: Falta -> Paréntesis de apertura '(' en la declaración 'while' en la línea: "
        + str(p.lineno(1))
    )

# Error: Falta paréntesis de cierre
def p_mientras_error_sin_parentesis_cierre(p):
    """
    mientras : WHILE PARENTESIS_A expresion bloque_codigo
    """
    errores_Sinc_Desc.append(
        "Error: Falta -> Paréntesis de cierre ')' en la declaración 'while' en la línea: "
        + str(p.lineno(1))
    )

def p_while_condicion_vacia(p):
    """
    mientras : WHILE PARENTESIS_A PARENTESIS_B LLAVE_A LLAVE_C
    """
    errores_Sinc_Desc.append("Error: Condición vacía en el bucle 'while' en la línea: " + str(p.lineno(1)))

# Error: Falta bloque de código o punto y coma
def p_mientras_error_falta_bloque_o_punto_y_coma(p):
    """
    mientras : WHILE PARENTESIS_A expresion PARENTESIS_B
    """
    errores_Sinc_Desc.append(
        "Error: Falta -> Bloque de código o punto y coma después de la condición en 'while' en la línea: "
        + str(p.lineno(1))
    )

def p_mientras_error_solo_parentesis(p):
    """
    mientras : PARENTESIS_A PARENTESIS_B
    """
    errores_Sinc_Desc.append("Error: Expresión vacía dentro de paréntesis en la línea: " + str(p.lineno(1)))

def p_for_loop_error(p):
    """
    for_loop : FOR PARENTESIS_A PUNTOCOMA for_condicion PUNTOCOMA for_actualizacion PARENTESIS_B bloque_codigo
    """
    errores_Sinc_Desc.append("Error: Falta -> Inicialización en la declaración 'for' en la línea: " + str(p.lineno(2)))

def p_for_sin_condicion(p):
    """
    for_loop : FOR PARENTESIS_A for_init PUNTOCOMA PUNTOCOMA for_actualizacion PARENTESIS_B bloque_codigo
    """
    errores_Sinc_Desc.append("Error: Falta condición en el ciclo 'for' en la línea: " + str(p.lineno(2)))
   
def p_declaracion_error_sin_id(p):
    """
    declaracion : tipo ASIGNACION expresion PUNTOCOMA
    """
    errores_Sinc_Desc.append("Error: Falta -> Identificador después del tipo en la línea: " + str(p.lineno(1)))

def p_bloque_codigo_error_incompleto(p):
    """
    bloque_codigo : LLAVE_A
                  | lista_declaraciones LLAVE_C
    """
    errores_Sinc_Desc.append("Error: Bloque de código incompleto, falta contenido o cierre en la línea: " + str(p.lineno(1)))

def p_expresion_falta_operando(p):
    """
    expresion : expresion SUMA
              | expresion RESTA
              | expresion MULTIPLICACION
              | expresion DIVISION
    """
    errores_Sinc_Desc.append("Error: Operación incompleta, falta un operando después del operador en la línea: " + str(p.lineno(2)))

def p_expresion_falta_parentesis(p):
    """
    expresion : PARENTESIS_A expresion
              | expresion PARENTESIS_B
    """
    errores_Sinc_Desc.append("Error: Falta -> Paréntesis de apertura o cierre en la expresión en la línea: " + str(p.lineno(1)))

def p_expresion_error_solo_parentesis(p):
    """
    expresion : PARENTESIS_A PARENTESIS_B
    """
    errores_Sinc_Desc.append("Error: Expresión vacía dentro de paréntesis en la línea: " + str(p.lineno(2)))

def p_expresion_error_operador_sin_operandos(p):
    """
    expresion : SUMA
              | RESTA
              | MULTIPLICACION
              | DIVISION
    """
    errores_Sinc_Desc.append("Error: Operador sin operandos en la línea: " + str(p.lineno(1)))

def p_comando_error_parentesis(p):
    """
    comando : MOVERADELANTE expresion PUNTOCOMA
    """
    errores_Sinc_Desc.append("Error: Falta -> Paréntesis en el comando en la línea: " + str(p.lineno(2)))

def p_comando_error_argumento(p):
    """
    comando : VELOCIDAD PARENTESIS_A PARENTESIS_B PUNTOCOMA
    """
    errores_Sinc_Desc.append("Error: Falta -> Argumento en el comando 'velocidad' en la línea: " + str(p.lineno(1)))

def p_comando_error_sin_cierre_parentesis(p):
    """
    comando : VELOCIDAD PARENTESIS_A expresion PUNTOCOMA
    """
    errores_Sinc_Desc.append("Error: Falta paréntesis de cierre ')' en el comando en la línea: " + str(p.lineno(2)))

def p_bloque_codigo_error_llave(p):
    """
    bloque_codigo : LLAVE_A lista_declaraciones
    """
    errores_Sinc_Desc.append("Error: Falta -> Llave de cierre '}' en el bloque de código en la línea: " + str(p.lineno(1)))

# CONDICIÓN MAL FORMADA
def p_error_condicion(p):
    """
    for_condicion : PARENTESIS_A expresion PUNTOCOMA
    """
    errores_Sinc_Desc.append("Error: Condición mal formada en el ciclo 'for' en la línea: " + str(p.lineno(1)))


def p_tipo(p):
    """
    tipo : INT
         | BOOL
         | STG
         | REAL
         | COLOR
    """
    p[0] = p[1]

# Reglas para las expresiones aritméticas y de comparación
def p_expresion_suma(p):
    'expresion : expresion SUMA expresion'
    try:
        p[0] = p[1] + p[3]  # Realiza la suma de dos expresiones
    except:
        errores_semanticos.append(f"Error: Tipos de datos incompatibles en la suma en la línea: {p.lineno(1)}")


def p_expresion_resta(p):
    'expresion : expresion RESTA expresion'
    try:
        p[0] = p[1] - p[3] 
    except:
        errores_semanticos.append(f"Error: Tipos de datos incompatibles en la resta en la línea: {p.lineno(1)}")

def p_expresion_mult(p):
    'expresion : expresion MULTIPLICACION expresion'
    if isinstance(p[1], (int, float)) and isinstance(p[3], (int, float)):
        p[0] = p[1] * p[3]
    else:
        errores_semanticos.append(
            f"Error: Tipos de datos incompatibles en la multiplicación en la línea {p.lineno(1)}"
        )

def p_expresion_div(p):
    'expresion : expresion DIVISION expresion'
    if not isinstance(p[1], (int, float)) or not isinstance(p[3], (int, float)):
        errores_semanticos.append(
            f"Error: Tipos de datos incompatibles en la división en la línea {p.lineno(1)}"
        )
    elif p[3] == 0:
        errores_semanticos.append(f"Error: No se puede dividir entre cero en la línea {p.lineno(1)}")
    else:
        p[0] = p[1] / p[3]
        if p[0] % 1 == 0:  # Si el resultado es un número entero, lo convierte en `int`
            p[0] = int(p[0])

def p_expresion_comparacion(p):
    '''
    expresion : expresion MENORQUE expresion
              | expresion MENORIGUAL expresion
              | expresion MAYORQUE expresion
              | expresion MAYORIGUAL expresion
    '''
    var = None
    var2 = None
    if (isinstance(p[1], str) and p[1].lower() == "sensorhumedad"):  # p[3] es un identificador
        var = p[1]
        p[1] = 0
    if (isinstance(p[3], str) and p[3].lower() == "sensorhumedad"):  # p[3] es un identificador
        var2 = p[3]
        p[3] = 0
    if isinstance(p[1], str):  # p[1] es un identificador
        var = p[1]
        p[1] = p[1].lower()
        p[1] = ts[p[1]]['valor']
    if isinstance(p[3], str) and (p[3] in ts):  # p[3] es un identificador
        var2 = p[3]
        p[3] = p[3].lower()
        p[3] = ts[p[3]]['valor']
    if (isinstance(p[1], (int, float)) or isinstance(ts[p[1][0]]["parametros"][p[1][2]]["valor"], (int, float))) and (isinstance(p[3], (int, float)) or isinstance(ts[p[3][0]]["parametros"][p[3][2]]["valor"], (int, float))):
        if var != None:
            p[1] = var
        if var2 != None:
            p[3] = var2
        p[0] = (f"{p[1]} {p[2]} {p[3]}")
    else:
        errores_semanticos.append(
            f"Error: No se puede comparar '{type(p[1]).__name__}' con '{type(p[3]).__name__}' en la línea {p.lineno(1)}."
        )


def p_expresion_comparacion2(p):
    '''
    expresion : expresion IGUAL expresion
              | expresion DIFERENTE expresion
    '''
    if type(p[1]) == type(p[3]):  # Comparación solo entre el mismo tipo
        if p[2] == '==':
            codigo_intermedio.condicion(f"{p[1]} {p[2]} {p[3]}")
            p[0] = p[1] == p[3]
        elif p[2] == '!=':
            codigo_intermedio.condicion(f"{p[1]} {p[2]} {p[3]}")
            p[0] = p[1] != p[3]
    else:
        errores_semanticos.append(
            f"Error: Comparación inválida entre '{type(p[1]).__name__}' y '{type(p[3]).__name__}' en la línea {p.lineno(1)}."
        )


def p_expresion(p):
    """
    expresion : PARENTESIS_A expresion PARENTESIS_B
               | NUMERO
               | REAL
               | CADENA
               | COLORRGB
               | COLORHEX
               | SENSORTEMPERATURA
               | SENSORHUMEDAD
               | SENSORPH
               | SENSORPESO
               | REVISARCOLOR
               | REVISARTAMANO
               | SENSORCONTADOR
               | COMPARARPH
               | COMPARARHUMEDAD
               | COMPARARTEMP
               | MEDIRALTURA
               | MEDIRGLOSOR
               | MEDIRCE
    """
    if len(p) == 4:
        p[0] = p[2]
    else:
        if isinstance(p[1], str):
            p[1] = p[1].upper()
        if p[1] == 'SENSORHUMEDAD':
            p[0] = 'SENSORHUMEDAD'
        elif p[1] in {'SENSORTEMPERATURA',
                    'SENSORCONTADOR', 'MEDIRCE'}:
            p[0] = 0 
        elif p[1] in {'SENSORPH', 'SENSORPESO',
                    'REVISARTAMANO', 'MEDIRALTURA','MEDIRGLOSOR'}:
            p[0] = 0.0 
        elif p[1] in {'COMPARARPH', 'COMPARARHUMEDAD',
                'COMPARARTEMP'}:
            p[0] = False
        elif p[1] in {'REVISARCOLOR'}:
            p[0] = '#ffffff'
        else:
            p[0] = p[1]

def p_expresion_booleana(p):
    """
    expresion : TRUE
              | FALSE
    """
    p[0] = True if p[1] == "TRUE" else False

def p_expresionID(p):
    """
    expresion : ID
    """
    global ts
    p[1] = p[1].lower()
    if p[1] in ts:
        p[0] = p[1]
    else:
        errores_Sinc_Desc.append(f"Error: La variable '{p[1]}' no ha sido declarada en la línea: {p.lineno(1)}")


def p_si(p):
    """
    si : IF PARENTESIS_A expresion PARENTESIS_B bloque_codigo
       | IF PARENTESIS_A expresion PARENTESIS_B bloque_codigo ELSE bloque_codigo
       | IF PARENTESIS_A expresion PARENTESIS_B bloque_codigo ELSE si
    """
    global en_si
    en_si=True
    if isinstance(p[3], str) and ('.' in p[3] or '>' in p[3] or '<' in p[3] or '==' in p[3] or '!=' in p[3]):
        # Pasar la expresión completa como cadena al generador de código
        etiqueta_falsa = codigo_intermedio.if_inicio(p[3])
    else:
        # Evaluación normal para condiciones simples
        etiqueta_falsa = codigo_intermedio.if_inicio(p[3])
    
    # Procesar el bloque then
    for instruccion in p[5][1]:
        instrucciones(instruccion)
    
    if len(p) == 8:
        if isinstance(p[7], list):
            etiqueta_fin = codigo_intermedio.if_else(etiqueta_falsa)
            # Aquí iría el código para procesar el else-if
            codigo_intermedio.if_fin(etiqueta_fin)
            p[0] = ('if_else_if', p[3], p[5], p[7])
        else:  # Es un else normal
            etiqueta_fin = codigo_intermedio.if_else(etiqueta_falsa)
            # Procesar el bloque else
            for instruccion in p[7][1]:
                instrucciones(instruccion)
            codigo_intermedio.if_fin(etiqueta_fin)
            p[0] = ('if_else', p[3], p[5], p[7])
    else:
        codigo_intermedio.if_fin(etiqueta_falsa)
        p[0] = ('if', p[3], p[5])

    en_si=False


def instrucciones(instruccion):
    if isinstance(instruccion, tuple):
            if instruccion[0] == 'mover_adelante':
                codigo_intermedio.mover_adelante(instruccion[1])
            elif instruccion[0] == 'mover_atras':
                codigo_intermedio.mover_atras(instruccion[1])
            elif instruccion[0] == 'girar_derecha':
                codigo_intermedio.girar_derecha(instruccion[1])
            elif instruccion[0] == 'girar_izquierda':
                codigo_intermedio.girar_izquierda(instruccion[1])
            elif instruccion[0] == 'gira_sensores':
                codigo_intermedio.girar_sensores(instruccion[1])
            elif instruccion[0] == 'velocidad':
                codigo_intermedio.velocidad(instruccion[1])
            elif instruccion[0] == 'aplicar':
                codigo_intermedio.aplicar(instruccion[1])
            elif instruccion[0] == 'alerta':
                codigo_intermedio.alerta(instruccion[1])
            elif instruccion[0] == 'aspersion':
                codigo_intermedio.aspersion()
            elif instruccion[0] == 'detener':
                codigo_intermedio.detener()

def p_mientras(p):
    """
    mientras : WHILE PARENTESIS_A expresion PARENTESIS_B bloque_codigo
    """
    etiquetas = codigo_intermedio.while_inicio(p[3])

    for instr in p[5][1]:
        instrucciones(instr)
    
    codigo_intermedio.while_fin(etiquetas)
    
    p[0] = ('While', p[3], p[5])

def p_for_loop(p):
    """
    for_loop : FOR PARENTESIS_A for_init PUNTOCOMA for_condicion PUNTOCOMA for_actualizacion PARENTESIS_B bloque_codigo
    """
    etiqueta_inicio = codigo_intermedio.nueva_etiqueta()
    etiqueta_fin = codigo_intermedio.nueva_etiqueta()
    
    # Código de inicialización
    if p[3][0] == 'init':
        if 'tipo' in p[3][1]:  # Declaración con tipo
            codigo_intermedio.declaracion(p[3][1]['tipo'], p[3][1]['id'], p[3][1]['valor'])
        else:  # Asignación simple
            codigo_intermedio.asignacion(p[3][1]['id'], p[3][1]['valor'])
    
    # Etiqueta de inicio del bucle
    codigo_intermedio.agregar(f'{etiqueta_inicio}:')
    
    # Generar código para la condición
    codigo_intermedio.generar_instruccion('CJMP', p[5][1], etiqueta_fin)
    
    # Código del cuerpo del bucle
    for instr in p[9]:
        codigo_intermedio.agregar(instr)
    
    # Código de actualización
    if p[7][0] == 'asignacion':
        codigo_intermedio.asignacion(p[7][1], p[7][2])
    elif p[7][0] == 'incremento':
        codigo_intermedio.operacion(p[7][1], p[7][1], '+', '1')
    elif p[7][0] == 'decremento':
        codigo_intermedio.operacion(p[7][1], p[7][1], '-', '1')
    
    # Salto de regreso al inicio
    codigo_intermedio.generar_instruccion('JMP', etiqueta_inicio)
    
    # Etiqueta de fin del bucle
    codigo_intermedio.agregar(f'{etiqueta_fin}:')
    
    p[0] = ('for_loop', {'init': p[3], 'condition': p[5], 'update': p[7], 'body': p[9]})

def p_for_init(p):
    """
    for_init : tipo ID ASIGNACION expresion
             | ID ASIGNACION expresion
    """
    if len(p) == 5:
        p[0] = ('init', {'tipo': p[1], 'id': p[2], 'valor': p[4]})
    else:
        p[0] = ('init', {'id': p[1], 'valor': p[3]})

def p_for_condicion(p):
    """
    for_condicion : expresion
    """
    p[0] = ('condicion', p[1])

def p_comando_mover_adelante(p):
    'comando : MOVERADELANTE PARENTESIS_A expresion PARENTESIS_B PUNTOCOMA'
    if isinstance(p[3], (int)):
        codigo_intermedio.mover_adelante(p[3])
        p[0] = ('mover_adelante', p[3])
    else:
        errores_semanticos.append(
            f"Error: Tipos de datos incompatibles en MOVERADELANTE en la línea {p.lineno(1)}"
        )

def p_comando_mover_atras(p):
    'comando : MOVERATRAS PARENTESIS_A expresion PARENTESIS_B PUNTOCOMA'
    if isinstance(p[3], (int)):
        codigo_intermedio.mover_atras(p[3])
        p[0] = ('mover_atras', p[3])
    else:
        errores_semanticos.append(
            f"Error: Tipos de datos incompatibles en MOVERATRAS en la línea {p.lineno(1)}"
        )

def p_comando_girar_izquierda(p):
    'comando : GIRARIZQUIERDA PARENTESIS_A expresion PARENTESIS_B PUNTOCOMA'
    if isinstance(p[3], (int)):
        codigo_intermedio.girar_izquierda(p[3])
        p[0] = ('girar_izquierda', p[3])
    else:
        errores_semanticos.append(
            f"Error: Tipos de datos incompatibles en GIRARIZQUIERDA en la línea {p.lineno(1)}"
        )

def p_comando_girar_derecha(p):
    'comando : GIRARDERECHA PARENTESIS_A expresion PARENTESIS_B PUNTOCOMA'
    if isinstance(p[3], (int)):
        codigo_intermedio.girar_derecha(p[3])
        p[0] = ('girar_derecha', p[3])
    else:
        errores_semanticos.append(
            f"Error: Tipos de datos incompatibles en GIRARDERECHA en la línea {p.lineno(1)}"
        )

def p_comando_velocidad(p):
    'comando : VELOCIDAD PARENTESIS_A expresion PARENTESIS_B PUNTOCOMA'
    if isinstance(p[3], (int)):
        codigo_intermedio.velocidad(p[3])
        p[0] = ('velocidad', p[3])
    else:
        errores_semanticos.append(
            f"Error: Tipos de datos incompatibles en VELOCIDAD en la línea {p.lineno(1)}"
        )

def p_comando_gira_sensores(p):
    'comando : GIRASENSORES PARENTESIS_A expresion PARENTESIS_B PUNTOCOMA'
    if isinstance(p[3], (int)):
        codigo_intermedio.girar_sensores(p[3])
        p[0] = ('gira_sensores', p[3])
    else:
        errores_semanticos.append(
            f"Error: Tipos de datos incompatibles en GIRASENSORES en la línea {p.lineno(1)}"
        )

def p_comando_detener(p):
    'comando : DETENER PUNTOCOMA'
    codigo_intermedio.detener()
    p[0] = ('detener',)

def p_comando_aspersion(p):
    'comando : ASPERSION PUNTOCOMA'
    p[0] = ('aspersion',)

def p_comando_alerta(p):
    'comando : ALERTA PARENTESIS_A expresion PARENTESIS_B PUNTOCOMA'
    codigo_intermedio.alerta(p[3])
    p[0] = ('alerta', p[3])


def p_comando_aplicar_error(p):
    'comando : APLICAR PARENTESIS_A  PARENTESIS_B PUNTOCOMA'
    p[0] = ('aplicar', p[3])

    errores_Sinc_Desc.append("Error: Falta compuesto en linea: " + str(p.lineno(2)))

def p_comando_aplicar_error2(p):
    'comando : APLICAR PARENTESIS_A expresion PARENTESIS_B PUNTOCOMA'
    p[0] = ('aplicar', p[3])

    errores_Sinc_Desc.append("Error: Falta compuesto en linea: " + str(p.lineno(2)))

def p_comando_aplicar(p):
    'comando : APLICAR PARENTESIS_A compuesto PARENTESIS_B PUNTOCOMA'
    p[0] = ('aplicar', p[3])

def p_compuesto(p):
    """
    compuesto : INSECTICIDA
              | FUNGICIDA
              | CAL
              | AZUFRE
              | CENIZAS
              | TURBA
              | FERTILIZANTE
              | COMPOSTA
    """
    p[0] = p[1]

def p_plantas(p):
    '''
    plantas : planta
            | plantas plantas
    '''
    if len(p) == 3:
        p[0] = (p[1],p[2])
    else:
        p[0] = (p[1])

def p_definir_planta(p):
    'planta : PLANTA ID bloque_parametros'
    var_name = p[2].lower()  # Nombre de la planta
    parametros = p[3]  # Diccionario con parámetros

    global ts
    if var_name in ts:
        errores_semanticos.append(f"Error: La planta '{var_name}' ya ha sido declarada.")
    else:
        ts[var_name] = {"tipo": "planta", "parametros": parametros}
        codigo_intermedio.declarar_planta(var_name, parametros)

    p[0] = ('planta', var_name, parametros)


def p_bloque_parametros(p):
    'bloque_parametros : LLAVE_A lista_parametros LLAVE_C'
    p[0] = p[2]

def p_lista_parametros(p):
    '''lista_parametros : parametro
                      | lista_parametros parametro'''
    
    if len(p) == 3:
        p[1].update(p[2])  # Agrega más parámetros al diccionario
        p[0] = p[1]
    else:
        p[0] = p[1]


tipos_parametros = {
    "ph": "real",
    "humedad": "int",
    "peso": "real",
    "tamano": "real",
    "color": "color",
    "ce": "real",
    "rangotemp": "real",
    "rangohumedad": "real",
    "rangoph": "real"
}

def p_parametro(p):
    """
    parametro : PH expresion PUNTOCOMA
                | HUMEDAD expresion PUNTOCOMA
                | PESO expresion PUNTOCOMA
                | TAMANO expresion PUNTOCOMA
                | COLOR expresion PUNTOCOMA
                | CE expresion PUNTOCOMA
                | RANGOTEMP expresion PUNTOCOMA
                | RANGOHUMEDAD expresion PUNTOCOMA
                | RANGOPH expresion PUNTOCOMA
    """
    parametro = p[1].lower()  # Convertimos el nombre del parámetro a minúsculas
    value = p[2]
    tipo = tipos_parametros[parametro]  # Obtener el tipo esperado
    # Verificar que el valor tenga el tipo correcto
    if tipo == "int" and not isinstance(value, int):
        errores_semanticos.append(f"Error de tipo: '{parametro}' debe ser un entero.")
    elif tipo == "real" and not isinstance(value, (int, float)):
        errores_semanticos.append(f"Error de tipo: '{parametro}' debe ser un número real.")
    elif tipo == "color":
        if not (isinstance(value, str) and (value.startswith("#"))):
            errores_semanticos.append(f"Error de tipo: '{parametro}' debe ser un color válido en formato HEX.")
    elif tipo == "str" and not isinstance(value, str):
        errores_semanticos.append(f"Error de tipo: '{parametro}' debe ser una cadena.")

    # Guardar el parámetro en la tabla de símbolos con su tipo
    p[0] = {parametro: {"tipo": tipo, "valor": value}}


def p_planta_parametro(p):
    """
    expresion : ID PUNTO PH
              | ID PUNTO HUMEDAD
              | ID PUNTO PESO
              | ID PUNTO TAMANO
              | ID PUNTO COLOR
              | ID PUNTO CE
              | ID PUNTO TEMPERATURA
    """
    var_name = p[1].lower()  # Nombre de la planta
    parametro = p[3].lower()  # Parámetro solicitado (ej. PH, HUMEDAD)

    if var_name not in ts:
        errores_semanticos.append(f"Error: La planta '{var_name}' no ha sido declarada.")
    elif parametro not in ts[var_name]["parametros"]:
        errores_semanticos.append(f"Error: La planta '{var_name}' no tiene el parámetro '{parametro}'.")
    else:
        p[0] = (var_name, p[2], parametro) # ts[var_name]["parametros"][parametro]["valor"]  # Devuelve el valor del parámetro


def p_registrar(p):
    'comando : REGISTRAR PARENTESIS_A expresion PARENTESIS_B PUNTOCOMA'
    codigo_intermedio.generar_instruccion('REGISTRAR', p[3])
    p[0] = p[3]


def p_for_actualizacion(p):
    """
    for_actualizacion : ID ASIGNACION expresion
                       | ID MASMAS
                       | ID MENOSMENOS
    """

def find_column(input, token): 
    line_start = input.rfind('\n', 0, token.lexpos) + 1 
    return (token.lexpos - line_start)

def p_error(p):
    global errores_Sinc_Desc
    if p:
        column = find_column(p.lexer.lexdata, p)
        errores_Sinc_Desc.append(f"Syntax error at token {p.type}, line {p.lineno}, column {column}")
    else:
        errores_Sinc_Desc.append("Syntax error at EOF")

#Construir el analizador
parser = yacc.yacc()


def test_parser(codigo):
    result = parser.parse(codigo)
    print(result)
    print(ts)
    print(codigo_intermedio.obtener_codigo())
    return ts

