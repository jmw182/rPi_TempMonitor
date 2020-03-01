import smtplib
from email.message import EmailMessage
from email.utils import make_msgid
import mimetypes
import os

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
        self.images = None
        self.attachments = None

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
    
    def form_alert_message(self,subject = None,body = None,recipient = None,images = None,attachments = None):
        if subject is not None:
            self.subject = subject
        if body is not None:
            self.body = body
        if recipient is not None:
            self.recipient = recipient
        self.images = images
        self.attachments = attachments

        if self.images is not None or self.attachments is not None:
            self.form_mime_alert_message(subject,body,recipient,images,attachments)
        else:
            self.full_email_text = "From: %s\nTo: %s\nSubject: %s\n\n%s\n" % (self.sender, self.recipient, self.subject, self.body)
    # end form_alert_message

    def form_mime_alert_message(self,subject = None,body = None,recipient = None,images = None,attachments = None):
        if subject is not None:
            self.subject = subject
        if body is not None:
            self.body = body
        if recipient is not None:
            self.recipient = recipient
        self.images = images
        self.attachments = attachments

        if self.images is None:
            nImg = 0
        else:
            nImg = len(self.images)
        
        if self.attachments is None:
            nAttch = 0
        else:
            nAttch = len(self.attachments)
        
        msg = EmailMessage()

        # generic email headers
        msg['Subject'] = self.subject
        msg['From'] = '<' + self.sender + '>'
        msg['To'] = '<' + self.recipient + '>'

        # set the plain text body
        msg.set_content(self.body)
        
        # alternate html
        msgTxt = self.body
        msgTxt = msgTxt.replace("\n","<br>")
        
        image_cids = []
        for i in range(nImg):
            cid = make_msgid()
            image_cids.append(cid)
            cid = cid[1:-1] # remove < >
            msgTxt = msgTxt + '<br><img src="cid:' + cid + '"><br>' # add image tag to html

        msg.add_alternative(msgTxt,subtype='html')

        # now open the images and attach to the email
        for i in range(nImg):
            with open(self.images[i], 'rb') as img:
                 # know the Content-Type of the image
                maintype, subtype = mimetypes.guess_type(img.name)[0].split('/')

                # attach it
                msg.get_payload()[1].add_related(img.read(), 
                                                    maintype=maintype, 
                                                    subtype=subtype, 
                                                    cid=image_cids[i])
        # end for
        
        # attach additional attachments
        for i in range(nAttch):
            with open(self.attachments[i], 'rb') as fp:
                # get content type
                ctype, encoding = mimetypes.guess_type(fp.name)
                if ctype is None or encoding is not None: # unknown or compressed
                    ctype = 'application/octet-stream'
                maintype, subtype = ctype.split('/', 1)
                # attach it
                msg.get_payload()[1].add_related(fp.read(),
                                                    maintype=maintype,
                                                    subtype=subtype,
                                                    filename=os.path.basename(fp.name))
        # end for
        
        self.full_email_text = msg.as_string()
    # end form_mime_alert_message

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
