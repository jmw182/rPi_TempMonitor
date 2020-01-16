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
        self.minTemp = 60 # change to input?
        self.pollTime = 30 # how often to check sensor
    # end __init__

    def temperature(self):
        return self.SensorObj.getTempF()
    
    def humidity(self):
        return self.SensorObj.getHumidity()

    def curTimeString(self):
        return time.strftime("%x %I:%M%p")

    def getSensorString(self):
        deg = " deg" #u'\xb0'  # utf code for degree, EAS currently does not support unicode
        t = "%0.1f" % self.temperature()
        h = "%0.1f" % self.humidity()
        sensStr = "Temperature: " + t + deg + "F\nHumidity: " + h + "%"
        return sensStr

    def send_alert(self,subject,message):
        self.EAS.form_alert_message(subject,message)
        self.EAS.send_alert()

    def checkMinTemp(self):
        if self.temperature() < self.minTemp:
            subject = "Raspberry Pi Temperature Monitor: Low Temp Alert"
            message = self.curTimeString() + " Low Temperature\n" + self.getSensorString()
            print(subject)
            print(message)
            self.send_alert(subject,message)

    def updateStats(self):
        t = self.temperature()
        self.minT = min(self.minT,t)
        self.maxT = max(self.maxT,t)
        self.sumT += t
        self.count += 1
        self.meanT = self.sumT/self.count

    def printUpdate(self):
        print(self.curTimeString())
        print(self.getSensorString()) # print current sensors
        print("Temperature Stats:")
        statsStr = "Min: %0.1f, Max: %0.1f, Mean: %0.1f" % (self.minT, self.maxT, self.meanT)
        print(statsStr + "\n")

    def run(self):
        self.start_time = time.time()
        self.minT = self.temperature()
        self.maxT = self.minT
        self.sumT = self.minT
        self.meanT = self.minT
        self.count = 1

        subject = "Raspberry Pi Temperature Monitor: Startup"
        message = self.curTimeString() + " Startup\n" + self.getSensorString()
        print(subject)
        print(message)
        #self.send_alert(subject,message)

        while True:
            time.sleep(self.pollTime) # sleep 30 s

            self.checkMinTemp() # check that min temp is satisfied

            self.updateStats()
            self.printUpdate()

        # end while
    # end run
# end class

if __name__ == "__main__":
    recipient = sys.argv[1] # email recipient
    username = sys.argv[2] # email username (sender)
    password = sys.argv[3] # email password
    tm = TempMonitor(recipient,username,password)
    tm.run()
