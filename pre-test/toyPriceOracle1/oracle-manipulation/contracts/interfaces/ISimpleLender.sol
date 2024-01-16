//SPDX-License-Identifier: MIT
pragma solidity ^0.8.13;

interface ILender {
    function depositUSDC(uint256 amount) external;

    function getPriceUSDCETH() external view returns (uint256);

    function maxBorrowAmount() external view returns (uint256);

    function borrowETH(uint256 amount) external;
}
