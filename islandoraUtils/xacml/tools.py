import islandoraUtils.xacml.writer as xacmlwriter
import islandoraUtils.xacml.parser as xacmlparser
import islandoraUtils.xacml.constants as xacmlconst

from abc import ABCMeta

'''
 @file
 This file defines a set of object for manipulating XACML. Other files in the
 XACML module provide a lower level access to creating XCAML these objects
 work together to provide a nice high level view of a standard islandora
 XACML object.

 All of this was hastily ported from PHP, so the comments may say array
 when they in fact mean list, set or dictionary. If you see these references
 please correct them.
'''

'''
 This abstract class represents a general XACML Rule. The XACML object contains
 4 standard XACML rules, which are all extended from this base class.
'''
class XacmlRule:

    # define this is an abstract base class
    __metaclass__ = ABCMeta

    '''
    Private internal representation of the XACML rule.
    '''
    _rule = None

    '''
    This points to the Xacml object that this rule is instantiated inside of,
    so that references to other rules can be made.
    @var Xacml
    '''
    _xacml = None;

    '''
    Initialized a rule datastructure
    @param $id
      Takes the ID for the new rule as a string.
    @param $effect
      The effect of the rule (Permit or Deny)
    @return array
      The rule dictionary.
    '''
    def _initializeRule(self, id, effect):
        rule = {}

        rule['ruleid'] = id
        rule['effect'] = effect;

        rule['users'] = set();
        rule['roles'] = set();
        rule['methods'] = [];

        return rule

    '''
    Helper function. Allows strings or arrays of strings to be passed in.

    @param $type
      Array key to modify in internal $rules datastructure.
    @param $data
      Data to be added.
    '''
    def _setValue(self, type, data):
        if isinstance(data, basestring):
            self._rule[type].add(data)
        else:
            self._rule[type] |= set(data)

    '''
    Helper function. We want to return lists.

    @param $type
      Array key in internal datastructure to return
    @return
      Array requested.
    '''
    def _getValues(self, type):
        return list(self._rule[type])

    '''
    Uses the set functionality to remove data from internal rule representation.

    @param $type
      Array key to work on
    @param $data
      Data to be removed.
    '''
    def _removeValue(self, type, datarg):

        if isinstance(datarg, basestring):

            data = set([datarg])
        else:
            data = set(datarg)

        self._rule[type] -= data

    '''
    Constructs new XacmlRule. This generic constructor does not set any
    methods. It assumes if arg1 is an array that array is an existing
    xacml rule datastructure. Concrete implementations should call
    parent::__construct then initialize the datastructure correctly if
    arg1 is NULL by calling parent::initializeRule() with the proper
    methods.
   
    @param $arg1
      array containing pre-exisitng xacml rule or NULL.
    @param $xacml
      reference to the XACML object that this datastructure is part of.
    '''
    def __init__(self, xacml, rule = None):
        if (rule):
            self._rule = self._initializeRule(rule['ruleid'], rule['effect'])
            self._rule['users'] |= set(rule['users'])
            self._rule['roles'] |= set(rule['roles'])
            self._rule['methods'] = list(rule['methods'])
            self._setValue('users', 'fedoraAdmin')
            self._setValue('roles', 'administrator')

        self.xacml = xacml

    '''
    Returns true if the rule is populated with data, otherwise returns false.
   
    For example a rule can be created that has no users or roles. This rule has
    no meaning in XACML. We need Users and Roles associated with the rule. This
    function lets us know if the rule has be populated.
   
    @return boolean
    '''
    def isPopulated(self):
        return self.getUsers() or self.getRoles()

    '''
    Add a user to the XACML rule.
   
    @param $user
      String or array or strings containing users to add.
    '''
    def addUser(self, user):
       self._setValue('users', user)

    '''
    Add roles to the XACML rule.
   
    @param $role
      String or array of string containing roles to add.
    '''
    def addRole(self,role):
        self._setValue('roles', role)

    '''
    Remove users from XACML Rule.
   
    @param $user
      String or array of strings with users to remove.
    '''
    def removeUser(self, user):
        self._removeValue('users', user)

    '''
    Remove roles from XACML rule.
   
    @param $role
      String or array of string with roles to remove.
    '''
    def removeRole(self, role):
        self._removeValue('roles', role)

    '''
    Get users associated with this XACML rule.
   
    @return
      Array containing the users.
    '''
    def getUsers(self):
        return self._getValues('users')

    '''
    Get roles associated with this XACML rule.
   
    @return
      Array containing the roles.
    '''
    def getRoles(self):
        return self._getValues('roles')

    '''
    Return the $rule datastructure associated with this object. This can be parsed by XacmlWriter.
   
    @return
      array containing the datastructure.
    '''
    def getRuleArray(self):
        rule = {}

        # make frigging sure that these are included
        self.addUser('fedoraAdmin');
        self.addRole('administrator')

        rule['ruleid'] = self._rule['ruleid']
        rule['effect'] = self._rule['effect']
        rule['users'] = list(self._rule['users'])
        rule['roles'] = list(self._rule['roles'])

        # copy methods
        rule['methods'] = list(self._rule['methods'])

        rule['dsids'] = []
        rule['mimes'] = []

        return rule

