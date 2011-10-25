
XACML_NAMESPACE = "urn:oasis:names:tc:xacml:1.0:policy"
XACML = "{%s}" % XACML_NAMESPACE
XSI_NAMESPACE =  "http://www.w3.org/2001/XMLSchema-instance"
XSI = "{%s}" % XSI_NAMESPACE
NSMAP = {None : XACML_NAMESPACE, 'xsi' : XSI_NAMESPACE}
XPATH_MAP = {'xacml' : XACML_NAMESPACE, 'xsi' : XSI_NAMESPACE}

stringequal = "urn:oasis:names:tc:xacml:1.0:function:string-equal"
mime = "urn:fedora:names:fedora:2.1:resource:datastream:mimeType"
dsid = "urn:fedora:names:fedora:2.1:resource:datastream:id"
onememeberof = "urn:oasis:names:tc:xacml:1.0:function:string-at-least-one-member-of"

MANAGEMENT_RULE = 'deny-management-functions';
DATASTREAM_RULE = 'deny-dsid-mime';
VIEWING_RULE = 'deny-access-functions';
PERMIT_RULE = 'allow-everything-else';