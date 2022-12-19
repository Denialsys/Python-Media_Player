from socket import (
    socket as imSocket,
    AF_INET as imAF_INET,
    SOCK_DGRAM as imSOCK_DGRAM
)

from time import sleep as imDelay
from requests import get as imGetServerResponse
from threading import Thread as imThread
from uuid import getnode as imGetMac

class NetworkModule:
    '''Module for testing network communication and server availability
        @Usage: (On a project)
            import networkModule
            g_NetworkModule = networkModule.NetworkModule()
            g_NetworkModule.fetchCurrentIP()  ##Check if there was a network, acquire the assigned IP
            
            g_currentIP = g_NetworkModule.c_currentIP  ##Necessary
            g_NetworkModule.c_serverUrl = 'http://www.sampleserver.com' ##Necessary
            g_NetworkModule.c_requestParam = {'ipAddress' : g_currentIP}  ##Necessary
            
            g_NetworkModule.checkNetworkAndServer() ##this will fill up c_currentIP and c_isServerActive with values
            
        @Variable / Method prefixes:
            im -> Imported method
            c_ -> Class variable
            m_ -> Method variable
            t_ -> temporary variable
            __ -> methods to be used only by the class'''
    def __init__(self):
        '''Initialize variables'''
        ##Variables that will be assigned by the user program
        self.c_serverUrl = ''
        
        ##Variables for checking network and server
        self.c_isUsingSocket = False
        self.c_requestParam = None
        self.c_jsonResponse = {}
        self.c_macAddres = self.__getMacAddress()
        self.c_currentIP = None
        self.c_isServerActive = False
        self.c_isCheckingPaused = False
        
        ##Variables for assigning the network checking to a thread
        self.c_requestDelay = .5
        self.c_persistentChecking = None
        self.c_isPersistentCheckingEnabled = False
        
        self.c_lastError = ''
        
    def fetchCurrentIP(self):
        '''For testing the network connectivity check if the local machine
           have an ip address'''
        m_errProcessName = self.__class__.__name__ + 'fetchCurrentIP -> '
        
        try:
            m_socket = imSocket(imAF_INET, imSOCK_DGRAM)
            m_socket.connect(("8.8.8.8",80))
            self.c_currentIP = m_socket.getsockname()[0]
            m_socket.close()
        except OSError:
            self.c_lastError = 'No network connection'
        except Exception as e:
            self.c_lastError = 'Error in retrieving IP Address: %s%s' % (m_errProcessName,str(e.args))

    def fetchJsonFromServer(self):
        '''Get the json response from the server, at the same time checking
            if the server is online'''
        m_errProcessName = self.__class__.__name__ + 'fetchJsonFromServer -> '

        ##If no network yet,return to avoid wasting process
        if self.c_currentIP == None : return
        ##if the request parameter was empty fabricate one
        if self.c_requestParam == None: self.c_requestParam = {'ipAddress': self.c_currentIP, 'macAddress' : self.c_macAddres}
        
        try:
            self.c_jsonResponse = imGetServerResponse(url = self.c_serverUrl, params = self.c_requestParam, headers={'Connection': 'close'}).json()
            self.c_isServerActive = True
            
        except Exception as e:
            self.c_lastError = 'Unable to find the server: %s%s' % (m_errProcessName,str(e.args))
            self.c_isServerActive = False

    def __getMacAddress(self):
        '''(Private method)Issues the mac address of the machine network interface'''
        m_errProcessName = self.__class__.__name__ + '__getMacAddress -> '
        try: 
            return ':'.join(['{:02x}'.format((imGetMac() >> i) & 0xff) for i in range(0,8*6,8)][::-1]).upper()
        except Exception as e:
            self.c_lastError = 'Unable to get ip address: %s%s' % (m_errProcessName, str(e.args))
            return None

    def checkNetworkAndServer(self):
        '''Successively check the network and the server'''
        self.c_isUsingSocket = True
        self.fetchCurrentIP()
        self.fetchJsonFromServer()
        self.c_isUsingSocket = False
        imDelay(self.c_requestDelay) ##Delay before another request
        while(self.c_isCheckingPaused): pass ##Pause network and server check

    def __persistentCheck(self):
        '''(Private method)Continuously loop on checking the network and server
            this method will be used in multithreading'''
        print('Persisten network and server checking started')
        while(self.c_isPersistentCheckingEnabled):
            self.checkNetworkAndServer()
        print('Persisten network and server checking has stopped')
        
    def startPersistentCheck(self):
        '''Start a thread that will periodically check the network and server
            this method needs the c_isPersistentCheckingEnabled, c_serverUrl and c_requestParam
            to be initialized first'''
        self.c_persistentChecking = imThread(target = self.__persistentCheck)
        self.c_persistentChecking.start()
