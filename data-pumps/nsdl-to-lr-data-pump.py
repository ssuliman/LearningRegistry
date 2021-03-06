#    Copyright 2011 SRI International
#    
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#    
#        http://www.apache.org/licenses/LICENSE-2.0
#    
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
'''
Reads OAI-PMH data and publishes to specific LR Node with envelopes that contain inline payloads.

Can work with both OAI Dublin Core and NSDL Dublin Core.

Created on Feb 11, 2011

@author: jklo
'''


from restkit.resource import Resource
import urllib2
import time
from lxml import etree
from StringIO import StringIO
import json
import logging
import sys
from urllib import urlencode

logging.basicConfig()
log = logging.getLogger("main")

config = {
    "server": "http://www.dls.ucar.edu",
    "path": "/dds_se/services/oai2-0",
    "verb": "ListRecords",
    "metadataPrefix":"nsdl_dc",
    "set":"ncs-NSDL-COLLECTION-000-003-112-016"
}
#config = {
#    "server": "http://hal.archives-ouvertes.fr",
#    "path": "/oai/oai.php",
#    "verb": "ListRecords",
#    "metadataPrefix":"oai_dc",
#    "set": None
#}
namespaces = {
              "oai" : "http://www.openarchives.org/OAI/2.0/",
              "oai_dc" : "http://www.openarchives.org/OAI/2.0/oai_dc/",
              "dc":"http://purl.org/dc/elements/1.1/",
              "dct":"http://purl.org/dc/terms/",
              "nsdl_dc":"http://ns.nsdl.org/nsdl_dc_v1.02/",
              "ieee":"http://www.ieee.org/xsd/LOMv1p0",
              "xsi":"http://www.w3.org/2001/XMLSchema-instance"
              }
# http://hal.archives-ouvertes.fr/oai/oai.php?verb=ListRecords&metadataPrefix=oai_dc

class Error(Exception):
    pass

def getDocTemplate():
    return { 
            "doc_type": "resource_data", 
            "doc_version": "0.10.0", 
            "resource_data_type" : "metadata",
            "active" : True,
            "submitter_type": "agent",
            "submitter": "NSDL 2 LR Data Pump",
            "submission_TOS": "Yes",
            "resource_locator": None,
            "filtering_keys": [],
            "payload_placement": None,
            "payload_schema": [],
            "payload_schema_locator":[],
            "payload_locator": None,
            "resource_data": None
            }
    

def formatOAIDoc(record):
    doc = getDocTemplate()
    resource_locator = record.xpath("oai:metadata/oai_dc:dc/dc:identifier/text()", namespaces=namespaces)
    subject = record.xpath("oai:metadata/oai_dc:dc/dc:subject/text()", namespaces=namespaces)
    language = record.xpath("oai:metadata/oai_dc:dc/dc:language/text()", namespaces=namespaces)
    payload = record.xpath("oai:metadata/oai_dc:dc", namespaces=namespaces)
    
    doc["resource_locator"] = resource_locator
    
    doc["filtering_keys"].extend(subject)
    doc["filtering_keys"].extend(language)

    
    doc["payload_schema"].append("OAI DC 2.0")
    doc["payload_schema_locator"].append("http://www.openarchives.org/OAI/2.0/oai_dc/ http://www.openarchives.org/OAI/2.0/oai_dc.xsd")
    
    doc["payload_placement"] = "inline"
    doc["resource_data"] = etree.tostring(payload[0])
    
    for key in doc.keys():
        if (doc[key] == None):
            del doc[key]
    
    return doc

def formatNSDLDoc(record):
    doc = getDocTemplate()
    resource_locator = record.xpath("oai:metadata/nsdl_dc:nsdl_dc/dc:identifier/text()", namespaces=namespaces)
    subject = record.xpath("oai:metadata/nsdl_dc:nsdl_dc/dc:subject/text()", namespaces=namespaces)
    language = record.xpath("oai:metadata/nsdl_dc:nsdl_dc/dc:language/text()", namespaces=namespaces)
    edLevel = record.xpath("oai:metadata/nsdl_dc:nsdl_dc/dct:educationLevel/text()", namespaces=namespaces)
    payload = record.xpath("oai:metadata/nsdl_dc:nsdl_dc", namespaces=namespaces)
    
    doc["resource_locator"] = resource_locator
    
    doc["filtering_keys"].extend(subject)
    doc["filtering_keys"].extend(language)
    doc["filtering_keys"].extend(edLevel)
    
    
    doc["payload_schema"].append("NSDL DC 1.02.020")
    doc["payload_schema_locator"].append("http://ns.nsdl.org/nsdl_dc_v1.02/ http://ns.nsdl.org/schemas/nsdl_dc/nsdl_dc_v1.02.xsd")
    
    doc["payload_placement"] = "inline"
    doc["resource_data"] = etree.tostring(payload[0])
    
    for key in doc.keys():
        if (doc[key] == None):
            del doc[key]
    
    return doc
    
