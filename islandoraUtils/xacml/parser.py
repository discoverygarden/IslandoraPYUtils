import islandoraUtils.xacml.constants as xacmlconstants
from islandoraUtils.xacml.exception import XacmlException
import string
from lxml import etree

@newrelic.agent.function_trace()
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

@newrelic.agent.function_trace()
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
        findUsers(rule, rule_element)

        xacml['rules'].append(rule)

@newrelic.agent.function_trace()
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

@newrelic.agent.function_trace()
def findMethods(rule, element):
    actions = element.find(xacmlconstants.XACML + "Target/" + xacmlconstants.XACML + "Actions")
    values = actions.findall('.//' + xacmlconstants.XACML + 'AttributeValue')

    for value in values:
        method = value.text

        if string.find(method, 'api-a') != -1 or string.find(method, 'api-m') != -1:
            rule['methods'].append(method[35:])
        else:
            rule['methods'].append(method[38:])

@newrelic.agent.function_trace()
def findRoles(rule, element):
    role_designator = element.xpath('.//xacml:Apply[@FunctionId="'+xacmlconstants.onememeberof+'"]/xacml:SubjectAttributeDesignator[@AttributeId="fedoraRole"]', namespaces=xacmlconstants.XPATH_MAP)
    if len(role_designator) != 0:
        role_attrib = role_designator[0].xpath('../xacml:Apply/xacml:AttributeValue', namespaces=xacmlconstants.XPATH_MAP)
        for role in role_attrib:
            rule['roles'].append(role.text)

@newrelic.agent.function_trace()
def findUsers(rule, element):
    user_designator = element.xpath('.//xacml:Apply[@FunctionId="'+xacmlconstants.onememeberof+'"]/xacml:SubjectAttributeDesignator[@AttributeId="urn:fedora:names:fedora:2.1:subject:loginId"]', namespaces=xacmlconstants.XPATH_MAP)
    if len(user_designator) != 0:
        user_attrib = user_designator[0].xpath('../xacml:Apply/xacml:AttributeValue', namespaces=xacmlconstants.XPATH_MAP)

        for user in user_attrib:
            rule['users'].append(user.text)
