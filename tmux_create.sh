#!/bin/sh

sudo tmux -S /tmp/pinball new-session -d -s $1

tmux selectp -t 1
tmux splitw -h -p 50
tmux splitw -v -p 50

tmux selectp -t 2
tmux splitw -h -p 50
tmux splitw -v -p 50

tmux selectp -t 3
tmux splitw -h -p 50
tmux splitw -v -p 50

tmux selectp -t 4
tmux splitw -h -p 50


# Split pane 1 horizontal by 65%, start redis-server
tmux send-keys "python poster.py" C-m
