import discord
import random
import json
    
MODE_INIT      = 0
MODE_ACCEPTING = 1
MODE_GAMING    = 2
MODE_DEAD      = 3
MODE_STR       = ['初期状態', '参加者受付中', 'ゲーム中', 'Bot停止中']

STATE_NONE        = 0
STATE_WAIT_CARD   = 1
STATE_WAIT_NIPPER = 2
STATE_STR         = ['', '手札提出待ち', 'ニッパー係待ち']

TEAM_P = 0
TEAM_A = 1
TEAM_STR = ['タイムパトロール', 'ボムボム主義者']

CARD_NONE = 0
CARD_D    = 1
CARD_B    = 2
CARD_N    = 3
CARD_STR = ['', '解除', 'ボム', 'なにもなし']

END_DEFUSE = 0
END_BOOM   = 1
END_TIMEUP = 2

CONFIG_FILE = 'data/config.json'

FLEVOR = ['タイムパトロールは時を守っているんだ!',
          '***募集中****\nボムボム主義者は皆様のご参加をお待ちしております',
          'https://github.com/tawada/timebomb-bot にてBot開発中',
          '時を戻れたらキミはなにがしたいかい？',
          'おや、もうこんな時間か',
          'タイムイズマネー、時は金なり',
          'Botだってたまにはサボります',
          'ロボ・・・ロボ・・・',
          '「生きるんて、つらいなぁ」――未来を見通す賢者 ――',
          'タイムボムが爆発した！・・・ウソですよ（ハート）'
          ]

class TimeBombBot:
    """
    タイムボムを制御するBot
    """
    def __init__(self):
        with open('./data/config.json') as f:
            df = json.load(f)
        if 'token' not in df.keys() or 'game_channel' not in df.keys():
            self.mode = MODE_DEAD
            print('config file is unavailable')
            return
        self.token = df['token']
        self.game_channel_id = int(df['game_channel'])
