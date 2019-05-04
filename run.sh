#!/usr/bin/env bash
root=$(cd `dirname $0`; pwd)
echo $root
cd $root

# crawl
cd robot/rss
sh run.sh

# gen index
cd $root
cd analysis
python man_text.py

# gen rec
cd $root
cd recommend
python train.py
python rec.py