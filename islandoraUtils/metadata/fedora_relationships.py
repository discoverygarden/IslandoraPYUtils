from lxml import etree
import copy
import fcrepo #For type checking...

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

class fedora_relationship():
    r"""Top level class in the class hierarchy.
    The top level classes are easy to test, since they are independant of fedora.

    Looks like this:
            fedora_relationship
                     ^
                    / \
     rels_int_string   rels_ext_string
            |                |
         rels_int         rels_ext

    """
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

    def __init__(self, namespaces=None, default_namespace=None, xml=None):

        if namespaces:
            if isinstance(namespaces,rels_namespace):
                self.nsmap[namespaces.alias] = namespaces.uri
                self.ns[namespaces.alias] = '{%s}' % namespaces.uri
            elif isinstance(namespaces,list):
                if isinstance(namespaces[0],basestring):
                    self.nsmap[namespaces[0]] = namespaces[1]
                    self.ns[namespaces[0]] = '{%s}' % namespaces[1]
                elif isinstance(namespaces[0],rels_namespace):
                    for namespace in namespaces:
                        self.nsmap[namespace.alias] = namespace.uri
                        self.ns[namespace.alias] = '{%s}' % namespace.uri
                else:
                    raise TypeError
            else:
                raise TypeError

        if(xml):
            parser = etree.XMLParser(remove_blank_text=True) # xml parser ignoring whitespace
            root = etree.fromstring(xml, parser)

            # we unfortunatly have to go through quite a lot of crap to add new namespaces to
            # an existing xml document. There is a lxml bug filed against this but currently
            # its on the wishlist. if that is like our wishlish this will be here for awhile.
            # https://bugs.launchpad.net/lxml/+bug/555602
            if namespaces:
                oldnsmap = root.nsmap
                for (alias, uri) in oldnsmap.items():
                    self.ns[alias] = '{%s}' % uri
                self.nsmap.update(oldnsmap)
                self.root = etree.Element(root.tag, nsmap=self.nsmap)
                self.root[:] = root[:]
            else:
                self.root = root

        else:
            self.root = etree.Element(self.rdf+'RDF', nsmap=self.nsmap)

        #set deafult namespace for predicates
        if(default_namespace):
            if( default_namespace not in self.ns ):
                raise KeyError
            self.nsalias = default_namespace
        else:
            self.nsalias = 'fedora'

        # state variable to know if the tree has been modified
        self.modified = False

    def toString(self, pretty_print = True):
        return etree.tostring(self.root, pretty_print=pretty_print)

    def __str__(self):
        return etree.tostring(self.root, pretty_print=True)

    def _doXPathQuery(self, subject=None, predicate=None, object=None):
        predicate_object = self._objectifyPredicate(predicate)

        # becasue we start using xpath here, and xpath namespacing is a little different
        # we have to change to using alias:tag instead of {uri}tag

        # because of the damn stupid inconsistency in the data between description
        # and Description, we need to figure out what we are dealing with.
        description = self.root.find(self.rdf+'description')
        if(description is not None):
            description_xpath = 'rdf:description'
        else:
            description_xpath = 'rdf:Description'

        if subject != None:
            description_xpath += '[@rdf:about="info:fedora/'+subject+'"]'

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
        if predicate == None:
            pred_obj = predicate
        elif isinstance(predicate,basestring):
            pred_obj = rels_predicate(self.nsalias,predicate)
        elif isinstance(predicate,list):
            pred_obj = rels_predicate(predicate[0], predicate[1])
            if predicate[0] not in self.ns:
                raise KeyError
        elif isinstance(predicate,rels_predicate):
            pred_obj = predicate
            if pred_obj.alias == None:
                pred_obj.alias = self.nsalias
            if pred_obj.alias not in self.ns:
                raise KeyError
        else:
            raise TypeError
        return pred_obj

    def _addRelationship(self, subject, predicate):
        description = self.root.find(self.rdf+'Description[@'+self.rdf+'about="info:fedora/'+subject+'"]')

        # add a check for lower case description
        if description == None:
            description = self.root.find(self.rdf+'description[@'+self.rdf+'about="info:fedora/'+subject+'"]')

        if description == None:
            description = etree.SubElement(self.root, self.rdf+'Description')
            description.attrib[self.rdf+'about'] = 'info:fedora/'+subject

        relationship = etree.SubElement(description, self.ns[predicate.alias]+predicate.predicate)
        return relationship

    def addRelationship(self, subject, predicate, object):
        if( subject == None or predicate == None or object == None):
            raise TypeError

        self.modified = True

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

        if result_elements:
            self.modified = True

        for element in result_elements:
            parent = element.getparent()
            parent.remove(element)

            if len(parent) == 0:
                grandparent = parent.getparent()
                grandparent.remove(parent)

