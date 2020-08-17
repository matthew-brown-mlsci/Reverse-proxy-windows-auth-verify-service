# Reverse-proxy-windows-auth-verify-service
Facilitates pass-thru NTLM auth via IIS reverse proxy site -> Flask API.  This allows a javascript jsonp ajax request to ascertain the Windows username/domain/pc of the orignating requestor.

## How does it work?

IIS is configured as a reverse proxy pointing at the Flask-powered API provided by the Windows Service.  IIS is configured to require authentication, and only allow NTLM for authentication.  The NTLM host headers are
forwarded to the Flask API, where the domain samAccountName is decoded using the publicly available NTLM
schema, which is then used for an AD query to verify group membership for a given group.

## Why?

Using this mechanism, it's possible to make JSONP calls from a web browser to verify AD group membership.  
Giving websites the power to verify and use local windows domain account information facilitates pass-through auth projects without resorting to alternate Microsoft web design tools.

## __To compile python -> service .exe__
```
set PYTHONHOME=C:\python37\python-3.7.1.amd64\
set PYTHONPATH=C:\python37\python-3.7.1.amd64\Lib\
pip install pyinstaller
pyinstaller -F --hidden-import=win32timezone "Reverse proxy windows auth verify service.py"
mkdir "c:\scripts"
mkdir "c:\scripts\Reverse proxy windows auth verify service"
copy "dist\Reverse proxy windows auth verify service.exe" "c:\scripts\Reverse proxy windows auth verify service\Reverse proxy windows auth verify service.exe"
c:
cd "c:\scripts\Reverse proxy windows auth verify service"
"Reverse proxy windows auth verify service.exe" install
```
- Make sure the service is running and port 9995 is open and accepting connections

## Configure IIS
- Add URL_Rewrite: http://www.microsoft.com/web/downloads/platform.aspx
- run MS web platform installer
- WebPlatformInstaller_x64_en-US.exe
- Clickety-click through installer
- run "Microsoft Web Platform Installer" (should be in start menu now)
- type "Application Request Routing 3.0" in the search box and hit enter, 'add' Application Request Routing 3.0
  click install, then accept prereqs/etc.
  various things will download/install
  exit installer
- restart iis console, "URL Rewrite" should now be available
- Create a new website to act as a reverse proxy
  Authentication: disable anonymous auth, enable windows auth
  click on windows auth, select 'providers', remove 'Negotiate' and leave *only* NTLM Provider
- HTTP Response Headers: 
  set common headers -> uncheck 'Enable HTTP keep-alive'
- URL Rewrite:
  Add rule
  Select 'Reverse Proxy'
  (Select 'yes' to enable functionality if dialog pops up about enabling Application Request Routing)
  Type in local server FQDN + port of python API/website service
  hit ok
- Restart IIS Server

## __Testing:__
+ Endpoint:
```
curl -s "http://localhost:9995/getWinAuthInfo"
```


## Endpoint /getWinAuthInfo will get forwarded authorization headers, including the NTLM negotiation sent by the browser.  This is decoded using the NTLM v3 schema:
```
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
```
Response with user (samaccountname) + domain + clientpc in json (of course!)


