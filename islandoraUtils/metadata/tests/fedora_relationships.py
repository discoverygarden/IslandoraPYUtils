import unittest
from islandoraUtils.metadata.fedora_relationships import rels_namespace, rels_object, rels_ext_string, rels_int_string, fedora_relationship, rels_predicate
from lxml import etree
import xml.etree.ElementTree

class XmlHelper:
    @classmethod
    def mangle(cls, xmlStr):
        parser = etree.XMLParser(remove_blank_text=True) # xml parser ignoring whitespace
        root = etree.fromstring(xmlStr, parser)
        xmlStr = etree.tostring(root, pretty_print=False)
        xmlElement = xml.etree.ElementTree.XML(xmlStr)
        xmlStr = xml.etree.ElementTree.tostring(xmlElement, 'UTF-8')
        return xmlStr


class TestRelsExtBigD(unittest.TestCase):
    def setUp(self):
        xml = """
<rdf:RDF xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:fedora="info:fedora/fedora-system:def/relations-external#" xmlns:fedora-model="info:fedora/fedora-system:def/model#" xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#">
    <rdf:Description rdf:about="info:fedora/cogru:1332">
        <fedora:isMemberOfCollection rdf:resource="info:fedora/cogru:1130"></fedora:isMemberOfCollection>
        <fedora-model:hasModel xmlns="info:fedora/fedora-system:def/model#" rdf:resource="info:fedora/cogru:cogruETD"></fedora-model:hasModel>
    </rdf:Description>
</rdf:RDF>
        """
        self.xml = xml
        self.relsext = rels_ext_string('cogru:1332', rels_namespace('islandora','http://islandora.ca/ontology/relsext#'), 'islandora', xml)

    def tearDown(self):
        self.relsext = None

    def test_add_literal(self):
        xmlStr = """
<rdf:RDF xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:islandora="http://islandora.ca/ontology/relsext#" xmlns:fedora="info:fedora/fedora-system:def/relations-external#" xmlns:fedora-model="info:fedora/fedora-system:def/model#" xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#">
    <rdf:Description rdf:about="info:fedora/cogru:1332">
        <fedora:isMemberOfCollection rdf:resource="info:fedora/cogru:1130"></fedora:isMemberOfCollection>
        <fedora-model:hasModel xmlns="info:fedora/fedora-system:def/model#" rdf:resource="info:fedora/cogru:cogruETD"></fedora-model:hasModel>
        <islandora:isViewableByUser>Jon</islandora:isViewableByUser>
    </rdf:Description>
</rdf:RDF>
        """

        self.relsext.addRelationship('isViewableByUser', rels_object('Jon',rels_object.LITERAL))

        expected_string = XmlHelper.mangle(xmlStr)
        result_string = XmlHelper.mangle(self.relsext.toString())

        self.assertEqual(expected_string, result_string, 'generated xml does not match')

    def test_purge_literal(self):
        #add literal then delete it
        self.relsext.addRelationship('isViewableByUser', rels_object('Jon',rels_object.LITERAL))
        self.relsext.purgeRelationships(predicate='isViewableByUser')

        expected_string = XmlHelper.mangle(self.xml)
        result_string = XmlHelper.mangle(self.relsext.toString())

        self.assertEqual(expected_string, result_string, 'generated xml does not match')

    def test_get_literal(self):
        #add literal then delete it
        self.relsext.addRelationship('isViewableByUser', rels_object('Jon',rels_object.LITERAL))
        relationships = self.relsext.getRelationships(predicate='isViewableByUser')

        self.assertEqual(len(relationships), 1, 'Too many relationships returned')

        relationships = relationships[0]

        self.assertEqual(relationships[0], 'cogru:1332', 'Incorrect Subject')
        self.assertEqual("%s" % relationships[1], 'isViewableByUser', 'Incorrect Predicate')
        self.assertEqual("%s" % relationships[2], 'Jon', 'Incorrect literal')

