'''
Created on May 5, 2011

@author
  William Panting
This file is meant to help with file manipulations/alterations.
'''
from pyPdf import PdfFileWriter, PdfFileReader
import logging, os
from . import xmlib
etree = xmlib.import_etree()

def appendPDFwithPDF(outFile,toAppend):
    '''
This function is meant to combine multiple pdf files, I'm not sure I like the pyPdf module's issues atm, hope it updates soon

@author
  William Panting

@param outFile
  a string representing the path of the file that is to be created/modified
@param toAppend
  a string representing the path of the file that is to be appended to the orgional file,
  or an ordered list of multiple strings representing files
@return bool
  true if successful false if not
'''
    pdfWriter=PdfFileWriter()
    
    #out file must not be a directory
    if os.path.isdir(outFile):
        logging.error('Input error: outFile cannot be a directory.')
        return False
    #if outfile is a file then it needs to be added to the output page by page just like the other pdfs
    elif os.path.isfile(outFile):
        #if toAppend is a string then make it into a list [outDir,toAppend]
        if isinstance(toAppend,str):
            toAppend=[outFile,toAppend]
        #if toAppend is a list prepend outDir to it
        elif isinstance(toAppend,list):
            toAppend.insert(0,outFile)

    #if toAppend is a string
    if isPDF(toAppend):
        toAppendReader=PdfFileReader(open(toAppend, "rb"))
        try:
            numPages=toAppendReader.getNumPages()
        except Exception: #this try catch handles where the pyPDF lib mistakenly thinks a pdf is encrypted, will not work with encryption 3,4
            toAppendReader.decrypt('')
            numPages=toAppendReader.getNumPages()
        #loop over pages adding them one by one
        pageCount=0
        while pageCount<numPages:
            pdfWriter.addPage(toAppendReader.getPage(pageCount))
            pageCount+=1
    #if toAppend is a list of paths
    elif isinstance(toAppend, list):
        for path in toAppend:
            #verify list as pdfs
            if isPDF(path)==False:
                logging.error('Error with input: '+str(path)+' --Each member of the list to append must be a valid pdf.')
                return False
            #loop over each page appending it
            toAppendReader=PdfFileReader(open(path, "rb"))
            try:
                numPages=toAppendReader.getNumPages()
            except Exception: #this try catch handles where the pyPDF lib mistakenly thinks a pdf is encrypted, will not work with encryption 3,4
                toAppendReader.decrypt('')
                numPages=toAppendReader.getNumPages()
            #loop over pages adding them one by one
            pageCount=0
            while pageCount<numPages:
                pdfWriter.addPage(toAppendReader.getPage(pageCount))
                pageCount+=1
    else:
        logging.error('Error with input: '+str(toAppend)+' --The input to Append must be a file path or list of file paths.')
        return False
    
    #write the concatenated file, must open for read write or if it exists or you get an exception in pyPdf
    if(os.path.lexists(outFile)):
        pdfStream = open(outFile, "r+b")
    else:
        pdfStream= open(outFile,'wb')
    pdfWriter.write(pdfStream)
    
    return True


def isPDF(file_path):
    '''
This function is a helper function that validates user input as a valid pdf file
but not realy it just checks the extension right now. 
@todo
  actualy check
@author 
  William Panting
@param file_path
  path to analyse for pdf-ness
@return bool
  true if the input is a path to a pdf false if not
'''
    if isinstance(file_path, str):
        if os.path.isfile(file_path) and file_path[file_path.rindex('.'):len(file_path)]=='.pdf':
            return True
    return False

def breakTEIOnPages(file_path, output_directory):
    '''
This function
@author
  William Panting
@param string file_path
'''
    if os.path.isfile(file_path) and (file_path.endswith('.xml') or file_path.endswith('.tei') or file_path.endswith('.TEI') or file_path.endswith('.XML')):
        TEIMilestone1 = etree.XSLT(etree.parse(os.path.join(os.path.dirname(__file__), '__resources/TEIMilestone1.xslt')))
        TEIMilestone2 = etree.XSLT(etree.parse(os.path.join(os.path.dirname(__file__), '__resources/TEIMilestone2.xslt')))
        TEIMilestone3 = etree.XSLT(etree.parse(os.path.join(os.path.dirname(__file__), '__resources/TEIMilestone3.xslt')))
        
        file_etree_object = etree.parse(file_path)
        try:
            intermediary_TEI = TEIMilestone1(file_etree_object)
         
            intermediary_TEI = TEIMilestone2(intermediary_TEI)
           
            intermediary_TEI = TEIMilestone3(intermediary_TEI)
        except Exception:
            print("%s" % Exception.args)
            print("%s" % Exception.message)
        else:
            print(intermediary_TEI)
        #print(intermediary_TEI)
        TEI_iterator = etree.iterparse(file_path, events=('start',))
        #TEI_iterator = etree.iterparse(file_path, events=('end',), tag='whateverAPageBreakIs')
        #go through file until eof
        for event, elem in TEI_iterator:
            #print(event)
            #print(elem)
            #go through file until page break
                #start a page with headers, opening tags etc.
                #add things into page as you traverse TEI file
            g=1+1    
            #close last page xml tags
            #save page into output_directory
        return True
    return False