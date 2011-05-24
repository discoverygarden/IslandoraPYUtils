'''
Created on Apr 5, 2011

@author: William Panting
@dependencies: Kakadu, ImageMagick, ABBYY CLI, Lame, SWFTools, FFmpeg

This is a Library that will make file conversions and manipulations like OCR using Python easier. 
Primarily it will use Kakadu and ABBYY
but it will fall back on ImageMagick if Kakadu fails and for some conversions Kakadu does not support.

Used scripts created by Jonathan Green as the starting piont.
Please make sure that the output directory already exists.
Note that the extra args variables are here to facilitate debugging if there are ever version issues.

TODO: add video support
TODO: add open office word doc conversions
TODO: make recursive option
TODO: explore handling output directory creation
TODO: explore more input file type checking
TODO: explore better conversion options
TODO: explore more backup solutions
'''
import logging, subprocess, os, xmlib
from lxml import etree

def tif_to_jp2(inPath,outPath,kakaduOpts=None,imageMagicOpts=None,*extraArgs):
    '''
Converts tiff to jp2

@param inPath: source file or dir
@param outPath: destination file or dir
@param kakaduOpts: a list of options or a string 'default'
@param imageMagicOpts: a list of options or a string 'default'  

@return bool: true if successful [completion not conversion] false if not
'''
    
    #error checking, does not take TN
    if checkStd(inPath,outPath,extraArgs,kakaduOpts,imageMagicOpts)==False:
        return False
    if kakaduOpts=='TN' or imageMagicOpts=='TN':
        logging.error('This function tif_to_jp2 does not accept the \'TN\' keyword')
        return False
    
    #determine the output directory for the tempfile and for if there are multiple output files due to a directory batch
    #put directory not created error handle here'''
    if os.path.isdir(outPath)==False: #outPath is a file path
        outDirectory,fileNameOut=os.path.split(outPath)
        fileList=(fileNameOut)
    else:#is a driectory
        outDirectory=outPath
    tmpFilePath=os.path.join(outDirectory,'uncompressed.tiff')
    #create list of files to be converted
    if os.path.isdir(inPath)==False:
        inDirectory, fileListStr=os.path.split(inPath)
        fileList=[fileListStr]
    else:
        inDirectory=inPath
        fileList=os.listdir(inPath)#get files in the dir
        for path in os.listdir(inPath):
            pathLength=len(path)
            #remove non tiff entries
            if path[(pathLength-4):pathLength]!='.tif' and path[(pathLength-5):pathLength]!='.tiff' :
                fileList.remove(path)
    
    
    for fileName in fileList:
        
        #if fileNameOut was not in outPath make one up
        if os.path.isdir(outPath)==True:
            fileNameOut=fileName[0:fileName.rindex('.')]+'.jp2'
        filePathIn=os.path.join(inDirectory,fileName)
        filePathOut=os.path.join(outDirectory,fileNameOut)
        #use convert because of lack of kakadu license means we can't convert a compressed tif
        r = subprocess.call(["convert", filePathIn, '+compress', tmpFilePath])
        if r != 0:
            logging.warning('JP2 creation failed (convert return code:%d for file input %s).' % ( r, filePathIn))
            
            
        #prep Kakadu call
        if kakaduOpts!='default':
            kakaduCall=("kdu_compress", "-i", tmpFilePath,"-o", filePathOut)
            kakaduCall.extend(kakaduOpts)
            
        else:
            kakaduCall=["kdu_compress", "-i", tmpFilePath,\
          "-o", filePathOut,\
          "-rate", "0.5", "Clayers=1", "Clevels=7",\
          "Cprecincts={256,256},{256,256},{256,256},{128,128},{128,128},{64,64},{64,64},{32,32},{16,16}",\
          "Corder=RPCL", "ORGgen_plt=yes", "ORGtparts=R", "Cblk={32,32}", "Cuse_sop=yes"]      
        #make Kakadu call
        r = subprocess.call(kakaduCall)
    
       
        #if Kakadu fails [happens on certain color pellets] use less powerful ImageMagicK on original file
        if r != 0:
            logging.warning('JP2 creation failed. Trying alternative (kdu_compress return code:%d).' % (r) )
           
            #prep image magic call
            if imageMagicOpts!='default':
                imageMagicCall=("convert", filePathIn)
                imageMagicCall.extend(imageMagicOpts)
                imageMagicCall.append(filePathOut)
            else:
                imageMagicCall=["convert", filePathIn, '-compress', 'JPEG2000', '-quality', '50%', filePathOut]
            #make image magic call  
            r = subprocess.call(imageMagicCall)
            if r != 0:
                logging.warning('JP2 creation failed (convert return code:%d for file input %s).' % ( r, filePathIn))
    
        if r == 0:
            logging.info('File converted: %s'% (filePathOut))
        
        #kill the temp file if it exists
        if os.path.exists(tmpFilePath):
            os.remove(tmpFilePath)
        
    return True


def tif_OCR(inPath,outPath,fileTypeOpts,inputOpts=None,*extraArgs):
    '''
ABBYY OCR CLI Command Line Tool support

@param: inPath: source file or dir
@param: outPath: destination file or dir
@param: inputOpts: the ABBYY command line options not associated with a specific file output tyep, can be None
@param: fileTypeOpts: 1. a dictionary where the key is a file output type and the vale is a string 'default' or list of options, or 2. a string 'default'

@return bool: true if successful [completion not conversion] false if not

TODO: make default output options for all output file types 
'''
        #error checking, does not take TN
    if checkPaths(inPath,outPath)==False:
        return False
    if fileTypeOpts=='TN' or inputOpts=='TN':
        logging.error('This function tif_to_jp2 does not accept the \'TN\' keyword')
        return False
    #special dictionary error checking
    if isinstance(fileTypeOpts, dict)==False and fileTypeOpts!='default':
        logging.error('The fileTypeOpts must be a dictionary or the keyword \'default\'.' )
        return False
      
    #prevents the script from attempting to write multiple output files to one output file path
    if os.path.isdir(inPath)==True and os.path.isdir(outPath)!=True:
        logging.error('If the input path is a directory, so must be the output path.')
        return False
    if len(fileTypeOpts)>1 and fileTypeOpts!='default' and os.path.isdir(outPath)!=True:
        logging.error('If there is to be more than one output file then the output path must be a directory.')
        return False
        
    #determine the output directory if there are multiple output files due to a directory batch
    #put directory not created error handling here'''
    if os.path.isdir(outPath)==False:
        outDirectory,fileNameOut=os.path.split(outPath)
        fileList=(fileNameOut)
    else:#is a driectory
        outDirectory=outPath
    
    #create list of files to be converted
    if os.path.isdir(inPath)==False:
        inDirectory, fileListStr=os.path.split(inPath)
        fileList=[fileListStr]
    else:
        inDirectory=inPath
        fileList=os.listdir(inPath)#get files in the dir
        for path in fileList:
            pathLength=len(path)
            #remove non tiff entries
            if path[(pathLength-4):pathLength]!='.tif' and path[(pathLength-5):pathLength]!='.tiff' :
                fileList.remove(path)
        
    for fileName in fileList:
        #some useful vars
        absPathFileIn=os.path.join(inDirectory,fileName)
        absPathFileOutNoExt=os.path.join(outDirectory,fileName[0:fileName.rindex('.')])
        
        #reset the ABBYY call
        ABBYY_Call=['CLI']
        #input opts and input file
        if inputOpts!='default' and inputOpts!=None:
            ABBYY_Call.extend(inputOpts)
        ABBYY_Call.extend(('-if',absPathFileIn))     

        #determine output file extension, and input check
        for outputType,outputOpts in fileTypeOpts.iteritems():
            if outputType=='PDF':
                extension='.pdf'
                defaultOutPutOpts=('-pem','ImageOnText','-pfq','75')
            elif outputType=='HTML':
                extension='.html'
                defaultOutPutOpts=()
            elif outputType=='RTF':
                extension='.rtf'
                defaultOutPutOpts=()
            elif outputType=='DBF':
                extension='.dbf'
                defaultOutPutOpts=()
            elif outputType=='XML':
                extension='.xml'
                defaultOutPutOpts=()
            elif outputType=='Text':
                extension='.txt'
                defaultOutPutOpts=('-tel','-tpb','-tet','UTF8')
            elif outputType=='XLS':
                extension='.xls'
                defaultOutPutOpts=()
            else:
                logging.error('Incorrect output type specified for ABBYY CLI.')
                return 1
            #append this round of output info
            ABBYY_Call.extend(('-f',outputType))
            if outputOpts!='default':
                ABBYY_Call.extend(fileTypeOpts[outputType])
            else:
                ABBYY_Call.extend(defaultOutPutOpts)
            #append output file for this round
            ABBYY_Call.extend(('-of',absPathFileOutNoExt+extension))
        
        #make ABBYYcall
        r = subprocess.call(ABBYY_Call)
        if r != 0:
            logging.warning('JP2 creation failed (ABBYY CLI return code:%d).' % ( r))
        if r == 0:
            logging.info('File OCR\'d: %s'% (absPathFileIn))
    return True


