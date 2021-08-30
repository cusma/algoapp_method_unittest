
import base64
import dataclasses

import algosdk
from algosdk.kmd import KMDClient
from algosdk.wallet import Wallet
from algosdk.v2client import algod, indexer
from algosdk import mnemonic, util

from algoapp_method_unittest import *

from asa_state_observer.asa_state_observer_asc1 import (
    compile_stateful,
    asa_state_observer,
    asa_state_observe_closeout_or_clear,
    GLOBAL_INTS,
    GLOBAL_BYTES,
    LOCAL_INTS,
    LOCAL_BYTES,
    METHOD_ASA_OPTED_IN,
    METHOD_ASA_AMOUNT_EQ,
    METHOD_ASA_AMOUNT_GT,
    METHOD_ASA_AMOUNT_GE,
    METHOD_ASA_AMOUNT_LT,
    METHOD_ASA_AMOUNT_LE,
)

__author__ = "Cosimo Bassi <cosimo.bassi@algorand.com>"


ALGOD_ADDRESS = "http://localhost:4001"
ALGOD_TOKEN = 64 * "a"
KMD_ADDRESS = "http://localhost:4002"
KMD_TOKEN = 64 * "a"
INDEXER_ADDRESS = "http://localhost:8980"
INDEXER_TOKEN = 64 * "a"

FUND_ACCOUNT_ALGOS = util.algos_to_microalgos(1000)  # Algos
FLAT_FEE = 1000

algod_client = algod.AlgodClient(
    algod_token=ALGOD_TOKEN, algod_address=ALGOD_ADDRESS
)

kmd_client = KMDClient(
    kmd_token=KMD_TOKEN, kmd_address=KMD_ADDRESS
)

indexer_client = indexer.IndexerClient(
    indexer_token=INDEXER_TOKEN, indexer_address=INDEXER_ADDRESS
)


@dataclasses.dataclass
class Account:
    address: str
    private_key: str
    lsig: str = None

    def mnemonic(self) -> str:
        return mnemonic.from_private_key(self.private_key)

    def is_lsig(self):
        return not self.private_key and self.lsig

    @classmethod
    def create_account(cls):
        private_key, address = algosdk.account.generate_account()
        return cls(private_key=private_key, address=address)


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


def get_params(client):
    params = client.suggested_params()
    params.flat_fee = True
    params.fee = FLAT_FEE
    return params


def sign(account, txn):
    if account.is_lsig():
        return transaction.LogicSigTransaction(txn, account.lsig)
    else:
        assert account.private_key
        return txn.sign(account.private_key)


def sign_send_wait(account, txn):
    """Sign a transaction, submit it, and wait for its confirmation."""
    signed_txn = sign(account, txn)
    tx_id = signed_txn.transaction.get_txid()
    transaction.write_to_file([signed_txn], "/tmp/txn.signed", overwrite=True)
    algod_client.send_transactions([signed_txn])
    wait_for_confirmation(algod_client, tx_id)

    return algod_client.pending_transaction_info(tx_id)


def find_sandbox_faucet():
    default_wallet_name = kmd_client.list_wallets()[0]["name"]
    wallet = Wallet(
        default_wallet_name, "", kmd_client
    )  # Sandbox's wallet has no password

    for account_ in wallet.list_keys():
        info = indexer_client.account_info(account_).get("account")
        if info.get("status") == "Online" and info.get("created-at-round") == 0:
            return Account(
                address=account_,
                private_key=wallet.export_key(account_)
            )

    raise KeyError("Could not find sandbox faucet")


def create_and_fund(faucet: Account) -> Account:
    new_account = Account.create_account()
    print(f"Funding new account: {new_account.address}.")

    fund(faucet, new_account)

    return new_account


def fund(faucet: Account, receiver: Account, amount=FUND_ACCOUNT_ALGOS):
    params = get_params(algod_client)
    txn = transaction.PaymentTxn(
        faucet.address, params, receiver.address, amount
    )
    return sign_send_wait(faucet, txn)


def compile_program(source_code):
    compile_response = algod_client.compile(source_code)
    return base64.b64decode(compile_response["result"])


