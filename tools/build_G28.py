#!/usr/bin/env python3
"""FINAL38 on FINAL37: requests created today now show on the Requests screen.

Cause: the default date range was set to  From = Today()-31, To = Today(), and Today() is midnight (00:00). The list keeps requests with
Created <= To, and Created carries the time of day, so everything created today after 00:00 was left out. (The To date picker already
stores 23:59:59 when it is changed by hand; only the opening default was wrong.)
Fixes:
* the default To is the end of today (23:59:59);
* the range is re-initialised when the app is used on a new day (varFilterDay), otherwise a session kept open past midnight would keep
  yesterday as "To" and hide the new day's requests; both date pickers are reset with it;
* a request created through "Add media" (the first save of a new request) now marks the Requests list as stale like Draft Save does,
  so it appears the next time the screen opens instead of only after the Reload button.
"""
import datetime, os, re, shutil, sys
from payaml import App

SRC, NEW = 'newG27', 'newG28'
if os.path.exists(NEW):
    shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
RM = 'RequestManagementScreen'
t = app.rule(RM, None, 'OnVisible')
n = t.replace('\r\n', '\n')
old = '            Set(varFilterStartDate, Today()-31);\n            Set(varFilterEndDate, Today());\n            UpdateContext({locProdTypeFilter: Blank(), locShowFilters: true});\n            Set(varReqFiltersInit, true)\n        );'
if '\n' + old.replace('            ', '            ', 1) not in '\n' + n and old.strip() not in n:
    pass
# the stored rule text is indented differently from the YAML view: match on the statements
pat = re.compile(r'( *)Set\(varFilterStartDate, Today\(\)-31\);\n( *)Set\(varFilterEndDate, Today\(\)\);\n( *)UpdateContext\(\{locProdTypeFilter: Blank\(\), locShowFilters: true\}\);\n( *)Set\(varReqFiltersInit, true\)\n( *)\);')
m = pat.search(n)
if not m:
    sys.exit('! filter init block not found')
i1, i5 = m.group(1), m.group(5)
rep = (f'{i1}// To = the END of today: Today() is 00:00 and Created has a time, so "Created <= To" hid today\'s requests\n'
       f'{i1}Set(varFilterStartDate, Today()-31);\n'
       f'{i1}Set(varFilterEndDate, Today() + Time(23, 59, 59));\n'
       f'{i1}Set(varFilterDay, Today());\n'
       f'{i1}UpdateContext({{locProdTypeFilter: Blank(), locShowFilters: true}});\n'
       f'{i1}Set(varReqFiltersInit, true)\n'
       f'{i5});\n'
       f'{i5}// a new day since the range was set (app kept open past midnight): the default range moves to today\n'
       f'{i5}If(\n'
       f'{i5}    varReqFiltersInit And varFilterDay <> Today(),\n'
       f'{i5}    Set(varFilterDay, Today());\n'
       f'{i5}    Set(varFilterStartDate, Today()-31);\n'
       f'{i5}    Set(varFilterEndDate, Today() + Time(23, 59, 59));\n'
       f'{i5}    Reset(HomeFilterStart);\n'
       f'{i5}    Reset(HomeFilterEnd)\n'
       f'{i5});')
n2 = n[:m.start()] + rep + n[m.end():]
app.set(RM, None, 'OnVisible', n2.replace('\n', '\r\n') if '\r\n' in t else n2, expect=t)
st = app.rule('App', None, 'OnStart')
app.set('App', None, 'OnStart', 'Set(varFilterDay, Today());\n' + st, expect=st)

# Add media: the first save of a new request marks the Requests list stale
RS = 'RequesDetailScreen'
t = app.rule(RS, 'Add_media_icon', 'OnSelect')
a = 'Set(varChildScript, "");\r\nNavigate(ChildInfoScreen)'
if t.count(a) != 1:
    sys.exit('! Add_media_icon anchor not found')
app.set(RS, 'Add_media_icon', 'OnSelect', t.replace(a, 'Set(varChildScript, "");\r\n// the request may have just been created: the Requests list reloads on its next visit\r\nSet(varReqDataLoaded, false);\r\nNavigate(ChildInfoScreen)'), expect=t)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL38 built')
