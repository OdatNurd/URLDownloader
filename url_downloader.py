import sublime
import sublime_plugin

import os
import re
import urllib
import tempfile
import textwrap
import ssl, certifi


# Portions of this code are based on the Default/open_context_url.py plugin
# which ships with Sublime, although some functional changes and rearrangements
# have been made.

rex = re.compile(
    r'''(?x)
    \b(?:
        https?://(?:(?:[\w\d\-]+(?:\.[\w\d\-.]+)+)|localhost)|  # http://
        www\.[\w\d\-]+(?:\.[\w\d\-.]+)+                         # www.
    )
    /?[\w\d\-.?,!'(){}\[\]/+&@%$#=:"|~;]*                       # url path and query string
    [\w\d\-~:/#@$*+=]                                           # allowed end chars
    ''')


def get_url(view, pt):
    """
    Given a point in the file, return back the URL held there, or None if there
    is not one.
    """
    line = view.line(pt)

    line.a = max(line.a, pt - 1024)
    line.b = min(line.b, pt + 1024)

    text = view.substr(line)

    for match in rex.finditer(text):
        if match.start() <= (pt - line.a) and match.end() >= (pt - line.a):
            url = text[match.start():match.end()]
            return url

    return None


def get_temp_filename(url):
    """
    Given a URL, get the temporary file's stub name and extension. If the URL
    has no filename portion, we assume that it will be index.html; is there
    some other sensible default?
    """
    path = urllib.parse.urlparse(url).path
    name = 'index.html' if path in ('', '/') else os.path.basename(path)

    return os.path.splitext(name)


class UrlDownloadContextCommand(sublime_plugin.TextCommand):
    """
    Modified version of OpenContextUrlCommand from Default/open_context_url.py.

    If the text under the cursor looks like a URL, execute the download command
    with it. Optionally this can also treat the selected text as a URL.
    """
    def run(self, edit, event=None):
        url = self.find_url(event)
        self.view.window().run_command('url_download', {'url': url})

    def is_visible(self, event=None):
        return self.find_url(event) is not None

    def is_enabled(self, event=None):
        return self.is_visible(event)

    def find_url(self, event):
        # If there is any selected text, use it as the URL to open, but only
        # when the open selection setting is turned on.
        s = sublime.load_settings('URLDownloader.sublime-settings')
        if s.get('open_selection', False) and not self.view.sel()[0].empty():
            return self.view.substr(self.view.sel()[0])

        # get the point to look for a URL at. This is the the cursor location
        # unless the command was invoked via a context menu action.
        pt = self.view.sel()[0].b
        if event is not None:
            pt = self.view.window_to_text((event["x"], event["y"]))

        return get_url(self.view, pt)

    def description(self, event):
        url = self.find_url(event)
        if len(url) > 64:
            url = url[0:64] + "..."
        return "Download and open " + url

    def want_event(self):
        return True


class UrlInputHandler(sublime_plugin.TextInputHandler):
    """
    Simple input handlers for gathering URL's to open; changes the placeholder
    """
    def __init__(self, previous_url):
        self.previous_url = previous_url or ''

    def placeholder(self):
        return 'URL to Download'

    def initial_text(self):
        return self.previous_url


class UrlDownloadCommand(sublime_plugin.WindowCommand):
    """
    Given a URL, attempt to download it and open it in a new tab. If no URL is
    given, prompt in the command palette for one.
    """
    previous_url = None

    def run(self, url):
        if not url.startswith('http') and not url.startswith('file'):
            s = sublime.load_settings('URLDownloader.sublime-settings')
            url = s.get('default_protocol', 'http://') + url

        self.previous_url = url
        sublime.set_timeout_async(lambda: self.open_url(url), 0)

    def open_url(self, url):
        try:
            self.window.status_message(f'Downloading: {url}')

            # Open the URL and get a stream to the contents
            context = ssl.create_default_context(cafile=certifi.where())
            stream = urllib.request.urlopen(url, context=context)

            # Create a temporary file and store the file content into it
            prefix,ext = get_temp_filename(url)

            fd, base_name = tempfile.mkstemp(prefix=prefix + "_", suffix=ext)
            os.write(fd, stream.read())
            os.close(fd)

            page_view = self.window.open_file(base_name)
            page_view.settings().set("_tmp_url", url)

            s = sublime.load_settings('URLDownloader.sublime-settings')
            if s.get('show_url', False):
                page_view.set_status('url', f'[URL: {url}]')

        except urllib.error.HTTPError as err:
            self.show_error(url, err)
        except urllib.error.URLError as err:
            self.show_error(url, err.reason)
        except urllib.error.ContentTooShortError:
            self.show_error(url, 'The server sent only a partial response')
        except BaseException as err:
            self.show_error(url, err)

    def show_error(self, url, err):
        sublime.error_message(
            textwrap.dedent(f"""
            Error while downloding:
            {url}:

            {err}
            """).lstrip())


    def input_description(self):
        return 'Download and open'

    def input(self, args):
        if 'url' not in args:
            return UrlInputHandler(self.previous_url)


class TemporaryDownloadEventListener(sublime_plugin.ViewEventListener):
    @classmethod
    def is_applicable(cls, settings):
        return settings.has('_tmp_url')

    def on_pre_save(self):
        self.view.erase_status('url')
        self.view.settings().erase('_tmp_url')

    def on_close(self):
        try:
            if os.path.exists(self.view.file_name()):
                os.remove(self.view.file_name())
                print('clobbered')
        except:
            pass