def tif_to_jpg(inPath,outPath, imageMagicOpts,*extraArgs):
    '''
This function will use ImageMagick to convert tifs to jpgs
@param: inPath: source file or dir
@param: outPath: destination file or dir
@param imageMagicOpts: can be 'default' 'TN' or a list of options to use

@return bool: true if successful false if not
'''
    #error checking
    if checkStd(inPath,outPath,extraArgs,imageMagicOpts)==False:
        return False
    
    #determine the output directory for the tempfile and for if there are multiple output files due to a directory batch
    #put directory not created error handle here'''
    if os.path.isdir(outPath)==False: #outPath is a file path
        outDirectory,fileNameOut=os.path.split(outPath)
        fileList=(fileNameOut)
    else:#is a driectory
        outDirectory=outPath
    #create list of files to be converted
    if os.path.isdir(inPath)==False:
        inDirectory, fileListStr=os.path.split(inPath)
        fileList=[fileListStr]
    else:
        inDirectory=inPath
        fileList=os.listdir(inPath)#get files in the dir
        for path in os.listdir(inPath):
            pathLength=len(path)
            #remove non tiff entries
            if path[(pathLength-4):pathLength]!='.tif' and path[(pathLength-5):pathLength]!='.tiff' :
                fileList.remove(path)
    
    
    for fileName in fileList:
        
        #if fileNameOut was not in outPath make one up
        if os.path.isdir(outPath)==True:
            fileNameOut=fileName[0:fileName.rindex('.')]+'.jpg'
        filePathIn=os.path.join(inDirectory,fileName)
        filePathOut=os.path.join(outDirectory,fileNameOut)
        
        #create image magick call
        if imageMagicOpts=='default':
            imageMagicCall=["convert", filePathIn, '-compress', 'JPEG', '-quality', '50%', filePathOut]
        elif imageMagicOpts=='TN':
            imageMagicCall=["convert", filePathIn, '-compress', 'JPEG', "-thumbnail", "85x110!", "-gravity", "center", "-extent", "85x110", filePathOut]
        else:
            imageMagicCall=["convert",filePathIn]
            imageMagicCall.extend(imageMagicOpts)
            imageMagicCall.append(filePathOut)
        
        #make image magic call  
        r = subprocess.call(imageMagicCall)
        if r != 0:
            logging.warning('JPG creation failed (convert return code:%d for file input %s).' % ( r, filePathIn))
        if r == 0:
            logging.info('File converted: %s'% (filePathOut))
    return True


def pdf_to_swf(inPath,outPath,swfToolsOpts,*extraArgs):
    '''
This function will use swftools to convert pdf files to swfs
@param: inPath: source file or dir
@param: outPath: destination file or dir
@param swfToolsOpts: options to be applied to the conversion can be 'default'

@return bool: true if successful [completion not conversion] false if not
'''
#error checking
    if checkStd(inPath,outPath,extraArgs,swfToolsOpts)==False:
        return False
    if swfToolsOpts=='TN':
        logging.error('This function pdf_to_swf does not accept the \'TN\' keyword')
        return False
    
    #determine the output directory for the tempfile and for if there are multiple output files due to a directory batch
    #put directory not created error handle here'''
    if os.path.isdir(outPath)==False: #outPath is a file path
        outDirectory,fileNameOut=os.path.split(outPath)
        fileList=(fileNameOut)
    else:#is a driectory
        outDirectory=outPath
    #create list of files to be converted
    if os.path.isdir(inPath)==False:
        inDirectory, fileListStr=os.path.split(inPath)
        fileList=[fileListStr]
    else:
        inDirectory=inPath
        fileList=os.listdir(inPath)#get files in the dir
        for path in os.listdir(inPath):
            pathLength=len(path)
            #remove non pdf entries
            if path[(pathLength-4):pathLength]!='.pdf':
                fileList.remove(path)
    
    
    for fileName in fileList:
        
        #if fileNameOut was not in outPath make one up
        if os.path.isdir(outPath)==True:
            fileNameOut=fileName[0:fileName.rindex('.')]+'.pdf'
        filePathIn=os.path.join(inDirectory,fileName)
        filePathOut=os.path.join(outDirectory,fileNameOut)
        
        #create image magick call
        if swfToolsOpts=='default':
            swfToolsCall=["pdf2swf", filePathIn, '-o', filePathOut,'-T 9', '-f', '-t', '-s', 'storeallcharacters', '-G']
        else:
            swfToolsCall=["pdf2swf",filePathIn,'-o', filePathOut]
            swfToolsCall.extend(swfToolsOpts)
        #make the system call  
        r = subprocess.call(swfToolsCall)
        #move to bitmap because swftools fails on very large files otherwise
        if swfToolsOpts=='default' and r!=0:
            logging.warning('PDF creation failed (SWFTools return code:%d for file input %s: Trying alternative.).' % ( r, filePathIn))
            swfToolsCall=["pdf2swf", filePathIn, '-o', filePathOut,'-T 9', '-f', '-t', '-s', 'storeallcharacters', '-G', '-s', 'poly2bitmap']
            r=subprocess.call(swfToolsCall)
        
        if r != 0:
            logging.warning('PDF creation failed (SWFTools return code:%d for file input %s).' % ( r, filePathIn))
        if r == 0:
            logging.info('File converted: %s'% (filePathOut))
    return True


