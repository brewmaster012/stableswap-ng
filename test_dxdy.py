import boa

def print_balances(pool):
    return [b/10**6 for b in pool.get_balances()]

def virtual_price(pool):
    usdc_amount = sum([ bal/10**6  for bal in  pool.get_balances()])
    return usdc_amount / (pool.totalSupply()/(10**pool.decimals()))

wallet = boa.env.eoa
INITIAL_AMOUNT = 100

math_deployer = boa.load_partial("contracts/main/CurveStableSwapNGMath.vy")
coin0 = boa.load("contracts/mocks/ERC20.vy", "coin0", "coin0", 6)
coin1 = boa.load("contracts/mocks/ERC20.vy", "coin1", "coin1", 6)
coin2 = boa.load("contracts/mocks/ERC20.vy", "coin2", "coin2", 6)
coin3 = boa.load("contracts/mocks/ERC20.vy", "coin3", "coin3", 6)
coin0._mint_for_testing(wallet, INITIAL_AMOUNT*10**6)
coin1._mint_for_testing(wallet, INITIAL_AMOUNT*10**6)
coin2._mint_for_testing(wallet, INITIAL_AMOUNT*10**6)
coin3._mint_for_testing(wallet, INITIAL_AMOUNT*10**6)

A = 400
fee = 0
# fee = 0
OFFPEG_FEE_MULTIPLIER = 20000000000
zero_address =   "0x0000000000000000000000000000000000000000"
pool_size = 4
fee_receiver = boa.env.generate_address()

factory = boa.load("contracts/main/CurveStableSwapFactoryNG.vy", fee_receiver, wallet)
print("fee_receiver", factory.fee_receiver())
print("admin", factory.admin())
print("fee rate", fee)
print("A", A)

amm_deployer = boa.load_partial("contracts/main/CurveStableSwapNG.vy")
amm_implementation = amm_deployer.deploy_as_blueprint()
math = boa.load("contracts/main/CurveStableSwapNGMath.vy")
factory.set_pool_implementations(0, amm_implementation.address)
factory.set_math_implementation(math.address)
# print("Pool implementation at index 0:", factory.pool_implementations(0))
# print("Math implementation:", factory.math_implementation())

# factory = boa.load("contracts/main/CurveStableSwapFactoryNG.vy", wallet, wallet)
pool_addr = factory.deploy_plain_pool(
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

for c in [coin0, coin1, coin2, coin3]:
    c.approve(pool_addr, 1_000_000 * 10**6)

pool = boa.load_partial("contracts/main/CurveStableSwapNG.vy").at(pool_addr)
pool.add_liquidity(
    [INITIAL_AMOUNT * 10**6] * pool_size,
    0,
)
print("deployer: initial deposit liquidity: 100 coin0/coin1/coin2/coin3")
print("  deployer LP token", pool.balanceOf(wallet))
alice = boa.env.generate_address()
# print("alice", alice)

coin0._mint_for_testing(alice, 1000*10**6)
coin0.approve(pool.address, 1000*10**6, sender=alice)

print("  before xchg pool",print_balances(pool))

dx = 98*10**6
dy = pool.exchange(
    0, 2,
    dx, 0,
    sender=alice,
)
print(f"alice exchanged dx={dx/10**6} coin0 for dy={dy/10**6} coin2")
print(f"  at relative loss of (dx-dy)/dx={(dx-dy)/dx*100:.2f}%" )
print(f"  causing severe pool imbalance")
balances1 = pool.get_balances()
print("  after xchg pool balance", print_balances(pool))
print("  LP token virtual price", virtual_price(pool))

coin1._mint_for_testing(alice, 1000*10**6)
coin1.approve(pool.address, 1000*10**6, sender=alice)

deposit_amt = 20*10**6
lp_mint_amt = pool.add_liquidity(
    [0, deposit_amt, 0, 0],
    0,
    sender = alice,
)
print(f"alice deposit {deposit_amt/10**6} coin1, got LP token", lp_mint_amt)
print("  LP nominal loss",(deposit_amt/10**6-lp_mint_amt/10**18)*1.0/(deposit_amt/10**6))
print("  LP token virtual price", virtual_price(pool))

# restoring pegging if we rebalance the pool?
coin2.approve(pool.address, dy, sender=alice)
dx = pool.exchange(
    2, 0,
    dy, 0,
    sender=alice,
)
print(f"alice rebalanced the pool by exchanging dy={dy/10**6:.2f} coin2 for dx={dx/10**6:.2f} coin0")
print(f"  at relative profit {(dx-dy)/dx*100:.2f}%")
print(f"  after re-balance the pool:", print_balances(pool))
print(f"  LP token virtual price", virtual_price(pool))

deposit_amt = 20*10**6
lp_mint_amt = pool.add_liquidity(
    [0, deposit_amt, 0, 0],
    0,
    sender = alice,
)
print(f"alice deposit {deposit_amt/10**6} coin1, got LP token", lp_mint_amt)
print("  LP nominal loss",(deposit_amt/10**6-lp_mint_amt/10**18)*1.0/(deposit_amt/10**6))
print("  LP token virtual price", virtual_price(pool))
print("  pool balances", print_balances(pool))
