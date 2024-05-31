import discord
import random
from discord.ext import commands
from discord import Activity, ActivityType
from datetime import datetime, timedelta

# Intents konfigürasyonu
intents = discord.Intents.all()

client = commands.Bot(command_prefix='!', intents=intents)

# Kullanıcıların parasını ve son günlük ödüllerini saklamak için sözlükler
user_balances = {}
last_daily = {}

# Emoji listesi
emojis = {'Hearts': '❤️', 'Diamonds': '♦️', 'Clubs': '♣️', 'Spades': '♠️'}

# Bot kurucusunun ID'si
bot_owner_id = 852585480725725194


@client.event
async def on_ready():
    total_users = sum([guild.member_count for guild in client.guilds])
    total_guilds = len(client.guilds)
    await client.change_presence(activity=Activity(
        type=ActivityType.playing,
        name=
        f'{total_guilds} sunucuda | {total_users} kullanıcıya hizmet veriyor.')
                                 )
    print('Bot is ready.')


@client.command()
async def daily(ctx):
    user_id = ctx.author.id
    now = datetime.now()

    if user_id not in last_daily or now - last_daily[user_id] >= timedelta(
            days=1):
        last_daily[user_id] = now

        if user_id not in user_balances:
            user_balances[user_id] = 0

        earnings = random.randint(200, 2000)
        user_balances[user_id] += earnings
        await ctx.send(
            f'>>> ### {ctx.author.mention}, günlük ödülünüz {earnings}$!')
    else:
        next_daily = last_daily[user_id] + timedelta(days=1)
        time_left = next_daily - now
        hours, remainder = divmod(int(time_left.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        await ctx.send(
            f'>>> ### {ctx.author.mention}, günlük ödülünüzü zaten aldınız! Yeniden alabilmeniz için {hours} saat, {minutes} dakika ve {seconds} saniye kaldı.'
        )


@client.command()
async def fafatara(ctx):
    user_id = ctx.author.id
    if user_id not in user_balances:
        user_balances[user_id] = 0

    user_balances[user_id] += 100
    await ctx.send(
        f'>>> ### {ctx.author.mention}, Fafatara dediğiniz için 100$ kazandınız! Bakiyeniz: {user_balances[user_id]}$'
    )


@client.command()
async def balance(ctx):
    if ctx.author.id not in user_balances:
        await ctx.send(">>> ### Henüz bir hesabınız yok!")
    else:
        await ctx.send(
            f'>>> ### {ctx.author.mention}, bakiyeniz: {user_balances[ctx.author.id]}$'
        )


@client.command()
async def bj(ctx, amount: int):
    user_id = ctx.author.id

    if user_id != bot_owner_id:
        if user_id not in user_balances:
            await ctx.send(">>> ### Önce bir hesap oluşturmanız gerekiyor!")
            return

        if amount <= 0:
            await ctx.send(">>> ### Geçerli bir miktar girin!")
            return

        if amount > user_balances[user_id]:
            await ctx.send(">>> ### Yeterli bakiyeniz yok!")
            return

    player_hands = []
    dealer_hand = []

    def draw_card():
        color = random.choice(['Hearts', 'Diamonds', 'Clubs', 'Spades'])
        number = random.choice(
            ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A'])
        return {'color': emojis[color], 'number': number}

    # İlk kartları dağıtalım
    for _ in range(2):
        player_hands.append(draw_card())
        dealer_hand.append(draw_card())

    # Oyuncunun elini gösterelim
    await ctx.send(f">>> ### {ctx.author.mention}, elindeki kartlar:")
    await display_hand(player_hands, ctx, hand_value(player_hands))

    # Dağıtıcının ilk kartını gösterelim
    await ctx.send(">>> ### Dağıtıcının elindeki kart:")
    await ctx.send(f"{dealer_hand[0]['number']} {dealer_hand[0]['color']}")

    # Blackjack oyununu oynayalım
    while True:
        await ctx.send(
            ">>> ### Kart çekmek için `!hit`, kalmak için `!stand` yazın.")
        response = await client.wait_for(
            'message',
            check=lambda m: m.author == ctx.author and m.content.lower(
            ) in ['!hit', '!stand'])

        if response.content.lower() == '!hit':
            player_hands.append(draw_card())
            await ctx.send(f">>> ### {ctx.author.mention}, elindeki kartlar:")
            await display_hand(player_hands, ctx, hand_value(player_hands))

            # El değeri 21'i geçtiyse kaybettik
            if hand_value(player_hands) > 21:
                await ctx.send(
                    f">>> ### Battınız! Kaybettiniz! El toplamı: {hand_value(player_hands)}"
                )
                if user_id != bot_owner_id:
                    user_balances[ctx.author.id] -= amount
                    await ctx.send(
                        f">>> ### Yeni bakiyeniz: {user_balances[ctx.author.id]}$"
                    )
                return

        elif response.content.lower() == '!stand':
            # Dağıtıcının tüm kartlarını gösterelim
            await ctx.send(">>> ### Dağıtıcının elindeki kartlar:")
            await display_hand(dealer_hand, ctx, hand_value(dealer_hand))

            # Dağıtıcının el değeri 17'ye ulaşana kadar kart çek
            while hand_value(dealer_hand) < 17:
                dealer_hand.append(draw_card())
                await display_hand(dealer_hand, ctx, hand_value(dealer_hand))

            # Oyuncunun ve dağıtıcının el değerlerini kontrol edelim
            player_value = hand_value(player_hands)
            dealer_value = hand_value(dealer_hand)

            if player_value > dealer_value or dealer_value > 21:
                await ctx.send(
                    f">>> ### Tebrikler! Kazandınız! El toplamı: {player_value}"
                )
                if user_id != bot_owner_id:
                    user_balances[ctx.author.id] += amount
            elif player_value == dealer_value:
                await ctx.send(f">>> ### Berabere! El toplamı: {player_value}")
            else:
                await ctx.send(
                    f">>> ### Kaybettiniz! El toplamı: {dealer_value}")
                if user_id != bot_owner_id:
                    user_balances[ctx.author.id] -= amount

            await ctx.send(
                f">>> ### Yeni bakiyeniz: {user_balances[ctx.author.id]}$")
            return


@client.command()
async def transfer(ctx, amount: int, member: discord.Member):
    user_id = ctx.author.id
    target_id = member.id

    if user_id != bot_owner_id and (user_id not in user_balances
                                    or user_balances[user_id] < amount):
        await ctx.send(">>> ### Yeterli bakiyeniz yok!")
        return

    if user_id != bot_owner_id:
        user_balances[user_id] -= amount

    if target_id not in user_balances:
        user_balances[target_id] = 0

    user_balances[target_id] += amount

    await ctx.send(
        f'>>> ### {ctx.author.mention}, {amount}$ tutarında {member.mention} kullanıcısına para transfer etti. Yeni bakiyeniz: {user_balances[user_id]}$'
    )


async def display_hand(hand, ctx, value):
    hand_str = " ".join([f"{card['number']}{card['color']}" for card in hand])
    await ctx.send(f">>> {hand_str} (Toplam: {value})")


def hand_value(hand):
    value = 0
    num_aces = 0
    for card in hand:
        if card['number'] == 'A':
            num_aces += 1
        elif card['number'] in ['J', 'Q', 'K']:
            value += 10
        else:
            value += int(card['number'])
    for _ in range(num_aces):
        if value + 11 <= 21:
            value += 11
        else:
            value += 1
    return value


# Discord botunu başlatma
client.run('')
