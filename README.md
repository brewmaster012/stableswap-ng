# Stable Vault on top of Stableswap pool
This repository contains a Proof-of-Concept implementation of a Stable Vault that issues
ERC20 token backed by the LP token of underlying Curve StableSwap pool.
The underlying StableSwap pool is a modified [Curve StableSwap pool](https://github.com/zeta-chain/FluidUSDC?tab=readme-ov-file); See the README there
to find movitation and more details.

the minor modificationsa are:

1. change fee ratio to 100% to admin and 0% to LP holder so that the virtual price of LP token
should not accrue value due to tx fees.


The [Vault](./unified/StableVault.vy) contract is 1) ERC20 contract backed by underlying `CurveStableSwapNG`
pool LP token; 2) pass through liquidity add/remove functions; 3) admin functions that change the
underlying `CurveStableSwapNG` pool address and migrate the LP managed by this vault (for the purpose
of adding asset to the pool or remove assets).

See the test cases of adding/removing liqudity and adding assets in this [test file](./unified/test.py)
and hints as to how to deploy the Vault contract.

Note that normal swaps are still through the underlying pool.

## dependencies
A modified [Curve StableSwap pool](https://github.com/zeta-chain/FluidUSDC?tab=readme-ov-file)
underlying pool deployed;

## contracts
In the `unfified` directory.

[Vault](./unified/StableVault.vy)

## To run the test
1. Install python3 poetry package manager and install the dependencies by running `poetry install`
2. Enter into virtual env `poetry shell`
3. Run the test script in the unified directory: `python3 test.py`

Sample output of the test scripts
```
% python3 test.py
fee_receiver 0xd13f0Bd22AFF8176761AEFBfC052a7490bDe268E
admin 0x00dE89C733555886f785b0C32b498300297e481F
fee rate 0
A 1000
deployer: initial deposit liquidity: 100 coin0/coin1/coin2/coin3
  deployer LP token 400000000000000000000
deployed StableVault:
  address: 0x864C57A226c39F4cfC30A589B9198D583Ad6971a
  pool:    0xB8199Ae2D51948B64ed7F8Fc598BB4F6CCD6C160
  name:    USDC Unified
  symbol:  uUSDC
  decimal: 18
  supply:  0
  N_COINS: 4
  coin0:   0x0880cf17Bd263d3d3a5c09D2D86cCecA3CcbD97c
Vault: alice deposit ERC20
  vault LP token bal: 400000000000000000000
  minted uUSDC        400000000000000000000
  vault supply        400000000000000000000
  vault backed? True
Vault: alice withdraw 1 coin1
  return val:      4999952
  vault supply:    395000000000000000000
  coin1 alice bal: 4999952
  vault backed? True
Add a coin4 and deploy new pool
before liq migration
  vault backed? True
migrating 395000000000000000000 from old pool to new pool;
  b4 pool balance: [200000000, 195000048, 200000000, 200000000]
  recv:           [99371069, 96886816, 99371069, 99371069, 3000000]
  recv sum:       398000023
  new pool bal:   397198295291789199500
  vault balance:  397198295291789199500
  newly minted LP token    2198295291789199500
  vault backed?   True
```


```
/-------------------------------------------\
|                                           |
|   Below is the original documentation    |
|   of Curve StableSwap                    |
|                                           |
\-------------------------------------------/
```

# Stableswap NG

Permissionless deployment of Curve Stableswap plain and metapools. Supports up to 8 coins for plain pools and 2 coins for metapools. Supports: rate-oraclised tokens (e.g. wstETH), ERC4626 (sDAI), rebasing (stETH), and plain (WETH:stETH) pools. Does not support native tokens.

For integrators: check exchange_received. That should improve your pathing significantly. Be aware that if a pool contains rebasing tokens, this method is intentionally disabled.

# Deployments

For a full list of deployments, please check: [The deployment script](scripts/deploy_infra.py)

## Overview

The metapool factory has several core components:

- [`Factory`](contracts/main/CurveStableSwapFactoryNG.vy) is the main contract used to deploy new metapools. It also acts a registry for finding the deployed pools and querying information about them.
- New pools are deployed via blueprints. The [implementation contract](contracts/main/CurveStableSwapNG.vy) targeted by the proxy is determined according to the base pool.

See the [documentation](https://docs.curve.fi) for more detailed information.

## Testing

### Installation

Install dependencies using poetry (python ^3.10.4)

```shell
pip install poetry==1.8.3
poetry install
```

### Type of tests

Testing gauge

```shell
pytest tests/gauge/
```

Testing factory

```shell
pytest tests/factory/
```

Testing swap is ERC20

```shell
pytest tests/token/
```

Testing swaps

```shell
pytest tests/pools/
```
