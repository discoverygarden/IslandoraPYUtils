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
FIXME: Some poor assumptions are made regarding paths... There exist other types of files besides 'files'and 'directories' (block/char devices, sym-links (which may cause weird evaluations?), etc...)
TODO: Seems like generalizing file selection based on a path and extension(s) could be rather useful
      or automatically determine file type by magic number (resulting in things like tif_to_jpg -> any_to_jpg)
TODO: provide override options for various input checks
'''
import logging, subprocess, os, xmlib

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
    if not checkPaths(inPath,outPath):
        return False
    if fileTypeOpts=='TN' or inputOpts=='TN':
        logging.error('This function tif_to_jp2 does not accept the \'TN\' keyword')
        return False
    #special dictionary error checking
    if not isinstance(fileTypeOpts, dict) and fileTypeOpts != 'default':
        logging.error('The fileTypeOpts must be a dictionary or the keyword \'default\'.' )
        return False

    #prevents the script from attempting to write multiple output files to one output file path
    if os.path.isdir(inPath) and not os.path.isdir(outPath):
        logging.error('If the input path is a directory, so must be the output path.')
        return False
    if len(fileTypeOpts)>1 and fileTypeOpts!='default' and os.path.isdir(outPath)!=True:
        logging.error('If there is to be more than one output file then the output path must be a directory.')
        return False

    #determine the output directory if there are multiple output files due to a directory batch
    #put directory not created error handling here'''
    if not os.path.isdir(outPath):
        outDirectory,fileNameOut=os.path.split(outPath)
        fileList=(fileNameOut)
    else:#is a driectory
        outDirectory=outPath

    #create list of files to be converted
    if not os.path.isdir(inPath):
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

        outputs = {
            'PDF': ('.pdf', ('-pem','ImageOnText','-pfq','75')),
            'HTML': ('.html', ()),
            'RTF': ('.rtf', ()),
            'DBF': ('.dbf', ()),
            'XML': ('.xml', ()),
            'TEXT': ('.txt', ('-tel','-tpb','-tet','UTF8')),
            'XLS': ('.xls', ())
        }

        #determine output file extension, and input check
        for outputType,outputOpts in fileTypeOpts.iteritems():
            try:
                extension, defaultOutPutsOpts = outputs[outputType]
            except KeyError:
                logging.error('Incorrect output type "%s" specified for ABBYY CLI.', outputType)
                return False
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
        elif r == 0:
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

def tif_to_pdf(inPath,outPath,tiff2pdfOpts,*extraArgs):
    '''
    This function will use the shell's tiff2pdf to convert tiff files to pdf
    @param: inPath: source file
    @param: outPath: destination file or dir
    @param tiff2pdfOpts: options to be applied to the conversion, can be 'default'
    
    @return bool: true if successful [completion not conversion] false if not
    '''
    #error checking
    if not checkStd(inPath,outPath,extraArgs,tiff2pdfOpts):
        return False
    if tiff2pdfOpts == 'TN':
        logging.error('This function tif_to_pdf does not support the \'TN\' keyword')
        return False

    #determine the output directory for the tempfile and for if there are multiple output files due to a directory batch
    #put directory not created error handle here'''
    if os.path.isdir(outPath): #outPath is a directory
        outDirectory = outPath
    else:#is a file path
        outDirectory, fileNameOut = os.path.split(outPath)
    #create list of files to be converted
    inDirectory, fileListStr = os.path.split(inPath)
    fileList = [fileListStr]

    for fileName in fileList:

        #if fileNameOut was not in outPath make one up
        if os.path.isdir(outPath):
            fileNameOut = "%s.pdf" % os.path.splitext(fileName)[0]
        filePathIn = os.path.join(inDirectory, fileName)
        filePathOut = os.path.join(outDirectory, fileNameOut)

        #create tiff2pdf call
        if tiff2pdfOpts=='default':
            tiff2pdfCall=["tiff2pdf", filePathIn, '-o', filePathOut]
        else:
            tiff2pdfCall=["tiff2pdf", filePathIn, '-o', filePathOut]
            tiff2pdfCall.extend(tiff2pdfOpts)
        #make the system call
        r = subprocess.call(tiff2pdfCall)

        if r == 0:
            logging.info('File converted: %s'% (filePathOut))
        else:
            logging.warning('PDF creation failed (tiff2pdf return code:%d for file input %s).' % ( r, filePathIn))
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
    xslt_root = etree.parse(os.path.join(os.path.dirname(__file__), '__resources/mods_to_solr.xslt'))
    transform = etree.XSLT(xslt_root)

    #determine the output directory for the tempfile and for if there are multiple output files due to a directory batch
    #put directory not created error handle here'''
    if not os.path.isdir(outPath): #outPath is a file path
        outDirectory,fileNameOut=os.path.split(outPath)
        fileList=(fileNameOut)
    else:#is a driectory
        outDirectory=outPath
    #create list of files to be converted
    if not os.path.isdir(inPath):
        inDirectory, fileListStr=os.path.split(inPath)
        fileList=[fileListStr]
    else:
        inDirectory=inPath
        fileList=os.listdir(inPath)#get files in the dir
        for path in os.listdir(inPath):
            if not path.endswith('.xml'):
                fileList.remove(path)
            elif not xmlib.rootHasNamespace(os.path.join(inPath,path), 'http://www.loc.gov/mods/v3'):
                fileList.remove(path)
            #remove files that are not xml that have the mods namespace

    for fileName in fileList:
        #if fileNameOut was not in outPath make one up
        if os.path.isdir(outPath):
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

