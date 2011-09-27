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
This function will break a tei file into tei snipits for each page
This may not work with tei files not from Hamilton
It explodes on non expanded pb tags. it will likely break on expanded ones
@author
  William Panting
@param string file_path
@param string output_directory
@todo
  make sure to get the last page
@todo
  start not repeating the DNR list
'''
    if os.path.isfile(file_path) and (file_path.endswith('.xml') or file_path.endswith('.tei') or file_path.endswith('.TEI') or file_path.endswith('.XML')):
        
        #init
        TEI_iterator = etree.iterparse(file_path, events=('start', 'end'))
        element_tracker = list()
        page_element_tracker = list()
        first_page_sentinal = True
        root_text_sentinal = 0 #to be considered true only if ==1
        page_number = 0
        pb_parent = etree.Element
        DoNotRepeat_list = list()
        #go through file until eof
        for event, elem in TEI_iterator:
            #consider coping headers
            #if the element is root then create current_page root
            if first_page_sentinal == True:
                root = etree.Element(elem.tag)
                xmlib.copy_element_attributes(elem, root)
                current_page = etree.ElementTree(root)
                first_page_sentinal = False
            
            if event == 'start':
                #handles getting root text as soon as it is available
                if root_text_sentinal == 1:
                    last_elem = element_tracker.pop()
                    current_page_root = current_page.getroot()
                    current_page_root.text = last_elem.text
                    element_tracker.append(last_elem)
                    root_text_sentinal+=1
                elif root_text_sentinal == 0:
                    root_text_sentinal+=1
                    
                '''on a page break open iterate through everything on on the element stack 
                   grab the textual content posting it to the current page's elements
                   then print it to file
                '''
                if elem.tag.endswith('}pb'):
                    #populate the .text of the incomplete elements of the current page
                    #if they were not populated in a previous page
                    #todo: FIX !!!
                    for element in element_tracker:#only get text if it isn't on a page already
                        if DoNotRepeat_list.count(element) == 0:
                            page_element = page_element_tracker[element_tracker.index(element)]
                            page_element.text = element.text
                        
                    DoNotRepeat_list = list()#clear so we aren't appending each pb
                    #create the next page parser
                    root_element_sentinal = True
                    for element in page_element_tracker:
                        if root_element_sentinal == True:
                            root = etree.Element(element.tag)
                            xmlib.copy_element_attributes(element, root)
                            next_page = etree.ElementTree(root)
                            root_element_sentinal = False
                            element_copy = root
                        else:
                            element_copy = etree.Element(element.tag)
                            xmlib.copy_element_attributes(element, element_copy)
                            last_element = DoNotRepeat_list.pop()
                            last_element.append(element_copy)
                            DoNotRepeat_list.append(last_element)
                        DoNotRepeat_list.append(element_copy)
                    
                    
                    #print to file, but don't print the 'first page' it's metadata
                    if page_number > 0:
                        output_path = os.path.join(output_directory,  os.path.basename(file_path)[:-4] + '_page_' + str(page_number) + '.xml')
                        current_page.write(output_path, encoding = "UTF-8")
                    
                    #switch to new page
                    page_number += 1
                    current_page = next_page
                    page_element_tracker = DoNotRepeat_list
                    DoNotRepeat_list = list(element_tracker)
                else:#push tag into new page
                    #construct element
                    page_elem = etree.Element(elem.tag)
                    xmlib.copy_element_attributes(elem, page_elem)
                    #put element on the current page
                    if page_element_tracker:
                        last_page_elem = page_element_tracker.pop()
                        last_page_elem.append(page_elem)
                        page_element_tracker.append(last_page_elem)
                    else:
                        last_page_elem = current_page.getroot()
                        last_page_elem.append(page_elem)
                        
                element_tracker.append(elem)
                page_element_tracker.append(page_elem)
                #push tag with attributes onto the current page
                    
            if event == 'end':
                #if close of file print to page
                if elem.tag.endswith('}TEI'):
                    output_path = os.path.join(output_directory,  os.path.basename(file_path)[:-4] + '_page_' + str(page_number) + '.xml')
                    current_page.write(output_path, encoding = "UTF-8")
                else:
                    #pop the stack to work on it
                    last_elem = element_tracker.pop()
                    last_page_elem = page_element_tracker.pop()
                    
                    #push preceding text onto current page
                    last_page_elem.tail = last_elem.tail #gets closing text
                    #only get text if it isn't on a page already
                    if DoNotRepeat_list.count(last_elem) == 0:
                        last_page_elem.text = last_elem.text #gets opening text
        return True
    return False