def wav_to_ogg(inPath,outPath,FFmpegOpts,*extraArgs):
    '''
This function will use FFmpeg to turn a wav file into an ogg file
@param: inPath: source file or dir
@param: outPath: destination file or dir
@param FFmpegOpts: options to be applied to the conversion can be 'default'

@return bool: true if successful [completion not conversion] false if not
'''
#error checking
    if checkStd(inPath,outPath,extraArgs,FFmpegOpts)==False:
        return False
    if FFmpegOpts=='TN':
        logging.error('This function wav_to_ogg does not accept the \'TN\' keyword')
        return False
    
    #determine the output directory for the tempfile and for if there are multiple output files due to a directory batch
    #put directory not created error handle here'''
    if os.path.isdir(outPath)==False: #outPath is a file path
        outDirectory,fileNameOut=os.path.split(outPath)
        fileList=(fileNameOut)
    else:#is a driectory
        outDirectory=outPath
    #create list of files to be converted
    if os.path.isdir(inPath)==False:
        inDirectory, fileListStr=os.path.split(inPath)
        fileList=[fileListStr]
    else:
        inDirectory=inPath
        fileList=os.listdir(inPath)#get files in the dir
        for path in os.listdir(inPath):
            pathLength=len(path)
            #remove non applicable file entries
            if path[(pathLength-4):pathLength]!='.wav':
                fileList.remove(path)
    
    
    for fileName in fileList:
        
        #if fileNameOut was not in outPath make one up
        if os.path.isdir(outPath)==True:
            fileNameOut=fileName[0:fileName.rindex('.')]+'.ogg'
        filePathIn=os.path.join(inDirectory,fileName)
        filePathOut=os.path.join(outDirectory,fileNameOut)
        
        #create the system call
        if FFmpegOpts=='default':
            FFmpegCall=['ffmpeg', '-i', filePathIn, '-acodec', 'libvorbis', '-ab', '48k', filePathOut]
        else:
            FFmpegCall=['ffmpeg', '-i', filePathIn]
            FFmpegCall.extend(FFmpegOpts)
            FFmpegCall.append(filePathOut)
        
        #make the system call  
        r = subprocess.call(FFmpegCall)
        if r != 0:
            logging.warning('ogg creation failed (FFmpeg return code:%d for file input %s).' % ( r, filePathIn))
        if r == 0:
            logging.info('File converted: %s'% (filePathOut))
    return True


def wav_to_mp3(inPath,outPath,lameOpts,*extraArgs):
    '''
This function uses the lame tool to make wav files into mp3 files
@param: inPath: source file or dir
@param: outPath: destination file or dir
@param lameOpts: options to be applied to the conversion can be 'default'

@return bool: true if successful [completion not conversion] false if not
'''
#error checking
    if checkStd(inPath,outPath,extraArgs,lameOpts)==False:
        return False
    if lameOpts=='TN':
        logging.error('This function wav_to_mp3 does not accept the \'TN\' keyword')
        return False
    
    #determine the output directory for the tempfile and for if there are multiple output files due to a directory batch
    #put directory not created error handle here'''
    if os.path.isdir(outPath)==False: #outPath is a file path
        outDirectory,fileNameOut=os.path.split(outPath)
        fileList=(fileNameOut)
    else:#is a driectory
        outDirectory=outPath
    #create list of files to be converted
    if os.path.isdir(inPath)==False:
        inDirectory, fileListStr=os.path.split(inPath)
        fileList=[fileListStr]
    else:
        inDirectory=inPath
        fileList=os.listdir(inPath)#get files in the dir
        for path in os.listdir(inPath):
            pathLength=len(path)
            #remove non applicable file entries
            if path[(pathLength-4):pathLength]!='.wav':
                fileList.remove(path)
    
    for fileName in fileList:
        
        #if fileNameOut was not in outPath make one up
        if os.path.isdir(outPath)==True:
            fileNameOut=fileName[0:fileName.rindex('.')]+'.mp3'
        filePathIn=os.path.join(inDirectory,fileName)
        filePathOut=os.path.join(outDirectory,fileNameOut)
        
        #create the system call
        if lameOpts=='default':
            lameCall=['lame', '-mm', '--cbr', '-b48', filePathIn, filePathOut]
        else:
            lameCall=['lame']
            lameCall.extend(lameOpts)
            lameCall.extend([filePathIn, filePathOut])
        
        #make the system call  
        r = subprocess.call(lameCall)
        if r != 0:
            logging.warning('mp3 creation failed (lame return code:%d for file input %s).' % ( r, filePathIn))
        if r == 0:
            logging.info('File converted: %s'% (filePathOut))
    return True


def pdf_to_jpg(inPath,outPath,imageMagicOpts,*extraArgs):
    '''
This function will use ImageMagick to convert tifs to jpgs
@param: inPath: source file or dir
@param: outPath: destination file or dir
@param imageMagicOpts: can be 'default' 'TN' or a list of options to use

@return bool: true if successful [completion not conversion] false if not
'''
    #error checking
    if checkStd(inPath,outPath,extraArgs,imageMagicOpts)==False:
        return False
    
    #determine the output directory for the tempfile and for if there are multiple output files due to a directory batch
    #put directory not created error handle here'''
    if os.path.isdir(outPath)==False: #outPath is a file path
        outDirectory,fileNameOut=os.path.split(outPath)
        fileList=(fileNameOut)
    else:#is a driectory
        outDirectory=outPath
    #create list of files to be converted
    if os.path.isdir(inPath)==False:
        inDirectory, fileListStr=os.path.split(inPath)
        fileList=[fileListStr]
    else:
        inDirectory=inPath
        fileList=os.listdir(inPath)#get files in the dir
        for path in os.listdir(inPath):
            pathLength=len(path)
            #remove non tiff entries
            if path[(pathLength-4):pathLength]!='.tif' and path[(pathLength-5):pathLength]!='.tiff' :
                fileList.remove(path)
    
    
    for fileName in fileList:
        
        #if fileNameOut was not in outPath make one up
        if os.path.isdir(outPath)==True:
            fileNameOut=fileName[0:fileName.rindex('.')]+'.jpg'
        filePathIn=os.path.join(inDirectory,fileName)
        filePathOut=os.path.join(outDirectory,fileNameOut)
        
        #create image magick call
        if imageMagicOpts=='default':
            imageMagicCall=["convert", filePathIn, '-compress', 'JPEG', '-quality', '50%', filePathOut]
        elif imageMagicOpts=='TN':
            imageMagicCall=["convert", filePathIn, '-compress', 'JPEG', "-thumbnail", "85x110!", "-gravity", "center", "-extent", "85x110", filePathOut]
        else:
            imageMagicCall=["convert",filePathIn]
            imageMagicCall.extend(imageMagicOpts)
            imageMagicCall.append(filePathOut)
        
        #make image magic call  
        r = subprocess.call(imageMagicCall)
        if r != 0:
            logging.warning('JPG creation failed (convert return code:%d for file input %s).' % ( r, filePathIn))
        if r == 0:
            logging.info('File converted: %s'% (filePathOut))
    return True

