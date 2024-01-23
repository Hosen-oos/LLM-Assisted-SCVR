**project 20-5**

```solidity
contract Synth is iBEP20 {
    address public BASE;
    address public LayerONE; // Underlying relevant layer1 token
    uint public genesis;
    address public DEPLOYER;

    string _name; string _symbol;
    uint8 public override decimals; uint256 public override totalSupply;

    mapping(address => uint) private _balances;
    mapping(address => mapping(address => uint)) private _allowances;
    mapping(address => uint) public mapSynth_LPBalance;
    mapping(address => uint) public mapSynth_LPDebt;
   
    function _DAO() internal view returns(iDAO) {
        return iBASE(BASE).DAO();
    }    
    // Restrict access
    modifier onlyDAO() {
        require(msg.sender == DEPLOYER, "!DAO");
        _;
    }
    // Restrict access
    modifier onlyPool() {
        require(iPOOLFACTORY(_DAO().POOLFACTORY()).isCuratedPool(msg.sender) == true, "!curated");
        _;
    }
    
    constructor (address _base, address _token) {
        BASE = _base;
        LayerONE = _token;
        string memory synthName = "-SpartanProtocolSynthetic";
        string memory synthSymbol = "-SPS";
        _name = string(abi.encodePacked(iBEP20(_token).name(), synthName));
        _symbol = string(abi.encodePacked(iBEP20(_token).symbol(), synthSymbol));
        decimals = iBEP20(_token).decimals();
        DEPLOYER = msg.sender;
        genesis = block.timestamp;
    }
    
    //==================================== SYNTH FUNCTIONS =================================//

    // Handle received LP tokens and mint Synths
    function mintSynth(address member, uint amount) external onlyPool returns (uint syntheticAmount){
        uint lpUnits = _getAddedLPAmount(msg.sender); // Get the received LP units
        mapSynth_LPDebt[msg.sender] += amount; // Increase debt by synth amount
        mapSynth_LPBalance[msg.sender] += lpUnits; // Increase lp balance by LPs received
        _mint(member, amount); // Mint the synths & tsf to user
        return amount;
    }
    
    // Handle received Synths and burn the LPs and Synths
    function burnSynth() external returns (bool){
        uint _syntheticAmount = balanceOf(address(this)); // Get the received synth units
        uint _amountUnits = (_syntheticAmount * mapSynth_LPBalance[msg.sender]) / mapSynth_LPDebt[msg.sender]; // share = amount * part/total
        mapSynth_LPBalance[msg.sender] -= _amountUnits; // Reduce lp balance
        mapSynth_LPDebt[msg.sender] -= _syntheticAmount; // Reduce debt by synths being burnt
        if(_amountUnits > 0){
            _burn(address(this), _syntheticAmount); // Burn the synths
            Pool(msg.sender).burn(_amountUnits); // Burn the LP tokens
        }
        return true;
    }

    // Burn LPs to if their value outweights the synths supply value (Ensures incentives are funnelled to existing LPers)
    function realise(address pool) external {
        uint baseValueLP = iUTILS(_DAO().UTILS()).calcLiquidityHoldings(mapSynth_LPBalance[pool], BASE, pool); // Get the SPARTA value of the LP tokens
        uint baseValueSynth = iUTILS(_DAO().UTILS()).calcActualSynthUnits(mapSynth_LPDebt[pool], address(this)); // Get the SPARTA value of the synths
        if(baseValueLP > baseValueSynth){
            uint premium = baseValueLP - baseValueSynth; // Get the premium between the two values
            if(premium > 10**18){
                uint premiumLP = iUTILS(_DAO().UTILS()).calcLiquidityUnitsAsym(premium, pool); // Get the LP value of the premium
                mapSynth_LPBalance[pool] -= premiumLP; // Reduce the LP balance
                Pool(pool).burn(premiumLP); // Burn the premium of the LP tokens
            }
        }
    }

    // Check the received token amount
    function _handleTransferIn(address _token, uint256 _amount) internal returns(uint256 _actual){
        if(_amount > 0) {
            uint startBal = iBEP20(_token).balanceOf(address(this)); // Get existing balance
            iBEP20(_token).transferFrom(msg.sender, address(this), _amount); // Transfer tokens in
            _actual = iBEP20(_token).balanceOf(address(this)) - startBal; // Calculate received amount
        }
        return _actual;
    }

    // Check the received LP tokens amount
    function _getAddedLPAmount(address _pool) internal view returns(uint256 _actual){
        uint _lpCollateralBalance = iBEP20(_pool).balanceOf(address(this)); // Get total balance held
        if(_lpCollateralBalance > mapSynth_LPBalance[_pool]){
            _actual = _lpCollateralBalance - mapSynth_LPBalance[_pool]; // Get received amount
        } else {
            _actual = 0;
        }
        return _actual;
    }
}

```



## [[H-05] Synth `realise` is vulnerable to flash loan attacks](https://github.com/code-423n4/2021-07-spartan-findings/issues/40)

_Submitted by jonah1005, also found by a_delamo_

Synth `realise` function calculates `baseValueLP` and `baseValueSynth` base on AMM spot price which is vulnerable to flash loan attack. `Synth`'s lp is subject to `realise` whenever the AMM ratio is different than Synth's debt ratio.

The attack does not necessarily require a flash loan. A big whale of the lp token holders could keep calling `realise` by shifting token ratio of AMM pool back and forth.

The vulnerability is located at `Synth.sol` [L187-L199](https://github.com/code-423n4/2021-07-spartan/blob/e2555aab44d9760fdd640df9095b7235b70f035e/contracts/Synth.sol#L187-L199). Where the formula [here](https://github.com/code-423n4/2021-07-spartan/blob/e2555aab44d9760fdd640df9095b7235b70f035e/contracts/Utils.sol#L114-L126) is dangerous.