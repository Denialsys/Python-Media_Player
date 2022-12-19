from os import (
    path as imPath,
    popen as imShell,
    remove as imDelete,
    getcwd as imGetCurrentDir,
    listdir as imListFile,
    makedirs as imMakeDirs
)

from re import sub as imRegEx

from json import (
    load as imJsonLoad,
    dump as imSaveJson
)

from datetime import (
    datetime as imDatetime,
    timedelta as imTimeDelta
)

from urllib.request import (
    urlretrieve as imDownload,
    quote as imEscapeUrl
)

class FileManagerModule():
    '''File Manager Module
        Module that anages the media files, loads the system configurations 
        and caches theserver instructions incase the media player goes offline
        
    @Usage: (On a project)
        import fileManagerModule
        
        g_sysSettingsDir = '/home/pi/Desktop/Python files/python classes/System Config.ini' ##main configuration settings
        g_cachedJsonDir = '/home/pi/Desktop/Python files/python classes/cachedSched.json' ##where the cached json will be stored
        g_mediaDir = '/home/pi/Desktop/' #Where the downloaded media files will be stored
        g_downloadUrl = 'http://192.168.1.19:8080/download?file='
        
        ##fabricate a json to manage
        g_mediaFiles = {'mediaFiles' : [{"fileName":"Big Buck Bunny.mp4","startTime":"13:00","endTime":"14:00"},
                        {"fileName":"rpi1.mp4","startTime":"11:00","endTime":"12:00"},
                        {"fileName":"rpi2.mp4","startTime":None,"endTime":None},
                        {"fileName":"rpi3.mp4","startTime":None,"endTime":None},
                        {"fileName":"Cloudytime.mp4","startTime":"15:00","endTime":"15:30"},
                        {"fileName":"City and Streets.mp4","startTime":None,"endTime":None}
                        ]}
        
        g_FileManagerModule = fileManagerModule.FileManagerModule()
        g_FileManagerModule.c_cachedJson = g_mediaFiles
        g_FileManagerModule.c_sysSettingsFile = g_sysSettingsDir
        g_FileManagerModule.c_cachedJsonFile = g_cachedJsonDir
        g_FileManagerModule.arrangeMediaList()
        g_FileManagerModule.c_downloadUrl = g_downloadUrl
        
    @Variable / Method prefixes:
        im -> Imported method
        c_ -> Class variable
        m_ -> Method variable
        t_ -> temporary variable
        __ -> methods to be used only by the class
    '''
    def __init__(self):
        
        ##Containers for file directories
        self.c_sysSettingsFile = None
        self.c_cachedJsonFile = None
        self.c_downloadUrl = None

        ##Media files containers
        self.c_mediaWithSched = []
        self.c_mediaWithoutSched = []
        self.c_scheduledToPlayNow = None
        
        ##Containers for the json data
        self.c_cachedJson = {}  ##stored json, this will always be updated when server json has updated
        self.c_sysSettings = {}

        self.c_serverTime = None
        self.c_timeDeviation = None

        self.c_lastError = ''

    def getCachedJson(self):
        '''Retrieves the contents of the json file'''
        
        m_errProcessName = self.__class__.__name__ + '-getCachedJson ->'
        
        try:
            ##Incase no json directory was assigned yet
            if self.c_cachedJsonFile == None: self.c_cachedJsonFile = imGetCurrentDir() + '/configurations/cachedSched.json'
            
            with open(self.c_cachedJsonFile, 'r') as t_jsonFile:
                self.c_cachedJson = imJsonLoad(t_jsonFile)
            return self.c_cachedJson
        
        except Exception as e:
            self.c_lastError = 'Error in retrieving the stored Json: %s%s' % (m_errProcessName, str(e.args))
            return {}

    def getSysSettings(self):
        '''Retrieves the contents of the json file'''
        
        m_errProcessName = self.__class__.__name__ + '-getSysSettings ->'
        
        try:
            ##Incase no json directory was assigned yet, create default directory
            if self.c_sysSettingsFile == None: self.c_sysSettingsFile = imGetCurrentDir() + '/configurations/systemSetting.json'
            
            with open(self.c_sysSettingsFile, 'r') as t_settingsFile:
                self.c_sysSettingsFile = imJsonLoad(t_settingsFile)
            return self.c_sysSettings

        except Exception as e:
            self.c_lastError = 'Error in retrieving the system settings: %s%s' % (m_errProcessName, str(e.args))
            return {}
    
    def arrangeMediaList(self, p_mediaDir):
        '''Segregates the list of media files taken from the server response
            fills up the list of media that doesn't have schedule and media that has.
            Also adds the media directory to the media filenames upon segregation
            @Params
                p_mediaDir -> the media directory that is to be added to the filename of the unscheduled media'''
        
        for t_media in self.c_cachedJson['mediaFiles']:
            
            m_mediaWithoutSched = t_media.copy()
            if 'fileName' in t_media: m_mediaWithoutSched['fileName'] = p_mediaDir + t_media['fileName']
            
            if (t_media['startTime'] == None) or (not t_media['startTime'].strip()):
                ##Media without schedule are treated differently they need directory in their file name
                self.c_mediaWithoutSched.append(p_mediaDir + t_media['fileName'])
            else:
                self.c_mediaWithSched.append(t_media)

    def isThereScheduledToPlayNow(self):
        '''Checks if there is a media supposed to play in the current time that this method was called
            @Return
                True -> If a media scheduled to play was found, also sets the scheduled media
                False -> If no media was to play yet'''
        m_errProcessName = self.__class__.__name__ + '-isThereScheduledToPlayNow ->'
        try:
            ##periodically calculate the current server time before checking for new media
            self.c_serverTime = (imDatetime.now() + self.c_timeDeviation).time()
            for t_media in self.c_mediaWithSched:
                if ( (imDatetime.strptime(t_media['startTime'],'%H:%M').time() <= self.c_serverTime) and
                         ( imDatetime.strptime(t_media['endTime'],'%H:%M').time() >= self.c_serverTime) ):
                    self.c_scheduledToPlayNow = t_media['fileName']
                    return True
                
            return False
        except Exception as e:
            self.c_lastError = 'Error in checking the scheduled medias: %s%s' % (m_errProcessName, str(e.args))
            return False

    def calcTimeDeviation(self):
        '''Calculates the difference between the server and the client time'''
        
        m_errProcessName = self.__class__.__name__ + '-calcTimeDeviation ->'
        try:
            self.c_timeDeviation = imDatetime.strptime(self.c_cachedJson['serverDateTime'], '%Y-%m-%d %H:%M') - imDatetime.now()
            self.c_serverTime = (imDatetime.now() + self.c_timeDeviation).time()
        except Exception as e:
            self.c_lastError = 'Unable to calculate time difference between server and client: %s%s' % (m_errProcessName, str(e.args))

    def saveJson(self):
        '''Dumps the newly acquired json file from server to a file so even when the server is offline
            the program still have a copy of the instructions'''
        
        m_errProcessName = self.__class__.__name__ + '-saveJson ->'
        try:
            if self.c_cachedJsonFile == None: self.c_cachedJsonFile = imGetCurrentDir() + '/configurations/cachedJson.json'
            with open(self.c_cachedJsonFile, 'w+') as t_jsonFile:
                imSaveJson(self.c_cachedJson, t_jsonFile)
        except Exception as e:
            self.c_lastError = 'Error in saving json: %s%s' % ( m_errProcessName, str(e.args) )
            
    def getLocalStorageSize(self):
        '''Calculates the remaining space in the local storage
            @Returns
                0 -> if given directory is invalid or theres an error in procedure
                number in KB, MB or GB -> if successfully queried'''
        
        m_errProcessName = self.__class__.__name__ + '-getLocalStorageSize ->'
        try:
            m_probeCommand = imShell('df -h /' ).read().strip().split('\n')
            if len(m_probeCommand) == 1:
                self.c_lastError = 'There must be an error with the root director to check: %s%s' % (m_errProcessName, str(e.args))
                return 0
            return imRegEx(' +',' ', m_probeCommand[1]).split(' ')[3]
        except Exception as e:
            self.c_lastError = 'Error in parsing the available storage size: %s%s' % (m_probeCommand, str(e.args))
            return 0

    def downloadMedia(self, p_mediaDir, p_mediaFile):
        '''Checks if the file already exist, download if not
            @Params
                p_mediaDir -> Directory which the file will be searched and saved into
                p_mediaFile -> File to be download'''
        
        m_errProcessName = self.__class__.__name__ + '-downloadMedia ->'
        
        ##NEEDS overwriting condition
        try:
            if self.getLocalStorageSize() == 0:
                self.c_lastError = 'Error in downloading! Local storage might be full! %s' % m_errProcessName
                print(self.c_lastError)
                return
            if not imPath.exists(p_mediaDir + p_mediaFile):
                print('\tDone downloading %s' % p_mediaFile)
                imDownload(self.c_downloadUrl + imEscapeUrl(p_mediaFile), p_mediaDir + p_mediaFile)
                
            else:
                print('\tSkipping %s, file already exist' % p_mediaFile)
        except Exception as e:
            self.c_lastError = 'Error in downloading the file %s: %s%s' % (p_mediaFile, m_errProcessName, str(e.args))
            if str(e.args) == '()': print('Error downloading %s file might not be available in the server' % p_mediaFile)

    def downloadListOfMedia(self, p_mediaDir, p_mediaListType=0):
        '''Downloads all the media listed in cached json
            @Params:
                p_mediaDir -> Directory which the file will be searched and saved into
                p_mediaListType -> list of media files that will be downloaded:
                                    0 - ALL
                                    1 - Media list that has schedule
                                    2 - Media list that has no schedule'''
        
        if p_mediaListType == 0: m_mediaList = self.c_cachedJson['mediaFiles']
        elif p_mediaListType == 1: m_mediaList = self.c_mediaWithSched.copy()
        else: m_mediaList = self.c_mediaWithoutSched.copy()
        
        for t_media in m_mediaList:
            self.downloadMedia(p_mediaDir, t_media['fileName'])
        print('Download list accommodated')
            
    def deleteAllMedia(self, p_mediaDir):
        '''Deletes the medias that are not in the list of medias to be played
            @Params
                p_mediaDir -> directory where the media files was located'''

        print('Deleting all previously used medias')
        m_targetFiles = imListFile(p_mediaDir)
        for t_mediaFile in m_targetFiles: self.deleteMedia(p_mediaDir, t_mediaFile)
        print('Obsolete medias deleted')
        
    def deleteMedia(self, p_mediaDir, p_fileName):
        '''Deletes a specified target file
            @Params
                p_mediaDir -> directory where the media files was located
                p_fileName -> the target filename'''
        
        m_errProcessName = self.__class__.__name__ + '-deleteMedia ->'
        try:
            print('Deleting %s%s' % (p_mediaDir, p_fileName))
            if ( imPath.exists(p_mediaDir + p_fileName) ): imDelete(p_mediaDir + p_fileName)
        except Exception as e:
            self.c_lastError = 'Error in deleting file: %s%s' % ( m_errProcessName, str(e.args) )