def exif_to_xml(inPath, outPath, *extraArgs):
    '''
    This function will extract the entire exif from an image and send it to an xml file, also for full directories
    @param input: file or directory to pipe from
    @param output: file or directory to pipe to
    @param extList (extraArgs[0]): list of file extensions to perform operations on, only needs to be provided with inPath is a directory
    @return bool: true on completion of funciton false on cought error
    TODO: add options
    '''
    #if it exists extract the extList var from extraArgs
    if len(extraArgs)>0:
        extList=extraArgs[0]
        extraArgs=extraArgs[1:len(extraArgs)]
        if isinstance(extList, list)==False:
            logging.error("The extension List must be a list not:"+str(extList))
            return False
    #standard error checking
    if checkStd(inPath,outPath,extraArgs)==False:
        return False
    #determine the output directory for the tempfile and for if there are multiple output files due to a directory batch
    #put directory not created error handle here'''
    if os.path.isdir(outPath)==False: #outPath is a file path
        outDirectory,fileNameOut=os.path.split(outPath)
        fileList=(fileNameOut)
    else:#is a driectory
        outDirectory=outPath
    #create list of files to be converted
    if os.path.isdir(inPath)==False:
        inDirectory, fileListStr=os.path.split(inPath)
        fileList=[fileListStr]
    else:
        inDirectory=inPath
        fileList=os.listdir(inPath)#get files in the dir
        for path in os.listdir(inPath):
            pathLength=len(path)
            #remove files that do not have an indicated extension from the list to work on
            for ext in extList:
                #use of rfind is because I don't want the ValueError thrown from rindex on failure to find the substr
                if path.rfind(ext)==-1 or path.rfind(ext)!=(pathLength-len(ext)):
                    fileList.remove(path)
                    print("removing path: "+path)
    
    for fileName in fileList:
        
        #if fileNameOut was not in outPath make one up
        if os.path.isdir(outPath)==True:
            fileNameOut=fileName[0:fileName.rindex('.')]+'.xml'
        filePathIn=os.path.join(inDirectory,fileName)
        filePathOut=os.path.join(outDirectory,fileNameOut)
        
        #create exiftool call
        exiftoolCall=['exiftool','-X',filePathIn]
        
        #make exiftool call  (using the Popen constructor because we need to do further work with the obj)
        r = subprocess.Popen(exiftoolCall,stdout=subprocess.PIPE)
        #grab exiftool output
        exif_value = r.communicate()[0]
        #put exiftool output in the file
        rFile=open(filePathOut,'w')
        rFile.write(exif_value)
        
        if r.poll() != 0:
            logging.warning('EXIF XML creation failed (convert return code:%d for file input %s).' % ( r, filePathIn))
        if r.poll() == 0:
            logging.info('File converted: %s'% (filePathOut))
    
    
    return True

