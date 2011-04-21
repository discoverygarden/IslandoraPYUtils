from lxml import etree
import types
import copy

class rels_namespace:
    def __init__(self, alias, uri):
        self.alias = alias
        self.uri = uri

    def __repr__(self):
        return '{%s}' % self.uri
        
class rels_object:
    DSID = 1
    LITERAL = 2
    PID = 3

    TYPES = [DSID, LITERAL, PID]

    def __init__(self, data, type):
        self.type = type
        self.data = data

    def __repr__(self):
        return self.data

class rels_predicate:
    def __init__(self, alias, predicate):
        self.predicate = predicate
        self.alias = alias

    def __repr__(self):
        return self.predicate 

class fedora_relationship_element():
    rdf_namespace = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'
    rdf = '{%s}' % rdf_namespace
    fedora_namespace = 'info:fedora/fedora-system:def/relations-external#'
    fedora = '{%s}' % fedora_namespace

    nsmap = { 
        'rdf' : rdf_namespace,
        'fedora' : fedora_namespace,
    }

    ns = {
        'rdf' : rdf,
        'fedora' : fedora,
    }

    def __init__(self, namespaces=None, default_namespace=None):        
        if namespaces:
            if type(namespaces) == types.InstanceType:
                self.nsmap[namespaces.alias] = namespaces.uri
                self.ns[namespaces.alias] = '{%s}' % namespaces.uri
            else:
                for namespace in namespaces:
                    self.nsmap[namespace.alias] = namespace.uri
                    self.ns[namespace.alias] = '{%s}' % namespace.uri

        #set deafult namespace for predicates
        if(default_namespace):
            if( default_namespace not in self.ns ):
                raise KeyError
            self.nsalias = default_namespace
        else:
            self.nsalias = 'fedora'

        self.root = etree.Element(self.rdf+'RDF', nsmap=self.nsmap)
    
    def toString(self):       
        return etree.tostring(self.root, pretty_print=True)

    def _doXPathQuery(self, subject=None, predicate=None, object=None):
        predicate_object = self._objectifyPredicate(predicate)

        # becasue we start using xpath here, and xpath namespacing is a little different
        # we have to change to using alias:tag instead of {uri}tag
        if subject == None:
            description_xpath = 'rdf:Description'
        else:
            description_xpath = 'rdf:Description[@rdf:about="info:fedora/'+subject+'"]'

        if predicate_object == None:
            predicate_xpath = '/*'
        else:
            predicate_xpath = '/'+predicate_object.alias+':'+predicate_object.predicate

        if object == None:
            object_xpath = ''
        else:
            if object.type == rels_object.PID or object.type == rels_object.DSID:
                object_xpath = '[@rdf:resource="info:fedora/%s"]' % object
            elif object.type == rels_object.LITERAL:
                object_xpath = '[.="%s"]' % object
       
        return self.root.xpath(description_xpath + predicate_xpath + object_xpath, namespaces=self.nsmap)

    def _objectifyPredicate(self, predicate):
        if type(predicate) == types.NoneType:
            pred_obj = None
        elif type(predicate) == types.StringType:
            pred_obj = rels_predicate(self.nsalias,predicate)
        else:
            pred_obj = predicate
            if(pred_obj.alias == None):
                pred_obj.alias = self.nsalias
            elif pred_obj.alias not in self.ns:
                raise KeyError

        return pred_obj

    def _addRelationship(self, subject, predicate):
        description = self.root.find(self.rdf+'Description[@'+self.rdf+'about="info:fedora/'+subject+'"]')

        if description == None:
            description = etree.SubElement(self.root, self.rdf+'Description')
            description.attrib[self.rdf+'about'] = 'info:fedora/'+subject

        relationship = etree.SubElement(description, self.ns[predicate.alias]+predicate.predicate)
        return relationship

    def addRelationship(self, subject, predicate, object):
        if( subject == None or predicate == None or object == None):
            raise TypeError

        pred_obj = self._objectifyPredicate(predicate)
        relationship = self._addRelationship(subject, pred_obj)

        if( object.type == rels_object.DSID or object.type == rels_object.PID):
            relationship.attrib[self.rdf+'resource'] = 'info:fedora/%s' % object
        elif( object.type == rels_object.LITERAL ):
            relationship.text = '%s' % object


    def getRelationships(self, subject=None, predicate=None, object=None):

        result_elements = self._doXPathQuery(subject, predicate, object)

        results = []

        for element in result_elements:
            result = []
            parent = element.getparent()
            parent_name = parent.attrib[self.rdf+'about'].rsplit('/',1)[1]
            result.append(parent_name)
            
            predicate_name_array = element.tag.rsplit('}',1)

            if(len(predicate_name_array) == 1):
                predicate_name = rels_predicate(None, predicate_name_array[0])
            else:
                predicate_ns = predicate_name_array[0][1:]
                for a,p in self.nsmap.iteritems():
                    if( predicate_ns == p ):
                        predicate_alias = a
                predicate_name = rels_predicate(predicate_alias, predicate_name_array[1])

            result.append(predicate_name)

            if self.rdf+'resource' in element.attrib:
                object_name = element.attrib[self.rdf+'resource']
                object_name = object_name.rsplit('/',1)[1]
                if( object_name.find(':') == -1 ):
                    object_type = rels_object.DSID
                else:
                    object_type = rels_object.PID

                object_obj = rels_object(object_name,object_type)
            else:
                object_obj = rels_object(element.text, rels_object.LITERAL)

            result.append(object_obj)
            results.append(result)

        return results

    def purgeRelationships(self, subject=None, predicate=None, object=None):
        if( subject == None and predicate == None and object == None ):
            raise TypeError       

        result_elements = self._doXPathQuery(subject,predicate,object)

        for element in result_elements:
            parent = element.getparent()
            parent.remove(element)

            if len(parent) == 0:
                grandparent = parent.getparent()
                grandparent.remove(parent)

