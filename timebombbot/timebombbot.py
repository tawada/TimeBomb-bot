import discord
import random
import json
import asyncio
    
GAME_NONE = 0
GAME_TIMEBOMB = 1
GAME_ONENIGHTWEREWOLF = 2
GAME_TIMER = 3
GAME_STR = ['', 'タイムボム', 'ワンナイト人狼', 'タイマー']

MODE_INIT      = 0
MODE_ACCEPTING = 1
MODE_GAMING    = 2
MODE_DEAD      = 3
MODE_STR       = ['初期状態', '参加者受付中', 'ゲーム中', 'Bot停止中']

STATE_NONE        = 0
STATE_WAIT_CARD   = 1
STATE_WAIT_NIPPER = 2
STATE_STR         = ['', '手札提出待ち', 'ニッパー係待ち']

STATE_SEE = 1
STATE_TALKING = 2
STATE_VOTE = 3

TEAM_P = 0
TEAM_A = 1
TEAM_STR = ['タイムパトロール', 'ボムボム主義者']

CARD_NONE = 0
CARD_D    = 1
CARD_B    = 2
CARD_N    = 3
CARD_STR = ['', '解除', 'ボム', 'なにもなし']

CARD_WEREWOLF = 1
CARD_SEER     = 2
CARD_THIEF    = 3
CARD_VILLAGER = 4
CARDo_STR = ['', '人狼', '占い師', '怪盗', '村人']

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
          '古来より時を狙う集団は多い。かくいう私もね・・・。',
          '爆弾作りは繊細さが命！タイムボムが誤爆すると作り始める前に戻ってしまうのさ。',
          'ボクはボムボム、キミもボムボム？',
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
        self.game = GAME_NONE
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
        if hasattr(dst, 'display_name') and dst.display_name.startswith('ロボ'):
            text = '(ロボたわわ->{})「{}」'.format(dst.display_name, text)
            dst = self.main_channel
        await self.client.send_message(dst, text)

    class dummy:
        def __init__(self):
            self.author       = None
            self.name         = None
            self.display_name = None
            self.channel      = None
            self.content      = None
            self.attachments  = False
    async def on_message(self, message):
        """
        受信した文字列を解析してゲームを進める関数
        """
        
        #Bot自身の発言は解析しない
        if self.client.user == message.author:
            return
        #ファイル送信には反応しない
        if message.attachments:
            return
        
        author          = message.author
        author_name     = author.display_name
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
                await self.send_message('プレイヤー：{}'.format([p.display_name for p in self.players]))
                await self.send_message('チーム：{}'.format([TEAM_STR[t] for t in self.players_team]))
                await self.send_message('手札：{}'.format([[CARD_STR[c] for c in p] for p in self.player_cards]))
                await self.send_message('mode:{}'.format(MODE_STR[self.mode]))
            elif r_text.startswith('/dm'):
                await self.send_message('DM Test', author)
            elif r_text.startswith('/reset'):
                self.mode = MODE_INIT
                return
            elif r_text.startswith('/say'):
                command, player, s_text = r_text.split()
                if '茶' not in player:
                    await self.send_message('不正なプレイヤー名です。')
                    return
                dummy_message                     = self.dummy()
                dummy_message.author              = self.dummy()
                dummy_message.author.name         = player
                dummy_message.author.display_name = 'ロボ' + player
                dummy_message.channel             = self.main_channel
                dummy_message.content             = s_text
                await self.send_message('{}「{}」'.format(dummy_message.author.display_name, s_text))
                await self.on_message(dummy_message)
                return
            return
        
        if self.mode == MODE_INIT:
            if int(message_channel.id) != int(self.main_channel.id):
                return
            if 'タイムボム' in r_text:
                self.game = GAME_TIMEBOMB
                self.mode = MODE_ACCEPTING
                s_text = '`タイムボム`を開始します。\n' + '参加者は`参加`を宣言してください。'
                self.players = []
                await self.send_message(s_text)
                return
            elif 'ワンナイト' in r_text or 'ワンナイト人狼' in r_text:
                self.game = GAME_ONENIGHTWEREWOLF
                self.mode = MODE_ACCEPTING
                s_text = '`ワンナイト人狼`を開始します。\n' + '参加者は`参加`を宣言してください。'
                self.players = []
                await self.send_message(s_text)
                return
            elif 'タイマー' in r_text:
                self.game = GAME_TIMER
                self.mode = MODE_ACCEPTING
                s_text = '`タイマー`を開始します。'
                self.players = []
                await self.send_message(s_text)
                await self.start_timer()
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
                    s_text = '`{}`が参加を取りやめた．．．'.format(author_name)
                    await self.send_message(s_text)
            elif '参加' in r_text or 'さんか' in r_text:
                if author not in self.players:
                    self.players.append(author)
                    n = len(self.players)
                    s_text = '`{}`が参加した。\n'.format(author_name)
                    await self.send_message(s_text)
                    if n == 1:
                        s_text = '参加者がそろったら`開始`を宣言してください。'
                        await self.send_message(s_text)
                    elif n >= 4:
                        s_text = '`開始`を宣言してください。\n現在の参加者は{}人です。'.format(n)
                        await self.send_message(s_text)
                else:
                    s_text = '{}はすでに参加しています。'.format(author_name)
                    await self.send_message(s_text)
            
            elif '開始' in r_text:
                if self.game == GAME_TIMEBOMB:
                    await self.start_game_timebomb()
                elif self.game == GAME_ONENIGHTWEREWOLF:
                    await self.start_game_onenightwerewolf()
                else:
                    return
        elif self.mode == MODE_GAMING:
            if self.game == GAME_ONENIGHTWEREWOLF:
                await self.gaming_onenightwerewolf(message)
                return
            n = len(self.players)
            if int(message_channel.id) != int(self.main_channel.id):
                return
            
            player_index = -1
            for i in range(n):
                if self.players[i].name == author.name:
                    player_index = i
                    break
            
            #ゲーム参加者以外は発言を解析しない
            if player_index == -1:
                s_text = '部外者は発言しないでください。'
                await self.send_message(s_text)
                return
            
            if self.state == STATE_WAIT_NIPPER:
                
                #ニッパー係の発言のみ解析
                if player_index != self.nipper:
                    return
                
                if '選択' in r_text:
                    index = -1
                    r_text_lower = r_text.lower()
                    for i in range(n):
                        if self.players[i].name.lower() in r_text_lower or self.players[i].display_name.lower() in r_text_lower:
                            index = i
                            break
                    #ニッパー係自身は対象としない
                    if index == -1 or index == self.nipper:
                        return
                        
                    if self.player_cards[index] == []:
                        s_text = '`{}`のカードはありません！'.format(self.players[index].display_name)
                        await self.send_message(s_text)
                        return
                    
                    select_index = random.randrange(len(self.player_cards[index]))
                    select_card  = self.player_cards[index].pop(select_index)
                    
                    s_text = '`{}`のカードをめくります。\nめくったカードは...`{}`でした。'.format(self.players[index].display_name, CARD_STR[select_card])
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
            s_text += '{}：{}陣営\n'.format(self.players[i].display_name, TEAM_STR[self.players_team[i]])
        await self.send_message(s_text)
        
        self.mode = MODE_INIT
    
    async def start_game_timebomb(self):
                n = len(self.players)
                s_text = 'ゲームを開始します。\n参加者は '
                for p in self.players:
                    s_text += '`{}` '.format(p.display_name)
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
                self.state = STATE_WAIT_NIPPER

    async def wait_5m(self):
        for i in range(5, 1, -1):
            s_text = '残り{}分'.format(i)
            await self.send_message(s_text)
            for _ in range(60):
                if self.nowait:
                    return
                await asyncio.sleep(1)
        s_text = '残り{}分'.format(1)
        await self.send_message(s_text)
        for _ in range(30):
            if self.nowait:
                return
            await asyncio.sleep(1)
        s_text = '残り{}秒'.format(30)
        await self.send_message(s_text)
        for _ in range(30):
            if self.nowait:
                return
            await asyncio.sleep(1)

    async def start_game_onenightwerewolf(self):
        n = len(self.players)
        if n not in {4, 5}:
            s_text = '{}人には対応していません'.format(n)
            await self.send_message(s_text)
            return
        Y = []
        Y.extend([CARD_WEREWOLF]*2)
        Y.extend([CARD_SEER])
        Y.extend([CARD_THIEF])
        Y.extend([CARD_VILLAGER]*2)
        self.player_cards = []
        team_werewolf = []
        team_seer = []
        team_thief = []
        random.shuffle(Y)
        for i in range(n):
            card = Y.pop(0)
            self.player_cards.append(card)
            if card == CARD_WEREWOLF:
                team_werewolf.append(i)
            elif card == CARD_SEER:
                team_seer.append(i)
            elif card == CARD_THIEF:
                team_thief.append(i)
        self.mode = MODE_GAMING
        self.state = STATE_SEE
        self.seer_to = -1
        self.thief_to = -1
        
        for i in range(n):
            card = self.player_cards[i]
            s_text = 'あなたは`{}`です。'.format(CARDo_STR[card])
            if card == CARD_WEREWOLF:
                if len(team_werewolf) == 1:
                    s_text += '\n仲間はいないようです。'
                else:
                    s_text += '\n`{}`が仲間のようです。'.format(
                        self.players[ team_werewolf[0]  if team_werewolf[0] != i                        else team_werewolf[1] ].display_name)
            elif card == CARD_SEER:
                s_text += '\n占い先を`選択`してください。'
                s_text += '\n制限時間内に`選択`しない場合は配布されていない役職がわかります。\n'
                for j in range(n):
                    if i != j:
                        s_text += '`{}` '.format(self.players[j].display_name)
                s_text += 'から`選択`してください。'
            elif card == CARD_THIEF:
                s_text += '\n交換先を`選択`してください。'
                s_text += '\n制限時間内に`選択`しない場合は役職を交換しません。\n'
                for j in range(n):
                    if i != j:
                        s_text += '`{}` '.format(self.players[j].display_name)
                s_text += 'から`選択`してください。'
            await self.send_message(s_text, self.players[i])
        s_text = '自分の役職を確認してください。'
        await self.send_message(s_text)
        s_text = '残り{}秒'.format(30)
        await self.send_message(s_text)
        await asyncio.sleep(25)
        for i in range(5, 0, -1):
            s_text = '残り{}秒'.format(i)
            await self.send_message(s_text)
            await asyncio.sleep(1)
        
        self.state = STATE_TALKING
        
        if team_seer != []:
            if self.seer_to == -1:
                s_text = 'この村には '
                for card in Y:
                    s_text += '`{}` '.format(CARDo_STR[card])
                s_text += 'が欠けています。'
                await self.send_message(s_text, self.players[team_seer[0]])
            else:
                s_text = '`{}` はどうやら `{}` です。'.format(self.players[self.seer_to].display_name, CARDo_STR[self.player_cards[self.seer_to]])
                await self.send_message(s_text, self.players[team_seer[0]])
        if team_thief != []:
            if self.thief_to == -1:
                s_text = '役職を交換しませんでした。'
                await self.send_message(s_text, self.players[team_thief[0]])
            else:
                s_text = '`{}` と交換してあなたは `{}` になりました。'.format(self.players[self.thief_to].display_name, CARDo_STR[self.player_cards[self.thief_to]])
                await self.send_message(s_text, self.players[team_thief[0]])
            
        s_text = 'それでは話し合いを始めてください。'
        await self.send_message(s_text)

        self.nowait = False
        await self.wait_5m()
        
        self.vote = [-1]*n
        self.state = STATE_VOTE
        s_text = 'それでは投票です。'
        await self.send_message(s_text)
        
        for i in range(len(self.players)):
            s_text = '吊りたい相手を`選択`してください。'
            await self.send_message(s_text, self.players[i])

    def get_player_index(self, author):
        for i in range(len(self.players)):
            if self.players[i].name == author.name:
                return i
        return -1
        
    def get_index(self, r_text):
        for i in range(len(self.players)):
            if self.players[i].name in r_text:
                return i
            elif self.players[i].display_name in r_text:
                return i
        return -1

    async def gaming_onenightwerewolf(self, message):
        if message.author.name not in [p.name for p in self.players]:
            # 参加者以外の発言は解析しない
            return
        r_text          = message.content
        if self.state == STATE_SEE:
            # 占い・怪盗のターン
