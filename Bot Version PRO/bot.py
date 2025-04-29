# 📥 Importações principais
import discord
from discord.ext import commands
from utils.database import init_db, is_admin, set_webhook_url
from utils.views import PainelADM, atualizar_lojas

# 🎯 Configurações do Bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# 🛢️ Inicializar Banco de Dados
init_db()

# 🎉 Evento: Quando o bot ficar online
@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}!")

# 🛠️ Comando: Adicionar Administrador
OWNER_ID = 640338597710528514
@bot.command()
async def addadmin(ctx, user_id: int):
    if ctx.author.id != OWNER_ID:
        await ctx.send("🚫 Apenas o dono do bot pode adicionar administradores.")
        return

    from utils.database import add_admin
    add_admin(ctx.guild.id, user_id)
    await ctx.send(f"✅ Administrador adicionado com sucesso: <@{user_id}>!")

# 🛠️ Comando: Painel de Administração
@bot.command()
async def painel(ctx):
    if not is_admin(ctx.guild.id, ctx.author.id):
        await ctx.send("🚫 Você não tem permissão para abrir o Painel.")
        return

    embed = discord.Embed(
        title="🛠️ Painel Administrativo",
        description="Utilize os botões abaixo para gerenciar seus produtos!",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed, view=PainelADM())

# 🛠️ Comando: Atualizar Todas as Lojas
@bot.command()
async def atualizarloja(ctx):
    if not is_admin(ctx.guild.id, ctx.author.id):
        await ctx.send("🚫 Você não tem permissão para atualizar a loja.")
        return

    await atualizar_lojas(ctx.guild, bot)
    await ctx.send("✅ Loja atualizada com sucesso!")

# 🛠️ Comando: Definir Canal por Categoria
@bot.command()
async def setcanal(ctx, categoria: str, canal: discord.TextChannel):
    if not is_admin(ctx.guild.id, ctx.author.id):
        await ctx.send("🚫 Você não tem permissão para configurar canais.")
        return

    from utils.database import set_canal
    set_canal(ctx.guild.id, categoria, canal.id)
    await ctx.send(f"✅ Canal para a categoria **{categoria}** configurado em {canal.mention}!")

# 🛠️ Comando: Configurar Access Token do MercadoPago
@bot.command()
async def setmercadopago(ctx, token: str):
    if not is_admin(ctx.guild.id, ctx.author.id):
        await ctx.send("🚫 Você não tem permissão para configurar MercadoPago.")
        return

    from utils.database import set_mercadopago_token
    set_mercadopago_token(ctx.guild.id, token)

    embed = discord.Embed(
        title="🏦 MercadoPago Configurado",
        description="✅ Access Token salvo com sucesso!",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed)

# 🛠️ Comando: Configurar Webhook para Pix
@bot.command()
async def setwebhook(ctx, url: str):
    if not is_admin(ctx.guild.id, ctx.author.id):
        await ctx.send("🚫 Você não tem permissão para configurar Webhook.")
        return

    set_webhook_url(ctx.guild.id, url)

    embed = discord.Embed(
        title="🌐 Webhook Configurado",
        description=f"✅ Webhook salvo com sucesso!\n🔗 URL: {url}",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed)

# 🛠️ Comando: Limpar Estoque de Produtos sem Contas
@bot.command()
async def limparestoque(ctx):
    if not is_admin(ctx.guild.id, ctx.author.id):
        await ctx.send("🚫 Você não tem permissão para limpar estoque.")
        return

    from utils.database import limpar_estoque
    limpar_estoque(ctx.guild.id)

    await atualizar_lojas(ctx.guild, bot)
    await ctx.send("✅ Estoques zerados removidos e lojas atualizadas!")

# 📢 Rodar o Bot
bot.run("MTM2NjE5MDc3NTkxNzg3MTEzNA.GE0JsH.8uMaRhDPFrVgcoDHeGoh3OEjgSbiXRqfvBzBIY")
