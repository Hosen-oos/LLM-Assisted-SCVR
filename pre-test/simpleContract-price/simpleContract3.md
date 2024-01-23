**project 20-6**

```solidity
contract SynthVault {
    address public BASE;
    address public DEPLOYER;

    uint256 public minimumDepositTime;  // Withdrawal & Harvest lockout period; intended to be 1 hour
    uint256 public totalWeight;         // Total weight of the whole SynthVault
    uint256 public erasToEarn;          // Amount of eras that make up the targeted RESERVE depletion; regulates incentives
    uint256 public vaultClaim;          // The SynthVaults's portion of rewards; intended to be ~10% initially
    address [] public stakedSynthAssets; // Array of all synth assets that have ever been staked in (scope: vault)
    uint private lastMonth;             // Timestamp of the start of current metric period (For UI)
    uint public genesis;                // Timestamp from when the synth was first deployed (For UI)

    uint256 public map30DVaultRevenue; // Tally of revenue during current incomplete metric period (for UI)
    uint256 public mapPast30DVaultRevenue; // Tally of revenue from last full metric period (for UI)
    uint256 [] public revenueArray; // Array of the last two metric periods (For UI)

    constructor(address _base) {
        BASE = _base;
        DEPLOYER = msg.sender;
        erasToEarn = 30;
        minimumDepositTime = 3600; // 1 hour
        vaultClaim = 1000;
        genesis = block.timestamp;
        lastMonth = 0;
    }

    mapping(address => mapping(address => uint256)) private mapMemberSynth_weight;
    mapping(address => uint256) private mapMemberTotal_weight;
    mapping(address => mapping(address => uint256)) private mapMemberSynth_deposit;
    mapping(address => mapping(address => uint256)) private mapMemberSynth_lastTime;
    mapping(address => uint256) private mapMember_depositTime;
    mapping(address => uint256) public lastBlock;
    mapping(address => bool) private isStakedSynth;
    mapping(address => mapping(address => bool)) private isSynthMember;

    //====================================== DEPOSIT ========================================//

    // User deposits Synths in the SynthVault
    function deposit(address synth, uint256 amount) external {
        depositForMember(synth, msg.sender, amount);
    }

    // Contract deposits Synths in the SynthVault for user
    function depositForMember(address synth, address member, uint256 amount) public {
        require(iSYNTHFACTORY(_DAO().SYNTHFACTORY()).isSynth(synth), "!synth"); // Must be a valid synth
        require(iBEP20(synth).transferFrom(msg.sender, address(this), amount)); // Must successfuly transfer in
        _deposit(synth, member, amount); // Assess and record the deposit
    }

    // Check and record the deposit
    function _deposit(address _synth, address _member, uint256 _amount) internal {
        if(!isStakedSynth[_synth]){
            isStakedSynth[_synth] = true; // Record as a staked synth
            stakedSynthAssets.push(_synth); // Add to staked synth array
        }
        mapMemberSynth_lastTime[_member][_synth] = block.timestamp + minimumDepositTime; // Record deposit time (scope: member -> synth)
        mapMember_depositTime[_member] = block.timestamp + minimumDepositTime; // Record deposit time (scope: member)
        mapMemberSynth_deposit[_member][_synth] += _amount; // Record balance for member
        uint256 _weight = iUTILS(_DAO().UTILS()).calcSpotValueInBase(iSYNTH(_synth).LayerONE(), _amount); // Get the SPARTA weight of the deposit
        mapMemberSynth_weight[_member][_synth] += _weight; // Add the weight to the user (scope: member -> synth)
        mapMemberTotal_weight[_member] += _weight; // Add to the user's total weight (scope: member)
        totalWeight += _weight; // Add to the total weight (scope: vault)
        isSynthMember[_member][_synth] = true; // Record user as a member
        emit MemberDeposits(_synth, _member, _amount, _weight, totalWeight);
    }

    // Calculate the user's current total claimable incentive
    function calcReward(address synth, address member) public view returns (uint256) {
        uint256 _weight = mapMemberSynth_weight[member][synth]; // Get user's weight (scope: member -> synth)
        uint256 _reserve = reserveBASE() / erasToEarn; // Aim to deplete reserve over a number of days
        uint256 _vaultReward = (_reserve * vaultClaim) / 10000; // Get the SynthVault's share of that
        return iUTILS(_DAO().UTILS()).calcShare(_weight, totalWeight, _vaultReward); // Get member's share of that
    }
    //================================ Helper Functions ===============================//

    function reserveBASE() public view returns (uint256) {
        return iBEP20(BASE).balanceOf(_DAO().RESERVE());
    }

    function getMemberDeposit(address synth, address member) external view returns (uint256){
        return mapMemberSynth_deposit[member][synth];
    }

    function getMemberWeight(address member) external view returns (uint256) {
        return mapMemberTotal_weight[member];
    }

    function getStakeSynthLength() external view returns (uint256) {
        return stakedSynthAssets.length;
    }

    function getMemberLastTime(address member) external view returns (uint256) {
        return mapMember_depositTime[member];
    }

    function getMemberLastSynthTime(address synth, address member) external view returns (uint256){
        return mapMemberSynth_lastTime[member][synth];
    }

    function getMemberSynthWeight(address synth, address member) external view returns (uint256) {
        return mapMemberSynth_weight[member][synth];
    }
}
```



```solidity
contract Utils {
    address public BASE;
    uint public one = 10**18;

    constructor (address _base) {
        BASE = _base;
    }

    struct PoolDataStruct {
        address tokenAddress;
        address poolAddress;
        uint genesis;
        uint baseAmount;
        uint tokenAmount;
        uint fees;
        uint volume;
        uint txCount;
        uint poolUnits;
    }

    //================================== CORE-MATH ==================================//
    // Calc share | share = amount * part / total
    function calcShare(uint256 part, uint256 total, uint256 amount) public pure returns (uint256 share) {
        if (part > total) {
            part = total; // Part cant be greater than the total
        }
        if (total > 0) {
            share = (amount * part) / total;
        }
    }

    //==================================== PRICING ====================================//

    function calcSpotValueInBase(address token, uint amount) external view returns (uint value){
        address pool = getPool(token);
        return calcSpotValueInBaseWithPool(pool, amount);
    }
    function calcSpotValueInBaseWithPool(address pool, uint amount) public view returns (uint value){
        uint _baseAmount = iPOOL(pool).baseAmount();
        uint _tokenAmount = iPOOL(pool).tokenAmount();
        return (amount*(_baseAmount))/(_tokenAmount);
    }
}
```



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