class rels_int_string(fedora_relationship):
    """Class to update a fedora RELS-INT datastream."""

    def __init__(self, pid, namespaces = None, default_namespace = None, xml = None):
        """Constructor for rels_int object.

        Arguements:
          obj -- The fcrepo object to modify/create rels_int for.
          namespaces -- Namespaces to be added to the rels_int.
              [] - list containing ['alias','uri']
              [rels_namespace, ...] - list of rels_namespace objects.
              [[],[],...[]] - list of ['alias','uri']
              rels_namespace - rels_namespace object containing namespace and alias.
          default_namespace -- String containing the alias of the default namespace.
          If no namespace is passed in then this is assumed:
          info:fedora/fedora-system:def/relations-external#

        """
        self.pid = pid
        fedora_relationship.__init__(self, namespaces, default_namespace, xml)

    def _updateObject(self, object):
        """Private method to overload object. Turns everything into a rels_object"""
        if object == None:
            obj = None
        elif isinstance(object,basestring):
            obj = rels_object('%s/%s'%(self.pid,object), rels_object.DSID)
        elif isinstance(object,rels_object):
            if object.type not in rels_object.TYPES:
                raise TypeError
            if object.type == rels_object.DSID:
                obj = copy.copy(object)
                obj.data = '%s/%s'%(self.pid, object.data)
            elif object.type == rels_object.LITERAL or object.type == rels_object.PID:
                obj = copy.copy(object)
        elif isinstance(object, list):
            reltype = object[1].lower()
            if reltype == 'dsid':
                obj = rels_object('%s/%s'%(self.pid, object[0]), rels_object.DSID)
            elif reltype == 'pid':
                obj = rels_object(object[0], rels_object.PID)
            elif reltype == 'literal':
                obj = rels_object(object[0], rels_object.LITERAL)
            else:
                raise KeyError
        elif isinstance(object,fcrepo.object.FedoraObject):
            obj = rels_object(object.pid, rels_object.PID)
        else:
            raise TypeError
        return obj

    def _updateSubject(self, subject):
        """Private method to add pid/dsid to the passed in dsid."""
        if(subject):
            subject = '%s/%s' % (self.pid, subject)
        return subject

    def addRelationship(self, subject, predicate, object):
        """Add new relationship to rels_int XML.

        Arguements:
          subject -- String containing the DSID of the subject.
          predicate -- The predicate.
              String - The predicate string. The default namespace is assumed.
              rels_predicate - object with namespace alias and predicate set.
              list - ['alias','predicate']
          object -- The object.
              string - String containing a DSID.
              rels_object - Rels object.
              list - ['string','type'] where: type is in ['dsid', 'pid', 'literal']

        """
        obj = self._updateObject(object)
        sub = self._updateSubject(subject)
        return fedora_relationship.addRelationship(self, sub, predicate, obj)

    def getRelationships(self, subject=None, predicate=None, object=None):
        """Query relationships contained in rels_int XML.

        This function uses xpath to do a query to find all the objects that match
        the passed in arguements. Passing None acts as a wildcard.

        Arguements:
          subject -- String containing the DSID of the subject.
          predicate -- The predicate to search for.
              This is an overloaded method:
              None - Any predicate.
              String - The predicate string. The default namespace is assumed.
              rels_predicate - object with namespace alias and predicate set.
              list - ['alias','predicate']
          object -- The object to search for.
              None - Any object.
              string - String containing a DSID.
              rels_object - Rels object.
              list - ['string','type'] where: type is in ['dsid', 'pid', 'literal']

        Returns:
          List of lists of the form:
          [[subject1,predicate1,object1],[subject2,predicate2,object2]]
          The predicates and objects returned are of rels_predicate and rels_object

        """
        obj = self._updateObject(object)
        sub = self._updateSubject(subject)
        return fedora_relationship.getRelationships(self, sub, predicate, obj)

    def purgeRelationships(self, subject=None, predicate=None, object=None):
        """Purge relationships from the rels_int XML.

        This function uses xpath to do a query to remove all the objects that match
        the passed in arguements. Passing None acts as a wildcard.

        WARNING: Because None is a wildcard, passing no arguements will
                 DELETE THE ENTIRE CONTENTS of the rels_int.

        Arguements:
          subject -- String containing the DSID.
          predicate -- The predicate to remove.
              None - Any predicate.
              String - The predicate string. The default namespace is assumed.
              rels_predicate - object with namespace alias and predicate set.
              list - ['alias','predicate']
          object -- The object to remove.
              None - Any object.
              string - String containing a DSID.
              rels_object - Rels object.
              list - ['string','type'] where: type is in ['dsid', 'pid', 'literal']

        """
        obj = self._updateObject(object)
        sub = self._updateSubject(subject)
        return fedora_relationship.purgeRelationships(self, sub, predicate, obj)


