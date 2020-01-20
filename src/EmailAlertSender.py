import smtplib
#from email.mime import multipart as MIMEMultipart
#from email.mime import text as MIMEText
#from email.mime import image as MIMEImage
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
    
    def form_alert_message(self,subject = None,body = None,recipient = None,images = None):
        if subject is not None:
            self.subject = subject
        if body is not None:
            self.body = body
        if recipient is not None:
            self.recipient = recipient
        self.images = images

        if self.images is not None:
            self.form_mime_alert_message(subject,body,recipient,images)
        else:
            self.full_email_text = "From: %s\nTo: %s\nSubject: %s\n\n%s\n" % (self.sender, self.recipient, self.subject, self.body)

    # end form_alert_message

    def form_mime_alert_message(self,subject = None,body = None,recipient = None,images = None):
        if subject is not None:
            self.subject = subject
        if body is not None:
            self.body = body
        if recipient is not None:
            self.recipient = recipient
        if images is not None:
            self.images = images
        
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

        nImg = len(self.images)
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
        # # set an alternative html body
        # msg.add_alternative("""\
        # <html>
        #     <body>
        #         <p>This is an HTML body.<br>
        #         It also has an image.
        #         </p>
        #         <img src="cid:{image_cid}">
        #     </body>
        # </html>
        # """.format(image_cid=image_cid[1:-1]), subtype='html')
        # # image_cid looks like <long.random.number@xyz.com>
        # # to use it as the img src, we don't need `<` or `>`
        # # so we use [1:-1] to strip them off


        # msgRoot = MIMEMultipart('related')
        # msgRoot['Subject'] = self.subject
        # msgRoot['From'] = self.sender
        # msgRoot['To'] = self.recipient
        # #msgRoot.preamble = 'This is a multi-part message in MIME format.'

        # # Encapsulate the plain and HTML versions of the message body in an
        # # 'alternative' part, so message agents can decide which they want to display.
        # msgAlternative = MIMEMultipart('alternative')
        # msgRoot.attach(msgAlternative)

        # msgText = MIMEText(self.body)
        # msgAlternative.attach(msgText)

        # # We reference the image in the IMG SRC attribute by the ID we give it below
        # #msgText = MIMEText('<b>Some <i>HTML</i> text</b> and an image.<br><img src="cid:image1"><br>Nifty!', 'html')
        # #msgAlternative.attach(msgText)
        # msgTxt = self.body
        # msgTxt = msgTxt.replace("\n","<br>")

        # msgImages = []
        # for img in self.images:
        #     im_name = os.path.splitext(os.path.basename(img))[0] # strip path and extension from name
        #     fp = open(img,'rb')
        #     msgImage = MIMEImage(fp.read())
        #     fp.close()
        #     msgTxt = msgTxt + '<br><img src="cid:' + im_name + '"><br>' # add image tag to html
        #     msgImage.add_header('Content-ID', '<' + im_name + '>')
        #     msgImages.append(msgImage)
            
        # msgText = MIMEText(msgTxt, 'html')
        # msgAlternative.attach(msgText)

        # for img in msgImages:
        #     msgRoot.attach(img)

        # self.full_email_text = msgRoot.as_string()
        # # This example assumes the image is in the current directory
        # #fp = open('test.jpg', 'rb')
        # #msgImage = MIMEImage(fp.read())
        # #fp.close()

        # # Define the image's ID as referenced above
        # #msgImage.add_header('Content-ID', '<image1>')
        # #msgRoot.attach(msgImage)

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