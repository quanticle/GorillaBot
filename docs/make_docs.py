# Copyright (c) 2013-2014 Molly White
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software
# and associated documentation files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or
# substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING
# BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from os import listdir
from os.path import isfile, join
import re
import requests
from secrets import *

command_regex = re.compile(r'((?:@command|@admin)\(.*?\)\ndef.*?)(?=@command|@admin|def |\Z)',
                           re.DOTALL)
parse_regex = re.compile(r'@(?P<type>command|admin)\((?P<aliases>.*?)\)\ndef (?P<command>\w+)'
                         r'\(.*?\):.*?(?P<docs>(?:\s+#-[^\n]*?\n)+)', re.DOTALL)
command_name_regex = re.compile(r'def (?P<command>\w+)')
whitespace_regex = re.compile(r' +#- ?')

def get_files():
    files = [join('../plugins', f) for f in listdir('../plugins') if isfile(join('../plugins', f))]
    admin_command_list = {}
    command_list = {}
    for file in files:
        with open(file, 'r', encoding='utf-8') as f:
            try:
                data = f.read()
            except UnicodeDecodeError as e:
                print(e)
            else:
                commands = re.findall(command_regex, data)
                for command in commands:
                    cmd_type, docs = parse_command(command)
                    if cmd_type == "admin":
                        admin_command_list[docs["command"]] = docs
                    elif cmd_type == "command":
                        command_list[docs["command"]] = docs
    format_docs(admin_command_list, command_list)

def parse_command(command):
    m = re.match(parse_regex, command)
    if m:
        docs = parse_docs(m.group('docs'))
        return m.group('type'),{"command": m.group('command'), "aliases": m.group(
            "aliases").replace('"', ''), "docs": docs}
    else:
        m = re.search(command_name_regex, command)
        if m:
            print("No documentation found for {}.".format(m.group('command')))
    return None, None

def parse_docs(docs):
    docs = docs.strip('\n')
    docs = re.sub(whitespace_regex, '', docs)
    return docs

def format_docs(admin, command):
    admin_keys = sorted(list(admin.keys()))
    command_keys = sorted(list(command.keys()))
    admin_docs = ""
    command_docs = ""
    for key in admin_keys:
        if admin[key]["aliases"] != "":
            admin_docs += "### {command}\nAliases: {aliases}\n\n{docs}\n\n".format(**admin[key])
        else:
            admin_docs += "### {command}\n\n{docs}\n\n".format(**admin[key])
    for key in command_keys:
        if command[key]["aliases"] != "":
            command_docs += "### {command}\nAliases: {aliases}\n\n{docs}\n\n".format(**command[key])
        else:
            command_docs += "### {command}\n\n{docs}\n\n".format(**command[key])
    write_docs(admin_docs, command_docs)

def write_docs(admin, command):
    with open('docs_template.md', 'r', encoding='utf-8') as f:
        template = f.read()
    headers = {'content-type': 'text/x-markdown',
               "User-Agent": "GorillaBot (https://github.com/molly/GorillaBot)"}
    resp = requests.post("https://api.github.com/markdown/raw",
                         data = format(template.format(commands=command, admincommands=admin)),
                         headers=headers)
    with open('../index.html', 'w', encoding='utf-8') as outfile:
        outfile.write(resp.text)

if __name__ == "__main__":
    get_files()