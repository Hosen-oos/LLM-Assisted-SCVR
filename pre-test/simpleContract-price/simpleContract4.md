**project 52**

```solidity
contract VaderPoolV2 is IVaderPoolV2, BasePoolV2, Ownable {

    // Used for safe token transfers
    using SafeERC20 for IERC20;

    // The LP wrapper contract
    ILPWrapper public wrapper;

    // The Synth Factory
    ISynthFactory public synthFactory;

    // Denotes whether the queue system is active
    bool public queueActive;
    
    constructor(bool _queueActive, IERC20 _nativeAsset)
        BasePoolV2(_nativeAsset)
    {
        queueActive = _queueActive;
    }

    function initialize(
        ILPWrapper _wrapper,
        ISynthFactory _synthFactory,
        address _router
    ) external onlyOwner {
        require(
            wrapper == ILPWrapper(_ZERO_ADDRESS),
            "VaderPoolV2::initialize: Already initialized"
        );
        require(
            _wrapper != ILPWrapper(_ZERO_ADDRESS),
            "VaderPoolV2::initialize: Incorrect Wrapper Specified"
        );
        require(
            _synthFactory != ISynthFactory(_ZERO_ADDRESS),
            "VaderPoolV2::initialize: Incorrect SynthFactory Specified"
        );
        require(
            _router != _ZERO_ADDRESS,
            "VaderPoolV2::initialize: Incorrect Router Specified"
        );
        wrapper = _wrapper;
        synthFactory = _synthFactory;
        router = _router;
    }

    function mintSynth(
        IERC20 foreignAsset,
        uint256 nativeDeposit,
        address from,
        address to
    )
        external
        override
        nonReentrant
        supportedToken(foreignAsset)
        returns (uint256 amountSynth)
    {
        nativeAsset.safeTransferFrom(from, address(this), nativeDeposit);

        ISynth synth = synthFactory.synths(foreignAsset);

        if (synth == ISynth(_ZERO_ADDRESS))
            synth = synthFactory.createSynth(
                IERC20Extended(address(foreignAsset))
            );

        (uint112 reserveNative, uint112 reserveForeign, ) = getReserves(
            foreignAsset
        ); // gas savings

        amountSynth = VaderMath.calculateSwap(
            nativeDeposit,
            reserveNative,
            reserveForeign
        );

        // TODO: Clarify
        _update(
            foreignAsset,
            reserveNative + nativeDeposit,
            reserveForeign,
            reserveNative,
            reserveForeign
        );
        synth.mint(to, amountSynth);
    }

    function burnSynth(
        IERC20 foreignAsset,
        uint256 synthAmount,
        address to
    ) external override nonReentrant returns (uint256 amountNative) {
        ISynth synth = synthFactory.synths(foreignAsset);

        require(
            synth != ISynth(_ZERO_ADDRESS),
            "VaderPoolV2::burnSynth: Inexistent Synth"
        );

        require(
            synthAmount > 0,
            "VaderPoolV2::burnSynth: Insufficient Synth Amount"
        );

        IERC20(synth).safeTransferFrom(msg.sender, address(this), synthAmount);
        synth.burn(synthAmount);

        (uint112 reserveNative, uint112 reserveForeign, ) = getReserves(
            foreignAsset
        ); // gas savings

        amountNative = VaderMath.calculateSwap(
            synthAmount,
            reserveForeign,
            reserveNative
        );

        // TODO: Clarify
        _update(
            foreignAsset,
            reserveNative - amountNative,
            reserveForeign,
            reserveNative,
            reserveForeign
        );
        nativeAsset.safeTransfer(to, amountNative);
    }
    
    function burn(uint256 id, address to)
        external
        override
        onlyRouter
        returns (
            uint256 amountNative,
            uint256 amountForeign,
            uint256 coveredLoss
        )
    {
        (amountNative, amountForeign) = _burn(id, to);

        Position storage position = positions[id];

        uint256 creation = position.creation;
        uint256 originalNative = position.originalNative;
        uint256 originalForeign = position.originalForeign;

        delete positions[id];

        // NOTE: Validate it behaves as expected for non-18 decimal tokens
        uint256 loss = VaderMath.calculateLoss(
            originalNative,
            originalForeign,
            amountNative,
            amountForeign
        );

        // TODO: Original Implementation Applied 100 Days
        coveredLoss =
            (loss * _min(block.timestamp - creation, _ONE_YEAR)) /
            _ONE_YEAR;
    }

}

```



```solidity
library VaderMath {
    uint256 public constant ONE = 1 ether;
    function calculateLiquidityUnits(
        uint256 vaderDeposited,
        uint256 vaderBalance,
        uint256 assetDeposited,
        uint256 assetBalance,
        uint256 totalPoolUnits
    ) public pure returns (uint256) {
        // slipAdjustment
        uint256 slip = calculateSlipAdjustment(
            vaderDeposited,
            vaderBalance,
            assetDeposited,
            assetBalance
        );

        // (Va + vA)
        uint256 poolUnitFactor = (vaderBalance * assetDeposited) +
            (vaderDeposited * assetBalance);

        // 2VA
        uint256 denominator = ONE * 2 * vaderBalance * assetBalance;

        // P * [(Va + vA) / (2 * V * A)] * slipAdjustment
        return ((totalPoolUnits * poolUnitFactor) / denominator) * slip;
    }

    function calculateLoss(
        uint256 originalVader,
        uint256 originalAsset,
        uint256 releasedVader,
        uint256 releasedAsset
    ) public pure returns (uint256 loss) {

        // [(A0 * P1) + V0]
        uint256 originalValue = ((originalAsset * releasedVader) /
            releasedAsset) + originalVader;

        // [(A1 * P1) + V1]
        uint256 releasedValue = ((releasedAsset * releasedVader) /
            releasedAsset) + releasedVader;

        // [(A0 * P1) + V0] - [(A1 * P1) + V1]
        if (originalValue > releasedValue) loss = originalValue - releasedValue;
    }

    function calculateSwap(
        uint256 amountIn,
        uint256 reserveIn,
        uint256 reserveOut
    ) public pure returns (uint256 amountOut) {
        // x * Y * X
        uint256 numerator = amountIn * reserveIn * reserveOut;

        // (x + X) ^ 2
        uint256 denominator = pow(amountIn + reserveIn);

        amountOut = numerator / denominator;
    }

    function delta(uint256 a, uint256 b) public pure returns (uint256) {
        return a > b ? a - b : b - a;
    }

    function pow(uint256 a) public pure returns (uint256) {
        return a * a;
    }

    function root(uint256 a) public pure returns (uint256 c) {
        if (a > 3) {
            c = a;
            uint256 x = a / 2 + 1;
            while (x < c) {
                c = x;
                x = (a / x + x) / 2;
            }
        } else if (a != 0) {
            c = 1;
        }
    }
}

```



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