"""
Testing module for Virtual Watershed Data adaptor.
"""

from ..watershed import make_watershed_metadata, make_fgdc_metadata, \
    VWClient, default_vw_client, _get_config, metadata_from_file

import datetime
import json
import pandas as pd
import os
import requests
import time
import unittest
from uuid import uuid4

from difflib import Differ
from requests.exceptions import HTTPError

from nose.tools import raises

# Path hack.
import sys; import os
sys.path.insert(0, os.path.abspath('..'))

from ..watershed import VARNAME_DICT


def show_string_diff(s1, s2):
    """ Writes differences between strings s1 and s2 """
    d = Differ()
    diff = d.compare(s1.splitlines(), s2.splitlines())
    diffList = [el for el in diff
                if el[0] != ' ' and el[0] != '?']

    for l in diffList:

        if l[0] == '+':
            print '+' + bcolors.GREEN + l[1:] + bcolors.ENDC
        elif l[0] == '-':
            print '-' + bcolors.RED + l[1:] + bcolors.ENDC
        else:
            assert False, 'Error, diffList entry must start with + or -'


class bcolors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'

VW_CLIENT = default_vw_client('vwpy/test/test.conf')


class TestJSONMetadata(unittest.TestCase):
    """ Test that individual and sets of JSON metadata are being properly
        generated. """
    def setUp(self):
        """
        initialize the class with some appropriate entry
        metadata from file
        """
        self.config = _get_config('vwpy/test/test.conf')

        self.modelRunUUID = '09079630-5ef8-11e4-9803-0800200c9a66'
        self.parentModelRunUUID = '373ae181-a0b2-4998-ba32-e27da190f6dd'

    def testCorrectMetadatum(self):
        """ Test that a single metadata JSON string is properly built (JSON)"""

        # minimal watershed JSON with geotiff
        generated = make_watershed_metadata(
            'vwpy/test/data/in.0010.I_lw.tif',
            self.config, 'MODELRUNXX**A*', 'MODELRUNXX**A*', 'inputs',
            'Dry Creek', 'Idaho', file_ext='tif', taxonomy='geoimage',
            model_name='isnobal', proc_date='2015-05-08')

        # load expected json metadata file
        expected = \
            open('vwpy/test/data/expected_minimal_tif_watershed.json',
                 'r').read()

        # check equality
        assert generated.strip() == expected.strip(), \
            show_string_diff(generated, expected)

        # minimal watershed JSON with iSNOBAL binary
        generated = make_watershed_metadata(
            'vwpy/test/data/in.0010',
            self.config, 'MODELRUNXX**A*','MODELRUNXX**A*', 'inputs',
            'Dry Creek', 'Idaho', file_ext='bin', model_vars='I_lw,T_a,e_a,u,T_g,S_n',
            model_name='isnobal', proc_date='2015-05-08')

        expected = open('vwpy/test/data/expected_minimal_isno_watershed.json',
                        'r').read()


        # check equality
        assert generated.strip() == expected.strip(), \
            show_string_diff(generated, expected)

        # full watershed JSON with geotiff
        xml = make_fgdc_metadata('vwpy/test/data/in.0010.I_lw.tif',
                                 self.config, 'MODELRUNXX**AA*',
                                 "2010-10-01", "2011-09-31",
                                 proc_date="2015-05-07",
                                 theme_key="watershed", row_count=170,
                                 column_count=124, lat_res=2.5,
                                 lon_res=2.5, map_units='m')

        generated = make_watershed_metadata(
            'vwpy/test/data/in.0010.I_lw.tif',
            self.config, 'MODELRUNXX**A*','MODELRUNXX**A*', 'inputs',
            'Dry Creek', 'Idaho', fgdc_metadata=xml,
            orig_epsg=26911, epsg=4326, model_set_type='tif', model_vars='I_lw',
            model_set_taxonomy='grid', start_datetime='2010-10-01 10:00:00',
            end_datetime='2010-10-01 11:00:00', model_name='isnobal')

        # load expected json metadata file
        expected = open('vwpy/test/data/expected_full_tif_watershed.json',
                        'r').read()

        # check equality
        assert generated.strip() == expected.strip(), \
            show_string_diff(generated, expected)

        # full watershed JSON with iSNOBAL binary
        xml = make_fgdc_metadata('vwpy/test/data/in.0010',
                                 self.config, 'MODELRUNXX**AA*',
                                 "2010-10-01", "2011-09-31",
                                 proc_date="2015-05-07",
                                 theme_key="watershed", row_count=170,
                                 column_count=124, lat_res=2.5,
                                 lon_res=2.5, map_units='m', file_ext='bin')

        generated = make_watershed_metadata(
            'vwpy/test/data/in.0010',
            self.config, 'MODELRUNXX**A*','MODELRUNXX**A*', 'inputs',
            'Dry Creek', 'Idaho', fgdc_metadata=xml,
            start_datetime='2010-01-01 10:00:00', end_datetime='2010-01-01 11:00:00',
            orig_epsg=26911, epsg=4326, model_set_type='binary',
            file_ext='bin', model_vars='I_lw,T_a,e_a,u,T_g,S_n',
            model_name='isnobal')


        expected = open('vwpy/test/data/expected_full_isno_watershed.json',
                        'r').read()

        # check equality
        assert generated.strip() == expected.strip(), \
            show_string_diff(generated, expected)


