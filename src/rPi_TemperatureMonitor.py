# Temperature monitoring program for raspberry pi

import EmailAlertSender
import Si7021EnvSensor
import time
import datetime
import calendar
import sys
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import csv
import pandas
import os
from pandas.plotting import register_matplotlib_converters
import gzip
import shutil

class TempMonitor:
    def __init__(self,recipient,username,password):
        self.sendDailyDigestFlag = False
        self.sendWeeklyDigestFlag = True
        self.sendStartupAlertFlag = True
        self.sendDailyDataFlag = False # flag to send data file with daily digest email, in addition to plots (only if sendDailyDigestFlag is True)
        self.sendWeeklyDataFlag = False # flag to send data file with weekly digest email, in addition to plots (only if sendWeeklyDigestFlag is True)
        self.EAS = EmailAlertSender.EAS()
        self.EAS.login(username,password)
        self.EAS.recipient = recipient
        self.SensorObj = Si7021EnvSensor.EnvSensor()
        self.minTemp = 65.2 # change to input?
        self.maxTemp = 90
        self.pollTime = 30 # how often to check sensor
        self.start_mtime = time.monotonic()
        self.last_T_alert_time = time.monotonic() # time of min temp alert, to find elasped time
        self.max_T_alert_interval = 60.0*60.0 # max time between min temp alerts in seconds
        self.daily_digest_time = datetime.time(16,45) # time for a daily digest email
        self.weekly_digest_time = self.daily_digest_time
        self.weekly_digest_day = 'Friday'
        if datetime.datetime.now().time() < datetime.time(10,0): # if earlier than 10 am, send digest today
            self.last_digest_date = datetime.date.today() - datetime.timedelta(days=1) # initialize to yesterday's date
        else: # do not send digest until tomorrow
            self.last_digest_date = datetime.date.today() # initialize to today
        self.last_weekly_digest_date = self.last_digest_date
        self.tmp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))),'tmp')
        self.daily_csv_file = os.path.join(self.tmp_dir,'tmp_daily.csv')
        self.daily_gz_file = os.path.join(self.tmp_dir,'tmp_daily.csv.gz')
        self.weekly_csv_file = os.path.join(self.tmp_dir,'tmp_weekly.csv')
        self.weekly_gz_file = os.path.join(self.tmp_dir,'tmp_weekly.csv.gz')
        self.temp_plot = os.path.join(self.tmp_dir,'temp_plot_DOW.png') # DOW will be replaced with day of week
        self.humid_plot = os.path.join(self.tmp_dir,'humid_plot_DOW.png') # DOW will be replaced with day of week

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

    def weeklyStatsReset(self):
        t = self.temperature()
        self.minT_week = t
        self.maxT_week = t
        self.sumT_week = t
        self.count_week = 1
        self.meanT_week = t

    def updateStats(self):
        t = self.temperature()
        self.minT = min(self.minT,t)
        self.maxT = max(self.maxT,t)
        self.sumT += t
        self.count += 1
        self.meanT = self.sumT/self.count

        self.minT_week = min(self.minT_week,t)
        self.maxT_week = max(self.maxT_week,t)
        self.sumT_week += t
        self.count_week += 1
        self.meanT_week = self.sumT_week/self.count_week

    def open_csv_w(self,tfdw = 'd'): # open csv for writing (clear contents)
        if tfdw.lower() == 'w': # weekly
            filename = self.weekly_csv_file
            self.weekly_csv = open(filename,'w') # open for writing and replace contents
            self.weekly_csv_writer = csv.writer(self.weekly_csv)
        else: # assume daily
            filename = self.daily_csv_file
            self.daily_csv = open(filename,'w')
            self.daily_csv_writer = csv.writer(self.daily_csv)
    
    def open_csv_a(self,tfdw = 'd'): # open csv for writing, append
        if tfdw.lower() == 'w': # weekly
            filename = self.weekly_csv_file
            self.weekly_csv = open(filename,'a')
            self.weekly_csv_writer = csv.writer(self.weekly_csv)
        else: # assume daily
            filename = self.daily_csv_file
            self.daily_csv = open(filename,'a')
            self.daily_csv_writer = csv.writer(self.daily_csv)
    
    def open_csv_r(self,tfdw = 'd'): # open csv for reading
        if tfdw.lower() == 'w': # weekly
            filename = self.weekly_csv_file
            self.weekly_csv = open(filename,'rb')
        else: # assume daily
            filename = self.daily_csv_file
            self.daily_csv = open(filename,'rb')

    def close_csv(self,tfdw = 'd'): # closes csv
        if tfdw.lower() == 'w': # weekly
            self.weekly_csv.close()
        else: # assume daily
            self.daily_csv.close()

    def write_to_csv(self,tfdw = 'd'):
        if tfdw.lower() == 'w': # weekly
            csv_file = self.weekly_csv
            csv_writer = self.weekly_csv_writer
        else: # assume daily
            csv_file = self.daily_csv
            csv_writer = self.daily_csv_writer

        row = [datetime.datetime.now(),self.temperature(),self.humidity()]
        csv_writer.writerow(row)
        # force write to disk
        csv_file.flush()
        os.fsync(csv_file.fileno())

    def zip_csv(self,tfdw = 'd'):
        if tfdw.lower() == 'w': # weekly
            csv_file = self.weekly_csv_file
            gz_file = self.weekly_gz_file
        else: # assume daily
            csv_file = self.daily_csv_file
            gz_file = self.daily_gz_file

        with open(csv_file, 'rb') as f_in:
            with gzip.open(gz_file, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
    # end zip_csv

    def read_csv_to_df(self,tfdw = 'd',reset = True):
        self.close_csv(tfdw)
        self.open_csv_r(tfdw)

        if tfdw.lower() == 'w': # weekly
            csv_file = self.weekly_csv
        else: # assume daily
            csv_file = self.daily_csv

        df = pandas.read_csv(csv_file,sep=',',names=['time','temperature','humidity']) # read as data frame
        self.close_csv(tfdw)
        self.zip_csv(tfdw)
        if reset == True:
            self.open_csv_w(tfdw) # resets csv file and opens for writing
        else:
            self.open_csv_a(tfdw) # appends to csv
        return df

    def curTimeString(self):
        return time.strftime("%x %I:%M%p")

    def curDayOfWeekString(self):
        return calendar.day_name[datetime.date.today().weekday()]
    
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
        print("Temperature Daily Stats:")
        statsStr = "Min: %0.1f, Max: %0.1f, Mean: %0.1f" % (self.minT, self.maxT, self.meanT)
        print(statsStr + "\n")
        print("Temperature Weekly Stats:")
        statsStrWeek = "Min: %0.1f, Max: %0.1f, Mean: %0.1f" % (self.minT_week, self.maxT_week, self.meanT_week)
        print(statsStrWeek + "\n")
    
    def send_alert(self,subject,message,images = None,attachments = None):
        try:
            self.EAS.form_alert_message(subject=subject,body=message,recipient=self.EAS.recipient,images=images,attachments=attachments)
            self.EAS.send_alert()
        except:
            print("error sending alert\n")

    def checkTempLimits(self):
        badTemp = False
        if (self.temperature() < self.minTemp) and ((time.monotonic() - self.last_T_alert_time) > self.max_T_alert_interval):
            badTemp = True
            self.last_T_alert_time = time.monotonic()
            subject = "Raspberry Pi Temperature Monitor: Low Temp Alert"
            message = (self.curTimeString() + " Low Temperature\n" + self.getSensorString() + "\n\n")
        elif (self.temperature() > self.maxTemp) and ((time.monotonic() - self.last_T_alert_time) > self.max_T_alert_interval):
            badTemp = True
            self.last_T_alert_time = time.monotonic()
            subject = "Raspberry Pi Temperature Monitor: High Temp Alert"
            message = (self.curTimeString() + " High Temperature\n" + self.getSensorString() + "\n\n")

        if badTemp:
            message += ("Min: %0.1f, Max: %0.1f, Mean: %0.1f, Count: %0.1f" % (self.minT, self.maxT, self.meanT, self.count))
            print(subject)
            print(message)
            self.send_alert(subject,message)

    def create_daily_digest_plots(self):
        temp_plot_name = self.temp_plot.replace('DOW', self.curDayOfWeekString() )
        humid_plot_name = self.humid_plot.replace('DOW', self.curDayOfWeekString() )

        data = self.read_csv_to_df()
        t_fmt = mdates.DateFormatter('%H:%M')
        plt_title = datetime.date.today().strftime('%x')
        t = mdates.datestr2num(data["time"])
        plt.figure()
        plt.plot_date(t,data['temperature'],'-')
        # plt.plot(data['time'],data['temperature'])
        plt.xlabel('Time')
        plt.ylabel('Temperature')
        plt.title(plt_title)
        plt.gcf().autofmt_xdate()
        plt.gca().xaxis.set_major_formatter(t_fmt)
        plt.savefig(temp_plot_name)

        plt.figure()
        plt.plot_date(t,data['humidity'],'-')
        #plt.plot(data['time'],data['humidity'])
        plt.xlabel('Time')
        plt.ylabel('Humidity')
        plt.title(plt_title)
        plt.gcf().autofmt_xdate()
        plt.gca().xaxis.set_major_formatter(t_fmt)
        plt.savefig(humid_plot_name)
    # end create_daily_digest_plots

    def create_weekly_digest_plots(self):
        temp_plot_name = self.temp_plot.replace('DOW', 'week')
        humid_plot_name = self.humid_plot.replace('DOW', 'week')

        data = self.read_csv_to_df('w')
        t_fmt = mdates.DateFormatter('%a %H:%M')
        plt_title = datetime.date.today().strftime('%x')
        t = mdates.datestr2num(data["time"])
        plt.figure()
        plt.plot_date(t,data['temperature'],'-')
        # plt.plot(data['time'],data['temperature'])
        plt.xlabel('Time')
        plt.ylabel('Temperature')
        plt.title(plt_title)
        plt.gcf().autofmt_xdate()
        plt.gca().xaxis.set_major_formatter(t_fmt)
        plt.savefig(temp_plot_name)

        plt.figure()
        plt.plot_date(t,data['humidity'],'-')
        #plt.plot(data['time'],data['humidity'])
        plt.xlabel('Time')
        plt.ylabel('Humidity')
        plt.title(plt_title)
        plt.gcf().autofmt_xdate()
        plt.gca().xaxis.set_major_formatter(t_fmt)
        plt.savefig(humid_plot_name)
    # end create_weekly_digest_plots

    def send_daily_digest(self):
        self.create_daily_digest_plots()
        if self.sendDailyDigestFlag:
            temp_plot_name = self.temp_plot.replace('DOW', self.curDayOfWeekString() )
            humid_plot_name = self.humid_plot.replace('DOW', self.curDayOfWeekString() )
            
            subject =  "Raspberry Pi Temperature Monitor: Daily Digest"
            message = (self.curTimeString() + " Daily Digest\nTemperature Stats:\n" +
                "Min: %0.1f, Max: %0.1f, Mean: %0.1f, Count: %0.1f" % (self.minT, self.maxT, self.meanT, self.count)
                + "\n\nCurrent Values:\n" + self.getSensorString() + "\n\n" + self.getTotalElapsedTimeString())
            if self.sendDailyDataFlag:
                self.send_alert(subject,message,[temp_plot_name, humid_plot_name],[self.daily_gz_file])
            else:
                self.send_alert(subject,message,[temp_plot_name, humid_plot_name])
    # end send_daily_digest

    def send_weekly_digest(self):
        self.create_weekly_digest_plots()
        if self.sendWeeklyDigestFlag:
            temp_plot_name = self.temp_plot.replace('DOW', 'week')
            humid_plot_name = self.humid_plot.replace('DOW', 'week')

            subject =  "Raspberry Pi Temperature Monitor: Weekly Digest"
            message = (self.curTimeString() + " Weekly Digest\nTemperature Stats:\n" +
                "Min: %0.1f, Max: %0.1f, Mean: %0.1f, Count: %0.1f" % (self.minT_week, self.maxT_week, self.meanT_week, self.count_week)
                + "\n\nCurrent Values:\n" + self.getSensorString() + "\n\n" + self.getTotalElapsedTimeString())
            if self.sendWeeklyDataFlag:
                self.send_alert(subject,message,[temp_plot_name, humid_plot_name],[self.weekly_gz_file])
            else:
                self.send_alert(subject,message,[temp_plot_name, humid_plot_name])
    # end send_weekly_digest

    def check_digest_time(self):
        if self.last_digest_date < datetime.date.today() and self.daily_digest_time < datetime.datetime.now().time():
            self.last_digest_date = datetime.date.today()
            self.send_daily_digest()
            self.statsReset()

        if self.weekly_digest_day == self.curDayOfWeekString() and self.last_weekly_digest_date < datetime.date.today() and self.weekly_digest_time < datetime.datetime.now().time():
            self.last_weekly_digest_date = datetime.date.today()
            self.send_weekly_digest()
            self.weeklyStatsReset()

    # end check_digest_time

    def run(self):
        self.start_mtime = time.monotonic()
        self.statsReset()
        self.weeklyStatsReset()
        self.open_csv_a() # opens and appends
        self.open_csv_a('w')

        subject = "Raspberry Pi Temperature Monitor: Startup"
        message = self.curTimeString() + " Startup\n" + self.getSensorString()
        print(subject)
        print(message)
        if self.sendStartupAlertFlag:
            self.send_alert(subject,message)

        while True:
            time.sleep(self.pollTime) # sleep 30 s

            self.checkTempLimits() # check that min/max temps are satisfied

            self.updateStats()
            self.printUpdate()
            self.write_to_csv()
            self.write_to_csv('w') # weekly csv

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
