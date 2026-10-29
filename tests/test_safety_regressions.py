import unittest
from engine.parser import has_error_output_connected, normalize
from engine.checks.webhooks import check_webhooks
from engine.checks.duplicates import check_duplicate_risk

class SafetyRegressionTests(unittest.TestCase):
    def test_explicit_none_webhook_auth_is_flagged(self):
        wf = normalize({'nodes': [{'name': 'Incoming', 'type': 'n8n-nodes-base.webhook', 'parameters': {'authentication': 'none'}}]})
        self.assertTrue(any(f.check_id == 'WH-001' for f in check_webhooks(wf)))

    def test_empty_second_branch_is_not_connected(self):
        self.assertFalse(has_error_output_connected('A', {'A': {'main': [[{'node':'B'}], []]}}))

    def test_unrelated_filter_does_not_prove_deduplication(self):
        wf = normalize({'nodes': [{'name':'Hook','type':'n8n-nodes-base.webhook'}, {'name':'Filter','type':'n8n-nodes-base.if','parameters': {'condition':'amount > 1'}}], 'connections': {'Hook': {'main': [[{'node':'Filter'}]]}}})
        self.assertTrue(any(f.check_id == 'DUP-001' for f in check_duplicate_risk(wf)))

if __name__ == '__main__': unittest.main()

class WorkflowValidationTests(unittest.TestCase):
    def test_rejects_missing_nodes(self):
        from engine.parser import normalize
        with self.assertRaises(ValueError): normalize({'name':'not a workflow'})

    def test_rejects_duplicate_node_names(self):
        from engine.parser import normalize
        with self.assertRaises(ValueError): normalize({'nodes':[{'name':'x','type':'n8n-nodes-base.set'}, {'name':'x','type':'n8n-nodes-base.if'}]})

    def test_rejects_dangling_connection(self):
        from engine.parser import normalize
        with self.assertRaises(ValueError): normalize({'nodes':[{'name':'x','type':'n8n-nodes-base.set'}], 'connections':{'x':{'main':[[{'node':'missing'}]]}}})
