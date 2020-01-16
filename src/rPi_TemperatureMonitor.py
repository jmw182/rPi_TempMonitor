# Temperature monitoring program for raspberry pi

import EmailAlertSender
import Si7021EnvSensor
import time
import sys

class TempMonitor:
    def __init__(self,recipient,username,password):
        self.EAS = EmailAlertSender.EAS()
        self.EAS.login(username,password)
        self.EAS.recipient = recipient
        self.SensorObj = Si7021EnvSensor.EnvSensor()
    # end __init__

    def temperature(self):
        return self.SensorObj.getTempF()
    
    def humidity(self):
        return self.SensorObj.getHumidity()

    def curTimeString(self):
        return time.strftime("%x %I:%M%p")

    def getSensorString(self):
        deg = "deg" #u'\xb0'  # utf code for degree, EAS currently does not support unicode
        t = "%0.1f" % self.temperature()
        h = "%0.1f" % self.humidity()
        sensStr = "Temperature: " + t + deg + "F\nHumidity: " + h + "%"
        return sensStr

    def run(self):
        self.start_time = time.time()
        
        subject = "Raspberry Pi Temperature Monitor Startup"
        message = self.curTimeString() + " Startup\n" + self.getSensorString()
        #print (subject)
        print(message)
        self.EAS.form_alert_message(subject,message)
        self.EAS.send_alert()


    # end run
# end class

if __name__ == "__main__":
    recipient = sys.argv[1] # email recipient
    username = sys.argv[2] # email username (sender)
    password = sys.argv[3] # email password
    tm = TempMonitor(recipient,username,password)
    tm.run()