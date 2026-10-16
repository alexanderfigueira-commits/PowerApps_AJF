# FLOW 9: import of the Central Deposit Word form (docx) -> draft request. Executed inside build_solution.py after flows_all.py (uses its helpers).
# The staging item is the REQUEST itself (Draft, hidden from the app's lists until ImportStatus = Done); the 8 Import* columns are on AV-CD-Requests.
# Phase "Uploaded":  read the docx (attached to the request), keep a copy in the SharePoint folder, write the preview (ImportPreview) and the data (ImportData).
# Phase "Confirmed": fill the request, create its media file, set the creator, mark it Done and e-mail the requestor the link.
UPLOAD_FOLDER = '/Shared Documents/UploadAVRequests'      # SharePoint library folder that keeps the uploaded originals
TEMP_FOLDER = '/AVImportTemp'                              # OneDrive (flow owner) scratch folder, emptied at the end
NL = "decodeUriComponent('%0A')"
MEDIA_LIST_GUID = LIST['media']
def OD(op, params):
    return {'type': 'OpenApiConnection', 'inputs': {'host': {'apiId': '/providers/Microsoft.PowerApps/apis/shared_onedriveforbusiness', 'connectionName': 'shared_onedriveforbusiness', 'operationId': op},
            'parameters': params, 'authentication': "@parameters('$authentication')"}}
def http(method, uri, body=None, accept='application/json;odata=nometadata'):
    p = {'dataset': P('SiteUrl'), 'parameters/method': method, 'parameters/uri': uri, 'parameters/headers': {'Accept': accept, 'Content-Type': 'application/json;odata=nometadata'}}
    if body is not None: p['parameters/body'] = body
    return sp('HttpRequest', p)
def seq_ra(items, first_after=None):
    """like seq() but every action runs after the previous one only when it succeeded (first one after first_after)."""
    return seq(items)
# ---------------------------------------------------------------- reading the document
def _row(label, exact):
    c = f'normalize-space(*[local-name()="tc"][1])="{label}"' if exact else f'starts-with(normalize-space(*[local-name()="tc"][1]),"{label}")'
    return f'//*[local-name()="tr"][{c}]'
def XV(label, exact=False):   # text of the answer cell of the row whose label matches
    return f"xpath(outputs('Compose_document'), 'normalize-space(string({_row(label, exact)}/*[local-name()=\"tc\"][2]))')"
def XCNT(label, exact=False): # how many rows have that label
    return f"xpath(outputs('Compose_document'), 'count({_row(label, exact)})')"
def XTICK(label, n=None):     # ticked boxes in the answer cell (n = only the n-th box, 1-based)
    box = f'{_row(label, False)}/*[local-name()="tc"][2]//*[local-name()="checked"]'
    if n: return f"greater(xpath(outputs('Compose_document'), 'count(({box})[{n}][@*[local-name()=\"val\"]=\"1\"])'), 0)"
    return f"greater(xpath(outputs('Compose_document'), 'count({box}[@*[local-name()=\"val\"]=\"1\"])'), 0)"
def ISO(name):                # dd/mm/yyyy, dd-mm-yyyy or yyyy-mm-dd -> yyyy-mm-dd ; anything else -> ''
    e = f"outputs('{name}')"; p = f"substring(concat({e},'          '),0,10)"
    dmy = f"and(equals(length({e}),10), or(equals(substring({p},2,1),'/'), equals(substring({p},2,1),'-')), isInt(substring({p},0,2)), isInt(substring({p},3,2)), isInt(substring({p},6,4)))"
    iso = f"and(equals(length({e}),10), equals(substring({p},4,1),'-'), isInt(substring({p},0,4)), isInt(substring({p},5,2)), isInt(substring({p},8,2)))"
    return f"@if({dmy}, concat(substring({p},6,4),'-',substring({p},3,2),'-',substring({p},0,2)), if({iso}, {e}, ''))"
FIELDS = [   # name, label, exact
    ('titleP', 'Title of reportage', 0), ('titleC', 'Title of the podcast', 0), ('titleV', 'Title', 1),
    ('descP', 'Description of the reportage', 0), ('descC', 'Description of the podcast', 0), ('descV', 'Description/Summary', 1),
    ('pubOnline', 'Date of publication online', 0), ('shoot', 'Shooting date', 0), ('recording', 'Recording', 1), ('filming', 'Filming', 1),
    ('placeP', 'Place where the photo', 0), ('placeV', 'Production place', 1), ('caption', 'Caption/short description', 0),
    ('authP', 'Contracting authority', 1), ('authV', 'Producer', 0), ('contractorP', 'Contractor, agency', 1), ('execV', 'Executive producer', 0),
    ('photographer', 'Name of the photographer', 0), ('links', 'Links', 0), ('tags', 'Pertinent tags', 0), ('seasonEp', 'Season and/or Episode number', 0),
    ('episodeTitle', 'Title of the Episode', 0), ('episodeSummary', 'Summary of the Episode', 0), ('language', 'Language version(s)', 0),
    ('prodEnd', 'Production end', 1), ('pubStart', 'Publication start', 1), ('pubEnd', 'Publication end', 1), ('script', 'Script/shotlist', 0),
    ('director', 'Director', 0), ('productType', 'Type of Product', 0)]
