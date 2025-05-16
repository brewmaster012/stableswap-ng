# pragma version 0.3.10
# pragma optimize codesize
# pragma evm-version shanghai

MAX_COINS: constant(uint256) = 8  # max coins is 8 in the factory
MAX_COINS_128: constant(int128) = 8

interface StableSwapNG:
    def N_COINS() -> uint256: view
    def add_liquidity(
        amounts: DynArray[uint256, MAX_COINS],
        min_mint_amount: uint256
    ) -> uint256: nonpayable
    def remove_liquidity(
        amount: uint256,
        min_amounts: DynArray[uint256, MAX_COINS]
    ) -> DynArray[uint256, MAX_COINS]: nonpayable
    def remove_liquidity_one_coin(
        token_amount: uint256,
        i: int128,
        min_amount: uint256
    ) -> uint256: nonpayable
    def remove_liquidity_imbalance(
        amounts: DynArray[uint256, MAX_COINS],
        max_burn_amount: uint256
    ) -> uint256: nonpayable
    def calc_withdraw_one_coin(token_amount: uint256, i: int128) -> uint256: view
    def calc_token_amount(
        amounts: DynArray[uint256, MAX_COINS],
        deposit: bool
    ) -> uint256: view
    def coins(i: uint256) -> address: view
    def fee() -> uint256: view

from vyper.interfaces import ERC20
implements: ERC20

# ------- Events -----------
event Transfer:
    sender: indexed(address)
    receiver: indexed(address)
    value: uint256

event Approval:
    owner: indexed(address)
    spender: indexed(address)
    value: uint256

# ------ ERC20 stuff ---------
name: public(immutable(String[64]))
symbol: public(immutable(String[32]))
decimals: public(constant(uint8)) = 18
version: public(constant(String[8])) = "v1.0.0"

balanceOf: public(HashMap[address, uint256])
allowance: public(HashMap[address, HashMap[address, uint256]])
total_supply: uint256

# ------ state variables ----------
poolAddress: public(address)
N_COINS: public(uint256)
N_COINS_128: int128

# ------ init ----------
@external
def __init__(
    _name: String[32],
    _symbol: String[10],
    _pool: address,
):
    name = _name
    symbol = _symbol
    # TODO: basic sanity check of the curve stableswap-ng pool
    self.poolAddress = _pool
    self.N_COINS = StableSwapNG(_pool).N_COINS()
    self.N_COINS_128 = convert(self.N_COINS, int128)
    return

# ------ Current CurveStableSwap pool queries -----
@view
@external
def coins(i: uint256) -> address:
    return StableSwapNG(self.poolAddress).coins(i)

@view
@internal
def _coins(i: int128) -> address:
    _i: uint256 = convert(i, uint256)
    return StableSwapNG(self.poolAddress).coins(_i)

# ------ Deposit and withdraw from the pools ------
@external
@nonreentrant('lock')
def deposit(
    _amounts: DynArray[uint256, MAX_COINS],
    _min_mint_amount: uint256,
    _receiver: address = msg.sender
) -> uint256:
    for i in range(self.N_COINS_128, bound=MAX_COINS_128):
        if _amounts[i] > 0:
            coin_address: address = self._coins(i)
            ERC20(coin_address).transferFrom(msg.sender, self, _amounts[i])
            ERC20(coin_address).approve(self.poolAddress, _amounts[i])

    lp_tokens: uint256 = StableSwapNG(self.poolAddress).add_liquidity(_amounts, _min_mint_amount)
    self._mint(_receiver, lp_tokens) # FIXME: assuming decimals of Vault == decimals of CurveStableSwapNG pool, 18.
    return lp_tokens

@external
@nonreentrant('lock')
def withdraw_one_coin(
     _burn_amount: uint256,
    i: int128,
    _min_received: uint256,
    _receiver: address = msg.sender,
) -> uint256:
    self._burnFrom(msg.sender, _burn_amount)
    coin_i: uint256 = StableSwapNG(self.poolAddress).remove_liquidity_one_coin(_burn_amount, i, _min_received)
    coin_address: address = self._coins(i)
    ERC20(coin_address).transfer(_receiver, coin_i)
    return coin_i

# ------ Migrate to new pool -------------



# ------ ERC20 impl ----------
@internal
def _mint(_to: address, _amount: uint256):
    self.balanceOf[_to] += _amount
    self.total_supply += _amount

@internal
def _transfer(_from: address, _to: address, _value: uint256):
    # # NOTE: vyper does not allow underflows
    # #       so the following subtraction would revert on insufficient balance
    self.balanceOf[_from] -= _value
    self.balanceOf[_to] += _value

    log Transfer(_from, _to, _value)

@internal
def _burnFrom(_from: address, _burn_amount: uint256):

    self.total_supply -= _burn_amount
    self.balanceOf[_from] -= _burn_amount
    log Transfer(_from, empty(address), _burn_amount)


@external
def approve(_spender : address, _value : uint256) -> bool:
    """
    @notice Approve the passed address to transfer the specified amount of
            tokens on behalf of msg.sender
    @dev Beware that changing an allowance via this method brings the risk that
         someone may use both the old and new allowance by unfortunate transaction
         ordering: https://github.com/ethereum/EIPs/issues/20#issuecomment-263524729
    @param _spender The address which will transfer the funds
    @param _value The amount of tokens that may be transferred
    @return bool success
    """
    self.allowance[msg.sender][_spender] = _value

    log Approval(msg.sender, _spender, _value)
    return True

@view
@external
@nonreentrant('lock')
def totalSupply() -> uint256:
    """
    @notice The total supply of pool LP tokens
    @return self.total_supply, 18 decimals.
    """
    return self.total_supply

@external
def transfer(_to : address, _value : uint256) -> bool:
    """
    @dev Transfer token for a specified address
    @param _to The address to transfer to.
    @param _value The amount to be transferred.
    """
    self._transfer(msg.sender, _to, _value)
    return True


@external
def transferFrom(_from : address, _to : address, _value : uint256) -> bool:
    """
     @dev Transfer tokens from one address to another.
     @param _from address The address which you want to send tokens from
     @param _to address The address which you want to transfer to
     @param _value uint256 the amount of tokens to be transferred
    """
    self._transfer(_from, _to, _value)

    _allowance: uint256 = self.allowance[_from][msg.sender]
    if _allowance != max_value(uint256):
        _new_allowance: uint256 = _allowance - _value
        self.allowance[_from][msg.sender] = _new_allowance
        log Approval(_from, msg.sender, _new_allowance)

    return True
