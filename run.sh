#!/usr/bin/env bash
root=$(cd `dirname $0`; pwd)
echo $root
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
python -m recommend.train
python -m recommend.rec