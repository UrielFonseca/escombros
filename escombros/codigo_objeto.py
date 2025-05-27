import re

def generar_codigo_objeto(codigo_intermedio: str) -> str:
    codigo = [
        '.include "C:/Users/moren/Downloads/avra-1.3.0/avra/includes/m328pdef.inc"',
        ".org 0x0000",
        "    rjmp RESET",
        "",
        "RESET:",
        "LDI R16, 0b00100011",
        "OUT DDRB, R16         ; DDRB = 0x24",
        """
        ; Configurar Timer1 (una vez)
        LDI R16, (1 << COM1A1) | (1 << COM1B1) | (1 << WGM11)
        STS TCCR1A, R16
        LDI R16, (1 << WGM13) | (1 << WGM12) | (1 << CS11)
        STS TCCR1B, R16

        ; TOP = 3999 > 20 ms
        LDI R16, LOW(3999)
        STS ICR1L, R16
        LDI R16, HIGH(3999)
        STS ICR1H, R16
        """
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
    def plantilla_aplicar(tipo):
        instrucciones = []

        if tipo == "CAL":
            instrucciones.extend([
                "; APLICAR CAL - mover servo en pin 9 (OC1A)",
                "LDI R16, LOW(3000)     ; 1.5ms pulso",
                "STS OCR1AL, R16",
                "LDI R16, HIGH(3000)",
                "STS OCR1AH, R16",
                "RCALL ESPERAR",
                "LDI R16, LOW(2000)     ; volver a posición inicial (1ms)",
                "STS OCR1AL, R16",
                "LDI R16, HIGH(2000)",
                "STS OCR1AH, R16",
            ])
        elif tipo == "AZUFRE":
            instrucciones.extend([
                "; APLICAR AZUFRE - mover servo en pin 10 (OC1B)",
                "LDI R16, LOW(3000)     ; 1.5ms pulso",
                "STS OCR1BL, R16",
                "LDI R16, HIGH(3000)",
                "STS OCR1BH, R16",
                "RCALL ESPERAR",
                "LDI R16, LOW(2000)     ; volver a posición inicial (1ms)",
                "STS OCR1BL, R16",
                "LDI R16, HIGH(2000)",
                "STS OCR1BH, R16",
            ])
        else:
            instrucciones.append(f"; [!] APLICAR tipo '{tipo}' no soportado")

        return instrucciones + [""]



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
                tipo = valor.upper() if valor else ""
                codigo.extend(plantilla_aplicar(tipo))
            elif instr == "DETENER":
                codigo.append("; Detener - apagar todos los bits PB0..PB5")
                codigo.append("LDI R16, 0b00000000")
                codigo.append("OUT PORTB, R16")
                codigo.append("")
            elif instr == "REGISTRAR":
                codigo.append("; REGISTRAR - simbólico, sin acción hardware")
                codigo.append("")
            elif instr == "SENSORHUMEDAD":
                codigo.extend([
                    "; SENSORHUMEDAD - Leer ADC0 (A0)",
                    "LDI R16, (1 << REFS0)         ; AVCC como referencia",
                    "STS ADMUX, R16                ; Seleccionar ADC0",
                    "LDI R16, (1 << ADEN) | (1 << ADSC) | (1 << ADPS2) | (1 << ADPS1) | (1 << ADPS0)",
                    "STS ADCSRA, R16               ; Habilitar ADC, iniciar conversión, prescaler 128",
                    "WAIT_ADC:",
                    "LDS R17, ADCSRA",
                    "SBRS R17, ADSC",
                    "RJMP WAIT_ADC",
                    "LDS R17, ADCH                 ; Resultado en R17",
                    ""
                ])

            else:
                codigo.append(f"; [!] call {instr} no reconocida")
            continue

        if "GOTO" in linea and "IF" in linea:
            # Formato esperado: IF <izq> <op> <der> GOTO <etiqueta>
            m = re.match(r"IF\s+(.+)\s+(==|!=|>|<)\s+(.+)\s+GOTO\s+(\w+)", linea, re.I)
            if m:
                izq, op, der, etiqueta = m.groups()
                etiqueta_true = etiqueta

                codigo.append(f"; IF {izq} {op} {der}")

                # Si SENSORHUMEDAD está a la izquierda
                if izq.strip().upper() == "SENSORHUMEDAD":
                    codigo.extend([
                        "; Leer sensor humedad (ADC0)",
                        "LDI R16, (1 << REFS0)", 
                        "STS ADMUX, R16",
                        "LDI R16, (1 << ADEN) | (1 << ADSC) | (1 << ADPS2) | (1 << ADPS1) | (1 << ADPS0)",
                        "STS ADCSRA, R16",
                        "WAIT_ADC_L:",
                        "LDS R17, ADCSRA",
                        "SBRS R17, ADSC",
                        "RJMP WAIT_ADC_L",
                        "LDS R20, ADCH  ; valor sensor -> R20"
                    ])
                    codigo.extend(valor_a_registro(der, "R21"))

                # Si SENSORHUMEDAD está a la derecha
                elif der.strip().upper() == "SENSORHUMEDAD":
                    codigo.extend([
                        "; Leer sensor humedad (ADC0)",
                        "LDI R16, (1 << REFS0)", 
                        "STS ADMUX, R16",
                        "LDI R16, (1 << ADEN) | (1 << ADSC) | (1 << ADPS2) | (1 << ADPS1) | (1 << ADPS0)",
                        "STS ADCSRA, R16",
                        "WAIT_ADC_R:",
                        "LDS R17, ADCSRA",
                        "SBRS R17, ADSC",
                        "RJMP WAIT_ADC_R",
                        "LDS R21, ADCH  ; valor sensor -> R21"
                    ])
                    codigo.extend(valor_a_registro(izq, "R20"))

                else:
                    # Ningún lado es sensorhumedad, caso normal
                    codigo.extend(valor_a_registro(izq, "R20"))
                    codigo.extend(valor_a_registro(der, "R21"))

                codigo.append("CP R20, R21")
                codigo.append(operador_a_brancha(op, etiqueta_true))
                # No ir si condición falsa
                # Si no se cumple, continuar con siguiente línea
                #   codigo.append(f"RJMP {etiqueta_true}")                  Linea optimizada no se ocupa porque se debe cumplir
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
    codigo.append("LOOP:")
    codigo.append("    RJMP LOOP")
    codigo.append("; Subrutina de espera (simulada)")
    codigo.append("ESPERAR:")
    codigo.append("    LDI R18, 100")
    codigo.append("WAIT_LOOP:")
    codigo.append("    NOP")
    codigo.append("    NOP")
    codigo.append("    NOP")
    codigo.append("    DEC R18")
    codigo.append("    BRNE WAIT_LOOP")
    codigo.append("    RET")


    return "\n".join(codigo)
