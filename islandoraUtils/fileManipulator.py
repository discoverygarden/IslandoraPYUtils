'''
Created on May 5, 2011

@author: William Panting
This file is meant to help with file manipulations/alterations.
'''
from pyPdf import PdfFileWriter, PdfFileReader
import logging, os

def appendPDFwithPDF(outFile,toAppend):
    '''
This function is meant to combine multiple pdf files, I'm not sure I like the pyPdf module's issues atm, hope it updates soon

@author: William Panting

@param outFile: a string representing the path of the file that is to be created/modified
@param toAppend: a string representing the path of the file that is to be appended to the orgional file,
                 or an ordered list of multiple strings representing files
@return bool: true if successful false if not
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


def isPDF(input):
    '''
This function is a helper function that validates user input as a valid pdf file
@author William Panting
@param input: path to analyse for pdf-ness
@return bool: true if the input is a path to a pdf false if not
'''
    if isinstance(input, str):
        if os.path.isfile(input) and input[input.rindex('.'):len(input)]=='.pdf':
            return True
    return False
