#!/usr/bin/env python

from httpx import AsyncClient
import asyncio
import argparse
from urllib.parse import urlparse
from bs4 import BeautifulSoup

def init_arguments():
    parser = argparse.ArgumentParser(
        prog='File upload scanner',
        description='A tool to test valid extensions in file upload forms'
    )
    parser.add_argument("-t", "--target", help="The target host (http), include the url of the webpage containing the file upload form", required=True)
    parser.add_argument("-w", "--wordlist", help="Filename of a file containing a list of extensions to test", required=True)
    mode_parser = parser.add_subparsers(dest="validation")
    response = mode_parser.add_parser('response', help="Response code based upload validation, validate the upload based on the HTTP response")
    response.add_argument('-r', '--response', help="the response code used to validate the upload (200, 302, whatever is valid for you)", default=None, type=int)
    path = mode_parser.add_parser('path', help="Path based validation, validate by checking the path for the uploaded file")    
    path.add_argument("-p", "--path", help="the path of the upload directory, starting from / after the host's tld", default=None, type=str)
    parser.add_argument("-c", "--cookie", help="Cookies for session, if needed, in format key=value", required=False)

    args = parser.parse_args()

    match args.validation:
        case 'response':
            if not args.response:
                parser.error("You need to specify a response code if you want to use reponse based validation")
            return args.target, args.wordlist, args.validation, args.response, args.cookie

        case 'path':
            if not args.path:
                parser.error("You need to specify a path if you want to use path based validation")
            return args.target, args.wordlist, args.validation, args.path, args.cookie

async def get_form_parameters(form_url, client: AsyncClient):
    page = await client.get(form_url)
    soup = BeautifulSoup(page.text, "html.parser")
    form = soup.find("form", attrs={"method": "POST"})
    file_parameter = form.find("input")

def init_session(target, cookie) -> AsyncClient:
    if cookie:
        cookie_key = cookie.split("=")[0]
        cookie_value = cookie.split("=")[1]
        return AsyncClient(base_url=target, cookies={cookie_key: cookie_value})
    return AsyncClient(base_url=target)


async def main():

    target, wordlist_path, validation_mode, validator, cookie = init_arguments()
    parsed_url = urlparse(target)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    form_url = parsed_url.path
    
    client = init_session(base_url, cookie)
    await get_form_parameters(form_url, client)

    return

if __name__ == '__main__':
    asyncio.run(main())