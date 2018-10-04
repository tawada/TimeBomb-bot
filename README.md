# timebomb-bot

Discordでタイムボムを遊ぶためのBotです.



ルールは[ここ](
http://sgrk.blog53.fc2.com/blog-entry-2905.html)とか[ここ](
https://intokubodoge.com/timebomb)を参考にしています.

---
## 実行方法
    $ git clone git@github.com:tawada/timebomb-bot.git
    $ cd timebomb-bot
    $ echo "token=XXXXXXXX"> data/config
    $ echo "game_channel=YYYYYYYY">> data/config
    $ make run

 * XXXXXXXXは[DEVELOPER PORTAL](https://discordapp.com/developers/applications/)から取得したTokenを入力してください.
 * YYYYYYYYはゲームをするチャンネルIDを入力してください.

---
## ゲーム開始方法
1. ゲームするチャンネルで1人が`ゲーム名`を言う
1. 各人が`参加`と言う
1. 1人が`開始`と言う

### 例
    太郎> タイムボム
    太郎> 参加
    次郎> 参加
    三郎> 参加
    四郎> 参加
    太郎> 開始
    GM> 参加者は4人です