def bulkUpdate(list):
    '''
    Save to Learning Registry
    '''
    if len(list) > 0:
        try:
            res = Resource("http://learningregistry.couchdb:5984")
            body = { "documents":list }
            log.info("request body: %s" % (json.dumps(body),))
            clientResponse = res.post(path="/publish", payload=json.dumps(body), headers={"Content-Type":"application/json"})
            log.info("status: {0}  message: {1}".format(clientResponse.status_int, clientResponse.body_string))
        except Exception:
            log.exception("Caught Exception When publishing to registry")


def fetchRecords(conf):
    '''
    Generator to fetch all records using a resumptionToken if supplied.
    '''
    server = conf["server"]
    path = conf["path"]
    verb = conf["verb"]
    metadataPrefix = conf["metadataPrefix"]
    set = conf["set"]
    
    params = { "verb": verb, "metadataPrefix": metadataPrefix }
    if set != None:
        params["set"] = set
    
    body = makeRequest("%s%s" % (server, path), **params)
    f = StringIO(body)
    tree = etree.parse(f)
    tokenList = tree.xpath("oai:ListRecords/oai:resumptionToken/text()", namespaces=namespaces)
    yield tree.xpath("oai:ListRecords/oai:record", namespaces=namespaces)
    
    del params["metadataPrefix"]
    
    while (len(tokenList) == 1):
        try:
            params["resumptionToken"] = tokenList[0]
            body = makeRequest("%s%s" % (server, path), **params)
            f = StringIO(body)
            tree = etree.parse(f)
            yield tree.xpath("oai:ListRecords/oai:record", namespaces=namespaces)
            tokenList = tree.xpath("oai:ListRecords/oai:resumptionToken/text()", namespaces=namespaces)
        except Exception as e:
            tokenList = []
            log.error(sys.exc_info())
            log.exception("Problem trying to get next segment.")

WAIT_DEFAULT = 120 # two minutes
WAIT_MAX = 5

def makeRequest(base_url, credentials=None, **kw):
        """Actually retrieve XML from the server.
        """
        # XXX include From header?
        headers = {'User-Agent': 'pyoai'}
        if credentials is not None:
            headers['Authorization'] = 'Basic ' + credentials.strip()
        request = urllib2.Request(
            base_url, data=urlencode(kw), headers=headers)
        return retrieveFromUrlWaiting(request)
        
def retrieveFromUrlWaiting(request,
                           wait_max=WAIT_MAX, wait_default=WAIT_DEFAULT):
    """Get text from URL, handling 503 Retry-After.
    """
    for i in range(wait_max):
        try:
            f = urllib2.urlopen(request)
            text = f.read()
            f.close()
            # we successfully opened without having to wait
            break
        except urllib2.HTTPError, e:
            if e.code == 503:
                try:
                    retryAfter = int(e.hdrs.get('Retry-After'))
                except TypeError:
                    retryAfter = None
                if retryAfter is None:
                    time.sleep(wait_default)
                else:
                    time.sleep(retryAfter)
            else:
                # reraise any other HTTP error
                raise
    else:
        raise Error, "Waited too often (more than %s times)" % wait_max
    return text            
      

def connect():
    for recset in fetchRecords(config):
        docList = []
        for rec in recset:
            if config["metadataPrefix"] == "oai_dc":
                docList.append(formatOAIDoc(rec))
            if config["metadataPrefix"] == "nsdl_dc":
                docList.append(formatNSDLDoc(rec))
        try:
            print(json.dumps(docList))
        except:
            log.exception("Problem w/ JSON dump")
        bulkUpdate(docList)
    

if __name__ == '__main__':
    connect()