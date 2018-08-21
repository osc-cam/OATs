ZENDESK_EXCLUDED_GROUPS = ['Cron Jobs',
                           'Request a Copy',
                           'Social Media',
                           'Thesis',
                           'Office of Scholarly Communication',
                           'OPs',
                           'Research Data',
                           'Repository'
                           ]

ZENDESK_EXCLUDED_REQUESTERS = ['Dspace',
                               'JIRA Integratrion',
                               'photo',
                               'Accountdashboard',
                               'Cs-onlineopen',
                               'Uptime Robot',
                               'Authorhelpdesk'
                               ]

# declare formats
JISC_FORMAT = ['Date of acceptance',
 'PubMed ID',
 'DOI',
 'Publisher',
 'Journal',
 'E-ISSN',
 'Type of publication',
 'Article title',
 'Date of publication',
 'Fund that APC is paid from (1)',
 'Fund that APC is paid from (2)',
 'Fund that APC is paid from (3)',
 'Funder of research (1)',
 'Grant ID (1)',
 'Funder of research (2)',
 'Grant ID (2)',
 'Funder of research (3)',
 'Grant ID (3)',
 'Date of APC payment',
 'APC paid (actual currency) excluding VAT',
 'Currency of APC',
 'APC paid (£) including VAT if charged',
 'Additional publication costs (£)',
 'Discounts, memberships & pre-payment agreements',
 'Amount of APC charged to COAF grant (including VAT if charged) in £',
 'Amount of APC charged to RCUK OA fund (including VAT if charged) in £',
 'Licence',
 'Notes']

JISC_FORMAT_EXPANDED = JISC_FORMAT + ['id',  # ZD number from zd
                         '#externalID [txt]',  # OA number from zd
                         'Reason for exclusion',  # field calculated and appended by ART
                         # 'Description',             # field from CUFS (RCUK)
                         # 'Ref 1',                   # field from CUFS (RCUK)
                         # 'Ref 5',                   # field from CUFS (RCUK)
                         'Comment',  # field from CUFS (COAF)
                         'Invoice',  # field from CUFS (COAF)
                         'RCUK policy [flag]',  # from zd
                         'RCUK payment [flag]',  # from zd
                         'COAF policy [flag]',  # from zd
                         'COAF payment [flag]',  # from zd
                         'handle'  # from Apollo
                         ]