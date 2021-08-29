"""
Algo App Method Unit Test

Utility library to perform unit tests of Algorand App's methods call expected
behaviour.

Approval Unit Test: testing a method call expecting App's approval.
Rejection Unit Test: testing a method call expecting App's rejection.

"""

__author__ = "Cosimo Bassi <cosimo.bassi@algorand.com>"


from algosdk.error import AlgodHTTPError
from algosdk.future import transaction


class Tests:
    def __init__(self):
        self.approval_unit_tests: int = 0
        self.rejection_unit_tests: int = 0
        self.passed_tests: int = 0
        self.failed_tests: int = 0

    def __str__(self):
        return f"📊 Test Stats\n" \
               f"Approval Unit Tests: {self.approval_unit_tests}\n" \
               f"Rejection Unit Tests: {self.rejection_unit_tests}\n" \
               f"Passed: {self.passed_tests}\n" \
               f"Failed: {self.failed_tests}"

    def approval(self):
        self.approval_unit_tests += 1

    def rejection(self):
        self.rejection_unit_tests += 1

    def passed(self):
        self.passed_tests += 1

    def failed(self):
        self.failed_tests += 1


def wait_for_confirmation(client, txid):
    """
    Utility function to wait until the transaction is confirmed before
    proceeding.
    """
    last_round = client.status().get("last-round")
    txinfo = client.pending_transaction_info(txid)

    while not txinfo.get("confirmed-round", -1) > 0:
        print(f"Waiting for transaction {txid} confirmation.")
        last_round += 1
        client.status_after_block(last_round)
        txinfo = client.pending_transaction_info(txid)

    print(f"Transaction {txid} confirmed in round "
          f"{txinfo.get('confirmed-round')}.")
    return txinfo


def approval_unit_test(algod_client, test_stats: Tests, app_call):
    """
    App method call unit test, expected behaviour: app call approval.

    Args:
        algod_client:
        test_stats:
        app_call: signed application call transaction

    """
    transaction.write_to_file([app_call], "/tmp/txn.signed", overwrite=True)
    method = app_call.dictify()['txn']['apaa'][0].decode()
    tx_id = app_call.transaction.get_txid()
    print(f"Method: {method}\t\tExpected ASC1 behaviour: Approval")
    try:
        algod_client.send_transactions([app_call])
        wait_for_confirmation(algod_client, tx_id)
    except AlgodHTTPError:
        test_stats.failed()
        print("⛔️ Failed! Transaction(s) rejected while expecting approval.\n")
    else:
        test_stats.passed()
        print("✅️ Passed! Transaction(s) approved as expected.\n")
    finally:
        test_stats.approval()


def rejection_unit_test(algod_client, test_stats: Tests, app_call):
    """
    App method call unit test, expected behaviour: app call rejection.

    Args:
        algod_client:
        test_stats:
        app_call: signed application call transaction

    """
    transaction.write_to_file([app_call], "/tmp/txn.signed", overwrite=True)
    method = app_call.dictify()['txn']['apaa'][0].decode()
    tx_id = app_call.transaction.get_txid()
    print(f"Method: {method}\t\tExpected ASC1 behaviour: Rejection")
    try:
        algod_client.send_transactions([app_call])
        wait_for_confirmation(algod_client, tx_id)
    except AlgodHTTPError:
        test_stats.passed()
        print("✅️ Passed! Transaction(s) rejected as expected.\n")
    else:
        test_stats.failed()
        print("⛔️ Failed! Transaction(s) approved while expecting rejection.\n")
    finally:
        test_stats.rejection()
