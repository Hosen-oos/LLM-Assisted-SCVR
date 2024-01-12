## [[H-01] Reward computation is wrong](https://github.com/code-423n4/2021-07-wildcredit-findings/issues/116)
_Submitted by cmichel_

The `LendingPair.accrueAccount` function distributes rewards **before** updating the cumulative supply / borrow indexes as well as the index + balance for the user (by minting supply tokens / debt).
This means the percentage of the user's balance to the total is not correct as the total can be updated several times in between.

```solidity
function accrueAccount(address _account) public {
  // distributes before updating accrual state
  _distributeReward(_account);
  accrue();
  _accrueAccountInterest(_account);

  if (_account != feeRecipient()) {
    _accrueAccountInterest(feeRecipient());
  }
}
```

**Example**: Two users deposit the same amounts in the same block. Thus, after some time they should receive the same tokens.
1. User A and B deposit 1000 tokens (in the same block) and are minted 1000 tokens in return. Total supply = `2000`
2. Assume after 50,000 blocks, `A` calls `accrueAccount(A)` which first calls `_distributeReward`. A is paid out 1000/2000 = 50% of the 50,000 blocks reward since deposit. Afterwards, `accrue` + `_accrueAccountInterest(A)` is called and `A` is minted 200 more tokens due to supplier lending rate. The supply **totalSupply is now 2200**.
3. After another 50,000 blocks, `A` calls `accrueAccount(A)` again. which first calls `_distributeReward`. A is paid out 1200/2200 = **54.5454% of the 50,000 blocks reward since deposit.**

