'''
Created on Apr 15, 2011
@file
  This is unavoidable don't move around the order of functions/imports and calls in this file
@author
  William Panting
@dependencies
  lxml
'''
import logging
from misc import base64_string_to_file

def import_etree():
    '''
This function will import the best etree it can find. 
Because dynamic importing is crazy this function can be used like this:
<example>
from .. import xmlib
etree = xmlib.import_etree()
</example>
ONLY USE THIS FUNCTION IF YOU ARE NOT USING LXML SPECIFIC APIS (GRR THIS INCLUDES .XPATH())
THIS FUNCTION ALSO SCREWS WITH LOGGING, SETUP YOUR LOGGER BEFORE CALLING IT
FIXME: AVOID LOGGING ISSUES
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
#yuk sory
etree = import_etree()

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

def copy_element_attributes(from_element, to_element):
    '''
    This function will copy the attributes from one etree element to anther
    
    @param from_element
      Get attributes from this one
    @param to_element
      Put attributes on this one
      
    @author
      William Panting
      
    '''
    
    attributes = from_element.attrib
    for attribute, value in attributes.iteritems():
        to_element.set(attribute, value)

    return

def base64_element_to_file(element, file_path):
    '''
    This function will write the text node of an etree
    element that is encoded as base64 to a file.
    
    @param etree element element:
        The element to pull the text from
    @param string file_path:
        The file to write to
    
    '''
    
    base64_string = element.text
    base64_string_to_file(base64_string, file_path)
    
    return