class TestFGDCMetadata(unittest.TestCase):
    """ Test individual and sets of XML FGDC-standard metadata are being
        properly generated and uploaded to the Virtual Watershed
    """
    def setUp(self):
        """ initialize the class with some appropriate entry
            metadata from file
        """
        self.config = _get_config('vwpy/test/test.conf')

        self.modelRunUUID = '09079630-5ef8-11e4-9803-0800200c9a66'
        self.dataFile = 'vwpy/test/data/in.0000'

    def testCorrectMetadatum(self):
        """ Test that a single metadata JSON string is properly built (FGDC)"""
        cfg = self.config

        generated = make_fgdc_metadata('vwpy/test/data/in.0000',
                                       cfg, 'MODELRUNXX**AA*', "2010-10-01",
                                       "2011-09-31", proc_date="2015-05-07",
                                       file_ext='ipw')

        expected = open('vwpy/test/data/expected_minimal_fgdc.xml',
                        'r').read()

        assert generated.strip() == expected.strip(), \
            show_string_diff(generated, expected)

        generated = \
            make_fgdc_metadata('vwpy/test/data/in.0010.I_lw.tif',
                               cfg, 'MODELRUNXX**AA*',
                               "2010-10-01", "2011-09-31",
                               proc_date="2015-05-07",
                               theme_key="watershed", row_count=170,
                               column_count=124, lat_res=2.5,
                               lon_res=2.5, map_units='m')

        expected = open('vwpy/test/data/expected_full_fgdc.xml',
                        'r').read()

        assert generated.strip() == expected.strip(), \
            show_string_diff(generated, expected)


