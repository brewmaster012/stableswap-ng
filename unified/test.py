import boa

def print_balances(pool):
    return [b/10**6 for b in pool.get_balances()]

def virtual_price(pool):
    usdc_amount = sum([ bal/10**6  for bal in  pool.get_balances()])
    return usdc_amount / (pool.totalSupply()/(10**pool.decimals()))

wallet = boa.env.eoa
INITIAL_AMOUNT = 100

math_deployer = boa.load_partial("../contracts/main/CurveStableSwapNGMath.vy")
coin0 = boa.load("../contracts/mocks/ERC20.vy", "coin0", "coin0", 6)
coin1 = boa.load("../contracts/mocks/ERC20.vy", "coin1", "coin1", 6)
coin2 = boa.load("../contracts/mocks/ERC20.vy", "coin2", "coin2", 6)
coin3 = boa.load("../contracts/mocks/ERC20.vy", "coin3", "coin3", 6)
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

factory = boa.load("../contracts/main/CurveStableSwapFactoryNG.vy", fee_receiver, wallet)
print("fee_receiver", factory.fee_receiver())
print("admin", factory.admin())
print("fee rate", fee)
print("A", A)

amm_deployer = boa.load_partial("../contracts/main/CurveStableSwapNG.vy")
amm_implementation = amm_deployer.deploy_as_blueprint()
math = boa.load("../contracts/main/CurveStableSwapNGMath.vy")
factory.set_pool_implementations(0, amm_implementation.address)
factory.set_math_implementation(math.address)

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

pool = boa.load_partial("../contracts/main/CurveStableSwapNG.vy").at(pool_addr)
pool.add_liquidity(
    [INITIAL_AMOUNT * 10**6] * pool_size,
    0,
)
print("deployer: initial deposit liquidity: 100 coin0/coin1/coin2/coin3")
print("  deployer LP token", pool.balanceOf(wallet))
alice = boa.env.generate_address()

vault = boa.load("./StableVault.vy", "USDC Unified", "uUSDC", pool.address);
print( "deployed StableVault:")
print(f"  address: {vault.address}")
print(f"  pool:    {vault.poolAddress()}")
print(f"  name:    {vault.name()}")
print(f"  symbol:  {vault.symbol()}")
print(f"  decimal: {vault.decimals()}")
print(f"  supply:  {vault.totalSupply()}")
print(f"  N_COINS: {vault.N_COINS()}")
print(f"  coin0:   {vault.coins(0)}")

coins = [coin0, coin1, coin2, coin3]
print("Vault: alice deposit ERC20")
for c in coins:
    c._mint_for_testing(alice, INITIAL_AMOUNT*10**6)
    c.approve(vault.address, 1000*10**6, sender=alice)
vault.deposit([100*10**6]*4, 0, sender=alice)
uUSDC_bal = vault.balanceOf(alice)
print(f"  vault LP token bal: {pool.balanceOf(vault.address)}")
print(f"  minted uUSDC        {uUSDC_bal}")
print(f"  vault supply        {vault.totalSupply()}")


print("Vault: alice withdraw 1 coin1")
coin1_recv = vault.withdraw_one_coin(
    5*10**18,
    1,
    0,
    sender=alice
)
print(f"  return val:      {coin1_recv}")
print(f"  vault supply:    {vault.totalSupply()}")
print(f"  coin1 alice bal: {coin1.balanceOf(alice)}")


print("Add a coin4 and deploy new pool")
coin4 = boa.load("../contracts/mocks/ERC20.vy", "coin4", "coin4", 6)
coin4._mint_for_testing(wallet, INITIAL_AMOUNT*10**6)
coins = [coin0, coin1, coin2, coin3, coin4]
pool_addr_new = factory.deploy_plain_pool(
    "USDC.5",
    "USDC.5",
    [c.address for c in coins],
    A,
    fee,
    OFFPEG_FEE_MULTIPLIER,
    866,
    0,
    [0]*len(coins),
    [bytes(b"")] * len(coins),
    [zero_address] * len(coins),
)
pool_new = boa.load_partial("../contracts/main/CurveStableSwapNG.vy").at(pool_addr_new)
# print("same code?", vault.same_code(pool.address, pool_new.address))

print("before liq migration")
print("  vault backed?", vault.backed_by_lp())
coin4.approve(vault.address, 1000*10**6)
lp_token = vault.totalSupply()
print(f"migrating {lp_token} from old pool to new pool; ")
print(f"  b4 pool balance: {pool.get_balances()}")
recv, new_lp = vault.migrate_pool_add_asset( pool_new.address, coin4.address, 3*10**6, 2*10**6)
print(f"  recv:           {recv}")
print(f"  recv sum:       {sum(recv)}")
print(f"  new pool bal:   {pool_new.balanceOf(vault.address)}")
print(f"  vault balance:  {vault.totalSupply()}")
print(f"  newly minted LP token    {new_lp}")
print(f"  vault backed?   {vault.backed_by_lp()}")
