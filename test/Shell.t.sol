// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.13;

import {Test, console} from "forge-std/Test.sol";
import {Shell} from "../src/Shell.sol";
import {IUniswapV2Router02} from "../src/UniswapInterface.sol";

contract ShellTest is Test {
    Shell public shell;
    address constant UniswapV2Router02_address = 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D;
    address constant WETH_address = 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2 ;

    function setUp() public {
        shell = new Shell();
    }

    function test_owner() public view {
        assertEq(shell.owner(), address(this));
    }

    function test_buy_success() public {
        vm.prank(shell.owner());
        shell.transfer(address(123), 1);
        vm.prank(address(123));
        vm.roll(6); //skipping the blacklisted blocks 1 , 2 , 3 , 4 , 5 
        console.log("blocknumber is " , block.number);
        shell.transfer(shell.owner(), 1);
    }

    function test_buy() public {
        vm.prank(shell.owner());
        shell.mint(address(123), 1);
        vm.roll(1); // not skipping the blacklisted blocks 1 , 2 , 3 , 4 , 5 
        vm.startPrank(address(123)); //used startPrank instead of prank because vm.prank only calls shell.owner() and not shell.transfer.
        shell.transfer(shell.owner(), 5555555);
        vm.stopPrank();
    }
}



