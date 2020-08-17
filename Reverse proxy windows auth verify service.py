"""

    Service built to live behind an IIS reverse proxy site
        - supports jsonp for javascript driven user/domain discovery
        - IIS site must have:
            windows auth enabled, anonymous auth disabled
            authentication providers - NTLM should be only provider
            http keep-alive disabled in http response headers

        - Configure IIS
               Add URL_Rewrite:
               http://www.microsoft.com/web/downloads/platform.aspx
               run MS web platform installer
               WebPlatformInstaller_x64_en-US.exe
               Clickety-click through installer
               run "Microsoft Web Platform Installer" (should be in start menu now)
               type "Application Request Routing 3.0" in the search box and hit enter, 'add' Application Request Routing 3.0
               click install, then accept prereqs/etc.
               various things will download/install
               exit installer
               restart iis console, "URL Rewrite" should now be available
               Create a new website to act as a reverse proxy
                    - Authentication: disable anonymous auth, enable windows auth
                         - click on windows auth, select 'providers', remove 'Negotiate' and leave *only* NTLM Provider
                    - HTTP Response Headers: 
                         - set common headers -> uncheck 'Enable HTTP keep-alive'
                    URL Rewrite:
                         - Add rule
                              Select 'Reverse Proxy'
                              (Select 'yes' to enable functionality if dialog pops up about enabling Application Request Routing)
                              Type in local server FQDN + port of python API/website service
                              hit ok
                    Restart IIS Server
                    



        - endpoint /getWinAuthInfo will get forwarded authorization headers, including the NTLM
          negotiation sent by the browser.  This is decoded using the NTLM v3 schema:

     * Client sending type 3 message.

        0       1       2       3
        +-------+-------+-------+-------+
    0:  |  'N'  |  'T'  |  'L'  |  'M'  |
        +-------+-------+-------+-------+
    4:  |  'S'  |  'S'  |  'P'  |   0   |
        +-------+-------+-------+-------+
    8:  |   3   |   0   |   0   |   0   |
        +-------+-------+-------+-------+
   12:  |  LM-resp len  |  LM-Resp len  |
        +-------+-------+-------+-------+
   16:  |  LM-resp off  |   0   |   0   |
        +-------+-------+-------+-------+
   20:  |  NT-resp len  |  NT-Resp len  |
        +-------+-------+-------+-------+
   24:  |  NT-resp off  |   0   |   0   |
        +-------+-------+-------+-------+
   28:  | domain length | domain length |
        +-------+-------+-------+-------+
   32:  | domain offset |   0   |   0   |
        +-------+-------+-------+-------+
   36:  |  user length  |  user length  |
        +-------+-------+-------+-------+
   40:  |  user offset  |   0   |   0   |
        +-------+-------+-------+-------+
   44:  |  host length  |  host length  |
        +-------+-------+-------+-------+
   48:  |  host offset  |   0   |   0   |
        +-------+-------+-------+-------+
   52:  |   0   |   0   |   0   |   0   |
        +-------+-------+-------+-------+
   56:  |  message len  |   0   |   0   |
        +-------+-------+-------+-------+
   60:  | 0x01  | 0x82  |   0   |   0   |
        +-------+-------+-------+-------+
   64:  | domain string                 |
        +                               +
        .                               .
        .                               .
        +           +-------------------+
        |           | user string       |
        +-----------+                   +
        .                               .
        .                               .
        +                 +-------------+
        |                 | host string |
        +-----------------+             +
        .                               .
        .                               .
        +   +---------------------------+
        |   | LanManager-response       |
        +---+                           +
        .                               .
        .                               .
        +            +------------------+
        |            | NT-response      |
        +------------+                  +
        .                               .
        .                               .
        +-------+-------+-------+-------+

        Response with user (samaccountname) + domain + clientpc in json (of course!)

compiling to service + install (in winpython cmd as admin):
        set PYTHONHOME=C:\aisdev\python37\python-3.7.1.amd64\
	    set PYTHONPATH=C:\aisdev\python37\python-3.7.1.amd64\Lib\
        pip install pyinstaller
        pyinstaller -F --hidden-import=win32timezone "ALab reverse proxy windows auth verify service.py"
        mkdir "c:\scripts"
        mkdir "c:\scripts\ALab reverse proxy windows auth verify service"
        copy "dist\ALab reverse proxy windows auth verify service.exe" "c:\scripts\ALab reverse proxy windows auth verify service\ALab reverse proxy windows auth verify service.exe"
        c:
        cd "c:\scripts\ALab reverse proxy windows auth verify service"
        "ALab reverse proxy windows auth verify service.exe" install

    testing:
        Use NTLM capable web browser, or jsonp javascript call: "http://localhost:9995/getWinAuthInfo"
"""

import servicemanager
import socket
import sys
import win32event
import win32service
import win32serviceutil
import datetime

from myapp import app

logfile = "C:\\scripts\\Reverse proxy windows auth verify service\\Reverse proxy windows auth verify service log.txt"
port = 9995

# Add a log entry + datetime
def log_entry(log_message):
	with open(logfile, 'a') as f:
		f.write(str(datetime.datetime.now()) + " : ")
		f.write(log_message + '\n')

class FlaskService(win32serviceutil.ServiceFramework):
    _svc_name_ = "Reverse proxy windows auth verify service"
    _svc_display_name_ = "Reverse proxy windows auth verify service"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(10)

    def SvcStop(self):
        log_entry('SvcStop started')
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.ReportServiceStatus(win32service.SERVICE_STOPPED)
        log_entry('SvrStop finished')

    def SvcDoRun(self):
        log_entry('SvrDoRun started')
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_,''))
        self.flaskmain()
        
    def flaskmain(self):
        log_entry('flaskmain() started')
        app.run(debug=False, host='0.0.0.0', port=port)
        log_entry('flaskmain() finished')


if __name__ == '__main__':
    log_entry("Reverse proxy windows auth verify service started")
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(FlaskService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(FlaskService)
    log_entry("Reverse proxy windows auth verify service stopped")