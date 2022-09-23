"""
Created on Sep 24, 2013

@author: RandomHardcoreJerks

Requires pywin32


original: http://code.activestate.com/recipes/474121/
    # HtmlClipboard
    # An interface to the "HTML Format" clipboard data format
    
    __author__ = "Phillip Piper (jppx1[at]bigfoot.com)"
    __date__ = "2006-02-21"
    __version__ = "0.1"

"""

import re
import time
import random
import win32clipboard
import win32con

#---------------------------------------------------------------------------
#  Convenience functions to do the most common operation

def HasHtml():
    """
    Return True if there is a Html fragment in the clipboard..
    """
    cb = HtmlClipboard()
    return cb.HasHtmlFormat()


def GetHtml():
    """
    Return the Html fragment from the clipboard or None if there is no Html in the clipboard.
    """
    cb = HtmlClipboard()
    if cb.HasHtmlFormat():
        return cb.GetFragment()
    else:
        return None


def PutHtml(fragment, plain_text):
    """
    Put the given fragment into the clipboard.
    Convenience function to do the most common operation
    """
    cb = HtmlClipboard()
    cb.PutFragment(fragment, plain_text)


#---------------------------------------------------------------------------

class HtmlClipboard:

    CF_HTML = None
    
    startHtml_prefix = \
        "Version:1.0\r\n" \
        "StartHTML:%09d\r\n"

    MARKER_BLOCK_START_HTML = \
        "Version:(\S+)\s+" \
        "StartHTML:(\d+)\s+"
        
    START_HTML_RE = re.compile(MARKER_BLOCK_START_HTML)

    MARKER_BLOCK_LITE = \
        "Version:0.9\r\n" \
        "StartHTML:%09d\r\n" \
        "EndHTML:%09d\r\n" \
        "StartFragment:%09d\r\n" \
        "EndFragment:%09d\r\n" \
        "SourceURL:%s\r\n"
    MARKER_BLOCK = \
        "Version:(\S+)\s+" \
        "StartHTML:(\d+)\s+" \
        "EndHTML:(\d+)\s+" \
        "StartFragment:(\d+)\s+" \
        "EndFragment:(\d+)\s+" \
        "SourceURL:(\S+)"
    MARKER_BLOCK_RE = re.compile(MARKER_BLOCK)

    DEFAULT_HTML_BODY = \
        "<html><body><!--StartFragment-->%s<!--EndFragment--></body></html>"

    def __init__(self):
        self.html = None
        self.fragment = None
        self.source = None
        self.htmlClipboardVersion = None


    def GetCfHtml(self):
        """
        Return the FORMATID of the HTML format
        """
        if self.CF_HTML is None:
            self.CF_HTML = win32clipboard.RegisterClipboardFormat("HTML Format")

        return self.CF_HTML


    def GetAvailableFormats(self):
        """
        Return a possibly empty list of formats available on the clipboard
        """
        formats = []
        try:
            win32clipboard.OpenClipboard(0)
            cf = win32clipboard.EnumClipboardFormats(0)
            while (cf != 0):
                formats.append(cf)
                cf = win32clipboard.EnumClipboardFormats(cf)
        finally:
            win32clipboard.CloseClipboard()

        return formats


    def HasHtmlFormat(self):
        """
        Return a boolean indicating if the clipboard has data in HTML format
        """
        return (self.GetCfHtml() in self.GetAvailableFormats())


    def GetFromClipboard(self):
        """
        Read and decode the HTML from the clipboard
        """

        # implement fix from: http://teachthe.net/?p=1137

        cbOpened = False
        while not cbOpened:
            try:
                win32clipboard.OpenClipboard(0)
                src = win32clipboard.GetClipboardData(self.GetCfHtml())
                #print(src)
                self.DecodeClipboardSource(src)
                
                cbOpened = True

                win32clipboard.CloseClipboard()
            except Exception as err:
                print(e)
                # If access is denied, that means that the clipboard is in use.
                # Keep trying until it's available.
                if err.winerror == 5:  # Access Denied
                    pass
                    # wait on clipboard because something else has it. we're waiting a
                    # random amount of time before we try again so we don't collide again
                    time.sleep( random.random()/50 )
                elif err.winerror == 1418:  # doesn't have board open
                    pass
                elif err.winerror == 0:  # open failure
                    pass
                else:
                    print( 'ERROR in Clipboard section of readcomments: %s' % err)

                    pass        
        
    def DecodeClipboardSource(self, src):
        """
        Decode the given string to figure out the details of the HTML that's on the string
        """
        dummyPrefix = self.startHtml_prefix % (0)
        lenDummyPrefix = len(dummyPrefix.encode("UTF-8"))
        srcPrefix = src[0:lenDummyPrefix]
        srcPrefix = srcPrefix.decode("UTF-8")
        matches = self.START_HTML_RE.match(srcPrefix)
        startHtml = int(matches.group(2))
        
        srcMarker = src[0:startHtml]
        srcMarker = srcMarker.decode("UTF-8")
        
        #print("srcMarker:" +  srcMarker)
        # Try the extended format first (which has an explicit selection)
        matches = self.MARKER_BLOCK_RE.match(srcMarker)
        if matches:
            self.prefix = matches.group(0)
            self.htmlClipboardVersion = matches.group(1)
            startHtml = int(matches.group(2))
            endHtml = int(matches.group(3))
            startFrag = int(matches.group(4))
            endFrag = int(matches.group(5))
            
            self.html = src[startHtml:endHtml].decode("UTF-8")
            #print("html:" + self.html)
            self.fragment = src[startFrag:endFrag].decode("UTF-8")
            #print("fragment:" + self.fragment)
            self.source = matches.group(6)
        else:
            # Failing that, try the version without a selection
            print("no recogonizable clip data")


    def GetHtml(self, refresh=False):
        """
        Return the entire Html document
        """
        if not self.html or refresh:
            self.GetFromClipboard()
        return self.html


    def GetFragment(self, refresh=False):
        """
        Return the Html fragment. A fragment is well-formated HTML enclosing the selected text
        """
        if not self.fragment or refresh:
            self.GetFromClipboard()
        return self.fragment

    def GetSource(self, refresh=False):
        """
        Return the URL of the source of this HTML
        """
        if not self.selection or refresh:
            self.GetFromClipboard()
        return self.source


    def PutFragment(self, fragment, plain_text=None, html=None, source=None):
        """
        Put the given well-formed fragment of Html into the clipboard.
        """
        import re

        TAG_RE = re.compile(r'<[^>]+>')

        def remove_tags(text):
            return TAG_RE.sub('', text)
        
        if plain_text is None:
            plain_text = remove_tags(fragment)
        if html is None:
            html = self.DEFAULT_HTML_BODY % fragment
        if source is None:
            source = "file://HtmlClipboard.py"
            
        encoded_html = html.encode("UTF-8")
        encoded_fragment = fragment.encode("UTF-8")
        encoded_source = source.encode("UTF-8")

        fragmentStart = encoded_html.index(encoded_fragment)
        fragmentEnd = fragmentStart + len(encoded_fragment)
        self.PutToClipboard(html, len(encoded_html), fragmentStart, fragmentEnd, plain_text, source)


    def PutToClipboard(self, html, encoded_html_len, fragmentStart, fragmentEnd, plain_text, source="None"):
        """
        Replace the Clipboard contents with the given html information.
        """

        try:
            win32clipboard.OpenClipboard(0)
            win32clipboard.EmptyClipboard()

            win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, plain_text)
            src = self.EncodeClipboardSource(html, encoded_html_len, fragmentStart, fragmentEnd, source)
            src = src.encode("UTF-8")
            #print(src)
            win32clipboard.SetClipboardData(self.GetCfHtml(), src)
        finally:
            win32clipboard.CloseClipboard()


    def EncodeClipboardSource(self, html, encoded_html_len, fragmentStart, fragmentEnd, source):
        """
        Join all our bits of information into a string formatted as per the HTML format specs.
        """
        # How long is the prefix going to be?
        dummyPrefix = self.MARKER_BLOCK_LITE % (0, 0, 0, 0, source)
        lenPrefix = len(dummyPrefix.encode("UTF-8"))

        prefix = self.MARKER_BLOCK_LITE % (lenPrefix, encoded_html_len+lenPrefix,
                        fragmentStart+lenPrefix, fragmentEnd+lenPrefix,
                        source)
        return (prefix + html)


def DumpHtml():

    cb = HtmlClipboard()
    print("GetAvailableFormats()=%s" % str(cb.GetAvailableFormats()))
    print("HasHtmlFormat()=%s" % str(cb.HasHtmlFormat()))
    print(cb.GetCfHtml())
    if cb.HasHtmlFormat():
        cb.GetFromClipboard()
        print("prefix=>>>%s<<<END" % cb.prefix)
        print("htmlClipboardVersion=>>>%s<<<END" % cb.htmlClipboardVersion)
        print("GetFragment()=>>>%s<<<END" % cb.GetFragment())
        print("GetHtml()=>>>%s<<<END" % cb.GetHtml())
        print("GetSource()=>>>%s<<<END" % cb.GetSource())


if __name__ == '__main__':

    def test_SimpleGetPutHtml():
        data = "<p>Writing to the clipboard is <strong>easy</strong> with this code.</p>"
        PutHtml(data)
        if GetHtml() == data:
            print("passed")
        else:
            print("failed")

    test_SimpleGetPutHtml()
    #DumpHtml()
