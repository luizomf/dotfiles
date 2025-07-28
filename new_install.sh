#!/bin/bash

# função para printar loginfos de forma legível
loginfo() {
  echo -e "
🔵 [1;34m$1[0m"
}

logsuccess() {
  echo -e "
🟢 [1;32m$1[0m"
}

logerror() {
  echo -e "
🔴 [1;31m$1[0m"
}

# garante que o script pare em caso de erro
set -e

OP_SYSTEM=""

if [ "$(uname -s)" == "Linux" ]; then
    echo "This system is Linux."
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        if [ "$ID" == "ubuntu" ]; then
            OP_SYSTEM="ubuntu"
        else
            logerror "This is another Linux distribution: $PRETTY_NAME"
        fi
    elif command -v lsb_release &> /dev/null; then
        if lsb_release -d | grep -q "Ubuntu"; then
            OP_SYSTEM="ubuntu"
        fi
    fi
elif [ "$(uname -s)" == "Darwin" ]; then 
  OP_SYSTEM="darwin"
else
  logerror "It is not safe to run this script on your system."
  exit 1
fi

if [[ "$OP_SYSTEM" == "darwin" ]]; then
  loginfo "mac os"
elif [[ "$OP_SYSTEM" == "ubuntu" ]]; then

  loginfo "Your system is Ubuntu, updating packages..."
  sudo apt update -y
  sudo apt upgrade -y

  loginfo "Installing ZSH..."
  sudo apt install zsh
  sudo chsh -s /usr/bin/zsh

else
  logerror "Wrong system, sorry!"
  exit 1
fi

