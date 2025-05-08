#!/opt/homebrew/bin/python3.11
import code
import boa



# boa.set_network_env("http://46.4.15.110:8545")

deployer = "0x33EaD83db0D0c682B05ead61E8d8f481Bb1B4933"
owner = deployer

OFFPEG_FEE_MULTIPLIER = 20000000000
zero_address =   "0x0000000000000000000000000000000000000000"
usdcs = []
coins = []
with boa.env.prank(owner):
    usdc_a = boa.load("/Users/pwu/UnifiedStable/titanoboa/examples/ERC20.vy", "USDC.A", "USDC.A", 6, 1000000000)
    usdc_b = boa.load("/Users/pwu/UnifiedStable/titanoboa/examples/ERC20.vy", "USDC.B", "USDC.B", 6, 1000000000)
    usdc_c = boa.load("/Users/pwu/UnifiedStable/titanoboa/examples/ERC20.vy", "USDC.C", "USDC.C", 6, 1000000000)
    usdc_d = boa.load("/Users/pwu/UnifiedStable/titanoboa/examples/ERC20.vy", "USDC.D", "USDC.D", 6, 1000000000)
    usdcs = [usdc_a, usdc_b, usdc_c, usdc_d]
    coins = [u.address for u in usdcs]
        

factory = boa.load("contracts/main/CurveStableSwapFactoryNG.vy", deployer, deployer)

amm_deployer = boa.load_partial("contracts/main/CurveStableSwapNG.vy")
amm_implementation = amm_deployer.deploy_as_blueprint()
math_deployer = boa.load_partial("contracts/main/CurveStableSwapNGMath.vy")
math_implementation = math_deployer.deploy_as_blueprint()

print("amm_deployer address", amm_implementation.address)
with boa.env.prank(owner):
    factory.set_pool_implementations(0, amm_implementation.address)
    factory.set_math_implementation(math_implementation.address)
    
    
print("factory deployed", factory.address, "owner", factory.admin)
print("deploying plain pool")

pool_size = 4
# def deploy_plain_pool(
#     _name: String[32],
#     _symbol: String[10],
#     _coins: DynArray[address, MAX_COINS],
#     _A: uint256,
#     _fee: uint256,
#     _offpeg_fee_multiplier: uint256,
#     _ma_exp_time: uint256,
#     _implementation_idx: uint256,
#     _asset_types: DynArray[uint8, MAX_COINS],
#     _method_ids: DynArray[bytes4, MAX_COINS],
#     _oracles: DynArray[address, MAX_COINS],
# ) -> address:
pool = factory.deploy_plain_pool(
    "USDC 4POOL",
    "USDC.4", 
    coins, 
    400, # A
    20000000, # fee: 0.2%
    OFFPEG_FEE_MULTIPLIER,
    866, # ma_exp_time, ~10min
    0, # implementation idx
    [0]*pool_size, 
    [bytes(b"")] * pool_size,
    [zero_address] * pool_size,
    )

print("USDC 4POOL deployed at", pool)

print("usdc a owner balance", usdc_a.balanceOf(owner))
print("usdc b owner balance", usdc_b.balanceOf(owner))
print("usdc c owner balance", usdc_c.balanceOf(owner))
print("usdc d owner balance", usdc_d.balanceOf(owner))

print("approving pool to spend usdcs")
with boa.env.prank(owner): 
    usdc_a.approve(pool, 1000000000000000000)
    usdc_b.approve(pool, 1000000000000000000)
    usdc_c.approve(pool, 1000000000000000000)
    usdc_d.approve(pool, 1000000000000000000)

print("adding liquidity... 100 USDC.a/b/c/d")


# trying to add liquidity
swap = amm_deployer.at(pool)
amounts = [100000000] * pool_size
with boa.env.prank(owner):
    lp_amount = swap.add_liquidity(amounts, 0)
print("adding liduiqity success?, lp tokens", lp_amount)
print("check balance of owner in pool token", swap.balanceOf(owner))

print("now removing/redeeming USDC.B")
with boa.env.prank(owner):
    dy = swap.remove_liquidity_one_coin(10000000000000000000, 1, 0)
print("USDC.B dy received", dy)
print("pool token balance", swap.balanceOf(owner))
# code.interact(local=locals())

dx = 50000000
print("swap USDC.A for USDC.C; dx", dx)
with boa.env.prank(owner):
    dy = swap.exchange(0, 2, dx, 0)
print("dy (USDC.C):", dy)
print("confirm USDC.C balance", usdc_c.balanceOf(owner))
