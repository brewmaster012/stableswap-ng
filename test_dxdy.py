import boa
import sys
import pdb

def info(type, value, tb):
    pdb.post_mortem(tb)

sys.excepthook = info

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

A = 1000
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
for coin in [coin0, coin1, coin2, coin3]:
    coin._mint_for_testing(alice, 1000*10**6)
    coin.approve(pool.address, 1000*10**6, sender=alice)

deposit_amt = 20*10**6
lp_mint_amt = pool.add_liquidity(
    [0, deposit_amt, 0, 0],
    0,
    sender = alice,
)
print(f"alice deposit (abundant) {deposit_amt/10**6} coin1, got LP token", lp_mint_amt)
print(f"  LP nominal loss {(deposit_amt/10**6-lp_mint_amt/10**18)*1.0/(deposit_amt/10**6)*100:.2f}%")
print(f"  LP token virtual price", virtual_price(pool))

deposit_amt = 20*10**6
lp_mint_amt = pool.add_liquidity(
    [0, 0, deposit_amt, 0],
    0,
    sender = alice,
)
print(f"alice deposit (scarce) {deposit_amt/10**6} coin2, got LP token", lp_mint_amt)
print(f"  LP nominal gain {-(deposit_amt/10**6-lp_mint_amt/10**18)*1.0/(deposit_amt/10**6)*100:.2f}%")
print(f"  LP token virtual price", virtual_price(pool))

# restoring pegging if we rebalance the pool?
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
print(f"  LP nominal loss {(deposit_amt/10**6-lp_mint_amt/10**18)*1.0/(deposit_amt/10**6)*100:.2f}%")
print("  LP token virtual price", virtual_price(pool))
print("  pool balances", print_balances(pool))

vps = [] # virtual price history
coins = [coin0, coin1, coin2, coin3]
users = []
ratios = []

def monte_carlo_sim(num_txs, loss_limit=0.1):
    num_add_liq = 0
    num_remove_liq = 0
    num_swap = 0
    import random

    for i in range(100):
        users.append( boa.env.generate_address())
    for user in users:
        for coin in coins:
            coin._mint_for_testing(user, 1000000000*10**6)
            coin.approve(pool.address, 1000000000*10**6, sender=user)
    for tx in range(num_txs):
        if tx % 100 == 0:
            bals = print_balances(pool)
            print(f"tx progress {tx}/{num_txs}")
            print(f"  pool balance:", bals)
            print(f"  max_bal/min_bal: {max(bals)*1.0/min(bals):e}", )
            print(f"  virtual price", virtual_price(pool))
        user = random.choice(users)
        # pick one of the 3 actions (add liq, swap, withdraw liq)
        op = random.randint(0, 2)
        if op == 0: # add one liq
            # pick a coin
            coin_idx = random.randint(0, len(coins)-1)
            coin = coins[coin_idx]
            amt = random.randint(1, 1000)
            deposit_amt = amt * 10**6
            amounts =  [0] * len(coins)
            amounts[coin_idx] = deposit_amt
            try:
                lp_mint_amt = pool.add_liquidity(
                    amounts,
                    int(amt*10**18*(1-loss_limit)),
                    sender = user,
                )
            except Exception as e:
                print("add_liquidity loss exceeded")

            num_add_liq += 1
        elif op == 1: # withdraw one liq
            coin_idx = random.randint(0, len(coins)-1)
            coin = coins[coin_idx]
            lp_amt = pool.balanceOf(user)
            if lp_amt == 0:
                continue
            # max_amt = max(pool.balanceOf(user) / 10**18, pool.balances(coin_idx)/10**6)
            withdraw_amt = random.randint(1, min(pool.balanceOf(user), 1000*10**18))

            out_coin_amt = pool.remove_liquidity_one_coin(
                withdraw_amt,
                coin_idx,
                0,
                sender = user,
            )
            # print("user withdraw liq")
            num_remove_liq += 1
        elif op == 2: # swap
            x, y = random.sample(range(len(coins)), 2)
            in_amt = random.randint(1, 10000) * 10**6
            try:
                out_amt = pool.exchange(
                    x, y,
                    in_amt, int(in_amt*(1-loss_limit)),
                    sender=user,
                )
            except Exception as e:
                print(f"swap loss exceeded {loss_limit}")
            num_swap += 1
        else:
            assert False

        bals = pool.get_balances()
        max_min_ratio = max(bals) / min(bals)
        ratios.append(max_min_ratio)
        vp = virtual_price(pool)
        vps.append(vp)
        if vp < 1:
            assert False

num_txs = 10000
loss_limit = 0.2
monte_carlo_sim(num_txs, loss_limit)

print(f"after {num_txs} txs")
print("  final pool balance", print_balances(pool))
print("  finla pool virtual price", virtual_price(pool))

# now balance the pool by making all consititutes equal
user = users[0]
balances = pool.get_balances()
max_bal = max(balances)
amounts = [max_bal - bal for bal in balances]
print(amounts)
lp_mint_amt = pool.add_liquidity(
    amounts,
    0,
    sender = user,
)
print("after balancing pool: ")
print("   pool balance", print_balances(pool))
print("   pool virtual price", virtual_price(pool))

import matplotlib.pyplot as plt
times = list(range(len(vps)))

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10,8), sharex=True)
ax1.plot(times, vps, 'b-')
ax1.set_ylabel('virtual prices')
ax1.grid(True)

ax2.plot(times, ratios, 'r-')
ax2.set_xlabel('Time')
ax2.set_ylabel('max/min balance ration')
ax2.set_yscale('log')
ax2.set_yticks([1, 10, 100, 1000])
ax2.set_yticklabels(['1', '10', '100', '1000'])
ax2.grid(True)
plt.figtext(0.5, 0.01, f"A={A}, fee={fee}, num_txs={num_txs}, loss_limit={loss_limit}", ha="center", fontsize=12)


plt.tight_layout()
# plt.show()
plt.savefig('vps_ratio_plot.png', dpi=300, bbox_inches='tight')
