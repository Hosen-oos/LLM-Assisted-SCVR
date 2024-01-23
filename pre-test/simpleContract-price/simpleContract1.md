**project 3**

```solidity
/// Stores how many of token you could get for 1k of peg
struct TokenPrice {
    uint256 blockLastUpdated;
    uint256 tokenPer1k;
    address[] liquidationPairs;
    address[] inverseLiquidationPairs;
    address[] liquidationTokens;
    address[] inverseLiquidationTokens;
}

abstract contract PriceAware is Ownable, RoleAware {
    address public immutable peg;
    mapping(address => TokenPrice) public tokenPrices;
    /// update window in blocks
    uint16 public priceUpdateWindow = 8;
    uint256 public UPDATE_RATE_PERMIL = 80;
    uint256 public UPDATE_MAX_PEG_AMOUNT = 50_000;
    uint256 public UPDATE_MIN_PEG_AMOUNT = 1_000;

    /// Get current price of token in peg
    function getCurrentPriceInPeg(
        address token,
        uint256 inAmount,
        bool forceCurBlock
    ) public returns (uint256) {
        TokenPrice storage tokenPrice = tokenPrices[token];
        if (forceCurBlock) {
            if (
                block.number - tokenPrice.blockLastUpdated > priceUpdateWindow
            ) {
                // update the currently cached price
                return getPriceFromAMM(token, inAmount);
            } else {
                // just get the current price from AMM
                return viewCurrentPriceInPeg(token, inAmount);
            }
        } else if (tokenPrice.tokenPer1k == 0) {
            // do the best we can if it's at zero
            return getPriceFromAMM(token, inAmount);
        }
        if (block.number - tokenPrice.blockLastUpdated > priceUpdateWindow) {
            // update the price somewhat
            getPriceFromAMM(token, inAmount);
        }
        return (inAmount * 1000 ether) / tokenPrice.tokenPer1k;
    }

    /// Get view of current price of token in peg
    function viewCurrentPriceInPeg(address token, uint256 inAmount)
        public
        view
        returns (uint256)
    {
        if (token == peg) {
            return inAmount;
        } else {
            TokenPrice storage tokenPrice = tokenPrices[token];
            uint256[] memory pathAmounts =
                UniswapStyleLib.getAmountsOut(
                    inAmount,
                    tokenPrice.liquidationPairs,
                    tokenPrice.liquidationTokens
                );
            uint256 outAmount = pathAmounts[pathAmounts.length - 1];
            return outAmount;
        }
    }

    /// @dev retrieves the price from the AMM
    function getPriceFromAMM(address token, uint256 inAmount)
        internal
        virtual
        returns (uint256)
    {
        if (token == peg) {
            return inAmount;
        } else {
            TokenPrice storage tokenPrice = tokenPrices[token];
            uint256[] memory pathAmounts =
                UniswapStyleLib.getAmountsOut(
                    inAmount,
                    tokenPrice.liquidationPairs,
                    tokenPrice.liquidationTokens
                );
            uint256 outAmount = pathAmounts[pathAmounts.length - 1];
            if (
                outAmount > UPDATE_MIN_PEG_AMOUNT &&
                outAmount < UPDATE_MAX_PEG_AMOUNT
            ) {
                setPriceVal(tokenPrice, inAmount, outAmount);
            }
            return outAmount;
        }
    }
}
```



## [[H-03] Price feed can be manipulated](https://github.com/code-423n4/2021-04-marginswap-findings/issues/21)

Anyone can trigger an update to the price feed by calling `PriceAware.getCurrentPriceInPeg(token, inAmount, forceCurBlock=true)`.
If the update window has passed, the price will be computed by simulating a Uniswap-like trade with the amounts.
This simulation uses the reserves of the Uniswap pairs which can be changed drastically using flash loans to yield almost arbitrary output amounts, and thus prices. Wrong prices break the core functionality of the contracts such as borrowing on margin, liquidations, etc.

Recommend against using the Uniswap spot price as the real price. Uniswap itself warns against this and instead recommends implementing a [TWAP price oracle](https://uniswap.org/docs/v2/smart-contract-integration/building-an-oracle/) using the `price*CumulativeLast` variables.

