const hre = require("hardhat");
async function main() {
  const FeedbackToken = await hre.ethers.getContractFactory("FeedbackToken");
  const feedbackToken = await FeedbackToken.deploy();
  await feedbackToken.waitForDeployment();
  console.log("✅ Contrato deployado em:", feedbackToken.target);
  console.log("🔗 Explorer: https://sepolia.etherscan.io/address/"  + feedbackToken.target);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("❌ Erro no deploy:", error);
    process.exit(1);
  });