#!/usr/bin/env bash
root=$(cd `dirname $0`; pwd)
echo $root

export PYTHONPATH=$PYTHONPATH:$root

cd $root

# crawl
cd robot/rss
sh run.sh

# gen index
cd $root
python -m analysis.train
python -m analysis.man_text
python -m analysis.create_tags

# gen rec
cd $root
python recommend/train.py
python recommend/rec.py
