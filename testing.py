import unittest
import pandas as pd
import numpy as np
import json
import io
import sys
sys.path.insert(0, '.')

from app import app, jsonSanitizer
from queryData import dataQuerienator3000
from prepareData import corrMatrixFilter

# ──────────────────────────────────────────────
# Shared fixtures
# ──────────────────────────────────────────────

def buildTitanicDf():
    """Controlled Titanic-like dataframe with known values for deterministic assertions."""
    np.random.seed(42)
    n = 891
    pclass  = np.random.choice([1,2,3], n, p=[0.24, 0.21, 0.55])
    survived = np.where(pclass==1, np.random.choice([0,1], n, p=[0.37,0.63]),
               np.where(pclass==2, np.random.choice([0,1], n, p=[0.53,0.47]),
                                   np.random.choice([0,1], n, p=[0.76,0.24])))
    sex      = np.random.choice(['male','female'], n, p=[0.65,0.35])
    age      = np.clip(np.random.normal(29.7, 14.5, n), 0.42, 80)
    sibsp    = np.random.choice([0,1,2,3,4,5,8], n, p=[0.682,0.230,0.050,0.020,0.010,0.005,0.003])
    parch    = np.random.choice([0,1,2,3,4,5,6], n, p=[0.760,0.130,0.090,0.010,0.006,0.003,0.001])
    fare     = np.clip(np.where(pclass==1, np.random.exponential(84, n),
               np.where(pclass==2, np.random.exponential(20, n),
                                   np.random.exponential(13, n))), 0, 512)
    embarked = np.random.choice(['S','C','Q'], n, p=[0.72,0.19,0.09])
    return pd.DataFrame({
        'PassengerId': np.arange(1, n+1),
        'Survived':    survived,
        'Pclass':      pclass,
        'Sex':         sex,
        'Age':         age,
        'SibSp':       sibsp,
        'Parch':       parch,
        'Fare':        fare,
        'Embarked':    embarked
    })

DF = buildTitanicDf()

# Pre-computed expected values (ground truth from groundTruth.ipynb)
EXPECTED_VB_FIELD1  = [1, 2, 3]
EXPECTED_VB_FIELD2  = [0.4672897196261682, 0.3225806451612903, 0.3302752293577982]
EXPECTED_PIE_FIELD1 = [1, 2, 3]
EXPECTED_PIE_FIELD2 = [10087.9918, 2064.7957, 2703.7500999999997]
EXPECTED_TILE_VALUE = 35.627188489208635
EXPECTED_SCATTER_ROWS = 891
EXPECTED_STACKED_FIELD1 = [1, 2, 3]
EXPECTED_STACKED_SERIES_KEYS = ['0', '1']


# ──────────────────────────────────────────────
# 1. Endpoint integration tests
# ──────────────────────────────────────────────

