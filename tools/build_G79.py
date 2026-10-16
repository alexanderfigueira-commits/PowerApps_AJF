#!/usr/bin/env python3
"""FINAL89 on FINAL88: choosing a template (CI_TplConfirmOK, and the row click that applies it when the form is empty) copies every field of the
template media item into the new form: title, description (HTML stripped), dates, place, credits, language, product type, FTP, notes, links, tags,
series / episode / season data, summary, script, caption, contracting authority, photographer, producer(s), executive producer, contract case,
all rights & declarations (incl. the six new columns) and the AI voice-over flag. Not copied, because they identify one media item: Beluga reference,
media number, attachments, approval. The people pickers are reset so they show the copied people.
Also: DOA_List1RowBadge_9 and CM_BtnPrev_1 are sent behind CI_TplConfirmShade (and the template pop-up overlay)."""
import datetime, json, os, re, shutil, sys
from payaml import App
SRC, NEW = 'newG78', 'newG79'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
S = 'ChildInfoScreen'
# the description expression of the open-row logic (strips the HTML of the rich-text column)
op = app.rule('RequesDetailScreen', 'DOA_List1RowBadge_8', 'OnSelect').replace('\r\n', '\n')
i = op.index('Set(varChildDescription1,') + len('Set(varChildDescription1,'); j = op.index('\nSet(varChildCaptureDate')
desc = op[i:j].strip().rstrip(';').rstrip()
assert desc.endswith(')'); desc = desc[:-1].strip().replace('ThisItem.', 'varTplCandidate.')
T = 'varTplCandidate'
def person(sel, txt, col):
    return [f'Set({sel}, If(IsEmpty({T}.{col}), Blank(), ForAll({T}.{col} As p, {{DisplayName: p.DisplayName, Mail: p.Email}})));',
            f'Set({txt}, Concat({T}.{col}, DisplayName, ", "));']
L = [f'Set(varChildTitle1, Coalesce({T}.ProductionTitle, ""));',
     f'Set(varChildDescription1, {desc});',
     f'Set(varChildCaptureDate, {T}.CaptureDate);',
     f'Set(varChildProductionEndDate, {T}.ProductionEndDate);',
     f'Set(varChildPublicationStartDate, {T}.PublicationStartDate);',
     f'Set(varChildPublicationEndDate, {T}.PublicationEndDate);',
     f'Set(varChildCredits1, Coalesce({T}.CreditContact, First({T}.Photographer).DisplayName, First({T}.Director).DisplayName, First({T}.Producer).DisplayName, ""));',
     f'Set(varChildProductionPlace1, Coalesce({T}.ProductionPlace, ""));',
     f'Set(varChildLinks1, Coalesce({T}.ReferenceLinks, ""));',
     f'Set(varChildTags, Coalesce({T}.Tags, ""));', f'Set(varChildTags1, Coalesce({T}.Tags, ""));',
     f'Set(varChildFTPPath1, Coalesce({T}.FTPPath, ""));',
     f'Set(varChildNotes, Coalesce({T}.Notes, ""));',
     f'Set(varChildScript, Coalesce({T}.ScriptShotlist, ""));',
     f'Set(varChildPhotoCaption, Coalesce({T}.PhotoCaption, ""));',
     f'Set(varChildContractingAuthority, Coalesce({T}.ContractingAuthority, ""));',
     f'Set(varChildExecProducer, Coalesce({T}.ExecProducerName, ""));',
     *person('varChildProducerSel', 'varChildProducer', 'Producer'),
     *person('varChildPhotographerSel', 'varChildPhotographer', 'Photographer'),
     f'Set(varChildSeriesTitle1, Coalesce({T}.SeriesTitle, ""));',
     f'Set(varChildEpisodeTitle1, Coalesce({T}.EpisodeTitle, ""));',
     f'Set(varChildEpisodeSummary1, Coalesce({T}.EpisodeSummary, ""));',
     f'Set(varChildSeasonNumber, Coalesce({T}.SeasonNumber, 0));',
     f'Set(varChildEpisodeNumber, Coalesce({T}.EpisodeNumber, 0));',
     f'Set(varChildProductType, Coalesce(First({T}.ProductType).Value, varChildProductType));',
     f'Set(varChildProductType1, Coalesce(First({T}.ProductType).Value, varChildProductType1));',
     f'Set(varChildLanguageVersions, Coalesce(First({T}.LanguageVersions).Value, varChildLanguageVersions));',
     f'Set(varChildContractCase, Coalesce(First({T}.ContractCase).Value, ""));',
     f'Set(varChildContractCase1Sub, Coalesce(First({T}.ContractCase1Sub).Value, ""));',
     f'Set(varDocFramework, Coalesce({T}.FrameworkContractSigned, false));',
     f'Set(varDocSpecific, Coalesce({T}.SpecificContractSigned, false));',
     f'Set(varDocOffer, Coalesce({T}.OfferProvided, false));',
     f'Set(varChildNoThirdParty, Coalesce({T}.NoThirdPartyRights, false));',
     f'Set(varChildModelReleaseProvided, Coalesce({T}.ModelReleaseProvided, false));',
     f'Set(varChildModelRelease, Coalesce({T}.ModelRelease, false) Or Coalesce({T}.ModelReleaseProvided, false));',
     f'Set(varChildMusicUsed, Coalesce({T}.MusicUsed, false));',
     f'Set(varChildMusicLicenceProvided, Coalesce({T}.MusicLicenseProvided, false));',
     f'Set(varChildPreexistingProvided, Coalesce({T}.PreexistingRightsProvided, false));',
     f'Set(varChildPreexisting, Coalesce({T}.PreexistingRights, false) Or Coalesce({T}.PreexistingRightsProvided, false));',
     f'Set(varChildSubtitlesProvided, Coalesce({T}.SubtitlesProvided, false));',
     f'Set(varChildAIVoiceover, {T}.AIVoiceover = "Yes");',
     'Reset(CM_Producer);', 'Reset(CM_Photographer);']
