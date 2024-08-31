import discord
from discord.ext import commands
from deep_translator import GoogleTranslator
import re
import os

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if bot.user.mentioned_in(message):
        await handle_mention(message)
    elif message.content.lower().startswith("translate this"):
        await handle_translation(message)

    await bot.process_commands(message)


async def handle_mention(message):
    content = re.sub(r"<@!?\d+>", "", message.content).strip()
    target_lang, text = extract_language_from_mention(content)
    translation = translate_text(text, target_lang)
    response = f"{message.author.mention} said: {translation}"
    await create_thread_and_respond(message, response, translation)


async def handle_translation(message):
    if message.reference:
        replied_msg = await message.channel.fetch_message(message.reference.message_id)
        content = replied_msg.content

        # Extract the language from the user's command
        target_lang, _ = extract_language_from_command(message.content)

        # Translate the content of the replied message
        translation = translate_text(content, target_lang)
        response = f"{message.author.mention} said: {translation}"
        await create_thread_and_respond(message, response, translation)
    else:
        # Handle case where there is no reference
        content = re.sub(
            r"^translate this\s*", "", message.content, flags=re.IGNORECASE
        )
        target_lang, text = extract_language_from_command(content)
        translation = translate_text(text, target_lang)
        response = f"{message.author.mention} said: {translation}"
        await create_thread_and_respond(message, response, translation)


async def create_thread_and_respond(message, response, translation):
    thread_title = create_thread_title(translation)
    try:
        thread = await message.create_thread(name=thread_title)
        await thread.send(response)
    except discord.errors.HTTPException:
        await message.reply(response)


def translate_text(text, target_lang):
    try:
        code_block_pattern = r"(```[\s\S]+?```|`.+?`)"
        segments = re.split(code_block_pattern, text)

        translated_segments = []
        for segment in segments:
            if re.match(code_block_pattern, segment):
                translated_segments.append(segment)
            else:
                translated_segments.append(
                    GoogleTranslator(source="auto", target=target_lang).translate(
                        segment
                    )
                )

        return "".join(translated_segments)
    except Exception as e:
        return f"Error in translation: {str(e)}"


def extract_language_from_mention(text):
    match = re.search(r"lang:(\w+)", text)
    if match:
        lang = match.group(1)
        text = re.sub(r"lang:\w+", "", text).strip()
    else:
        lang = "en"
    return lang, text


def extract_language_from_command(command):
    match = re.search(r"into\s+(\w+)", command, re.IGNORECASE)
    lang = match.group(1) if match else "en"
    return lang, command


def create_thread_title(text, max_length=100):
    words = text.split()
    title = " ".join(words[:10])
    if len(title) > max_length:
        title = title[: max_length - 3] + "..."
    return f"Translation: {title}"


@bot.command()
async def zap(ctx):
    embed = discord.Embed(
        title="👋 Zap Bot - How to Use Me!",
        description="Hey there! I'm your friendly translation buddy! Let's learn how to use me step by step! 🐾",
        color=discord.Color.blue(),
    )

    embed.add_field(
        name="1️⃣ Mention Me for Help!",
        value="Just mention me to translate something to English or any language you want! Easy peasy! 😄\n"
        "- Example: `@bot Hello, how are you?`\n"
        "- Or: `@bot lang:es Hello, how are you?` (This will translate to Spanish!)",
        inline=False,
    )

    embed.add_field(
        name="2️⃣ Reply with 'translate this'",
        value="Want me to translate a message you see? Just reply with 'translate this'! 🎯\n"
        "- Example: `translate this` (I'll guess the language!)\n"
        "- Or: `translate this into spanish` or `translate this into es` (I'll translate to Spanish!)",
        inline=False,
    )

    embed.add_field(
        name="3️⃣ Translate Your Own Message",
        value="You can also ask me to translate your own messages! ✨\n"
        "- Example: `translate this Hello, how are you?`\n"
        "- Or: `translate this into french Hello, how are you?` (I'll translate to French!)",
        inline=False,
    )

    embed.add_field(
        name="4️⃣ See All Languages I Know",
        value="Wanna know all the languages I can speak? Ask me! 🌍\n"
        "- Command: `!languages` (I'll show you a list of all supported languages!)",
        inline=False,
    )

    embed.set_footer(
        text="I'm always here to help you translate anything! 🌟 developed by: Adarsh Gourab Mahalik"
    )

    await ctx.send(
        embed=embed, ephemeral=True
    )  # Make the message visible only to the user


@bot.command()
async def languages(ctx):
    langs = GoogleTranslator().get_supported_languages(as_dict=True)
    lang_list = "\n".join([f"{code}: {name}" for code, name in langs.items()])

    # Create the embed with a brief introduction
    embed = discord.Embed(
        title="🌍 Languages I Can Speak!",
        description="Wow! I can translate into so many languages! 🎉 Check them out below:",
        color=discord.Color.green(),
    )

    embed.set_footer(
        text="Just tell me which language you want, and I'll do the magic! ✨"
    )

    # Send the embed
    await ctx.send(
        embed=embed, ephemeral=True
    )  # Make the message visible only to the user

    # Send the list of languages as a separate plain text message
    if len(lang_list) > 2000:  # Discord's character limit per message is 2000
        chunks = [lang_list[i : i + 2000] for i in range(0, len(lang_list), 2000)]
        for chunk in chunks:
            await ctx.send(f"```\n{chunk}\n```", ephemeral=True)
    else:
        await ctx.send(f"```\n{lang_list}\n```", ephemeral=True)


bot.run(os.getenv("DISCORD_TOKEN"))
