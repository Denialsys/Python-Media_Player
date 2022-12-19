'''Main program

    @Variable / Method prefixes:
    im -> Imported method
    c_ -> Class variable
    m_ -> Method variable
    t_ -> temporary variable
    __ -> methods to be used only by the class
'''

print ('Initializing Components')
##============================================>>
## Program settings variables                 >>
##============================================>>

##Dependency file locations
from threading import Thread as imThread
from os import getcwd as imGetCurrentDir

g_sysSettingsFile = imGetCurrentDir() + '/configurations/System Config.json'
g_cachedJsonFile = imGetCurrentDir() + '/configurations/cachedSched.json'
g_mediaDir = imGetCurrentDir() + '/media files/' #Where the downloaded media files will be stored
g_splashDir = imGetCurrentDir() + '/splash/'
g_isSystemReady = False ##Main switch of the system procedures

g_serverUrl = 'http://192.168.1.19:8080/getJson'
##g_serverUrl = 'https://jsonblob.com/api/jsonBlob/65573a66-d754-11e8-839a-f3e5fcd22764'
g_downloadUrl = 'http://192.168.1.19:8080/download?file='

g_jsonMain = {} #json data where the instructions will be parsed
g_jsonStamp = {} #json data used for tracking changes
g_currentIP = ''

g_lastKnownProcess = None
g_errProcessName = ''
g_systemError = ''

## Program settings variables
##--------------------------------------------<<

##============================================>>
## Module settings                            >>
##============================================>>
try:
    print('Loading libraries')
    g_errProcessName = 'Module Settings: MediaPanelModule ->'
    import mediaPanelModule
    g_lastKnownProcess = 0x01
    ##Initialization for media panel module
    g_MediaPanelModule = mediaPanelModule.MediaPanelModule()
    g_MediaPanelModule.show_all()
    g_MediaPanelModule.playMedia(g_splashDir + 'rpi2.mp4')   ##play splash screen
    g_isSystemReady = True
    
    g_errProcessName = 'Module Settings: NetworkModule ->'
    import networkModule
    g_lastKnownProcess = 0x00
    ##Initial settings for network module
    g_NetworkModule = networkModule.NetworkModule()
    g_NetworkModule.c_requestDelay = 1 #delay in seconds before repeating network test
    g_NetworkModule.c_serverUrl = g_serverUrl
    
    g_errProcessName = 'Module Settings: FileManagerModule ->'
    import fileManagerModule
    g_lastKnownProcess = 0x02
    ##Initialization for file manager module
    g_FileManagerModule = fileManagerModule.FileManagerModule()
    g_FileManagerModule.c_downloadUrl = g_downloadUrl
    g_FileManagerModule.c_sysSettingsFile = g_sysSettingsFile
    g_FileManagerModule.c_cachedJsonFile = g_cachedJsonFile
    g_FileManagerModule.c_mediaDir = g_mediaDir
    
except Exception as e:
    print('Error occured preventing start up of the system')
    g_systemError = 'Error in library imports: %s%s' % (g_errProcessName, str(e.args))
    g_lastKnownProcess = 0x03
## Module settings
##--------------------------------------------<<

def interruptService():
    '''Subroutine for external interrupts'''

def shutdownDevice():
    '''For safely shutting down the system'''

def abort():
    '''Aborts all the process / stops the main loop'''
    if g_lastKnownProcess < 0x0B: m_isSafeToProceed = True
    else: m_isSafeToProceed = False
    g_MediaPanelModule.stop()
    g_MediaPanelModule.c_isMediaListPlayerOn = False
    g_NetworkModule.c_isPersistentCheckingEnabled = False
    g_lastKnownProcess = 0x1E
    print('All routines aborted')
    
