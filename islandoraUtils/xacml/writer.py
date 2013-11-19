from lxml import etree
import islandoraUtils.xacml.constants as xacmlconstants
from islandoraUtils.xacml.exception import XacmlException
import newrelic.agent

@newrelic.agent.function_trace()
def toXML(xacml, prettyprint=False):
    # create the root element
    policy = createRoot(xacml)
    createTarget(policy, xacml)
    createRules(policy, xacml)

    # return the XML as a formatted string
    return etree.tostring(policy, pretty_print=prettyprint, xml_declaration=True)

@newrelic.agent.function_trace()
def createRoot(xacml):
    policy = etree.Element(xacmlconstants.XACML + "Policy", nsmap = xacmlconstants.NSMAP)
    policy.set('PolicyId','islandora-xacml-editor-v1')
    policy.set('RuleCombiningAlgId', xacml['RuleCombiningAlgId'])
    return policy

@newrelic.agent.function_trace()
def createTarget(policy, xacml):
    target = etree.SubElement(policy, xacmlconstants.XACML + 'Target')

    subjects = etree.SubElement(target, xacmlconstants.XACML + 'Subjects')
    etree.SubElement(subjects, xacmlconstants.XACML + 'AnySubject')

    resources = etree.SubElement(target, xacmlconstants.XACML + 'Resources')
    etree.SubElement(resources, xacmlconstants.XACML + 'AnyResource')

    actions = etree.SubElement(target, xacmlconstants.XACML + 'Actions')
    etree.SubElement(actions, xacmlconstants.XACML + 'AnyAction')

@newrelic.agent.function_trace()
def createRules(policy, xacml):
    for rule in xacml['rules']:
        createRule(policy, rule)

@newrelic.agent.function_trace()
def createRule(policy, rule):
    root = etree.SubElement(policy, xacmlconstants.XACML + 'Rule')

    root.set('RuleId', rule['ruleid'])
    root.set('Effect', rule['effect'])

    createRuleTarget(root, rule)
    createRuleCondition(root, rule)

@newrelic.agent.function_trace()
def createRuleTarget(root, rule):
    target = etree.SubElement(root, xacmlconstants.XACML + "Target")

    createRuleTargetSubjects(target, rule)
    createRuleTargetResources(target, rule)
    createRuleTargetActions(target, rule)

@newrelic.agent.function_trace()
def createRuleTargetSubjects(target, rule):
    subjects = etree.SubElement(target, xacmlconstants.XACML +  "Subjects")
    etree.SubElement(subjects, xacmlconstants.XACML + "AnySubject")

@newrelic.agent.function_trace()
def createRuleTargetActions(target, rule):
    actions = etree.SubElement(target, xacmlconstants.XACML +  "Actions")
    if rule['methods']:
        for method in rule['methods']:
            createRuleTargetAction(actions, method)
    else:
        etree.SubElement(actions, xacmlconstants.XACML + "AnyAction")

@newrelic.agent.function_trace()
def createRuleTargetAction(actions, method):
    action = etree.SubElement(actions, xacmlconstants.XACML + 'Action')
    actionMatch = etree.SubElement(action, xacmlconstants.XACML +  'ActionMatch')
    actionMatch.set('MatchId',xacmlconstants.stringequal)

    if method == 'api-a' or method == 'api-m':
        attributevalue = 'urn:fedora:names:fedora:2.1:action:' + method
        attributeid = 'urn:fedora:names:fedora:2.1:action:api'
    else:
        attributevalue = 'urn:fedora:names:fedora:2.1:action:id-' + method
        attributeid = "urn:fedora:names:fedora:2.1:action:id"

    attributeValue = etree.SubElement(actionMatch, xacmlconstants.XACML +  "AttributeValue")
    attributeValue.text = attributevalue
    attributeValue.set("DataType","http://www.w3.org/2001/XMLSchema#string")

    actionAttributeDesignator = etree.SubElement(actionMatch, xacmlconstants.XACML +  "ActionAttributeDesignator")
    actionAttributeDesignator.set("AttributeId", attributeid)
    actionAttributeDesignator.set("DataType","http://www.w3.org/2001/XMLSchema#string")

