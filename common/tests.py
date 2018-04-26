import zendesk

a = zendesk.Parser()
zd_file = 'L:\OSC\DataSources\ZendeskExports\export-2018-04-20-1120-234063-360000053233b409.csv'

dicts = a.index_zd_data(zd_file)

