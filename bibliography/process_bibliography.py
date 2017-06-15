# -*- coding: utf-8 -*-
"""
Created on Tue Jun 13 18:52:00 2017

@author: Jonathan Gilligan
"""
# import pybtex as pt
import pybtex.database as ptd
import yaml
import os
import glob
import shutil
import re
import cgi

def preprocess(infile, outfile):
    original = open(infile)
    modified = open(outfile, 'w')
    lines = original.readlines()
    lines = [ re.sub('^( *)[Aa]uthor\\+[Aa][Nn]', '\\1author_an', li) for li in lines ]
    modified.writelines(lines)

def call_citeproc(source, target):
    os.system('pandoc-citeproc -y ' + source + ' > ' + target)

file_expr = re.compile('^(?P<desc>[^:]*):(?P<path>[^:]+)[\\\\/](?P<file>[^:/\\\\]+):(?P<type>[^:;]*)$')

def extract_file_link(filestr):
    files = filestr.split(';')
    matches = [file_expr.match(s) for s in files ]
    # d = dict([(m.group('desc'), m.group('file')) for m in matches])
    d = [ {'desc':m.group('desc'), 'file': m.group('file')} for m in matches]
    return d

def merge(bitem, yitem):
    fields = ['file', 'title_md', 'booktitle_md', 'note_md']

    for f in fields:
        if f in bitem.fields.keys():
            s = str(bitem.fields[f])
            if f == 'file':
                yitem[f] = extract_file_link(s)
            else:
                yitem[f] = s
    return yitem

def process_item(bitem, yitem):
    yitem = merge(bitem, yitem)
    return yitem

def gen_refs(bibfile):
    target = os.path.splitext(os.path.split(bibfile)[1])[0] + '.yml'
    call_citeproc(bibfile, target)

    bib = ptd.parse_file(bibfile)
    ybib = yaml.load(open(target))

    for yitem in ybib['references']:
        bitem = bib.entries.get(yitem['id'])
        yitem = merge(bitem, yitem)

    yaml.dump(ybib, open('publications.yml', 'w'))
    return ybib

clean_expr = re.compile('[^a-zA-z0-9]+')

def gen_items(bib):
    output_keys = ['title', 'author', 'short_author',
                   'container-title', 'collection-title',
                   'editor', 'short_editor',
                   'publisher-place', 'publisher',
                   'genre', 'status',
                   'volume', 'issue', 'page', 'number',
                   'ISBN', 'DOI', # 'URL',
                   'issued',
                   'keyword',
                   'note',
                   'file'
                   ]
    if not os.path.exists('content'):
        os.mkdir('content')
    for item in bib:
        key = clean_expr.sub('_', item['id'])
        if 'author' in item.keys():
            item['short_author'] = [ {'family':n['family'], 'given':re.sub('\\b([A-Z])[a-z][a-z]+\\b', '\\1.', n['given'])} for n in item['author'] ]
        if 'editor' in item.keys():
            item['short_editor'] = [ {'family':n['family'], 'given':re.sub('\\b([A-Z])[a-z][a-z]+\\b', '\\1.', n['given'])} for n in item['editor'] ]
        header_items = dict([(k, v) for (k, v) in item.items() if k in output_keys])
        header_items['id'] = key
        dd = header_items['issued'][0]
        y = int(dd['year'])
        m = 1
        d = 1
        if 'month' in dd.keys():
            m = int(dd['month'])
        if 'day' in dd.keys():
            d = int(dd['day'])
        header_items['date'] = ("%04d-%02d-%02d" % (y, m, d))
        if 'URL' in item.keys():
            header_items['pub_url'] = item['URL']
        header_items['pub_type'] = item['type']
        outfile = open(os.path.join('content', key + '.md'), 'w')
        outfile.write('---\n')
        yaml.dump(header_items, outfile)
        outfile.write('---\n')
        abstract = None
        if 'abstract_md' in item.keys():
            abstract = item['abstract_md']
        elif 'abstract' in item.keys():
            abstract = item['abstract']
        if abstract is not None:
            abstract = cgi.escape(abstract).encode('ascii', 'xmlcharrefreplace')
            outfile.write(abstract + '\n')
        outfile.close()

def move_md_files(src = 'content', dest = '../content/publications'):
    files = glob.glob(os.path.join(src, '*.md'))
    if not os.path.isdir(dest):
        os.makedirs(dest)
    for f in files:
        base = os.path.split(f)[1]
        dest_file = os.path.join(dest, base)
        shutil.copyfile(f, dest_file)

def move_pdf_files(src = 'pdfs', dest = '../static/files/pubs/pdfs'):
    files = os.listdir(src)
    if not os.path.isdir(dest):
        os.makedirs(dest)
    for f in files:
        src_file = os.path.join(src, f)
        dest_file = os.path.join(dest, f)
        if os.path.isfile(src_file):
            shutil.copyfile(src_file, dest_file)

def main():
    preprocess('jg_pubs.bib', 'jg_pubs_an.bib')
    bib = gen_refs('jg_pubs_an.bib')
    gen_items(bib['references'])
    move_md_files()
    move_pdf_files()

if __name__ == '__main__':
    main()