def main():
    '''Main routine'''

    global g_errProcessName, g_jsonStamp, g_currentIP, g_jsonMain, g_isSystemReady
    g_errProcessName = 'main ->'

    g_lastKnownProcess = 0x04
    m_isWithoutSchedPlaying = False
    m_networkRetries = 0
    m_isSafeToProceed = False

    ##============================>>
    ## Initial network and json test
    ##----------------------------<<
    if g_isSystemReady == False:
        ##Critical initialization has errors, prevent starting up
        print('Please verify that the Module settings has no errors')
        g_lastKnownProcess = 0x05
        return
    else:
        print ('\n================ Starting Main Routine ================\n')
        print('Checking network and server')
        g_lastKnownProcess = 0x06
        while(not m_isSafeToProceed):
            try:
                if m_networkRetries >= 5:
                    ##Access cached instructions, read json from cache
                    print('Accessing from cache')
                    m_networkRetries = 0
                    ##use the method regardless of its return value
                    g_FileManagerModule.getCachedJson()
                    g_lastKnownProcess = 0x07
                else:
                    ##Read json from server
                    print('Accessing server instructions')
                    g_NetworkModule.checkNetworkAndServer()
                    m_networkRetries += 1
                    g_lastKnownProcess = 0x08
                    ##If theres no server stop here
                    if (not g_NetworkModule.c_isServerActive): continue
                    
                    g_FileManagerModule.c_cachedJson = g_NetworkModule.c_jsonResponse.copy()
                    g_FileManagerModule.saveJson()
                    g_lastKnownProcess = 0x09
                ##check if the json from cache or server has contents
                if ( len(g_FileManagerModule.c_cachedJson) ):
                    m_isSafeToProceed = True
                    g_lastKnownProcess = 0x0A
                
            except Exception as e:
                g_systemError = 'Error in getting the initial json data: %s%s' % (g_errProcessName, str(e.args))
                g_lastKnownProcess = 0x0B
                continue

    ##if needed components are successfully initialized proceed to main loop
    ##ADD CONDITION to refer to settings file for the time deviation if the server is not online
    g_FileManagerModule.calcTimeDeviation()
    g_lastKnownProcess = 0x0C
    g_FileManagerModule.arrangeMediaList(g_mediaDir)
    g_lastKnownProcess = 0x0D

    print('Downloading medias')
    g_FileManagerModule.downloadListOfMedia(g_mediaDir, 0) ##download all media from server instruction
    g_lastKnownProcess = 0x0E

    if g_FileManagerModule.isThereScheduledToPlayNow():
        g_MediaPanelModule.c_mediaResourceLocatorList = [g_mediaDir + g_FileManagerModule.c_scheduledToPlayNow]
        g_lastKnownProcess = 0x0F
    else:
        g_MediaPanelModule.c_mediaResourceLocatorList = g_FileManagerModule.c_mediaWithoutSched
        m_isWithoutSchedPlaying = True
        g_lastKnownProcess = 0x10

    print('\nAiring media and proceeding to routine')
    g_MediaPanelModule.startMediaListPlayer()
    g_lastKnownProcess = 0x11
    g_NetworkModule.c_isPersistentCheckingEnabled = True
    g_NetworkModule.startPersistentCheck()
    g_lastKnownProcess = 0x12
    
    ##Starting the main proceedure
    while (g_isSystemReady):
        
        ##This condition triggers when: Server was active, there was a new json instruction, c_json response was not empty
        if ( (g_NetworkModule.c_isServerActive) and
                (g_NetworkModule.c_jsonResponse['mediaFiles'] != g_FileManagerModule.c_cachedJson['mediaFiles']) and
                 len(g_NetworkModule.c_jsonResponse) ):
            
            ##Check if the server requests a change of media contents or
            ##issues an administrative commands
            
            g_lastKnownProcess = 0x13
            print('changes detected, copying the new instruction')
            g_MediaPanelModule.stop()   ##Stop the player as it will be restarted again later
            m_isWithoutSchedPlaying = False
            g_NetworkModule.c_isCheckingPaused = True ##Pause network checking
            g_lastKnownProcess = 0x14
            
            ##Copy new instruction and save to file
            ##THIS SAVE ALL THE JSON RESPONSE FROM THE SERVER
            g_FileManagerModule.c_cachedJson = g_NetworkModule.c_jsonResponse.copy()
            g_FileManagerModule.saveJson()
            g_lastKnownProcess = 0x15
            
            ##Clear out the space before downloading another set of media
            g_FileManagerModule.deleteAllMedia(g_mediaDir)
            g_FileManagerModule.downloadListOfMedia(g_mediaDir)
            g_FileManagerModule.arrangeMediaList(g_mediaDir)
            g_lastKnownProcess = 0x16
            
            g_NetworkModule.c_isCheckingPaused = False

        ##Play scheduled media files
        if ( g_FileManagerModule.isThereScheduledToPlayNow() and
                (g_MediaPanelModule.c_currentMedia != (g_mediaDir + g_FileManagerModule.c_scheduledToPlayNow)) ):
            g_lastKnownProcess = 0x17
            print('Playing scheduled media')
            g_MediaPanelModule.stop()
            m_isWithoutSchedPlaying = False
            g_MediaPanelModule.c_mediaResourceLocatorList = [g_mediaDir + g_FileManagerModule.c_scheduledToPlayNow]
            g_MediaPanelModule.startMediaListPlayer(p_isScheduled=True)
            g_lastKnownProcess = 0x18
            
        ##Play unscheduled media files
        elif ( (not m_isWithoutSchedPlaying) and (not g_FileManagerModule.isThereScheduledToPlayNow()) and
               len(g_FileManagerModule.c_mediaWithoutSched) ):
            g_lastKnownProcess = 0x19
            print('Playing unscheduled media list')
            g_MediaPanelModule.stop()
            g_MediaPanelModule.c_mediaResourceLocatorList = g_FileManagerModule.c_mediaWithoutSched
            m_isWithoutSchedPlaying = True
            g_MediaPanelModule.startMediaListPlayer()
            g_lastKnownProcess = 0x1A

    g_lastKnownProcess = 0x1B
    print('Main thread has ended')
    g_MediaPanelModule.stop()
    g_NetworkModule.c_isPersistentCheckingEnabled = False
    g_lastKnownProcess = 0x1C

if __name__ == '__main__':
    '''Start the system'''

    ##Start the system on threaded mode so that we can debug later
    g_lastKnownProcess = 0x1D
    g_mainThread = imThread (target = main)
    g_mainThread.start()
    print('Thread has started')