'''
This is the concrete implementation of XacmlRule for the rule restricting who
can manage an object.
'''
class XacmlManagementRule(XacmlRule):
    '''
    This calls the parent constructor and then if $arg1 is NULL instantiates the
    rule as a blank rule.
   
    @param $arg1
      Existing Rule datastructure with ID MANAGEMENT_RULE or NULL
    @param $xacml
      Reference to the parent XACML object.
    '''
    def __init__(self, xacml, rule = None):
        XacmlRule.__init__(self, xacml, rule)
        if(not rule):
            self._rule = self._initializeRule(xacmlconst.MANAGEMENT_RULE, 'Deny')
            self._rule['methods'] = [
                'addDatastream',
                'addDisseminator',
                'adminPing',
                'getDisseminatorHistory',
                'getNextPid',
                'ingest',
                'modifyDatastreamByReference',
                'modifyDatastreamByValue',
                'modifyDisseminator',
                'modifyObject',
                'purgeObject',
                'purgeDatastream',
                'purgeDisseminator',
                'setDatastreamState',
                'setDisseminatorState',
                'setDatastreamVersionable',
                'compareDatastreamChecksum',
                'serverShutdown',
                'serverStatus',
                'upload',
                'dsstate',
                'resolveDatastream',
                'reloadPolicies'
            ]

'''
This is the concrete implementation of XacmlRule for the rule restricting who
can view an object.
'''
class XacmlViewingRule( XacmlRule ):

    '''
    This calls the parent constructor and then if $arg1 is NULL instantiates
    the rule as a new blank rule.
   
    @param $arg1
      Existing Rule datastructure with ID VIEWING_RULE or NULL
    @param $xacml
      Reference to the parent XACML object.
    '''
    def __init__(self, xacml, rule = None):
        XacmlRule.__init__(self, xacml, rule)
        if not rule:
            self._rule = self._initializeRule(xacmlconst.VIEWING_RULE, 'Deny')
            self._rule['methods'] = [
                'api-a',
                'getDatastreamHistory',
                'listObjectInResourceIndexResults'
            ]

    '''
    Calls parent::getRuleArray() and then adds the roles and users fromt the
    managementRule and datastreamRule datastructues if they are populated. This
    ensures that our xacml object works as expected. Otherwise it would be
    possible to have people that could manage an object but not view
    datastreams. An unexpected behavior.
   
    @return
      $rule datastructure parsable by XacmlWriter.
    '''
    def getRuleArray(self):
        rule = XacmlRule.getRuleArray(self)
        users = set(rule['users'])
        roles = set(rule['roles'])

        if self.xacml.managementRule.isPopulated():
            users |= set(self.xacml.managementRule.getUsers())
            roles |= set(self.xacml.managementRule.getRoles())

        if self.xacml.datastreamRule.isPopulated():
            users |= set(self.xacml.datastreamRule.getUsers())
            roles |= set(self.xacml.datastreamRule.getRoles())

        rule['users'] = list(users)
        rule['roles'] = list(roles)

        return rule

'''
This is a concrete implementaion of a XacmlRule that allows everything. It needs
to be added to the end of every XACML policy to allow anything not explicitly
forbidden by the policy. Otherwise XACML defaults to denying access.

This is entirely managed by Xacml object so not much needs to be said about it.
'''
class XacmlPermitEverythingRule(XacmlRule):
    def __init__(self, xacml):
        XacmlRule.__init__(self, xacml)
        self._rule = self._initializeRule(xacmlconst.PERMIT_RULE, 'Permit')

    def getRuleArray(self):
        rule = XacmlRule.getRuleArray(self)

        rule['roles'] = []
        rule['users'] = []

        return rule

