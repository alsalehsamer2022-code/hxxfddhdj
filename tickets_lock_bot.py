import asyncio
import os

import discord
from discord.ext import commands

# ============================================================
#                        الإعدادات
# ============================================================
TOKEN = os.environ["DISCORD_TOKEN"]        # حطه في Environment ولا تكتبه هنا
TICKET_PREFIX = "ticket-"                  # أي قناة اسمها يبدأ بهذا تعتبر تكت
ACTION_DELAY = 0.6                         # ثواني بين كل قناة عشان ما ينضرب الـ rate limit
COMMAND_PREFIX = "!"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)


# ============================================================
#                        دوال مساعدة
# ============================================================
def is_staff_member(member):
    p = member.guild_permissions
    return p.administrator or p.manage_channels or p.manage_guild


def is_staff_role(role):
    p = role.permissions
    return p.administrator or p.manage_channels or p.manage_guild


def ticket_channels(guild):
    return [c for c in guild.text_channels if c.name.lower().startswith(TICKET_PREFIX)]


async def lock_channel(channel):
    """يمنع صاحب التكت (والرتب غير الإدارية) من الكتابة، ويبقي الستاف على صلاحياتهم."""
    guild = channel.guild
    for target, ow in list(channel.overwrites.items()):
        if target == guild.default_role:
            continue
        if isinstance(target, discord.Member):
            if target.bot or is_staff_member(target):
                continue
        elif isinstance(target, discord.Role):
            if is_staff_role(target):
                continue
        else:
            continue
        if ow.send_messages is False:
            continue
        ow.send_messages = False
        ow.add_reactions = False
        await channel.set_permissions(target, overwrite=ow, reason="تقفيل جماعي للتكتات")
    await channel.send("🔒 تم تقفيل هذا التكت من قبل الإدارة.")


async def process_tickets(ctx_channel, guild, mode, invoker):
    channels = ticket_channels(guild)
    if not channels:
        await ctx_channel.send("ما فيه تكتات مفتوحة.")
        return

    done, failed = 0, 0
    for ch in channels:
        try:
            if mode == "delete":
                await ch.delete(reason="حذف جماعي للتكتات بواسطة " + str(invoker))
            else:
                await lock_channel(ch)
            done += 1
        except Exception as e:
            failed += 1
            print("تعذر معالجة", ch.name, repr(e))
        await asyncio.sleep(ACTION_DELAY)

    action = "حذف" if mode == "delete" else "تقفيل"
    text = "✅ تم " + action + " **" + str(done) + "** تكت."
    if failed:
        text += "\n⚠️ فشل " + str(failed) + " تكت، تأكد إن البوت عنده صلاحية **Manage Channels**."
    await ctx_channel.send(text)


class ConfirmView(discord.ui.View):
    def __init__(self, mode):
        super().__init__(timeout=60)
        self.mode = mode

    @discord.ui.button(label="تأكيد", emoji="✅", style=discord.ButtonStyle.danger)
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_staff_member(interaction.user):
            await interaction.response.send_message("🔒 للإدارة فقط.", ephemeral=True)
            return
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(content="⏳ جاري المعالجة...", view=self)
        await process_tickets(interaction.channel, interaction.guild, self.mode, interaction.user)

    @discord.ui.button(label="إلغاء", emoji="❌", style=discord.ButtonStyle.secondary)
    async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(content="❌ ملغي.", view=self)


def confirm_text(count, mode):
    if mode == "delete":
        return "⚠️ بتحذف **" + str(count) + "** تكت نهائياً. ما فيه رجعة. متأكد؟"
    return "⚠️ بتقفل **" + str(count) + "** تكت (صاحب التكت ما يقدر يكتب فيه). متأكد؟"


# ============================================================
#                        الأوامر
# ============================================================
@bot.event
async def on_ready():
    print("✅ شغّال كـ", bot.user)


@bot.command(name="closeall", aliases=["تقفيل_الكل"])
@commands.has_permissions(manage_channels=True)
async def closeall_cmd(ctx, mode: str = "lock"):
    """!closeall          → يقفل كل التكتات
       !closeall delete   → يحذف كل التكتات"""
    mode = mode.lower()
    if mode not in ("lock", "delete"):
        await ctx.send("❌ الوضع لازم يكون `lock` أو `delete`.")
        return
    count = len(ticket_channels(ctx.guild))
    if count == 0:
        await ctx.send("ما فيه تكتات مفتوحة.")
        return
    await ctx.send(confirm_text(count, mode), view=ConfirmView(mode))


@closeall_cmd.error
async def closeall_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("🔒 هذا الأمر للإدارة فقط.")


if __name__ == "__main__":
    bot.run(TOKEN)
