#!/usr/bin/env python3
"""Builds the Power Platform solution 'CentralDepositFlows' (unmanaged) with the flows of docs/power-automate-flows.md.
Now: flow 1 'CD - 01 Request submitted'. Run:  python3 flows/build_solution.py   ->  flows/CentralDepositFlows_1_0_0_0.zip"""
import json, os, uuid, zipfile, xml.dom.minidom, re
HERE = os.path.dirname(os.path.abspath(__file__))
SITE = 'https://eceuropaeu.sharepoint.com/teams/GRP-EBSProductionForm'
LIST = {'requests': 'b170a694-8b5c-4ac7-a9d5-b9111488b7bd', 'media': '301869de-daa0-4d59-838c-647a5ffd2ea5', 'roles': '58e5019a-29bb-4cca-94dd-733e418619a0', 'notes': 'eeb548b6-2d28-4101-9995-47ce4bd8ddd9', 'suspension': '5995c8f7-f1f9-49b3-a838-6409af0ffc2b'}
APP = 'https://apps.powerapps.com/play/e/487b2992-105a-eb44-aa4b-296dae01044b/a/ba2698a5-2c73-4939-83cc-dd3c5120277d?tenantId=b24c8b06-522c-46fe-9080-70926f8dddb1'
PREFIX = 'avcd'
PUBLISHER = 'Cr99038'          # the environment's publisher (prefix avcd, option value prefix 51206), taken from the sample export
ALL = bool(os.environ.get('ALL'))
SKIP1 = bool(os.environ.get('SKIP1'))      # flow 1 is already imported and tested: leave it out
VERSION = ('1.1.0.3' if SKIP1 else '1.1.0.0') if ALL else '1.0.0.2'
CONN_APPR = 'avcd_sharedapprovals_c5d18'
# stable ids so a re-import updates instead of duplicating
G = lambda name: str(uuid.uuid5(uuid.NAMESPACE_URL, 'centraldeposit/' + name)).upper()
WF1 = G('flow01')
CONN_SP, CONN_MAIL = f'{PREFIX}_sharedsharepointonline_a7c31', f'{PREFIX}_sharedsendmail_b92e4'
VALUES = {'AppBaseUrl': APP, 'SiteUrl': SITE}
P = lambda n: VALUES[n]
def sp(op, params):
    return {'type': 'OpenApiConnection', 'inputs': {'host': {'apiId': '/providers/Microsoft.PowerApps/apis/shared_sharepointonline', 'connectionName': 'shared_sharepointonline', 'operationId': op},
            'parameters': params, 'authentication': "@parameters('$authentication')"}}
def mail(to, subject, body, cc=None):
    return {'type': 'OpenApiConnection', 'inputs': {'host': {'apiId': '/providers/Microsoft.PowerApps/apis/shared_sendmail', 'connectionName': 'shared_sendmail', 'operationId': 'SendEmailV3'},
            'parameters': {'request/to': to, 'request/subject': subject, 'request/text': body}, 'authentication': "@parameters('$authentication')"}}
T = lambda f: f"triggerOutputs()?['body/{f}']"
RN, TITLE, STATUS, SUBMITTED = T('Title'), T('RequestTitle'), T('field_5/Value'), T('field_6')
LINK = f"{P('AppBaseUrl')}&RequestID=@{{{T('ID')}}}"
DATE = f"@{{convertTimeZone({SUBMITTED},'UTC','Romance Standard Time','dd-MM-yyyy HH:mm')}}"
ASSIGNEE_TO = (f"@{{if(empty(coalesce({T('Assignee/Email')},'')), join(body('Select_administrator_emails'),';'), "
               f"concat({T('Assignee/Email')}, if(empty(coalesce({T('CoAssignee/Email')},'')), '', concat(';', {T('CoAssignee/Email')}))))}}")
