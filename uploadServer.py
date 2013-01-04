#!/usr/bin/env python
"""
  Copyright 2013 Thomas McGrew <tjmcgrew@gmail.com>

  This program is free software: you can redistribute it and/or modify it under 
  the terms of the GNU Affero General Public License as published by the Free 
  Software Foundation, either version 3 of the License, or (at your option) any 
  later version.

  This program is distributed in the hope that it will be useful, but WITHOUT 
  ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS 
  FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more 
  details.

  You should have received a copy of the GNU Affero General Public License along 
  with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from SocketServer import ForkingMixIn
import os
import re
from cStringIO import StringIO
from optparse import OptionParser


UPLOAD_BUTTON = "uploadButton"
UPLOAD_FILE = "upload"

class ForkingServer(ForkingMixIn, HTTPServer):
  pass

class UploadHandler(BaseHTTPRequestHandler):
  upload_button = UPLOAD_BUTTON
  upload_file = UPLOAD_FILE

  def do_GET( self ):
    """
    Listens for a GET request and returns an upload form
    """
    self.rfile._sock.settimeout( 30 )
    self._parse_cookies( )
    self._preprocess_get( )
    self._send_get_response( )

  def do_POST( self ):
    """
    Reads a post request from a web browser and parses the variables.
    """
    self.rfile._sock.settimeout( 30 )
    self.remaining_content = int( self.headers[ 'Content-Length' ])
    self._parse_cookies( )
    self._preprocess_post( )
    self._read_post_data( )
    self._send_post_response( )

  def _parse_cookies( self ):
    # parse the cookies
    if self.headers.has_key( 'Cookie' ):
      cookie_pieces = re.split( "(.*?)=(.*?)(:?; |$)", self.headers['Cookie'] )
      self.cookies = dict( zip( cookie_pieces[1::4], cookie_pieces[2::4]))
    else:
      self.cookies = None
    return self.cookies

  def _read_post_data( self ):
    # read the separator token.
    token = self.rfile.readline( )
    self.remaining_content -= len(token)
    token = token.strip( )

    # read the post request
    self.buf = ''
    self.postdict = dict( )
    while self.remaining_content > 0 or len(self.buf):
      name, value_buffer = self._parse_post_item( token )
      if type( value_buffer ) is file:
        self.log_message( "Saved file %s", value_buffer.name )
        value = value_buffer.name
      else:
        value = value_buffer.getvalue( )

      if self.postdict.has_key( name ):
        if type(self.postdict[ name ]) is str:
          self.postdict[ name ] = [ self.postdict[ name ], value ]
        else:
          self.postdict[ name ].append( value )
      else:
        self.postdict[ name ] = value
      value_buffer.close( )
      if type( value_buffer ) is file:
        self._postprocess_upload( value )

  def _postprocess_upload( self, filename ):
    pass

  def _preprocess_get( self ):
    pass

  def _preprocess_post( self ):
    pass

  def _send_get_response( self ):
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
      </html>""" % ( OPTIONS.url, self.upload_file, self.upload_button ))


  def _send_post_response( self ):
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

    rtype: tuple
    return: A tuple containing the name of the variable and the buffer 
    containing it's value. This could either be a file object or a StringIO
    object.
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
      if os.sep in filename:
        filename = filename[ filename.rfind( os.sep ): ]

    while len(line.strip()):
      line = self._next_line( )

    if filename:
      if not os.path.exists( OPTIONS.upload_folder ):
        os.mkdir( OPTIONS.upload_folder )
      value_buffer = open( '%s/%s' % ( OPTIONS.upload_folder, filename), 'wb' )
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

    rtype: string
    return: The next line in the post data buffer
    """
    while self.remaining_content > 0 and not '\n' in self.buf :
      self.buf += self.rfile.read( 
        8192 if self.remaining_content > 8192 else self.remaining_content )
      self.remaining_content -= 8192
    line = self.buf[ :self.buf.find('\n') if '\n' in self.buf else len(self.buf)] 
    self.buf = self.buf[len(line)+1:]
    return line

def main( handler=UploadHandler ):
  global OPTIONS
  opts, args = optParser.parse_args( )
  OPTIONS = opts
  httpd = ForkingServer(( opts.address, opts.port ), handler )
  httpd.serve_forever( )

optParser = OptionParser( version="%prog 0.2", usage="%prog [options]" )
optParser.add_option( "-p", "--port",  dest="port", type="int", default=8000,
  help="Specify the port for the server to listen on" )
optParser.add_option( "-a", "--address", dest="address", default="",
  help="The ip address for the server to listen on" )
optParser.add_option( "-f", "--form-path", dest="url", default="/",
  help="The path to the upload form on the server. Useful if the server is"
       "behind a proxy" )
optParser.add_option( "-u", "--upload-location", dest="upload_folder", 
  default="/tmp", help="The location to store uploaded files" )


if __name__ == "__main__":
  main( ) 

