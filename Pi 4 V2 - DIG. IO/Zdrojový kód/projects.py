# Přidání nového projektu: připiš položku do PROJECTS (+ případně API v app.py).
PROJECTS = [
    {
        "id": "ultrasonic",
        "title": "Ultrazvukový měřič vzdálenosti",
        "icon": "📏",
        "description": ("Senzor HC-SR04 měří vzdálenost v cm. Hodnota se zobrazuje na "
                        "4místném displeji TM1637 (1 desetinné místo) a živě v grafu "
                        "v dashboardu. Rozsah cca 2–400 cm."),
        "wiring": [
            {"part": "HC-SR04", "pin": "VCC", "to": "5V (fyzický pin 2)"},
            {"part": "HC-SR04", "pin": "GND", "to": "GND (pin 6)"},
            {"part": "HC-SR04", "pin": "TRIG", "to": "GPIO17 (pin 11)"},
            {"part": "HC-SR04", "pin": "ECHO", "to": "GPIO18 (pin 12) PŘES DĚLIČ 1k/2k (5V → 3,3V!)"},
            {"part": "TM1637 displej", "pin": "VCC", "to": "5V (pin 4) nebo 3,3V (pin 1)"},
            {"part": "TM1637 displej", "pin": "GND", "to": "GND (pin 9)"},
            {"part": "TM1637 displej", "pin": "CLK", "to": "GPIO24 (pin 18)"},
            {"part": "TM1637 displej", "pin": "DIO", "to": "GPIO23 (pin 16)"},
        ],
        "notes": ("ECHO dělič: ECHO → 1 kΩ → GPIO18, a z GPIO18 → 2 kΩ → GND. "
                  "Bez něj hrozí poškození Raspberry Pi (GPIO snáší jen 3,3 V). "
                  "Piny TRIG/ECHO a CLK/DIO se mění v hardware.py."),
    },
]
