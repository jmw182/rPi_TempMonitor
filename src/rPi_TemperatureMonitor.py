# Temperature monitoring program for raspberry pi

import EmailAlertSender
import Si7021EnvSensor
import time
import sys

class TempMonitor:
    def __init__(self,username,password):
        self.EAS = EmailAlertSender.EAS()
        self.EAS.login(username,password)
        self.SensorObj = Si7021EnvSensor.EnvSensor()
    # end __init__

    def temperature(self):
        return self.SensorObj.getTempF()
    
    def humidity(self):
        return self.SensorObj.getHumidity()

    def curTimeString(self):
        return time.strftime("%x %I:%M%p")

    def getSensorString(self):
        deg = u'\xb0'  # utf code for degree
        t = "%0.1f" % self.temperature()
        h = "%0.1f" % self.humidity()
        sensStr = "Temperature: " + t + deg + "F\nHumidity: " + h + "%"
        return sensStr

    def run(self):
        self.start_time = time.time()
        
        subject = "Raspberry Pi Temperature Monitor Startup"
        message = self.curTimeString() + " Startup\n" + self.getSensorString()
        print (subject)
        print(message)


    # end run
# end class

if __name__ == "__main__":
    username = sys.argv[1] # email username
    password = sys.argv[2] # email password
    tm = TempMonitor(username,password)
    tm.run()