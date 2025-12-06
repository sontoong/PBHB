if ! pidof firefox >/dev/null;
then
    firefox &>/dev/null &
else
    echo "Firefox already running"
fi

cd /projects/bh-bot
venv-linux/bin/python3 -m bh_bot