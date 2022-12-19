'''Main program

Prefixes:

g_    :    Global variables
f_    :    Local variables
t_    :    Temporary variables
c_    :    Class variables

'''

print ('Initializing Components')
import networkModule

g_NetworkModule = networkModule.NetworkModule()
'''Make the program run before importing this'''

g_serverUrl = 'http://192.168.1.19:8080/SampleFileStream/TelevisionController'
g_NetworkModule.c_serverUrl = g_serverUrl
