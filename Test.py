'''
cXML test client that partially implements the cXML User's Guide (http://cxml.org/) for Procurement PunchOut.
I wrote this script to test the Message Authentication Code (MAC) as part of an implementation of Infor M3 (http://www.infor.com/product-summary/erp/m3/).
Thibaud Lopez Schneider, 2015-08-31
'''

import base64
import hashlib
import hmac
import http.client
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from urllib.parse import urlparse

# URL to the supplier's cXML server (replace with your supplier's URL)
url = "https://example.com/?PunchOutSetupRequest"

# Calculate the date/times
now = datetime.now()
payloadID = now.isoformat() + "@hostname"
timestamp = now.isoformat()
creationDate = now.isoformat()
expirationDate = (now+timedelta(hours=1)).isoformat()

# Test values from the cXML User's Guide (replace with your supplier's values)
toDomain = "DUNS"
toIdentity = "049329048"
fromDomain = "NetworkID"
fromIdentity = "AN9900000100"
senderDomain = "NetworkID"
senderIdentity = "AN9900000100"
password = "abracadabra"
creationDate = "2003-01-15T08:42:46-08:00" # test only; prefer calculated value above
expirationDate = "2003-01-15T11:42:46-08:00" # test only; prefer calculated value above

# Normalize the values
data = [fromDomain.lower(),
        fromIdentity.strip().lower(),
        senderDomain.lower(),
        senderIdentity.strip().lower(),
        creationDate,
        expirationDate]

# Concatenate the UTF-8-encoded byte representation of the strings, each followed by a null byte (0x00)
data = b''.join([(bytes(x, "utf-8") + b'\x00') for x in data])

# Calculate the Message Authentication Code (MAC)
digest = hmac.new(password.encode("utf-8"), data, hashlib.sha1).digest()

# Truncate to 96 bits (12 bytes)
truncated = digest[0:12]

# Base-64 encode, and convert bytearray to string
mac = str(base64.b64encode(truncated), "utf-8")

# Build the cXML
xml = ET.parse("Test.xml")
xml.getroot().attrib["payloadID"] = payloadID
xml.getroot().attrib["timestamp"] = timestamp
xml.find("Header/From/Credential").attrib["domain"] = fromDomain
xml.find("Header/From/Credential/Identity").text = fromIdentity
xml.find("Header/To/Credential").attrib["domain"] = toDomain
xml.find("Header/To/Credential/Identity").text = toIdentity
xml.find("Header/Sender/Credential").attrib["domain"] = senderDomain
xml.find("Header/Sender/Credential/Identity").text = senderIdentity

# Set the CredentialMac
credentialMac = xml.find("Header/Sender/Credential").find("CredentialMac")
credentialMac.attrib["creationDate"] = creationDate
credentialMac.attrib["expirationDate"] = expirationDate
credentialMac.text = mac

# Resulting cXML document
body = ET.tostring(xml.getroot(), method="xml", encoding="utf-8")
print(str(body, "utf-8"))

# Make the HTTP request
url = urlparse(url)
print("Connecting to:", url.netloc)
conn = http.client.HTTPSConnection(url.netloc)
headers = {"Content-Type": "text/xml; charset=utf-8"}
conn.request("POST", url.geturl(), body, headers)

# Get the HTTP response
response = conn.getresponse()
headers = response.getheaders()
body = response.read()
print("HTTP/1.1", response.status, response.reason)
[print(h[0] + ": " + h[1]) for h in headers]
print(str(body, "utf-8"))
conn.close()

# Get the resulting PunchOut URL from the cXML response
xml = ET.fromstring(body)
url = xml.find("Response/Status[@code='200']/../PunchOutSetupResponse/StartPage/URL")
print("URL:", url.text)
