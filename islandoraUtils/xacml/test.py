from islandoraUtils.xacml.tools import Xacml

xacml = Xacml()
xacml.managementRule.addUser('jon')
xacml.managementRule.addRole(['roleA', 'roleB'])
xacml.managementRule.removeRole('roleB')

xacml.viewingRule.addUser('feet')
xacml.viewingRule.addRole('toes')

xacml.datastreamRule.addUser('22')
xacml.datastreamRule.addDsid('OBJ')
xacml.datastreamRule.addMimetype('image/pdf')

xstring = xacml.getXmlString()
xacml = Xacml(xstring)
xstring2 = xacml.getXmlString()

print xstring2