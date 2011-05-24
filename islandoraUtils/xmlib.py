'''
Created on Apr 15, 2011

@author: William Panting
@dependencies: lxml
'''
from lxml import etree

def rootHasNamespace(xmlIn,namespaceIn):
    '''
Checks if the indicated xml file's root has the indicated namespace
@param xmlIn: xml file to check
@param namespaceIn: namespace to check for
@return bool: return true if namespace found false if not
'''
    parser = etree.XMLParser(remove_blank_text=True)
    xmlFile = etree.parse(xmlIn, parser)
    xmlFileRoot = xmlFile.getroot()
    xmlFileRootNamespaces = xmlFileRoot.nsmap
    for namespace in xmlFileRootNamespaces:
        if xmlFileRootNamespaces[namespace] == namespaceIn:
            return True
    return False