def create_application(creator: Account):
    global_schema = transaction.StateSchema(GLOBAL_INTS, GLOBAL_BYTES)
    local_schema = transaction.StateSchema(LOCAL_INTS, LOCAL_BYTES)

    approval_program_teal = compile_stateful(asa_state_observer())
    approval_program = compile_program(approval_program_teal)
    with open('/tmp/approval.teal', 'w') as f:
        f.write(approval_program_teal)

    clear_program_teal = compile_stateful(
        asa_state_observe_closeout_or_clear()
    )
    clear_program = compile_program(clear_program_teal)
    with open('/tmp/clear.teal', 'w') as f:
        f.write(clear_program_teal)

    on_complete = transaction.OnComplete.NoOpOC.real
    params = get_params(algod_client)

    txn = transaction.ApplicationCreateTxn(
        creator.address,
        params,
        on_complete,
        approval_program,
        clear_program,
        global_schema,
        local_schema,
    )
    transaction_response = sign_send_wait(creator, txn)
    return transaction_response["application-index"]


def create_asset(
        creator_account,
        total: int,
        unit_name: str,
        asset_name: str,
        decimals: int,
        frozen: bool = False,
        manager=None,
        reserve=None,
        freeze=None,
        clawback=None,
        disable_empty_addresses: bool = True,
):
    """Create an asset and return its ID."""
    params = get_params(algod_client)

    txn = transaction.AssetConfigTxn(
        sender=creator_account.address,
        sp=params,
        total=total,
        decimals=decimals,
        unit_name=unit_name,
        asset_name=asset_name,
        manager=creator_account.address if not isinstance(manager, str) else manager,
        reserve=creator_account.address if not isinstance(reserve, str) else reserve,
        freeze=creator_account.address if not isinstance(freeze, str) else freeze,
        clawback=creator_account.address if not isinstance(clawback, str) else clawback,
        default_frozen=False if not frozen else True,
        strict_empty_address_check=disable_empty_addresses,
    )
    ptx = sign_send_wait(creator_account, txn)
    return ptx["asset-index"]


def call_asa_state_observer(
        method: str,
        caller: Account,
        app_id: int,
        target_asa_id: int,
        target_account: Account,
        amount: int = 0,
):
    params = get_params(algod_client)

    args = []
    if method == METHOD_ASA_OPTED_IN:
        args = [METHOD_ASA_OPTED_IN.encode()]
    elif method == METHOD_ASA_AMOUNT_EQ:
        args = [METHOD_ASA_AMOUNT_EQ.encode(), amount]
    elif method == METHOD_ASA_AMOUNT_GT:
        args = [METHOD_ASA_AMOUNT_GT.encode(), amount]
    elif method == METHOD_ASA_AMOUNT_GE:
        args = [METHOD_ASA_AMOUNT_GE.encode(), amount]
    elif method == METHOD_ASA_AMOUNT_LT:
        args = [METHOD_ASA_AMOUNT_LT.encode(), amount]
    elif method == METHOD_ASA_AMOUNT_LE:
        args = [METHOD_ASA_AMOUNT_LE.encode(), amount]
    else:
        quit(f"{method} is an invalid method call.")

    test_txn = transaction.ApplicationNoOpTxn(
        sender=caller.address,
        sp=params,
        index=app_id,
        app_args=args,
        foreign_assets=[target_asa_id],
        accounts=[target_account.address],
    )
    return sign(caller, test_txn)


