# PrivateChart
## 概要
本リポジトリは
[FX-Note](https://github.com/h-akira/FX-Note)
の分割した後継リポジトリの一つであり，
Djangoを用いて為替関係の情報の取りまとめや振り返り
ができるWebアプリケーションを開発しているものである．
無料取得可能な為替関連データで商用利用可能等なものが多くはないため，
現段階で一般公開は想定せず個人または身内内での利用を前提として開発している．

## 機能
- 歴史的な相場や自身が大きな損失または利益を得た相場のチャートを保存する（メイン）
- 過去の相場を用いたデモトレード（引継によるおまけ）

## 備考
- 取引履歴の取得はGMOクリック証券のFXネオのみ対応し，Pythonスクリプトを実行してWEBスクレイビングにより行われる
- 上記の特性から複数のユーザーによる利用は想定していない（管理者のみ利用可能）
- チャートは`mplfinancd`を用いて画像として出力する

## 関連リポジトリ
- https://github.com/h-akira/FX-Note
- https://github.com/h-akira/ExchangeProject
- https://github.com/h-akira/ExchangeData
