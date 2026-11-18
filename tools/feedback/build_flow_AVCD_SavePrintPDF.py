#!/usr/bin/env python3
"""Builds the import packages of the Power Automate flow AVCD_SavePrintPDF:
  - AVCD_SavePrintPDF_solution.zip : unmanaged Dataverse solution (Power Automate > Solutions > Import solution)
  - AVCD_SavePrintPDF_legacy.zip   : legacy package (My flows > Import > Import Package (Legacy))
The flow saves a PDF in the library AV-CD-Exports only when the caller is an ADMINISTRATOR in AV-CD-RolesPermissionsList."""
import json, uuid, zipfile, datetime, io, os
OUT = '/home/user/PowerApps_AJF/docs/flows'
SITE = 'https://eceuropaeu.sharepoint.com/teams/GRP-EBSProductionForm'
ROLES_LIST = '58e5019a-29bb-4cca-94dd-733e418619a0'      # AV-CD-RolesPermissionsList
LIBRARY = '/AVCDExports'
PRINTS = '/AVCDPrints'
PRINTS_LIB = 'AVCDPrints'
NAME = 'AVCD_SavePrintPDF'
FLOW_ID = 'b6f2a3d1-4c7e-4e0a-9a51-2d7c8e6f1a01'
CR_LOGICAL = 'avcd_sharedsharepointonline_pdfexport'
API = '/providers/Microsoft.PowerApps/apis/shared_sharepointonline'
def sp(op, params):
    return {'type': 'OpenApiConnection',
            'inputs': {'host': {'connectionName': 'shared_sharepointonline', 'operationId': op, 'apiId': API},
                       'parameters': params, 'authentication': "@parameters('$authentication')"}}
CALLER = "toLower(coalesce(triggerOutputs()?['headers']?['x-ms-user-email'], ''))"
def respond(url_expr, status, msg):
    return {'type': 'Response', 'kind': 'PowerApp',
            'inputs': {'statusCode': 200,
                       'body': {'fileurl': url_expr, 'status': status, 'message': msg},
                       'schema': {'type': 'object', 'properties': {
                           'fileurl': {'title': 'fileurl', 'x-ms-dynamically-added': True, 'type': 'string'},
                           'status': {'title': 'status', 'x-ms-dynamically-added': True, 'type': 'string'},
                           'message': {'title': 'message', 'x-ms-dynamically-added': True, 'type': 'string'}}}}}
