# FUScan

"Simple" Python script to check which extension is accepted by a HTML file upload form.

```
usage: File upload scanner [-h] -t TARGET -w WORDLIST [-c COOKIE]
                           {response,path} ...

A tool to test valid extensions in file upload forms

positional arguments:
  {response,path}
    response            Response code based upload validation, validate the upload
                        based on the HTTP response
    path                Path based validation, validate by checking the path for the
                        uploaded file

options:
  -h, --help            show this help message and exit
  -t TARGET, --target TARGET
                        The target host (http), include the url of the webpage
                        containing the file upload form
  -w WORDLIST, --wordlist WORDLIST
                        Filename of a file containing a list of extensions to test
  -c COOKIE, --cookie COOKIE
                        Cookies for session, if needed, in format key=value
```