#        self.game_channel_id = int(df['debug_channel'])
        self.mode = MODE_INIT
        self.state = STATE_NONE
        self.n_players = 0
        self.players = []
        self.player_channel = []
        self.players_team = []
        self.player_cards = []
        self.select_cards = []
        self.client = discord.Client()
        self.main_channel = discord.Object(id=self.game_channel_id)
        
    def run(self):
        """
        Botの実行
        """
        
        #Botの初期化に失敗していたらなにもしない
        if self.mode == MODE_DEAD:
            return
        
        #callback関数を定義
        @self.client.event
        async def on_message(message):
            await self.on_message(message)
        
        #callback関数を登録
        self.client.run(self.token)

    async def send_message(self, text, channel=None):
        """
        Discordに文字列を送信
        text: 送信したい文字列
        channel: 送信したいチャンネル, デフォルトはゲームのチャンネル
        """
        
        #デバッグ用, 送信文字列を表示
        print('send:{}'.format(text))
        
        #channelを省略するとデフォルトはゲームのチャンネル
        if channel == None:
            channel = self.main_channel
        await self.client.send_message(channel, text)
    
    async def on_message(self, message):
        """
        受信した文字列を解析してゲームを進める関数
        """
        
        #Bot自身の発言は解析しない
        if self.client.user == message.author:
            return
        
        author          = message.author
        author_name     = author.name
        author_channel  = await self.client.start_private_message(author)
        author_channel  = await self.client.start_private_message(author)
        message_channel = message.channel
        r_text          = message.content
        print('receive:{}'.format(r_text))
        
        if r_text.startswith('/'):
            if r_text.startswith('/player'):
                await self.send_message('{}'.format(self.players))
            elif r_text.startswith('/team'):
                await self.send_message('{}'.format(self.players_team))
            elif r_text.startswith('/card'):
                await self.send_message('{}'.format(self.player_cards))
                await self.send_message('{}'.format(self.select_cards))
            elif r_text.startswith('/state'):
                await self.send_message('mode:{}'.format(MODE_STR[self.mode]))
                await self.send_message('state:{}'.format(STATE_STR[self.state]))
            elif r_text.startswith('/all'):
                await self.send_message('{}'.format([p.name for p in self.players]))
                await self.send_message('{}'.format([TEAM_STR[t] for t in self.players_team]))
                await self.send_message('{}'.format([[CARD_STR[c] for c in p] for p in self.player_cards]))
                await self.send_message('{}'.format([CARD_STR[c] for c in self.select_cards]))
                await self.send_message('mode:{}'.format(MODE_STR[self.mode]))
                await self.send_message('state:{}'.format(STATE_STR[self.state]))
            return
        
        if self.mode == MODE_INIT:
            if int(message_channel.id) != int(self.main_channel.id):
                return
            if 'タイムボム' in r_text:
                self.mode = MODE_ACCEPTING
                s_text = 'タイムボムを開始します。\n' + '参加者は\'参加\'を宣言してください。'
                self.players = []
                await self.send_message(s_text)
                return
            elif '参加' in r_text or '開始' in r_text:
                s_text = 'ゲーム名を宣言してください。'
                await self.send_message(s_text)
            
        elif self.mode == MODE_ACCEPTING:
            if int(message_channel.id) != int(self.main_channel.id):
                return
            if '不参加' in r_text:
                if author in self.players:
                    self.players.remove(author)
                    s_text = '{}が参加を取りやめた．．．'.format(author_name)
                    await self.send_message(s_text)
            elif '参加' in r_text or 'さんか' in r_text:
                if author not in self.players:
                    self.players.append(author)
                    n = len(self.players)
                    s_text = '{}が参加した。\n'.format(author_name)
                    await self.send_message(s_text)
                    if n == 1:
                        s_text = '参加者がそろったら\'開始\'を宣言してください。'
                        await self.send_message(s_text)
                    elif n >= 4:
                        s_text = '\'開始\'を宣言してください。'
                        await self.send_message(s_text)
                else:
                    s_text = '{}はすでに参加しています。'.format(author_name)
                    await self.send_message(s_text)
            
            elif '開始' in r_text:
                n = len(self.players)
                s_text = 'ゲームを開始します。\n参加者は '
                for p in self.players:
                    s_text += p.name + ' '
                s_text += 'の{}人です。'.format(n)
                await self.send_message(s_text)
                
                self.defuse = 0
                
                #人数によってチーム編成
                if n in {1, 2, 3}:
                    p,a = 2,2
                elif n in {4, 5}:
                    p,a = 3,2
                elif n == 6:
                    p,a = 4,2
                elif n in {7, 8}:
                    p,a = 5,3
                else:
                    return
                
                T=([TEAM_P]*p)
                T.extend([TEAM_A]*a)
                random.shuffle(T)
                self.players_team = [T[i] for i in range(n)]
                self.select_cards = [CARD_NONE for i in range(n)]
                for i in range(n):
                    #private_channel = await self.client.start_private_message(self.players[i])
                    s_text = 'あなたは{}です'.format(TEAM_STR[self.players_team[i]])
                    #await self.send_message(s_text, private_channel)
                    await self.client.send_message(self.players[i], s_text)
                
                if n == p+a:
                    s_text = '{}が{}人、{}が{}人います。'.format(TEAM_STR[TEAM_P], p, TEAM_STR[TEAM_A], a)
                    await self.send_message(s_text)
                else:
                    s_text = '{}人の参加者に対して、{}のカードを{}枚、{}のカードを{}枚配っています。'.format(n, TEAM_STR[TEAM_P], p, TEAM_STR[TEAM_A], a)
                    await self.send_message(s_text)
                
                self.round = 1
                self.tern = 1
                self.nipper = random.randrange(n)
                                
                await self.start_round()
                await self.start_tern()
                self.mode = MODE_GAMING
                self.game_state = STATE_WAIT_CARD
                
        elif self.mode == MODE_GAMING:
            
            player_index = self.players.index(author)
            #ゲーム参加者以外は発言を解析しない
            if player_index == -1:
                s_text = '部外者は発言しないでください。'
                await self.send_message(s_text)
                return
            
            if self.game_state == STATE_WAIT_CARD:
                
                #ゲームチャンネルではカードを出せない
                if int(message_channel.id) == int(self.main_channel.id):
                    return
                
                if CARD_D in r_text:
                    card_index = CARD_D
                elif CARD_B in r_text:
                    card_index = CARD_B
                elif CARD_N in r_text:
                    card_index = CARD_A
                else:
                    return
                
                #ニッパー係はカードを出せない
                if self.nipper == player_index:
                    return
                
                self.player_cards[player_index].remove(card_index)
                self.select_cards[player_index] = card_index
                s_text = '{}の手札を場に出しました。'.format(CARD_STR[card_index])
                await self.send_message(s_text, message_channel)
                s_text = '{}が手札を場に出しました。'.format(author_name)
                await self.send_message(s_text)
                
                if CARD_NONE not in self.select_cards:
                    self.game_state = STATE_WAIT_NIPPER
                    s_text = '全員のカードが場に出ました。\nニッパー係は\'プレイヤー名\'を\'選択\'してください。'
                
            elif self.game_state == STATE_WAIT_NIPPER:
                if '選択' in r_text:
                    index = -1
                    for i in range(n):
                        if self.players[i].name in r_text:
                            index = i
                            break
                    if index == -1:
                        return
                    s_text = '{}のカードは...{}でした。'.format(self.players[index].name, CARD_STR[self.select_cards[index]])
                    await self.send_message(s_text, private_channel)
                    self.nipper = index
                    if self.select_cards[i] == CARD_B:
                        await self.end(END_BOOM)
                        return
                    elif self.select_cards[i] == CARD_D:
                        self.defuse += 1
                        if self.defuse == n:
                            await self.end(END_DEFUSE)
                            return
                        s_text = '現在の解除ポイントは{}点です。'.format(self.defuse)
                    if self.tern == n:
                        self.round += 1
                        self.tern = 1
                        if self.round == 4:
                            await self.end(END_TIMEUP)
                            return
                        await self.start_round()
                        return
                    else:
                        self.tern += 1
                        await self.start_tern()
                        return
            else:
                self.mode = MODE_INIT
                await self.send_message('Abort')
        else:
            return
    async def end(self, end_type):
        if end_type == END_DEFUSE:
            s_text  = 'タイムボムは無事に解除された。\n'
            s_text += '{}の勝利です！'.format(TEAM_STR[TEAM_P])
            await self.send_message(s_text)
            
        elif end_type == END_TIMEUP:
            s_text  = 'タイムボムは解除も爆発もおこさないまま時だけがすぎていった。\n'
            s_text += '{}の勝利です！'.format(TEAM_STR[TEAM_P])
            await self.send_message(s_text)
        elif end_type == END_BOOM:
            s_text  = 'タイムボムは爆発した！\n'
            s_text += '{}の勝利です！'.format(TEAM_STR[TEAM_A])
            await self.send_message(s_text)
        
        s_text = ''
        for i in range(len(self.players)):
            s_text += '{}：{}陣営\n'.format(self.players[i].name, self.TEAM_STR[self.players_team[i]])
        await self.send_message(s_text)
        
        self.mode = MODE_INIT
    
    async def start_round(self):
        n = len(self.players)
        #人数によって山札を変更
        if n in {1, 2}:
            Y=([CARD_D]*3)
            Y.extend([CARD_B])
            Y.extend([CARD_N]*11)
        else:
            Y=([CARD_D]*n)
            Y.extend([CARD_B])
            Y.extend([CARD_N]*(4*n-1))
        
        random.shuffle(Y)
        self.player_cards = []
        for i in range(n):
            #カードを5枚ずつ配る
            self.player_cards.append([Y[5*i+j] for j in range(5)])
                
    async def start_tern(self):
        n = len(self.players)
        s_text = 'ラウンド{} ターン{}\n'.format(self.round, self.tern)
        s_text +='ニッパー係は{}です。'.format(self.players[self.nipper].name)
        await self.send_message(s_text)
        for i in range(n):
            self.select_cards[i] = -1
#            private_channel = await self.client.start_private_message(self.players[i])
            s_text  = 'あなたの手札は '
            for j in range(6-self.tern):
               s_text += '{} '.format(CARD_STR[self.player_cards[i][j]])
            s_text += 'です。'
#            await self.send_message(s_text, private_channel)
            await self.client.send_message(self.players[i], s_text)
            
            if i == self.nipper:
                self.select_cards[i] = 0
                continue
            
            s_text = '場に出す手札を選んでください。'
            await self.client.send_message(self.players[i], s_text)
            
        if random.randrange(2) == 0:
            if FLEVOR == []:
                return
            s_text = '`{}`'.format(FLEVOR.pop(random.randrange(len(FLEVOR))))
            await self.send_message(s_text)