class TestRelsExtSmallD(unittest.TestCase):
    def setUp(self):
        xml = """
<rdf:RDF xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:fedora="info:fedora/fedora-system:def/relations-external#" xmlns:fedora-model="info:fedora/fedora-system:def/model#" xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#">
    <rdf:description rdf:about="info:fedora/cogru:1332">
        <fedora:isMemberOfCollection rdf:resource="info:fedora/cogru:1130"></fedora:isMemberOfCollection>
        <fedora-model:hasModel xmlns="info:fedora/fedora-system:def/model#" rdf:resource="info:fedora/cogru:cogruETD"></fedora-model:hasModel>
    </rdf:description>
</rdf:RDF>
        """
        self.xml = xml
        self.relsext = rels_ext_string('cogru:1332', rels_namespace('islandora','http://islandora.ca/ontology/relsext#'), 'islandora', xml)

    def tearDown(self):
        self.relsext = None

    def test_add_literal(self):
        xmlStr = """
<rdf:RDF xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:islandora="http://islandora.ca/ontology/relsext#" xmlns:fedora="info:fedora/fedora-system:def/relations-external#" xmlns:fedora-model="info:fedora/fedora-system:def/model#" xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#">
    <rdf:description rdf:about="info:fedora/cogru:1332">
        <fedora:isMemberOfCollection rdf:resource="info:fedora/cogru:1130"></fedora:isMemberOfCollection>
        <fedora-model:hasModel xmlns="info:fedora/fedora-system:def/model#" rdf:resource="info:fedora/cogru:cogruETD"></fedora-model:hasModel>
        <islandora:isViewableByUser>Jon</islandora:isViewableByUser>
    </rdf:description>
</rdf:RDF>
        """

        self.relsext.addRelationship('isViewableByUser', rels_object('Jon',rels_object.LITERAL))

        expected_string = XmlHelper.mangle(xmlStr)
        result_string = XmlHelper.mangle(self.relsext.toString())

        self.assertEqual(expected_string, result_string, 'generated xml does not match')

    def test_purge_literal(self):
        #add literal then delete it
        self.relsext.addRelationship('isViewableByUser', rels_object('Jon',rels_object.LITERAL))
        self.relsext.purgeRelationships(predicate='isViewableByUser')

        expected_string = XmlHelper.mangle(self.xml)
        result_string = XmlHelper.mangle(self.relsext.toString())

        self.assertEqual(expected_string, result_string, 'generated xml does not match')

    def test_get_literal(self):
        #add literal then delete it
        self.relsext.addRelationship('isViewableByUser', rels_object('Jon',rels_object.LITERAL))
        relationships = self.relsext.getRelationships(predicate='isViewableByUser')

        self.assertEqual(len(relationships), 1, 'Too many relationships returned')

        relationships = relationships[0]

        self.assertEqual(relationships[0], 'cogru:1332', 'Incorrect Subject')
        self.assertEqual("%s" % relationships[1], 'isViewableByUser', 'Incorrect Predicate')
        self.assertEqual("%s" % relationships[2], 'Jon', 'Incorrect literal')

