import pytest
from brownie import config, chain, Contract


@pytest.fixture
def gov(accounts):
    yield accounts.at("0xFEB4acf3df3cDEA7399794D0869ef76A6EfAff52", force=True)


@pytest.fixture
def user(accounts):
    yield accounts[0]


@pytest.fixture
def rewards(accounts):
    yield accounts[1]


@pytest.fixture
def guardian(accounts):
    yield accounts[2]


@pytest.fixture
def management(accounts):
    yield accounts[3]


@pytest.fixture
def strategist(accounts):
    yield accounts[4]


@pytest.fixture
def keeper(accounts):
    yield accounts[5]


@pytest.fixture
def token():
    token_address = "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599"  # this should be the address of the ERC-20 used by the strategy/vault (DAI)
    yield Contract(token_address)


@pytest.fixture
def lpComponent():
    token_address = "0x9ff58f4ffb29fa2266ab25e75e2a8b3503311656"  # this should be the address of the ERC-20 used by the strategy/vault (DAI)
    yield Contract(token_address)


@pytest.fixture
def borrowed():
    token_address = "0x9c39809Dec7F95F5e0713634a4D0701329B3b4d2"  # this should be the address of the ERC-20 used by the strategy/vault (DAI)
    yield Contract(token_address)


@pytest.fixture
def incentivesController():
    token_address = "0xd784927Ff2f95ba542BfC824c8a8a98F3495f6b5"
    yield Contract(token_address)


@pytest.fixture
def reward():
    token_address = "0x4da27a545c0c5b758a6ba100e3a049001de870f5"  # this should be the address of the ERC-20 used by the strategy/vault (DAI)
    yield Contract(token_address)


@pytest.fixture
def aave():
    token_address = "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9"  # this should be the address of the ERC-20 used by the strategy/vault (DAI)
    yield Contract(token_address)


@pytest.fixture
def amount(accounts, token, user, gov, management):
    amount = 1_000 * 10 ** token.decimals()
    # In order to get some funds for the token you are about to use,
    # it impersonate an exchange address to use it's funds.
    reserve = accounts.at("0x9ff58f4ffb29fa2266ab25e75e2a8b3503311656", force=True)
    token.transfer(user, amount, {"from": reserve})

    ## Also send a little bit to gov for test_manual_operation
    token.transfer(gov, 100 * 10 ** token.decimals(), {"from": reserve})
    token.transfer(management, 100 * 10 ** token.decimals(), {"from": reserve})
    yield amount


@pytest.fixture
def weth():
    token_address = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
    yield Contract(token_address)


@pytest.fixture
def weth_amout(user, weth):
    weth_amout = 10 ** weth.decimals()
    user.transfer(weth, weth_amout)
    yield weth_amout


@pytest.fixture
def vault(pm, gov, rewards, guardian, management, token):
    Vault = pm(config["dependencies"][0]).Vault
    vault = guardian.deploy(Vault)
    vault.initialize(token, gov, rewards, "", "", guardian, management)
    vault.setDepositLimit(2 ** 256 - 1, {"from": gov})
    vault.setManagement(management, {"from": gov})
    yield vault


@pytest.fixture
def strategy(strategist, keeper, vault, Strategy, gov):
    strategy = strategist.deploy(Strategy, vault)
    strategy.setKeeper(keeper)
    strategy.setHealthCheck("0xDDCea799fF1699e98EDF118e0629A974Df7DF012", {"from": gov})
    vault.addStrategy(strategy, 10_000, 0, 2 ** 256 - 1, 1_000, {"from": gov})
    yield strategy


@pytest.fixture
def RELATIVE_APPROX():
    yield 1e-5


@pytest.fixture
def levered_strat(vault, user, token, strategy, RELATIVE_APPROX, amount):
    # Deposit to the vault and harvest
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
    chain.sleep(1)
    strategy.harvest()
    assert strategy.doHealthCheck() == True
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount
    chain.sleep(1)
    return strategy


## Forces reset before each test
@pytest.fixture(autouse=True)
def isolation(fn_isolation):
    pass
