'''
Created on Apr 15, 2011

@author: William Panting
@dependencies: lxml
'''
from lxml import etree

'''
Checks if the indicated xml file's root has the indicated namespace
@param xmlIn: xml file to check
@param namespace: namespace to check for
@return bool: return true if namespace found false if not
'''
def rootHasNamespace(xmlIn,namepace):
    parser = etree.XMLParser(remove_blank_text=True)
    xmlFile = etree.parse(xmlIn, parser)
    xmlFileRoot = xmlFile.getroot()
    xmlFileRootNamespaces = xmlFileRoot.nsmap
    for namespace in xmlFileRootNamespaces:
        if xmlFileRootNamespaces[namespace] == namespace:
            return True
    return False