BODY_ADMIN = f'''<p>Hello,</p>
<p>A new request has been submitted and is waiting for review.</p>
<table style="border-collapse:collapse" cellpadding="3">
<tr><td><b>Request</b></td><td>@{{{RN}}} &middot; @{{{TITLE}}}</td></tr>
<tr><td><b>Requestor</b></td><td>@{{{T('Author/DisplayName')}}} (@{{{T('Author/Email')}}})</td></tr>
<tr><td><b>Department</b></td><td>@{{{T('field_1/Value')}}}</td></tr>
<tr><td><b>Production type</b></td><td>@{{{T('production_type_request/Value')}}}</td></tr>
<tr><td><b>Media files</b></td><td>@{{length(body('Get_media_files')?['value'])}}</td></tr>
<tr><td><b>Submitted</b></td><td>{DATE}</td></tr>
<tr><td><b>Assigned to</b></td><td>@{{coalesce({T('Assignee/DisplayName')}, 'Not assigned yet')}}</td></tr>
</table>
<p>@{{body('Create_HTML_table')}}</p>
<p><a href="{LINK}">Open the request in Central Deposit</a></p>
<p>Audiovisual Service, DG COMM</p>'''
BODY_REQUESTOR = f'''<p>Hello @{{{T('Author/DisplayName')}}},</p>
<p>Your request <b>@{{{RN}}} &middot; @{{{TITLE}}}</b> has been submitted and is now <b>Processing</b>. The Audiovisual Service will review it and you will receive an e-mail with the decision.</p>
<p>While the request is in Processing you can read it but not change it. If we need more information we will send it back to you.</p>
<p><a href="{LINK}">Open your request</a></p>
<p>Audiovisual Service, DG COMM</p>'''
BODY_ERROR = f'''<p>Flow <b>CD - 01 Request submitted</b> failed for request @{{{RN}}}.</p>
<p>Run: @{{workflow()?['run']?['name']}}</p><p>@{{string(result('Scope_-_Main'))}}</p>'''
def flow01():
    main = {
        'Get_administrators': sp('GetItems', {'dataset': P('SiteUrl'), 'table': LIST['roles'], '$filter': "Role eq 'ADMINISTRATOR'", '$top': 100}),
        'Select_administrator_emails': {'type': 'Select', 'runAfter': {'Get_administrators': ['Succeeded']},
            'inputs': {'from': "@body('Get_administrators')?['value']", 'select': "@item()?['UserEmail']?['Email']"}},
        'Get_media_files': {**sp('GetItems', {'dataset': P('SiteUrl'), 'table': LIST['media'], '$filter': f"field_30 eq '@{{{RN}}}'", '$top': 100}), 'runAfter': {'Select_administrator_emails': ['Succeeded']}},
        'Select_media': {'type': 'Select', 'runAfter': {'Get_media_files': ['Succeeded']},
            'inputs': {'from': "@body('Get_media_files')?['value']", 'select': {'Media': "@item()?['Title']", 'Title': "@item()?['ProductionTitle']", 'Type': "@item()?['field_25']?['Value']"}}},
        'Create_HTML_table': {'type': 'Table', 'runAfter': {'Select_media': ['Succeeded']}, 'inputs': {'from': "@body('Select_media')", 'format': 'HTML'}},
        'Send_e-mail_to_administrators': {**mail(ASSIGNEE_TO, f"[Central Deposit] New request to review: @{{{RN}}} · @{{{TITLE}}}", BODY_ADMIN), 'runAfter': {'Create_HTML_table': ['Succeeded']}},
        'Send_e-mail_to_requestor': {**mail(f"@{{{T('Author/Email')}}}", f"[Central Deposit] Request @{{{RN}}} submitted", BODY_REQUESTOR), 'runAfter': {'Send_e-mail_to_administrators': ['Succeeded']}},
        'Mark_as_notified': {**sp('PatchItem', {'dataset': P('SiteUrl'), 'table': LIST['requests'], 'id': f"@{T('ID')}", 'item/Title': f"@{RN}", 'item/field_5/Value': f"@{STATUS}",
                                               'item/SubmissionNotifiedOn': "@utcNow()"}), 'runAfter': {'Send_e-mail_to_requestor': ['Succeeded']}},
    }
    actions = {
        'Initialize_SupportMailbox': {'type': 'InitializeVariable', 'runAfter': {}, 'inputs': {'variables': [{'name': 'SupportMailbox', 'type': 'string', 'value': 'audiovisual-service@ec.europa.eu'}]}},
        'Scope_-_Main': {'type': 'Scope', 'runAfter': {'Initialize_SupportMailbox': ['Succeeded']}, 'actions': main},
        'Scope_-_Catch': {'type': 'Scope', 'runAfter': {'Scope_-_Main': ['Failed', 'TimedOut']},
                          'actions': {'Send_failure_e-mail': mail("@{variables('SupportMailbox')}", f"[Central Deposit] Flow failed: request @{{{RN}}}", BODY_ERROR)}},
    }
    trigger = {'recurrence': {'interval': 1, 'frequency': 'Minute'}, 'splitOn': "@triggerOutputs()?['body/value']", 'metadata': {'operationMetadataId': G('trigger01').lower()},
               'type': 'OpenApiConnection',
               'inputs': {'host': {'apiId': '/providers/Microsoft.PowerApps/apis/shared_sharepointonline', 'connectionName': 'shared_sharepointonline', 'operationId': 'GetOnChangedItems'},
                          'parameters': {'dataset': P('SiteUrl'), 'table': LIST['requests']}, 'authentication': "@parameters('$authentication')"},
               'conditions': [{'expression': f"@and(equals({STATUS}, 'Processing'), empty(coalesce({T('field_11')}, '')), empty(coalesce({T('SubmissionNotifiedOn')}, '')))"}],
               'runtimeConfiguration': {'concurrency': {'runs': 1}}}
    return {'properties': {'connectionReferences': {
                'shared_sharepointonline': {'runtimeSource': 'embedded', 'connection': {'connectionReferenceLogicalName': CONN_SP}, 'api': {'name': 'shared_sharepointonline'}},
                'shared_sendmail': {'runtimeSource': 'embedded', 'connection': {'connectionReferenceLogicalName': CONN_MAIL}, 'api': {'name': 'shared_sendmail'}}},
            'definition': {'$schema': 'https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#', 'contentVersion': '1.0.0.0',
                           'parameters': {'$connections': {'defaultValue': {}, 'type': 'Object'}, '$authentication': {'defaultValue': {}, 'type': 'SecureObject'}},
                           'triggers': {'When_a_request_is_submitted': trigger}, 'actions': actions},
            'templateName': None}, 'schemaVersion': '1.0.0.0'}
