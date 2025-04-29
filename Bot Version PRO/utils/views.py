# 📥 Importações
import discord
import sqlite3
import asyncio
import qrcode
from io import BytesIO
from utils.database import (
    add_produto,
    add_contas,
    get_produtos_por_categoria,
    vender_conta,
    get_all_produtos,
    get_contas_do_produto,
    remover_conta,
    is_admin,
    get_canal,
    get_todas_categorias
)
from utils.mercadopago import criar_pagamento, consultar_pagamento

# 🎛️ Painel de Administração
class PainelADM(discord.ui.View):
    @discord.ui.button(label="➕ Adicionar Produto", style=discord.ButtonStyle.green)
    async def adicionar_produto(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_admin(interaction.guild.id, interaction.user.id):
            await interaction.response.send_message("🚫 Você não tem permissão para usar o painel.", ephemeral=True)
            return

        await interaction.response.send_message("📂 Informe a categoria do produto:", ephemeral=True)
        categoria_msg = await interaction.client.wait_for('message', check=lambda m: m.author.id == interaction.user.id)
        categoria = categoria_msg.content

        await interaction.followup.send("📝 Informe o nome do produto:", ephemeral=True)
        nome_msg = await interaction.client.wait_for('message', check=lambda m: m.author.id == interaction.user.id)
        nome = nome_msg.content

        await interaction.followup.send("💲 Informe o preço do produto (ex: 10.00):", ephemeral=True)
        preco_msg = await interaction.client.wait_for('message', check=lambda m: m.author.id == interaction.user.id)
        preco = float(preco_msg.content)

        await interaction.followup.send("📦 Informe a quantidade de estoque:", ephemeral=True)
        estoque_msg = await interaction.client.wait_for('message', check=lambda m: m.author.id == interaction.user.id)
        estoque = int(estoque_msg.content)

        produto_id = add_produto(interaction.guild.id, nome, categoria, preco, estoque)

        await interaction.followup.send("✉️ Envie as contas no formato email:senha, uma por linha:", ephemeral=True)
        contas_msg = await interaction.client.wait_for('message', check=lambda m: m.author.id == interaction.user.id)
        contas = contas_msg.content.splitlines()

        add_contas(interaction.guild.id, produto_id, contas)

        await interaction.followup.send("✅ Produto e contas adicionados com sucesso!", ephemeral=True)
        await atualizar_loja_categoria(interaction.guild, produto_id)

    @discord.ui.button(label="📦 Ver Estoque", style=discord.ButtonStyle.blurple)
    async def ver_estoque(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_admin(interaction.guild.id, interaction.user.id):
            await interaction.response.send_message("🚫 Você não tem permissão para usar o painel.", ephemeral=True)
            return

        produtos = get_all_produtos(interaction.guild.id)
        embed = discord.Embed(title="📦 Estoque Atual", color=discord.Color.green())

        if produtos:
            for id_produto, nome, categoria, preco, estoque in produtos:
                embed.add_field(
                    name=f"🆔 ID: {id_produto} | 📂 {nome}",
                    value=f"💬 Categoria: `{categoria}`\n💲Preço: R${preco:.2f}\n📦 Estoque: {estoque}",
                    inline=False
                )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message("🚫 Nenhum produto cadastrado.", ephemeral=True)

    @discord.ui.button(label="🗑️ Remover Conta", style=discord.ButtonStyle.red)
    async def remover_conta(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_admin(interaction.guild.id, interaction.user.id):
            await interaction.response.send_message("🚫 Você não tem permissão para usar o painel.", ephemeral=True)
            return

        await interaction.response.send_message("🛒 Informe o 🆔 ID do produto:", ephemeral=True)
        produto_msg = await interaction.client.wait_for('message', check=lambda m: m.author.id == interaction.user.id)
        produto_id = int(produto_msg.content)

        contas = get_contas_do_produto(interaction.guild.id, produto_id)

        if not contas:
            await interaction.followup.send("🚫 Nenhuma conta encontrada.", ephemeral=True)
            return

        view = RemoverContaView(contas, interaction.guild)
        await interaction.followup.send("🗑️ Escolha a conta para remover:", view=view, ephemeral=True)

# 🛠️ Views Auxiliares para Remover Conta
class RemoverContaView(discord.ui.View):
    def __init__(self, contas, guild):
        super().__init__()
        self.guild = guild
        for conta_id, email_senha in contas:
            self.add_item(RemoverContaButton(conta_id, email_senha, guild))

class RemoverContaButton(discord.ui.Button):
    def __init__(self, conta_id, email_senha, guild):
        super().__init__(label=email_senha, style=discord.ButtonStyle.danger)
        self.conta_id = conta_id
        self.guild = guild

    async def callback(self, interaction: discord.Interaction):
        from utils.database import remover_conta
        produto_id = remover_conta(self.guild.id, self.conta_id)
        await atualizar_loja_categoria(self.guild, produto_id)
        await interaction.response.send_message("✅ Conta removida e loja atualizada!", ephemeral=True)

# 📦 Atualizar Loja por Categoria
async def atualizar_loja_categoria(guild, produto_id):
    conn = sqlite3.connect('database/loja.db')
    c = conn.cursor()
    c.execute("SELECT categoria FROM produtos WHERE id = ?", (produto_id,))
    result = c.fetchone()
    conn.close()

    if result:
        categoria = result[0]
        canal_id = get_canal(guild.id, categoria)

        if canal_id:
            canal = guild.get_channel(canal_id)
            if canal:
                async for msg in canal.history(limit=1):
                    if msg.author == guild.me:
                        await msg.delete()

                produtos = get_produtos_por_categoria(guild.id, categoria)
                if produtos:
                    embed = discord.Embed(
                        title=f"🛍️ {categoria} - Produtos Disponíveis",
                        description="🛒 Escolha o serviço desejado:",
                        color=discord.Color.blue()
                    )
                    view = ProdutoDropdown(produtos)
                    await canal.send(embed=embed, view=view)
                else:
                    await canal.send(f"🚫 Sem produtos disponíveis para {categoria}.")

# 📦 Atualizar TODAS as Lojas
async def atualizar_lojas(guild, bot):
    categorias = get_todas_categorias(guild.id)
    for categoria, canal_id in categorias:
        canal = guild.get_channel(canal_id)
        if canal:
            async for msg in canal.history(limit=1):
                if msg.author == guild.me:
                    await msg.delete()

            produtos = get_produtos_por_categoria(guild.id, categoria)
            if produtos:
                embed = discord.Embed(
                    title=f"🛍️ {categoria} - Produtos Disponíveis",
                    description="🛒 Escolha seu serviço no menu abaixo!",
                    color=discord.Color.blue()
                )
                view = ProdutoDropdown(produtos)
                await canal.send(embed=embed, view=view)
            else:
                await canal.send(f"🚫 Sem produtos disponíveis para {categoria}.")

# 🛒 Dropdown de Produtos
class ProdutoDropdown(discord.ui.View):
    def __init__(self, produtos):
        super().__init__()
        options = []
        for id_produto, nome, preco, estoque in produtos:
            options.append(
                discord.SelectOption(
                    label=nome,
                    description=f"💲 R${preco:.2f} | 📦 {estoque} unidades",
                    value=str(id_produto)
                )
            )
        self.add_item(ProdutoSelect(options))

class ProdutoSelect(discord.ui.Select):
    def __init__(self, options):
        super().__init__(placeholder="🛒 Escolha o produto!", options=options)

    async def callback(self, interaction: discord.Interaction):
        produto_id = int(self.values[0])

        conn = sqlite3.connect('database/loja.db')
        c = conn.cursor()
        c.execute("SELECT nome, preco FROM produtos WHERE id = ?", (produto_id,))
        result = c.fetchone()
        conn.close()

        if not result:
            await interaction.response.send_message("🚫 Produto não encontrado!", ephemeral=True)
            return

        nome_produto, preco = result

        qr_code_data, payment_id = criar_pagamento(
            nome_produto,
            preco,
            interaction.user.id,
            interaction.guild.id
        )

        qr = qrcode.make(qr_code_data)
        buffer = BytesIO()
        qr.save(buffer, format="PNG")
        buffer.seek(0)
        qr_file = discord.File(fp=buffer, filename="qrcode.png")

        embed = discord.Embed(
            title="💳 Pagamento via PIX (Direto)",
            description=f"🛒 Produto: **{nome_produto}**\n💲 Valor: **R${preco:.2f}**\n\n📷 Escaneie o QR Code abaixo para pagar!",
            color=discord.Color.green()
        )
        embed.set_image(url="attachment://qrcode.png")

        await interaction.response.send_message(embed=embed, file=qr_file, ephemeral=True)

        for _ in range(60):
            await asyncio.sleep(5)
            status = consultar_pagamento(payment_id, interaction.guild.id)
            if status == "approved":
                conta = vender_conta(interaction.guild.id, produto_id)
                if conta:
                    await interaction.user.send(f"🎁 Sua conta:\n`{conta}`")
                    await interaction.followup.send("✅ Pagamento confirmado! Sua conta foi enviada!", ephemeral=True)
                    await atualizar_loja_categoria(interaction.guild, produto_id)
                else:
                    await interaction.followup.send("🚫 Produto sem estoque!", ephemeral=True)
                return
            elif status == "rejected":
                await interaction.followup.send("🚫 Pagamento recusado pelo MercadoPago.", ephemeral=True)
                return

        await interaction.followup.send("⏳ Tempo de pagamento esgotado. Pedido cancelado.", ephemeral=True)
