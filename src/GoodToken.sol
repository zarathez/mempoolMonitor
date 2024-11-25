//SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";

contract GoodToken is ERC20 {
    constructor() ERC20("GoodToken", "GDTK") {
        _mint(msg.sender, 1000000000000000000000000000000000000000000000000);
    }
}