'''
A concrete implementation of XacmlRule to restrict who can view certain mimetypes and datastreams.
'''
class XacmlDatastreamRule(XacmlRule):

    def __init__(self, xacml, rule = None):
        XacmlRule.__init__(self, xacml, rule)
        if not rule:
            self._rule = self._initializeRule(xacmlconst.DATASTREAM_RULE, 'Deny')
            self._rule['methods'] = [
                'getDatastreamDissemination'
            ]
            self._rule['mimes'] = set()
            self._rule['dsids'] = set()
        else:
            self._rule['mimes'] = set(rule['mimes'])
            self._rule['dsids'] = set(rule['dsids'])

    '''
    Calls parent::getRuleArray() and then adds the roles and users fromt the
    managementRule object if they are populated. This ensures that our xacml
    object works as expected. Otherwise it would be possible to have people that
    could manage an object but not view datastreams. An unexpected behavior.
   
    @return
      $rule datastructure parsable by XacmlWriter.
    '''
    def getRuleArray(self):
        rule = XacmlRule.getRuleArray(self)
        rule['dsids'] = list(self._rule['dsids'])
        rule['mimes'] = list(self._rule['mimes'])

        if self.xacml.managementRule.isPopulated():
            users = set(rule['users'])
            roles = set(rule['roles'])
            users |= set(self.xacml.managementRule.getUsers())
            roles |= set(self.xacml.managementRule.getRoles())
            rule['users'] = list(users)
            rule['roles'] = list(roles)

        return rule

    '''
    Add a dsid to the rule.
   
    @param $dsid
      String or array of strings containing the datastream to add.
    '''
    def addDsid(self, dsid):
        self._setValue('dsids', dsid)

    '''
    Add a mimetype to the rule.
   
    @param $mime
    String or array of strings to add to the rule.
    '''
    def addMimetype(self, mime):
        self._setValue('mimes', mime)

    '''
    Remove mimetypes from the rule.
   
    @param $mime
      String or array ofs tring to remove from the rule.
    '''
    def removeMimetype(self, mime):
        self._removeValue('mimes', mime)

    def removeDsid(self, dsid):
        self._removeValue('dsids', dsid)

    def getMimetypes(self):
        return self._getValues('mimes')

    def getDsids(self):
        return self._getValues('dsids')

    '''
    Returns true if the rule is populated with data, otherwise returns false.
   
    For example a rule can be created that has no users, roles, dsids or mimetypes.
    This makes sure there is at least on role or user and at least one mimtype or dsid.
   
    @return boolean
    '''
    def isPopulated(self):
        return XacmlRule.isPopulated(self) and (self.getMimetypes or self.getDsids())

'''
 This class is how programmers should interact with Xacml objects. It takes either xacml XAML as a string
 or no arguements and creates a blank xacml object. The interaction with the rules takes place through
 member object of this class. For instance to add roles that can manage the object:
 @code
 from islandoraUtils.xacml.tools import Xacml
    xacml = Xacml()
    # allow userA to manage the object
    xacml.managementRule.addUser('userA')
    # allow roleC and roleD to manage the object
    xacml.managementRule.addRole(['roleC', 'roleD'])
 @endcode
'''
class Xacml:

    _permitEverythingRule = None;

    '''
    Rule controling who can manage the object with this XACML policy.
    @var XacmlManagementRule
    '''
    managementRule = None;

    '''
    Rule controlling who can view the specific datastreams and mimetypes that are in this rule.
    @var XacmlDatastreamRule
    '''
    datastreamRule = None

    '''
    Rule controlling who can view datastreams in this object.
    @var XacmlViewingRule
    '''
    viewingRule = None

    '''
    The constructor for the XACML object. Initialize new XACML object.
   
    @param (optional) $xacml The XACML XML as a string. If this isn't passed
      the constructor will instead create a new XACML object that permits
      everything.
    @throws XacmlException if the XML cannot be parsed
    '''
    def __init__(self, xacml = None):
        management_rule = None;
        datastream_rule = None;
        viewing_rule = None;

        if xacml != None:
            xacmlds = xacmlparser.parse(xacml)

            # decide what is enabled
            for rule in xacmlds['rules']:
                if rule['ruleid'] == xacmlconst.MANAGEMENT_RULE:
                    management_rule = rule
                elif rule['ruleid'] == xacmlconst.DATASTREAM_RULE:
                    datastream_rule = rule
                elif rule['ruleid'] == xacmlconst.VIEWING_RULE:
                    viewing_rule = rule

        self.datastreamRule = XacmlDatastreamRule(self, datastream_rule)
        self.managementRule = XacmlManagementRule(self, management_rule)
        self.viewingRule = XacmlViewingRule(self, viewing_rule)
        self.permitEverythingRule = XacmlPermitEverythingRule(self)

    '''
    This creates a datastructure to be passed into XacmlWriter. It takes into
    account which rules have been populated.
    '''
    def _getXacmlDatastructure(self):
        xacml = {
            'RuleCombiningAlgId' : 'urn:oasis:names:tc:xacml:1.0:rule-combining-algorithm:first-applicable',
            'rules'              : []
        }
        
        if self.datastreamRule.isPopulated():
            xacml['rules'].append(self.datastreamRule.getRuleArray())
        if self.managementRule.isPopulated():
            xacml['rules'].append(self.managementRule.getRuleArray())
        if self.viewingRule.isPopulated():
            xacml['rules'].append(self.viewingRule.getRuleArray())

        xacml['rules'].append(self.permitEverythingRule.getRuleArray())

        return xacml

    '''
    Returns a string containing the XML for this XACML policy.
   
    @param boolean $prettyPrint
      If set to TRUE the function will return a prettyprinted xacml policy.
   
    @return string containing xacml xml
    '''
    def getXmlString(self, prettyPrint=True):
        xacml = self._getXacmlDatastructure()
        return xacmlwriter.toXML(xacml, prettyPrint);