@newrelic.agent.function_trace()
def createRuleTargetResources(target, rule):
    resources = etree.SubElement(target, xacmlconstants.XACML +  "Resources")

    if not rule['mimes'] and not rule['dsids']:
        etree.SubElement(resources, xacmlconstants.XACML + "AnyResource")
    else:
        for mime in rule['mimes']:
            createRuleTargetResource(resources, mime, 'mime')
        for dsid in rule['dsids']:
            createRuleTargetResource(resources, dsid, 'dsid')

@newrelic.agent.function_trace()
def createRuleTargetResource(resources, name, type):
    resource = etree.SubElement(resources, xacmlconstants.XACML +  'Resource')
    resourceMatch = etree.SubElement(resource, xacmlconstants.XACML +  'ResourceMatch')
    resourceMatch.set('MatchId', xacmlconstants.stringequal)

    AttributeValue = etree.SubElement(resourceMatch, xacmlconstants.XACML +  'AttributeValue')
    AttributeValue.text = name
    AttributeValue.set('DataType',"http://www.w3.org/2001/XMLSchema#string")

    ResourceAttributeDesignator = etree.SubElement(resourceMatch, xacmlconstants.XACML +  'ResourceAttributeDesignator')
    ResourceAttributeDesignator.set("DataType","http://www.w3.org/2001/XMLSchema#string")

    if type == 'mime':
        ResourceAttributeDesignator.set("AttributeId","urn:fedora:names:fedora:2.1:resource:datastream:mimeType")
    elif type == 'dsid':
        ResourceAttributeDesignator.set("AttributeId","urn:fedora:names:fedora:2.1:resource:datastream:id")

@newrelic.agent.function_trace()
def createRuleCondition(target, rule):
    condition = etree.Element(xacmlconstants.XACML + "Condition")
    condition.set("FunctionId", "urn:oasis:names:tc:xacml:1.0:function:not")

    if rule['users']:
      users = createRuleConditionApply(rule['users'],'user')

    if rule['roles']:
      roles = createRuleConditionApply(rule['roles'],'role')

    try:
        apply = etree.Element(xacmlconstants.XACML +  "Apply")
        apply.set("FunctionId","urn:oasis:names:tc:xacml:1.0:function:or")
        apply.append(users)
        apply.append(roles)
        condition.append(apply)
        target.append(condition)
    except NameError:
        try:
            condition.append(users)
            target.append(condition)
        except NameError:
            pass
        try:
            condition.append(roles)
            target.append(condition)
        except NameError:
            pass

@newrelic.agent.function_trace()
def createRuleConditionApply(attributes, type):
    apply = etree.Element(xacmlconstants.XACML + 'Apply')
    apply.set("FunctionId","urn:oasis:names:tc:xacml:1.0:function:string-at-least-one-member-of")

    subjectAttribureDesignator = etree.SubElement(apply, xacmlconstants.XACML +  'SubjectAttributeDesignator')
    subjectAttribureDesignator.set("DataType", "http://www.w3.org/2001/XMLSchema#string")
    subjectAttribureDesignator.set("MustBePresent", "false")

    if type == 'role':
        subjectAttribureDesignator.set('AttributeId',"fedoraRole")
    elif type == 'user':
        subjectAttribureDesignator.set('AttributeId',"urn:fedora:names:fedora:2.1:subject:loginId")

    stringBag = etree.SubElement(apply, xacmlconstants.XACML + "Apply")
    stringBag.set("FunctionId", "urn:oasis:names:tc:xacml:1.0:function:string-bag")

    for attribute in attributes:
      attrib = etree.SubElement(stringBag, xacmlconstants.XACML +  "AttributeValue")
      attrib.text = attribute
      attrib.set("DataType","http://www.w3.org/2001/XMLSchema#string")

    return apply
