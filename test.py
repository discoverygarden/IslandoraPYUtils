import xacmlwriter
import xacmlparser
import pprint

xacml = {
  'RuleCombiningAlgId' : 'urn:oasis:names:tc:xacml:1.0:rule-combining-algorithm:first-applicable',
  'rules' : [
    {
      'id' : 'denyapi-access-to-datastream-except-to-user-or-role',
      'effect' : 'Deny',
      'methods' : ['getDatastreamDissemination'],
      'dsids' : ['AboutStacks.pdf'],
      'users' : ['usera', 'userb'],
      'roles' : [],
      'mimes' : ['image/tiff', 'audio/x-wave'],
    },
    {
      'id' : 'denyapi-except-to-user-or-role',
      'effect' : 'Deny',
      'methods' : ['ingest', 'modifyDatastreamByReference', 'modifyDatastreamByValue', 'modifyDisseminator', 'purgeObject', 'purgeDatastream', 'purgeDisseminator', 'setDatastreamState', 'setDisseminatorState', 'setDatastreamVersionable', 'addDatastream', 'addDisseminator'],
      'dsids' : [],
      'mimes' : [],
      'users' : [],
      'roles' : ['roleb', 'rolec'],
    },
  ]
}

pp = pprint.PrettyPrinter(indent=4)
xml = xacmlwriter.toXML(xacml,True)
print xml
xacml = xacmlparser.parse(xml)
pp.pprint(xacml)
