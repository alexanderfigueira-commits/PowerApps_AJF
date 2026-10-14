# Flows 2 to 8, executed inside build_solution.py (uses its helpers: sp, mail, T, P, G, LIST, LINK ...).
# Idempotency without "Get changes": marker columns on AV-CD-Requests (LastNotifiedStatus, LastNotifiedAssignee, LastNotifiedCoAssignee, LastReminderOn, SecondApprovalOn).
def seq(items):
    out, prev = {}, None
    for n, a in items:
        a = dict(a); a['runAfter'] = {prev: ['Succeeded']} if prev else {}
        out[n] = a; prev = n
    return out
def cond(expr, yes, no=None):
    c = {'type': 'If', 'expression': {'equals': ['@' + expr, True]}, 'actions': seq(yes)}
    if no is not None: c['else'] = {'actions': seq(no)}
    return c
def compose(v): return {'type': 'Compose', 'inputs': v}
def query(src, where): return {'type': 'Query', 'inputs': {'from': src, 'where': where}}
def select(src, m): return {'type': 'Select', 'inputs': {'from': src, 'select': m}}
def table(src): return {'type': 'Table', 'inputs': {'from': src, 'format': 'HTML'}}
def terminate(): return {'type': 'Terminate', 'inputs': {'runStatus': 'Cancelled'}}
def foreach(src, items): return {'type': 'Foreach', 'foreach': src, 'actions': seq(items)}
def getitems(list_key, flt, top=100): return sp('GetItems', {'dataset': P('SiteUrl'), 'table': LIST[list_key], '$filter': flt, '$top': top})
def patch_req(id_expr, title_expr, status_expr, extra):
    p = {'dataset': P('SiteUrl'), 'table': LIST['requests'], 'id': id_expr, 'item/Title': title_expr, 'item/field_5/Value': status_expr}
    p.update({f'item/{k}': v for k, v in extra.items()})
    return sp('PatchItem', p)
def scope_wrap(name, main_items, err_flow):
    return {'Initialize_SupportMailbox': {'type': 'InitializeVariable', 'runAfter': {}, 'inputs': {'variables': [{'name': 'SupportMailbox', 'type': 'string', 'value': 'audiovisual-service@ec.europa.eu'}]}},
            'Scope_-_Main': {'type': 'Scope', 'runAfter': {'Initialize_SupportMailbox': ['Succeeded']}, 'actions': seq(main_items)},
            'Scope_-_Catch': {'type': 'Scope', 'runAfter': {'Scope_-_Main': ['Failed', 'TimedOut']},
                              'actions': {'Send_failure_e-mail': mail("@{variables('SupportMailbox')}", f"[Central Deposit] Flow failed: {err_flow}",
                                          f"<p>Flow <b>{name}</b> failed.</p><p>Run: @{{workflow()?['run']?['name']}}</p><p>@{{string(result('Scope_-_Main'))}}</p>")}}}
def trig_changed(table_key, conds, name):
    return {'When_a_request_changes': {'recurrence': {'interval': 1, 'frequency': 'Minute'}, 'splitOn': "@triggerOutputs()?['body/value']", 'metadata': {'operationMetadataId': G('t-' + name).lower()},
            'type': 'OpenApiConnection', 'inputs': {'host': {'apiId': '/providers/Microsoft.PowerApps/apis/shared_sharepointonline', 'connectionName': 'shared_sharepointonline', 'operationId': 'GetOnChangedItems'},
            'parameters': {'dataset': P('SiteUrl'), 'table': LIST[table_key]}, 'authentication': "@parameters('$authentication')"},
            'conditions': [{'expression': '@' + conds}], 'runtimeConfiguration': {'concurrency': {'runs': 1}}}}
def trig_new(table_key, name, conds=None):
    t = trig_changed(table_key, 'true', name)['When_a_request_changes']
    t['inputs']['host']['operationId'] = 'GetOnNewItems'
    t['conditions'] = [{'expression': '@' + conds}] if conds else []
    if not conds: t.pop('conditions')
    return {'When_a_note_is_created': t}