definition = {
    '$schema': 'https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#',
    'contentVersion': '1.0.0.0',
    'parameters': {'$connections': {'defaultValue': {}, 'type': 'Object'}, '$authentication': {'defaultValue': {}, 'type': 'SecureObject'}},
    'triggers': {'manual': {
        'type': 'Request', 'kind': 'PowerAppV2',
        'inputs': {'schema': {'type': 'object', 'required': ['text', 'file'], 'properties': {
            'text': {'title': 'FileName', 'type': 'string', 'x-ms-dynamically-added': True, 'description': 'PDF file name, e.g. 26-0023_Photo_20261117-1530.pdf', 'x-ms-content-hint': 'TEXT'},
            'file': {'title': 'PdfFile', 'type': 'object', 'x-ms-dynamically-added': True, 'description': 'The PDF produced by PDF() in the app', 'x-ms-content-hint': 'FILE',
                     'properties': {'name': {'type': 'string'}, 'contentBytes': {'type': 'string', 'format': 'byte'}}},
            'mode': {'title': 'Mode', 'type': 'string', 'x-ms-dynamically-added': True, 'description': 'print = copy for the user to print or save (any app user); empty = archive in AVCDExports (administrators)', 'x-ms-content-hint': 'TEXT'}}}}}},
    'actions': {
        'Get_administrators': {**sp('GetItems', {'dataset': SITE, 'table': ROLES_LIST, '$filter': "Role eq 'ADMINISTRATOR'", '$top': 500}),
                               'runAfter': {}, 'description': 'Administrators of the app (AV-CD-RolesPermissionsList, Role = ADMINISTRATOR)'},
        'Filter_caller_is_administrator': {
            'type': 'Query', 'runAfter': {'Get_administrators': ['Succeeded']},
            'inputs': {'from': "@outputs('Get_administrators')?['body/value']",
                       'where': f"@equals(toLower(coalesce(item()?['UserEmail']?['Email'], '')), {CALLER})"},
            'description': 'Keeps the administrator whose e-mail is the e-mail of the person who pressed the button in the app'},
        'Is_print_copy': {
            'type': 'If', 'runAfter': {'Filter_caller_is_administrator': ['Succeeded']},
            'description': 'Mode = print: a copy for the person who pressed Download PDF, in AVCDPrints, opened through a view-only link',
            'expression': {'and': [{'equals': ["@toLower(coalesce(triggerBody()?['mode'], ''))", 'print']}]},
            'actions': {
                'Create_print_file': {**sp('CreateFile', {'dataset': SITE, 'folderPath': PRINTS,
                                                          'name': "@triggerBody()?['text']",
                                                          'body': "@base64ToBinary(triggerBody()?['file']?['contentBytes'])"}),
                                      'runAfter': {}, 'runtimeConfiguration': {'contentTransfer': {'transferMode': 'Chunked'}}},
                'Create_view_link': {**sp('CreateSharingLink', {'dataset': SITE, 'table': PRINTS_LIB,
                                                                'id': "@body('Create_print_file')?['ItemId']",
                                                                'permission/type': 'view', 'permission/scope': 'organization'}),
                                     'runAfter': {'Create_print_file': ['Succeeded']}},
                'Respond_print_link': {**respond("@body('Create_view_link')?['link']?['webUrl']", 'saved', 'The PDF is ready to print or save.'),
                                       'runAfter': {'Create_view_link': ['Succeeded']}},
                'Respond_print_failed': {**respond('', 'error', 'The PDF could not be prepared for download (check the AVCDPrints library and the flow connection).'),
                                         'runAfter': {'Create_view_link': ['Failed', 'TimedOut', 'Skipped']}}},
            'else': {'actions': {}}},
        'Caller_is_administrator': {
            'type': 'If', 'runAfter': {'Is_print_copy': ['Succeeded']},
            'expression': {'and': [{'not': {'equals': ["@toLower(coalesce(triggerBody()?['mode'], ''))", 'print']}},
                                   {'greater': ["@length(body('Filter_caller_is_administrator'))", 0]}]},
            'actions': {
                'Create_file': {**sp('CreateFile', {'dataset': SITE, 'folderPath': LIBRARY,
                                                    'name': "@triggerBody()?['text']",
                                                    'body': "@base64ToBinary(triggerBody()?['file']?['contentBytes'])"}),
                                'runAfter': {}, 'runtimeConfiguration': {'contentTransfer': {'transferMode': 'Chunked'}}},
                'Respond_saved': {**respond(f"@{{concat('{SITE}', body('Create_file')?['Path'])}}", 'saved', 'The PDF was saved in AVCDExports.'),
                                  'runAfter': {'Create_file': ['Succeeded']}},
                'Respond_save_failed': {**respond('', 'error', 'The PDF could not be saved in AVCDExports (check the library and the flow connection).'),
                                        'runAfter': {'Create_file': ['Failed', 'TimedOut']}}},
            'else': {'actions': {
                'Not_a_print_copy': {'type': 'If', 'runAfter': {},
                                     'expression': {'and': [{'not': {'equals': ["@toLower(coalesce(triggerBody()?['mode'], ''))", 'print']}}]},
                                     'actions': {'Respond_not_administrator': {**respond('', 'denied', 'Only administrators can save the PDF in AV-CD-Exports.'), 'runAfter': {}}},
                                     'else': {'actions': {}}}}}}},
    'outputs': {}}

# 1.0.0.2: one path for every app user (administrators and requestors): the PDF is saved in AVCDExports and the link is returned.
definition['actions'] = {
    'Create_file': {**sp('CreateFile', {'dataset': SITE, 'folderPath': LIBRARY,
                                        'name': "@triggerBody()?['text']",
                                        'body': "@base64ToBinary(triggerBody()?['file']?['contentBytes'])"}),
                    'runAfter': {}, 'runtimeConfiguration': {'contentTransfer': {'transferMode': 'Chunked'}},
                    'description': 'Saves the PDF of the print preview in AVCDExports'},
    'Respond_saved': {**respond(f"@{{concat('{SITE}', body('Create_file')?['Path'])}}", 'saved', 'The PDF was saved.'),
                      'runAfter': {'Create_file': ['Succeeded']}},
    'Respond_save_failed': {**respond('', 'error', 'The PDF could not be saved in AVCDExports (check the library and the flow connection).'),
                            'runAfter': {'Create_file': ['Failed', 'TimedOut']}}}
