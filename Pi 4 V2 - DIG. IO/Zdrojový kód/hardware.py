import threading, time, random, math, collections

try:
    import RPi.GPIO as GPIO
    REAL = True
except Exception:
    REAL = False

TRIG, ECHO = 17, 18        # HC-SR04
CLK, DIO = 24, 23          # TM1637
BRIGHTNESS = 5             # 0-7
DECIMALS = True            # True = 123.4 cm, False = celé cm
DP_DIGIT = 2               # u které číslice svítí tečka (0-3); u "hodinových" modulů jen 1 (dvojtečka)

SEGS = {"0": 0x3F, "1": 0x06, "2": 0x5B, "3": 0x4F, "4": 0x66, "5": 0x6D,
        "6": 0x7D, "7": 0x07, "8": 0x7F, "9": 0x6F, " ": 0x00, "-": 0x40}

class TM1637:
    def __init__(self, clk, dio):
        self.clk, self.dio = clk, dio
        GPIO.setup(clk, GPIO.OUT, initial=GPIO.HIGH)
        GPIO.setup(dio, GPIO.OUT, initial=GPIO.HIGH)

    def _d(self): time.sleep(0.00005)
    def _start(self):
        GPIO.output(self.dio, 1); GPIO.output(self.clk, 1); self._d()
        GPIO.output(self.dio, 0); self._d(); GPIO.output(self.clk, 0)
    def _stop(self):
        GPIO.output(self.clk, 0); GPIO.output(self.dio, 0); self._d()
        GPIO.output(self.clk, 1); self._d(); GPIO.output(self.dio, 1); self._d()
    def _write(self, b):
        for i in range(8):
            GPIO.output(self.clk, 0)
            GPIO.output(self.dio, (b >> i) & 1); self._d()
            GPIO.output(self.clk, 1); self._d()
        GPIO.output(self.clk, 0)
        GPIO.setup(self.dio, GPIO.IN); self._d()      # ACK
        GPIO.output(self.clk, 1); self._d(); GPIO.output(self.clk, 0)
        GPIO.setup(self.dio, GPIO.OUT)

    def show(self, data, on=True):
        self._start(); self._write(0x40); self._stop()
        self._start(); self._write(0xC0)
        for b in data: self._write(b)
        self._stop()
        self._start(); self._write(0x88 | BRIGHTNESS if on else 0x80); self._stop()

class Ultrasonic:
    def __init__(self):
        self.running = True
        self.display_on = True
        self.value = None
        self.history = collections.deque(maxlen=600)   # (unix čas, cm)
        if REAL:
            GPIO.setmode(GPIO.BCM); GPIO.setwarnings(False)
            GPIO.setup(TRIG, GPIO.OUT, initial=GPIO.LOW)
            GPIO.setup(ECHO, GPIO.IN)
            self.tm = TM1637(CLK, DIO)
        threading.Thread(target=self._measure_loop, daemon=True).start()
        threading.Thread(target=self._display_loop, daemon=True).start()

    def _read_cm(self):
        if not REAL:
            return round(70 + 20 * math.sin(time.time() / 3) + 5 * random.random(), 1)
        GPIO.output(TRIG, True); time.sleep(0.00001); GPIO.output(TRIG, False)
        t0 = time.time()
        while GPIO.input(ECHO) == 0:
            if time.time() - t0 > 0.03: return None
        start = time.time()
        while GPIO.input(ECHO) == 1:
            if time.time() - start > 0.03: return None
        return round((time.time() - start) * 34300 / 2, 1)

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

    def _encode(self, cm):
        n = int(round(cm * 10)) if DECIMALS else int(round(cm))
        n = min(n, 9999)
        s = str(n).rjust(4 if DECIMALS else 4)
        if DECIMALS: s = s.rjust(4, "0")[-4:] if n < 10 else s
        out = [SEGS.get(c, 0) for c in s]
        if DECIMALS: out[DP_DIGIT] |= 0x80
        return out

    def _display_loop(self):
        if not REAL: return
        prev = None
        while True:
            if not self.display_on or self.value is None:
                frame = ("off",)
                if frame != prev: self.tm.show([0, 0, 0, 0], on=False); prev = frame
            else:
                data = self._encode(self.value)
                if data != prev: self.tm.show(data); prev = data
            time.sleep(0.1)

sensor = None
def get_sensor():
    global sensor
    if sensor is None: sensor = Ultrasonic()
    return sensor