def xml_pretty(s):
    s = re.sub(r'>\s+<', '><', s.strip())
    xml.dom.minidom.parseString(s.encode('utf-8'))
    return '<?xml version="1.0" encoding="utf-8"?>' + s
FLOWS = [('CD - 01 Request submitted', WF1, 'CD-01RequestSubmitted', flow01())]
if ALL:
    exec(open(os.path.join(HERE, 'flows_all.py'), encoding='utf-8').read())
    FLOWS[0][3]['properties']['definition']['actions']['Scope_-_Main']['actions']['Mark_as_notified']['inputs']['parameters']['item/LastNotifiedStatus'] = 'Processing'
    if SKIP1: FLOWS.pop(0)
    for n, fn, f in (('CD - 02 Status changed', 'CD-02StatusChanged', flow02), ('CD - 03 Resubmitted', 'CD-03Resubmitted', flow03), ('CD - 04 Assignment', 'CD-04Assignment', flow04),
                     ('CD - 05 Second approval', 'CD-05SecondApproval', flow05), ('CD - 06 New message', 'CD-06NewMessage', flow06),
                     ('CD - 07 Unread messages', 'CD-07UnreadMessages', flow07), ('CD - 08 Reminders', 'CD-08Reminders', flow08)):
        FLOWS.append((n, G('flow' + fn[3:5]), fn, f()))