class rels_ext_string(fedora_relationship):
    """Class to update a fedora RELS-EXT datastream."""

    def __init__(self, pid, namespaces = None, default_namespace = None, xml = None):
        """Constructor for rels_ext object.

        Arguements:
          obj -- The fcrepo object to modify/create rels_ext for.
          namespaces -- Namespaces to be added to the rels_ext.
              [] - list containing ['alias','uri']
              [rels_namespace, ...] - list of rels_namespace objects.
              [[],[],...[]] - list of ['alias','uri']
              rels_namespace - rels_namespace object containing namespace and alias.
          default_namespace -- String containing the alias of the default namespace.
          If no namespace is passed in then this is assumed:
          info:fedora/fedora-system:def/relations-external#

        """
        self.pid = pid
        fedora_relationship.__init__(self, namespaces, default_namespace, xml)

    def _updateObject(self, object):
        """Private method to overload object. Turns everything into a rels_object"""
        if object == None:
            obj = None
        elif isinstance(object,basestring):
            obj = rels_object('%s'%(object), rels_object.DSID)
        elif isinstance(object,rels_object):
            if object.type not in rels_object.TYPES:
                raise TypeError
            else:
                obj = copy.copy(object)
        elif isinstance(object, list):
            reltype = object[1].lower()
            if reltype == 'dsid':
                obj = rels_object(object[0], rels_object.DSID)
            elif reltype == 'pid':
                obj = rels_object(object[0], rels_object.PID)
            elif reltype == 'literal':
                obj = rels_object(object[0], rels_object.LITERAL)
            else:
                raise KeyError
        elif isinstance(object,fcrepo.object.FedoraObject):
            obj = rels_object(object.pid, rels_object.PID)
        else:
            raise TypeError
        return obj

    def addRelationship(self, predicate, object):
        """Add new relationship to rels_ext XML.

        Arguements:
          predicate -- The predicate.
              This is an overloaded method:
              String - The predicate string. The default namespace is assumed.
              rels_predicate - object with namespace alias and predicate set.
              list - ['alias','predicate']
          object -- The object.
              string - String containing a PID.
              rels_object - Rels object.
              list - ['string','type'] where: type is in ['dsid', 'pid', 'literal']

        """
        obj = self._updateObject(object)
        return fedora_relationship.addRelationship(self, self.pid, predicate, obj)

    def getRelationships(self, predicate=None, object=None):
        """Query relationships contained in rels_ext XML.

        This function uses xpath to do a query to find all the objects that match
        the passed in arguements. Passing None acts as a wildcard.

        Arguements:
          predicate -- The predicate to search for.
              This is an overloaded method:
              None - Any predicate.
              String - The predicate string. The default namespace is assumed.
              rels_predicate - object with namespace alias and predicate set.
              list - ['alias','predicate']
          object -- The object to search for.
              None - Any object.
              string - String containing a PID.
              rels_object - Rels object.
              list - ['string','type'] where: type is in ['dsid', 'pid', 'literal']

        Returns:
          List of lists of the form:
          [[subject1,predicate1,object1],[subject2,predicate2,object2]]
          The predicates and objects returned are of rels_predicate and rels_object

        """
        obj = self._updateObject(object)
        return fedora_relationship.getRelationships(self, self.pid, predicate, obj)

    def purgeRelationships(self, predicate=None, object=None):
        """Purge relationships from the rels_ext XML.

        This function uses xpath to do a query to remove all the objects that match
        the passed in arguements. Passing None acts as a wildcard.

        WARNING: Because None is a wildcard, passing no arguements will
                 DELETE THE ENTIRE CONTENTS of the rels_ext.

        Arguements:
          predicate -- The predicate to remove.
              This is an overloaded method:
              None - Any predicate.
              String - The predicate string. The default namespace is assumed.
              rels_predicate - object with namespace alias and predicate set.
              list - ['alias','predicate']
          object -- The object to remove.
              None - Any object.
              string - String containing a PID.
              rels_object - Rels object.
              list - ['string','type'] where: type is in ['dsid', 'pid', 'literal']

        """
        obj = self._updateObject(object)
        return fedora_relationship.purgeRelationships(self, self.pid, predicate, obj)

