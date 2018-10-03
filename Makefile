#USER DEFINITION
FILENAME  := program
REPOSITORY:= git@github.com:tawada/timebomb-bot.git

TARGET      = data/data_file.csv 
CONFIG      = data/config.json
.PHONY : run clean git_init git_update tree

GCC         = gcc
PYTHON      = python3
TIME        = time
DATE        = date
GIT         = git

P_FILE      = $(FILENAME).py
C_FILE      = $(FILENAME).c
EXE_FILE    = $(FILENAME).exe

HOSTNAME    = $(shell hostname|awk -F'[.]' '{print $$1;}')
HOUR        = $(shell date "+%H")

define GIT_INIT
	$(GIT) remote add origin $(REPOSITORY)
	$(GIT) push -u origin master
endef
define GIT_UPDATE
	$(GIT) commit -a -m 'Update $(HOSTNAME)'
	$(GIT) push origin $(HOSTNAME)
endef
define GIT_TREE
	$(GIT) log --graph --all --format="%x09%C(cyan bold)%an%Creset%x09%C(yellow)%h%Creset %C(magenta reverse)%d%Creset %s"
endef

run:$(P_FILE) $(TARGET)
	$(PYTHON) $< $(HOUR)
#	git commit -a -m 'Daily update'
#	git push origin auto

$(EXE_FILE):$(C_FILE)
	gcc -o $@ $^ -std=c99

tree:
	$(GIT_TREE)

clean:
	rm *.csv

# dst := src
# With ':=' dst is instantly substituted of src.
# dst  = src
# With '=' dst is substituted of src when it runs.


# target.out: file1 file2
#    exe
#
# $@ == target.out
# $% ???
# $< == file1
# $? ???
# $^ == file1 file2
# $+ ???
# $* == target

#$@ : ターゲットファイル名
#$% : ターゲットがアーカイブメンバだったときのターゲットメンバ名
#$< : 最初の依存するファイルの名前
#$? : ターゲットより新しいすべての依存するファイル名
#$^ : すべての依存するファイルの名前
#$+ : Makefileと同じ順番の依存するファイルの名前
#$* : サフィックスを除いたターゲットの名前
#参照：http://www.jsk.t.u-tokyo.ac.jp/~k-okada/makefile/
