import discord
import asyncio
from discord import app_commands
from discord.ext import commands
from youtube_dl import YoutubeDL

class InstagramButton(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.value = None
        self.timeout=600

        botaourl = discord.ui.Button(label="Segueaaa lá",url="https://www.instagram.com/kleuberserra/")
        self.add_item(botaourl)

class music(commands.Cog):
    def __init__(self, client):
        self.client = client
    
        #all the music related stuff
        self.is_playing = False

        # 2d array containing [song, channel]
        self.music_queue = []
        self.YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist':'True'}
        self.FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

        self.vc = ""

     #searching the item on youtube
    def search_yt(self, item):
        with YoutubeDL(self.YDL_OPTIONS) as ydl:
            try: 
                info = ydl.extract_info('ytsearch: {}'.format(item))['entries'][0]
            except Exception: 
                return False

        return {'source': info['formats'][0]['url'], 'title': info['title'], 'url': info['url']}

    def play_next(self):
        if len(self.music_queue) > 0:
            self.is_playing = True

            #get the first url
            m_url = self.music_queue[0][0]['source']

            #remove the first element as you are currently playing it
            self.music_queue.pop(0)

            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())
        else:
            self.is_playing = False

    # infinite loop checking 
    async def play_music(self):
        if len(self.music_queue) > 0:
            self.is_playing = True

            m_url = self.music_queue[0][0]['source']
            
            #try to connect to voice channel if you are not already connected

            if self.vc == "" or not self.vc.is_connected() or self.vc == None:
                self.vc = await self.music_queue[0][1].connect()
            else:
                await self.vc.move_to(self.music_queue[0][1])
            
            print(self.music_queue)
            #remove the first element as you are currently playing it
            self.music_queue.pop(0)

            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())
        else:
            self.is_playing = False
            await self.vc.disconnect()

    @app_commands.command(name="ajuda",description="Mostre um comando de ajuda.")
    async def help(self,interaction:discord.Interaction):
        await interaction.response.defer(thinking=True)
        helptxt = "`/ajuda` - Veja esse guia!\n`/play` - Toque uma música do YouTube!\n`/fila` - Veja a fila de músicas na Playlist\n`/pular` - Pule para a próxima música da fila"
        embedhelp = discord.Embed(
            colour = 1646116,#grey
            title=f'Comandos do {self.client.user.name}',
            description = helptxt
        )
        try:
            embedhelp.set_thumbnail(url=self.client.user.avatar.url)
        except:
            pass
        msg = await interaction.followup.send(embed=embedhelp)
        await asyncio.sleep(60)
        await msg.delete()


    @app_commands.command(name="play",description="Toca uma música do YouTube.")
    @app_commands.describe(
        busca = "Digite o nome da música no YouTube"
    )

    async def play(self, interaction:discord.Interaction,busca:str):
        await interaction.response.defer(thinking=True)
        query = busca
        
        try:
            voice_channel = interaction.user.voice.channel
        except:
        #if voice_channel is None:
            #you need to be connected so that the bot knows where to go
            embedvc = discord.Embed(
                colour= 1646116,#grey
                description = 'Para tocar uma música, primeiro se conecte a um canal de voz.'
            )
            msg = await interaction.followup.send(embed=embedvc)
            await asyncio.sleep(60)
            await msg.delete()
            return
        else:
            song = self.search_yt(query)
            if type(song) == type(True):
                embedvc = discord.Embed(
                    colour= 12255232,#red
                    description = 'Algo deu errado! Tente mudar ou configurar a playlist/vídeo ou escrever o nome dele novamente!'
                )
                msg = await interaction.followup.send(embed=embedvc)
                await asyncio.sleep(60)
                await msg.delete()
            else:
                embedvc = discord.Embed(
                    colour= 32768,#green
                    description = f"Você adicionou a música **{song['title']}** à fila!"
                )

                msg = await interaction.followup.send(embed=embedvc)
                self.music_queue.append([song, voice_channel])
                await asyncio.sleep(60)
                await msg.delete()
                
                if self.is_playing == False:
                    await self.play_music()

    @app_commands.command(name="fila",description="Mostra as atuais músicas da fila.")
    async def q(self, interaction:discord.Interaction):
        await interaction.response.defer(thinking=True)
        retval = ""
        for i in range(0, len(self.music_queue)):
            retval += f'**{i+1} - **' + self.music_queue[i][0]['title'] + "\n"

        print(retval)
        if retval != "":
            embedvc = discord.Embed(
                colour= 12255232,
                description = f"{retval}"
            )
            msg = await interaction.followup.send(embed=embedvc)
            await asyncio.sleep(60)
            await msg.delete()
        else:
            embedvc = discord.Embed(
                colour= 1646116,
                description = 'Não existe músicas na fila no momento.'
            )
            msg = await interaction.followup.send(embed=embedvc)
            await asyncio.sleep(60)
            await msg.delete()


    @app_commands.command(name="pular",description="Pula a atual música que está tocando.")
    @app_commands.default_permissions(manage_channels=True)
    async def pular(self, interaction:discord.Interaction):
        await interaction.response.defer(thinking=True)
        if self.vc != "" and self.vc:
            self.vc.stop()
            #try to play next in the queue if it exists
            await self.play_music()
            embedvc = discord.Embed(
                colour= 1646116,#ggrey
                description = f"Você pulou a música."
            )
            msg = await interaction.followup.send(embed=embedvc)
            await asyncio.sleep(60)
            await msg.delete()

    @pular.error #Erros para kick
    async def skip_error(self,interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, commands.MissingPermissions):
            embedvc = discord.Embed(
                colour= 12255232,
                description = f"Você precisa da permissão **Gerenciar canais** para pular músicas."
            )
            msg = await interaction.followup.send(embed=embedvc)    
            await asyncio.sleep(60)
            await msg.delete() 
        else:
            raise error

async def setup(client):
    await client.add_cog(music(client))
    