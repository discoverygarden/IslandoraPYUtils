'''
Created on Apr 15, 2011

@author
  William Panting
@dependencies
  lxml
'''
from lxml import etree
import logging

def rootHasNamespace(xmlIn,namespaceIn):
    '''
Checks if the indicated xml file's root has the indicated namespace
@param xmlIn
  xml file to check
@param namespaceIn
  namespace to check for
@return bool
  return true if namespace found false if not
'''
    parser = etree.XMLParser(remove_blank_text=True)
    xmlFile = etree.parse(xmlIn, parser)
    xmlFileRoot = xmlFile.getroot()
    xmlFileRootNamespaces = xmlFileRoot.nsmap
    for namespace in xmlFileRootNamespaces:
        if xmlFileRootNamespaces[namespace] == namespaceIn:
            return True
    return False

def import_etree():
    '''
This function will import the best etree it can find. 
Because dynamic importing is crazy this function can be used like this:
<example>
from .. import xmlib
etree = xmlib.import_etree()
</example>

@author
  Adam, Will
'''
    #Get etree from somewhere it should be...
    try:
        from lxml import etree
        logging.debug("running with lxml.etree")
    except ImportError:
        try:
            # Python 2.5
            import xml.etree.cElementTree as etree
            logging.debug("running with cElementTree on Python 2.5+")
        except ImportError:
            try:
                # Python 2.5
                import xml.etree.ElementTree as etree
                logging.debug("running with ElementTree on Python 2.5+")
            except ImportError:
                try:
                    # normal cElementTree install
                    import cElementTree as etree
                    logging.debug("running with cElementTree")
                except ImportError:
                    try:
                        # normal ElementTree install
                        import elementtree.ElementTree as etree
                        logging.debug("running with ElementTree")
                    except ImportError:
                        message = "Failed to import ElementTree from any known place"
                        logging.critical(message)
                        raise ImportError(message)
    return etree 