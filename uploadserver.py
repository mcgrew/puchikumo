#!/usr/bin/env python
"""
  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from SocketServer import ForkingMixIn
import os
import sys
import re
from cStringIO import StringIO
from optparse import OptionParser
import json
import random
import string
import mimetypes
from glob import glob
from time import ctime
from email.utils import formatdate
import math
from urllib import unquote_plus as unquote
import subprocess
from time import sleep
from collections import defaultdict

# stuff for ssl support
from SocketServer import BaseServer
import ssl
import socket


VERSION = "0.3.0"
UPLOAD_BUTTON = "uploadButton"
UPLOAD_FILE = "upload"

class ForkingServer(ForkingMixIn, HTTPServer):
  def __init__(self, address, handler):
    HTTPServer.__init__(self, address, handler)
    if (OPTIONS.certfile):
      cert = OPTIONS.certfile
      if (OPTIONS.keyfile):
        key = OPTIONS.keyfile
      else:
        key = OPTIONS.certfile
      BaseServer.__init__(self, address, handler)
      self.socket = ssl.SSLSocket(
        socket.socket(self.address_family,self.socket_type),
        keyfile = key,
        certfile = cert
      )
      self.server_bind()
      self.server_activate()

class UploadHandler(BaseHTTPRequestHandler):
  upload_button = UPLOAD_BUTTON
  upload_file = UPLOAD_FILE

  def do_HEAD(self):
    """
    Responds to a HEAD request.
    """
    if OPTIONS.download:
      self._file_request(self.path[1:], True)
      return

  def _start_session(self):
    """
    Starts a session by setting a session cookie.
    """
    if not self.cookies.has_key(OPTIONS.sessionkey):
      self._set_cookie(OPTIONS.sessionkey,
        ''.join(random.choice(string.ascii_uppercase + string.digits) 
        for i in range(32)))

  def _set_cookie(self, name, value, path='/'):
    """
    Sends a header to set a cookie.

    :Parameters:
      name : string
        The name or key for the cookie
      value : string
        The value for the cookie
      path : string (optional)
        The path setting for the cookie. Defaults to '/'
    """
    self.cookies[name] = value
    self.send_header('Set-Cookie', '%s=%s; Path=%s' % (name, value, path))

  def _parse_cookies(self):
    """
    Reads the cookie information sent from the client and places it in 
    the self.cookies dict. If no cookie information has been sent, this dict 
    will be empty (length of 0).
    """
    # parse the cookies
    if self.headers.has_key('Cookie'):
      cookie_pieces = re.split("(.*?)=(.*?)(:?; |$)", self.headers['Cookie'])
      self.cookies = dict(zip(cookie_pieces[1::4], cookie_pieces[2::4]))
    else:
      self.cookies = dict()
    return self.cookies

  def _read_get_data(self):
    """
    Parses the GET data from the url (The part after the '?').
    """
    self.query_string = ""
    self.getdict = defaultdict(bool)
    vars = self.path.split('?', 1)
    if len(vars) == 2:
      self.path = vars[0]
      self.query_string = vars[1]
      vars = vars[1].split('&')
      for var in vars:
        if '=' in var:
          thisvar = var.split('=', 1)
          self.getdict[thisvar[0]] = thisvar[1]
        else:
          self.getdict[var] = True

  def do_GET(self):
    """
    Listens for a GET request and returns an upload form
    """
    self.rfile._sock.settimeout(30)
    self._parse_cookies()
    self._read_get_data()
    self._preprocess_get()
    if OPTIONS.progress:
      if self.path == "/_progress": 
        # send the progres JSON feed
        self._progress()
        return
    if len(OPTIONS.cgi) and self.path.startswith('/_cgi_bin/'):
      self._run_cgi(self.path[10:], self.query_string)
      return
    self._send_get_response()

  def _run_cgi(self, path, args=""):
    """
    Executes a CGI file and writes it's output to the output stream. Errors are
    written to stdout for logging.

    :Parameters:
      path : string
        The path to the executable to be run.
      args : string (optional)
        The QUERY_STRING for the cgi script.
    """
    executable = os.path.join(OPTIONS.cgi, path)
    if not os.path.isfile(executable):
      self.send_error(404)
      return
    if not os.access(executable, os.X_OK):
      self.send_error(403)
      return
    cgi_env = dict(os.environ)
    cgi_env['QUERY_STRING'] = args
    print "Executing " + executable + " with query string " + args
    cgi = subprocess.Popen([executable,], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
      env=cgi_env)
    self.send_response(200)
    while cgi.poll() is None:
      sleep(0.1)
      self.wfile.write(cgi.stdout.read())
    self.wfile.write(cgi.stdout.read())
    print cgi.stderr.read()
    self.wfile.close()
    

  def _progress(self):
    """
    Responds to a progress request by reading the json file and sending it to
    the client.
    """
    if not OPTIONS.progress:
      self.send_error(403)
      return
    progressfilename = \
      os.sep.join([OPTIONS.tmp_folder, "progress", 
        self.cookies[OPTIONS.sessionkey]])
    if not os.path.exists(progressfilename):
      self.send_error(404)
      return

    self.send_response(200)
    self.send_header('Content-Type', 'application/json')
    self.send_header('Content-Length', 
      int(os.stat(progressfilename).st_size))
    # A futile attempt to stop caching in IE. Doesn't seem to work.
    self.send_header("Expires", formatdate(0, usegmt=True))
    self.send_header("Cache-Control", "max-age=0, no-cache, must-revalidate")
    self.send_header("Pragma", "no-cache")
    self.end_headers()
    progressfile = open(progressfilename, 'r')
    self.wfile.write(progressfile.read())
    progressfile.close()
    self.wfile.close()

  def _preprocess_get(self):
    """
    GET request pre-processing. By default this method does nothing, override
    it to perform some tasks before processing of the request.
    """
    pass

  def _send_get_response(self):
    """
    Responds to the GET request with the appropriate directory listing, file
    contents, or upload form.
    """
    if OPTIONS.download:
      self._file_request(self.path[1:])
    else:
      self.send_response(200)
      self.send_header('Content-Type', 'text/html')
      if OPTIONS.progress:
        self._start_session()
      self.end_headers()
      self.wfile.write("<!DOCTYPE html>\n<html><head></head><body>")
      self._upload_form()
      self.wfile.write("</body></html>")

  def _upload_form(self):
    """
    Sends the upload form to the client.
    """
    path = OPTIONS.url + (self.path[1:] if self.path[0]=='/' else self.path)
    if self.getdict['next']:
      path += '?next=' + self.getdict['next']
    self.wfile.write("""
          <form method="post" name="fileUpload" action="%s" 
          enctype="multipart/form-data">
          <input type="file" name="%s" multiple="true"/>
            <button id='upload' type="submit" name="%s" value="true">Upload file(s)</button>
          </form>
      """ % (path, self.upload_file, self.upload_button))

  def _file_request(self, path='/', head_only=False):
    """
    Responds to a file or directory request with the appropriate information.

    :Parameters:
      path : string
        The path to the file or directory listing to be sent.
      head_only : bool
        Whether to send the file data or merely the header information.
    """
    # user is requesting a file, send it.
    real_path = unquote(OPTIONS.upload_folder + '/' + path)
    if not os.path.exists(real_path):
      self.send_error(404)
      if OPTIONS.progress:
        self._start_session()
      return
        
    if os.path.isfile(real_path):
      self._send_file(real_path, head_only)
    if os.path.isdir(real_path):
      self._directory_listing(real_path, head_only)

  def _send_file(self, path, head_only=False):
    """
    Responds to a file request by the client by sending the file contents.

    :Parameters:
      path : string
        The path to the file to be sent.
      head_only : bool
        Whether to send the file data or merely the header information.
    """
    self.send_response(200)
    mimetype = mimetypes.guess_type(path)[0]
    stats = os.stat(path)
    if not mimetype:
      mimetype = 'text/plain'
    self.send_header('Content-Type', mimetype)
    self.send_header('Content-Length', stats.st_size)
    self.send_header('Last-Modified', formatdate(stats.st_mtime, usegmt=True))
    if OPTIONS.progress:
      self._start_session()
    self.end_headers()
    if not head_only:
      requested_file = open(path, 'r')
      self.wfile.write(requested_file.read())
      requested_file.close()
    self.wfile.close()
    return

  def _directory_listing(self, path, head_only=False):
    """
    Responds to a directory request with the directory listing.

    :Parameters:
      path : string
        The path to the directory listing to be sent.
      head_only : bool
        Whether to send the file data or merely the header information.
    """
    self.send_response(200)
    self.send_header('Content-Type', 'text/html')
    self.end_headers()
    # user requested a directory, list the files in it.
    file_list = glob(path + '/*')
    self.end_headers()
    if not head_only:
      self.wfile.write("<!DOCTYPE html><html><head></head><body>")
      relpath = os.path.relpath(path, OPTIONS.upload_folder)
      relpath = '/' if relpath == '.' else '/'+relpath 
      self.wfile.write("<h1>Directory listing for %s</h1><br>" % relpath)
      self.wfile.write("<table cellpadding='3'><tbody>")
      self.wfile.write(
        "<tr><th>Name</th><th>Size</th><th>Type</th><th>Last Modified</th></tr>")
      if path != '/':
        self.wfile.write(
          "<tr><td><a href='../'>Parent Directory</td><td colspan=3></td></tr>")
      # file size multipliers
      multipliers = ('%dB', '%dKB', '%dMB', '%dGB', '%sTB')
      for f in file_list:
        relpath = os.path.relpath(f, path)
        filetype = mimetypes.guess_type(path + f)[0]
        if not filetype:
          filetype = '-'
        stats = os.stat(f)
        file_size = self._get_file_size(f)
        if (file_size > 0):
          # magnitude of the file size
          size_mag = int(math.log(file_size, 1024)) if file_size else 0
          filesize_label = multipliers[size_mag] % (file_size >> (10 * size_mag))
        else:
          filesize_label = ''
        if os.path.isdir(f):
          relpath += '/'
          filetype = 'directory'
        self.wfile.write(
          "<tr><td><a href='%s'>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % 
          (relpath, relpath, filesize_label,
            filetype, ctime(stats.st_mtime))
        )
      self.wfile.write("</tbody></table>")
      self.wfile.write("<br><br>")
      self._upload_form()
      self.wfile.write("</body></html>")
      return

  def _get_file_size(self, path):
    """
    Determines the size of a file or directory.

    :Parameters:
      path : string
        The path to the file or directory to determine the size of.

    rtype: int
    return: The size of the file or directory.
    """
    try:
      if os.path.isdir(path):
        file_list = glob(path + '/*')
        dir_size = 0
        for f in file_list:
          dir_size += self._get_file_size(f)
        return dir_size
      else:
        return os.stat(path).st_size
    except:
      return 0

  def _init_progress(self):
    """
    Initilizes the progress json feed.
    """
    progressfilename = os.sep.join([OPTIONS.tmp_folder, "progress", 
        self.cookies[OPTIONS.sessionkey]])
    progressfile = open(progressfilename, 'w')
    progress = {'files':[], 'read': 0, 'total': self.content_length}
    progressfile.write(json.dumps(progress))
    progressfile.close()

  def _update_progress(self, current_transfer=None):
    """
    Adds uploaded files and current upload progress to a file for the JSON 
    progress feed.
    """
    # create a file with a different name and rename it. This should prevent the
    # progress feed thread from sending an incomplete file.
    progressfilename = os.sep.join([OPTIONS.tmp_folder, "progress", 
        self.cookies[OPTIONS.sessionkey]])
    progressfile = open(progressfilename + '~', 'w')
    progress = {'files': [os.path.basename(x) for x in self.postdict['files']], 
      'read': ((self.content_length - self.remaining_content)
        if self.remaining_content > 0 else self.content_length),
      'total': self.content_length}
    if current_transfer:
      progress['current'] = current_transfer
    progressfile.write(json.dumps(progress))
    progressfile.close()
    os.rename(progressfilename + '~', progressfilename)


  def do_POST(self):
    """
    Reads a post request from a web browser and parses the variables.
    """
    self.rfile._sock.settimeout(30)
    self.content_length = int(self.headers['Content-Length'])
    if (self.content_length < 0):
      self.content_length += 0x100000000
    self.remaining_content = self.content_length
    self._parse_cookies()
    self._read_get_data()
    self.upload_folder = OPTIONS.upload_folder
    if OPTIONS.progress:
      self._start_session()
      progressdir = os.sep.join([OPTIONS.tmp_folder, "progress"])
      if not os.path.exists(progressdir):
        os.makedirs(progressdir)
      # initalize the json feed to prevent the sending of an old file.
      self._init_progress()
    self._preprocess_post()
    self._read_post_data()
    self._send_post_response()

  def _read_post_data(self):
    """
    Parses the information in a POST request.
    """
    # read the separator token.
    token = self.rfile.readline()
    self.remaining_content -= len(token)
    token = token.strip()

    # read the post request
    self.readbuf = None
    self.writebuf = StringIO()
    self.postdict = defaultdict(bool)
    self.postdict['files'] = []
    while True:
      name, value_buffer = self._parse_post_item(token)
      if not value_buffer:
        return
      if type(value_buffer) is file:
        self.log_message("Saved file %s", value_buffer.name)
        value = value_buffer.name
        self.postdict['files'].append(value)
        if OPTIONS.progress:
          self._update_progress()
      else:
        value = value_buffer.getvalue()

      if self.postdict.has_key(name):
        if type(self.postdict[name]) is str:
          self.postdict[name] = [self.postdict[name], value]
        else:
          self.postdict[name].append(value)
      else:
        self.postdict[name] = value
      value_buffer.close()
      if type(value_buffer) is file:
        self._postprocess_upload(value)

  def _postprocess_upload(self, filename):
    """
    File upload post-processing. By defualt this method does nothing, override
    it if you would like to perform some operation on each file that is
    uploaded.

    :Parameters:
      filename : string
        The path to the file which has just completed uploading.
    """
    pass

  def _preprocess_post(self):
    """
    POST request pre-processing. By default this method does nothing, override
    it to perform some tasks before processing of the request.
    """
    pass

  def _redirect(self, where):
    """
    Redirects the user to the specified url. This may be a relative or absolute
    url.
    """
    self.send_response(301)
    if not where.startswith('http://') and not where.startswith('https://'):
      if self.headers.has_key('X-Forwarded-For'):
        host = self.headers['X-Forwarded-For'].split(',')[0]
      else:
        host = self.headers['Host']
      if OPTIONS.keyfile and OPTIONS.certfile:
        where = 'https://' + host + where
      else:
        where = 'http://' + host + where
    self.send_header('Location', where)
    self.end_headers()
    self.wfile.close()

  def _send_post_response(self):
    """
    Sends a post response after upload. This includes a redirect response if
    the user specified ?next=<where> in the post url.
    """
    if self.getdict['next']:
      return self._redirect(self.getdict['next'])
    self.send_response(200)
    if OPTIONS.progress:
      self._start_session()
    self.send_header('Content-Type', 'text/html')
    self.end_headers()
    self.wfile.write("<!DOCTYPE html><html><head></head><body>")
    self.wfile.write("Upload Complete")
    self.wfile.write("</body></html>")
    self.wfile.close()


  def _parse_post_item(self, token):
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
    line = self._next_line()
    nameheader = re.search('Content-Disposition: form-data; name="(.*?)"', line)
    if nameheader:
      name = nameheader.group(1)
    fileheader = re.search('filename="(.*?)"', line)
    if fileheader:
      filename = fileheader.group(1)
      if os.sep in filename:
        filename = filename[filename.rfind(os.sep):]

    while len(line.strip()):
      line = self._next_line()

    if filename:
      uploadpath = '%s%s' % (self.upload_folder, self.path)
      if not os.path.exists(uploadpath):
        os.makedirs(uploadpath) 
      value_buffer = open('%s%s/%s' % (self.upload_folder, self.path, filename), 'wb')
    else:
      value_buffer = StringIO()
    prev_line = False
    while not line.startswith(token):
      if self._finished():
        self._flush_write_buffer(None)
        return False, False
      line = self._next_line()
      if line.startswith(token):
        self.writebuf.write(prev_line[:-2])# strip the "^M\n" from the end
        break
      if not (prev_line is False):
        self.writebuf.write(prev_line)
      prev_line = line
      if OPTIONS.progress:
        # update the upload progress
        self._update_progress(filename)
      if self.writebuf.tell() > OPTIONS.writebuf:
        self._flush_write_buffer(value_buffer)
    self._flush_write_buffer(value_buffer)
    return (name, value_buffer)

  def _flush_write_buffer(self, outfile):
    """
    Clears the write buffer by flushing the buffer to the specified file.
    
    :Parameters:
      outfile : file
        An open file-like object to write to.
    """
    if outfile:
      outfile.write(self.writebuf.getvalue())
    self.writebuf.truncate(0)

  def _next_line(self):
    """
    Reads the next line of text from the post buffer and returns it.

    rtype: string
    return: The next line in the post data buffer
    """
    line = self.readbuf.readline() if self.readbuf else ''
    if not len(line):
      if self.remaining_content <= 0:
        self.readbuf = None;
      else:
        readsize = OPTIONS.readbuf if self.remaining_content > OPTIONS.readbuf \
          else self.remaining_content 
        self.readbuf = StringIO(self.rfile.read(readsize))
        self.remaining_content -= readsize
        line = self.readbuf.readline()
    if not line.endswith('\n') and not self._finished():
      line += self._next_line()
    return line

  def _finished(self):
    """
    Determines if we are done here (POST).
    """
    return self.remaining_content <= 0 and not self.readbuf

optParser = OptionParser(version="%%prog %s" % VERSION, usage="%prog [options]")
optParser.add_option("-a", "--address", dest="address", default="",
  help="The ip address for the server to listen on")
optParser.add_option("--read-buffer", dest="readbuf", type="int", default=8,
  help="Specify the buffer size for post request (in KB).")
optParser.add_option("--write-buffer", dest="writebuf", type="int", default=8,
  help="Specify the buffer size for post request (in KB).")
optParser.add_option("-f", "--form-url", dest="url", default="/",
  help="The path to the upload form on the server. Useful if the server is "
       "behind a proxy")
optParser.add_option("-p", "--port",  dest="port", type="int", default=8000,
  help="Specify the port for the server to listen on")
optParser.add_option("-u", "--upload-path", dest="upload_folder", 
  default="/tmp/uploads", help="The location to store uploaded files")
optParser.add_option("-t", "--tmp-path", default="/tmp", dest="tmp_folder",
  help="The location to store temporary files for the progress feed, etc.")
optParser.add_option("--enable-progress", action="store_true", 
  dest="progress", default=False,
  help="Enable JSON feed for monitoring upload progress")
optParser.add_option("--enable-download", action="store_true", 
  dest="download", default=False,
  help="Enable downloading of stored files")
optParser.add_option("--session-key", dest="sessionkey", 
  default="UploadSession",
  help="The name of the cookie to be used for identifying users")
optParser.add_option("--cgi-path", dest="cgi", default="",
  help="The path for cgi executables. By default cgi is disabled.")
optParser.add_option("--ssl-cert", dest="certfile", default="",
  help="The path for ssl certificate file. By default ssl is disabled.")
optParser.add_option("--ssl-key", dest="keyfile", default="",
  help="The path for ssl key file. By default ssl is disabled.")

def main(handler=UploadHandler):
  global OPTIONS
  sys.stderr.write("Starting with command: %s\n" % ' '.join(sys.argv))
  OPTIONS, args = optParser.parse_args()
  # convert buffer size to MB
  OPTIONS.readbuf *= 1048576
  OPTIONS.writebuf *= 1048576
  httpd = ForkingServer((OPTIONS.address, OPTIONS.port), handler)
  try:
    httpd.serve_forever()
  except KeyboardInterrupt:
    print
    print "Shutting down..."
    httpd.server_close()


if __name__ == "__main__":
  main() 

