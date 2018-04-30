from oatsutils import DOI_CLEANUP, DOI_FIX, prune_and_cleanup_string

class Parser():

    def __init__(self):
        self.doi2handle = {}

    def populate_doi2handle(self, apolloexport, enc='utf-8'):
        '''
        This function takes a CSV file exported by Apollo and builds a dictionary
        translating DOIs to Apollo handles
        :param apolloexport: input CSV file
        :return: doi2apollo dictionary
        '''

        with open(apolloexport, encoding = enc) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                apollo_handle = row['handle']
                if len(row['rioxxterms.versionofrecord'].strip()) > 5:
                    doi = prune_and_cleanup_string(row['rioxxterms.versionofrecord'], DOI_CLEANUP, DOI_FIX)
                else:
                    doi = prune_and_cleanup_string(row['dc.identifier.uri'].split(',')[0], DOI_CLEANUP, DOI_FIX)
                self.doi2handle[doi] = apollo_handle

        return self.doi2handle