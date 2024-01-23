**project 78**

```solidity
///@title FlanBackstop (placeholder name)
///@author Justin Goro
/**
 * @notice Initially Flan's liquidity may be fairly low, limiting Limbo's ability to reward souls. Flan backstop accepts stablecoins in return for minting Pyroflan.
 *Under the hood a smaller quantity of Flan is minted and paired with the stablecoin in Uniswap in order to tilt the price of Flan higher while incresaing liquidity.
 * The same operation is performed with PyroFlan
 * The calling user then receives PyroFlan equal in value to the intial amount sent in but at the new price. A small premium is added.
 * The incentives facing the user: mint $X of PyroFlan with <$X of stablecoin, stake PyroFlan in Limbo for high APY, do not immediately dump because PyroFlan increases in value and because of 2% exit fee.
 * The incentives should be enough to encourage a gradual increase in pooled Flan and stablecoins, creating some minting runway for Limbo to accelerate.
 * In the future when Flan and Limbo are thriving and Flan is listed on Curve, we can create a version of this for Curve and Uniswap V3 in order to concentrate Flan liquidity and further cement stablecoin status.
 * Note: in this version, LP tokens generated are cast into the void. The argument of keeping them for fee revenue is negated by the impact on Flan. It would just be taking from Peter to give to Paul. 
 */
///@dev This contract uses Pyrotokens3. At the time of authoring, Pyrotokens3 implementation is incomplete and not fully tested but the interface (ABI) is locked.
contract FlanBackstop is Governable {
  /**
   *@param dao LimboDAO
   *@param flan Flan address
   *@param pyroFlan PyroFlan address
   */
  constructor(
    address dao,
    address flan,
    address pyroFlan
  ) Governable(dao) {
    config.pyroFlan = pyroFlan;
    config.flan = flan;
    IERC20(flan).approve(pyroFlan, 2**256 - 1);
  }

  struct ConfigVars {
    address flan;
    address pyroFlan;
    mapping(address => address) flanLPs;
    mapping(address => address) pyroFlanLPs;
    mapping(address => uint256) acceptableHighestPrice; //Highest tolerated Flan per stable
    mapping(address => uint8) decimalPlaces; //USDC and USDT have 6 decimal places because large stablecoin transfers are exactly where you'd like to find accidental bugs
  }

  ConfigVars public config;

  /**
   *@param stablecoin One of the popular stablecoins such as USDC, USDT, MIM, OUSD etc.
   *@param flanLP Uniswap V2 (or a fork such as Sushi) flan/Stablecoin LP
   *@param pyroFlanLP Uniswap V2 (or a fork such as Sushi) pyroFlan/Stablecoin LP
   *@param acceptableHighestPrice Since the prices are being read from balances, not oracles, the opportunity for price manipulation through flash loans exists. The community can put a circuit breaker in place to prevent such an exploit.
   *@param decimalPlaces USDT and USDC do not conform to common ERC20 practice. 
   */
  function setBacker(
    address stablecoin,
    address flanLP,
    address pyroFlanLP,
    uint256 acceptableHighestPrice,
    uint8 decimalPlaces
  ) external onlySuccessfulProposal {
    config.flanLPs[stablecoin] = flanLP;
    config.pyroFlanLPs[stablecoin] = pyroFlanLP;
    config.acceptableHighestPrice[stablecoin] = acceptableHighestPrice;
    config.decimalPlaces[stablecoin] = decimalPlaces;
  }

  /**
  *@notice takes in a stablecoin, mints flan and pyroFlan and pairs with stablecoin in a Uniswap Pair to generate liquidity
   *@param stablecoin Stablecoin with which to purchase
   *@param amount amount in stablecoin wei units.
   */
  function purchasePyroFlan(address stablecoin, uint256 amount) external {
    uint normalizedAmount = normalize(stablecoin, amount);
    address flanLP = config.flanLPs[stablecoin];
    address pyroFlanLP = config.pyroFlanLPs[stablecoin];
    require(flanLP != address(0) && pyroFlanLP != address(0), "BACKSTOP: configure stablecoin");

    uint256 balanceOfFlanBefore = IERC20(config.flan).balanceOf(flanLP);
    uint256 balanceOfStableBefore = IERC20(stablecoin).balanceOf(flanLP);
    uint256 priceBefore = (balanceOfFlanBefore * getMagnitude(stablecoin)) / balanceOfStableBefore;

    //Price tilt pairs and mint liquidity
    FlanLike(config.flan).mint(address(this), normalizedAmount / 2);
    IERC20(config.flan).transfer(flanLP, normalizedAmount / 4);
    IERC20(stablecoin).transferFrom(msg.sender, flanLP, amount / 2);

    UniPairLike(flanLP).mint(address(this));
    uint256 redeemRate = PyroTokenLike(config.pyroFlan).redeemRate();
    PyroTokenLike(config.pyroFlan).mint(pyroFlanLP, normalizedAmount / 4);
    redeemRate = PyroTokenLike(config.pyroFlan).redeemRate();
    redeemRate = PyroTokenLike(config.pyroFlan).redeemRate();
    IERC20(stablecoin).transferFrom(msg.sender, pyroFlanLP, amount / 2);
    UniPairLike(pyroFlanLP).mint(address(this));

    uint256 balanceOfFlan = IERC20(config.flan).balanceOf(flanLP);
    uint256 balanceOfStable = IERC20(stablecoin).balanceOf(flanLP);

    uint256 tiltedPrice = (balanceOfFlan * getMagnitude(stablecoin)) / balanceOfStable;
    require(tiltedPrice < config.acceptableHighestPrice[stablecoin], "BACKSTOP: potential price manipulation");
    uint256 growth = ((priceBefore - tiltedPrice) * 100) / priceBefore;

    uint256 flanToMint = (tiltedPrice * normalizedAmount) / (1 ether);

    //share some price tilting with the user to incentivize minting: The larger the purchase, the better the return
    uint256 premium = (flanToMint * (growth / 2)) / 100;

    FlanLike(config.flan).mint(address(this), flanToMint + premium);
    redeemRate = PyroTokenLike(config.pyroFlan).redeemRate();
    PyroTokenLike(config.pyroFlan).mint(msg.sender, flanToMint + premium);
    redeemRate = PyroTokenLike(config.pyroFlan).redeemRate();
  }

  function getMagnitude(address token) internal view returns (uint256) {
    uint256 places = config.decimalPlaces[token];
    return 10**places;
  }

  function normalize(address token, uint256 amount) internal view returns (uint256) {
    uint256 places = config.decimalPlaces[token];
    uint256 bump = 10**(18 - places);
    return amount * bump;
  }
}
```