def mods_to_solr(inPath, outPath, *extraArgs):
    '''
This function will take a MODS xml file and transform it into a SOLR xml file.

@param inPath: source file or dir
@param outPath: destination file or dir

@return bool: True on successful completion of function False on errors
'''
    #error checking
    if checkStd(inPath,outPath,extraArgs)==False:
        return False
    #set up the translator
    mods_to_solr=r'''<?xml version="1.0" encoding="UTF-8"?>
<!--
 * Copyright 2007, The Digital Library Federation, All Rights Reserved
 *
 * Permission is hereby granted, free of charge, to any person obtaining
 * a copy of this software and associated documentation files (the
 * "Software"), to deal in the Software without restriction, including
 * without limitation the rights to use, copy, modify, merge, publish,
 * distribute, sublicense, and/or sell copies of the Software, and to
 * permit persons to whom the Software is furnished to do so, subject
 * to the following conditions:
 *
 * The above copyright notice and this permission notice shall be
 * included in all copies or substantial portions of the Software.

 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
 * IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
 * CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
 * TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
 * SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
-->

<xsl:stylesheet version="1.0" 
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:xlink="http://www.w3.org/1999/xlink"
    xmlns:m="http://www.loc.gov/mods/v3">
    
    <xsl:template match="/">
    <xsl:apply-templates/>
    </xsl:template>

    <xsl:template match="m:mods">
    <xsl:variable name="form" select="m:physicalDescription/m:form"/>
    <xsl:variable name="rform" select="m:physicalDescription/m:reformattingQuality"/>
    <xsl:variable name="intm" select="m:physicalDescription/m:internetMediaType"/>
    <xsl:variable name="extent" select="m:physicalDescription/m:extent"/>
    <xsl:variable name="dorigin" select="m:physicalDescription/m:digitalOrigin"/>
    <xsl:variable name="note" select="m:note"/>
    <xsl:variable name="topic" select="m:subject/m:topic"/>
    <xsl:variable name="geo" select="m:subject/m:geographic"/>
    <xsl:variable name="time" select="m:subject/m:temporal"/>
    <xsl:variable name="hierarchic" select="m:subject/m:hierarchicalGeographic"/>
    <xsl:variable name="subname" select="m:subject/m:name"/>

    <xsl:element name="add">
    <xsl:element name="doc">

    <!-- SetSpec is handled twice, once for regular indexing and once for faceting,
         The setSpec will be broken up into individual elements by the java processing
         -->
         
    <!-- set_spec is handled up above -->
    
    <!-- we only want one title sort element -->
    <xsl:if test="m:titleInfo/m:title">
      <xsl:if test="position() = 1">
      <xsl:element name="field">
              <xsl:attribute name="name">title_sort_s</xsl:attribute>
              <xsl:value-of select="m:titleInfo/m:title"/>
          </xsl:element>
      </xsl:if>
    </xsl:if>
    <xsl:if test="m:identifier[@type='pid']">
      <xsl:if test="position() = 1">
        <xsl:element name="field">
          <xsl:attribute name="name">id</xsl:attribute>
          <xsl:value-of select="m:identifier[@type='pid']"/>
        </xsl:element>
      </xsl:if>
    </xsl:if>
  
    <!-- identifier -->
    <xsl:apply-templates select="m:identifier"/>
  
    <!-- titleInfo -->
    <xsl:apply-templates select="m:titleInfo"/>
    
    <!-- name -->
    <xsl:apply-templates select="m:name"/>

    <!-- subject -->
    <xsl:apply-templates select="m:subject"/>

    <!-- typeOfResource -->
    <xsl:apply-templates select="m:typeOfResource"/>
      
    <!-- genre -->
    <xsl:if test="m:genre">
    <xsl:element name="field"><xsl:attribute name="name">genre_t</xsl:attribute>
      <xsl:for-each select="m:genre">
        <xsl:if test=". != ''">
          <xsl:if test="position() != 1">
        <xsl:text>; </xsl:text>
          </xsl:if>
          <xsl:value-of select="."/>
        </xsl:if>
      </xsl:for-each>
    </xsl:element>
    
        <xsl:for-each select="m:genre">
            <xsl:element name="field"><xsl:attribute name="name">genre_facet</xsl:attribute>
        <xsl:value-of select="normalize-space(.)"/>
        </xsl:element>
        </xsl:for-each>
    </xsl:if>
    
    <!-- collection -->
    <xsl:for-each select="m:relatedItem/m:titleInfo[@authority='dlfaqcoll']/m:title">
        <xsl:element name="field"><xsl:attribute name="name">collection_facet</xsl:attribute>
        <xsl:value-of select="normalize-space(.)"/>
    </xsl:element>
    </xsl:for-each>
    
    <!-- originInfo -->   
    <xsl:apply-templates select="m:originInfo"/>
      
    <!-- language -->   
    <xsl:if test="m:language/m:languageTerm[@type='text']">
    <xsl:element name="field"><xsl:attribute name="name">language_t</xsl:attribute>
      <xsl:for-each select="m:language/m:languageTerm[@type='text']">
        <xsl:if test =". != ''">
          <xsl:if test = "position() != 1">
        <xsl:text>; </xsl:text>
          </xsl:if>
          <xsl:value-of select="."/>
        </xsl:if>
      </xsl:for-each>
    </xsl:element>        
    <xsl:for-each select="m:language/m:languageTerm[@type='text']">
      <xsl:element name="field"><xsl:attribute name="name">language_facet</xsl:attribute>
        <xsl:value-of select="normalize-space(.)"/>
      </xsl:element>        
    </xsl:for-each>
    </xsl:if>
      
    <!-- physicalDescription -->
    <xsl:if test="$form or $rform or $intm or $extent or $dorigin">
    <xsl:apply-templates select="m:physicalDescription"/>
    </xsl:if>
      
    <!-- abstract -->
    <xsl:apply-templates select="m:abstract"/>
    
    <!-- tableOfContents -->
    <xsl:apply-templates select="m:tableOfContents"/>
      
    <!-- targetAudience -->
    <xsl:apply-templates select="m:targetAudience"/>
      
    <!-- note -->
    <xsl:if test="$note">
    <xsl:for-each select="m:note">
        <xsl:if test=". != ''">
          <xsl:element name="field"><xsl:attribute name="name">note_t</xsl:attribute>
        <xsl:value-of select="."/>
          </xsl:element>
        </xsl:if>
    </xsl:for-each> 
    </xsl:if>
 
    <!-- relatedItem -->
    <xsl:apply-templates select="m:relatedItem"/>
    
    <!-- location --> 
    <xsl:apply-templates select="m:location">
    </xsl:apply-templates>
    
    <!-- accessCondition -->
    <xsl:apply-templates select="m:accessCondition"/>

  </xsl:element>
  </xsl:element>
</xsl:template>

<xsl:template match="m:titleInfo">
  <xsl:variable name="nsort" select="m:nonSort"/>      
  <xsl:variable name="titl" select="m:title"/>
  <xsl:variable name="subt" select="m:subTitle"/>
  <xsl:variable name="partname" select="m:partName"/>
  <xsl:variable name="partNumber" select="m:partnum"/>
      
  <xsl:choose>
    <xsl:when test="@type = 'alternative' or m:title/@type = 'alternative'">
      <xsl:element name="field">
    <xsl:attribute name="name"><xsl:text>alt_title_t</xsl:text></xsl:attribute>
    <xsl:value-of select="m:title"/>
      </xsl:element>
    </xsl:when>
    <xsl:when test="@type = 'uniform' or m:title/@type = 'uniform'">
      <xsl:element name="field">
    <xsl:attribute name="name"><xsl:text>uni_title_t</xsl:text></xsl:attribute>
    <xsl:value-of select="m:title"/>
      </xsl:element>
    </xsl:when>
    <xsl:when test="@type = 'abbreviated' or m:title/@type = 'abbreviated'">
      <xsl:element name="field">
    <xsl:attribute name="name"><xsl:text>abbr_title_t</xsl:text></xsl:attribute>
    <xsl:value-of select="m:title"/>
      </xsl:element>
    </xsl:when>
    <xsl:when test="@type = 'translated' or m:title/@type = 'translated'">
      <xsl:element name="field">
    <xsl:attribute name="name"><xsl:text>trans_title_t</xsl:text></xsl:attribute>
    <xsl:value-of select="m:title"/>
      </xsl:element>
    </xsl:when>
    <xsl:otherwise>
      <xsl:element name="field">
    <xsl:attribute name="name">title_t</xsl:attribute>
    <!-- including nsort because this is keyword search spec -->
    <xsl:value-of select="$nsort"/>
    <xsl:value-of select="$titl"/>
    
    <xsl:for-each select="m:subTitle">
      <xsl:if test=". != ''">
        <xsl:if test="position()=1 and $titl">
          <xsl:text>; </xsl:text>
        </xsl:if>
        <xsl:value-of select="."/>
        <xsl:if test="position() != last()">
          <xsl:text>; </xsl:text>
        </xsl:if>
      </xsl:if>
    </xsl:for-each>
    
    <xsl:for-each select="m:partName">
      <xsl:if test=". != ''">
        <xsl:if test="position()=1 and ($titl or $subt)">
          <xsl:text>; </xsl:text>
        </xsl:if>
        <xsl:value-of select="."/>
        <xsl:if test="position() != last()">
          <xsl:text>; </xsl:text>
        </xsl:if>
      </xsl:if>
    </xsl:for-each>
    
    <xsl:for-each select="m:partNumber">
      <xsl:if test=". != ''">
        <xsl:if test="position()=1 and ($titl or $subt or $partname)">
          <xsl:text>; </xsl:text>
        </xsl:if>
        <xsl:value-of select="."/>
        <xsl:if test="position() != last()">
          <xsl:text>; </xsl:text>
        </xsl:if>
      </xsl:if>
    </xsl:for-each>      
      </xsl:element>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>

<xsl:template match="m:identifier">
  
    <xsl:element name="field"><xsl:attribute name="name"><xsl:text>identifier_t</xsl:text></xsl:attribute>
        <xsl:value-of select="."/>
    </xsl:element>

</xsl:template>
 
<xsl:template match="m:name">

  <xsl:element name="field">
  <xsl:attribute name="name">
  <xsl:choose>
    <xsl:when test="@type='organization'"><xsl:text>name_organization_t</xsl:text></xsl:when>
    <xsl:when test="@type='conference'"><xsl:text>name_conference_t</xsl:text></xsl:when>
    <xsl:when test="@type='personal'"><xsl:text>name_personal_t</xsl:text></xsl:when>
  </xsl:choose>
  </xsl:attribute>
  
  <xsl:choose>
    <xsl:when test="m:namePart[@type='family'] or m:namePart[@type='given']">
      <xsl:if test="m:namePart[@type='family']">
    <xsl:value-of select="m:namePart[@type='family']"/>            
      </xsl:if>
      <xsl:if test="m:namePart[@type='given']">
    <xsl:if test="m:namePart[@type='family']">
      <xsl:text>, </xsl:text>
    </xsl:if>
    <xsl:value-of select="m:namePart[@type='given']"/>              
      </xsl:if>
      <xsl:if test="m:namePart[@type='date']">
    <xsl:text>, </xsl:text>
      <xsl:value-of select="m:namePart[@type='date']"/>
    </xsl:if>       
      </xsl:when>
      
      <!-- if only namePart no specific family or given name tags -->
      <xsl:otherwise>
    <xsl:choose>
      <xsl:when test="m:namePart != ''">
        <xsl:for-each select="m:namePart">
          <xsl:value-of select="."/>
          <xsl:if test="position()!=last()">
        <xsl:text>, </xsl:text>
          </xsl:if>
        </xsl:for-each>
      </xsl:when>
      <!-- if only displayForm -->
      <xsl:otherwise>
        <xsl:if test="m:displayForm != ''">
          <xsl:for-each select="m:displayForm">
        <xsl:value-of select="."/>
        <xsl:if test="position()!=last()">
          <xsl:text>, </xsl:text>
        </xsl:if>
          </xsl:for-each>
        </xsl:if>
      </xsl:otherwise>
    </xsl:choose>
      </xsl:otherwise>
    </xsl:choose>

    <!-- if there is text roleTerm -->
    <xsl:for-each select="m:role/m:roleTerm[@type='text']">
      <xsl:if test=". != ''">
    <xsl:text>, </xsl:text>
    <xsl:value-of select="."/>
      </xsl:if>
    </xsl:for-each>
  </xsl:element>
  
  <xsl:element name="field">
  
  <xsl:attribute name="name">
  <xsl:choose>
    <xsl:when test="@type='organization'"><xsl:text>name_organization_facet</xsl:text></xsl:when>
    <xsl:when test="@type='conference'"><xsl:text>name_conference_facet</xsl:text></xsl:when>
    <xsl:when test="@type='personal'"><xsl:text>name_personal_facet</xsl:text></xsl:when>
  </xsl:choose>
  </xsl:attribute>  
  
  <xsl:choose>
    <xsl:when test="m:namePart[@type='family'] or m:namePart[@type='given']">
      <xsl:if test="m:namePart[@type='family']">
    <xsl:value-of select="normalize-space(m:namePart[@type='family'])"/>            
      </xsl:if>
      <xsl:if test="m:namePart[@type='given']">
    <xsl:if test="normalize-space(m:namePart[@type='family'])">
      <xsl:text>, </xsl:text>
    </xsl:if>
    <xsl:value-of select="normalize-space(m:namePart[@type='given'])"/>              
      </xsl:if>
      <xsl:if test="m:namePart[@type='date']">
    <xsl:text>, </xsl:text>
      <xsl:value-of select="normalize-space(m:namePart[@type='date'])"/>
    </xsl:if>       
      </xsl:when>
      
      <!-- if only namePart no specific family or given name tags -->
      <xsl:otherwise>
    <xsl:choose>
      <xsl:when test="m:namePart != ''">
        <xsl:for-each select="m:namePart">
          <xsl:value-of select="."/>
          <xsl:if test="position()!=last()">
        <xsl:text>, </xsl:text>
          </xsl:if>
        </xsl:for-each>
      </xsl:when>
      <!-- if only displayForm -->
      <xsl:otherwise>
        <xsl:if test="m:displayForm != ''">
          <xsl:for-each select="m:displayForm">
        <xsl:value-of select="."/>
        <xsl:if test="position()!=last()">
          <xsl:text>, </xsl:text>
        </xsl:if>
          </xsl:for-each>
        </xsl:if>
      </xsl:otherwise>
    </xsl:choose>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:element>
</xsl:template>

<xsl:template match="m:subject">
    <xsl:variable name="topic" select="m:topic|m:occupation|m:titleInfo"/>
    <xsl:variable name="geo" select="m:geographic|m:hierarchicalGeographic|m:geographicCode"/>
    <xsl:variable name="time" select="m:temporal"/>
    <xsl:variable name="cart" select="m:cartographics"/>
    <xsl:variable name="genre" select="m:genre"/>
    <xsl:variable name="subname" select="m:name"/>

    <xsl:for-each select="$topic">
    <xsl:element name="field"><xsl:attribute name="name"><xsl:text>subject_topic_t</xsl:text></xsl:attribute>
        <xsl:value-of select="."/>
    </xsl:element>
    <xsl:element name="field"><xsl:attribute name="name"><xsl:text>subject_topic_facet</xsl:text></xsl:attribute>
        <xsl:value-of select="normalize-space(.)"/>
    </xsl:element>
    </xsl:for-each>
    <xsl:for-each select="$geo">
    <xsl:element name="field"><xsl:attribute name="name"><xsl:text>subject_geographic_t</xsl:text></xsl:attribute>
        <xsl:value-of select="."/>
    </xsl:element>
    <xsl:element name="field"><xsl:attribute name="name"><xsl:text>subject_geographic_facet</xsl:text></xsl:attribute>
        <xsl:value-of select="normalize-space(.)"/>
    </xsl:element>
    </xsl:for-each>
    <xsl:for-each select="$time">
    <xsl:element name="field"><xsl:attribute name="name"><xsl:text>subject_temporal_t</xsl:text></xsl:attribute>
        <xsl:value-of select="."/>
    </xsl:element>
    <xsl:element name="field"><xsl:attribute name="name"><xsl:text>subject_temporal_facet</xsl:text></xsl:attribute>
        <xsl:value-of select="normalize-space(.)"/>
    </xsl:element>
    </xsl:for-each>
    <xsl:for-each select="$subname">
    <xsl:element name="field"><xsl:attribute name="name"><xsl:text>subject_name_t</xsl:text></xsl:attribute>
        <xsl:value-of select="."/>
    </xsl:element>
    <xsl:element name="field"><xsl:attribute name="name"><xsl:text>subject_name_facet</xsl:text></xsl:attribute>
        <xsl:value-of select="normalize-space(.)"/>
    </xsl:element>
    </xsl:for-each>
    <xsl:for-each select="$genre">
    <xsl:element name="field"><xsl:attribute name="name"><xsl:text>genre_t</xsl:text></xsl:attribute>
        <xsl:value-of select="."/>
    </xsl:element>
    <xsl:element name="field"><xsl:attribute name="name"><xsl:text>genre_facet</xsl:text></xsl:attribute>
        <xsl:value-of select="normalize-space(.)"/>
    </xsl:element>
    </xsl:for-each>

    <!-- slurp up all sub elements of subject into one field, not sure if we need this -->
    <xsl:if test="*">
        <xsl:element name="field"><xsl:attribute name="name"><xsl:text>subject_t</xsl:text></xsl:attribute>
            <xsl:for-each select="*">
                <xsl:if test=". != ''">
                    <xsl:value-of select="."/>
                    <xsl:if test="position()!=last()">
                        <xsl:text> --</xsl:text>
                    </xsl:if>
                </xsl:if>
            </xsl:for-each>
        </xsl:element>
        <xsl:element name="field"><xsl:attribute name="name"><xsl:text>subject_facet</xsl:text></xsl:attribute>
            <xsl:for-each select="*">
                <xsl:if test=". != ''">
                    <xsl:value-of select="normalize-space(.)"/>
                    <xsl:if test="position()!=last()">
                        <xsl:text> --</xsl:text>
                    </xsl:if>
                </xsl:if>
            </xsl:for-each>
        </xsl:element>
    </xsl:if>
</xsl:template>

<xsl:template match="m:typeOfResource">
  <xsl:element name="field"><xsl:attribute name="name">type_of_resource_t</xsl:attribute>
    <xsl:value-of select="."/>
  </xsl:element>
  <xsl:element name="field"><xsl:attribute name="name">type_of_resource_facet</xsl:attribute>
    <xsl:value-of select="normalize-space(.)"/>
  </xsl:element>
</xsl:template>

<xsl:template match="m:abstract">
  <xsl:choose>
    <xsl:when test="@xlink">
      <xsl:element name="field">
    <xsl:attribute name="name"><xsl:text>abstract_t</xsl:text></xsl:attribute>
    <xsl:value-of select="@xlink"/>
      </xsl:element>
    </xsl:when>
    <xsl:otherwise>
      <xsl:element name="field"><xsl:attribute name="name">abstract_t</xsl:attribute>
    <xsl:value-of select="."/>
      </xsl:element>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>


<xsl:template match="m:tableOfContents">
    <xsl:choose>
      <xsl:when test="@xlink">
    <xsl:element name="field">
      <xsl:attribute name="name"><xsl:text>table_of_contents_t</xsl:text></xsl:attribute>
      <xsl:value-of select="@xlink"/>
    </xsl:element>        
      </xsl:when>
      <xsl:otherwise>
    <xsl:element name="field"><xsl:attribute name="name">table_of_contents_t</xsl:attribute>
      <xsl:value-of select="."/>
    </xsl:element>
      </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<xsl:template match="m:targetAudience">
    <xsl:choose>
      <xsl:when test="@xlink">
    <xsl:element name="field">
      <xsl:attribute name="name"><xsl:text>toc_t</xsl:text></xsl:attribute>
      <xsl:value-of select="@xlink"/>
    </xsl:element>
      </xsl:when>
      <xsl:otherwise>
    <xsl:element name="field"><xsl:attribute name="name">target_audience_t</xsl:attribute>
      <xsl:value-of select="."/>
    </xsl:element>        
      </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<xsl:template match="m:relatedItem">
  <xsl:if test="@type = 'host'">
    <xsl:element name="field"><xsl:attribute name="name">related_item_identifier_t</xsl:attribute>
      <xsl:value-of select="m:identifier"/>
    </xsl:element>
    <xsl:element name="field"><xsl:attribute name="name">related_item_title_t</xsl:attribute>
      <xsl:value-of select="m:titleInfo/m:title"/>
    </xsl:element>    
  </xsl:if>
</xsl:template>

<xsl:template match="m:location">
    <xsl:if test="m:physicalLocation">
      <xsl:element name="field"><xsl:attribute name="name">location_t</xsl:attribute>
    <xsl:for-each select="m:physicalLocation">
      <xsl:if test=". != ''">
        <xsl:value-of select="."/>
        <xsl:if test="position() != last()">
          <xsl:text>; </xsl:text>
        </xsl:if>
      </xsl:if>
    </xsl:for-each>
      </xsl:element>
    </xsl:if>
</xsl:template>

<xsl:template match="m:accessCondition">
  <xsl:element name="field"><xsl:attribute name="name">access_condition_t</xsl:attribute>
    <xsl:value-of select="."/>
  </xsl:element>
</xsl:template>

<xsl:template match="m:physicalDescription">
  <xsl:element name="field"><xsl:attribute name="name">physical_description_t</xsl:attribute>
    <xsl:for-each select="*">
      <xsl:if test=". != ''">
    <xsl:value-of select="."/>
    <xsl:if test="position() != last()">
      <xsl:text>; </xsl:text>
    </xsl:if>
      </xsl:if>
    </xsl:for-each>
  </xsl:element>
</xsl:template>

<xsl:template match="m:originInfo">
    <!--+ 
        + first look for any date with a keyDate and any attribute with the value w3cdtf
        + then for any date with a keyDate
        + then for the first dateIssued
        + then for the first dateCreated
        + then for the first copyrightDate
        + then for the first dateOther
        +-->
    <xsl:variable name="date_splat_w3c_key_date" select="*[@keyDate and @*='w3cdtf']"/>
    <xsl:variable name="date_splat_key_date" select="*[@keyDate]"/>
    <xsl:variable name="date_created" select="m:dateCreated[not(@keyDate)]"/>
    <xsl:variable name="date_issued" select="m:dateIssued[not(@keyDate)]"/>
    <xsl:variable name="date_copyrighted" select="m:copyrightDate[not(@keyDate)]"/>
    <xsl:variable name="date_other" select="m:dateOther[not(@keyDate)]"/>
    <xsl:variable name="date_captured" select="m:dateCaptured[not(@keyDate)]"/>
    <xsl:variable name="date_valid" select="m:dateValid[not(@keyDate)]"/>
    <xsl:variable name="date_modified" select="m:dateModified[not(@keyDate)]"/>
    
    <xsl:choose>
    <xsl:when test="$date_splat_w3c_key_date">
           <xsl:element name="field"><xsl:attribute name="name">raw_date</xsl:attribute>
          <xsl:value-of select="$date_splat_w3c_key_date"/>
           </xsl:element>
    </xsl:when>
    <xsl:when test="$date_splat_key_date">
           <xsl:element name="field"><xsl:attribute name="name">raw_date</xsl:attribute>
          <xsl:value-of select="$date_splat_key_date"/>
           </xsl:element>
    </xsl:when>
    <xsl:when test="$date_created">
        <xsl:for-each select="$date_created">
                <xsl:element name="field"><xsl:attribute name="name">raw_date</xsl:attribute>
                    <xsl:choose>
                    <xsl:when test="@point='start'">
                      <xsl:value-of select="."/>
                      <xsl:text>-</xsl:text>
                      <xsl:value-of select="following-sibling::*[1]"/>
                       </xsl:when>
                       <xsl:otherwise>
                       <xsl:value-of select="."/>
                       </xsl:otherwise>
                     </xsl:choose>
                </xsl:element>
            </xsl:for-each>
        </xsl:when>
    <xsl:when test="$date_issued">
        <xsl:for-each select="$date_issued">
                <xsl:element name="field"><xsl:attribute name="name">raw_date</xsl:attribute>
                    <xsl:choose>
                    <xsl:when test="@point='start'">
                      <xsl:value-of select="."/>
                      <xsl:text>-</xsl:text>
                      <xsl:value-of select="following-sibling::*[1]"/>
                       </xsl:when>
                   <xsl:when test="@point='end'">
                        <xsl:text>n.d.</xsl:text>
                       </xsl:when>
                       <xsl:otherwise>
                       <xsl:value-of select="."/>
                       </xsl:otherwise>
                     </xsl:choose>
                </xsl:element>
            </xsl:for-each>
    </xsl:when>
    <xsl:when test="$date_copyrighted">
        <xsl:for-each select="$date_copyrighted">
                <xsl:element name="field"><xsl:attribute name="name">raw_date</xsl:attribute>
                    <xsl:choose>
                    <xsl:when test="@point='start'">
                      <xsl:value-of select="."/>
                      <xsl:text>-</xsl:text>
                      <xsl:value-of select="following-sibling::*[1]"/>
                       </xsl:when>
                   <xsl:when test="@point='end'">
                        <xsl:text>n.d.</xsl:text>
                       </xsl:when>
                       <xsl:otherwise>
                       <xsl:value-of select="."/>
                       </xsl:otherwise>
                     </xsl:choose>
                </xsl:element>
            </xsl:for-each>
    </xsl:when>
    <xsl:when test="$date_other">
        <xsl:for-each select="$date_other">
                <xsl:element name="field"><xsl:attribute name="name">raw_date</xsl:attribute>
                    <xsl:choose>
                    <xsl:when test="@point='start'">
                      <xsl:value-of select="."/>
                      <xsl:text>-</xsl:text>
                      <xsl:value-of select="following-sibling::*[1]"/>
                       </xsl:when>
                   <xsl:when test="@point='end'">
                        <xsl:text>n.d.</xsl:text>
                       </xsl:when>
                       <xsl:otherwise>
                       <xsl:value-of select="."/>
                       </xsl:otherwise>
                     </xsl:choose>
                </xsl:element>
            </xsl:for-each>
    </xsl:when>
    </xsl:choose>

    <xsl:if test="m:placeTerm[@type='text']|m:publisher">
        <xsl:element name="field"><xsl:attribute name="name">publisher_place_t</xsl:attribute>
        <xsl:for-each select="m:placeTerm[@type='text']|m:publisher">
                <xsl:if test=". != ''">
                <xsl:value-of select="."/>
                <xsl:if test="position() != last()">
                        <xsl:text>; </xsl:text>
                </xsl:if>
            </xsl:if>
            </xsl:for-each>
        </xsl:element>
    </xsl:if>
    
    <xsl:if test="m:edition|m:issuance|m:frequency">
        <xsl:element name="field"><xsl:attribute name="name">origin_aspects_t</xsl:attribute>
        <xsl:for-each select="m:edition|m:issuance|m:frequency">
                <xsl:if test=". != ''">
                <xsl:value-of select="."/>
                <xsl:if test="position() != last()">
                        <xsl:text>; </xsl:text>
                </xsl:if>
            </xsl:if>
            </xsl:for-each>
        </xsl:element>
    </xsl:if>

  <xsl:variable name="pl" select="m:place"/>
  <xsl:variable name="pub" select="m:publisher"/>
  <xsl:variable name="datei" select="m:dateIssued" separator="== "/>
  <xsl:variable name="datec" select="m:dateCreated"/>
  <xsl:variable name="datecr" select="m:copyrightDate"/>
  <xsl:variable name="edit" select="m:edition"/>
  
  <xsl:if test="$pl or $pub or $datei or $datec or $edit">
      <xsl:element name="field"><xsl:attribute name="name">origin_t</xsl:attribute>
      <xsl:if test="$pl or $pub or $datei or $datec">
          <!-- place U concatenated with publisher T into U -->
          <xsl:if test="$pl or $pub">
          <!-- place U -->
          <xsl:if test="$pl">
            <xsl:for-each select="m:place/m:placeTerm">
              <xsl:choose>
            <xsl:when test="@type = 'code'">
            </xsl:when>
            <xsl:otherwise>
              <xsl:value-of select="."/>
              <xsl:if test="position()!=last()">
                <xsl:text>; </xsl:text>
              </xsl:if>
            </xsl:otherwise>          
            </xsl:choose>
          </xsl:for-each>
        </xsl:if>
        
        <!-- concatenated by ',' -->
        <xsl:if test="$pl and $pub">
          <xsl:text>, </xsl:text>
        </xsl:if>
        
        <!-- publisher T -->
        <xsl:if test="$pub">
          <xsl:for-each select="m:publisher">
            <xsl:if test=". != ''">
              <xsl:value-of select="."/>
              <xsl:if test="position()!=last()">
            <xsl:text>; </xsl:text>
              </xsl:if>
            </xsl:if>
          </xsl:for-each>   
        </xsl:if>
        </xsl:if>
          
        <xsl:if test="( $pl or $pub ) and ( $datei or $datec )">
          <xsl:text>, </xsl:text>
        </xsl:if>

        <!-- dateIssued YR -->
        <xsl:if test="$datei">
                <xsl:for-each select="m:dateIssued">
          <xsl:if test=". != ''">
            <xsl:value-of select="."/>
            <xsl:if test="position()!=last()">
              <xsl:text>; </xsl:text>
            </xsl:if>
          </xsl:if>
        </xsl:for-each>
        </xsl:if>
        
        <xsl:if test="$datei or $datec">
          <xsl:text>; </xsl:text>
        </xsl:if>

        <!-- dateCreated YR -->
        <xsl:if test="$datec">
         <xsl:for-each select="m:dateCreated">
          <xsl:if test=". != ''">
            <xsl:value-of select="."/>
            <xsl:if test="position()!=last()">
              <xsl:text>; </xsl:text>
            </xsl:if>
          </xsl:if>
        </xsl:for-each>
        </xsl:if>
    </xsl:if>
    
    <xsl:if test="$pl or $pub or $datei or $datec">
      <xsl:text>, </xsl:text>
    </xsl:if>

    <xsl:if test="$edit">
          <xsl:for-each select="m:edition">
        <xsl:if test=". != ''">
          <xsl:value-of select="."/>
          <xsl:if test="position()!=last()">
            <xsl:text>; </xsl:text>
          </xsl:if>
        </xsl:if>
          </xsl:for-each>
    </xsl:if> 
       </xsl:element>

  </xsl:if>  
</xsl:template>

</xsl:stylesheet>
'''
    xslt_root = etree.XML(mods_to_solr)
    transform = etree.XSLT(xslt_root)
    
    #determine the output directory for the tempfile and for if there are multiple output files due to a directory batch
    #put directory not created error handle here'''
    if os.path.isdir(outPath)==False: #outPath is a file path
        outDirectory,fileNameOut=os.path.split(outPath)
        fileList=(fileNameOut)
    else:#is a driectory
        outDirectory=outPath
    #create list of files to be converted
    if os.path.isdir(inPath)==False:
        inDirectory, fileListStr=os.path.split(inPath)
        fileList=[fileListStr]
    else:
        inDirectory=inPath
        fileList=os.listdir(inPath)#get files in the dir
        for path in os.listdir(inPath):
            if path[(len(path)-4):len(path)]!='.xml' :
                fileList.remove(path)
            elif xmlib.rootHasNamespace(os.path.join(inPath,path), 'http://www.loc.gov/mods/v3')!=True:
                fileList.remove(path)
            #remove files that are not xml that have the mods namespace
    
    for fileName in fileList:
        #if fileNameOut was not in outPath make one up
        if os.path.isdir(outPath)==True:
            fileNameOut=fileName[0:fileName.rindex('.')]+'_solr.xml'
        #cunstruct the paths
        filePathIn=os.path.join(inDirectory,fileName)
        filePathOut=os.path.join(outDirectory,fileNameOut)
        #read mods file
        modsFile=open(filePathIn,'r')
        doc = etree.parse(modsFile)
        #translate
        transform_result = transform(doc)
        #write solr file
        solrOut=open (filePathOut,'w')
        solrOut.write(str(transform_result))
    
    
    return True   
    