K = lambda n: f"outputs('Compose_{n}')"
KIND = K('kind')
PICK = lambda ph, po, vi: f"@if(equals({KIND},'Photo'), {K(ph)}, if(equals({KIND},'Podcast'), {K(po)}, {K(vi)}))"
def read_actions():
    a = [('Compose_heading', compose('@xpath(outputs(\'Compose_document\'), \'normalize-space(string((//*[local-name()="p"][contains(.,"Mandatory Metadata")])[1]))\')')),
         ('Compose_kind', compose("@if(contains(outputs('Compose_heading'),'for Photos'),'Photo',if(contains(outputs('Compose_heading'),'for Podcast'),'Podcast','Video'))")),
         ('Compose_layout_ok', compose(f"@or(and(equals({KIND},'Photo'), greater({XCNT('Title of reportage')},0)), and(equals({KIND},'Podcast'), greater({XCNT('Title of the podcast')},0)), and(equals({KIND},'Video'), greater({XCNT('Title', 1)},0)))"))]
    return a
def field_actions():
    a = [(f'Compose_{n}', compose('@' + XV(l, bool(e)))) for n, l, e in FIELDS]
    a += [(f'Compose_{n}_iso', compose(ISO(f'Compose_{n}'))) for n in ('pubOnline', 'shoot', 'recording', 'filming', 'prodEnd', 'pubStart', 'pubEnd')]
    ticks = [('case1a', XTICK('Case 1', 1)), ('case1b', XTICK('Case 1', 2)), ('case1c', XTICK('Case 1', 3))] + [(f'case{i}', XTICK(f'Case {i}')) for i in range(2, 7)] + \
            [('modelRelease', XTICK('Model release forms')), ('music', XTICK('Music')), ('preexisting', XTICK('Other pre-existing rights'))]
    a += [(f'Compose_{n}', compose('@' + t)) for n, t in ticks]
    a += [('Compose_contract_case', compose(f"@if({K('case2')},'Case 2 - specific service contract',if({K('case3')},'Case 3 - co-production agreement',if({K('case4')},'Case 4 - acquisition of existing material',if({K('case5')},'Case 5 - internal EU production',if({K('case6')},'Case 6 - donation / free licence',if(or({K('case1a')},{K('case1b')},{K('case1c')}),'Case 1 - framework / direct service contract',''))))))"))]
    a += [('Compose_case1_any', compose(f"@or({K('case1a')},{K('case1b')},{K('case1c')})"))]
    d = lambda ph, po, vi: PICK(ph, po, vi)
    data = {'type': f"@{{{KIND}}}",
            'requestTitle': d('titleP', 'titleC', 'titleV'), 'requestDescription': d('descP', 'descC', 'descV'),
            'mediaTitle': d('titleP', 'episodeTitle', 'titleV'),
            'mediaDescription': f"@if(equals({KIND},'Photo'), {K('caption')}, if(equals({KIND},'Video'), {K('descV')}, ''))",
            'photoCaption': f"@if(equals({KIND},'Photo'), {K('caption')}, '')",
            'episodeTitle': f"@if(equals({KIND},'Podcast'), {K('episodeTitle')}, '')", 'episodeSummary': f"@if(equals({KIND},'Podcast'), {K('episodeSummary')}, '')",
            'seasonEpisode': f"@if(equals({KIND},'Podcast'), {K('seasonEp')}, '')",
            'captureDate': f"@if(equals({KIND},'Photo'), {K('shoot_iso')}, if(equals({KIND},'Podcast'), {K('recording_iso')}, {K('filming_iso')}))",
            'productionEnd': f"@{K('prodEnd_iso')}", 'publicationStart': f"@if(equals({KIND},'Photo'), {K('pubOnline_iso')}, {K('pubStart_iso')})", 'publicationEnd': f"@{K('pubEnd_iso')}",
            'place': d('placeP', 'placeV', 'placeV'), 'links': f"@{K('links')}", 'tags': f"@{K('tags')}", 'script': f"@{K('script')}",
            'credits': f"@if(equals({KIND},'Photo'), if(empty({K('photographer')}), '', concat('Photographer: ', {K('photographer')})), {K('director')})",
            'contractingAuthority': d('authP', 'authV', 'authV'), 'executiveProducer': d('contractorP', 'execV', 'execV'),
            'language': f"@{K('language')}", 'productType': f"@{K('productType')}",
            'contractCase': f"@{K('contract_case')}", 'framework': f"@{K('case1a')}", 'specific': f"@{K('case1b')}", 'offer': f"@{K('case1c')}",
            'modelRelease': f"@{K('modelRelease')}", 'music': f"@{K('music')}", 'preexisting': f"@{K('preexisting')}"}
    a += [('Compose_data', compose(data))]
    D = lambda k: f"outputs('Compose_data')?['{k}']"
    rows = [('Form type', 'type'), ('Request title', 'requestTitle'), ('Request description', 'requestDescription'), ('Media title', 'mediaTitle'), ('Media description / caption', 'mediaDescription'),
            ('Capture / shooting / filming date', 'captureDate'), ('Production end date', 'productionEnd'), ('Publication start date', 'publicationStart'), ('Publication end date', 'publicationEnd'),
            ('Production place', 'place'), ('Season / episode', 'seasonEpisode'), ('Episode title', 'episodeTitle'), ('Episode summary', 'episodeSummary'),
            ('Links', 'links'), ('Pertinent tags', 'tags'), ('Credits / director / photographer', 'credits'), ('Script / shotlist', 'script'),
            ('Producer / contracting authority', 'contractingAuthority'), ('Executive producer / contractor', 'executiveProducer'),
            ('Language (to choose in the app)', 'language'), ('Type of product (to choose in the app)', 'productType'), ('Contract case', 'contractCase')]
    lines = [f"concat('{l}|', {D(k)})" for l, k in rows]
    lines += [f"concat('Case 1 documents|', if({D('framework')},'framework ',''), if({D('specific')},'specific ',''), if({D('offer')},'offer',''))",
              f"concat('Model release|', if({D('modelRelease')},'ticked',''))", f"concat('Music|', if({D('music')},'ticked',''))", f"concat('Pre-existing rights|', if({D('preexisting')},'ticked',''))"]
    a += [('Compose_preview', compose('@join(createArray(' + ', '.join(lines) + f'), {NL})'))]
    badd = [('captureDate', 'Capture / shooting / filming date', 'filming', 'shoot', 'recording'), ('productionEnd', 'Production end', 'prodEnd'), ('publicationStart', 'Publication start', 'pubStart', 'pubOnline'), ('publicationEnd', 'Publication end', 'pubEnd')]
    warn = [f"if(and(not(empty(concat({', '.join(K(r) for r in raw)}))), empty({D(k)})), '{lbl}: the date was not recognised (use dd/mm/yyyy). ', '')" for k, lbl, *raw in badd]
    warn += [f"if(empty({D('requestTitle')}), 'The title is empty. ', '')", f"if(empty({D('contractCase')}), 'No contract case ticked. ', '')"]
    a += [('Compose_warnings', compose('@concat(' + ', '.join(warn) + ')'))]
    return a