def test():
    faucet = find_sandbox_faucet()
    print(f" --- Sandbox ALGO Faucet: {faucet.address}.\n")

    deployer = create_and_fund(faucet)
    asa_state_observer_id = create_application(deployer)
    print(f" --- ASA State Observer App ID: {asa_state_observer_id}.\n")

    test_asa_id = create_asset(
        creator_account=deployer,
        total=1,
        unit_name='TST',
        asset_name='Test ASA',
        decimals=0,
    )
    print(f" --- Test Asset ID: {test_asa_id}.\n")

    test_stats = Tests()

    # --/ APPROVAL TESTS SESSION
    approval_unit_test(
        algod_client,
        test_stats,
        call_asa_state_observer(
            method=METHOD_ASA_OPTED_IN,
            caller=deployer,
            app_id=asa_state_observer_id,
            target_asa_id=test_asa_id,
            target_account=deployer
        )
    )

    approval_unit_test(
        algod_client,
        test_stats,
        call_asa_state_observer(
            method=METHOD_ASA_AMOUNT_EQ,
            caller=deployer,
            app_id=asa_state_observer_id,
            target_asa_id=test_asa_id,
            target_account=deployer,
            amount=1
        )
    )

    approval_unit_test(
        algod_client,
        test_stats,
        call_asa_state_observer(
            method=METHOD_ASA_AMOUNT_GT,
            caller=deployer,
            app_id=asa_state_observer_id,
            target_asa_id=test_asa_id,
            target_account=deployer,
            amount=0
        )
    )

    approval_unit_test(
        algod_client,
        test_stats,
        call_asa_state_observer(
            method=METHOD_ASA_AMOUNT_GE,
            caller=deployer,
            app_id=asa_state_observer_id,
            target_asa_id=test_asa_id,
            target_account=deployer,
            amount=0
        )
    )

    approval_unit_test(
        algod_client,
        test_stats,
        call_asa_state_observer(
            method=METHOD_ASA_AMOUNT_GE,
            caller=deployer,
            app_id=asa_state_observer_id,
            target_asa_id=test_asa_id,
            target_account=deployer,
            amount=1
        )
    )

    approval_unit_test(
        algod_client,
        test_stats,
        call_asa_state_observer(
            method=METHOD_ASA_AMOUNT_LT,
            caller=deployer,
            app_id=asa_state_observer_id,
            target_asa_id=test_asa_id,
            target_account=deployer,
            amount=42
        )
    )

    approval_unit_test(
        algod_client,
        test_stats,
        call_asa_state_observer(
            method=METHOD_ASA_AMOUNT_LE,
            caller=deployer,
            app_id=asa_state_observer_id,
            target_asa_id=test_asa_id,
            target_account=deployer,
            amount=42
        )
    )

    approval_unit_test(
        algod_client,
        test_stats,
        call_asa_state_observer(
            method=METHOD_ASA_AMOUNT_LE,
            caller=deployer,
            app_id=asa_state_observer_id,
            target_asa_id=test_asa_id,
            target_account=deployer,
            amount=1
        )
    )
    # --/ END APPROVAL TESTS SESSION

    # --/ REJECTION TESTS SESSION
    rejection_unit_test(
        algod_client,
        test_stats,
        call_asa_state_observer(
            method=METHOD_ASA_OPTED_IN,
            caller=deployer,
            app_id=asa_state_observer_id,
            target_asa_id=42,
            target_account=deployer
        )
    )

    rejection_unit_test(
        algod_client,
        test_stats,
        call_asa_state_observer(
            method=METHOD_ASA_AMOUNT_EQ,
            caller=deployer,
            app_id=asa_state_observer_id,
            target_asa_id=test_asa_id,
            target_account=deployer,
            amount=42
        )
    )

    rejection_unit_test(
        algod_client,
        test_stats,
        call_asa_state_observer(
            method=METHOD_ASA_AMOUNT_GT,
            caller=deployer,
            app_id=asa_state_observer_id,
            target_asa_id=test_asa_id,
            target_account=deployer,
            amount=1
        )
    )

    rejection_unit_test(
        algod_client,
        test_stats,
        call_asa_state_observer(
            method=METHOD_ASA_AMOUNT_GE,
            caller=deployer,
            app_id=asa_state_observer_id,
            target_asa_id=test_asa_id,
            target_account=deployer,
            amount=42
        )
    )

    rejection_unit_test(
        algod_client,
        test_stats,
        call_asa_state_observer(
            method=METHOD_ASA_AMOUNT_LT,
            caller=deployer,
            app_id=asa_state_observer_id,
            target_asa_id=test_asa_id,
            target_account=deployer,
            amount=1
        )
    )

    rejection_unit_test(
        algod_client,
        test_stats,
        call_asa_state_observer(
            method=METHOD_ASA_AMOUNT_LE,
            caller=deployer,
            app_id=asa_state_observer_id,
            target_asa_id=test_asa_id,
            target_account=deployer,
            amount=0
        )
    )
    # --/ END REJECTION TESTS SESSION

    return test_stats


if __name__ == "__main__":
    print(test().__str__())
