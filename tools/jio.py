"""Studio-shaped JSON writer: 2-space indent, CRLF line ends, no ASCII escaping, no trailing newline.
(Header.json / Properties.json are compact and are written by their own scripts.)"""
import json


def jdump(doc):
    return json.dumps(doc, indent=2, ensure_ascii=False).replace('\n', '\r\n')


def jwrite(doc, path):
    with open(path, 'wb') as f:
        f.write(jdump(doc).encode('utf-8'))