#            private_channel = await self.client.start_private_message(message.author)
#            if int(message.channel.id) != int(private_channel.id):
#                # プライベート発言以外は解析しない
#                return
            if '選択' not in r_text:
                return
            index = self.get_index(r_text)
            if index == -1:
                return
            if self.players[index].name == message.author.name:
                # 発言者自身は選択できない
                return
            player_index = self.get_player_index(message.author)
            if self.player_cards[player_index] == CARD_SEER and self.seer_to == -1:
                self.seer_to = index
                s_text = '`{}`を占います。'.format(self.players[index].display_name)
                await self.send_message(s_text)
            elif self.player_cards[player_index] == CARD_THIEF and self.thief_to == -1:
                self.thief_to = index
                s_text = '`{}`と交換します。'.format(self.players[index].display_name)
                await self.send_message(s_text)
            return
        elif self.state == STATE_TALKING:
            if r_text.startswith('@投票'):
                self.nowait = True
            return
        elif self.state == STATE_VOTE:
#            private_channel = await self.client.start_private_message(message.author)
#            if int(message.channel.id) != int(private_channel.id):
#                # プライベート発言以外は解析しない
#                return
            if r_text.startswith('@アクション'):
                s_text = ''
                for i in range(len(self.players)):
                    if self.vote[i] == -1:
                        s_text += '`{}` '.format(self.players[i].display_name)
                s_text += 'が投票していません。'
                await self.send_message(s_text)
                return
            if '選択' not in r_text and '投票' not in r_text:
                return
            index = self.get_index(r_text)
            if index == -1:
                return
            if self.players[index].name == message.author.name:
                # 発言者自身は選択できない
                return
            player_index = self.get_player_index(message.author)
            if self.vote[player_index] != -1:
                return
            self.vote[player_index] = index
            s_text = '`{}` に投票しました。'.format(self.players[index].display_name)
            await self.send_message(s_text, message.author)
            if self.vote.count(-1) == 0:
                await self.end_onenightwerewolf()
            return
        return

    async def end_onenightwerewolf(self):
        n = len(self.players)
        count_vote = {i:0 for i in range(n)}
        for v in self.vote:
            count_vote[v] += 1
        count_vote_tuple = sorted(count_vote.items(), key=lambda x: -x[1])
        s_text = ''
        for k,v in count_vote_tuple:
            s_text += '`{}` に{}人投票\n'.format(self.players[k].display_name, v)
        await self.send_message(s_text)
        
        if (len(count_vote_tuple)) == 1 or count_vote_tuple[0][1] != count_vote_tuple[1][1]:
            index = count_vote_tuple[0][0]
            s_text = '`{}` が吊られた。'.format(self.players[index].display_name)
            await self.send_message(s_text)
        
            if self.player_cards[index] == CARD_WEREWOLF and self.thief_to != index:
                s_text = '`{}` は`{}`だった。\n人間の勝利です！'.format(self.players[index].display_name, CARDo_STR[CARD_WEREWOLF])
                await self.send_message(s_text)
            else:
                s_text = '`{}` は`{}`だった。\n人間の敗北です！'.format(self.players[index].display_name, CARDo_STR[self.player_cards[index]])
                await self.send_message(s_text)
        else:
            s_text = '得票が同数のため, 平和裁判でした。'
            if self.player_cards.count(CARD_WEREWOLF) == 0:
                s_text += '\nこの村に `{}` はいませんでした。\n人間の勝利です！'.format(CARDo_STR[CARD_WEREWOLF])
            else:
                s_text += '\nこの村に潜む `{}` に人間は食い尽くされました。\n `{}`の勝利です！'.format(CARDo_STR[CARD_WEREWOLF], CARDo_STR[CARD_WEREWOLF])
            await self.send_message(s_text)
            
        s_text = ''
        for i in range(len(self.players)):
            s_text += '`{}`：`{}`\n'.format(self.players[i].display_name, CARDo_STR[self.player_cards[i]])
        await self.send_message(s_text)
        
        self.game = GAME_NONE
        self.mode = MODE_INIT

    async def start_timer(self):
        for i in range(1,5):
            await asyncio.sleep(1)
            s_text = '{}秒経過'.format(i)
            await self.send_message(s_text)
        await asyncio.sleep(1)
        s_text = '{}秒タイマーでしたー'.format(5)
        await self.send_message(s_text)
        self.game = GAME_NONE
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
        for i in range(n):
            s_text  = 'あなたの手札は '
            if self.player_cards[i] == []:
                s_text += 'ありません。'
            else:
                for c in self.player_cards[i]:
                    s_text += '`{}` '.format(CARD_STR[c])
                s_text += 'です。'
            await self.send_message(s_text, self.players[i])
        s_text = '*新しいラウンドの開始です！*\nカードを配りました。'
        await self.send_message(s_text)
        
    async def start_tern(self):
        """
        ターンの開始処理
        """
        n = len(self.players)
        s_text = '\n\n**ラウンド{} ターン{}**\n'.format(self.round, self.tern)
        if self.defuse!=0:
            s_text += '現在の解除ポイントは`{}`点です。\n'.format(self.defuse)
        s_text += 'ニッパー係は`{}`です。\n'.format(self.players[self.nipper].display_name)
        s_text += 'ニッパー係は`プレイヤー名`を`選択`してください。'
        await self.send_message(s_text)
        
        if random.randrange(10) == 0:
            if FLEVOR == []:
                return
            s_text = '`{}`'.format(FLEVOR.pop(random.randrange(len(FLEVOR))))
            await self.send_message(s_text)

