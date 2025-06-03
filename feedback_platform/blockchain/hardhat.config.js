require("dotenv").config();
require("@nomicfoundation/hardhat-toolbox");

module.exports = {
  solidity: {
    version: "0.8.28",
    settings: {
      optimizer: {
        enabled: true,
        runs: 200
      }
    }
  },
  networks: {
    sepolia: {
      url: process.env.WEB3_PROVIDER_URL || "",
      accounts: [process.env.PRIVATE_KEY || ""],
      chainId: parseInt(process.env.CHAIN_ID) || 11155111,
    },
  },
};