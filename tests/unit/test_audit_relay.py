import unittest
from analysis.audit_relay import obligations, check_coverage


class IndependentRelayTests(unittest.TestCase):
    def test_final_remote_deduplicates_relay(self):
        files={'f':dict(bytes=10,origin='W1',destinations=['W2','W2','m'],final=True)}
        self.assertEqual(set(obligations(files,'m')),{('f','W2',10),('f','m',10)})

    def test_equal_counts_and_bytes_do_not_replace_identity(self):
        req=[('f','m',10),('f','W2',10)]
        wrong=[dict(file='f',destination='W2',bytes=10)]*2
        with self.assertRaises(ValueError): check_coverage(req,wrong)

    def test_missing_zero_byte_relay_rejected(self):
        req=obligations({'f':dict(bytes=0,origin='W1',destinations=['W2'],final=False)},'m')
        with self.assertRaises(ValueError):
            check_coverage(req,[dict(file='f',destination='W2',bytes=0)])

    def test_local_and_external_inputs(self):
        files={'a':dict(bytes=10,origin='m',destinations=['W1','W1'],final=False),
               'b':dict(bytes=10,origin='W1',destinations=['W1'],final=False)}
        self.assertEqual(obligations(files,'m'),[('a','W1',10)])

    def test_missing_coordinator(self):
        with self.assertRaises(ValueError): obligations({},None)

    def test_cover_with_extra_delivery_is_not_bijective(self):
        req=[('f','W2',10)]
        self.assertFalse(check_coverage(req,[dict(file='f',destination='W2',bytes=10)]*2))


if __name__=='__main__': unittest.main()
