import xacmlconstants
import string
from xacmlexception import XacmlException
from lxml import etree

def parse (xacml_string):
    xacml = {}
    xacml['rules'] = []

    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.fromstring(xacml_string, parser)

    # Do basic sanity check that root element is <Policy>
    if root.tag != xacmlconstants.XACML + 'Policy':
      raise XacmlException('Root tag is not Policy.')

    # see if the policy was written by islandora, othewise throw an exception
    if root.get('PolicyId') != 'islandora-xacml-editor-v1':
      raise XacmlException('XACML file was not written by XACML Editor.')

    parseXacml(xacml, root)

    return xacml

def parseXacml(xacml, root):
    xacml['PolicyId'] = root.get("PolicyId")
    xacml['RuleCombiningAlgId'] = root.get("RuleCombiningAlgId")

    # get each rule element
    for rule_element in root.findall(xacmlconstants.XACML + "Rule"):
        rule = {}

        rule['effect'] = rule_element.get("Effect")
        rule['ruleid'] = rule_element.get("RuleId")
        rule['dsids'] = []
        rule['mimes'] = []
        rule['methods'] = []
        rule['users'] = []
        rule['roles'] = []

        findDsidMime(rule, rule_element)
        findMethods(rule, rule_element)
        findRoles(rule, rule_element)
        #findUsers(rule, rule_element)

        xacml['rules'].append(rule)

def findDsidMime(rule, element):
    resources = element.findall('.//' + xacmlconstants.XACML + "ResourceMatch")

    for resource in resources:
        value = resource[0].text
        type = resource[1].get("AttributeId")

        if(type == xacmlconstants.mime):
            rule['mimes'].append(value)
        elif(type == xacmlconstants.dsid):
            rule['dsids'].append(value)
        else:
            raise XacmlException('Unknown ResourceMatch AttributeId.')

def findMethods(rule, element):
    actions = element.find(xacmlconstants.XACML + "Target/" + xacmlconstants.XACML + "Actions")
    values = actions.findall('.//' + xacmlconstants.XACML + 'AttributeValue')

    for value in values:
        method = value.text

        if string.find(method, 'api-a') != -1 or string.find(method, 'api-m') != -1:
            rule['methods'].append(method[35:])
        else:
            rule['methods'].append(method[38:])

def findRoles(rule, element):
    role_designator = element.find('.//' + xacmlconstants.XACML + 'Apply[@FunctionId=' + xacmlconstants.onememeberof + ']/' + xacmlconstants.XACML + 'SubjectAttributeDesignator[@AttributeId="fedoraRole"]')
    print role_designator

#    if($role_designator->length != 0) {
#      $role_attrib = $xpath->query('../xacml:Apply/xacml:AttributeValue',$role_designator->item(0));
#
#      foreach($role_attrib as $role) {
#        $rule['roles'][] = $role->nodeValue;
#      }
#    }
#  }