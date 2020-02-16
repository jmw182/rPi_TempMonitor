# Temperature monitoring program for raspberry pi

import EmailAlertSender
import Si7021EnvSensor
import time
import datetime
import sys
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import csv
import pandas
import os
from pandas.plotting import register_matplotlib_converters

class TempMonitor:
    def __init__(self,recipient,username,password):
        self.EAS = EmailAlertSender.EAS()
        self.EAS.login(username,password)
        self.EAS.recipient = recipient
        self.SensorObj = Si7021EnvSensor.EnvSensor()
        self.minTemp = 58 # change to input?
        self.pollTime = 30 # how often to check sensor
        self.start_mtime = time.monotonic()
        self.min_T_alert_time = time.monotonic() # time of min temp alert, to find elasped time
        self.max_min_T_alert_interval = 60*60 # max time between min temp alerts in seconds
        self.daily_digest_time = datetime.time(16,45) # time for a daily digest email
        if datetime.datetime.now().time() < datetime.time(10,0): # if earlier than 10 am, send digest today
            self.last_digest_date = datetime.date.today() - datetime.timedelta(days=1) # initialize to yesterday's date
        else: # do not send digest until tomorrow
            self.last_digest_date = datetime.date.today() # initialize to today
        self.tmp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))),'tmp')
        self.csv_file = os.path.join(self.tmp_dir,'tmp.csv')
        self.temp_plot = os.path.join(self.tmp_dir,'temp_plot.png')
        self.humid_plot = os.path.join(self.tmp_dir,'humid_plot.png')

        self._temperature = 0 # store values as private variables in case of sensor access error
        self._humidity = 0

        register_matplotlib_converters() 
    # end __init__

    def temperature(self):
        try:
            self._temperature = self.SensorObj.getTempF()
        except:
            print("Error accessing temperature")
        return self._temperature
    
    def humidity(self):
        try:
            self._humidity = self.SensorObj.getHumidity()
        except:
            print("Error accessing humidity")
        return self._humidity

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

    def open_csv_w(self): # open csv for writing (clear contents)
        self.csv = open(self.csv_file,'w') # open for writing and replace contents
        self.csv_writer = csv.writer(self.csv)
    
    def open_csv_a(self): # open csv for writing, append
        self.csv = open(self.csv_file,'a')
        self.csv_writer = csv.writer(self.csv)
    
    def open_csv_r(self): # open csv for reading
        self.csv = open(self.csv_file,'rb')

    def close_csv(self): # closes csv
        self.csv.close()

    def write_to_csv(self):
        self.csv_writer.writerow([datetime.datetime.now(),self.temperature(),self.humidity()])
        # force write to disk
        self.csv.flush()
        os.fsync(self.csv.fileno())

    def read_csv_to_df(self):
        self.close_csv()
        self.open_csv_r()
        df = pandas.read_csv(self.csv,sep=',',names=['time','temperature','humidity']) # read as data frame
        self.close_csv()
        self.open_csv_w() # resets csv file and opens for writing
        return df

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

    def printUpdate(self):
        print(self.curTimeString())
        print(self.getSensorString()) # print current sensors
        print("Temperature Stats:")
        statsStr = "Min: %0.1f, Max: %0.1f, Mean: %0.1f" % (self.minT, self.maxT, self.meanT)
        print(statsStr + "\n")
    
    def send_alert(self,subject,message,images = None):
        try:
            self.EAS.form_alert_message(subject=subject,body=message,images=images)
            self.EAS.send_alert()
        except:
            print("error sending alert\n")

    def checkMinTemp(self):
        if (self.temperature() < self.minTemp) and ((time.monotonic() - self.min_T_alert_time) > self.max_min_T_alert_interval):
            self.min_T_alert_time = time.monotonic()
            subject = "Raspberry Pi Temperature Monitor: Low Temp Alert"
            message = (self.curTimeString() + " Low Temperature\n" + self.getSensorString() + "\n\n" +
                "Min: %0.1f, Max: %0.1f, Mean: %0.1f, Count: %0.1f" % (self.minT, self.maxT, self.meanT, self.count))
            print(subject)
            print(message)
            self.send_alert(subject,message)

    def create_digest_plots(self):
        data = self.read_csv_to_df()
        t_fmt = mdates.DateFormatter('%H:%M')
        t = mdates.datestr2num(data["time"])
        plt.figure()
        plt.plot_date(t,data['temperature'],'-')
        # plt.plot(data['time'],data['temperature'])
        plt.xlabel('Time')
        plt.ylabel('Temperature')
        plt.title(datetime.date.today().strftime('%x'))
        plt.gcf().autofmt_xdate()
        plt.gca().xaxis.set_major_formatter(t_fmt)
        plt.savefig(self.temp_plot)

        plt.figure()
        plt.plot_date(t,data['humidity'],'-')
        #plt.plot(data['time'],data['humidity'])
        plt.xlabel('Time')
        plt.ylabel('Humidity')
        plt.title(datetime.date.today().strftime('%x'))
        plt.gcf().autofmt_xdate()
        plt.gca().xaxis.set_major_formatter(t_fmt)
        plt.savefig(self.humid_plot)
    # end create_digest_plots

    def send_digest(self):
        self.create_digest_plots()
        subject =  "Raspberry Pi Temperature Monitor: Daily Digest"
        message = (self.curTimeString() + " Daily Digest\nTemperature Stats:\n" +
            "Min: %0.1f, Max: %0.1f, Mean: %0.1f, Count: %0.1f" % (self.minT, self.maxT, self.meanT, self.count)
            + "\n\nCurrent Values:\n" + self.getSensorString() + "\n\n" + self.getTotalElapsedTimeString())
        self.send_alert(subject,message,[self.temp_plot,self.humid_plot])
    # end send_digest

    def check_digest_time(self):
        if self.last_digest_date < datetime.date.today() and self.daily_digest_time < datetime.datetime.now().time():
            self.last_digest_date = datetime.date.today()
            self.send_digest()
            self.statsReset()
    # end check_digest_time

    def run(self):
        self.start_mtime = time.monotonic()
        self.statsReset()
        self.open_csv_a() # opens and appends

        subject = "Raspberry Pi Temperature Monitor: Startup"
        message = self.curTimeString() + " Startup\n" + self.getSensorString()
        print(subject)
        print(message)
        self.send_alert(subject,message)

        while True:
            time.sleep(self.pollTime) # sleep 30 s

            self.checkMinTemp() # check that min temp is satisfied

            self.updateStats()
            self.printUpdate()
            self.write_to_csv()

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