class fedora_helper():
    """This class adds fcrepo functionality to fedora_relationship_element."""
    def __init__(self, obj, reldsid):

        if reldsid in obj:
            xmlstring = obj[reldsid].getContent().read()
        else:
            xmlstring = None

        self.dsid = reldsid
        self.obj = obj

    def update(self):
        if self.modified:
            if self.dsid not in self.obj:
                self.obj.addDataStream(self.dsid, self.toString(), label=u"Fedora Object-to-Object Relationship Metadata")
            else:
                self.obj[self.dsid].setContent(self.toString())

class rels_int(rels_int_string, fedora_helper):
    """Class to update a fedora RELS-INT datastream."""

    def __init__(self, obj, namespaces = None, default_namespace = None):
        """Constructor for rels_int object.

        Arguements:
          obj -- The fcrepo object to modify/create rels_int for.
          namespaces -- Namespaces to be added to the rels_int.
              [] - list containing ['alias','uri']
              [rels_namespace, ...] - list of rels_namespace objects.
              [[],[],...[]] - list of ['alias','uri']
              rels_namespace - rels_namespace object containing namespace and alias.
          default_namespace -- String containing the alias of the default namespace.
          If no namespace is passed in then this is assumed:
          info:fedora/fedora-system:def/relations-external#

        """
        fedora_helper.__init__(self, obj, 'RELS-INT')
        rels_int_string.__init__(self, obj.pid, namespaces, default_namespace, self.xmlstring)

    def addRelationship(self, subject, predicate, object):
        """Add new relationship to rels_int XML.

        Arguements:
          subject -- String containing the DSID of the subject.
          predicate -- The predicate.
              String - The predicate string. The default namespace is assumed.
              rels_predicate - object with namespace alias and predicate set.
              list - ['alias','predicate']
          object -- The object.
              string - String containing a DSID.
              rels_object - Rels object.
              list - ['string','type'] where: type is in ['dsid', 'pid', 'literal']

        """
        return rels_int_string.addRelationship(self, subject, predicate, object)

    def getRelationships(self, subject=None, predicate=None, object=None):
        """Query relationships contained in rels_int XML.

        This function uses xpath to do a query to find all the objects that match
        the passed in arguements. Passing None acts as a wildcard.

        Arguements:
          subject -- String containing the DSID of the subject.
          predicate -- The predicate to search for.
              This is an overloaded method:
              None - Any predicate.
              String - The predicate string. The default namespace is assumed.
              rels_predicate - object with namespace alias and predicate set.
              list - ['alias','predicate']
          object -- The object to search for.
              None - Any object.
              string - String containing a DSID.
              rels_object - Rels object.
              list - ['string','type'] where: type is in ['dsid', 'pid', 'literal']

        Returns:
          List of lists of the form:
          [[subject1,predicate1,object1],[subject2,predicate2,object2]]
          The predicates and objects returned are of rels_predicate and rels_object

        """
        return rels_int_string.getRelationships(self, subject, predicate, object)

    def purgeRelationships(self, subject=None, predicate=None, object=None):
        """Purge relationships from the rels_int XML.

        This function uses xpath to do a query to remove all the objects that match
        the passed in arguements. Passing None acts as a wildcard.

        WARNING: Because None is a wildcard, passing no arguements will
                 DELETE THE ENTIRE CONTENTS of the rels_int.

        Arguements:
          subject -- String containing the DSID.
          predicate -- The predicate to remove.
              None - Any predicate.
              String - The predicate string. The default namespace is assumed.
              rels_predicate - object with namespace alias and predicate set.
              list - ['alias','predicate']
          object -- The object to remove.
              None - Any object.
              string - String containing a DSID.
              rels_object - Rels object.
              list - ['string','type'] where: type is in ['dsid', 'pid', 'literal']

        """
        return rels_int_string.purgeRelationships(self, subject, predicate, object)

    def update(self):
        """Save the updated rels_ext XML to the fedora object."""
        return fedora_helper.update(self)

