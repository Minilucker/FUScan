#!/usr/bin/env python

from httpx import AsyncClient
import asyncio
import argparse
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from rich import print
from rich.progress import track 

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
    input_list = form.find_all("input")
    upload_path = form.get("action")
    parameters_list = []
    for parameter in input_list:
        param = {"type": parameter.get('type'),"name": parameter.get('name')}
        parameters_list.append(param)
    return parameters_list, upload_path

    

def init_session(target, cookie) -> AsyncClient:
    if cookie:
        cookie_key = cookie.split("=")[0]
        cookie_value = cookie.split("=")[1]
        return AsyncClient(base_url=target, cookies={cookie_key: cookie_value})
    return AsyncClient(base_url=target)

async def validate(validator, client, results: list):
    if not type(results) == dict:
        success_list = list()
        for ext in track(results, description="[white]Fuzzing the resulting file ..."):
            response = await client.get(f"{validator}/file{ext}")
            if response.status_code == 200:
                success_list.append(ext)
        return success_list

    else:
        for codematch in results:
            valid_extensions = list()
            if (codematch.get("code") == validator):
                valid_extensions.append(codematch.get("ext"))
        return valid_extensions


async def send_probes(wordlist, parameters, upload_path, client: AsyncClient):
    data = dict()
    for parameter in parameters:
        if parameter.get("type") == "file":
            fileParam = parameter.get("name")
            parameters.remove(parameter)
            continue
        data[parameter.get('name')] = "dummy"
    wl = open(wordlist, 'r').readlines()
    code_results = list()
    for ext in track(wl, description="[white]Fuzzing file upload form ..."):
        ext = ext.strip()
        file ={fileParam: (f'file{ext}', open('dummyfile', 'rb'))}
        resp = await client.post(upload_path, files=file, data=data)
        
        code_results.append({"ext": ext, "code": resp.status_code})
    return code_results

async def main():

    target, wordlist_path, validation_mode, validator, cookie = init_arguments()
    parsed_url = urlparse(target)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    form_url = parsed_url.path
    
    client = init_session(base_url, cookie)
    secondary_params, upload_path = await get_form_parameters(form_url, client)
    results = await send_probes(wordlist_path, secondary_params, upload_path, client)
    match validation_mode:
        case "response":
            successful_ext = await validate(validator=results, client=client, results=results)
        case "path":
            results = list(map(lambda dict: dict.pop('ext', None), results))
            successful_ext = await validate(validator=validator, client=client, results=results)
    print()
    if len(successful_ext) == 0:
        print("[red][-] No valid extension found")
    for success in successful_ext:
        print(f"[green][+] Valid extension found : {success}[/green]")

if __name__ == '__main__':
    asyncio.run(main())