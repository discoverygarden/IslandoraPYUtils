#!/usr/bin/env python2.6
import logging
import datetime
from StringIO import StringIO
import base64

from islandoraUtils import xmlib
etree = xmlib.import_etree()
                    
class EACCPF(object):
    '''
    A python library to deal with (a tiny subset) of EAC-CPF 
    See http://eac.staatsbibliothek-berlin.de/eac-cpf-schema.html
    
    TODO:  Ensure ordering of elements, for validation purposes...
    '''
    NSMAP = {
        'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
        None: 'urn:isbn:1-931666-33-4', #default namespace
        'xlink': 'http://www.w3.org/1999/xlink'
    }
    
    def __init__(self, id, element=None, xml=None, agency=('DGI', 'DiscoveryGarden Inc.'), language=('eng', 'English'), script=('Latn', 'Latin'), loggerName='islandoraUtils.metadata.eaccpf'):
        '''
        "--EAC-CPF" will be appended to the ID to create a "recordId"
        "language" is that used for maintenance, not contents
        '''
        self.logger = logging.getLogger(loggerName)
        #TODO:  Validate any input data, to make sure that it looks like valid eac-cpf
        if element and xml:
            raise Exception('Either element or xml should be given, not both')
        elif element:
            self.element = element
        elif xml:
            self.element = etree.fromstring(xml)
        else:
            #Build a fairly bare eac-cpf schema for a base.
            root = etree.Element('eac-cpf', 
                attrib={'{http://www.w3.org/2001/XMLSchema-instance}schemaLocation': 'urn:isbn:1-931666-33-4 http://eac.staatsbibliothek-berlin.de/schema/cpf.xsd'}, 
                nsmap=self.NSMAP)
            control = etree.SubElement(root, 'control')
            etree.SubElement(control, 'recordId').text = '%(id)s--EAC-CPF' % {'id': id}
            etree.SubElement(control, 'maintenanceStatus').text = 'new'
            agent = etree.SubElement(control, 'maintenanceAgency')
            
            #FIXME...  The unpacking use could probably be a little clearer...  Anyway.
            lang = etree.SubElement(control, 'languageDeclaration')
            a, b = language
            etree.SubElement(lang, 'language', {'languageCode': a}).text = b
            a, b = script
            etree.SubElement(lang, 'script', {'scriptCode': a}).text = b
            
            etree.SubElement(control, 'maintenanceHistory')
            etree.SubElement(control, 'sources')
            
            #Deliciously awesome tuple unpacking!
            a, b = agency
            #etree.SubElement(agent, 'agencyCode').text = a #Needs to be in a defined set to validate
            etree.SubElement(agent, 'agencyName').text = b
            
            etree.SubElement(root, 'cpfDescription')
            
            self.element = root
            
        self.__check_base()
    
    def __check_base(self):
        '''
        We want to be able to make a few assumptions regarding what 
        elements will be present, so let's ensure that a few sections are 
        present (fake validation?)
        '''
        el = self.element
        for i in ['control', 'control/maintenanceHistory', 'control/sources', 'cpfDescription']:
            if el.find(i) is None:
                raise Exception('No %s element!' % i)
    
    def __str__(self):
        '''Get the XML as a string'''
        return etree.tostring(self.element, pretty_print=True, encoding="utf8")
            
    def add_maintenance_event(self, type="derived", time="now", agent_type="human", agent="Me"):
        '''
        If 'time' is not provided, or is 'now', utcnow will be used.
        If 'time' is an instance of datetime, it will be used directly
        Otherwise, 'time' will be interpreted as a Unix timestamp.
        '''
        mh = self.element.find('control/maintenanceHistory')

        if time == "now" or time == None:
            t = datetime.datetime.utcnow().isoformat()
        elif isinstance(time, datetime.datetime):
            t = time.isoformat()
        else:
            t = datetime.utcfromtimestamp(time).isoformat()
            
        me = etree.SubElement(mh, 'maintenanceEvent')
        etree.SubElement(me, 'eventType').text = type
        etree.SubElement(me, 'eventDateTime', {'standardDateTime': t})
        etree.SubElement(me, 'agentType').text = agent_type
        etree.SubElement(me, 'agent').text = agent
    
    #TODO:  Should probably check that this source does not already exists in the list of sources...
    def add_XML_source(self, caption="XML source", xml=None):
        '''
        Currently, 'xml' can either be an instance of etree.Element, 
        or can be a string containing the XML
        '''
        if xml is None:
            raise Exception('No XML provided!')
        
        sources = self.element.find('control/sources')
        source = etree.SubElement(sources, 'source')
        etree.SubElement(source, 'sourceEntry').text = caption
        
        try:
            xmlWrap = etree.SubElement(source, 'objectXMLWrap')
            xmlWrap.append(xml)
        except TypeError:
            xmlWrap.append(etree.fromstring(xml))
    
    #TODO:  Should probably check that this source does not already exists in the list of sources...    
    def add_bin_source(self, caption="Binary source (base-64 encoded)", obj=None, encoded=False):
        '''
        base64 encodes the provided obj, and adds into 
        /eac-cpf/control/sources/source/objectBinWrap element
        '''
        #FIXME:  Seems like it might be very memory inefficient...  Probably better off creating a temp-file, though how to deal with knowing the size before hand...  Determine how large the obj is before hand, and allocate double?
        d64 = StringIO()
        if isinstance(obj, file):
            base64.encode(obj, d64)
        elif obj is not None:
            d64.write(base64.encodestring(obj))
        
        sources = self.element.find('control/sources')
        source = etree.SubElement(sources, 'source')
        etree.SubElement(source, 'sourceEntry').text = caption
        
        etree.SubElement(source, 'objectBinWrap').text = d64.getvalue()
        d64.close()
    
    #FIXME:  Should probably verify that 'role' is in the agreed upon vocab?
    #TODO:  Checking whether or not a the entry to add already exists would probably be a good idea.
    def add_name_entry(self, role='primary', name={'forename': 'first', 'middle': 'middle', 'surname': 'last'}, entityType='person'):
        '''
        * "name" should be a dictionary whose keys will be used as the 
            "localType" attribute in nameEntry/part, with the text set 
            to the value for the given key
        * "role" will be used as the "localType" attribute on the 
            nameEntry, and because we are allowing only one "primary", 
            old primaries will be made into "alt[s]"'''
        id = self.element.find('cpfDescription/identity')
        if id is None:
            id = etree.SubElement(self.element.find('cpfDescription'), 'identity')
            
        et = id.find('entityType')
        if et is None:
            et = etree.SubElement(id, 'entityType').text = entityType
            
        if role is 'primary':
            for old_primary in id.findall('nameEntry[@localType="primary"]'):
                old_primary.set('localType', 'alt')
        ne = etree.SubElement(id, 'nameEntry', {'localType': role})
        
        for k, v in name.items():
            etree.SubElement(ne, 'part', {'localType': k}).text = v
    
    def __get_subelement(self, path):
        '''
        Get (possibly creating) a node at the given path.
        '''
        toReturn = self.element.find(path)
        if toReturn is None:
            element, sep, sub = path.rpartition('/')
            if not element:
                el = self.element
            else:
                el = self.element.find(element)
                if el is None:
                    el = self.__get_subelement(element)
                                
            return etree.SubElement(el, sub)
        else:
            return toReturn
        
    def add_exist_dates(self, birth=None, death=None):
        '''
        Adds a date of birth and/or death to the description.
        '''
        if birth:
            self.__get_subelement('cpfDescription/description/existDates/dateRange/fromDate').set('standardDate', unicode(birth))
        if death:
            self.__get_subelement('cpfDescription/description/existDates/dateRange/toDate').set('standardDate', unicode(death))
    
    def add_bio(self, bio=None, wipe=True):
        '''
        bio should be sequence of XML elements (which includes an element 
        with children!--hopefully with the set of elements permitted by 
        the EAC-CPF schema)... We'll try to store it even if it's not
        (first by trying to create XML from a string, and falling-back to
        throwing the what was provided into a <p> element)...
        
        TODO:  Might need to create copies of elements when they are 
        passed in, due to how lxml works...  Dunno.
        '''
        try:
            biogHist = self.__get_subelement('cpfDescription/description/biogHist')
            if wipe:
                biogHist.clear()
            biogHist.extend(bio)
            self.logger.debug('Added bio subelements via extend')
        except TypeError:
            try:
                biogHist.extend(etree.fromstring(bio))
                self.logger.debug('Added bio subelements after creating etree from string.')
            except (etree.XMLSyntaxError, ValueError):
                etree.SubElement(biogHist, 'p').text = bio
                self.logger.debug('Added bio as text of a <p> tag')
                
    def add_chron_list(self, item_list):
        chronList = self.__get_subelement('cpfDescription/description/biogHist/chronList')
        for item in item_list:
            chronItem = etree.SubElement(chronList, 'chronItem')
            self.__add_elements(chronItem, item)
    
    def __add_elements(self, element, item):
        for tag, value in item.items():
            if tag == 'dateRange':
                dr = etree.SubElement(element, tag)
                for tg, val in value.items():
                    el = etree.SubElement(dr, tg)
                    el.text = unicode(val)
                    el.set('standardDate', unicode(val))  
            elif tag == 'date':
                el = etree.SubElement(element, tag)
                el.text = unicode(value)
                el.set('standardDate', unicode(value))
            elif tag in ['descriptiveNote']:
                etree.SubElement(etree.SubElement(element, tag), 'p').text = value
            else:
                etree.SubElement(element, tag).text = value
    
    def __add_address(self, element, role, addr=None):
        '''
        "Private" function, used to actually add the address.  Takes an element, as the address can be added
        at (at least) two different "levels" in the schema
        '''
        address = etree.SubElement(etree.SubElement(element, 'place', {'localType': role}), 'address')
        
        for k, v in addr.items():
            etree.SubElement(address, 'addressLine', {'localType': k}).text = v
        
    def add_address(self, role='primary', addr=None):
        '''
        Add an address entry under the eac-cpf/cpfDescription/description...
        Multiple place entries will be automatically placed under a "places"
        entry.
        Only a single "primary" entry is allowed with any number of "alt[s]"
        (so if you attempt to add an additional "primary" when there is
        already one, the old one will be made into an "alt")
        '''
        tmp_desc = self.element.find('cpfDescription/description')
        if tmp_desc is not None:
            tmp_pl = self.element.findall('cpfDescription/description/place')
     
            #FIXME:  Should merge multiple "places", if found?
            tmp_pls = self.element.find('cpfDescription/description/places')
            
            if tmp_pl:
                if not tmp_pls:
                    places = etree.SubElement(self.element.find('cpfDescription/description'), 'places')
                else:
                    places = tmp_pls
                    
                #TODO:  Move the existing "place" element(s) under the "places" element...  This could probably use some more testing?
                places.extend(tmp_pl)
                
                if role is 'primary':
                    for place in places.findall('place[@localType="primary"]'):
                        place.set('localType', 'alt')
                        
                node = places
            else:
                node = tmp_desc
        else:
            node = etree.SubElement(self.element.find('cpfDescription'), 'description')
        
        self.__add_address(node, role, addr)
        
    def add_relation(self, type, url=None, elements=None):
        relations = self.__get_subelement('cpfDescription/relations')
        rel_el = etree.SubElement(relations, type)
        
        if url:
            rel_el.set('{%(xlink)s}href' % self.NSMAP, url)
        if elements:
            self.__add_elements(rel_el, elements)

      
