#!/opt/homebrew/bin/python3.11
import code
import boa

boa.set_network_env("http://46.4.15.110:8545")

from eth_account import Account
boa.env.add_account(Account.from_key("22fef8f070aa1e973d6303c630d553840ed38579382a2b99822db4df84ab253a"))

deployer = "0x09A4A66ffA7511c618007a1261d77fBbb617C28C"
owner = deployer
print("owner", owner)
print("balance", boa.env.get_balance(owner))

print("gas price", boa.env.get_gas_price())

OFFPEG_FEE_MULTIPLIER = 20000000000
zero_address =   "0x0000000000000000000000000000000000000000"
Usdc_arb = "0x0327f0660525b15Cdb8f1f5FBF0dD7Cd5Ba182aD"
usdc_sol = "0x8344d6f84d26f998fa070BbEA6D2E15E359e2641"
usdc_base = "0x96152E6180E085FA57c7708e18AF8F05e37B479D"
usdc_avax = "0xa52Ad01A1d62b408fFe06C2467439251da61E4a9"

erc20_partial = boa.load_partial("/Users/pwu/UnifiedStable/titanoboa/examples/ERC20.vy")
arb = erc20_partial.at(usdc_arb)
sol = erc20_partial.at(usdc_sol)
base = erc20_partial.at(usdc_base)
avax = erc20_partial.at(usdc_avax)
print(arb.symbol(), arb.balanceOf(owner))
print(sol.symbol(), sol.balanceOf(owner))
print(base.symbol(), base.balanceOf(owner))
print(avax.symbol(), avax.balanceOf(owner))
coins = [usdc_arb, usdc_sol, usdc_base, usdc_avax]


factory_addr = "0x4dA267b2F80c74D0FdBcF06f4F65730bB003223E"
factory = boa.load_partial("contracts/main/CurveStableSwapFactoryNG.vy").at(factory_addr)
print("factory admin", factory.admin())


# amm_deployer = boa.load_partial("contracts/main/CurveStableSwapNG.vy")
# amm_implementation = amm_deployer.deploy_as_blueprint()
# print("amm_deployer address", amm_implementation.address)

amm_impl_addr = "0x1eD4644Bd2D0e1BBd89d100ba96B1dA48Bf1048f"

math_deployer = boa.load_partial("contracts/main/CurveStableSwapNGMath.vy")
# math_implementation = math_deployer.deploy_as_blueprint()

math_impl_addr = "0xa216F1520c684c0F2153238C6d4614A489bb8EE2"

# print("amm_deployer address", amm_implementation.address)
# with boa.env.prank(owner):
#     factory.set_pool_implementations(0, amm_implementation.address)
#     factory.set_math_implementation(math_implementation.address)
    
    
# print("factory deployed", factory.address, "owner", factory.admin)
# print("deploying plain pool")

# pool_size = 4
# # def deploy_plain_pool(
# #     _name: String[32],
# #     _symbol: String[10],
# #     _coins: DynArray[address, MAX_COINS],
# #     _A: uint256,
# #     _fee: uint256,
# #     _offpeg_fee_multiplier: uint256,
# #     _ma_exp_time: uint256,
# #     _implementation_idx: uint256,
# #     _asset_types: DynArray[uint8, MAX_COINS],
# #     _method_ids: DynArray[bytes4, MAX_COINS],
# #     _oracles: DynArray[address, MAX_COINS],
# # ) -> address:
# pool = factory.deploy_plain_pool(
#     "USDC 4POOL",
#     "USDC.4", 
#     coins, 
#     400, # A
#     20000000, # fee: 0.2%
#     OFFPEG_FEE_MULTIPLIER,
#     866, # ma_exp_time, ~10min
#     0, # implementation idx
#     [0]*pool_size, 
#     [bytes(b"")] * pool_size,
#     [zero_address] * pool_size,
#     )

# print("USDC 4POOL deployed at", pool)

# print("usdc a owner balance", usdc_a.balanceOf(owner))
# print("usdc b owner balance", usdc_b.balanceOf(owner))
# print("usdc c owner balance", usdc_c.balanceOf(owner))
# print("usdc d owner balance", usdc_d.balanceOf(owner))

# print("approving pool to spend usdcs")
# with boa.env.prank(owner): 
#     usdc_a.approve(pool, 1000000000000000000)
#     usdc_b.approve(pool, 1000000000000000000)
#     usdc_c.approve(pool, 1000000000000000000)
#     usdc_d.approve(pool, 1000000000000000000)

# print("adding liquidity... 100 USDC.a/b/c/d")


# # trying to add liquidity
# swap = amm_deployer.at(pool)
# amounts = [100000000] * pool_size
# with boa.env.prank(owner):
#     lp_amount = swap.add_liquidity(amounts, 0)
# print("adding liduiqity success?, lp tokens", lp_amount)
# print("check balance of owner in pool token", swap.balanceOf(owner))

# print("now removing/redeeming USDC.B")
# with boa.env.prank(owner):
#     dy = swap.remove_liquidity_one_coin(10000000000000000000, 1, 0)
# print("USDC.B dy received", dy)
# print("pool token balance", swap.balanceOf(owner))
# # code.interact(local=locals())

# dx = 50000000
# print("swap USDC.A for USDC.C; dx", dx)
# with boa.env.prank(owner):
#     dy = swap.exchange(0, 2, dx, 0)
# print("dy (USDC.C):", dy)
# print("confirm USDC.C balance", usdc_c.balanceOf(owner))
