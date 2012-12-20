#!/usr/bin/env python2
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from SocketServer import ForkingMixIn
import os
import re
from cStringIO import StringIO


UPLOAD_BUTTON = "uploadButton"
UPLOAD_FILE = "upload"
UPLOAD_FOLDER = "/tmp"
FORM_URL = "/"

def main( ):
  server_address = ('',8000)
  httpd = ThreadedServer( server_address, UploadHandler )
  httpd.serve_forever( )

class ThreadedServer(ForkingMixIn, HTTPServer):
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
            <button type="submit" name="%s" value="true">Upload</button>
          </form>
        </body>
      </html>""" % ( FORM_URL, UPLOAD_FILE, UPLOAD_BUTTON ))

  def do_POST( self ):
    """
    Reads a post request from a web browser and parses the variables.
    """

    #get the content of the separator line
    self.rfile._sock.settimeout( 30 )
    self.remaining_content = int( self.headers[ 'Content-Length' ])
    token = self.rfile.readline( )
    self.remaining_content -= len(token)
    token = token.strip( )
    print "Token: " + token

    # read the post request
    self.buf = ''
    self.postdict = dict( )
    while self.remaining_content > 0 or len(self.buf):
      name, value_buffer = self._parse_post_item( token )
      if type( value_buffer ) == file:
        print( "Saved file %s" % value_buffer.name )
        self.postdict[ name ] = value_buffer.name
      else:
        self.postdict[ name ] = value_buffer.getvalue( )
      value_buffer.close( )
    print( self.postdict )
    self.send_response( 200 )
    self.send_header( 'Content-Type', 'text/html' )
    self.end_headers( )
    self.wfile.write( "<!DOCTYPE html><html><head></head><body>" )
    self.wfile.write( repr( self.postdict ))
    self.wfile.write( "</body>" )
    self.wfile.close( )

  def _parse_post_item( self, token ):
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
    line = self._next_line( )
    nameheader = re.search( 
      'Content-Disposition: form-data; name="(.*?)"', line )
    if nameheader:
      name = nameheader.group(1)
    fileheader = re.search( 'filename="(.*?)"', line )
    if fileheader:
      filename = fileheader.group( 1 )
      if '/' in filename:
        filename = filename[ filename.rfind( '/'): ]

    while len(line.strip()):
      line = self._next_line( )

    if filename:
      value_buffer = open( '%s/%s' % ( UPLOAD_FOLDER, filename), 'wb' )
    else:
      value_buffer = StringIO( )
    prev_line = False
    while not line.startswith( token ):
      line = self._next_line( )
      if line.startswith( token ):
        value_buffer.write( prev_line[:-1] )# strip the extra ^M from the end
        break
      if not ( prev_line is False ):
        value_buffer.write( prev_line )
        value_buffer.write( '\n' )
      prev_line = line

    return ( name, value_buffer )

  def _next_line( self ):
    """
    Reads the next line of text from the post buffer and returns it.
    :Parameters:

    rtype: 
    return: 
    """
    while self.remaining_content > 0 and not '\n' in self.buf :
      self.buf += self.rfile.read( 
        8192 if self.remaining_content > 8192 else self.remaining_content )
      self.remaining_content -= 8192
    line = self.buf[ :self.buf.find('\n') if '\n' in self.buf else len(self.buf)] 
    self.buf = self.buf[len(line)+1:]
    return line


if __name__ == "__main__":
  main( )
