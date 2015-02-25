#!/usr/bin/env python

import wikitools
import mwparserfromhell

import sys
import urlparse
import hashlib

WIKIPEDIA_BASE_URL = 'https://en.wikipedia.org'
WIKIPEDIA_WIKI_URL = WIKIPEDIA_BASE_URL + '/wiki/'
WIKIPEDIA_API_URL = WIKIPEDIA_BASE_URL + '/w/api.php'

MARKER = '7b94863f3091b449e6ab04d44cb372a0' # unlikely to be in any article

TEST_WIKITEXT_CACHE_FILENAME = '.test-wikitext.cache'

# Monkey-patch mwparserfromhell so it strips some templates and tags the way
# we want.
def template_strip(self, normalize, collapse):
    if self.name.matches('convert'):
        return ' '.join(map(unicode, self.params[:2]))
mwparserfromhell.nodes.Template.__strip__ = template_strip

def tag_strip(self, normalize, collapse):
    if self.tag == 'ref':
        return None
    return self._original_strip(normalize, collapse)
mwparserfromhell.nodes.Tag._original_strip = mwparserfromhell.nodes.Tag.__strip__
mwparserfromhell.nodes.Tag.__strip__ = tag_strip

mwparserfromhell.nodes.Heading.__strip__ = mwparserfromhell.nodes.Node.__strip__

def is_citation_needed(t):
    return t.name.matches('Citation needed') or t.name.matches('cn')

def extract_snippets(wikitext, minlen = 140, maxlen = 420):
    snippets = []

    # FIXME we should only add each paragraph once
    for paragraph in wikitext.split('\n\n'):
        wikicode = mwparserfromhell.parse(paragraph)

        for t in wikicode.filter_templates():
            if is_citation_needed(t):
                stripped_len = len(wikicode.strip_code())
                if stripped_len > maxlen or stripped_len < minlen:
                    # TL;DR or too short
                    continue

                # add the marker so we know where the Citation-needed template was
                wikicode.insert_before(t, MARKER)

        if MARKER in wikicode:
            snippet = wikicode.strip_code()
            snippets.append(snippet)

    return snippets

if __name__ == '__main__':
    import pprint

    title = sys.argv[1]
    wikitext = None
    try:
        with open(TEST_WIKITEXT_CACHE_FILENAME, 'r') as cache:
            if cache.readline()[:-1] == title:
                wikitext = cache.read()
    except:
        pass
    finally:
        if wikitext is None:
            wikipedia = wikitools.wiki.Wiki(WIKIPEDIA_API_URL)
            page = wikitools.Page(wikipedia, title)
            wikitext = page.getWikiText()

    with open(TEST_WIKITEXT_CACHE_FILENAME, 'w') as cache:
        print >>cache, title
        cache.write(wikitext)

    pprint.pprint(extract_snippets(wikitext))