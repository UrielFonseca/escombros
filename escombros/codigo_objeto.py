import re

def generar_codigo_objeto(codigo_intermedio: str) -> str:
    codigo = [
        '.include "C:/Users/moren/Downloads/avra-1.3.0/avra/includes/m328pdef.inc"',
        '',
        '.def temp     = r16',
        '.def counter  = r17',
        '.def sensor   = r19',
        '.def angle    = r18',
        '',
        '.org 0x0000',
        '    rjmp RESET',
        '',
        'RESET:',
        '    ; Inicializar stack',
        '    ldi temp, low(RAMEND)',
        '    out SPL, temp',
        '    ldi temp, high(RAMEND)',
        '    out SPH, temp',
        '',
        '    ; Configurar PB1 (pin 9) y PB2 (pin 10) como salidas',
        '    sbi DDRB, PB1',
        '    sbi DDRB, PB2',
        '',
        '    ; Configurar ADC (AVcc ref, canal 0)',
        '    ldi temp, (1 << REFS0)',
        '    sts ADMUX, temp',
        '    ldi temp, (1 << ADEN) | (1 << ADPS2) | (1 << ADPS1) | (1 << ADPS0)',
        '    sts ADCSRA, temp',
        ''
    ]

    plantas = {}
    planta_actual = None
    registro_base = 30
    propiedades_planta = ["PH", "HUMEDAD", "CE", "RANGOHUMEDAD", "RANGOPH"]

    def valor_a_registro(valor, destino):
        if "." in valor:
            planta, prop = valor.split(".")
            reg = plantas.get(planta.lower(), {}).get(prop.lower())
            if reg:
                return [f"MOV {destino}, {reg}"]
            else:
                return [f"; [!] {planta}.{prop} no declarado"]
        else:
            try:
                val_int = int(float(valor))
                return [f"LDI {destino}, {val_int}"]
            except:
                return [f"; [!] Valor inválido: {valor}"]

    def operador_a_branch(op, etiqueta):
        return {
            ">": f"BRSH {etiqueta}",
            "<": f"BRLO {etiqueta}",
            "==": f"BREQ {etiqueta}",
            "!=": f"BRNE {etiqueta}"
        }.get(op, f"; [!] Operador '{op}' no implementado")

    def plantilla_aplicar_pulsos(pin: str):
        return [
            f"; Pulso para mover servo en {pin} a 90° (1.5 ms)",
            f"    ldi angle, 150",
            f"    sbi PORTB, {pin}",
            f"    rcall DELAY_10US_MULT",
            f"    cbi PORTB, {pin}",
            f"    rcall DELAY_18MS",

            f"; Esperar 500 ms antes de regresar",
            f"    ldi counter, 25",
            f"wait_500ms_{pin}:",
            f"    rcall DELAY_20MS",
            f"    dec counter",
            f"    brne wait_500ms_{pin}",

            f"; Pulso para mover servo en {pin} a 0° (1.0 ms)",
            f"    ldi angle, 100",
            f"    sbi PORTB, {pin}",
            f"    rcall DELAY_18MS",
            f"    cbi PORTB, {pin}",
            f"    rcall DELAY_10US_MULT",
            ''
        ]


    for linea in codigo_intermedio.splitlines():
        linea = linea.strip()
        if not linea:
            continue

        if linea.endswith(":"):
            codigo.append(f"{linea}")
            continue

        if linea.upper().startswith("PLANTA"):
            planta_actual = linea.split()[1].lower()
            plantas[planta_actual] = {}
            continue

        if planta_actual and any(re.match(rf'^{prop}\b', linea.upper()) for prop in propiedades_planta):
            partes = linea.split()
            if len(partes) >= 2:
                prop = partes[0].lower()
                val = partes[1]
                reg = f"R{registro_base}"
                plantas[planta_actual][prop] = reg

                # Escalar valores grandes para humedad y rangohumedad
                if prop in ["humedad", "rangohumedad"]:
                    try:
                        val_escalado = int(float(val) / 4)
                        codigo.append(f"LDI {reg}, {val_escalado} ")
                    except:
                        codigo.append(f"; [!] Error al escalar {planta_actual}.{prop} = {val}")
                else:
                    try:
                        codigo.append(f"LDI {reg}, {int(float(val))}    ; {planta_actual}.{prop} = {val}")
                    except:
                        codigo.append(f"; [!] Valor inválido para {planta_actual}.{prop}: {val}")

                registro_base -= 1
            continue


        if "IF" in linea and "GOTO" in linea:
            m = re.match(r"IF\s+(.+)\s+(==|!=|>|<)\s+(.+)\s+GOTO\s+(\w+)", linea, re.I)
            if m:
                izq, op, der, etiqueta = m.groups()
                sensor_reg = "sensor"
                comp_reg = "R20"

                codigo += [
                    "; Leer sensor humedad",
                    "    lds temp, ADCSRA",
                    "    ori temp, (1 << ADSC)",
                    "    sts ADCSRA, temp",
                    "WAIT_ADC:",
                    "    lds temp, ADCSRA",
                    "    sbrc temp, ADSC",
                    "    rjmp WAIT_ADC",
                    "    lds sensor, ADCL    ; solo 8 bits bajos"
                ]

                if izq.upper() == "SENSORHUMEDAD":
                    codigo += valor_a_registro(der, comp_reg)
                    codigo.append(f"    cp {sensor_reg}, {comp_reg}")
                elif der.upper() == "SENSORHUMEDAD":
                    codigo += valor_a_registro(izq, comp_reg)
                    codigo.append(f"    cp {comp_reg}, {sensor_reg}")
                else:
                    codigo += valor_a_registro(izq, "R20")
                    codigo += valor_a_registro(der, "R21")
                    codigo.append("    cp R20, R21")

                codigo.append(f"    {operador_a_branch(op, etiqueta)}")
                continue

        if linea.startswith("GOTO"):
            etiqueta = linea.split()[1]
            codigo.append(f"    RJMP {etiqueta}")
            continue

        if linea.lower().startswith("call"):
            partes = linea.split("call", 1)[1].split(",")
            instr = partes[0].strip().upper()
            valor = partes[1].strip().upper() if len(partes) > 1 else ""

            if instr == "APLICAR":
                if valor == "CAL":
                    codigo += plantilla_aplicar_pulsos("PB1")
                elif valor == "AZUFRE":
                    codigo += plantilla_aplicar_pulsos("PB2")
                else:
                    codigo.append(f"; [!] APLICAR tipo no válido: {valor}")
            continue

        codigo.append(f"; [!] Línea no reconocida: {linea}")

    # Fin y bucle infinito
    codigo += [
        "",
        "FIN:",
        "    RJMP FIN",
        "",
        "; Subrutinas de retardo",
        "DELAY_10US_MULT:",
        "    mov counter, angle",
        "LOOP_10US_MULT:",
        "    rcall DELAY_10US",
        "    dec counter",
        "    brne LOOP_10US_MULT",
        "    ret",
        "",
        "DELAY_10US:",
        "    ldi temp, 32",
        "LOOP10:",
        "    dec temp",
        "    brne LOOP10",
        "    ret",
        "",
        "DELAY_18MS:",
        "    ldi counter, 180",
        "LOOP18:",
        "    rcall DELAY_100US",
        "    dec counter",
        "    brne LOOP18",
        "    ret",
        "",
        "DELAY_100US:",
        "    ldi temp, 100",
        "LOOP100:",
        "    dec temp",
        "    brne LOOP100",
        "    ret",
        "DELAY_20MS:",
        "   ldi counter, 200",
        "loop_20ms:",
        "   rcall DELAY_100US",
        "    dec counter",
        "    brne loop_20ms",
        "    ret"
    ]

    return "\n".join(codigo)
