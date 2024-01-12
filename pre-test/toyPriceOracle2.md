# toyPriceOracle2

1.

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface IPriceOracle {
    function getPrice(address asset) external view returns (uint256);
}

contract VulnerableContract {
    IPriceOracle public priceOracle;

    mapping(address => uint256) public userBalances;

    constructor(address _priceOracle) {
        priceOracle = IPriceOracle(_priceOracle);
    }

    function deposit(address asset) external payable {
        uint256 assetPrice = priceOracle.getPrice(asset);
        require(assetPrice > 0, "Asset price is zero");
        uint256 assetValue = msg.value / assetPrice;
        userBalances[msg.sender] += assetValue;
    }

    function withdraw(address asset, uint256 assetAmount) external {
        require(userBalances[msg.sender] >= assetAmount, "Insufficient balance");

        uint256 assetPrice = priceOracle.getPrice(asset);
        require(assetPrice > 0, "Asset price is zero");
        uint256 ethValue = assetAmount * assetPrice;
        userBalances[msg.sender] -= assetAmount;
        payable(msg.sender).transfer(ethValue);
    }

    function withdrawAll() external {
        payable(msg.sender).transfer(address(this).balance);
    }
}
```

2.

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