class fedora_relationship(fedora_relationship_element):
    def __init__(self, obj, reldsid, namespaces=None, default_namespace=None):
        fedora_relationship_element.__init__(self, namespaces, default_namespace)

        if reldsid in obj:
            parser = etree.XMLParser(remove_blank_text=True) # xml parser ignoring whitespace
            self.root = etree.fromstring(obj[reldsid].getContent().read(), parser)

        self.dsid = reldsid
        self.obj = obj
    
    def update(self):
        if self.dsid not in self.obj:
            self.obj.addDataStream(self.dsid, self.toString())
        else:
            self.obj[self.dsid].setContent(self.toString())

class rels_int(fedora_relationship):
    def __init__(self, obj, namespaces = None, default_namespace = None):
        fedora_relationship.__init__(self, obj, 'RELS-INT', namespaces, default_namespace)

    def _updateObject(self, object):
        if type(object) == types.NoneType:
            obj = None
        elif type(object) == types.StringType:
            obj = rels_object('%s/%s'%(self.obj.pid,object), rels_object.DSID)
        else:
            if object.type == rels_object.DSID:
                obj = copy.copy(object)
                obj.data = '%s/%s'%(self.obj.pid, object.data)
            elif object.type == rels_object.LITERAL:
                obj = copy.copy(object)
            else:
                raise TypeError
        return obj

    def _updateSubject(self, subject):
        if(subject):
            subject = '%s/%s' % (self.obj.pid, subject)
        return subject

    def addRelationship(self, subject, predicate, object):
        obj = self._updateObject(object)
        sub = self._updateSubject(subject)
        return fedora_relationship.addRelationship(self, sub, predicate, obj)

    def getRelationships(self, subject=None, predicate=None, object=None):
        obj = self._updateObject(object)
        sub = self._updateSubject(subject)
        return fedora_relationship.getRelationships(self, sub, predicate, obj)

    def purgeRelationships(self, subject=None, predicate=None, object=None):
        obj = self._updateObject(object)
        sub = self._updateSubject(subject)
        return fedora_relationship.purgeRelationships(self, sub, predicate, obj)


class rels_ext(fedora_relationship):
    def __init__(self, obj, namespaces = None, default_namespace = None):
        fedora_relationship.__init__(self, obj, 'RELS-EXT', namespaces, default_namespace)

    def _updateObject(self, object):
        if type(object) == types.NoneType:
            obj = None
        elif type(object) == types.StringType:
            obj = rels_object(object, rels_object.PID)
        else:
            if object.type == rels_object.PID or object.type == rels_object.LITERAL:
                obj = copy.copy(object)
            else:
                raise TypeError
        return obj

    def addRelationship(self, predicate, object):
        obj = self._updateObject(object)
        return fedora_relationship.addRelationship(self, self.obj.pid, predicate, obj)

    def getRelationships(self, predicate=None, object=None):
        obj = self._updateObject(object)
        return fedora_relationship.getRelationships(self, self.obj.pid, predicate, obj)

    def purgeRelationships(self, predicate=None, object=None):
        obj = self._updateObject(object)
        return fedora_relationship.purgeRelationships(self, self.obj.pid, predicate, obj)


# do some basic testing of the functionality
if __name__ == '__main__':

    relationship = fedora_relationship_element([rels_namespace('coal','http://www.coalliance.org/ontologies/relsint'), rels_namespace('jon','http://jebus/trainstation')])
    print relationship.toString()
    relationship.addRelationship('coccc:2040', rels_predicate('jon','feezle'), rels_object('JON',rels_object.LITERAL))
    print relationship.toString()

    relationship = fedora_relationship_element(rels_namespace('coal','http://www.coalliance.org/ontologies/relsint'), 'coal')
    print relationship.toString()
    relationship.addRelationship('coccc:2040', 'HasAwesomeness', rels_object('JON',rels_object.LITERAL))
    print relationship.toString()

    relationship = fedora_relationship_element()
    print relationship.toString()
    relationship.addRelationship('coccc:2040', 'HasAwesomeness', rels_object('JON',rels_object.LITERAL))
    print relationship.toString()
    relationship.addRelationship('coccc:2040', 'HasTN', rels_object('coccc:2030',rels_object.PID))
    print relationship.toString()
    relationship.addRelationship('coccc:2033', 'HasTN', rels_object('coccc:2040',rels_object.PID))
    print relationship.toString()
    relationship.addRelationship('coccc:2033/DSID', 'HasTN', rels_object('coccc:2040/DSID',rels_object.DSID))
    print relationship.toString()
    
    results = relationship.getRelationships(predicate = 'HasTN')
    print results
    results = relationship.getRelationships(predicate = rels_predicate('fedora','HasTN'))
    print results
    results = relationship.getRelationships(object = rels_object('coccc:2040/DSID',rels_object.DSID))
    print results
    results = relationship.getRelationships(object = rels_object('JON',rels_object.LITERAL))
    print results
    results = relationship.getRelationships(subject = 'coccc:2040')
    print results
    results = relationship.getRelationships(subject = 'coccc:2040', predicate = 'HasTN')
    print results

    relationship.purgeRelationships(subject = 'coccc:2040')
    print relationship.toString()
