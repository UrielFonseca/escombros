import re

def generar_codigo_objeto(codigo_intermedio: str) -> str:
    codigo = [
        '.include "C:/Users/moren/Downloads/avra-1.3.0/avra/includes/m328pdef.inc"',
        ".org 0x0000",
        "    rjmp RESET",
        "",
        "RESET:",
        "; ================================",
        "; Inicialización de registros I/O",
        "; ================================",
        "; DDRB (0x24): Configurar PB0, PB1 (OC1A/D9) y PB5 (LED) como salida",
        "LDI R16, 0b00100011",
        "OUT DDRB, R16         ; DDRB = 0x24",
        ""
    ]

    plantas = {}
    planta_actual = None
    registro_base = 30  # R30 para planta.ph, luego R29, R28...
    registro_temporales = {}
    registro_actual = 19
    propiedades_planta = ["PH", "HUMEDAD", "CE", "RANGOHUMEDAD", "RANGOPH"]

    etiquetas_if = {}  # para generar etiquetas únicas para IF
    contador_etiquetas = 0

    # Función para generar etiquetas únicas
    def nueva_etiqueta(base):
        nonlocal contador_etiquetas
        etiqueta = f"{base}_{contador_etiquetas}"
        contador_etiquetas += 1
        return etiqueta

    # Función para traducir operaciones de comparación a instrucciones AVR
    def operador_a_brancha(op, etiqueta):
        if op == ">":
            return f"BRSH {etiqueta}"
        elif op == "<":
            return f"BRLO {etiqueta}"
        elif op == "==":
            return f"BREQ {etiqueta}"
        elif op == "!=":
            return f"BRNE {etiqueta}"
        else:
            return f"; [!] Operador '{op}' no implementado"

    # Función para obtener el registro de una variable o planta.propiedad
    def valor_a_registro(valor, destino):
        if "." in valor:
            planta, prop = valor.split(".")
            reg = plantas.get(planta, {}).get(prop.lower())
            if reg:
                return [f"MOV {destino}, {reg}"]
            else:
                return [f"; [!] {planta}.{prop} no declarado"]
        elif valor.lower() in registro_temporales:
            return [f"MOV {destino}, {registro_temporales[valor.lower()]}"]
        else:
            try:
                val_int = int(float(valor))
                return [f"LDI {destino}, {val_int}"]
            except ValueError:
                return [f"; [!] Valor '{valor}' no reconocido"]

    # Mapeo simple para acciones que usan OUT PORTB con valores directos
    acciones_portb = {
        "MOVERADELANTE": "0b00000001",  # PB0
        "MOVERATRAS":    "0b00000010",  # PB1
        "GIRASENSORES":  "0b00000100",  # PB2
        "ASPERSION":     "0b00010000",  # PB4
    }

    # Plantilla para configurar Timer1 PWM igual al ejemplo
    def plantilla_aplicar():
        return [
            "; Configurar Timer1 para servo en OC1A",
            "LDI R16, (1 << COM1A1) | (1 << WGM11)",
            "STS TCCR1A, R16",
            "LDI R16, (1 << WGM13) | (1 << WGM12) | (1 << CS11) ; Prescaler 8",
            "STS TCCR1B, R16",
            "; TOP = 39999 (20ms a 16MHz con prescaler 8)",
            "LDI R16, LOW(39999)",
            "STS ICR1L, R16",
            "LDI R16, HIGH(39999)",
            "STS ICR1H, R16",
            "; OCR1A = 3000 (~1.5ms pulso central)",
            "LDI R16, LOW(3000)",
            "STS OCR1AL, R16",
            "LDI R16, HIGH(3000)",
            "STS OCR1AH, R16",
            ""
        ]

    # Recorrer código intermedio línea a línea
    for linea in codigo_intermedio.splitlines():
        linea = linea.strip()
        if not linea:
            continue

        # Etiquetas directas
        if linea.endswith(":"):
            codigo.append(linea)
            continue

        # Detectar nueva planta
        if linea.upper().startswith("PLANTA"):
            planta_actual = linea.split()[1].lower()
            plantas[planta_actual] = {}
            codigo.append(f"; ================================")
            codigo.append(f"; Variables de la planta {planta_actual}")
            codigo.append(f"; ================================")
            continue

        # Detectar propiedades de planta
        if planta_actual and any(re.match(rf'^{prop}\b', linea.upper()) for prop in propiedades_planta):
            partes = linea.split()
            if len(partes) >= 2:
                prop = partes[0].lower()
                val = partes[1]
                reg = f"R{registro_base}"
                plantas[planta_actual][prop] = reg
                codigo.append(f"LDI {reg}, {int(float(val))}    ; {planta_actual}.{prop} = {val}")
                registro_base -= 1
            continue

        # Variables temporales (real o int)
        if linea.startswith("real") or linea.startswith("int"):
            partes = re.split(r'\s+', linea)
            if len(partes) >= 4:
                tipo, nombre, _, valor = partes[:4]
                nombre = nombre.lower()
                if nombre not in registro_temporales:
                    reg = f"R{registro_actual}"
                    registro_temporales[nombre] = reg
                    registro_actual -= 1
                else:
                    reg = registro_temporales[nombre]
                try:
                    codigo.append(f"LDI {reg}, {int(float(valor))}")
                except:
                    codigo.append(f"; [!] Valor inválido para {nombre}: {valor}")
            continue

        # Llamadas a funciones/instrucciones
        if linea.lower().startswith("call"):
            partes = linea.split("call", 1)[1].split(",")
            instr = partes[0].strip().upper()
            valor = partes[1].strip() if len(partes) > 1 else None

            if instr in acciones_portb:
                valor_out = acciones_portb[instr]
                codigo.append(f"; {instr} - salida PORTB")
                codigo.append(f"LDI R16, {valor_out}")
                codigo.append("OUT PORTB, R16")
                codigo.append("")
            elif instr == "APLICAR":
                codigo.extend(plantilla_aplicar())
            elif instr == "DETENER":
                codigo.append("; Detener - apagar todos los bits PB0..PB5")
                codigo.append("LDI R16, 0b00000000")
                codigo.append("OUT PORTB, R16")
                codigo.append("")
            elif instr == "REGISTRAR":
                codigo.append("; REGISTRAR - simbólico, sin acción hardware")
                codigo.append("")
            else:
                codigo.append(f"; [!] call {instr} no reconocida")
            continue

        # IF ... GOTO condicional
        if "GOTO" in linea and "IF" in linea:
            # Formato esperado: IF <izq> <op> <der> GOTO <etiqueta>
            m = re.match(r"IF\s+(.+)\s+(==|!=|>|<)\s+(.+)\s+GOTO\s+(\w+)", linea, re.I)
            if m:
                izq, op, der, etiqueta = m.groups()
                etiqueta_true = etiqueta

                codigo.append(f"; IF {izq} {op} {der}")
                codigo.extend(valor_a_registro(izq, "R20"))
                codigo.extend(valor_a_registro(der, "R21"))
                codigo.append("CP R20, R21")
                codigo.append(operador_a_brancha(op, etiqueta_true))
                # Si no se cumple, continuar con siguiente línea
                codigo.append(f"RJMP {etiqueta_true}")
                continue

        # GOTO simple
        if linea.startswith("GOTO"):
            etiqueta = linea.split()[1]
            codigo.append(f"RJMP {etiqueta}")
            continue

        # Si línea no reconocida
        codigo.append(f"; [!] Línea no reconocida: {linea}")

    # Final: bucle infinito LOOP
    codigo.append("")
    codigo.append("; ================================")
    codigo.append("; Bucle principal")
    codigo.append("; ================================")
    codigo.append("LOOP:")
    codigo.append("    RJMP LOOP")

    return "\n".join(codigo)
