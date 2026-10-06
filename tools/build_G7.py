#!/usr/bin/env python3
"""FINAL17 on FINAL16: the media save works again now that the PublicationChannel column is deleted.

Removed everywhere (the column is gone from the list and from the app's schema, so each use was an error):
* ChildValidScreen.CV_BtnSaveArchive: the PublicationChannel field of the media record (colArchives) and of the
  Patch to AV-CD-Mediafiles;
* RequesDetailScreen.OnVisible: the PublicationChannel field read back into colArchives;
* RequesDetailScreen.RS_CRowSelect: the two Set() lines that read ThisItem.PublicationChannel;
* the two variables that only served it (varChildPubBeluga / varChildPubSpotify): App.OnStart, Add_media_icon.
Nothing else is touched.
"""
import datetime, os, re, shutil, sys
from payaml import App

SRC, NEW = 'newG6', 'newG7'
if os.path.exists(NEW):
    shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
NL = r'\r?\n'


def cut(screen, ctl, prop, patterns, expect_counts):
    t = app.rule(screen, ctl, prop)
    n = t
    for pat, want in zip(patterns, expect_counts):
        found = len(re.findall(pat, n, flags=re.S))
        if found != want:
            sys.exit(f'! {screen}.{ctl}.{prop}: {found} x {pat[:50]!r}, expected {want}')
        n = re.sub(pat, '', n, flags=re.S)
    if re.search(r'PublicationChannel|varChildPubBeluga|varChildPubSpotify', n):
        sys.exit(f'! {screen}.{ctl}.{prop}: still mentions it')
    app.set(screen, ctl, prop, n, expect=t)


# save button: the record added to the media list, and the Patch to SharePoint
cut('ChildValidScreen', 'CV_BtnSaveArchive', 'OnSelect', [
    NL + r' *PublicationChannel: Concat\(Filter\(Table\(\{Value: "Beluga", On: varChildPubBeluga\}, \{Value: "Spotify", On: varChildPubSpotify\}\), On\), Value, ";"\),',
    NL + r' *// single-choice column: one record[^\n]*' + NL + r' *PublicationChannel: If\(' + NL + r'[^\n]*varChildPubBeluga Or varChildPubSpotify,' + NL + r'[^\n]*' + NL + r' *Blank\(\)' + NL + r' *\),',
], [1, 1])
# media list loaded from SharePoint
cut('RequesDetailScreen', None, 'OnVisible', [NL + r' *PublicationChannel: Coalesce\(PublicationChannel\.Value, ""\),'], [1])
# opening a media row
cut('RequesDetailScreen', 'RS_CRowSelect', 'OnSelect', [NL + r'Set\(varChildPubBeluga, "Beluga" in Coalesce\(ThisItem\.PublicationChannel, ""\)\);' + NL + r'Set\(varChildPubSpotify, "Spotify" in Coalesce\(ThisItem\.PublicationChannel, ""\)\);'], [1])
# the two variables
cut('RequesDetailScreen', 'Add_media_icon', 'OnSelect', [NL + r'Set\(varChildPubBeluga, false\);' + NL + r'Set\(varChildPubSpotify, false\);'], [1])
cut('App', None, 'OnStart', [r'Set\(varChildPubBeluga, false\);' + NL + r'Set\(varChildPubSpotify, false\);' + NL], [1])
app.save()

h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL17 built')
