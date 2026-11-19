import sys, json
sys.argv = [sys.argv[0], '../newV46']
import extract as E
screens = E.load_screens()
names = list(screens)
ADM = {'varUserRole': 'ADMINISTRATOR'}
REQ = {'varUserRole': 'REQUESTOR'}
base = {'varReqReady': True, 'locShowFilters': False, 'locPrinting': False, 'varCompactPrint': False, 'varFilter': 'All', 'locProdTypeFilter': ''}
def env(*ds):
    e = dict(base)
    for d in ds: e.update(d)
    return e
def mt(t, **kw):
    d = {'varChildMediaType': t, 'varRequestorLocked': False}
    d.update(kw); return d
def RD(status, **kw):
    d = {'varCurrentRequest': 'rec', 'varCurrentRequest.ID': 144, 'varCurrentRequest.Status.Value': status, 'varRequestorLocked': False, 'varViewOnly': False}
    d.update(kw); return d
C1 = 'Case 1 - framework / direct service contract'
SC = [
 ('RequestManagementScreen', 'Administrator', env(ADM)),
 ('RequestManagementScreen', 'Requestor', env(REQ)),
 ('RequestManagementScreen', 'Administrator, filters open', env(ADM, {'locShowFilters': True})),
 ('RequesDetailScreen', 'Requestor, draft', env(REQ, RD('Draft'))),
 ('RequesDetailScreen', 'Requestor, need info (Pending)', env(REQ, RD('Pending'))),
 ('RequesDetailScreen', 'Requestor, rejected (read-only)', env(REQ, RD('Rejected', varRequestorLocked=True))),
 ('RequesDetailScreen', 'Administrator, view-only (Processing)', env(ADM, RD('Processing', varRequestorLocked=True, varViewOnly=True))),
 ('ChildInfoScreen', 'Photo-Reportage', env(REQ, mt('Photo'))),
 ('ChildInfoScreen', 'Video', env(REQ, mt('Video'))),
 ('ChildInfoScreen', 'Podcast', env(REQ, mt('Podcast'))),
 ('ChildInfoScreen', 'Photo, template picker open', env(REQ, mt('Photo', varShowTemplatePicker=True))),
 ('ChildMetaScreen', 'Photo-Reportage', env(REQ, mt('Photo'))),
 ('ChildMetaScreen', 'Video', env(REQ, mt('Video'))),
 ('ChildMetaScreen', 'Podcast', env(REQ, mt('Podcast'))),
 ('ChildLegalScreen', 'Photo-Reportage, case 2', env(REQ, mt('Photo', varChildContractCase='Case 2 - specific service contract'))),
 ('ChildLegalScreen', 'Podcast, case 1', env(REQ, mt('Podcast', varChildContractCase=C1))),
 ('ChildLegalScreen', 'Video, case 1, all declarations ticked', env(REQ, mt('Video', varChildContractCase=C1, varChildModelRelease=True, varChildMusicUsed=True, varChildPreexisting=True, varChildSubtitlesProvided=True))),
 ('ChildValidScreen', 'Validations', env(REQ, mt('Photo'))),
 ('ReviewScreen', 'Administrator', env(ADM)),
 ('Dashboard-Ope-Requestor', 'Requestor', env(REQ)),
 ('Dashboard-Ope-Administrator', 'Administrator', env(ADM)),
 ('DashboardScreen', 'KPI, administrator', env(ADM, {'varShowTrend': False})),
 ('DashboardScreen', 'KPI, requestor', env(REQ)),
 ('HomePrintScreen', 'Print and export', env(ADM)),
 ('PrintPhotoDetailScreen', 'Photo-Reportage print', env(ADM)),
 ('PrintVideoDetailScreen', 'Video print', env(ADM)),
 ('PrintPodcastDetailScreen', 'Podcast print', env(ADM)),
 ('HelpScreen', 'Help', env(REQ)),
]
out = []
for s, v, e in SC:
    d = E.build(s, screens[s], e, names, v)
    out.append(d)
    print(f"{s:30s} {v:42s} ops={len(d['ops']):4d} bytes={len(json.dumps(d['ops'], separators=(',', ':'))):6d}")
json.dump(out, open('all.json', 'w'))