class TestVWClient(unittest.TestCase):
    """ Test the functionality of the Virtual Watershed client """
    def setUp(self):
        # clean up pre-existing unittest model runs
        modelruns = VW_CLIENT.modelrun_search()
        unittest_uuids = [r['Model Run UUID'] for r in modelruns.records
                          if 'unittest' in r['Model Run Name']]

        for u in unittest_uuids:
            s = VW_CLIENT.delete_modelrun(u)
            print "pre-test cleanup success on %s: %s" % (u, str(s))

        self.config = _get_config('vwpy/test/test.conf')

        self.kwargs = {'keywords': 'Snow,iSNOBAL,wind',
                       'researcher_name': self.config['Researcher']['researcher_name'],
                       'description': 'unittest',
                       'model_run_name': 'unittest' + str(uuid4())}

        self.UUID = VW_CLIENT.initialize_modelrun(**self.kwargs)

        self.parent_uuid = self.UUID

        VW_CLIENT.upload(self.UUID, 'vwpy/test/data/in.0000')

        fgdc_md = make_fgdc_metadata('vwpy/test/data/in.0000',
            self.config, self.UUID, "2010-10-01 00:00:00", "2010-10-01 01:00:00")

        wmd_from_file = metadata_from_file('vwpy/test/data/in.0000',
            self.UUID, self.UUID, 'unittest for download', 'Dry Creek', 'Idaho',
            start_datetime="2010-10-01 00:00:00",
            end_datetime="2010-10-01 01:00:00",
            fgdc_metadata=fgdc_md, model_set_type='grid', file_ext='bin',
            taxonomy='geoimage', model_set_taxonomy='grid',
            model_name='isnobal', epsg=4326, orig_epsg=26911)

        res = VW_CLIENT.insert_metadata(wmd_from_file)

        time.sleep(1)

    def test_initialize_modelrun(self):
        """
        Test that a new model_run_uuid corresponding to new model run is properly initialized
        """
        kwargs = {'keywords': 'Snow,iSNOBAL,wind',
                  'researcher_name': 'Matthew Turner',
                  'description': 'model run db testing',
                  'model_run_name': 'initialize unittest ' + str(uuid4())}

        new_uuid = \
            VW_CLIENT.initialize_modelrun(**kwargs)

        result = VW_CLIENT.dataset_search(model_run_uuid=new_uuid)

        assert result.total == 0, \
            'Result does not exist?? result.total = %d' % result.total

    @raises(HTTPError)
    def test_duplicate_error(self):
        """
        If the user tries to init a new model run with a previously used name, catch HTTPError
        """
        keywords = 'Snow,iSNOBAL,wind'
        description = 'model run db testing'

        model_run_name = 'dup_test ' + str(uuid4())

        uuid = VW_CLIENT.initialize_modelrun(keywords=keywords,
                                             description=description,
                                             model_run_name=model_run_name,
                                             researcher_name=self.config['Researcher']['researcher_name'])

        print "first inserted successfully"

        # TODO get watershed guys to make researcher, model run name be PK
        # at that point, this test will fail, but re-inserting Bill's
        # fake submission will throw

        VW_CLIENT.initialize_modelrun(keywords=keywords,
                                      researcher_name=self.config['Researcher']['researcher_name'],
                                      description=description,
                                      model_run_name=model_run_name)

        VW_CLIENT.delete_modelrun(uuid)

    @raises(HTTPError)
    def test_authFail(self):
        """ Test that failed authorization is correctly caught """
        vw_host = self.config['Connection']['watershed_url']
        VWClient(vw_host, 'fake_user', 'fake_passwd')

    def test_insert(self):
        """ VW Client properly inserts data """
        kwargs = {'keywords': 'Snow,iSNOBAL,wind',
                  'researcher_name': self.config['Researcher']['researcher_name'],
                  'description': 'unittest',
                  'model_run_name': 'unittest' + str(uuid4())}
        UUID = \
            VW_CLIENT.initialize_modelrun(**kwargs)

        VW_CLIENT.upload(UUID, 'vwpy/test/data/in.0000')

        dataFile = 'vwpy/test/data/in.0000'

        fgdcXML = \
            make_fgdc_metadata(dataFile, self.config, UUID,
                               "2010-10-01 00:00:00", "2010-10-01 01:00:00")

        watershedJSON = \
            make_watershed_metadata(dataFile, self.config, UUID,
                UUID, 'inputs', 'Dry Creek', 'Idaho',
                description='Description of the data',
                start_datetime='2010-01-01 10:00:00',
                end_datetime='2010-01-01 11:00:00', orig_epsg=26911, epsg=4326,
                model_set_type='binary', file_ext='bin',
                model_set_taxonomy='grid', taxonomy='geoimage',
                model_vars='I_lw,T_a,e_a,u,T_g,S_n', model_name='isnobal')

        insert_result = VW_CLIENT.insert_metadata(watershedJSON)

        time.sleep(1)

        vwTestUUIDEntries = VW_CLIENT.dataset_search(model_run_uuid=UUID)

        assert vwTestUUIDEntries.records,\
            'No VW Entries corresponding to the test UUID'

    def test_insertFail(self):
        "VW Client passes along correct status code on failed insert"

        response = VW_CLIENT.insert_metadata('{"metadata": {"xml": "mo garbage"}}')

        assert response.status_code == 500

    def test_upload(self):
        """ VW Client properly uploads data """
        # fetch the file from the url we know from the VW file storage pattern
        results = \
            VW_CLIENT.dataset_search(model_run_uuid=self.UUID, limit=1)

        url = results.records[0]['downloads'][0]['bin']

        outfile = "vwpy/test/data/back_in.0000"

        if os.path.isfile(outfile):
            os.remove(outfile)

        VW_CLIENT.download(url, outfile)

        # check that the file now exists in the file system as expected
        assert os.path.isfile(outfile)

        os.remove(outfile)

        # now do the same for netcdf
        nc_file = 'vwpy/test/data/flat_sample.nc'

        VW_CLIENT.upload(self.UUID, nc_file)

        wmd_from_file = metadata_from_file('flat_sample.nc', self.UUID, self.UUID,
            'testing upload/download of netcdf', 'Dry Creek', 'Idaho',
            model_name='isnobal', model_set_type='grid', model_set='inputs',
            model_set_taxonomy='grid', taxonomy='geoimage',
            file_ext='nc', orig_epsg=26911, epsg=4326)

        VW_CLIENT.insert_metadata(wmd_from_file)

        time.sleep(1)

        nc_url = [r['downloads'][0]['nc']
                  for r in VW_CLIENT.dataset_search(model_run_uuid=self.UUID).records
                  if r['name'].split('.')[-1] == 'nc'][0]

        outfile = "vwpy/test/data/back_in.nc"

        if os.path.isfile(outfile):
            os.remove(outfile)

        VW_CLIENT.download(nc_url, outfile)

        # check that the file now exists in the file system as expected
        assert os.path.isfile(outfile)

        os.remove(outfile)

    def test_swift_upload(self):
        """ VW Client properly uploads data using the swift client"""

        # now do the same for netcdf
        nc_file = 'vwpy/test/data/flat_sample_for_swift.nc'

        res = VW_CLIENT.swift_upload(self.UUID, nc_file)

        wmd_from_file = metadata_from_file(nc_file, self.UUID, self.UUID,
            'testing upload/download of netcdf', 'Dry Creek', 'Idaho',
            model_name='isnobal', model_set_type='grid', model_set='inputs',
            model_set_taxonomy='grid', taxonomy='geoimage',
            file_ext='nc', orig_epsg=26911, epsg=4326)

        VW_CLIENT.insert_metadata(wmd_from_file)

        time.sleep(1)

        nc_url = [r['downloads'][0]['nc']
                  for r in VW_CLIENT.dataset_search(model_run_uuid=self.UUID).records
                  if r['name'].split('.')[-1] == 'nc'][0]

        outfile = "vwpy/test/data/back_in.nc"

        if os.path.isfile(outfile):
            os.remove(outfile)

        VW_CLIENT.download(nc_url, outfile)

        # check that the file now exists in the file system as expected
        assert os.path.isfile(outfile)

        os.remove(outfile)

    def test_download(self):
        """
        VW Client properly downloads data
        """
        result = \
            VW_CLIENT.dataset_search(model_run_uuid=self.UUID, limit=1)

        r0 = result.records[0]
        url = r0['downloads'][0]['bin']

        outfile = "vwpy/test/data/test_dl.file"

        if os.path.isfile(outfile):
            os.remove(outfile)

        VW_CLIENT.download(url, outfile)

        assert os.path.isfile(outfile)

        os.remove(outfile)

    @raises(AssertionError)
    def test_downloadFail(self):
        """ VW Client throws error on failed download """
        url = "http://httpbin.org/status/404"

        VW_CLIENT.download(url, "this won't ever exist")

    def test_watershed_connection(self):
        """
        Test watershed functions operating on an IPW instance or as a static method
        """
        # load expected json metadata file
        expected = open('vwpy/test/data/expected_ipw_metadata.json',
                        'r').read()

        description = 'Testing metadata!'

        # TODO this gets tests passing; standardize uuids in setUp on nxt rfctr
        parent_uuid = '373ae181-a0b2-4998-ba32-e27da190f6dd'
        uuid = '09079630-5ef8-11e4-9803-0800200c9a66'

        generated = metadata_from_file('vwpy/test/data/in.0000',
                                       parent_uuid,
                                       uuid,
                                       description, 'Dry Creek', 'Idaho',
                                       model_name='isnobal',
                                       file_ext='bin',
                                       config_file='vwpy/test/test.conf',
                                       proc_date='2015-07-14')

        # check equality
        assert generated
        assert expected
        assert generated.strip() == expected.strip(), show_string_diff(generated, expected)

    def test_metadata_from_file(self):
        """
        Test that metadata is properly generated a .tif file
        """
        # some values we're using for testing
        parent_uuid = '373ae181-a0b2-4998-ba32-e27da190f6dd'
        uuid = '09079630-5ef8-11e4-9803-0800200c9a66'
        # .tif
        generated = metadata_from_file(
            os.path.dirname(__file__) + '/data/in.0008.I_lw.tif',
            parent_uuid, uuid, 'Testing metadata!', 'Dry Creek', 'Idaho',
            config_file='vwpy/test/test.conf', model_vars='I_lw',
            proc_date="2015-05-12")

        expected = open('vwpy/test/data/expected_tif.json', 'r').read()

        assert generated.strip() == expected.strip(), \
            show_string_diff(generated, expected)

        # now assume we have resampled to 3-day intervals
        dt = pd.Timedelta('3 days')

        generated = metadata_from_file(
            os.path.dirname(__file__) + '/data/in.0008.I_lw.tif',
            parent_uuid, uuid, 'Testing metadata!', 'Dry Creek', 'Idaho',
            config_file='vwpy/test/test.conf', dt=dt,
            model_vars='melt', proc_date="2015-05-12")

        expected = open('vwpy/test/data/expected_tif_nonhourdt.json',
                        'r').read()

        assert generated.strip() == expected.strip(), \
            show_string_diff(generated, expected)

    def tearDown(self):
        # clean up pre-existing unittest model runs
        modelruns = VW_CLIENT.modelrun_search()
        unittest_uuids = [r['Model Run UUID'] for r in modelruns.records
                          if 'unittest' in r['Model Run Name']]

        for u in unittest_uuids:
            s = VW_CLIENT.delete_modelrun(u)
            print "post-test cleanup success on %s: %s" % (u, str(s))

        dup_test_uuids = [r['Model Run UUID'] for r in modelruns.records
                          if 'dup_test' in r['Model Run Name']]

        for u in dup_test_uuids:
            s = VW_CLIENT.delete_modelrun(u)
            print "post-test cleanup success on %s: %s" % (u, str(s))


def _gen_kw_args():
    return {'keywords': 'Snow,iSNOBAL,wind',
            'description': 'unittest',
            'model_run_name': 'unittest' + str(uuid4())}