def ind(lines, pad): return ('\n' + pad).join(lines)
for ctl, pad in (('CI_TplConfirmOK', ''), ('CI_TplRowBg', '    ')):
    t = app.rule(S, ctl, 'OnSelect'); eol = '\r\n' if '\r\n' in t else '\n'; n = t.replace('\r\n', '\n')
    m = re.search(r'Set\(varChildTitle1, Coalesce\(varTplCandidate\.ProductionTitle, ""\)\);.*?Set\(varChildAIVoiceover, varTplCandidate\.AIVoiceover = "Yes"\);', n, re.S)
    assert m, ctl
    n = n[:m.start()] + ind(L, pad) + n[m.end():]
    app.set(S, ctl, 'OnSelect', n.replace('\n', eol), expect=t)
app.save()
# z-order: behind CI_TplConfirmShade (21) and the picker overlay (13)
jp = [os.path.join(NEW, 'Controls', f) for f in os.listdir(f'{NEW}/Controls') if '"ChildInfoScreen"' in open(os.path.join(NEW, 'Controls', f), encoding='utf-8-sig').read()[:400]][0]
raw = open(jp, 'rb').read(); bom = raw.startswith(b'\xef\xbb\xbf'); crlf = b'\r\n' in raw
d = json.loads(raw.decode('utf-8-sig')); k = 0
for c in d['TopParent']['Children']:
    if c['Name'] in ('DOA_List1RowBadge_9', 'CM_BtnPrev_1'):
        r = [x for x in c['Rules'] if x['Property'] == 'ZIndex'][0]; r['InvariantScript'] = '12'; k += 1
        for e in c.get('ControlPropertyState', []):
            if isinstance(e, dict) and e.get('InvariantPropertyName') == 'ZIndex' and e.get('AutoRuleBindingString'): e['AutoRuleBindingString'] = '12'
assert k == 2
out = json.dumps(d, ensure_ascii=False, indent=2)
open(jp, 'w', encoding='utf-8-sig' if bom else 'utf-8', newline='').write(out.replace('\n', '\r\n') if crlf else out)
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL89 built')
