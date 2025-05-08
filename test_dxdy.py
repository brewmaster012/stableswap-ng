import boa

wallet = boa.env.eoa

math_deployer = boa.load_partial("contracts/main/CurveStableSwapNGMath.vy")
coin0 = boa.load("contracts/mocks/ERC20.vy", "coin0", "coin0", 6)
coin1 = boa.load("contracts/mocks/ERC20.vy", "coin1", "coin1", 6)
coin2 = boa.load("contracts/mocks/ERC20.vy", "coin2", "coin2", 6)
coin3 = boa.load("contracts/mocks/ERC20.vy", "coin3", "coin3", 6)
coin0._mint_for_testing(wallet, 100*10**6)
coin1._mint_for_testing(wallet, 100*10**6)
coin2._mint_for_testing(wallet, 100*10**6)
coin3._mint_for_testing(wallet, 100*10**6)

A = 400
fee = 20000000
OFFPEG_FEE_MULTIPLIER = 20000000000
zero_address =   "0x0000000000000000000000000000000000000000"
pool_size = 4

factory = boa.load("contracts/main/CurveStableSwapFactoryNG.vy", wallet, wallet)
print("admin", factory.admin())

amm_deployer = boa.load_partial("contracts/main/CurveStableSwapNG.vy")
amm_implementation = amm_deployer.deploy_as_blueprint()
math = boa.load("contracts/main/CurveStableSwapNGMath.vy")
# math_implementation = math_deployer.deploy_as_blueprint()
factory.set_pool_implementations(0, amm_implementation.address)
factory.set_math_implementation(math.address)
# import code; code.interact(local=globals())

print("Pool implementation at index 0:", factory.pool_implementations(0))
print("Math implementation:", factory.math_implementation())

# factory = boa.load("contracts/main/CurveStableSwapFactoryNG.vy", wallet, wallet)
pool = factory.deploy_plain_pool(
    "USDC.4",
    "USDC.4",
    [c.address for c in [coin0, coin1, coin2, coin3]],
    A,
    fee,
    OFFPEG_FEE_MULTIPLIER,
    866,
    0,
    [0]*pool_size,
    [bytes(b"")] * pool_size,
    [zero_address] * pool_size,
)
# print(pool.symbol)