class TestFedoraRelationship(unittest.TestCase):

    def test_two_namespace_literal(self):
        xmlStr = """
<rdf:RDF xmlns:coal="http://www.coalliance.org/ontologies/relsint" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:fedora="info:fedora/fedora-system:def/relations-external#" xmlns:jon="http://jebus/trainstation">
  <rdf:Description rdf:about="info:fedora/coccc:2040">
    <jon:feezle>JON</jon:feezle>
  </rdf:Description>
</rdf:RDF>
        """
        relationship = fedora_relationship([rels_namespace('coal','http://www.coalliance.org/ontologies/relsint'), rels_namespace('jon','http://jebus/trainstation')])
        relationship.addRelationship('coccc:2040', rels_predicate('jon','feezle'), rels_object('JON',rels_object.LITERAL))
        result_string = XmlHelper.mangle(relationship.toString())
        expected_string = XmlHelper.mangle(xmlStr)
        self.assertEqual(result_string, expected_string, 'Generated XML Incorrect')

    def test_one_namespace_literal(self):
        xmlStr = """
<rdf:RDF xmlns:coal="http://www.coalliance.org/ontologies/relsint" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:fedora="info:fedora/fedora-system:def/relations-external#">
  <rdf:Description rdf:about="info:fedora/coccc:2040">
    <coal:HasAwesomeness>JON</coal:HasAwesomeness>
  </rdf:Description>
</rdf:RDF>
        """
        relationship = fedora_relationship(rels_namespace('coal','http://www.coalliance.org/ontologies/relsint'), 'coal')
        relationship.addRelationship('coccc:2040', 'HasAwesomeness', rels_object('JON',rels_object.LITERAL))
        result_string = XmlHelper.mangle(relationship.toString())
        expected_string = XmlHelper.mangle(xmlStr)
        self.assertEqual(result_string, expected_string, 'Generated XML Incorrect')

    def test_literal_pid_dsid(self):
        xmlStr= """
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:fedora="info:fedora/fedora-system:def/relations-external#">
  <rdf:Description rdf:about="info:fedora/coccc:2040">
    <fedora:HasAwesomeness>JON</fedora:HasAwesomeness>
    <fedora:HasTN rdf:resource="info:fedora/coccc:2030"/>
  </rdf:Description>
  <rdf:Description rdf:about="info:fedora/coccc:2033">
    <fedora:HasTN rdf:resource="info:fedora/coccc:2040"/>
  </rdf:Description>
  <rdf:Description rdf:about="info:fedora/coccc:2033/DSID">
    <fedora:HasTN rdf:resource="info:fedora/coccc:2040/DSID"/>
  </rdf:Description>
</rdf:RDF>
        """
        relationship = fedora_relationship()
        relationship.addRelationship('coccc:2040', 'HasAwesomeness', rels_object('JON',rels_object.LITERAL))
        relationship.addRelationship('coccc:2040', 'HasTN', rels_object('coccc:2030',rels_object.PID))
        relationship.addRelationship('coccc:2033', 'HasTN', rels_object('coccc:2040',rels_object.PID))
        relationship.addRelationship('coccc:2033/DSID', 'HasTN', rels_object('coccc:2040/DSID',rels_object.DSID))
        result_string = XmlHelper.mangle(relationship.toString())
        expected_string = XmlHelper.mangle(xmlStr)
        self.assertEqual(result_string, expected_string, 'Generated XML Incorrect')

    def test_get_relationships(self):
        xmlStr= """
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:fedora="info:fedora/fedora-system:def/relations-external#">
  <rdf:Description rdf:about="info:fedora/coccc:2040">
    <fedora:HasAwesomeness>JON</fedora:HasAwesomeness>
    <fedora:HasTN rdf:resource="info:fedora/coccc:2030"/>
  </rdf:Description>
  <rdf:Description rdf:about="info:fedora/coccc:2033">
    <fedora:HasTN rdf:resource="info:fedora/coccc:2040"/>
  </rdf:Description>
  <rdf:Description rdf:about="info:fedora/coccc:2033/DSID">
    <fedora:HasTN rdf:resource="info:fedora/coccc:2040/DSID"/>
  </rdf:Description>
</rdf:RDF>
        """
        relationship = fedora_relationship(xml=xmlStr)
        results = relationship.getRelationships(predicate = 'HasTN')

        self.assertEqual(len(results), 3, 'Too many relationships returned')
        self.assertEqual(results[0][0], "coccc:2040", "Subject incorrect")
        self.assertEqual(results[1][0], "coccc:2033", "Subject incorrect")
        self.assertEqual(results[2][0], "DSID", "Subject incorrect")

        self.assertEqual("%s" % results[0][1], "HasTN", "Predicate incorrect")
        self.assertEqual("%s" % results[1][1], "HasTN", "Predicate incorrect")
        self.assertEqual("%s" % results[2][1], "HasTN", "Predicate incorrect")

        self.assertEqual("%s" % results[0][2], "coccc:2030", "Object incorrect")
        self.assertEqual("%s" % results[1][2], "coccc:2040", "Object incorrect")
        self.assertEqual("%s" % results[2][2], "DSID", "Object incorrect")

    def test_purge_relationships(self):
        xmlStr1= """
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:fedora="info:fedora/fedora-system:def/relations-external#">
  <rdf:Description rdf:about="info:fedora/coccc:2040">
    <fedora:HasAwesomeness>JON</fedora:HasAwesomeness>
    <fedora:HasTN rdf:resource="info:fedora/coccc:2030"/>
  </rdf:Description>
  <rdf:Description rdf:about="info:fedora/coccc:2033">
    <fedora:HasTN rdf:resource="info:fedora/coccc:2040"/>
  </rdf:Description>
  <rdf:Description rdf:about="info:fedora/coccc:2033/DSID">
    <fedora:HasTN rdf:resource="info:fedora/coccc:2040/DSID"/>
  </rdf:Description>
</rdf:RDF>
        """

        xmlStr2= """
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:fedora="info:fedora/fedora-system:def/relations-external#">
  <rdf:Description rdf:about="info:fedora/coccc:2033">
    <fedora:HasTN rdf:resource="info:fedora/coccc:2040"/>
  </rdf:Description>
  <rdf:Description rdf:about="info:fedora/coccc:2033/DSID">
    <fedora:HasTN rdf:resource="info:fedora/coccc:2040/DSID"/>
  </rdf:Description>
</rdf:RDF>
        """
        relationship = fedora_relationship(xml=xmlStr1)
        relationship.purgeRelationships(subject = 'coccc:2040')
        result_string = XmlHelper.mangle(relationship.toString())
        expected_string = XmlHelper.mangle(xmlStr2)
        self.assertEqual(result_string, expected_string, 'Generated XML Incorrect')

if __name__ == '__main__':
    unittest.main()