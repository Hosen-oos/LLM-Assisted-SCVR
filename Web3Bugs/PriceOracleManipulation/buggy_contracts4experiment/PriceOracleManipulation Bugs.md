## PriceOracleManipulation Bugs

__S1__: Price oracle manipulation. 3 16 20 42 52

+ __S1-1__: AMM price oracle manipulation.

  3 20 52

+ __S1-2__: Sandwich attack.

  42 52

+ __S1-3__: Non-AMM price oracle manipulation.

  16



S1-1:

3 H-03

20 H-05

20 H-06

20 H-13

23 H-10 

52 H-02 

52 H-05

52 H-10

52 H-18

67 H-03

70 H-06

70 H-07

78 H-05

78 H-07

83 H-05



S1-2 

20 H-07

42 H-09

42 H-12

52 H-01

52 H-22

52 H-29

52 H-31

193 H-02



S1-3

16 H-01

 

**Project 3**

## [[H-03] Price feed can be manipulated](https://github.com/code-423n4/2021-04-marginswap-findings/issues/21)

Anyone can trigger an update to the price feed by calling `PriceAware.getCurrentPriceInPeg(token, inAmount, forceCurBlock=true)`.
If the update window has passed, the price will be computed by simulating a Uniswap-like trade with the amounts.
This simulation uses the reserves of the Uniswap pairs which can be changed drastically using flash loans to yield almost arbitrary output amounts, and thus prices. Wrong prices break the core functionality of the contracts such as borrowing on margin, liquidations, etc.

