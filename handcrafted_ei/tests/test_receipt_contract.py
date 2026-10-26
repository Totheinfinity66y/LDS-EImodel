import json
from pathlib import Path
import tempfile
import unittest
from handcrafted_ei.receipt import verify


class ReceiptContractTests(unittest.TestCase):
    def test_unsupported_receipt_is_not_silently_accepted(self):
        for schema in (None,1,3):
            with tempfile.TemporaryDirectory() as directory:
                out=Path(directory)
                item={'experiment':'unsupported'}
                if schema is not None: item['schema']=schema
                for name,value in [('archives',{}),('summary',{}),('config',{}),('manifest',[item])]:
                    (out/(name+'.json')).write_text(json.dumps(value),encoding='utf-8')
                with self.assertRaisesRegex(ValueError,'schema 2'):
                    verify(out,write_result=False)