def trig_schedule(hour, minute, name):
    return {'Recurrence': {'recurrence': {'frequency': 'Week', 'interval': 1, 'timeZone': 'Romance Standard Time',
            'schedule': {'weekDays': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'], 'hours': [str(hour)], 'minutes': [minute]}},
            'metadata': {'operationMetadataId': G('t-' + name).lower()}, 'type': 'Recurrence'}}
def definition(triggers, actions):
    return {'$schema': 'https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#', 'contentVersion': '1.0.0.0',
            'parameters': {'$connections': {'defaultValue': {}, 'type': 'Object'}, '$authentication': {'defaultValue': {}, 'type': 'SecureObject'}}, 'triggers': triggers, 'actions': actions}
def wrap(defn, approvals=False):
    refs = {'shared_sharepointonline': {'runtimeSource': 'embedded', 'connection': {'connectionReferenceLogicalName': CONN_SP}, 'api': {'name': 'shared_sharepointonline'}},
            'shared_sendmail': {'runtimeSource': 'embedded', 'connection': {'connectionReferenceLogicalName': CONN_MAIL}, 'api': {'name': 'shared_sendmail'}}}
    if approvals: refs['shared_approvals'] = {'runtimeSource': 'embedded', 'connection': {'connectionReferenceLogicalName': CONN_APPR}, 'api': {'name': 'shared_approvals'}}
    return {'properties': {'connectionReferences': refs, 'definition': defn, 'templateName': None}, 'schemaVersion': '1.0.0.0'}
LOW = lambda e: f"toLower(coalesce({e},''))"
EM = lambda f: f"coalesce({T(f)},'')"
SIGN = '<p>Audiovisual Service, DG COMM</p>'
def mail_to(parts):   # distinct, non-empty addresses joined by ';' (parts = expressions that return an array or a string)
    return parts
# ---- shared steps ----
REQUESTOR = f"@{{{EM('Author/Email')}}}"
LINKC = f"{P('AppBaseUrl')}&RequestID=@{{{T('ID')}}}"
RN_, TI_ = T('Title'), T('RequestTitle')
HEAD = f"@{{{RN_}}} &middot; @{{{TI_}}}"
# =========================================================================================================
# FLOW 2: status changed (the request status only: media files are not looked at)
def flow02():
    st = T('field_5/Value')
    cond_t = (f"and(or(equals({st},'Approved'), equals({st},'Rejected'), equals({st},'Pending'), equals({st},'Published')), "
              f"not(equals(coalesce({T('LastNotifiedStatus')},''), {st})))")
    to = "@{join(body('Filter_recipients'),';')}"   # requestor + assignee + the support mailbox, always
    def body(msg): return (f"<p>Hello @{{{EM('Author/DisplayName')}}},</p>{msg}<p>Decided by @{{outputs('Compose_reviewer')}} on @{{outputs('Compose_decision_date')}}.</p>"
                           f"<p><a href=\"{LINKC}\">Open the request</a></p>{SIGN}")
    comment = "<p><b>@{outputs('Compose_comment')}</b></p>"
    archived = f"equals(coalesce({T('ArchivedOnly')},false),true)"
    items = [
        ('Filter_recipients', query(f"@union(createArray({EM('Author/Email')}), createArray({EM('Assignee/Email')}), createArray(variables('SupportMailbox')))", "@not(empty(item()))")),
        ('Compose_reviewer', compose(f"@coalesce(first(coalesce({T('field_8')}, createArray()))?['DisplayName'], 'the Audiovisual Service')")),
        ('Compose_decision_date', compose(f"@if(empty(coalesce({T('field_11')},'')), '', convertTimeZone({T('field_11')},'UTC','Romance Standard Time','dd-MM-yyyy HH:mm'))")),
        ('Compose_comment', compose(f"@coalesce({T('field_10')}, 'No comment')")),
        ('Switch_status', {'type': 'Switch', 'expression': f"@{st}", 'cases': {
            'Case_approved': {'case': 'Approved', 'actions': seq([('Send_2A_approved', mail(to, f"[Central Deposit] Request @{{{RN_}}} approved",
                body(f"<p>Your request <b>{HEAD}</b> has been <b>approved</b>.</p><p>@{{if({archived}, 'It is kept in the Central Deposit archive and will not be published on the Audiovisual Service portal.', 'It will now be published on the Audiovisual Service portal.')}}</p><p>Comment:</p>" + comment)))])},
            'Case_rejected': {'case': 'Rejected', 'actions': seq([('Send_2B_rejected', mail(to, f"[Central Deposit] Request @{{{RN_}}} rejected",
                body(f"<p>Your request <b>{HEAD}</b> has been <b>rejected</b>.</p><p>Reason:</p>" + comment + "<p>The request is now read-only. If you think this is a mistake, answer in the Message Center of the request.</p>")))])},
            'Case_pending': {'case': 'Pending', 'actions': seq([('Send_2C_need_info', mail(to, f"[Central Deposit] Action needed on request @{{{RN_}}}",
                body(f"<p>The Audiovisual Service needs <b>more information</b> before it can decide on your request <b>{HEAD}</b>.</p><p>What we need:</p>" + comment + "<p>Please open the request, update it and press <b>Resubmit for review</b>.</p>")))])},
            'Case_published': {'case': 'Published', 'actions': seq([('Send_2D_published', mail(to, f"[Central Deposit] Request @{{{RN_}}} published",
                body(f"<p>Your request <b>{HEAD}</b> has been <b>published</b> on the Audiovisual Service portal.</p>")))])}},
            'default': {'actions': {}}}),
        ('Mark_status_notified', patch_req(f"@{T('ID')}", f"@{RN_}", f"@{st}", {'LastNotifiedStatus': f"@{st}"})),
    ]
    return wrap(definition(trig_changed('requests', cond_t, 'flow02'), scope_wrap('CD - 02 Status changed', items, f"@{{{RN_}}}")))
# FLOW 3: resubmitted
def flow03():
    cond_t = f"and(equals({T('field_5/Value')},'Processing'), not(empty(coalesce({T('field_11')},''))), not(equals(coalesce({T('LastNotifiedStatus')},''),'Processing')))"
    # only the assignee (the administrator in charge) and the support mailbox, always: no administrators, no co-assignee
    to_3a = f"@{{if(empty({EM('Assignee/Email')}), variables('SupportMailbox'), concat({EM('Assignee/Email')}, ';', variables('SupportMailbox')))}}"
    items = [
        ('Send_3A_to_assignee_and_support', mail(to_3a, f"[Central Deposit] Request @{{{RN_}}} resubmitted for review",
            f"<p>Hello,</p><p><b>@{{{EM('Author/DisplayName')}}}</b> has updated and resubmitted the request <b>{HEAD}</b>.</p><p>Assignee: @{{coalesce({T('Assignee/DisplayName')},'not assigned yet')}}</p><p>Your previous question: @{{{EM('field_10')}}}</p><p><a href=\"{LINKC}\">Open the request</a></p>{SIGN}")),
        ('Send_3B_to_requestor', mail(REQUESTOR, f"[Central Deposit] Request @{{{RN_}}} resubmitted",
            f"<p>Hello @{{{EM('Author/DisplayName')}}},</p><p>Thank you: your request <b>@{{{RN_}}}</b> is back in <b>Processing</b>.</p><p><a href=\"{LINKC}\">Open your request</a></p>")),
        ('Mark_processing_notified', patch_req(f"@{T('ID')}", f"@{RN_}", f"@{T('field_5/Value')}", {'LastNotifiedStatus': 'Processing'}))]
    return wrap(definition(trig_changed('requests', cond_t, 'flow03'), scope_wrap('CD - 03 Resubmitted', items, f"@{{{RN_}}}")))
# FLOW 4: assignment / co-assignment (markers LastNotifiedAssignee / LastNotifiedCoAssignee hold the e-mail last announced)
def flow04():
    a, c = LOW(T('Assignee/Email')), LOW(T('CoAssignee/Email'))
    la, lc = LOW(T('LastNotifiedAssignee')), LOW(T('LastNotifiedCoAssignee'))
    cond_t = f"and(not(equals({T('field_5/Value')},'Draft')), or(not(equals({a},{la})), not(equals({c},{lc}))))"
    def who(f): return f"@{{coalesce({T(f)}, '')}}"
    info = (f"<table cellpadding=\"3\"><tr><td><b>Requestor</b></td><td>@{{{EM('Author/DisplayName')}}}</td></tr><tr><td><b>Department</b></td><td>@{{{EM('field_1/Value')}}}</td></tr>"
            f"<tr><td><b>Production type</b></td><td>@{{{EM('production_type_request/Value')}}}</td></tr><tr><td><b>Status</b></td><td>@{{{EM('field_5/Value')}}}</td></tr></table>")
    items = [
        ('Compose_assignee_changed', compose(f"@not(equals({a},{la}))")), ('Compose_co_changed', compose(f"@not(equals({c},{lc}))")),
        ('If_assignee_changed', cond("outputs('Compose_assignee_changed')", [
            ('If_new_assignee', cond(f"not(empty({a}))", [('Send_4A_new_assignee', mail(f"@{{{EM('Assignee/Email')}}}", f"[Central Deposit] You are the assignee of request @{{{RN_}}}",
                f"<p>Hello @{{{EM('Assignee/DisplayName')}}},</p><p>You have been assigned as <b>assignee</b> of the request <b>{HEAD}</b>@{{if(empty({c}),'',concat(' together with ', {EM('CoAssignee/DisplayName')}))}}.</p>{info}<p><a href=\"{LINKC}\">Open the request</a></p>{SIGN}"))])),
            ('If_previous_assignee', cond(f"not(empty({la}))", [('Send_4B_previous_assignee', mail(f"@{{{EM('LastNotifiedAssignee')}}}", f"[Central Deposit] You are no longer the assignee of request @{{{RN_}}}",
                f"<p>Hello,</p><p>The request <b>{HEAD}</b> has been reassigned to <b>@{{coalesce({T('Assignee/DisplayName')},'someone else')}}</b>. No further action is needed from you.</p><p><a href=\"{LINKC}\">Open the request</a></p>"))])),
            ('If_first_assignment', cond(f"and(empty({la}), not(empty({a})))", [('Send_4E_requestor', mail(REQUESTOR, f"[Central Deposit] Request @{{{RN_}}} assigned",
                f"<p>Hello @{{{EM('Author/DisplayName')}}},</p><p>Your request <b>{HEAD}</b> is being handled by <b>@{{{EM('Assignee/DisplayName')}}}</b>@{{if(empty({c}),'',concat(' and ', {EM('CoAssignee/DisplayName')}))}}. You can write to them in the Message Center of the request.</p><p><a href=\"{LINKC}\">Open your request</a></p>"))]))])),
        ('If_co_changed', cond("outputs('Compose_co_changed')", [
            ('If_new_co_assignee', cond(f"not(empty({c}))", [('Send_4C_new_co_assignee', mail(f"@{{{EM('CoAssignee/Email')}}}", f"[Central Deposit] You are the co-assignee of request @{{{RN_}}}",
                f"<p>Hello @{{{EM('CoAssignee/DisplayName')}}},</p><p>You have been added as <b>co-assignee</b> of the request <b>{HEAD}</b>. The assignee is <b>@{{{EM('Assignee/DisplayName')}}}</b>. You can review and decide on this request as well.</p><p><a href=\"{LINKC}\">Open the request</a></p>{SIGN}"))])),
            ('If_previous_co_assignee', cond(f"not(empty({lc}))", [('Send_4D_previous_co_assignee', mail(f"@{{{EM('LastNotifiedCoAssignee')}}}", f"[Central Deposit] You are no longer co-assignee of request @{{{RN_}}}",
                f"<p>Hello,</p><p>You have been removed as co-assignee of <b>{HEAD}</b>.</p>"))]))])),
        ('Mark_assignment_notified', patch_req(f"@{T('ID')}", f"@{RN_}", f"@{T('field_5/Value')}", {'LastNotifiedAssignee': f"@{a}", 'LastNotifiedCoAssignee': f"@{c}"}))]
    return wrap(definition(trig_changed('requests', cond_t, 'flow04'), scope_wrap('CD - 04 Assignment', items, f"@{{{RN_}}}")))
# the administrator side of every e-mail: the assignee (when there is one) and the support mailbox, always. Never the list of administrators, never the co-assignee.
def TO_ASSIGNEE(a): return f"@{{if(empty({a}), variables('SupportMailbox'), concat({a}, ';', variables('SupportMailbox')))}}"
# FLOW 6: new message
def flow06():
    role = T('AuthorRole/Value')
    items = [
        ('Get_request', getitems('requests', f"Title eq '@{{{T('ParentRequest')}}}'", 1)),
        ('Compose_request', compose("@first(body('Get_request')?['value'])")),
        ('If_request_found', cond("not(empty(outputs('Compose_request')))", [
            ('If_from_requestor', cond(f"equals({role},'Requestor')", [
                ('Send_6A_to_assignee_and_support', mail(TO_ASSIGNEE("coalesce(outputs('Compose_request')?['Assignee']?['Email'],'')"),
                    f"[Central Deposit] New message on request @{{{T('ParentRequest')}}} from @{{{T('AuthorName')}}}",
                    f"<p>Hello,</p><p><b>@{{{T('AuthorName')}}}</b> wrote in the Message Center of <b>@{{{T('ParentRequest')}}} &middot; @{{outputs('Compose_request')?['RequestTitle']}}</b>:</p>"
                    f"<blockquote style=\"border-left:3px solid #3860b2;margin:8px 0;padding:4px 12px;color:#333\">@{{{T('NoteText')}}}</blockquote><p><a href=\"{P('AppBaseUrl')}&RequestID=@{{outputs('Compose_request')?['ID']}}\">Open the request and answer</a></p>"))],
                [('Send_6B_to_requestor', mail("@{outputs('Compose_request')?['Author']?['Email']}", f"[Central Deposit] New message on your request @{{{T('ParentRequest')}}}",
                    f"<p>Hello @{{outputs('Compose_request')?['Author']?['DisplayName']}},</p><p><b>@{{{T('AuthorName')}}}</b> (Audiovisual Service) wrote in the Message Center of your request <b>@{{{T('ParentRequest')}}} &middot; @{{outputs('Compose_request')?['RequestTitle']}}</b>:</p>"
                    f"<blockquote style=\"border-left:3px solid #3860b2;margin:8px 0;padding:4px 12px;color:#333\">@{{{T('NoteText')}}}</blockquote><p><a href=\"{P('AppBaseUrl')}&RequestID=@{{outputs('Compose_request')?['ID']}}\">Open your request and answer</a></p>"))]))]))]
    return wrap(definition(trig_new('notes', 'flow06'), scope_wrap('CD - 06 New message', items, f"@{{{T('ParentRequest')}}}")))
SUSPENDED = [('Get_active_suspension', getitems('suspension', "Active eq 1 and StartBlockedDate le '@{utcNow('yyyy-MM-dd')}' and EndBlockedDate ge '@{utcNow('yyyy-MM-dd')}'", 1)),
             ('If_suspended', cond("greater(length(body('Get_active_suspension')?['value']),0)", [('Stop_suspended_period', terminate())]))]
# FLOW 7: unread messages (one reminder per note: notes 24 to 48 hours old that nobody read)
def flow07():
    items = SUSPENDED + [
        ('Get_unread_notes', getitems('notes', "ReadOn eq null and Created le '@{addHours(utcNow(),-24)}' and Created ge '@{addHours(utcNow(),-48)}'", 200)),
        ('Select_request_numbers', select("@body('Get_unread_notes')?['value']", "@item()?['ParentRequest']")),
        ('Compose_distinct_requests', compose("@union(body('Select_request_numbers'), body('Select_request_numbers'))")),
        ('For_each_request', foreach("@outputs('Compose_distinct_requests')", [
            ('Get_request', getitems('requests', "Title eq '@{items('For_each_request')}'", 1)),
            ('Compose_req', compose("@first(body('Get_request')?['value'])")),
            ('Filter_notes_of_request', query("@body('Get_unread_notes')?['value']", "@equals(item()?['ParentRequest'], items('For_each_request'))")),
            ('Filter_from_requestor', query("@body('Filter_notes_of_request')", "@equals(item()?['AuthorRole']?['Value'],'Requestor')")),
            ('Filter_from_admin', query("@body('Filter_notes_of_request')", "@equals(item()?['AuthorRole']?['Value'],'Administrator')")),
            ('If_requestor_notes', cond("greater(length(body('Filter_from_requestor')),0)", [('Send_7A_to_assignee_and_support', mail(TO_ASSIGNEE("coalesce(outputs('Compose_req')?['Assignee']?['Email'],'')"),
                "[Central Deposit] @{length(body('Filter_from_requestor'))} unread message(s) on request @{items('For_each_request')}",
                f"<p>Hello,</p><p>You have <b>@{{length(body('Filter_from_requestor'))}}</b> message(s) from the requestor on <b>@{{items('For_each_request')}} &middot; @{{outputs('Compose_req')?['RequestTitle']}}</b> that nobody has read for more than 24 hours.</p><p><a href=\"{P('AppBaseUrl')}&RequestID=@{{outputs('Compose_req')?['ID']}}\">Open the request</a></p>"))])),
            ('If_admin_notes', cond("greater(length(body('Filter_from_admin')),0)", [('Send_7B_to_requestor', mail("@{outputs('Compose_req')?['Author']?['Email']}",
                "[Central Deposit] @{length(body('Filter_from_admin'))} unread message(s) on your request @{items('For_each_request')}",
                f"<p>Hello @{{outputs('Compose_req')?['Author']?['DisplayName']}},</p><p>You have <b>@{{length(body('Filter_from_admin'))}}</b> unread message(s) from the Audiovisual Service on your request <b>@{{items('For_each_request')}} &middot; @{{outputs('Compose_req')?['RequestTitle']}}</b>.</p><p><a href=\"{P('AppBaseUrl')}&RequestID=@{{outputs('Compose_req')?['ID']}}\">Open your request</a></p>"))]))]))]
    return wrap(definition(trig_schedule(9, 0, 'flow07'), scope_wrap('CD - 07 Unread messages', items, 'unread messages')))
# FLOW 8: reminders (Processing for 7+ days, Pending for 7+ days, at most one reminder every 3 days: LastReminderOn)
def flow08():
    def block(kind, days_expr, subject_fn, body_fn, to_fn):
        n = kind.lower()
        return [(f'Get_{n}_requests', getitems('requests', f"field_5 eq '{kind}' and {days_expr}", 200)),
                (f'Filter_{n}_due', query(f"@body('Get_{n}_requests')?['value']", "@or(empty(coalesce(item()?['LastReminderOn'],'')), less(item()?['LastReminderOn'], addDays(utcNow(),-3)))")),
                (f'For_each_{n}', foreach(f"@body('Filter_{n}_due')", [
                    (f'Send_reminder_{n}', mail(to_fn, subject_fn, body_fn)),
                    (f'Mark_reminder_{n}', sp('PatchItem', {'dataset': P('SiteUrl'), 'table': LIST['requests'], 'id': "@items('For_each_" + n + "')?['ID']", 'item/Title': "@items('For_each_" + n + "')?['Title']",
                                                         'item/field_5/Value': "@items('For_each_" + n + "')?['field_5']?['Value']", 'item/LastReminderOn': '@utcNow()'}))]))]
    it = lambda n, f: f"items('For_each_{n}')" + ''.join(f"?['{x}']" for x in f.split('/'))
    link = lambda n: f"{P('AppBaseUrl')}&RequestID=@{{{it(n, 'ID')}}}"
    proc_to = TO_ASSIGNEE("coalesce(items('For_each_processing')?['Assignee']?['Email'],'')")
    items = SUSPENDED + block('Processing', "field_6 lt '@{addDays(utcNow(),-7)}'",
        f"[Central Deposit] Reminder: request @{{{it('processing','Title')}}} is waiting for review",
        f"<p>Hello,</p><p>The request <b>@{{{it('processing','Title')}}} &middot; @{{{it('processing','RequestTitle')}}}</b> from @{{{it('processing','Author/DisplayName')}}} has been in <b>Processing</b> since @{{formatDateTime({it('processing','field_6')},'dd-MM-yyyy')}} and is not reviewed yet.</p><p><a href=\"{link('processing')}\">Open the request</a></p>",
        proc_to) + block('Pending', "field_11 lt '@{addDays(utcNow(),-7)}'",
        f"[Central Deposit] Reminder: we are waiting for your answer on request @{{{it('pending','Title')}}}",
        f"<p>Hello @{{{it('pending','Author/DisplayName')}}},</p><p>We asked for more information on <b>@{{{it('pending','Title')}}} &middot; @{{{it('pending','RequestTitle')}}}</b> and have not received it:</p><blockquote>@{{{it('pending','field_10')}}}</blockquote><p>Please open the request, update it and press <b>Resubmit for review</b>.</p><p><a href=\"{link('pending')}\">Open your request</a></p>",
        f"@{{{it('pending','Author/Email')}}}")
    return wrap(definition(trig_schedule(8, 30, 'flow08'), scope_wrap('CD - 08 Reminders', items, 'reminders')))
