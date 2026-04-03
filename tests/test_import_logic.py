import unittest
from scripts.importar_taco import transform_food_data

class TestImportLogic(unittest.TestCase):
    
    def test_transform_food_data_success(self):
        """Valida que o payload JSON padronizado é convertido corretamente, preservando float para nutricionais."""
        fake_json = [
            {
                "id": 1,
                "description": "Arroz, integral, cozido",
                "category": "Cereais e derivados",
                "energy_kcal": 124.5,
                "protein_g": 2.58,
                "lipid_g": 1.0,
                "carbohydrate_g": "25.8"
            }
        ]
        
        rows = transform_food_data(fake_json)
        
        self.assertEqual(len(rows), 1)
        row = rows[0]
        
        self.assertEqual(len(row), 7) # Verifica as 7 colunas
        
        # ID [0] é gerado via uuid4
        self.assertIsInstance(row[0], str)
        self.assertEqual(len(row[0]), 36) 
        
        self.assertEqual(row[1], "Arroz, integral, cozido")
        self.assertEqual(row[2], "Cereais e derivados")
        self.assertEqual(row[3], 124.5)
        self.assertEqual(row[4], 2.58)
        self.assertEqual(row[5], 1.0)
        self.assertEqual(row[6], 25.8)

    def test_transform_food_data_missing_and_null_fields(self):
        """Valida a tolerância de falhas para inputs ausentes, 'NA', '*', '' ou Nulos."""
        fake_json_responses = [
            {
                "id": 2,
                "description": "Alimento Misterioso",
                "energy_kcal": None,
                "protein_g": "NA",
                "lipid_g": "*",
                "carbohydrate_g": ""
                # category ausente
            }
        ]
        
        rows = transform_food_data(fake_json_responses)
        
        self.assertEqual(len(rows), 1)
        row = rows[0]
        
        self.assertEqual(row[1], "Alimento Misterioso")
        self.assertEqual(row[2], "Sem Grupo") # Fallback
        self.assertEqual(row[3], 0.0) # None -> 0.0
        self.assertEqual(row[4], 0.0) # "NA" -> 0.0
        self.assertEqual(row[5], 0.0) # "*" -> 0.0
        self.assertEqual(row[6], 0.0) # "" ou ausente -> 0.0

if __name__ == '__main__':
    unittest.main()
