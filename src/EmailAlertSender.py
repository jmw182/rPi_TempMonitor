import smtplib

class EAS:
# Wrapper for smtplib to send easy email alerts.
# Defaults to SMTP SSL connection over port 465.
# Defaults to gmail host address


    def __init__(self,host = 'smtp.gmail.com', port = 465,TLS = True):
        self.host = host
        self.port = port
        self.TLS = TLS
        self.server = None

        self.sender = None
        self.recipient = None
        self.subject = None
        self.body = None
        self.full_email_text = None

        self.__password = None
    # end __init__

    def connect(self):
        if self.port == 465:
            self.server = smtplib.SMTP_SSL(self.host,self.port) # init server with SSL
            self.server.ehlo()
        else:
            self.server = smtplib.SMTP(self.host,self.port) # init server without SSL
            self.server.ehlo()
            if self.TLS:
                self.server.starttls() # start TLS
            # endif TLS
        #endif port
    # end conect

    def close(self):
        if self.connected():
            try:
                self.server.quit()
            except:
                print("Error on STMP quit, likely already disconnected.")
            self.server = None
    # end close
    
    def connected(self):
        return isinstance(self.server,smtplib.SMTP)

    def login(self,sender,password):
        self.sender = sender
        self.__password = password
    # end login

    def login_server(self):
        if not self.connected():
            self.connect()
        self.server.login(self.sender,self.__password)
    # end login_server
    
    def form_alert_message(self,subject = None,body = None,recipient = None):
        if subject is not None:
            self.subject = subject
        if body is not None:
            self.body = body
        if recipient is not None:
            self.recipient = recipient

        self.full_email_text = "From: %s\nTo: %s\nSubject: %s\n\n%s\n" % (self.sender, self.recipient, self.subject, self.body)
    # end form_alert_message

    def send_mail(self):
         self.server.sendmail(self.sender,self.recipient,self.full_email_text)
    # end send_mail

    def send_alert(self):
        self.connect()
        self.login_server()
        self.send_mail()
        self.close()
    # end send_alert

    def __del__(self):
        self.close()
    # end __del__