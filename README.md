URLDownloader
=============

This is a simple example package that allows you to easily download the
contents of any web URL to edit locally. Given a URL, the package will download
the resulting file to your computer's temporary directory and then open the
file.

The temporary file will be deleted when the tab is closed, unless you first
`save` or `save as` the contents to another file.

The opened file will display the URL that it was downloaded from in the status
bar as a reminder of where it came from; this can be adjusted in the settings
if desired.

This example was created in response to a question on my
[YouTube Channel](https://youtube.com/c/odatnurd).


## Usage

There are a few ways to trigger the package:

1. The `URLDownloader: Download and open URL` command in the command palette
   will allow you to manually enter any URL you like

2. Right click (or your system's equivalent) on a URL in a file to select and
   open it.

3. Via a key binding; there is not one by default, but there is an example in
   the package key bindings file. Use `Preferences > Package Settings > URLDownloader`
   to see it.


## Settings

The package currently supports the following settings:

* `open_selection` (`true`): When this is `true`, any selected text will be
  treated as the URL to open, falling back to just using the URL under the
  cursor if no text is selected. When this is `false`, the selection is ignored
  and the URL always needs to be under the cursor.

* `show_url` (`true`): When this is `true`, any downloaded files that are opened
  will show the URL that they were downloaded from in the status bar of the
  window. `false` will disable this. Note that when downloading images, this
  setting has no effect because images are not editable and thus don't support
  custom status bar text.

* `default_protocol` (`http://`): For any URL that does not have a protocol on
  it, this is the default protocol to be used. Set it to `https://` to default
  to secure connections.