# ---------------------------------------------------------------- the flow
def flow09():
    st = T('ImportStatus'); ID_ = T('ID'); RN_T = T('Title')
    def patch_req_x(extra):
        return patch_req(f"@{ID_}", f"@{RN_T}", 'Draft', extra)
    uploader = f"coalesce({T('ImportedBy')},'')"
    req = f"coalesce({T('ImportRequestorEmail')},'')"
    # ---- phase 1: read
    read = [
        ('Mark_reading', patch_req_x({'ImportStatus': 'Reading'})),
        ('Get_attachment_list', http('GET', f"_api/web/lists(guid'{LIST['requests']}')/items(@{{{ID_}}})/AttachmentFiles?$select=FileName")),
        ('Filter_docx', query("@coalesce(body('Get_attachment_list')?['value'], createArray())", "@endsWith(toLower(coalesce(item()?['FileName'],'')), '.docx')")),
        ('If_docx_found', cond("greater(length(body('Filter_docx')),0)", [
            ('Compose_file_name', compose("@first(body('Filter_docx'))?['FileName']")),
            ('Get_attachment_content', sp('GetAttachmentContent', {'dataset': P('SiteUrl'), 'table': LIST['requests'], 'itemId': f"@{ID_}", 'attachmentId': "@outputs('Compose_file_name')"})),
            ('Save_original_in_folder', sp('CreateFile', {'dataset': P('SiteUrl'), 'folderPath': UPLOAD_FOLDER, 'name': f"@concat({RN_T}, '_', outputs('Compose_file_name'))", 'body': "@body('Get_attachment_content')"})),
            ('Compose_work_name', compose("@guid()")),
            ('Create_zip_in_OneDrive', OD('CreateFile', {'folderPath': TEMP_FOLDER, 'name': "@concat(outputs('Compose_work_name'), '.zip')", 'body': "@body('Get_attachment_content')"})),
            ('Extract_docx', OD('ExtractFolderV2', {'source': "@body('Create_zip_in_OneDrive')?['Path']", 'destination': f"@concat('{TEMP_FOLDER}/', outputs('Compose_work_name'))", 'overwrite': True})),
            ('Get_document_xml', OD('GetFileContentByPath', {'path': f"@concat('{TEMP_FOLDER}/', outputs('Compose_work_name'), '/word/document.xml')", 'inferContentType': True})),
            ('Compose_document', compose("@xml(if(empty(coalesce(body('Get_document_xml')?['$content'],'')), string(body('Get_document_xml')), base64ToString(body('Get_document_xml')?['$content'])))"))]
            + read_actions() + [
            ('If_layout_ok', cond("outputs('Compose_layout_ok')", field_actions() + [
                ('Mark_parsed', patch_req_x({'ImportStatus': 'Parsed', 'ImportData': "@string(outputs('Compose_data'))", 'ImportPreview': "@outputs('Compose_preview')", 'ImportMessage': "@outputs('Compose_warnings')"}))],
                [('Mark_unknown_layout', patch_req_x({'ImportStatus': 'Error', 'ImportMessage': "@concat('This does not look like one of the Central Deposit metadata forms (photo, podcast or video). Heading read: ', outputs('Compose_heading'))"}))])),
            ('Delete_zip', OD('DeleteFile', {'id': "@body('Create_zip_in_OneDrive')?['Id']"}))],
            [('Mark_no_docx', patch_req_x({'ImportStatus': 'Error', 'ImportMessage': 'No .docx file was found on the upload.'}))]))]
    # ---- phase 2: fill the request, create its media file
    d = lambda k: f"outputs('Compose_input')?['{k}']"
    set_creator_body = {'formValues': [{'FieldName': 'Author', 'FieldValue': f"@concat('[{{\"Key\":\"i:0#.f|membership|', toLower({req}), '\"}}]')"}], 'bNewDocumentUpdate': True}
    create = [
        ('Mark_creating', patch_req_x({'ImportStatus': 'Creating'})),
        ('Compose_input', compose(f"@json(triggerOutputs()?['body/ImportData'])")),
        ('Fill_request', patch_req_x({'RequestTitle': f"@{d('requestTitle')}", 'field_2': f"@{d('requestDescription')}", 'field_1/Value': f"@{T('ImportDG')}",
                                      'production_type_request/Value': f"@{d('type')}", 'ArchivedOnly': False})),
        ('Create_media_file', sp('PostItem', {'dataset': P('SiteUrl'), 'table': LIST['media'], 'item/Title': f"@concat({RN_T}, '-01')", 'item/field_30': f"@{RN_T}",
            'item/field_25': f"@createArray(json(concat('{{\"Value\":\"', {d('type')}, '\"}}')))", 'item/field_29': [{'Value': 'Draft'}],
            'item/ProductionTitle': f"@{d('mediaTitle')}", 'item/PhotoCaption': f"@{d('photoCaption')}", 'item/field_1': f"@{d('mediaDescription')}",
            'item/field_5': f"@{d('episodeTitle')}", 'item/field_6': f"@{d('episodeSummary')}", 'item/field_2': f"@{d('place')}", 'item/field_9': f"@{d('links')}", 'item/field_10': f"@{d('tags')}",
            'item/ScriptShotlist': f"@{d('script')}", 'item/CreditContact': f"@{d('credits')}", 'item/ContractingAuthority': f"@{d('contractingAuthority')}", 'item/ExecProducerName': f"@{d('executiveProducer')}",
            'item/field_21': f"@if(empty({d('captureDate')}), null, {d('captureDate')})", 'item/field_24': f"@if(empty({d('productionEnd')}), null, {d('productionEnd')})",
            'item/field_22': f"@if(empty({d('publicationStart')}), null, {d('publicationStart')})", 'item/field_23': f"@if(empty({d('publicationEnd')}), null, {d('publicationEnd')})",
            'item/field_27': f"@if(empty({d('contractCase')}), null, createArray(json(concat('{{\"Value\":\"', {d('contractCase')}, '\"}}'))))",
            'item/FrameworkContractSigned': f"@{d('framework')}", 'item/SpecificContractSigned': f"@{d('specific')}", 'item/OfferProvided': f"@{d('offer')}",
            'item/ModelRelease': f"@{d('modelRelease')}", 'item/MusicUsed': f"@{d('music')}", 'item/PreexistingRights': f"@{d('preexisting')}"})),
        ('Try_set_creator', {'type': 'Scope', 'actions': seq([('Set_creator', http('POST', f"_api/web/lists(guid'{LIST['requests']}')/items(@{{{ID_}}})/validateupdatelistitem", set_creator_body))])}),
        ('Compose_creator_set', compose("@equals(result('Try_set_creator')[0]['status'], 'Succeeded')")),
        ('Mark_done', patch_req_x({'ImportStatus': 'Done', 'ImportRequestID': f"@string({ID_})",
            'ImportMessage': f"@concat(coalesce({T('ImportMessage')},''), if(outputs('Compose_creator_set'), '', 'The creator could not be set to the requestor (it stays the person who uploaded the form). '))"})),
        ('Filter_recipients', query(f"@union(createArray({req}), createArray({uploader}), createArray(variables('SupportMailbox')))", "@not(empty(item()))")),
        ('Try_send_link', {'type': 'Scope', 'actions': seq([('Send_requestor_link', mail("@{join(body('Filter_recipients'),';')}", f"[Central Deposit] Draft request @{{{RN_T}}} created from a metadata form",
            f"<p>Hello,</p><p>A <b>draft</b> request was created from a Central Deposit metadata form: <b>@{{{RN_T}}} &middot; @{{{d('requestTitle')}}}</b>.</p>"
            f"<p>Please open it, check the data, complete what is missing (attachments, legal documents, ...) and submit it.</p><p><a href=\"{P('AppBaseUrl')}&RequestID=@{{{ID_}}}\">Open the draft request</a></p>"
            f"<p>Uploaded by @{{{uploader}}}.</p>{SIGN}"))])}),
        ('Compose_link_sent', compose("@equals(result('Try_send_link')[0]['status'], 'Succeeded')")),
        ('If_link_not_sent', cond("not(outputs('Compose_link_sent'))", [('Note_link_not_sent', patch_req_x({'ImportMessage': "@concat(coalesce(body('Mark_done')?['ImportMessage'],''), 'The e-mail with the link could not be sent. ')"}))]))]
    main = [('If_phase', cond(f"equals({st},'Uploaded')", read, [('If_confirmed', cond(f"equals({st},'Confirmed')", create))]))]
    err = patch_req_x({'ImportStatus': 'Error', 'ImportMessage': "@substring(concat('The import failed: ', string(result('Scope_-_Main'))), 0, min(length(concat('The import failed: ', string(result('Scope_-_Main')))), 3000))"})
    actions = {'Initialize_SupportMailbox': {'type': 'InitializeVariable', 'runAfter': {}, 'inputs': {'variables': [{'name': 'SupportMailbox', 'type': 'string', 'value': 'audiovisual-service@ec.europa.eu'}]}},
               'Scope_-_Main': {'type': 'Scope', 'runAfter': {'Initialize_SupportMailbox': ['Succeeded']}, 'actions': seq(main)},
               'Scope_-_Catch': {'type': 'Scope', 'runAfter': {'Scope_-_Main': ['Failed', 'TimedOut']}, 'actions': seq([
                   ('Mark_import_error', err),
                   ('Send_failure_e-mail', mail(f"@{{join(union(createArray(variables('SupportMailbox')), createArray({uploader})), ';')}}", '[Central Deposit] The form import failed',
                       f"<p>The import of a metadata form failed (request @{{{RN_T}}}, item @{{{ID_}}}).</p><p>Run: @{{workflow()?['run']?['name']}}</p><p>@{{string(result('Scope_-_Main'))}}</p>"))])}}
    # the creator and the e-mail steps are optional: whatever happens, the flow goes on
    cr = actions['Scope_-_Main']['actions']['If_phase']['else']['actions']['If_confirmed']['actions']
    cr['Compose_creator_set']['runAfter'] = {'Try_set_creator': ['Succeeded', 'Failed', 'TimedOut', 'Skipped']}
    cr['Compose_link_sent']['runAfter'] = {'Try_send_link': ['Succeeded', 'Failed', 'TimedOut', 'Skipped']}
    return wrap(definition(trig_changed('requests', f"or(equals({st},'Uploaded'), equals({st},'Confirmed'))", 'flow09'), actions), onedrive=True)
