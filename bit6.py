from bip_utils import Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes, Bip49, Bip49Coins, Bip84, Bip84Coins
from bip_utils import Bip39MnemonicGenerator, Bip39WordsNum
from concurrent.futures import ThreadPoolExecutor

def generate_wallets(mnemonic):
    # Generate seed from mnemonic
    seed = Bip39SeedGenerator(mnemonic).Generate()

    # P2PKH (Legacy, BIP44)
    bip44 = Bip44.FromSeed(seed, Bip44Coins.BITCOIN)
    legacy_account = bip44.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(0)
    legacy_address = legacy_account.PublicKey().ToAddress()

    # P2SH (SegWit, BIP49)
    bip49 = Bip49.FromSeed(seed, Bip49Coins.BITCOIN)
    segwit_account = bip49.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(0)
    segwit_address = segwit_account.PublicKey().ToAddress()

    # Bech32 (Native SegWit, BIP84)
    bip84 = Bip84.FromSeed(seed, Bip84Coins.BITCOIN)
    native_segwit_account = bip84.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(0)
    native_segwit_address = native_segwit_account.PublicKey().ToAddress()

    return {
        "P2PKH": legacy_address,
        "P2SH": segwit_address,
        "Bech32": native_segwit_address,
    }

def generate_mnemonic():
    return Bip39MnemonicGenerator().FromWordsNumber(Bip39WordsNum.WORDS_NUM_12)

def identify_wallet_type(address):
    if address.startswith('1') and 26 <= len(address) <= 34:
        return "P2PKH"
    elif address.startswith('3') and 26 <= len(address) <= 34:
        return "P2SH"
    elif address.startswith('bc1') and (42 <= len(address) <= 62):
        return "Bech32"
    else:
        return None

def check_addresses_batch(addresses, wallet_addresses,mnemonic):
    results = []
    for wallet in addresses:
        wallet_type = identify_wallet_type(wallet)
        if wallet_type is None:
            results.append(f"Invalid address: {wallet}")
            continue
        generated_address = wallet_addresses.get(wallet_type)
        is_match = wallet == generated_address
        results.append({
            'address': wallet,
            'generated_address': generated_address,
            'match': is_match,
            'mnemonic': mnemonic
        })
    return results

if __name__ == "__main__":
    file_path = 'btc.txt'

    with open(file_path, 'r') as file:
        addresses = [line.rstrip() for line in file]

    while True:
        # Generate a random mnemonic
        mnemonic = generate_mnemonic()
        print(f"Mnemonic: {mnemonic}")

        # Generate wallet addresses once per mnemonic
        wallet_addresses = generate_wallets(mnemonic)

        # Use ThreadPoolExecutor for multithreaded batch processing
        batch_size = 100  # Adjust batch size for optimal performance
        address_batches = [addresses[i:i + batch_size] for i in range(0, len(addresses), batch_size)]

        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(check_addresses_batch, batch, wallet_addresses,mnemonic) for batch in address_batches]

        for future in futures:
            for result in future.result():
                if(result['match']):
                    with open('match.txt', 'a') as file2:
                        file.write(f"address: {result['address']} generated: {result['generated_address']} check: {result['match']} Mnemonic: {result['mnemonic']} \n")

                # print(f"address: {result['address']} generated: {result['generated_address']} check: {result['match']} Mnemonic: {result['mnemonic']}")
