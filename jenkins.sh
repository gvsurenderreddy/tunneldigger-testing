#!/bin/sh
# Alexander Couzens <lynxis@fe80.eu>
#
# jenkins script

set -e

if [ ! -d testing ] ; then
  git clone https://github.com/lynxis/tunneldigger-testing testing
  cd testing
  
  # use git repo managed by jenkins
  ## we have to move the .git into testing and link it back because we mount the git-repo
  ## into the containers which means /testing/git-repo must be a real directory.
  mv $WORKSPACE/tunneldigger/.git git-repo
  ln -s $WORKSPACE/testing/git-repo $WORKSPACE/tunneldigger/.git
  
  ./test_td.py --setup
  cd ..
fi

# retrieve git rev
cd $WORKSPACE/tunneldigger/
NEW_REV=$(git log -1 --format=format:%H)

cd $WORKSPACE/testing/
# test the version aginst itself
./test_td.py -t -s $NEW_REV -c $NEW_REV

OLD_REV="c638231efca6b3a6e1c675ac0834a3e851ad1bdc 7cbe5d60c1b72415e15e573e0a9189f47a3f2094"
# do client NEW_REV against old revs
for rev in $OLD_REV ; do
  ./test_td.py -t -s $rev -c $NEW_REV
done

# do server NEW_REV against old revs
for rev in $OLD_REV ; do
  ./test_td.py -t -s $NEW_REV -c $rev
done
