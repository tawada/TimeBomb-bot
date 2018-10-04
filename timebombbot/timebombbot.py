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
        self.players = []
        self.players_team = []
        self.player_cards = []
        self.total_cards = []
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

    async def send_message(self, text, dst=None):
        """
        Discordに文字列を送信
        text: 送信したい文字列
        dst: 送信したいチャンネル, 相手, デフォルトはゲームのチャンネル
        """
        
        #デバッグ用, 送信文字列を表示
        print('send:{}'.format(text))
        
        #dstを省略するとデフォルトはゲームのチャンネル
        if dst == None:
            dst = self.main_channel
        if hasattr(dst, 'name') and dst.name.startswith('ロボ'):
            text = '{}({})'.format(text, dst.name)
            dst = self.main_channel
        await self.client.send_message(dst, text)

    class dummy:
        def __init__(self):
            self.author       = None
            self.name         = None
            self.display_name = None
            self.channel      = None
            self.content      = None

    async def on_message(self, message):
        """
        受信した文字列を解析してゲームを進める関数
        """
        
        #Bot自身の発言は解析しない
        if self.client.user == message.author:
            return
        
        author          = message.author
        author_name     = author.name
        #author_channel  = await self.client.start_private_message(author)
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
            elif r_text.startswith('/state'):
                await self.send_message('mode:{}'.format(MODE_STR[self.mode]))
                await self.send_message('state:{}'.format(STATE_STR[self.state]))
            elif r_text.startswith('/all'):
                await self.send_message('プレイヤー：{}'.format([p.name for p in self.players]))
                await self.send_message('チーム：{}'.format([TEAM_STR[t] for t in self.players_team]))
                await self.send_message('手札：{}'.format([[CARD_STR[c] for c in p] for p in self.player_cards]))
                await self.send_message('mode:{}'.format(MODE_STR[self.mode]))
                await self.send_message('state:{}'.format(STATE_STR[self.state]))
            elif r_text.startswith('/say'):
                command, player, s_text = r_text.split()
                if '茶' not in player:
                    await self.send_message('不正なプレイヤー名です。')
                    return
                dummy_message                     = self.dummy()
                dummy_message.author              = self.dummy()
                dummy_message.author.name         = 'ロボ' + player
                dummy_message.author.display_name = player
                dummy_message.channel             = self.main_channel
                dummy_message.content             = s_text
                await self.send_message('{}「{}」'.format(dummy_message.author.name, s_text))
                await self.on_message(dummy_message)
                return
            return
        
        if self.mode == MODE_INIT:
            if int(message_channel.id) != int(self.main_channel.id):
                return
            if 'タイムボム' in r_text:
                self.mode = MODE_ACCEPTING
                s_text = 'タイムボムを開始します。\n' + '参加者は`参加`を宣言してください。'
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
                        s_text = '参加者がそろったら`開始`を宣言してください。'
                        await self.send_message(s_text)
                    elif n >= 4:
                        s_text = '`開始`を宣言してください。'
                        await self.send_message(s_text)
                else:
                    s_text = '{}はすでに参加しています。'.format(author_name)
                    await self.send_message(s_text)
            
            elif '開始' in r_text:
                n = len(self.players)
                s_text = 'ゲームを開始します。\n参加者は '
                for p in self.players:
                    s_text += '`{}` '.format(p.name)
                s_text += 'の{}人です。'.format(n)
                await self.send_message(s_text)
                
                #ゲーム内変数の初期化
                self.state = STATE_NONE
                self.players_team = []
                self.player_cards = []
                self.total_cards = []
                
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
                for i in range(n):
                    s_text = 'あなたは`{}`です'.format(TEAM_STR[self.players_team[i]])
                    await self.send_message(s_text, self.players[i])
                
                if n == p+a:
                    s_text = '{}が{}人、{}が{}人います。'.format(TEAM_STR[TEAM_P], p, TEAM_STR[TEAM_A], a)
                    await self.send_message(s_text)
                else:
                    s_text = '{}人の参加者に対して、{}のカードを{}枚、{}のカードを{}枚配っています。'.format(n, TEAM_STR[TEAM_P], p, TEAM_STR[TEAM_A], a)
                    await self.send_message(s_text)
                
                self.round = 1
                self.tern = 1
                self.nipper = random.randrange(n)
                
                #人数によって山札を変更
                if n in {1, 2}:
                    Y=([CARD_D]*3)
                    Y.extend([CARD_B])
                    Y.extend([CARD_N]*11)
                else:
                    Y=([CARD_D]*n)
                    Y.extend([CARD_B])
                    Y.extend([CARD_N]*(4*n-1))
                self.total_cards = Y
                
                await self.start_round()
                await self.start_tern()
                self.mode = MODE_GAMING
                self.game_state = STATE_WAIT_NIPPER
                
        elif self.mode == MODE_GAMING:
            n = len(self.players)
            if int(message_channel.id) != int(self.main_channel.id):
                return
            
            player_index = -1
            for i in range(n):
                if self.players[i].name == author.name:
                    player_index = i
                    break
            print(player_index)
            #ゲーム参加者以外は発言を解析しない
            if player_index == -1:
                s_text = '部外者は発言しないでください。'
                await self.send_message(s_text)
                return
            
            if self.game_state == STATE_WAIT_NIPPER:
                
                #ニッパー係の発言のみ解析
                if player_index != self.nipper:
                    return
                
                if '選択' in r_text:
                    index = -1
                    for i in range(n):
                        if self.players[i].name in r_text or self.players[i].display_name:
                            index = i
                            break
                    if index == -1:
                        return
                        
                    if self.player_cards[index] == []:
                        s_text = '`{}`のカードはありません！'.format(self.players[index].name)
                        await self.send_message(s_text)
                        return
                    
                    select_index = random.randrange(len(self.player_cards[index]))
                    select_card  = self.player_cards[index].pop(select_index)
                    s_text = '`{}`のカードをめくります。\nめくったカードは...`{}`でした。'.format(self.players[index].name, CARD_STR[select_card])
                    await self.send_message(s_text)
                    
                    self.nipper = index
                    
                    s_text = ''
                    if select_card == CARD_B:
                        await self.end(END_BOOM)
                        return
                    elif select_card == CARD_D:
                        self.defuse += 1
                        if self.defuse == n:
                            await self.end(END_DEFUSE)
                            return
                    
                    if self.tern == n:
                        self.round += 1
                        self.tern = 1
                        if self.round == 5:
                            await self.end(END_TIMEUP)
                            return
                        
                        #使っていないカードを山札に回収
                        self.total_cards = []
                        for pc in self.player_cards:
                            self.total_cards.extend(pc)
                        await self.start_round()
                        await self.start_tern()
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
            s_text  = '解除が間に合わずタイムボムは爆発した！\n'
            s_text += '{}の勝利です！'.format(TEAM_STR[TEAM_A])
            await self.send_message(s_text)
            
        elif end_type == END_BOOM:
            s_text  = 'タイムボムは爆発した！\n'
            s_text += '{}の勝利です！'.format(TEAM_STR[TEAM_A])
            await self.send_message(s_text)
        
        s_text = ''
        for i in range(len(self.players)):
            s_text += '{}：{}陣営\n'.format(self.players[i].name, TEAM_STR[self.players_team[i]])
        await self.send_message(s_text)
        
        self.mode = MODE_INIT
    
    async def start_round(self):
        """
        ラウンドの開始処理
        """
        n = len(self.players)
        Y = self.total_cards
        random.shuffle(Y)
        self.player_cards = []
        
        m = 6-self.round
        for i in range(n):
            #カードを配る
            self.player_cards.append([Y[m*i+j] for j in range(m)])
    
    async def start_tern(self):
        """
        ターンの開始処理
        """
        n = len(self.players)
        s_text = '\n**ラウンド{} ターン{}**\n'.format(self.round, self.tern)
        if self.defuse!=0:
            s_text += '現在の解除ポイントは`{}`点です。\n'.format(self.defuse)
        s_text += 'ニッパー係は`{}`です。\n'.format(self.players[self.nipper].name)
        s_text += 'ニッパー係は`プレイヤー名`を`選択`してください。'
        await self.send_message(s_text)
        for i in range(n):
            s_text  = 'あなたの手札は '
            if self.player_cards[i] == []:
                s_text += 'ありません。'
            else:
                for c in self.player_cards[i]:
                    s_text += '`{}` '.format(CARD_STR[c])
                s_text += 'です。'
            await self.send_message(s_text, self.players[i])
        
        if random.randrange(10) == 0:
            if FLEVOR == []:
                return
            s_text = '`{}`'.format(FLEVOR.pop(random.randrange(len(FLEVOR))))
            await self.send_message(s_text)

