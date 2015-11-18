#!/bin/sh
# Alexander Couzens <lynxis@fe80.eu>
#
# jenkins script

set -e

if [ ! -d $WORKSPACE/testing ] ; then
  git clone https://github.com/lynxis/tunneldigger-testing testing
  cd testing
  
  # use git repo managed by jenkins
  ## we have to move the .git into testing and link it back because we mount the git-repo
  ## into the containers which means /testing/git-repo must be a real directory.
  mv $WORKSPACE/tunneldigger/.git git-repo
  ln -s $WORKSPACE/testing/git-repo $WORKSPACE/tunneldigger/.git
  
  ./tunneldigger.py --setup
  cd ..
fi

# retrieve git rev
cd $WORKSPACE/tunneldigger/
NEW_REV=$(git log -1 --format=format:%H)

cd $WORKSPACE/testing/
# test the version aginst itself
export CLIENT_REV=$NEW_REV
export SERVER_REV=$NEW_REV
nosetests3

OLD_REV="c638231efca6b3a6e1c675ac0834a3e851ad1bdc 7cbe5d60c1b72415e15e573e0a9189f47a3f2094"
# do client NEW_REV against old revs
for rev in $OLD_REV ; do
  export CLIENT_REV=$NEW_REV
  export SERVER_REV=$rev
  nosetests3
done

# do server NEW_REV against old revs
for rev in $OLD_REV ; do
  export CLIENT_REV=$rev
  export SERVER_REV=$NEW_REV
  nosetests3
done