def workflow_json(conn_refs):
    return {'properties': {'connectionReferences': conn_refs, 'definition': definition, 'templateName': ''}, 'schemaVersion': '1.0.0.0'}

# ---------- 1. solution
sol_conn = {'shared_sharepointonline': {'runtimeSource': 'embedded', 'connection': {'connectionReferenceLogicalName': CR_LOGICAL},
                                        'api': {'name': 'shared_sharepointonline'}}}
wf_file = f'Workflows/{NAME}-{FLOW_ID.upper()}.json'
solution_xml = f'''<ImportExportXml version="9.2.24101.200" SolutionPackageVersion="9.2" languagecode="1033" generatedBy="CrmLive" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" OrganizationVersion="9.2.24101.200" OrganizationSchemaType="Standard" CRMServerServiceabilityVersion="9.2.24101.00200">
  <SolutionManifest>
    <UniqueName>AVCDPrintPDF</UniqueName>
    <LocalizedNames>
      <LocalizedName description="AV-CD Print PDF" languagecode="1033" />
    </LocalizedNames>
    <Descriptions>
      <Description description="Flow AVCD_SavePrintPDF: saves the print PDF of a request in AVCDExports and returns its link (every app user)." languagecode="1033" />
    </Descriptions>
    <Version>1.0.0.2</Version>
    <Managed>0</Managed>
    <Publisher>
      <UniqueName>avcd</UniqueName>
      <LocalizedNames>
        <LocalizedName description="AV Central Deposit" languagecode="1033" />
      </LocalizedNames>
      <Descriptions>
        <Description description="AV Central Deposit" languagecode="1033" />
      </Descriptions>
      <EMailAddress xsi:nil="true"></EMailAddress>
      <SupportingWebsiteUrl xsi:nil="true"></SupportingWebsiteUrl>
      <CustomizationPrefix>avcd</CustomizationPrefix>
      <CustomizationOptionValuePrefix>51234</CustomizationOptionValuePrefix>
      <Addresses>
        <Address>
          <AddressNumber>1</AddressNumber>
          <AddressTypeCode>1</AddressTypeCode>
          <City xsi:nil="true"></City>
          <County xsi:nil="true"></County>
          <Country xsi:nil="true"></Country>
          <Fax xsi:nil="true"></Fax>
          <FreightTermsCode xsi:nil="true"></FreightTermsCode>
          <ImportSequenceNumber xsi:nil="true"></ImportSequenceNumber>
          <Latitude xsi:nil="true"></Latitude>
          <Line1 xsi:nil="true"></Line1>
          <Line2 xsi:nil="true"></Line2>
          <Line3 xsi:nil="true"></Line3>
          <Longitude xsi:nil="true"></Longitude>
          <Name xsi:nil="true"></Name>
          <PostalCode xsi:nil="true"></PostalCode>
          <PostOfficeBox xsi:nil="true"></PostOfficeBox>
          <PrimaryContactName xsi:nil="true"></PrimaryContactName>
          <ShippingMethodCode>1</ShippingMethodCode>
          <StateOrProvince xsi:nil="true"></StateOrProvince>
          <Telephone1 xsi:nil="true"></Telephone1>
          <Telephone2 xsi:nil="true"></Telephone2>
          <Telephone3 xsi:nil="true"></Telephone3>
          <TimeZoneRuleVersionNumber xsi:nil="true"></TimeZoneRuleVersionNumber>
          <UPSZone xsi:nil="true"></UPSZone>
          <UTCOffset xsi:nil="true"></UTCOffset>
          <UTCConversionTimeZoneCode xsi:nil="true"></UTCConversionTimeZoneCode>
        </Address>
        <Address>
          <AddressNumber>2</AddressNumber>
          <AddressTypeCode>1</AddressTypeCode>
          <City xsi:nil="true"></City>
          <County xsi:nil="true"></County>
          <Country xsi:nil="true"></Country>
          <Fax xsi:nil="true"></Fax>
          <FreightTermsCode xsi:nil="true"></FreightTermsCode>
          <ImportSequenceNumber xsi:nil="true"></ImportSequenceNumber>
          <Latitude xsi:nil="true"></Latitude>
          <Line1 xsi:nil="true"></Line1>
          <Line2 xsi:nil="true"></Line2>
          <Line3 xsi:nil="true"></Line3>
          <Longitude xsi:nil="true"></Longitude>
          <Name xsi:nil="true"></Name>
          <PostalCode xsi:nil="true"></PostalCode>
          <PostOfficeBox xsi:nil="true"></PostOfficeBox>
          <PrimaryContactName xsi:nil="true"></PrimaryContactName>
          <ShippingMethodCode>1</ShippingMethodCode>
          <StateOrProvince xsi:nil="true"></StateOrProvince>
          <Telephone1 xsi:nil="true"></Telephone1>
          <Telephone2 xsi:nil="true"></Telephone2>
          <Telephone3 xsi:nil="true"></Telephone3>
          <TimeZoneRuleVersionNumber xsi:nil="true"></TimeZoneRuleVersionNumber>
          <UPSZone xsi:nil="true"></UPSZone>
          <UTCOffset xsi:nil="true"></UTCOffset>
          <UTCConversionTimeZoneCode xsi:nil="true"></UTCConversionTimeZoneCode>
        </Address>
      </Addresses>
    </Publisher>
    <RootComponents>
      <RootComponent type="29" id="{{{FLOW_ID}}}" behavior="0" />
    </RootComponents>
    <MissingDependencies />
  </SolutionManifest>
</ImportExportXml>
'''
customizations_xml = f'''<ImportExportXml xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" OrganizationVersion="9.2.24101.200" OrganizationSchemaType="Standard" CRMServerServiceabilityVersion="9.2.24101.00200">
  <Entities />
  <Roles />
  <Workflows>
    <Workflow WorkflowId="{{{FLOW_ID}}}" Name="{NAME}">
      <JsonFileName>/{wf_file}</JsonFileName>
      <Type>1</Type>
      <Subprocess>0</Subprocess>
      <Category>5</Category>
      <Mode>0</Mode>
      <Scope>4</Scope>
      <OnDemand>0</OnDemand>
      <TriggerOnCreate>0</TriggerOnCreate>
      <TriggerOnDelete>0</TriggerOnDelete>
      <AsyncAutodelete>0</AsyncAutodelete>
      <SyncWorkflowLogOnFailure>0</SyncWorkflowLogOnFailure>
      <StateCode>0</StateCode>
      <StatusCode>1</StatusCode>
      <RunAs>1</RunAs>
      <IsTransacted>1</IsTransacted>
      <IntroducedVersion>1.0.0.0</IntroducedVersion>
      <IsCustomizable>1</IsCustomizable>
      <BusinessProcessType>0</BusinessProcessType>
      <IsCustomProcessingStepAllowedForOtherPublishers>1</IsCustomProcessingStepAllowedForOtherPublishers>
      <PrimaryEntity>none</PrimaryEntity>
      <LocalizedNames>
        <LocalizedName languagecode="1033" description="{NAME}" />
      </LocalizedNames>
    </Workflow>
  </Workflows>
  <FieldSecurityProfiles />
  <Templates />
  <EntityMaps />
  <EntityRelationships />
  <OrganizationSettings />
  <optionsets />
  <CustomControls />
  <EntityDataProviders />
  <connectionreferences>
    <connectionreference connectionreferencelogicalname="{CR_LOGICAL}">
      <connectionreferencedisplayname>AV-CD SharePoint (print PDF)</connectionreferencedisplayname>
      <connectorid>{API}</connectorid>
      <iscustomizable>1</iscustomizable>
      <promptingbehavior>0</promptingbehavior>
      <statecode>0</statecode>
      <statuscode>1</statuscode>
    </connectionreference>
  </connectionreferences>
  <Languages>
    <Language>1033</Language>
  </Languages>
</ImportExportXml>
'''
content_types = '''<?xml version="1.0" encoding="utf-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="xml" ContentType="application/octet-stream" /><Default Extension="json" ContentType="application/octet-stream" /></Types>'''
p = f'{OUT}/{NAME}_solution.zip'
with zipfile.ZipFile(p, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('[Content_Types].xml', content_types)
    z.writestr('solution.xml', '<?xml version="1.0" encoding="utf-8"?>\n' + solution_xml)
    z.writestr('customizations.xml', '<?xml version="1.0" encoding="utf-8"?>\n' + customizations_xml)
    z.writestr(wf_file, json.dumps(workflow_json(sol_conn), indent=2))
print('wrote', p)

# ---------- 2. legacy package
FLOW_RES, API_RES, CONN_RES = str(uuid.uuid5(uuid.NAMESPACE_URL, 'avcd-flow')), str(uuid.uuid5(uuid.NAMESPACE_URL, 'avcd-api')), str(uuid.uuid5(uuid.NAMESPACE_URL, 'avcd-conn'))
ICON = 'https://connectoricons-prod.azureedge.net/releases/v1.0.1676/1.0.1676.3617/sharepointonline/icon.png'
manifest = {'schema': '1.0', 'details': {'displayName': NAME, 'description': 'Saves the print PDF of a request in AVCDExports and returns its link (every app user).',
            'createdTime': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.0000000Z'), 'packageTelemetryId': str(uuid.uuid4()),
            'creator': 'AV Central Deposit', 'sourceEnvironment': ''},
            'resources': {
                FLOW_RES: {'type': 'Microsoft.Flow/flows', 'suggestedCreationType': 'New', 'creationType': 'Existing, New, Update',
                           'details': {'displayName': NAME}, 'configurableBy': 'User', 'hierarchy': 'Root', 'dependsOn': [API_RES, CONN_RES]},
                API_RES: {'id': API, 'name': 'shared_sharepointonline', 'type': 'Microsoft.PowerApps/apis', 'suggestedCreationType': 'Existing',
                          'details': {'displayName': 'SharePoint', 'iconUri': ICON}, 'configurableBy': 'System', 'hierarchy': 'Child', 'dependsOn': []},
                CONN_RES: {'type': 'Microsoft.PowerApps/apis/connections', 'suggestedCreationType': 'Existing', 'creationType': 'Existing',
                           'details': {'displayName': 'SharePoint', 'iconUri': ICON}, 'configurableBy': 'User', 'hierarchy': 'Child', 'dependsOn': [API_RES]}}}
leg_def = {'name': FLOW_ID, 'id': f'/providers/Microsoft.Flow/flows/{FLOW_ID}', 'type': 'Microsoft.Flow/flows',
           'properties': {'apiId': '/providers/Microsoft.PowerApps/apis/shared_logicflows', 'displayName': NAME, 'definition': definition,
                          'connectionReferences': {'shared_sharepointonline': {'connectionName': 'shared-sharepointonl-00000000-0000-0000-0000-000000000000',
                                                                               'source': 'Embedded', 'id': API, 'tier': 'NotSpecified'}},
                          'flowFailureAlertSubscribed': False, 'isManaged': False}}
p = f'{OUT}/{NAME}_legacy.zip'
base = f'Microsoft.Flow/flows/{FLOW_ID}'
with zipfile.ZipFile(p, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('manifest.json', json.dumps(manifest, indent=2))
    z.writestr('Microsoft.Flow/flows/manifest.json', json.dumps({'packageSchemaVersion': '1.0', 'flowAssets': {'assetPaths': [FLOW_ID]}}, indent=2))
    z.writestr(f'{base}/definition.json', json.dumps(leg_def, indent=2))
    z.writestr(f'{base}/apisMap.json', json.dumps({'shared_sharepointonline': API_RES}, indent=2))
    z.writestr(f'{base}/connectionsMap.json', json.dumps({'shared_sharepointonline': CONN_RES}, indent=2))
print('wrote', p)
open(f'{OUT}/{NAME}_definition.json', 'w').write(json.dumps(definition, indent=2))