Recommend against using the Uniswap spot price as the real price. Uniswap itself warns against this and instead recommends implementing a [TWAP price oracle](https://uniswap.org/docs/v2/smart-contract-integration/building-an-oracle/) using the `price*CumulativeLast` variables.



**Project 16**

## [[H-01] Wrong trading pricing calculations](https://github.com/code-423n4/2021-06-tracer-findings/issues/119)

_Submitted by 0xsanson, also found by shw_

In the `Pricing` contract, an agent can manipulate the trading prices by spamming a high amount of trades.

Indeed an agent can create a high amount of orders at an arbitrary price and with a near-zero amount (so the agent doesn't even need large funds); next he/she pairs the orders with another account and calls `Trader.executeTrade`; now every order calls a `Pricing.recordTrade` using the arbitrary price set by the agent.

Since the trades are all made in the same hour, by the way `hourlyTracerPrices[currentHour]` is calculated, it skews the average price towards the price set by the agent. This arbitrary value is used to calculate the `fundingRates` and the `fairPrice`, allowing a malicious agent the ability to manipulate the market.

Recommend passing the `fillAmount` parameter to `recordTrade(...)`, and calculate `hourlyTracerPrices[currentHour].trades` summing `fillAmount` instead of 1 every trade.

**[raymogg (Tracer) confirmed](https://github.com/code-423n4/2021-06-tracer-findings/issues/119#issuecomment-873747695):**

 > Issue is valid, and there appear to be a few other issues that reference similar problems.
 >
 > The Trader contract will have a whitelist allowing only select relayers to push orders on chain. As long as off chain order books have sufficient liquidity, this issue is then mitigated as users can't just arbitrarily match orders and send them in, they must be matched on a book with liquidity. To alter the price you would then need to eat through significant liquidity (increasing the cost of this attack).



**Project 20**

## [[H-05] Synth `realise` is vulnerable to flash loan attacks](https://github.com/code-423n4/2021-07-spartan-findings/issues/40)

_Submitted by jonah1005, also found by a_delamo_

Synth `realise` function calculates `baseValueLP` and `baseValueSynth` base on AMM spot price which is vulnerable to flash loan attack. `Synth`'s lp is subject to `realise` whenever the AMM ratio is different than Synth's debt ratio.

The attack does not necessarily require a flash loan. A big whale of the lp token holders could keep calling `realise` by shifting token ratio of AMM pool back and forth.

The vulnerability is located at `Synth.sol` [L187-L199](https://github.com/code-423n4/2021-07-spartan/blob/e2555aab44d9760fdd640df9095b7235b70f035e/contracts/Synth.sol#L187-L199). Where the formula [here](https://github.com/code-423n4/2021-07-spartan/blob/e2555aab44d9760fdd640df9095b7235b70f035e/contracts/Utils.sol#L114-L126) is dangerous.

Here's a script for conducting flashloan attack:

```python
flashloan_amount = init_amount
user = w3.eth.accounts[0]
marked_token.functions.transfer(user, flashloan_amount).transact()
marked_token.functions.transfer(token_pool.address, flashloan_amount).transact({'from': user})
token_pool.functions.addForMember(user).transact({'from': user})
received_lp = token_pool.functions.balanceOf(user).call()
synth_balance_before_realise = token_synth.functions.mapSynth_LPBalance(token_pool.address).call()
token_synth.functions.realise(token_pool.address).transact()
token_pool.functions.transfer(token_pool.address, received_lp).transact({'from': user})
token_pool.functions.removeForMember(user).transact({'from': user})
token_synth.functions.realise(token_pool.address).transact()
synth_balance_after_realise = token_synth.functions.mapSynth_LPBalance(token_pool.address).call()
print('synth_lp_balance_after_realise', synth_balance_after_realise)
print('synth_lp_balance_before_realise', synth_balance_before_realise)

```

Output:

```
synth_balance_after_realise 1317859964829313908162
synth_balance_before_realise 2063953488372093023256
```

Calculating Lp token's value base on AMM protocol is known to be dangerous.
There are a few steps that might solve the issue:

1. calculate token's price from a reliable source.  Implement a TWAP oracle or uses chainlink oracle.
2. calculate lp token value based on anti-flashloan formula.  Alpha finance's formula is a good reference: https://blog.alphafinance.io/fair-lp-token-pricing

**[verifyfirst (Spartan) confirmed and disagreed with severity](https://github.com/code-423n4/2021-07-spartan-findings/issues/40#issuecomment-883856664):**

 > A proposal has been suggested to limit the use of realise() for a DAO proposal. This will allow only liquidity providers to choose the outcome of a function that directly affects them.

## [[H-06] `SynthVault` rewards can be gamed](https://github.com/code-423n4/2021-07-spartan-findings/issues/166)

_Submitted by cmichel_

The `SynthVault._deposit` function adds `weight` for the user that depends on the spot value of the deposit synth amount in `BASE`.

This spot price can be manipulated and the cost of manipulation is relative to the pool's liquidity.
However, the reward (see `calcReward`) is measured in BASE tokens unrelated to the pool.
Therefore, if the pool's liquidity is low and the reward reserve is high, the attack can be profitable:

1. Manipulate the pool spot price of the `iSYNTH(_synth).LayerONE()` pool by dripping a lot of `BASE` into it repeatedly (sending lots of smaller trades is less costly due to the [path-independence of the continuous liquidity model](https://docs.thorchain.org/thorchain-finance/continuous-liquidity-pools)). This increases the `BASE` per `token` price.
2. Call `SynthVault.depositForMember` and deposit a _small_ amount of synth token. The `iUTILS(_DAO().UTILS()).calcSpotValueInBase(iSYNTH(_synth).LayerONE(), _amount)` will return an inflated weight due to the price.
3. Optionally drip more `BASE` into the pool and repeat the deposits
4. Drip back `token` to the pool to rebalance it

The user's `weight` is now inflated compared to the deposited / locked-up amount and they can claim a large share of the rewards. The cost of the attack depends on the pool's liquidity and the profit depends on the reserve. It could therefore be profitable under certain circumstances.

Recommend tracking a TWAP price of the synth instead, store the deposited synths instead, and compute the weight & total weight on the fly based on the TWAP * deposit amount instead of at the time of deposit.

**[verifyfirst (Spartan) acknowledged](https://github.com/code-423n4/2021-07-spartan-findings/issues/166#issuecomment-884641152):**

 > There is already a discussion in place to change spot rate to swap rate calculation for weights.

## [[H-07] Missing slippage checks](https://github.com/code-423n4/2021-07-spartan-findings/issues/171)

_Submitted by cmichel, also found by tensors_

There are no minimum amounts out, or checks that frontrunning/slippage is sufficiently mitigated.
This means that anyone with enough capital can force arbitrarily large slippage by sandwiching transactions, close to 100%. See issue page for referenced code.

Recommend adding a minimum amount out parameter. The function reverts if the minimum amount isn't obtained.

**[verifyfirst (Spartan) acknowledge:](https://github.com/code-423n4/2021-07-spartan-findings/issues/85#issuecomment-884593067)**

> We acknowledge the issue for the protocol's AMM, but if this becomes a large issue in the future, the router is easily upgradeable to include a minimum rate parameter.

**[SamusEldburg (Spartan) confirmed and disagreed with severity:](https://github.com/code-423n4/2021-07-spartan-findings/issues/85#issuecomment-889638485)**

> Have changed this to confirmed; even though we already were aware of it; we have discussed and are happy to add in a UI-handed arg for minAmount now rather than reactively in the future. Disagree with severity though; this wasn't a problem with V1 at all.

**[ghoul-sol (Judge) commented](https://github.com/code-423n4/2021-07-spartan-findings/issues/85#issuecomment-894863717):**

> I'll keep high risk as sandwich attacks are very common and risk of getting a bad swap is real.

## [[H-13] Flash loan manipulation on `getPoolShareWeight` of `Utils`](https://github.com/code-423n4/2021-07-spartan-findings/issues/238)

_Submitted by shw_

The `getPoolShareWeight` function returns a user's pool share weight by calculating how many SPARTAN the user's LP tokens account for. However, this approach is vulnerable to flash loan manipulation since an attacker can swap a large number of TOKEN to SPARTAN to increase the number of SPARTAN in the pool, thus effectively increasing his pool share weight.

According to the implementation of `getPoolShareWeight,` a user's pool share weight is calculated by `uints * baseAmount / totalSupply`, where `uints` is the number of user's LP tokens, `totalSupply` is the total supply of LP tokens, and `baseAmount` is the number of SPARTAN in the pool. Thus, a user's pool share weight is proportional to the number of SPARTAN in the pool. Consider the following attack scenario:

1. Supposing the attacked pool is SPARTAN-WBNB. The attacker first prepares some LP tokens (WBNB-SPP) by adding liquidity to the pool.
2. The attacker then swaps a large number of WBNB to SPARTAN, which increases the pool's `baseAmount`. He could split his trade into small amounts to reduce slip-based fees.
3. The attacker now wants to increase his weight in the `DaoVault`. He adds his LP tokens to the pool by calling the `deposit` function of `Dao.`
4. `Dao` then calls `depositLP` of `DaoVault`, causing the attacker's weight to be recalculated. Due to the large proportion of SPARTAN in the pool, the attacker's weight is artificially increased.
5. With a higher member weight, the attacker can, for example, vote the current proposal with more votes than he should have or obtain more rewards when calling `harvest` of the `Dao` contract.
6. The attacker then swaps back SPARTAN to WBNB and only loses the slip-based fees.

Referenced code:
[Utils.sol#L46-L50](https://github.com/code-423n4/2021-07-spartan/blob/main/contracts/Utils.sol#L46-L50),
[Utils.sol#L70-L77](https://github.com/code-423n4/2021-07-spartan/blob/main/contracts/Utils.sol#L70-L77),
[DaoVault.sol#L44-L56](https://github.com/code-423n4/2021-07-spartan/blob/main/contracts/DaoVault.sol#L44-L56),
[Dao.sol#L201](https://github.com/code-423n4/2021-07-spartan/blob/main/contracts/Dao.sol#L201), and
[Dao.sol#L570](https://github.com/code-423n4/2021-07-spartan/blob/main/contracts/Dao.sol#L570).

A possible mitigation is to record the current timestamp when a user's weight in the `DaoVault` or `BondVault` is recalculated and force the new weight to take effect only after a certain period, e.g., a block time. This would prevent the attacker from launching the attack since there is typically no guarantee that he could arbitrage the WBNB back in the next block.

**[SamusElderg (Spartan) confirmed and disagreed with severity](https://github.com/code-423n4/2021-07-spartan-findings/issues/238#issuecomment-886351432):**

 > Recommended mitigation has been included in contributors ongoing discussions to make this more resistant to manipulation

**[ghoul-sol (judge) commented](https://github.com/code-423n4/2021-07-spartan-findings/issues/238#issuecomment-894866142):**

 > Keeping high risk because of impact



**Project 42**

## [[H-09] treasury is vulnerable to sandwich attack](https://github.com/code-423n4/2021-10-mochi-findings/issues/60)

_Submitted by jonah1005_

#### Impact

There's a permissionless function `veCRVlock` in `MochiTreasury`. Since everyone can trigger this function, the attacker can launch a sandwich attack with flashloan to steal the funds.
[MochiTreasuryV0.sol#L73-L94](https://github.com/code-423n4/2021-10-mochi/blob/main/projects/mochi-core/contracts/treasury/MochiTreasuryV0.sol#L73-L94)

Attackers can possibly steal all the funds in the treasury. I consider this is a high-risk issue.

#### Proof of Concept

[MochiTreasuryV0.sol#L73-L94](https://github.com/code-423n4/2021-10-mochi/blob/main/projects/mochi-core/contracts/treasury/MochiTreasuryV0.sol#L73-L94)

Here's an exploit pattern

1.  Flashloan and buy CRV the uniswap pool
2.  Trigger `veCRVlock()`
3.  The treasury buys CRV at a very high price.
4.  Sell CRV and pay back the loan.

#### Recommended Mitigation Steps

Recommend to add `onlyOwner` modifier.

**[ryuheimat (Mochi) confirmed](https://github.com/code-423n4/2021-10-mochi-findings/issues/60)**

## [[H-12] feePool is vulnerable to sandwich attack.](https://github.com/code-423n4/2021-10-mochi-findings/issues/65)

_Submitted by jonah1005_

#### Impact

There's a permissionless function `distributeMochi` in [FeePoolV0.sol L55-L62](https://github.com/code-423n4/2021-10-mochi/blob/main/projects/mochi-core/contracts/feePool/FeePoolV0.sol#L55-L62). Since everyone can trigger this function, an attacker can launch a sandwich attack with flashloan to steal the funds.

The devs have mentioned this concern in the comment. An attacker can steal the funds with a flash loan attack.

Attackers can steal all the funds in the pool. I consider this is a high-risk issue.

#### Proof of Concept

[FeePoolV0.sol#L55-L62](https://github.com/code-423n4/2021-10-mochi/blob/main/projects/mochi-core/contracts/feePool/FeePoolV0.sol#L55-L62)

Please refer to [yDai Incident](https://peckshield.medium.com/the-ydai-incident-analysis-forced-investment-2b8ac6058eb5) to check the severity of a `harvest` function without slippage control.

Please refer to [Mushrooms-finance-theft](https://medium.com/immunefi/mushrooms-finance-theft-of-yield-bug-fix-postmortem-16bd6961388f) to check how likely this kind of attack might happen.

#### Recommended Mitigation Steps

If the dev wants to make this a permissionless control, the contract should calculate a min return based on TWAP and check the slippage.


### Comments:

**[ryuheimat (Mochi) disputed](https://github.com/code-423n4/2021-10-mochi-findings/issues/65#issuecomment-953031170):**

 > I think this is same case as https://github.com/code-423n4/2021-10-mochi-findings/issues/60

**[ghoul-sol (judge) commented](https://github.com/code-423n4/2021-10-mochi-findings/issues/65#issuecomment-957027904):**

 > The same attack, different part of the code. I'll keep them both.



**Project 52**

## [[H-02] Redemption value of synths can be manipulated to drain `VaderPool` of all native assets](https://github.com/code-423n4/2021-11-vader-findings/issues/3)

_Submitted by TomFrenchBlockchain_

#### Impact

Draining of funds from `VaderPool`

#### Proof of Concept

See the `VaderPool.mintSynth` function:
<https://github.com/code-423n4/2021-11-vader/blob/607d2b9e253d59c782e921bfc2951184d3f65825/contracts/dex-v2/pool/VaderPoolV2.sol#L126-L167>

As the pool's reserves can be manipulated through flashloans similar to on UniswapV2, an attacker may set the exchange rate between `nativeAsset` and synths (calculated from the reserves). An attacker can exploit this to drain funds from the pool.

1.  The attacker first flashloans and sells a huge amount of `foreignAsset` to the pool. The pool now thinks `nativeAsset` is extremely valuable.
2.  The attacker now uses a relatively small amount of `nativeAsset` to mint synths using `VaderPool.mintSynth`. As the pool thinks `nativeAsset` is very valuable the attacker will receive a huge amount of synths.
3.  The attacker can now manipulate the pool in the opposite direction by buying up the `foreignAsset` they sold to the pool. `nativeAsset` is now back at its normal price, or perhaps artificially low if the attacker wishes.
4.  The attacker now burns all of their synths. As `nativeAsset` is considered much less valuable than at the point the synths were minted it takes a lot more of `nativeAsset` in order to pay out for the burned synths.

For the price of a flashloan and some swap fees, the attacker has now managed to extract a large amount of `nativeAsset` from the pool. This process can be repeated as long as it is profitable.

#### Recommended Mitigation Steps

Prevent minting of synths or at the very least tie the exchange rate to a manipulation resistant oracle.

## [[H-05] LPs of VaderPoolV2 can manipulate pool reserves to extract funds from the reserve.](https://github.com/code-423n4/2021-11-vader-findings/issues/31)

_Submitted by TomFrenchBlockchain, also found by WatchPug_

#### Impact

Impermanent loss protection can be exploited to drain the reserve.

#### Proof of Concept

In `VaderPoolV2.burn` we calculate the current losses that the LP has made to impermanent loss.

<https://github.com/code-423n4/2021-11-vader/blob/3a43059e33d549f03b021d6b417b7eeba66cf62e/contracts/dex-v2/pool/VaderPoolV2.sol#L237-L269>

These losses are then refunded to the LP in VADER tokens from the reserve

<https://github.com/code-423n4/2021-11-vader/blob/3a43059e33d549f03b021d6b417b7eeba66cf62e/contracts/dex-v2/router/VaderRouterV2.sol#L208-L227>

This loss is calculated by the current reserves of the pool so if an LP can manipulate the pool's reserves they can artificially engineer a huge amount of IL in order to qualify for a payout up to the size of their LP position.

<https://github.com/code-423n4/2021-11-vader/blob/3a43059e33d549f03b021d6b417b7eeba66cf62e/contracts/dex/math/VaderMath.sol#L73-L93>

The attack is then as follows.

1.  Be an LP for a reasonable period of time (IL protection scales linearly up to 100% after a year)
2.  Flashloan a huge amount of one of the pool's assets.
3.  Trade against the pool with the flashloaned funds to unbalance it such that your LP position has huge IL.
4.  Remove your liquidity and receive compensation from the reserve for the IL you have engineered.
5.  Re-add your liquidity back to the pool.
6.  Trade against the pool to bring it back into balance.

The attacker now holds the majority of their flashloaned funds (minus slippage/swap fees) along with a large fraction of the value of their LP position in VADER paid out from the reserve. The value of their LP position is unchanged. Given a large enough LP position, the IL protection funds extracted from the reserve will exceed the funds lost to swap fees and the attacker will be able to repay their flashloan with a profit.

This is a high risk issue as after a year any large LP is incentivised and able to perform this attack.

#### Recommended Mitigation Steps

Use a manipulation resistant oracle for the relative prices of the pool's assets (TWAP, etc.)

## [[H-10]  calculate Loss is vulnerable to flashloan attack](https://github.com/code-423n4/2021-11-vader-findings/issues/65)

_Submitted by jonah1005_

#### Impact

The VaderPool would compensate users' IL. The formula it uses to calculate lp value is vulnerable to manipulation.

The formula to calculate the lp value is similar to warp finance which is known to be unsafe. [warpfinance-incident-root-cause-analysis](https://peckshield.medium.com/warpfinance-incident-root-cause-analysis-581a4869ee00) (Please to refer to the POC section)

The Attacker can purchase an old lp position, manipulate price, take IL compensation and drain the reserve.
I consider this is a high-risk issue.

#### Proof of Concept

[VaderMath.sol#L69-L93](https://github.com/code-423n4/2021-11-vader/blob/main/contracts/dex/math/VaderMath.sol#L69-L93)

The lp value is calculated as `[(A0 * P1) + V0]` and `// [(A1 * P1) + V1]`.
Assume that there's an ETH pool and there's 100 ETH and 100 Vader in the pool.

1.  Attacker deposit 1 ETH and 1 Vader and own 1% of the liquidity.
2.  Wait 1 year
3.  Start flash loan and buy a lot ETH with 99900 Vader.
4.  There's  0.1 ETH 100,000 Vader in the pool.
5.  Burn 1 % lp at the price 1 ETH = 1,000,000 Vader.
6.  A0 \* P1 + V0 = 1 (eth) \* 1,000,000 (price) + 100 (vader)
7.  A1 \* P1 + V1 = 0.001 (eth) \* 1,000,000 (price) + 10,000 (vader)
8.  IL compensation would be around `9891000`.

#### Tools Used

None

#### Recommended Mitigation Steps

Please use the fair lp pricing formula from alpha finance instead. [fair-lp-token-pricing](https://blog.alphafinance.io/fair-lp-token-pricing/)

**[SamSteinGG (Vader) disputed](https://github.com/code-423n4/2021-11-vader-findings/issues/65#issuecomment-979141518):**

 > The described attack scenario can not be executed as the pool would actually consume the flash loan. The CLP model follows a non-linear curve that actually diminishes in value as the trade size increases, meaning that at most 25% of the total assets in the pool can be drained at a given iteration. This, on top with the fees of each transaction render this attack vector impossible. Please request a tangible attack test from the warden if this is meant to be accepted as valid.

**[alcueca (judge) commented](https://github.com/code-423n4/2021-11-vader-findings/issues/65#issuecomment-991496670):**

 > The CLP model isn't mentioned in the readme or the whitepaper. The issue is valid according to the materials supplied.

**[SamSteinGG (Vader) commented](https://github.com/code-423n4/2021-11-vader-findings/issues/65#issuecomment-995757161):**

 > @alcueca As the grading guidelines of C4 state, a documentation issue cannot constitute more than a low risk finding. We advise the severity to be lowered.











