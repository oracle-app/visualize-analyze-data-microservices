import unittest
from app import app
class TestApi(unittest.TestCase): 
    def setUp(self): 
        self.client = app.test_client()
        self.client.testing = True

    def testNoFileReturns400(self): 
        res = self.client.post("/analyzeData")
        self.assertEqual(res.status_code, 400)

    def testWrongFiletypeReturns415(self):
        data = {"file": (open("tests/dummy.txt", "rb"), "dummy.txt")}
        response = self.client.post("/analyzeData", data=data, content_type="multipart/form-data")
        self.assertEqual(response.status_code, 415)

    def testValidCsvReturns200_01(self):
        data = {"file": (open("tests/tested.csv", "rb"), "tested.csv")}
        response = self.client.post("/analyzeData", data=data, content_type="multipart/form-data")
        self.assertEqual(response.status_code, 200)

    def testResponseContainsCharts01(self):
        data = {"file": (open("tests/tested.csv", "rb"), "tested.csv")}
        response = self.client.post("/analyzeData", data=data, content_type="multipart/form-data")
        json_data = response.get_json()
        self.assertIn("Charts", json_data)
        #5 Charts
        self.assertEqual(len(json_data["Charts"]), 5)

    def testValidCsvReturns200_02(self):
        data = {"file": (open("tests/animation_movies_enriched_1878_2029.csv", "rb"), "tested.csv")}
        response = self.client.post("/analyzeData", data=data, content_type="multipart/form-data")
        self.assertEqual(response.status_code, 200)

    def testResponseContainsCharts02(self):
        data = {"file": (open("tests/animation_movies_enriched_1878_2029.csv", "rb"), "tested.csv")}
        response = self.client.post("/analyzeData", data=data, content_type="multipart/form-data")
        json_data = response.get_json()
        self.assertIn("Charts", json_data)
        #5 Charts
        self.assertEqual(len(json_data["Charts"]), 5)
        
    def testValidCsvReturns200_03(self):
        data = {"file": (open("tests/dataset_2191_sleep.csv", "rb"), "tested.csv")}
        response = self.client.post("/analyzeData", data=data, content_type="multipart/form-data")
        self.assertEqual(response.status_code, 200)

    def testResponseContainsCharts03(self):
        data = {"file": (open("tests/dataset_2191_sleep.csv", "rb"), "tested.csv")}
        response = self.client.post("/analyzeData", data=data, content_type="multipart/form-data")
        json_data = response.get_json()
        self.assertIn("Charts", json_data)
        #5 Charts
        self.assertEqual(len(json_data["Charts"]), 5)

    def testValidCsvReturns_200_04(self):
        data = {"file": (open("tests/listings.csv", "rb"), "tested.csv")}
        response = self.client.post("/analyzeData", data=data, content_type="multipart/form-data")
        self.assertEqual(response.status_code, 200)

    def testResponseContainsCharts04(self):
        data = {"file": (open("tests/listings.csv", "rb"), "tested.csv")}
        response = self.client.post("/analyzeData", data=data, content_type="multipart/form-data")
        json_data = response.get_json()
        self.assertIn("Charts", json_data)
        #5 Charts
        self.assertEqual(len(json_data["Charts"]), 5)

    def testValidCsvReturns_200_05(self):
        data = {"file": (open("tests/past_rates.csv", "rb"), "tested.csv")}
        response = self.client.post("/analyzeData", data=data, content_type="multipart/form-data")
        self.assertEqual(response.status_code, 200)

    def testResponseContainsCharts_05(self):
        data = {"file": (open("tests/past_rates.csv", "rb"), "tested.csv")}
        response = self.client.post("/analyzeData", data=data, content_type="multipart/form-data")
        json_data = response.get_json()
        self.assertIn("Charts", json_data)
        #5 Charts
        self.assertEqual(len(json_data["Charts"]), 5)

    def testValidCsvReturns_200_06(self):
        data = {"file": (open("tests/Smartphone_Usage_And_Addiction_Analysis_7500_Rows (1).csv", "rb"), "tested.csv")}
        response = self.client.post("/analyzeData", data=data, content_type="multipart/form-data")
        self.assertEqual(response.status_code, 200)

    def testResponseContainsCharts06(self):
        data = {"file": (open("tests/Smartphone_Usage_And_Addiction_Analysis_7500_Rows (1).csv", "rb"), "tested.csv")}
        response = self.client.post("/analyzeData", data=data, content_type="multipart/form-data")
        json_data = response.get_json()
        self.assertIn("Charts", json_data)
        #5 Charts
        self.assertEqual(len(json_data["Charts"]), 5)

    def testValidCsvReturns200_07(self):
        data = {"file": (open("tests/Teen_Mental_Health_Dataset.csv", "rb"), "tested.csv")}
        response = self.client.post("/analyzeData", data=data, content_type="multipart/form-data")
        self.assertEqual(response.status_code, 200)

    def testResponseContainsCharts07(self):
        data = {"file": (open("tests/Teen_Mental_Health_Dataset.csv", "rb"), "tested.csv")}
        response = self.client.post("/analyzeData", data=data, content_type="multipart/form-data")
        json_data = response.get_json()
        self.assertIn("Charts", json_data)
        #5 Charts
        self.assertEqual(len(json_data["Charts"]), 5)


if __name__ == "__main__":
    unittest.main()   
