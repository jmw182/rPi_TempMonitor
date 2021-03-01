import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import csv
import pandas
from pandas.plotting import register_matplotlib_converters

def make_temp_plot():
    filename = '/home/pi/git/rPi_TempMonitor/tmp/tmp_daily.csv'
    csv = open(filename, 'rb')
    data = pandas.read_csv(csv,sep=',',names=['time','temperature','humidity'])
    
    t_fmt = mdates.DateFormatter('%H:%M')
    plt_title = datetime.date.today().strftime('%x')
    t = mdates.datestr2num(data["time"])
    plt.figure()
    plt.plot_date(t,data['temperature'],'-')
    plt.xlabel('Time')
    plt.ylabel('Temperature')
    plt.title(plt_title)
    plt.gcf().autofmt_xdate()
    plt.gca().xaxis.set_major_formatter(t_fmt)
    
    plt.show()

if __name__ == "__main__":
    register_matplotlib_converters() 
    make_temp_plot()