From here, you can already see that `A` receives more than 50% of the 100,000 block rewards although they deposited at the same time as `B` and didn't deposit or withdraw any funds.
`B` will receive `~1000/2200 = 45%` (ignoring any new LP supply tokens minted for `A`'s second claim.)

The impact is that wrong rewards will be minted users which do not represent their real fair share. Usually, users will get fewer rewards than they should receive, as their individual interest was not updated yet, but the totals (total debt and total supply) could have been updated by other accounts in between.

There are two issues that both contribute to it:
- total LP supply and total debt must be updated by the **total new interest** when `accrue` is called, not only increased by an **individual user**'s interest. See my other issue "Reward computation is wrong" that goes into more depth
- Lending/borrow accrual must happen before reward distribution

**[talegift (Wild Credit) acknowledged but disagreed with severity](https://github.com/code-423n4/2021-07-wildcredit-findings/issues/116#issuecomment-880581152):**
 > _Assets not at direct risk, but the function of the protocol or its availability could be impacted, or **leak value** with a hypothetical attack path with stated assumptions, but **external requirements**._
>
> Update to severity - 2

**[ghoul-sol (Judge) commented](https://github.com/code-423n4/2021-07-wildcredit-findings/issues/116#issuecomment-890597758):**
 > Disagree with sponsor about severity, this is significant accounting error.
 
 ## [[H-07] Wrong `calcAsymmetricShare` calculation](https://github.com/code-423n4/2021-04-vader-findings/issues/214)

```Solidity
    function calcAsymmetricShare(uint u, uint U, uint A) public pure returns (uint){
        // share = (u * U * (2 * A^2 - 2 * U * u + U^2))/U^3
        // (part1 * (part2 - part3 + part4)) / part5
        uint part1 = (u * A);
        uint part2 = ((U * U) * 2);
        uint part3 = ((U * u) * 2);
        uint part4 = (u * u);
        uint numerator = ((part1 * part2) - part3) + part4;
        uint part5 = ((U * U) * U);
        return (numerator / part5);
    }
```

The inline-comment defines the number of asymmetric shares as `(u * U * (2 * A^2 - 2 * U * u + U^2))/U^3` but the `Utils.calcAsymmetricShare` function computes `(uA * 2U^2 - 2uU + u^2) / U^3` which is not equivalent as can be seen from the `A^2` term in the first term which does not occur in the second one.

The associativity on `P * part1` is wrong, and `part2` is not multiplied by `P`.

The math from the spec is not correctly implemented and could lead to the protocol being economically exploited, as the asymmetric share (which is used to determine the collateral value in base tokens) could be wrong. For example, it might be possible to borrow more than the collateral put up.

Recommend clarifying if the comment or the code is correct and fix them if not.

**[strictly-scarce (vader) confirmed](https://github.com/code-423n4/2021-04-vader-findings/issues/214#issuecomment-828468071):**
 > Valid

**[strictly-scarce (vader) commented](https://github.com/code-423n4/2021-04-vader-findings/issues/214#issuecomment-830635568):**
 > Whilst the math is incorrect, in the current implementation it is not yet implemented, so disagree with Severity (funds not lost), recommend: 2

## [[H-08] Wrong liquidity units calculation](https://github.com/code-423n4/2021-04-vader-findings/issues/204)

```Solidity
function calcLiquidityUnits(uint b, uint B, uint t, uint T, uint P) external view returns (uint units){
        if(P == 0){
            return b; // If pool is empty; use b as initial units
        } else {
            // units = ((P (t B + T b))/(2 T B)) * slipAdjustment
            // P * (part1 + part2) / (part3) * slipAdjustment
            uint slipAdjustment = getSlipAdustment(b, B, t, T);
            uint part1 = t*(B);
            uint part2 = T*(b);
            uint part3 = T*(B)*(2);
            uint _units = (P * (part1 + (part2))) / (part3);
            return _units * slipAdjustment / one;  // Divide by 10**18
        }
    }
```

The spec defines the number of LP units to be minted as `units = (P (a B + A b))/(2 A B) * slipAdjustment = P * (part1 + part2) / part3 * slipAdjustments` but the `Utils.calcLiquidityUnits` function computes `((P * part1) + part2) / part3 * slipAdjustments`.

The associativity on `P * part1` is wrong, and `part2` is not multiplied by `P`.

The math from the spec is not correctly implemented and could lead to the protocol being economically exploited, as redeeming the minted LP tokens does not result in the initial tokens anymore.

Recommend fixing the equation.

**[strictly-scarce (vader) confirmed](https://github.com/code-423n4/2021-04-vader-findings/issues/204#issuecomment-830609695):**
> Valid, but funds not at risk.


## [[H-05] Wrong liquidation logic](https://github.com/code-423n4/2021-04-marginswap-findings/issues/23)

The `belowMaintenanceThreshold` function decides if a trader can be liquidated:

```solidity
function belowMaintenanceThreshold(CrossMarginAccount storage account)
    internal
    returns (bool)
{
    uint256 loan = loanInPeg(account, true);
    uint256 holdings = holdingsInPeg(account, true);
    // The following should hold:
    // holdings / loan >= 1.1
    // =>
    return 100 * holdings >= liquidationThresholdPercent * loan;
}
```

The inequality in the last equation is wrong because it says the higher the holdings (margin + loan) compared to the loan, the higher the chance of being liquidated. The inverse equality was probably intended `return 100 * holdings <= liquidationThresholdPercent * loan;`. Users that shouldn't be liquidated can be liquidated, and users that should be liquidated cannot get liquidated.

## [[M-04] Total LP supply & total debt accrual is wrong](https://github.com/code-423n4/2021-07-wildcredit-findings/issues/115)
_Submitted by cmichel_

The total debt and total supply only increase when debt/supply is minted to the user when it should increase by the entire new interest amount on each accrual.

```solidity
function accrueAccount(address _account) public {
  _distributeReward(_account);
  // accrue only updates cumulativeInterestRate to the newInterest
  // newInterest is not added to total debt or total LP supply!
  accrue();
  // instead total debt / total LP supply is increased here by a much smaller amount, the new interest specific for the updating user
  _accrueAccountInterest(_account);

  if (_account != feeRecipient()) {
    _accrueAccountInterest(feeRecipient());
  }
}
```

The borrow rates (see `borrowRatePerBlock`) are wrong due to the wrong utilization ratio: The borrow utilization rate uses `LPToken.totalSupply`. Assume there's a single lender supplying \$100k, another single borrower borrows \$70k (ignoring irrelevant details like liquidation and the borrower not putting up collateral for the sake of the argument).
After some time debt accrued and the supplier "updates" by calling `accrue` (but the borrower does not update), this increases the LP total supply to, say, \$110k, while total debt is not updated. The utilization rate and thus the borrow rate is now less than before (from 70/100=70% to 70/110=63%). In reality, it should have increased as the supplier interest is only a fraction of the borrower accumulated debt. From now on less debt than expected accrues until the borrower is updated and total debt is increased.
To get the correct borrow rates in the current system, every borrower and every supplier would need to be updated on every accrual which is infeasible.

Recommend doing it like Compound/Aave, increase total debt and total supply on each accrual by the **total** new interest (not by the specific user's interest only).
This might require a bigger refactor because the LP token is treated as a ("lazy-evaluated") rebasing token and the total supply is indeed the total tokens in circulation `LP.totalSupply()` and one cannot mint the new interest to all users at once in each `accrue`.
That's why Compound uses an interest-bearing token and tracks total supply separately and Aave uses a real rebasing token that dynamically scales the balance in `balanceOf` and must not be updated individually for each user.