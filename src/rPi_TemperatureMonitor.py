# Temperature monitoring program for raspberry pi

import EmailAlertSender
import Si7021EnvSensor
import time
import datetime
import sys

class TempMonitor:
    def __init__(self,recipient,username,password):
        self.EAS = EmailAlertSender.EAS()
        self.EAS.login(username,password)
        self.EAS.recipient = recipient
        self.SensorObj = Si7021EnvSensor.EnvSensor()
        self.minTemp = 60 # change to input?
        self.pollTime = 30 # how often to check sensor
        self.start_mtime = time.monotonic()
        self.min_T_alert_time = time.monotonic() # time of min temp alert, to find elasped time
        self.max_min_T_alert_interval = 60*60 # max time between min temp alerts in seconds
        self.daily_digest_time = datetime.time(16,45) # time for a daily digest email
        self.last_digest_date = datetime.date.today() # initialize to today
        #self.last_digest_date = datetime.date.today() - datetime.timedelta(days=1) # initialize to yesterday's date
    # end __init__

    def temperature(self):
        return self.SensorObj.getTempF()
    
    def humidity(self):
        return self.SensorObj.getHumidity()

    def statsReset(self):
        t = self.temperature()
        self.minT = t
        self.maxT = t
        self.sumT = t
        self.count = 1
        self.meanT = t

    def updateStats(self):
        t = self.temperature()
        self.minT = min(self.minT,t)
        self.maxT = max(self.maxT,t)
        self.sumT += t
        self.count += 1
        self.meanT = self.sumT/self.count

    def curTimeString(self):
        return time.strftime("%x %I:%M%p")
    
    def getTotalElapsedTimeString(self):
        dt = datetime.timedelta(seconds=time.monotonic()-self.start_mtime)
        return "Total Elapsed Time: " + str(dt) 

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
        if (self.temperature() < self.minTemp) and ((time.monotonic() - self.min_T_alert_time) > self.max_min_T_alert_interval):
            self.min_T_alert_time = time.monotonic()
            subject = "Raspberry Pi Temperature Monitor: Low Temp Alert"
            message = self.curTimeString() + " Low Temperature\n" + self.getSensorString()
            print(subject)
            print(message)
            self.send_alert(subject,message)

    def printUpdate(self):
        print(self.curTimeString())
        print(self.getSensorString()) # print current sensors
        print("Temperature Stats:")
        statsStr = "Min: %0.1f, Max: %0.1f, Mean: %0.1f" % (self.minT, self.maxT, self.meanT)
        print(statsStr + "\n")

    def send_digest(self):
        subject =  "Raspberry Pi Temperature Monitor: Daily Digest"
        message = (self.curTimeString() + " Daily Digest\nTemperature Stats:\n" +
            "Min: %0.1f, Max: %0.1f, Mean: %0.1f, Count: %0.1f" % (self.minT, self.maxT, self.meanT, self.count)
            + "\n\nCurrent Values:\n" + self.getSensorString() + "\n\n" + self.getTotalElapsedTimeString())
        self.send_alert(subject,message)
    #end send_digest

    def check_digest_time(self):
        if self.last_digest_date < datetime.date.today() and self.daily_digest_time < datetime.datetime.now().time():
            self.last_digest_date = datetime.date.today()
            self.send_digest()
    # end check_digest_time

    def run(self):
        self.start_mtime = time.monotonic()
        self.statsReset()

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

            self.check_digest_time()

        # end while
    # end run
# end class

if __name__ == "__main__":
    recipient = sys.argv[1] # email recipient
    username = sys.argv[2] # email username (sender)
    password = sys.argv[3] # email password
    tm = TempMonitor(recipient,username,password)
    tm.run()
