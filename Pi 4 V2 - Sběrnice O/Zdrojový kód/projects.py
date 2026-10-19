# Přidání nového projektu: připiš položku do PROJECTS (+ případně API v app.py).
PROJECTS = [
    {
        "id": "ultrasonic",
        "title": "Ultrazvukový měřič vzdálenosti",
        "icon": "📏",
        "description": ("Senzor HC-SR04 měří vzdálenost v cm. Hodnota se zobrazuje na "
                        "LCD displeji přes I2C (1 desetinné místo) a živě v grafu "
                        "v dashboardu. Na LCD (2×16) můžeš z dashboardu poslat i vlastní text. Rozsah cca 2–400 cm."),
        "wiring": [
            {"part": "HC-SR04", "pin": "VCC", "to": "5V (fyzický pin 2)"},
            {"part": "HC-SR04", "pin": "GND", "to": "GND (pin 6)"},
            {"part": "HC-SR04", "pin": "TRIG", "to": "GPIO17 (pin 11)"},
            {"part": "HC-SR04", "pin": "ECHO", "to": "GPIO18 (pin 12) PŘES DĚLIČ 1k/2k (5V → 3,3V!)"},
            {"part": "LCD I2C", "pin": "VCC", "to": "5V (pin 4)"},
            {"part": "LCD I2C", "pin": "GND", "to": "GND (pin 9)"},
            {"part": "LCD I2C", "pin": "SDA", "to": "GPIO2 / SDA (pin 3)"},
            {"part": "LCD I2C", "pin": "SCL", "to": "GPIO3 / SCL (pin 5)"},
        ],
        "notes": ("ECHO dělič: ECHO → 1 kΩ → GPIO18, a z GPIO18 → 2 kΩ → GND. "
                  "Bez něj hrozí poškození Raspberry Pi (GPIO snáší jen 3,3 V). "
                  "I2C se řeší softwarově, v raspi-config nic zapínat nemusíš. Pokud displej nereaguje, zkus v hardware.py změnit LCD_ADDR na 0x3F a nastav kontrast šroubkem na modulu."),
    },
]
