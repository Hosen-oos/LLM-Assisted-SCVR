# toyPriceOracle2

```solidity
contract LendingContract { 
	IERC20 public WETH;
	IERC20 public USDC;
	IUniswapV2Pair public pair; // USDC - WETH
	// debt --> USDC, collateral --> WETH
	mapping(address => uint) public debt; 
	mapping(address => uint) public collateral;
	function liquidate(address user) external {
		uint dAmount = debt[user];
		uint cAmount = collateral[user];
		require(getPrice() * cAmount * 80 / 100 < dAmount,
			"the given user’s fund cannot be liquidated");
		address _this = address(this);
		USDC.transferFrom(msg.sender, _this, dAmount);
		WETH.transferFrom(_this, msg.sender, cAmount);
	}
	function getPrice() view returns (uint) {
		return (USDC.balanceOf(address(pair)) /
 				WETH.balanceOf(address(pair)))
 	}
}
```

Vulnerability:

The vulnerability lies in `function liquidate` (line 9) which forces to close a given user’s *ill position*, i.e., the user’s debts exceed 80% of her collateral. The price oracle is involved when calculating the real-world value of the collateral, i.e., WETH, through `function getPrice()` (defifined in lines 18-21). The function does not use the Uniswap API. Instead, it directly queries the instance balances of USDC and WETH in Uniswap and uses their ratio as the price.

To exploit, the adversary drastically decreases the price of a collateral, forcefully making a victim’s position liquidable. She then liquidates a valuable collateral with a much smaller amount of fund.
