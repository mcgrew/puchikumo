#!/usr/bin/env python2
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from SocketServer import ThreadingMixIn
import os
import re


UPLOAD_BUTTON = "uploadButton"
UPLOAD_FILE = "upload"
UPLOAD_FOLDER = "folder"
FORM_URL = "/"

def main( ):
  server_address = ('',8000)
  httpd = HTTPServer( server_address, UploadHandler )
  httpd.serve_forever( )

class ThreadedServer(HTTPServer,ThreadingMixIn):
  pass

class UploadHandler(BaseHTTPRequestHandler):

  def do_GET( self ):
    """
    Listens for a GET request and returns an upload form
    """
    self.send_response( 200 )
    self.send_header( 'Content-Type', 'text/html' )
    self.end_headers( )
    self.wfile.write( """<!DOCTYPE html>
      <html>
        <head>
        </head>
        <body>
          <form method="post" name="fileUpload" action="%s" 
          enctype="multipart/form-data">
            <input type="file" name="%s" multiple="true"/><br />
            <input type="text" name="%s" /><br />
            <button type="submit" name="%s" value="true">Upload</button>
          </form>
        </body>
      </html>""" % ( FORM_URL, UPLOAD_FILE, UPLOAD_FOLDER, UPLOAD_BUTTON ))

  def do_POST( self ):
    """
    Reads a post request from a web browser and parses the variables.
    """
    self.rfile._sock.settimeout( 30 )
    self.send_response( 200 )
    self.send_header( 'Content-Type', 'text/html' )
    self.end_headers( )
    byteCount = 0
    self.tmpFile = open('/home/mcgrew/garbage', 'wb')

    #get the content of the separator line
    content_length = int( self.headers[ 'Content-Length' ])
    token = self.rfile.readline( )
    content_length -= len(token)
    token = token.strip( )
    print "Token: " + token

    # read the post request
    buf = ''
    self.wfile.write( "<!DOCTYPE html><html><head></head><body>" )
    while content_length > 0 or len(buf):
      name, filename, value, content_length, buf = \
        self._parse_post_item( token, content_length, buf )
      if filename:
        print( "Saving file %s" % filename )
        f = open( '/tmp/%s'% filename, 'wb' )
        f.write( value )
        f.close( )
        self.wfile.write( "<p>Saved file %s</p>" % filename )
    self.wfile.write( "</body>" )
    self.wfile.close( )

  def _parse_post_item( self, token, content_length, buf ):
    """
    Parses out a single item from a post request.

    :Parameters:
      token : string
        The separator token for each post variable
      content_length
        The remaining content in the stream

    rtype: tuple
    return: A tuple containing the name of the variable, filename if applicable,
      value of the variable (or the temporary filename if it is a file), and
      the remaining content length in the stream.
    """
    name = None
    filename = None
    buf, content_length, line = self._next_line( buf, content_length )
    nameheader = re.search( 
      'Content-Disposition: form-data; name="(.*?)"', line )
    if nameheader:
      name = nameheader.group(1)
    if name == UPLOAD_FILE:
      fileheader = re.search( 'filename="(.*?)"', line )
      if fileheader:
        filename = fileheader.group( 1 )

    while len(line.strip()):
      buf, content_length, line = self._next_line( buf, content_length )
      print( line )

    value = ''
    prev_line = False
    while not line.startswith( token ):
      buf, content_length, line = self._next_line( buf, content_length )
      if line.startswith( token ):
        value += prev_line[:-1] # strip the extra ^M from the end
        break
      if not ( prev_line is False ):
        value += prev_line + '\n' 
      prev_line = line

    return ( name, filename, value, content_length, buf )

  def _next_line( self, buf, content_length ):
    """
    Reads the next line of text from the post buffer and returns it.
    :Parameters:

    rtype: 
    return: 
    """
    while content_length > 0 and not '\n' in buf :
      buf += self.rfile.read( 8192 if content_length > 8192 else content_length)
      content_length -= 8192
    line = buf[ :buf.find('\n') if '\n' in buf else len(buf)] 
    buf = buf[len(line)+1:]
    return ( buf, content_length, line )


if __name__ == "__main__":
  main( )