'''
collection of helper functions used by the API functions
'''


def checkPaths(pathIn, pathOut):
    '''
Does some standardized error checking on the input and output path arguments

@param pathIn: input path to check
@param pathOut: output path to check

@return bool: return false if the arguments are not valid, true if they are
'''
    #make sure that the indicated paths are valid
    if os.path.lexists(pathIn)==False:
        logging.error('The indicated input path is not valid: '+pathIn)
        return False
    
    if os.path.isdir(pathOut):
        return True
    elif os.path.isfile(pathOut):
        logging.error('If the output path is a file it can not already exist: '+ pathOut)
        return False
    elif os.path.lexists(os.path.dirname(pathOut))!=True:
        logging.error('The output path is invalid: '+pathOut)
        return False
        
    #make sure that if the input path is a directory that the output path is also a directory
    if os.path.isdir(pathIn)==True and os.path.isdir(pathOut)==False:
        logging.error('If the input path is a directory then so must be the output directory')
        return False
    
    return True


def checkOpts(optsIn):
    '''
Does some standardized checking on command line option arguments

@param optsIn: option set to check

@return bool: return false if the arguments are not valid, true if they are
'''
    if isinstance(optsIn, list)==False and optsIn!='default' and optsIn!='TN':
        logging.error('CommandLine arguments must be lists or a known keyword like \'TN\' or \'default\'' )
        return False
    return True


def checkExtraArgs(args):
    '''
Does a standard check to see if too many args was passed in

@param args: list holding the *args to be checked

@return bool: return false if the arguments are not valid, true if they are
'''
    if len(args)>0:
        logging.error('Too many arguments supplied:'+args)
        return False
    return True


def checkStd(pathIn,pathOut,args,*opts):
    '''
Wrapper function that calls all standard error checking

@param pathIn: input path to check
@param pathOut: output path to check
@param args: list holding the *args to be checked
@param *opts: option set to check

@return bool: return false if the arguments are not valid, true if they are
'''
    if checkPaths(pathIn,pathOut)==False:
        return False
    if checkExtraArgs(args)==False:
        return False
    for optSet in opts:
        if checkOpts(optSet)==False:
            return False
    return True