def customizations():
    wf = ''.join(f'''<Workflow WorkflowId="{{{gid.lower()}}}" Name="{name}"><JsonFileName>/Workflows/{fn}-{gid}.json</JsonFileName><Type>1</Type><Subprocess>0</Subprocess><Category>5</Category>
<Mode>0</Mode><Scope>4</Scope><OnDemand>0</OnDemand><TriggerOnCreate>0</TriggerOnCreate><TriggerOnDelete>0</TriggerOnDelete><AsyncAutodelete>0</AsyncAutodelete>
<SyncWorkflowLogOnFailure>0</SyncWorkflowLogOnFailure><StateCode>0</StateCode><StatusCode>1</StatusCode><RunAs>1</RunAs><IsTransacted>1</IsTransacted>
<IntroducedVersion>{VERSION}</IntroducedVersion><IsCustomizable>1</IsCustomizable><BusinessProcessType>0</BusinessProcessType>
<IsCustomProcessingStepAllowedForOtherPublishers>1</IsCustomProcessingStepAllowedForOtherPublishers><ModernFlowType>0</ModernFlowType><PrimaryEntity>none</PrimaryEntity>
<LocalizedNames><LocalizedName languagecode="1033" description="{name}" /></LocalizedNames></Workflow>''' for name, gid, fn, _ in FLOWS)
    conns = ''.join(f'''<connectionreference connectionreferencelogicalname="{n}"><connectionreferencedisplayname>{d}</connectionreferencedisplayname>
<connectorid>/providers/Microsoft.PowerApps/apis/{c}</connectorid><iscustomizable>1</iscustomizable><promptingbehavior>0</promptingbehavior><statecode>0</statecode><statuscode>1</statuscode></connectionreference>'''
                    for n, d, c in ((CONN_SP, 'SharePoint', 'shared_sharepointonline'), (CONN_MAIL, 'Mail', 'shared_sendmail')) + (((CONN_APPR, 'Approvals', 'shared_approvals'),) if ALL else ()))
    return xml_pretty(f'''<ImportExportXml xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" OrganizationVersion="9.2.26092.157" OrganizationSchemaType="Standard" CRMServerServiceabilityVersion="9.2.26092.00157">
<Entities /><Roles /><Workflows>{wf}</Workflows><FieldSecurityProfiles /><Templates /><EntityMaps /><EntityRelationships /><OrganizationSettings /><optionsets />
<CustomControls /><EntityDataProviders />
<connectionreferences>{conns}</connectionreferences><Languages><Language>1033</Language></Languages></ImportExportXml>''')
def solution():
    roots = ''.join(f'<RootComponent type="29" id="{{{gid.lower()}}}" behavior="0" />' for _, gid, _, _ in FLOWS)
    addr = lambda n: f'<Address><AddressNumber>{n}</AddressNumber><AddressTypeCode xsi:nil="true"></AddressTypeCode><City xsi:nil="true"></City><County xsi:nil="true"></County><Country xsi:nil="true"></Country><Fax xsi:nil="true"></Fax><FreightTermsCode xsi:nil="true"></FreightTermsCode><ImportSequenceNumber xsi:nil="true"></ImportSequenceNumber><Latitude xsi:nil="true"></Latitude><Line1 xsi:nil="true"></Line1><Line2 xsi:nil="true"></Line2><Line3 xsi:nil="true"></Line3><Longitude xsi:nil="true"></Longitude><Name xsi:nil="true"></Name><PostalCode xsi:nil="true"></PostalCode><PostOfficeBox xsi:nil="true"></PostOfficeBox><PrimaryContactName xsi:nil="true"></PrimaryContactName><ShippingMethodCode xsi:nil="true"></ShippingMethodCode><StateOrProvince xsi:nil="true"></StateOrProvince><Telephone1 xsi:nil="true"></Telephone1><Telephone2 xsi:nil="true"></Telephone2><Telephone3 xsi:nil="true"></Telephone3><TimeZoneRuleVersionNumber xsi:nil="true"></TimeZoneRuleVersionNumber><UPSZone xsi:nil="true"></UPSZone><UTCOffset xsi:nil="true"></UTCOffset><UTCConversionTimeZoneCode xsi:nil="true"></UTCConversionTimeZoneCode></Address>'
    return xml_pretty(f'''<ImportExportXml version="9.2.26092.157" SolutionPackageVersion="9.2" languagecode="1033" generatedBy="CrmLive" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" OrganizationVersion="9.2.26092.157" OrganizationSchemaType="Standard" CRMServerServiceabilityVersion="9.2.26092.00157">
<SolutionManifest><UniqueName>CentralDepositFlows</UniqueName>
<LocalizedNames><LocalizedName description="Central Deposit flows" languagecode="1033" /></LocalizedNames><Descriptions />
<Version>{VERSION}</Version><Managed>0</Managed>
<Publisher><UniqueName>{PUBLISHER}</UniqueName><LocalizedNames><LocalizedName description="Central Deposit Team" languagecode="1033" /></LocalizedNames>
<Descriptions><Description description="Central Deposit Team" languagecode="1033" /></Descriptions>
<EMailAddress xsi:nil="true"></EMailAddress><SupportingWebsiteUrl xsi:nil="true"></SupportingWebsiteUrl>
<CustomizationPrefix>{PREFIX}</CustomizationPrefix><CustomizationOptionValuePrefix>51206</CustomizationOptionValuePrefix>
<Addresses>{addr(1)}{addr(2)}</Addresses></Publisher>
<RootComponents>{roots}</RootComponents><MissingDependencies /></SolutionManifest></ImportExportXml>''')
def envdef(k, d, v):
    return xml_pretty(f'''<environmentvariabledefinition schemaname="{k}"><defaultvalue>{v.replace('&', '&amp;')}</defaultvalue>
<displayname default="{d}"><label description="{d}" languagecode="1033" /></displayname><introducedversion>{VERSION}</introducedversion><iscustomizable>1</iscustomizable>
<isrequired>0</isrequired><secretstore>0</secretstore><type>100000000</type></environmentvariabledefinition>''')
CT = '<?xml version="1.0" encoding="utf-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="xml" ContentType="application/octet-stream" /><Default Extension="json" ContentType="application/octet-stream" /></Types>'
out = os.path.join(HERE, f'CentralDepositFlows_{VERSION.replace(".", "_")}.zip')
files = {'[Content_Types].xml': CT, 'solution.xml': solution(), 'customizations.xml': customizations()}
for name, gid, fn, flow in FLOWS:
    files[f'Workflows/{fn}-{gid}.json'] = json.dumps(flow, indent=2, ensure_ascii=False)
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
    for n, c in files.items(): z.writestr(n, c)
# self-checks
for n, c in files.items():
    if n.endswith('.xml'): xml.dom.minidom.parseString(c.encode('utf-8'))
    if n.endswith('.json'):
        json.loads(c)
        for e in re.findall(r'@\{([^}]*)\}', c):
            assert e.count('(') == e.count(')'), e
print('written', out, len(files), 'files')