class TestEndpoint(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True

    def testNoFileReturns400(self):
        res = self.client.post('/analyzeData')
        self.assertEqual(res.status_code, 400)

    def testWrongFiletypeReturns415(self):
        data = {'file': (open('tests/dummy.txt', 'rb'), 'dummy.txt')}
        res = self.client.post('/analyzeData', data=data, content_type='multipart/form-data')
        self.assertEqual(res.status_code, 415)

    def testValidCsvReturns200_01(self):
        data = {'file': (open('tests/tested.csv', 'rb'), 'tested.csv')}
        res = self.client.post('/analyzeData', data=data, content_type='multipart/form-data')
        self.assertEqual(res.status_code, 200)

    def testResponseHasChartsKey01(self):
        data = {'file': (open('tests/tested.csv', 'rb'), 'tested.csv')}
        res = self.client.post('/analyzeData', data=data, content_type='multipart/form-data')
        self.assertIn('Charts', res.get_json())

    def testResponseChartCountRange01(self):
        """Model returned at least 1 and at most 5 charts — pipeline did not crash."""
        data = {'file': (open('tests/tested.csv', 'rb'), 'tested.csv')}
        res = self.client.post('/analyzeData', data=data, content_type='multipart/form-data')
        count = len(res.get_json()['Charts'])
        self.assertGreaterEqual(count, 1)
        self.assertLessEqual(count, 5)

    def testResponseChartCountExact01(self):
        """Model followed instructions and returned exactly 5 charts."""
        data = {'file': (open('tests/tested.csv', 'rb'), 'tested.csv')}
        res = self.client.post('/analyzeData', data=data, content_type='multipart/form-data')
        self.assertEqual(len(res.get_json()['Charts']), 5)

    def testEachChartHasRequiredKeys01(self):
        data = {'file': (open('tests/tested.csv', 'rb'), 'tested.csv')}
        res = self.client.post('/analyzeData', data=data, content_type='multipart/form-data')
        for chart in res.get_json()['Charts']:
            self.assertIn('chartName', chart)
            self.assertIn('chartType', chart)
            self.assertIn('data', chart)

    def testEachChartDataHasLists01(self):
        data = {'file': (open('tests/tested.csv', 'rb'), 'tested.csv')}
        res = self.client.post('/analyzeData', data=data, content_type='multipart/form-data')
        for chart in res.get_json()['Charts']:
            if 'error' not in chart:
                self.assertIsInstance(chart['data'], dict)

    # Repeat for other datasets
    def testValidCsvReturns200_02(self):
        data = {'file': (open('tests/animation_movies_enriched_1878_2029.csv', 'rb'), 'file.csv')}
        res = self.client.post('/analyzeData', data=data, content_type='multipart/form-data')
        self.assertEqual(res.status_code, 200)

    def testResponseChartCountRange02(self):
        data = {'file': (open('tests/animation_movies_enriched_1878_2029.csv', 'rb'), 'file.csv')}
        res = self.client.post('/analyzeData', data=data, content_type='multipart/form-data')
        count = len(res.get_json()['Charts'])
        self.assertGreaterEqual(count, 1)
        self.assertLessEqual(count, 5)

    def testResponseChartCountExact02(self):
        data = {'file': (open('tests/animation_movies_enriched_1878_2029.csv', 'rb'), 'file.csv')}
        res = self.client.post('/analyzeData', data=data, content_type='multipart/form-data')
        self.assertEqual(len(res.get_json()['Charts']), 5)

    def testValidCsvReturns200_03(self):
        data = {'file': (open('tests/dataset_2191_sleep.csv', 'rb'), 'file.csv')}
        res = self.client.post('/analyzeData', data=data, content_type='multipart/form-data')
        self.assertEqual(res.status_code, 200)

    def testResponseChartCountRange03(self):
        data = {'file': (open('tests/dataset_2191_sleep.csv', 'rb'), 'file.csv')}
        res = self.client.post('/analyzeData', data=data, content_type='multipart/form-data')
        count = len(res.get_json()['Charts'])
        self.assertGreaterEqual(count, 1)
        self.assertLessEqual(count, 5)

    def testResponseChartCountExact03(self):
        data = {'file': (open('tests/dataset_2191_sleep.csv', 'rb'), 'file.csv')}
        res = self.client.post('/analyzeData', data=data, content_type='multipart/form-data')
        self.assertEqual(len(res.get_json()['Charts']), 5)

    def testValidCsvReturns200_04(self):
        data = {'file': (open('tests/listings.csv', 'rb'), 'file.csv')}
        res = self.client.post('/analyzeData', data=data, content_type='multipart/form-data')
        self.assertEqual(res.status_code, 200)

    def testResponseChartCountRange04(self):
        data = {'file': (open('tests/listings.csv', 'rb'), 'file.csv')}
        res = self.client.post('/analyzeData', data=data, content_type='multipart/form-data')
        count = len(res.get_json()['Charts'])
        self.assertGreaterEqual(count, 1)
        self.assertLessEqual(count, 5)

    def testResponseChartCountExact04(self):
        data = {'file': (open('tests/listings.csv', 'rb'), 'file.csv')}
        res = self.client.post('/analyzeData', data=data, content_type='multipart/form-data')
        self.assertEqual(len(res.get_json()['Charts']), 5)

    def testValidCsvReturns200_05(self):
        data = {'file': (open('tests/past_rates.csv', 'rb'), 'file.csv')}
        res = self.client.post('/analyzeData', data=data, content_type='multipart/form-data')
        self.assertEqual(res.status_code, 200)

    def testResponseChartCountRange05(self):
        data = {'file': (open('tests/past_rates.csv', 'rb'), 'file.csv')}
        res = self.client.post('/analyzeData', data=data, content_type='multipart/form-data')
        count = len(res.get_json()['Charts'])
        self.assertGreaterEqual(count, 1)
        self.assertLessEqual(count, 5)

    def testResponseChartCountExact05(self):
        data = {'file': (open('tests/past_rates.csv', 'rb'), 'file.csv')}
        res = self.client.post('/analyzeData', data=data, content_type='multipart/form-data')
        self.assertEqual(len(res.get_json()['Charts']), 5)

    def testValidCsvReturns200_06(self):
        data = {'file': (open('tests/Smartphone_Usage_And_Addiction_Analysis_7500_Rows (1).csv', 'rb'), 'file.csv')}
        res = self.client.post('/analyzeData', data=data, content_type='multipart/form-data')
        self.assertEqual(res.status_code, 200)

    def testResponseChartCountRange06(self):
        data = {'file': (open('tests/Smartphone_Usage_And_Addiction_Analysis_7500_Rows (1).csv', 'rb'), 'file.csv')}
        res = self.client.post('/analyzeData', data=data, content_type='multipart/form-data')
        count = len(res.get_json()['Charts'])
        self.assertGreaterEqual(count, 1)
        self.assertLessEqual(count, 5)

    def testResponseChartCountExact06(self):
        data = {'file': (open('tests/Smartphone_Usage_And_Addiction_Analysis_7500_Rows (1).csv', 'rb'), 'file.csv')}
        res = self.client.post('/analyzeData', data=data, content_type='multipart/form-data')
        self.assertEqual(len(res.get_json()['Charts']), 5)

    def testValidCsvReturns200_07(self):
        data = {'file': (open('tests/Teen_Mental_Health_Dataset.csv', 'rb'), 'file.csv')}
        res = self.client.post('/analyzeData', data=data, content_type='multipart/form-data')
        self.assertEqual(res.status_code, 200)

    def testResponseChartCountRange07(self):
        data = {'file': (open('tests/Teen_Mental_Health_Dataset.csv', 'rb'), 'file.csv')}
        res = self.client.post('/analyzeData', data=data, content_type='multipart/form-data')
        count = len(res.get_json()['Charts'])
        self.assertGreaterEqual(count, 1)
        self.assertLessEqual(count, 5)

    def testResponseChartCountExact07(self):
        data = {'file': (open('tests/Teen_Mental_Health_Dataset.csv', 'rb'), 'file.csv')}
        res = self.client.post('/analyzeData', data=data, content_type='multipart/form-data')
        self.assertEqual(len(res.get_json()['Charts']), 5)


# ──────────────────────────────────────────────
# 2. jsonSanitizer unit tests
# ──────────────────────────────────────────────

class TestJsonSanitizer(unittest.TestCase):

    def _baseChart(self, chartType='Vertical Bar Chart', metricsFilter=None):
        return json.dumps({'Charts': [{'chartName': 'Test', 'chartType': chartType,
                'metrics': {'field1': 'Pclass', 'field2': 'Survived'},
                'metricsFilter': metricsFilter or {'Survived': 'Avg'}}]})

    def testCleanJsonParsesCorrectly(self):
        result = jsonSanitizer(self._baseChart())
        self.assertIn('Charts', result)
        self.assertEqual(len(result['Charts']), 1)

    def testMarkdownFencesAreStripped(self):
        fenced = f'```json\n{self._baseChart()}\n```'
        result = jsonSanitizer(fenced)
        self.assertIn('Charts', result)

    def testMissingCommaIsRepaired(self):
        broken = '```json\n{"Charts": [{"chartName": "Test", "chartType": "Scatter"\n"metrics": {"field1": "Fare", "field2": "Survived"}, "metricsFilter": {}}]}\n```'
        result = jsonSanitizer(broken)
        self.assertIn('Charts', result)

    def testInvalidChartTypeDefaultsToVerticalBar(self):
        result = jsonSanitizer(self._baseChart(chartType='Magic Chart'))
        self.assertEqual(result['Charts'][0]['chartType'], 'Vertical Bar Chart')

    def testValidChartTypesArePreserved(self):
        validTypes = ['Tile', 'Vertical Bar Chart', 'Horizontal Bar Chart',
                      'Stacked Bar Chart', 'Line', 'Pie', 'Donut', 'Scatter', 'Area']
        for chartType in validTypes:
            result = jsonSanitizer(self._baseChart(chartType=chartType))
            self.assertEqual(result['Charts'][0]['chartType'], chartType)

    def testInvalidFilterDefaultsToAvg(self):
        result = jsonSanitizer(self._baseChart(metricsFilter={'Survived': 'Mean'}))
        self.assertEqual(result['Charts'][0]['metricsFilter']['Survived'], 'Avg')

    def testValidFiltersArePreserved(self):
        for f in ['Max', 'Min', 'Avg', 'Sum']:
            result = jsonSanitizer(self._baseChart(metricsFilter={'Survived': f}))
            self.assertEqual(result['Charts'][0]['metricsFilter']['Survived'], f)

    def testNullMetricsFilterDoesNotCrash(self):
        result = jsonSanitizer(self._baseChart(metricsFilter=None))
        self.assertIn('Charts', result)

    def testExplicitNullMetricsFilterDoesNotCrash(self):
        raw = '{"Charts": [{"chartName": "Test", "chartType": "Vertical Bar Chart", "metrics": {"field1": "Pclass", "field2": "Survived"}, "metricsFilter": null}]}'
        result = jsonSanitizer(raw)
        self.assertIn('Charts', result)

    def testEmptyChartsArrayReturnsEmptyList(self):
        result = jsonSanitizer('{"Charts": []}')
        self.assertEqual(result['Charts'], [])

    def testMultipleChartsAllSanitized(self):
        raw = json.dumps({'Charts': [
            {'chartName': 'A', 'chartType': 'Bad Type', 'metrics': {'field1': 'Pclass', 'field2': 'Survived'}, 'metricsFilter': {'Survived': 'Mean'}},
            {'chartName': 'B', 'chartType': 'Pie',      'metrics': {'field1': 'Pclass', 'field2': 'Fare'},     'metricsFilter': {'Fare': 'Index'}},
        ]})
        result = jsonSanitizer(raw)
        self.assertEqual(result['Charts'][0]['chartType'], 'Vertical Bar Chart')
        self.assertEqual(result['Charts'][0]['metricsFilter']['Survived'], 'Avg')
        self.assertEqual(result['Charts'][1]['chartType'], 'Pie')
        self.assertEqual(result['Charts'][1]['metricsFilter']['Fare'], 'Avg')


# ──────────────────────────────────────────────
# 3. dataQuerienator3000 unit tests
# ──────────────────────────────────────────────

class TestDataQuerienator3000(unittest.TestCase):

    def _chart(self, chartType, field1='Pclass', field2='Survived', field3=None, metricsFilter=None):
        metrics = {'field1': field1, 'field2': field2}
        if field3:
            metrics['field3'] = field3
        return {
            'chartName': 'Test Chart',
            'chartType': chartType,
            'metrics': metrics,
            'metricsFilter': metricsFilter or {field2: 'Avg'}
        }

    # --- Structure and values: Vertical Bar ---
    def testVerticalBarReturnsCorrectKeys(self):
        res = dataQuerienator3000(self._chart('Vertical Bar Chart'), DF)
        self.assertIn('chartName', res)
        self.assertIn('chartType', res)
        self.assertIn('data', res)
        self.assertIn('field1', res['data'])
        self.assertIn('field2', res['data'])

    def testVerticalBarField1IsList(self):
        res = dataQuerienator3000(self._chart('Vertical Bar Chart'), DF)
        self.assertIsInstance(res['data']['field1'], list)

    def testVerticalBarField2IsList(self):
        res = dataQuerienator3000(self._chart('Vertical Bar Chart'), DF)
        self.assertIsInstance(res['data']['field2'], list)

    def testVerticalBarField1Values(self):
        res = dataQuerienator3000(self._chart('Vertical Bar Chart'), DF)
        self.assertEqual(res['data']['field1'], EXPECTED_VB_FIELD1)

    def testVerticalBarField2Values(self):
        res = dataQuerienator3000(self._chart('Vertical Bar Chart'), DF)
        for actual, expected in zip(res['data']['field2'], EXPECTED_VB_FIELD2):
            self.assertAlmostEqual(actual, expected, places=5)

    def testVerticalBarLengthsMatch(self):
        res = dataQuerienator3000(self._chart('Vertical Bar Chart'), DF)
        self.assertEqual(len(res['data']['field1']), len(res['data']['field2']))

    # --- Horizontal Bar (same logic as vertical) ---
    def testHorizontalBarReturnsCorrectStructure(self):
        res = dataQuerienator3000(self._chart('Horizontal Bar Chart'), DF)
        self.assertIn('field1', res['data'])
        self.assertIn('field2', res['data'])

    def testHorizontalBarField1Values(self):
        res = dataQuerienator3000(self._chart('Horizontal Bar Chart'), DF)
        self.assertEqual(res['data']['field1'], EXPECTED_VB_FIELD1)

    # --- Scatter ---
    def testScatterReturnsCorrectKeys(self):
        res = dataQuerienator3000(self._chart('Scatter', field1='Fare', field2='Survived', metricsFilter={}), DF)
        self.assertIn('field1', res['data'])
        self.assertIn('field2', res['data'])

    def testScatterRowCount(self):
        res = dataQuerienator3000(self._chart('Scatter', field1='Fare', field2='Survived', metricsFilter={}), DF)
        self.assertEqual(len(res['data']['field1']), EXPECTED_SCATTER_ROWS)

    def testScatterField1IsListOfFloats(self):
        res = dataQuerienator3000(self._chart('Scatter', field1='Fare', field2='Survived', metricsFilter={}), DF)
        self.assertTrue(all(isinstance(x, float) for x in res['data']['field1']))

    def testScatterLengthsMatch(self):
        res = dataQuerienator3000(self._chart('Scatter', field1='Fare', field2='Survived', metricsFilter={}), DF)
        self.assertEqual(len(res['data']['field1']), len(res['data']['field2']))

    # --- Line ---
    def testLineReturnsCorrectStructure(self):
        res = dataQuerienator3000(self._chart('Line', field1='Fare', field2='Survived', metricsFilter={}), DF)
        self.assertIn('field1', res['data'])
        self.assertIn('field2', res['data'])

    # --- Pie ---
    def testPieReturnsCorrectKeys(self):
        res = dataQuerienator3000(self._chart('Pie', field1='Pclass', field2='Fare', metricsFilter={'Fare': 'Sum'}), DF)
        self.assertIn('field1', res['data'])
        self.assertIn('field2', res['data'])

    def testPieField1Values(self):
        res = dataQuerienator3000(self._chart('Pie', field1='Pclass', field2='Fare', metricsFilter={'Fare': 'Sum'}), DF)
        self.assertEqual(res['data']['field1'], EXPECTED_PIE_FIELD1)

    def testPieField2Values(self):
        res = dataQuerienator3000(self._chart('Pie', field1='Pclass', field2='Fare', metricsFilter={'Fare': 'Sum'}), DF)
        for actual, expected in zip(res['data']['field2'], EXPECTED_PIE_FIELD2):
            self.assertAlmostEqual(actual, expected, places=2)

    # --- Donut (same as Pie) ---
    def testDonutReturnsCorrectStructure(self):
        res = dataQuerienator3000(self._chart('Donut', field1='Pclass', field2='Fare', metricsFilter={'Fare': 'Sum'}), DF)
        self.assertIn('field1', res['data'])
        self.assertIn('field2', res['data'])

    # --- Tile ---
    def testTileReturnsValueKey(self):
        res = dataQuerienator3000(self._chart('Tile', field1='Pclass', field2='Fare', metricsFilter={'Fare': 'Avg'}), DF)
        self.assertIn('value', res['data'])

    def testTileValueIsFloat(self):
        res = dataQuerienator3000(self._chart('Tile', field1='Pclass', field2='Fare', metricsFilter={'Fare': 'Avg'}), DF)
        self.assertIsInstance(res['data']['value'], float)

    def testTileValueCorrect(self):
        res = dataQuerienator3000(self._chart('Tile', field1='Pclass', field2='Fare', metricsFilter={'Fare': 'Avg'}), DF)
        self.assertAlmostEqual(res['data']['value'], EXPECTED_TILE_VALUE, places=2)

    # --- Stacked Bar ---
    def testStackedBarReturnsCorrectStructure(self):
        res = dataQuerienator3000(self._chart('Stacked Bar Chart', field1='Pclass', field2='Survived', field3='Fare', metricsFilter={'Fare': 'Avg'}), DF)
        self.assertIn('field1', res['data'])
        self.assertIn('field2', res['data'])

    def testStackedBarField1Values(self):
        res = dataQuerienator3000(self._chart('Stacked Bar Chart', field1='Pclass', field2='Survived', field3='Fare', metricsFilter={'Fare': 'Avg'}), DF)
        self.assertEqual(res['data']['field1'], EXPECTED_STACKED_FIELD1)

    def testStackedBarField2IsDict(self):
        res = dataQuerienator3000(self._chart('Stacked Bar Chart', field1='Pclass', field2='Survived', field3='Fare', metricsFilter={'Fare': 'Avg'}), DF)
        self.assertIsInstance(res['data']['field2'], dict)

    def testStackedBarField2SeriesKeys(self):
        res = dataQuerienator3000(self._chart('Stacked Bar Chart', field1='Pclass', field2='Survived', field3='Fare', metricsFilter={'Fare': 'Avg'}), DF)
        self.assertEqual(sorted(res['data']['field2'].keys()), sorted(EXPECTED_STACKED_SERIES_KEYS))

    def testStackedBarEachSeriesIsListOfCorrectLength(self):
        res = dataQuerienator3000(self._chart('Stacked Bar Chart', field1='Pclass', field2='Survived', field3='Fare', metricsFilter={'Fare': 'Avg'}), DF)
        for key, series in res['data']['field2'].items():
            self.assertIsInstance(series, list)
            self.assertEqual(len(series), len(EXPECTED_STACKED_FIELD1))

    # --- Error cases ---
    def testMissingField1ReturnsErrorDict(self):
        chart = {'chartName': 'Test', 'chartType': 'Vertical Bar Chart',
                 'metrics': {'field2': 'Survived'}, 'metricsFilter': {}}
        res = dataQuerienator3000(chart, DF)
        self.assertIn('error', res)
        self.assertEqual(res['data'], {})

    def testMissingField2ReturnsErrorDict(self):
        chart = {'chartName': 'Test', 'chartType': 'Vertical Bar Chart',
                 'metrics': {'field1': 'Pclass'}, 'metricsFilter': {}}
        res = dataQuerienator3000(chart, DF)
        self.assertIn('error', res)

    def testNonexistentColumnReturnsErrorDict(self):
        res = dataQuerienator3000(self._chart('Vertical Bar Chart', field1='GhostColumn', field2='Survived'), DF)
        self.assertIn('error', res)
        self.assertEqual(res['data'], {})

    def testBothFieldsNonexistentReturnsErrorDict(self):
        res = dataQuerienator3000(self._chart('Vertical Bar Chart', field1='Ghost1', field2='Ghost2'), DF)
        self.assertIn('error', res)

    def testErrorDictContainsChartName(self):
        res = dataQuerienator3000(self._chart('Vertical Bar Chart', field1='Ghost', field2='Survived'), DF)
        self.assertIn('chartName', res)

    def testErrorDictContainsChartType(self):
        res = dataQuerienator3000(self._chart('Vertical Bar Chart', field1='Ghost', field2='Survived'), DF)
        self.assertIn('chartType', res)


# ──────────────────────────────────────────────
# 4. corrMatrixFilter unit tests
# ──────────────────────────────────────────────

class TestCorrMatrixFilter(unittest.TestCase):

    def testValidNumericColumnReturnsTrue(self):
        self.assertTrue(corrMatrixFilter(DF['Fare'], DF))

    def testAnotherValidNumericColumnReturnsTrue(self):
        self.assertTrue(corrMatrixFilter(DF['Survived'], DF))

    def testAllUniqueColumnReturnsFalse(self):
        self.assertFalse(corrMatrixFilter(DF['PassengerId'], DF))

    def testStringColumnReturnsFalse(self):
        self.assertFalse(corrMatrixFilter(DF['Sex'], DF))

    def testBoolColumnReturnsFalse(self):
        boolSeries = pd.Series([True, False, True, False, True], name='flag')
        self.assertFalse(corrMatrixFilter(boolSeries, DF))

    def testColumnNamedIdReturnsFalse(self):
        s = pd.Series([1,2,3,4,5], name='passenger_id')
        self.assertFalse(corrMatrixFilter(s, DF))

    def testColumnNamedCodeReturnsFalse(self):
        s = pd.Series([1,2,3,4,5], name='booking_code')
        self.assertFalse(corrMatrixFilter(s, DF))

    def testColumnNamedKeyReturnsFalse(self):
        s = pd.Series([1,2,3,4,5], name='primary_key')
        self.assertFalse(corrMatrixFilter(s, DF))

    def testColumnNamedIndexReturnsFalse(self):
        s = pd.Series([1,2,3,4,5], name='row_index')
        self.assertFalse(corrMatrixFilter(s, DF))

    def testColumnNamedNumReturnsFalse(self):
        s = pd.Series([1,2,3,4,5], name='record_num')
        self.assertFalse(corrMatrixFilter(s, DF))

    def testAgeColumnReturnsTrue(self):
        self.assertTrue(corrMatrixFilter(DF['Age'], DF))

    def testPclassColumnReturnsTrue(self):
        self.assertTrue(corrMatrixFilter(DF['Pclass'], DF))


# ──────────────────────────────────────────────
# 5. parse_file unit tests
# ──────────────────────────────────────────────

class TestParseFile(unittest.TestCase):

    class FakeFile:
        def __init__(self, content, filename):
            self._content = content
            self.filename = filename
        def read(self):
            return self._content

    def testValidCsvReturnsDataframe(self):
        with open('tests/tested.csv', 'rb') as f:
            content = f.read()
        from app import parse_file
        df = parse_file(self.FakeFile(content, 'tested.csv'))
        self.assertIsInstance(df, pd.DataFrame)

    def testValidCsvHasExpectedColumns(self):
        with open('tests/tested.csv', 'rb') as f:
            content = f.read()
        from app import parse_file
        df = parse_file(self.FakeFile(content, 'tested.csv'))
        self.assertGreater(len(df.columns), 0)

    def testValidCsvHasRows(self):
        with open('tests/tested.csv', 'rb') as f:
            content = f.read()
        from app import parse_file
        df = parse_file(self.FakeFile(content, 'tested.csv'))
        self.assertGreater(len(df), 0)

    def testMalformedCsvSkipsBadLines(self):
        malformed = b'col1,col2\n1,2\n3,4,5,EXTRA\n6,7\n'
        from app import parse_file
        df = parse_file(self.FakeFile(malformed, 'malformed.csv'))
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 2)  # only valid rows

    def testUnsupportedExtensionRaisesValueError(self):
        from app import parse_file
        with self.assertRaises(ValueError):
            parse_file(self.FakeFile(b'data', 'file.json'))

    def testTxtExtensionRaisesValueError(self):
        from app import parse_file
        with self.assertRaises(ValueError):
            parse_file(self.FakeFile(b'data', 'dummy.txt'))


if __name__ == '__main__':
    unittest.main()