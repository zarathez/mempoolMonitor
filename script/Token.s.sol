// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.13;

import {Script, console} from "forge-std/Script.sol";
import {Shell} from "../src/Shell.sol";

contract Token {

}

contract TokenScript is Script {
    function setUp() public {}

    function run() public {
        uint privateKey = vm.envUint("OWNER_PRIAVTE_KEY");
        address account = vm.addr(privateKey);

        console.log("account", account);

    
        vm.startBroadcast(privateKey);
        Shell shell = new Shell();
        vm.stopBroadcast();
    }
}
