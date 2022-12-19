import vlc
from os import path as imPath
from time import time as imTime
from threading import Thread as imThread

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
gi.require_version('GdkX11', '3.0')
from gi.repository import GdkX11

class MediaPanelModule(Gtk.Window):
    '''Creates a gui panel that will encapsulate the media player so playing and
        stoping the media will not make the scree flicker simplified version of
        media player handler

        @Precaution:
            If a media was to be deleted while the media player was still playing
            please use:

                g_MediaPanel.stop()

            to ensure the file deletion will not throw file handle error

        @Usage: (On a project)
            import mediaPanelModule
            g_MediaPanel = mediaPanelModule.MediaPanelModule()
            g_MediaPanel.show_all()
            ##You can use this module to play just one media by:
            g_MediaPanel.playMedia('Exact/media/directory/MediaFile.mp4')
            
            ##Or just queue up a list of media to play then start the thread
            g_MediaPanel.c_mediaResourceLocatorList = videoList ##Necessary to add playlist for the media player
            g_MediaPanel.c_isMediaListPlayerOn = True ##Necessary to enable the thread that will play the media
            g_MediaPanel.startMediaListPlayer()
        
        @Supported video formats:
            -MP4
            -MOV
            -AVI
            
        @Supported image formats:
            -JPG
            -PNG

        @Variable / Method prefixes:
            im -> Imported method
            c_ -> Class variable
            m_ -> Method variable
            t_ -> temporary variable
            __ -> methods to be used only by the class'''

    def __init__(self):
        '''Pre initialize the needed component
            @Params:
            -p_isPlaybackEnabled -> enables sequencial playing of medias in the list
            -p_imageDisplayTime -> default number of seconds to display an image media'''
        
        Gtk.Window.__init__(self)
        self.fullscreen()
        self.connect("destroy",Gtk.main_quit)
        
        ##To make the media panel the size of the screen
        self.__c_screenHeight = Gtk.Window().get_screen().get_height()
        self.__c_screenWidth = Gtk.Window().get_screen().get_width()

        ##Variables for media player
        self.c_currentMedia = None
        self.c_mediaPlayer = None
        self.c_airedStampTime = 0
        self.c_isMediaEndReached = True

        ##Variables for media list player
        self.c_mediaListPlayerThread = None
        self.c_isMediaListPlayerOn = False
        self.c_mediaIndex = 0
        self.c_scheduledMediaIndex = 0  ##Not implemented yet
        self.c_mediaResourceLocatorList = []
        
        ##Sets up the instance of the gui as well as the media player and its events
        self.c_videoPanel = Gtk.DrawingArea()
        self.c_videoPanel.set_size_request(self.__c_screenWidth, self.__c_screenHeight)
        self.c_videoPanel.connect("realize",self.__realized)
        self.vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(self.vbox)
        self.vbox.pack_start(self.c_videoPanel, True, True, 0)
        
        self.c_lastError = ''
        
    def __realized(self, p_widget, data=None):
        '''Creates the media player instance in the draw area of the gui
        @Vlc instance params:
        --no-xlib -> please check the documentations
        --avcodec-threads -> sets the number of threads for decoding the video
        --sout-avcodec-hurry-up -> set the encoder to make on-the-fly quality trade
                        offs if the cpu cant keep up with the rate'''
        
        ##create a media player instance and attach it to gui panel
        m_windowID = p_widget.get_window().get_xid()
        self.c_vlcInstance = vlc.Instance("--no-xlib --avcodec-threads=3 --sout-avcodec-hurry-up")
        self.c_mediaPlayer = self.c_vlcInstance.media_player_new()
        self.c_mediaPlayer.set_xwindow(m_windowID)
        
        ##Set up an event listener, call a function on event
        self.c_mediaPlayerEndWatcher = self.c_mediaPlayer.event_manager()
        self.c_mediaPlayerEndWatcher.event_attach(vlc.EventType().MediaPlayerEndReached, self.__setMediaEndReached)
    
    ##========================>>
    ##Media player instructions
    ##========================>>
    def playMediaList(self, p_isScheduled):
        '''Play / loop over a list of media files, does nothing if media playing is not enabled'''
        print('Media playlist thread has started')

        ##start the playing of media list if switch is on and media list is not empty
        while(self.c_isMediaListPlayerOn and len(self.c_mediaResourceLocatorList)):
            
            ##Check first if the previously played media has ended
            if (self.c_isMediaEndReached):
                if (p_isScheduled):
##                    print('\nPlaying scheduled media in %s' % (self.c_mediaResourceLocatorList[0]) )
                    self.playMedia(self.c_mediaResourceLocatorList[0])
                else:
##                    print('\nPlaying unscheduled media in %s' % (self.c_mediaResourceLocatorList[self.c_mediaIndex]) )
                    self.playMedia(self.c_mediaResourceLocatorList[self.c_mediaIndex])
                    self.c_mediaIndex = (self.c_mediaIndex + 1) % len(self.c_mediaResourceLocatorList)
             
        print('Media playlist thread has stopped')

    def startMediaListPlayer(self, p_isScheduled=False):
        '''Starts the media list player in threaded mode
            @Params
                p_isScheduled -> '''
        self.c_isMediaListPlayerOn = True
        self.c_mediaListPlayerThread = imThread (target = self.playMediaList, args=(p_isScheduled,))
        self.c_mediaListPlayerThread.start()
        while(self.c_mediaPlayer.get_state() != vlc.State.Playing): continue
            
    def playMedia(self, p_mediaResourceLocator):
        '''Play a single a media only, checks first if the file exist, if not do nothing
            if already playing media, stop then play the new media'''
        if imPath.isfile(p_mediaResourceLocator):
            if ( not self.c_isMediaEndReached ) : self.stop()
            self.c_mediaPlayer.set_mrl(p_mediaResourceLocator)
            self.c_currentMedia = p_mediaResourceLocator
            self.c_mediaPlayer.play()
            self.c_airedStampTime = int(imTime())
            self.c_isMediaEndReached = False
        else:
            self.c_lastError = 'File in (' + p_mediaResourceLocator + ') does not exist yet'

    def play(self):
        self.c_isMediaEndReached = False
        self.c_mediaPlayer.play()

    def pause(self):
        self.c_mediaPlayer.pause()

    def stop(self):
        self.c_isMediaListPlayerOn = False
        self.c_airedStampTime = 0
        self.c_mediaPlayer.stop()
        self.c_isMediaEndReached = True

    def __setMediaEndReached(self, p_event):
        '''Indicate that the end of the media was reached
            this is a lot faster than getting the state of the media player'''
        self.c_isMediaEndReached = True

    def getAiredTime(self):
        '''Returns the number of seconds a media was played'''
        if self.c_airedStampTime != 0:
            return int(imTime()) - self.c_airedStampTime
        else:
            return 0
    ##========================<<
    ##Media player instructions
    ##========================<<
