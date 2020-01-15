import board
import busio
import adafruit_si7021

# Si7021 Temperature & Humidity Environmetal Sensor
class EnvSensor:

    def __init__(self):
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.sensor = adafruit_si7021.SI7021(self.i2c)

    def getTempCelsius(self):
        return self.sensor.temperature

    def getTempF(self):
        return self.getTempCelsius() * 9.0/5.0 + 32.0

    def getHumidity(self):
        return self.sensor.relative_humidity

