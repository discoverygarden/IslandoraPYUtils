
XACML_NAMESPACE = "urn:oasis:names:tc:xacml:1.0:policy"
XACML = "{%s}" % XACML_NAMESPACE
XSI_NAMESPACE =  "http://www.w3.org/2001/XMLSchema-instance"
XSI = "{%s}" % XSI_NAMESPACE
NSMAP = {None : XACML_NAMESPACE, 'xsi' : XSI_NAMESPACE}

stringequal = "urn:oasis:names:tc:xacml:1.0:function:string-equal"