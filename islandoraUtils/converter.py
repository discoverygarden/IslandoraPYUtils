'''
Created on Apr 5, 2011

@author: William Panting
@dependancies: Kakadu, ImageMagick, ABBYY CLI, Lame, SWFTools, FFmpeg

This is a Library that will make file conversions and manipulations like OCR using Python easier. 
Primarily it will use Kakadu and ABBYY
but it will fall back on ImageMagick if Kakadu fails and for some conversions Kakadu does not support.

Used scripts created by Jonathan Green as the starting piont.
Please make sure that the output directory already exists.

TODO: make recursive option
TODO: explore handling output directory creation
TODO: explore more input file type checking
TODO: add video support
TODO: add open office word doc conversions
TODO: explore better conversion options
TODO: explore more backup solutions
'''
import logging, subprocess, os
'''
This is a collection of methods that converts various file formats to others.
We use 'convert' due to lack of Kakadu license

@param inPath: source file or dir
@param outPath: destination file or dir
@param kakaduOpts: a list of options or a string 'default'
@param imageMagicOpts: a list of options or a string 'default'  

@return bool: true if successful [completion not conversion] false if not
'''
def tif_to_jp2(inPath,outPath,kakaduOpts=None,imageMagicOpts=None,*extraArgs):
    
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


'''
ABBYY OCR CLI Command Line Tool support

@param: inPath: source file or dir
@param: outPath: destination file or dir
@param: inputOpts: the ABBYY command line options not associated with a specific file output tyep, can be None
@param: fileTypeOpts: 1. a dictionary where the key is a file output type and the vale is a string 'default' or list of options, or 2. a string 'default'

@return bool: true if successful [completion not conversion] false if not

TODO: make default output options for all output file types 
'''
def tif_OCR(inPath,outPath,fileTypeOpts,inputOpts=None,*extraArgs):
    '''
    #quick and dirty parameter input check
    if(isinstance(fileTypeOpts, dict)!=True and fileTypeOpts!='default')\
    or(isinstance(inputOpts, list)!=True and inputOpts!='default' and inputOpts!=None)\
    or isinstance(inPath, str)!=True \
    or isinstance(outPath, str)!=True\
    or len(extraArgs)!=0:        
        logging.error('Bad function call to tif_OCR')
        return False
  '''
        #error checking, does not take TN
    if checkStd(inPath,outPath,extraArgs,inputOpts)==False:
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

'''
This function will use ImageMagick to convert tifs to jpgs
@param: inPath: source file or dir
@param: outPath: destination file or dir
@param imageMagicOpts: can be 'default' 'TN' or a list of options to use

@return bool: true if successful false if not
'''
def tif_to_jpg(inPath,outPath, imageMagicOpts,*extraArgs):
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

'''
This function will use swftools to convert pdf files to swfs
@param: inPath: source file or dir
@param: outPath: destination file or dir
@param swfToolsOpts: options to be applied to the conversion can be 'default'

@return bool: true if successful [completion not conversion] false if not
'''
def pdf_to_swf(inPath,outPath,swfToolsOpts,*extraArgs):
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

'''
This function will use FFmpeg to turn a wav file into an ogg file
@param: inPath: source file or dir
@param: outPath: destination file or dir
@param FFmpegOpts: options to be applied to the conversion can be 'default'

@return bool: true if successful [completion not conversion] false if not
'''
def wav_to_ogg(inPath,outPath,FFmpegOpts,*extraArgs):
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

'''
This function uses the lame tool to make wav files into mp3 files
@param: inPath: source file or dir
@param: outPath: destination file or dir
@param lameOpts: options to be applied to the conversion can be 'default'

@return bool: true if successful [completion not conversion] false if not
'''
def wav_to_mp3(inPath,outPath,lameOpts,*extraArgs):
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

'''
This function will use ImageMagick to convert tifs to jpgs
@param: inPath: source file or dir
@param: outPath: destination file or dir
@param imageMagicOpts: can be 'default' 'TN' or a list of options to use

@return bool: true if successful [completion not conversion] false if not
'''
def pdf_to_jpg(inPath,outPath,imageMagicOpts,*extraArgs):
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

'''
collection of helper functions used by the API functions
'''

'''
Does some standardized error checking on the input and output path arguments
@param pathIn: input path to check
@param pathOut: output path to check
@return bool: return false if the arguments are not valid, true if they are
'''
def checkPaths(pathIn, pathOut):
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

'''
Does some standardized checking on command line option arguments
@param optsIn: option set to check
@return bool: return false if the arguments are not valid, true if they are
'''
def checkOpts(optsIn):
    if isinstance(optsIn, list)==False and optsIn!='default' and optsIn!='TN':
        logging.error('CommandLine arguments must be lists or a known keyword like \'TN\' or \'default\'' )
        return False
    return True

'''
Does a standard check to see if too many args was passed in
@param args: list holding the *args to be checked
@return bool: return false if the arguments are not valid, true if they are
'''
def checkExtraArgs(args):
    if len(args)>0:
        logging.error('Too many arguments supplied:'+args)
        return False
    return True

'''
Wrapper function that calls all standard error checking
@param pathIn: input path to check
@param pathOut: output path to check
@param args: list holding the *args to be checked
@param optsIn: option set to check
@return bool: return false if the arguments are not valid, true if they are
'''
def checkStd(pathIn,pathOut,args,*opts):
    if checkPaths(pathIn,pathOut)==False:
        return False
    if checkExtraArgs(args)==False:
        return False
    for optSet in opts:
        if checkOpts(optSet)==False:
            return False
    return True