'''
Created on May 5, 2011

@author: William Panting
This file is meant to help with file manipulations/alterations.
'''
from pyPdf import PdfFileWriter, PdfFileReader
import logging, os
'''
This function is meant to combine multiple pdf files

@author: William Panting

@param outFile: a string representing the path of the file that is to be created/modified
@param toAppend: a string representing the path of the file that is to be appended to the orgional file,
                 or an ordered list of multiple strings representing files
@return bool: true if successful false if not
'''
def appendPDFwithPDF(outFile,toAppend):
    pdfWriter=PdfFileWriter()
    
    #if toAppend is a string
    if isPDF(toAppend):
        toAppendReader=PdfFileReader(file(toAppend, "rb"))
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
            toAppendReader=PdfFileReader(file(path, "rb"))
            numPages=toAppendReader.getNumPages()
            #loop over pages adding them one by one
            pageCount=0
            while pageCount<numPages:
                pdfWriter.addPage(toAppendReader.getPage(pageCount))
                pageCount+=1
    else:
        logging.error('Error with input: '+str(toAppend)+' --The input to Append must be a file path or list of file paths.')
        return False
    
    #write the concatenated file
    pdfStream = file(outFile, "wb")
    pdfWriter.write(pdfStream)
    
    return True

'''
This function is a helper function that validates user input as a valid pdf file
@author William Panting
@param input: path to anylise for pdf'ness
@return bool: true if the input is a path to a pdf false if not
'''
def isPDF(input):
    if isinstance(input, str):
        if os.path.isfile(input) and input[input.rindex('.'):len(input)]=='.pdf':
            return True
    return False