def testSchema():
    '''
A bit of simple testing--create a garbage EAC-CPF schema
This is realy unit testing but it is not in a 'if __name__ == '__main__':'
to simplify the structure because of the dynamic importing of etree
'''  
    test = EACCPF('test')
    test.add_maintenance_event()
    test.add_XML_source('Blargh', '<Honk/>')
    test.add_maintenance_event(type='revised', agent="Him")
    test.add_XML_source('Bob', etree.Element('Loblaw'))
    test.add_maintenance_event(type='revised', agent="They", agent_type="machine")
    #with open('./FileHandler.py') as aFile:
    #    test.add_bin_source('Try a file object', aFile)
    test.add_name_entry()
    test.add_name_entry(name={'a': 'asdf', 'b': '2', 'c': '3'})
    test.add_exist_dates('1923', '2010')
    test.add_address(addr={'line1': 'here', 'line2': 'there', 'country': 'Everywhere'})
    test.add_address(addr={'line1': 'asdf', 'line2': 'qwerty', 'country': 'yuiop'})
    test.add_bio('this is not xml!')
    b_tmp = etree.Element('bio')
    etree.SubElement(b_tmp, 'p').text = 'Ceci est de XML'
    #test.add_bio(b_tmp)
    test.add_bio("<bio><p>C'est de la XML fausse!</p><asdf><p>other</p></asdf></bio>")
    test.add_bin_source('Some text and stuff...', '<>></\'e2345^&lt;!')
    
    cl = [{
            'date': 2011,
            'event': 'Achieved PhD'
        },{
            'dateRange': {
                'fromDate': 2001,
                'toDate': 2011
            },
            'event': '10 years'
        },{
            'dateRange': {
                'fromDate': 1999
            },
            'event': 'Since 1999'
        },{
            'dateRange': {
                'toDate': 2030
            },
            'event': 'Until 2030'
        }
    ]
        
    test.add_chron_list(cl)
    
    test.add_relation('resourceRelation', url="http://www.example.org/blah.asdf", elements={'relationEntry': 'Academic webpage', 'descriptiveNote': 'Blah blah blah.'})
    test.add_relation('cpfRelation', elements={'dateRange': {'fromDate': 1999, 'toDate': 2005}, 'descriptiveNote': 'Was a member and stuff...'})
    el = None
    #el = test.element.find('control/sources/source/objectBinWrap')
    if el is not None:
        print('Decoded base64 test:\n%s' % base64.decodestring(el.text))
    return test    
if __name__ == '__main__':
    test = testSchema()
    # = etree.ElementTree(test.element).xmlschema(etree.parse(source='http://eac.staatsbibliothek-berlin.de/schema/cpf.xsd'))
    print(test)
    #print(validator(test.element))
    #print(validator.error_log)
