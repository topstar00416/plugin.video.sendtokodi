# -*- coding: utf-8 -*-
import json
import os
import sys
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

class replacement_stderr(sys.stderr.__class__):
    def isatty(self): return False

sys.stderr.__class__ = replacement_stderr

def debug(content):
    log(content, xbmc.LOGDEBUG)


def notice(content):
    log(content, xbmc.LOGNOTICE)


def log(msg, level=xbmc.LOGNOTICE):
    addon = xbmcaddon.Addon()
    addonID = addon.getAddonInfo('id')
    xbmc.log('%s: %s' % (addonID, msg), level)




from contextlib import closing
from xbmcvfs import File

# fixes python caching bug in youtube-dl
def patchYoutubeDL():
    
    toBePatched = """for expression in date_formats(day_first):
        try:
            upload_date = datetime.datetime.strptime(date_str, expression).strftime('%Y%m%d')
        except ValueError:
            pass
    if upload_date is None:""" # last line ensures we won't patch it repeatedly

    patch = """for expression in date_formats(day_first):
        try:
            upload_date = datetime.datetime.strptime(date_str, expression).strftime('%Y%m%d')
        except ValueError:
            pass
        except:
            pass
    if upload_date is None:""" # last line ensures we won't patch it repeatedly

    addonPath = xbmcaddon.Addon().getAddonInfo('path') 
    youtubeDlPath = addonPath + "/youtube_dl"
    utilsPyPath = youtubeDlPath + '/utils.py'

    # Borrowed from https://forum.kodi.tv/showthread.php?tid=315590
    with closing(File(utilsPyPath, 'r')) as fo:
	    fileData = fo.read()

    dataToWrite = fileData.replace(toBePatched, patch)

    with closing(File(utilsPyPath, 'w')) as fo:
	    fo.write(dataToWrite)

patchYoutubeDL()

from youtube_dl import YoutubeDL


def showInfoNotification(message):
    xbmcgui.Dialog().notification("SendToKodi", message, xbmcgui.NOTIFICATION_INFO, 5000)


def showErrorNotification(message):
    xbmcgui.Dialog().notification("SendToKodi", message,
                                  xbmcgui.NOTIFICATION_ERROR, 5000)


# Get the plugin url in plugin:// notation.
__url__ = sys.argv[0]
# Get the plugin handle as an integer number.
__handle__ = int(sys.argv[1])


def getParams():
    result = {}
    paramstring = sys.argv[2]
    additionalParamsIndex = paramstring.find(' ')
    if additionalParamsIndex == -1:
        result['url'] = paramstring[1:]
        result['ydlOpts'] = {}
    else:
        result['url'] = paramstring[1:additionalParamsIndex]
        additionalParamsString = paramstring[additionalParamsIndex:]
        additionalParams = json.loads(additionalParamsString)
        result['ydlOpts'] = additionalParams['ydlOpts']
    return result


def createListItemFromVideo(video):
    debug(video)
    url = video['url']
    thumbnail = video.get('thumbnail')
    title = video['title']
    list_item = xbmcgui.ListItem(title, path=url)
    list_item.setInfo(type='Video', infoLabels={'Title': title})

    if thumbnail is not None:
        list_item.setArt({'thumb': thumbnail})

    return list_item



ydl_opts = {
    'format': 'best'
}

params = getParams()
url = str(params['url'])
ydl_opts.update(params['ydlOpts'])
ydl = YoutubeDL(ydl_opts)
ydl.add_default_info_extractors()

with ydl:
    showInfoNotification("resolving stream(s) for " + url)
    result = ydl.extract_info(url, download=False)

if 'entries' in result:
    # Playlist
    pl = xbmc.PlayList(1)
    pl.clear()
    for video in result['entries']:
        list_item = createListItemFromVideo(video);
        xbmc.PlayList(1).add(list_item.getPath(), list_item)
    xbmc.Player().play(pl)
    showInfoNotification("playing playlist " + result['title'])
else:
    # Just a video, pass the item to the Kodi player.
    showInfoNotification("playing title " + result['title'])
    xbmcplugin.setResolvedUrl(__handle__, True, listitem=createListItemFromVideo(result))
