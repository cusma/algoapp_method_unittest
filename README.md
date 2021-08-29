# AlgoApp Method Unit Test
The [`algoapp_method_unittest`](https://github.com/cusma/algoapp_method_unittest/blob/main/algoapp_method_unittest.py) 
utility library is a support to perform unit tests on Algorand App's methods call, verifying their expected behaviour.

- **Approval Unit Test**: testing a method call expecting App's approval.
- **Rejection Unit Test**: testing a method call expecting App's rejection.

#### Dependencies:
- `py-algorand-sdk` [1.7.0](https://github.com/algorand/py-algorand-sdk/releases/tag/v1.7.0)
- [`asa_state_observer_asc1`](https://github.com/cusma/asa_state_observer/blob/main/asa_state_observer_asc1.py) to run unit tests example.

## Unit Tests result example
The `algoapp_method_unittest` has been used in this example to perform unit
tests on [ASA State Observer](https://github.com/cusma/asa_state_observer) app methods' behaviour.

### ASA State Observer Unit Tests example output
```
Method: AsaOptedIn		Expected ASC1 behaviour: Approval
Transaction CCF6IGELZMQBGFT6CX62OFOBZX24RFIYGG4RHBLPWI6O4TX72QJA confirmed in round 246.
✅️ Passed! Transaction(s) approved as expected.

Method: AsaAmountEq		Expected ASC1 behaviour: Approval
Transaction LKHN777YXLALWBYDCGSLXWCXHEXAXONM6ZSD27A2SRYWJUFYQRAA confirmed in round 247.
✅️ Passed! Transaction(s) approved as expected.

Method: AsaAmountGt		Expected ASC1 behaviour: Approval
Transaction MRGZIUEKCBTS2RWYYSWDJY27AOTM3EEYINCNHE7BF5JFW5RSIRSQ confirmed in round 248.
✅️ Passed! Transaction(s) approved as expected.

Method: AsaAmountGe		Expected ASC1 behaviour: Approval
Transaction WQ64ICMCQGEUZO6AC37PE2SYGUVNBFCDDHULAA755F7WOE4BKZKA confirmed in round 249.
✅️ Passed! Transaction(s) approved as expected.

Method: AsaAmountGe		Expected ASC1 behaviour: Approval
Transaction 3JYB3VJJ3FJZYTB2KFER4CDVUGIZJCD73B5VXVCTEKCRF3QK64HQ confirmed in round 250.
✅️ Passed! Transaction(s) approved as expected.

Method: AsaAmountLt		Expected ASC1 behaviour: Approval
Transaction EQ6AWKFLIAG45XQAY35JIUFWB6V3SHNJE642YVKGMFKDZOEYPP2Q confirmed in round 251.
✅️ Passed! Transaction(s) approved as expected.

Method: AsaAmountLe		Expected ASC1 behaviour: Approval
Transaction W5FIXUY5GTBFRNOJKVRMKM6TTGMS22EOLGR2YXPISWEO5A2E3EGQ confirmed in round 252.
✅️ Passed! Transaction(s) approved as expected.

Method: AsaAmountLe		Expected ASC1 behaviour: Approval
Transaction D5OXQFNDHVWFLKADUVL5KL3WJV56PHLEPARLDJ5PU3YQW3RC7WPA confirmed in round 253.
✅️ Passed! Transaction(s) approved as expected.

Method: AsaOptedIn		Expected ASC1 behaviour: Rejection
✅️ Passed! Transaction(s) rejected as expected.

Method: AsaAmountEq		Expected ASC1 behaviour: Rejection
✅️ Passed! Transaction(s) rejected as expected.

Method: AsaAmountGt		Expected ASC1 behaviour: Rejection
✅️ Passed! Transaction(s) rejected as expected.

Method: AsaAmountGe		Expected ASC1 behaviour: Rejection
✅️ Passed! Transaction(s) rejected as expected.

Method: AsaAmountLt		Expected ASC1 behaviour: Rejection
✅️ Passed! Transaction(s) rejected as expected.

Method: AsaAmountLe		Expected ASC1 behaviour: Rejection
✅️ Passed! Transaction(s) rejected as expected.

📊 Test Stats
Approval Unit Tests: 8
Rejection Unit Tests: 6
Passed: 14
Failed: 0
```

## Tips
Use the `app_method_unittest` library with the [Sandbox](https://developer.algorand.org/articles/introducing-sandbox-20/)
in `devMode` to speed up the testing process.
