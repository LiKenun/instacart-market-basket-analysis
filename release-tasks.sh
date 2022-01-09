if [ ! -f products.tsv ] || [ ! -f suggestions.npz ]
then
  if [ ! -f data.zpaq ]
  then
    exit 2
  fi
  zpaq x data.zpaq -force || exit 126
fi
if [ ! -f products.tsv ] || [ ! -f suggestions.npz ]
then
  exit 2
fi
