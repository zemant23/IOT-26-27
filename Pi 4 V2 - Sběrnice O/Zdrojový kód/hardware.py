import threading, time, random, math, collections, unicodedata

try:
    import RPi.GPIO as GPIO
    REAL = True
except Exception:
    REAL = False
TRIG, ECHO = 17, 18        # HC-SR04
LCD_ADDR = 0x27            # I2C adresa modulu (nejčastěji 0x27, někdy 0x3F)
SDA, SCL = 2, 3            # softwarové I2C, není potřeba zapínat I2C v raspi-config
LCD_COLS, LCD_ROWS = 16, 2
CAL_OFFSET_CM = 0.0        # přičte se k naměřené hodnotě (záporné číslo = ubere)
CAL_SCALE = 1.0            # násobek, např. 0.98 pokud měří o 2 % víc

class SoftI2C:
    """Jednoduché I2C přes libovolné GPIO (open-drain: pin buď 'pustím' = 1 přes pull-up, nebo stáhnu k 0)."""
    def __init__(self, sda, scl):
        self.sda, self.scl = sda, scl
        self._hi(sda); self._hi(scl)
    def _hi(self, p): GPIO.setup(p, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    def _lo(self, p): GPIO.setup(p, GPIO.OUT, initial=GPIO.LOW)
    def _byte(self, b):
        for i in range(7, -1, -1):
            (self._hi if (b >> i) & 1 else self._lo)(self.sda)
            self._hi(self.scl); self._lo(self.scl)
        self._hi(self.sda); self._hi(self.scl)           # ACK
        ack = GPIO.input(self.sda) == 0
        self._lo(self.scl)
        return ack
    def write_byte(self, addr, data):
        self._hi(self.sda); self._hi(self.scl)
        self._lo(self.sda); self._lo(self.scl)            # START
        ok = self._byte(addr << 1) and self._byte(data)
        self._lo(self.sda); self._hi(self.scl); self._hi(self.sda)   # STOP
        if not ok: raise OSError("LCD neodpovídá (adresa/zapojení?)")

class LCD:
    """HD44780 přes I2C expander PCF8574 (4bitový režim)."""
    RS, EN, BL = 0x01, 0x04, 0x08
    def __init__(self, addr, cols, rows):
        self.addr, self.cols, self.rows = addr, cols, rows
        self.bl = self.BL
        self.bus = SoftI2C(SDA, SCL)
        for b in (0x33, 0x32, 0x28, 0x0C, 0x06, 0x01):
            self._send(b, 0); time.sleep(0.003)

    def _pulse(self, d):
        self.bus.write_byte(self.addr, d | self.EN | self.bl); time.sleep(0.0005)
        self.bus.write_byte(self.addr, (d & ~self.EN) | self.bl); time.sleep(0.0005)
    def _send(self, byte, mode):
        self._pulse((byte & 0xF0) | mode)
        self._pulse(((byte << 4) & 0xF0) | mode)
    def backlight(self, on):
        self.bl = self.BL if on else 0
        self.bus.write_byte(self.addr, self.bl)
    def clear(self):
        self._send(0x01, 0); time.sleep(0.003)
    def write(self, row, text):
        offs = (0x00, 0x40, self.cols, 0x40 + self.cols)[row]
        self._send(0x80 | offs, 0)
        for ch in text.ljust(self.cols)[:self.cols]:
            self._send(ord(ch), self.RS)

class Ultrasonic:
    def __init__(self):
        self.running = True
        self.display_on = True
        self.value = None
        self.lcd_error = None
        self.mode = "distance"          # "distance" | "text"
        self.text = ("", "")
        self.history = collections.deque(maxlen=600)   # (unix čas, cm)
        self.lcd = None
        if REAL:
            GPIO.setmode(GPIO.BCM); GPIO.setwarnings(False)
            GPIO.setup(TRIG, GPIO.OUT, initial=GPIO.LOW)
            GPIO.setup(ECHO, GPIO.IN)
            try:
                self.lcd = LCD(LCD_ADDR, LCD_COLS, LCD_ROWS)
            except Exception as e:
                self.lcd_error = str(e)
                print("LCD nenalezen (zkontroluj I2C a adresu):", e)
        threading.Thread(target=self._measure_loop, daemon=True).start()
        threading.Thread(target=self._display_loop, daemon=True).start()

    def _read_cm(self):
        if not REAL:
            return round(CAL_OFFSET_CM + 70 + 20 * math.sin(time.time() / 3) + 5 * random.random(), 1)
        GPIO.output(TRIG, True); time.sleep(0.00001); GPIO.output(TRIG, False)
        t0 = time.time()
        while GPIO.input(ECHO) == 0:
            if time.time() - t0 > 0.03: return None
        start = time.time()
        while GPIO.input(ECHO) == 1:
            if time.time() - start > 0.03: return None
        return round((time.time() - start) * 34300 / 2 * CAL_SCALE + CAL_OFFSET_CM, 1)

    def _measure_loop(self):
        while True:
            if self.running:
                vals = [v for v in (self._read_cm() for _ in range(3)) if v is not None]
                if vals:
                    self.value = sorted(vals)[len(vals) // 2]
                    self.history.append((time.time(), self.value))
                else:
                    self.value = None
            time.sleep(0.15)

    def set_text(self, l1, l2):
        clean = lambda t: unicodedata.normalize("NFKD", str(t)).encode("ascii", "ignore").decode()[:LCD_COLS]
        self.text = (clean(l1), clean(l2)); self.mode = "text"

    def _display_loop(self):
        if not self.lcd: return
        prev = None
        while True:
            try:
                if not self.display_on:
                    state = "off"
                elif self.mode == "text":
                    state = self.text
                elif self.value is None:
                    state = ("Vzdalenost:", "-- mimo rozsah")
                else:
                    state = ("Vzdalenost:", f"{self.value:.1f} cm")
                if state != prev:
                    if state == "off":
                        self.lcd.clear(); self.lcd.backlight(False)
                    else:
                        self.lcd.backlight(True)
                        self.lcd.write(0, state[0]); self.lcd.write(1, state[1])
                    prev = state
            except Exception as e:
                self.lcd_error = str(e); prev = None
            time.sleep(0.2)

sensor = None
def get_sensor():
    global sensor
    if sensor is None: sensor = Ultrasonic()
    return sensor