## [[H-05] Flash loan price manipulation in `purchasePyroFlan()`](https://github.com/code-423n4/2022-01-behodler-findings/issues/231)

_Submitted by sirhashalot_

The comment on [line 54](https://github.com/code-423n4/2022-01-behodler/blob/cedb81273f6daf2ee39ec765eef5ba74f21b2c6e/contracts/FlanBackstop.sol#L54) of FlanBackstop.sol states "the opportunity for price manipulation through flash loans exists", and I agree that this is a serious risk. While the acceptableHighestPrice variable attempts to limit the maximum price change of the flan-stablecoin LP, a flashloan sandwich attack can still occur within this limit and make up for the limitation with larger volumes or multiple flashloan attacks. Flashloan price manipulation is the cause for many major hacks, including [bZx](https://bzx.network/blog/postmortem-ethdenver), [Harvest](https://rekt.news/harvest-finance-rekt/), and others.

#### Proof of Concept

[Line 83](https://github.com/code-423n4/2022-01-behodler/blob/cedb81273f6daf2ee39ec765eef5ba74f21b2c6e/contracts/FlanBackstop.sol#L83) of FlanBackstop.sol calculates the price of flan to stablecoin in the Uniswap pool based on the balances at a single point in time. Pool balances at a single point in time can be manipulated with flash loans, which can skew the numbers to the extreme. The single data point of LP balances is used to calculate [the growth variable in line 103](https://github.com/code-423n4/2022-01-behodler/blob/cedb81273f6daf2ee39ec765eef5ba74f21b2c6e/contracts/FlanBackstop.sol#L103), and the growth variable influences the quantity of pyroflan a user receives in [the premium calculation on line 108](https://github.com/code-423n4/2022-01-behodler/blob/cedb81273f6daf2ee39ec765eef5ba74f21b2c6e/contracts/FlanBackstop.sol#L108).

```solidity
uint256 priceBefore = (balanceOfFlanBefore * getMagnitude(stablecoin)) / balanceOfStableBefore;
uint256 growth = ((priceBefore - tiltedPrice) * 100) / priceBefore;
uint256 premium = (flanToMint * (growth / 2)) / 100;
```

Problems can occur when the volumes that the `purchasePyroFlan()` function sends to the Uniswap pool are large compared to the pool's liquidity volume, or if the Uniswap pool price is temporarily tilted with a flashloan (or a whale). Because this function purposefully changes the exchange rate of the LP, by transferring tokens to the LP in a 2-to-1 ratio, a large volume could caught a large price impact in the LP. The code attempts to protect against this manipulation in [line 102](https://github.com/code-423n4/2022-01-behodler/blob/cedb81273f6daf2ee39ec765eef5ba74f21b2c6e/contracts/FlanBackstop.sol#L102) with a require statement, but this can be worked around by reducing the volume per flashloan and repeating the attack multiple times. A user can manipulate the LP, especially when the LP is new with low liquidity, in order to achieve large amounts of flan and pyroflan.

#### Recommended Mitigation Steps

Use a TWAP instead of the pool price at a single point in time to increase the cost of performing a flashloan sandwich attack. See [the Uniswap v2 price oracle solution ](https://docs.uniswap.org/protocol/V2/concepts/core-concepts/oracles)documentation for more explanations on how Uniswap designed an approach to providing asset prices while reducing the change of manipulation.