class rels_ext(rels_ext_string, fedora_helper):
    """Class to update a fedora RELS-EXT datastream."""

    def __init__(self, obj, namespaces = None, default_namespace = None):
        """Constructor for rels_ext object.

        Arguements:
          obj -- The fcrepo object to modify/create rels_ext for.
          namespaces -- Namespaces to be added to the rels_ext.
              [] - list containing ['alias','uri']
              [rels_namespace, ...] - list of rels_namespace objects.
              [[],[],...[]] - list of ['alias','uri']
              rels_namespace - rels_namespace object containing namespace and alias.
          default_namespace -- String containing the alias of the default namespace.
          If no namespace is passed in then this is assumed:
          info:fedora/fedora-system:def/relations-external#

        """
        fedora_helper.__init__(self, obj, 'RELS-EXT')
        rels_ext_string.__init__(self, obj.pid, namespaces, default_namespace, self.xmlstring)

    def addRelationship(self, predicate, object):
        """Add new relationship to rels_ext XML.

        Arguements:
          predicate -- The predicate.
              This is an overloaded method:
              String - The predicate string. The default namespace is assumed.
              rels_predicate - object with namespace alias and predicate set.
              list - ['alias','predicate']
          object -- The object.
              string - String containing a PID.
              rels_object - Rels object.
              list - ['string','type'] where: type is in ['dsid', 'pid', 'literal']

        """
        return rels_ext_string.addRelationship(self, predicate, object)

    def getRelationships(self, predicate=None, object=None):
        """Query relationships contained in rels_ext XML.

        This function uses xpath to do a query to find all the objects that match
        the passed in arguements. Passing None acts as a wildcard.

        Arguements:
          predicate -- The predicate to search for.
              This is an overloaded method:
              None - Any predicate.
              String - The predicate string. The default namespace is assumed.
              rels_predicate - object with namespace alias and predicate set.
              list - ['alias','predicate']
          object -- The object to search for.
              None - Any object.
              string - String containing a PID.
              rels_object - Rels object.
              list - ['string','type'] where: type is in ['dsid', 'pid', 'literal']

        Returns:
          List of lists of the form:
          [[subject1,predicate1,object1],[subject2,predicate2,object2]]
          The predicates and objects returned are of rels_predicate and rels_object

        """
        return rels_ext_string.getRelationships(self, predicate, object)

    def purgeRelationships(self, predicate=None, object=None):
        """Purge relationships from the rels_ext XML.

        This function uses xpath to do a query to remove all the objects that match
        the passed in arguements. Passing None acts as a wildcard.

        WARNING: Because None is a wildcard, passing no arguements will
                 DELETE THE ENTIRE CONTENTS of the rels_ext.

        Arguements:
          predicate -- The predicate to remove.
              This is an overloaded method:
              None - Any predicate.
              String - The predicate string. The default namespace is assumed.
              rels_predicate - object with namespace alias and predicate set.
              list - ['alias','predicate']
          object -- The object to remove.
              None - Any object.
              string - String containing a PID.
              rels_object - Rels object.
              list - ['string','type'] where: type is in ['dsid', 'pid', 'literal']

        """
        return rels_ext_string.purgeRelationships(self, predicate, object)

    def update(self):
        """Save the updated rels_ext XML to the fedora object."""
        return fedora_helper.update(self)

# do some basic testing of the functionality
if __name__ == '__main__':

    relationship = fedora_relationship([rels_namespace('coal','http://www.coalliance.org/ontologies/relsint'), rels_namespace('jon','http://jebus/trainstation')])
    print relationship.toString()
    relationship.addRelationship('coccc:2040', rels_predicate('jon','feezle'), rels_object('JON',rels_object.LITERAL))
    print relationship.toString()

    relationship = fedora_relationship(rels_namespace('coal','http://www.coalliance.org/ontologies/relsint'), 'coal')
    print relationship.toString()
    relationship.addRelationship('coccc:2040', 'HasAwesomeness', rels_object('JON',rels_object.LITERAL))
    print relationship.toString()

    relationship = fedora_relationship()
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
