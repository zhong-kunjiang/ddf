import os

_FINGERPRINTS = {
  "ACURA ILX 2016 ACURAWATCH PLUS": {
    1024L: 5, 513L: 5, 1027L: 5, 1029L: 8, 929L: 4, 1057L: 5, 777L: 8, 1034L: 5, 1036L: 8, 398L: 3, 399L: 7, 145L: 8, 660L: 8, 985L: 3, 923L: 2, 542L: 7, 773L: 7, 800L: 8, 432L: 7, 419L: 8, 420L: 8, 1030L: 5, 422L: 8, 808L: 8, 428L: 8, 304L: 8, 819L: 7, 821L: 5, 57L: 3, 316L: 8, 545L: 4, 464L: 8, 1108L: 8, 597L: 8, 342L: 6, 983L: 8, 344L: 8, 804L: 8, 1039L: 8, 476L: 4, 892L: 8, 490L: 8, 1064L: 7, 882L: 2, 884L: 7, 887L: 8, 888L: 8, 380L: 8, 1365L: 5,
    # sent messages
    0xe4: 5, 0x1fa: 8, 0x200: 3, 0x30c: 8, 0x33d: 5,
  },
  "HONDA CIVIC 2016 TOURING": {
    1024L: 5, 513L: 5, 1027L: 5, 1029L: 8, 777L: 8, 1036L: 8, 1039L: 8, 1424L: 5, 401L: 8, 148L: 8, 662L: 4, 985L: 3, 795L: 8, 773L: 7, 800L: 8, 545L: 6, 420L: 8, 806L: 8, 808L: 8, 1322L: 5, 427L: 3, 428L: 8, 304L: 8, 432L: 7, 57L: 3, 450L: 8, 929L: 8, 330L: 8, 1302L: 8, 464L: 8, 1361L: 5, 1108L: 8, 597L: 8, 470L: 2, 344L: 8, 804L: 8, 399L: 7, 476L: 7, 1633L: 8, 487L: 4, 892L: 8, 490L: 8, 493L: 5, 884L: 8, 891L: 8, 380L: 8, 1365L: 5,
    # sent messages
    0xe4: 5, 0x1fa: 8, 0x200: 3, 0x30c: 8, 0x33d: 5, 0x35e: 8, 0x39f: 8,
  },
  "HONDA CR-V 2016 TOURING": {
    57L: 3, 145L: 8, 316L: 8, 340L: 8, 342L: 6, 344L: 8, 380L: 8, 398L: 3, 399L: 6, 401L: 8, 420L: 8, 422L: 8, 426L: 8, 432L: 7, 464L: 8, 474L: 5, 476L: 4, 487L: 4, 490L: 8, 493L: 3, 507L: 1, 542L: 7, 545L: 4, 597L: 8, 660L: 8, 661L: 4, 773L: 7, 777L: 8, 800L: 8, 804L: 8, 808L: 8, 882L: 2, 884L: 7, 888L: 8, 891L: 8, 892L: 8, 923L: 2, 929L: 8, 983L: 8, 985L: 3, 1024L: 5, 1027L: 5, 1029L: 8, 1033L: 5, 1036L: 8, 1039L: 8, 1057L: 5, 1064L: 7, 1108L: 8, 1125L: 8, 1296L: 8, 1365L: 5, 1424L: 5, 1600L: 5, 1601L: 8,
    # sent messages
    0x194: 4, 0x1fa: 8, 0x30c: 8, 0x33d: 5,
  },
  "TOYOTA RAV4 2017": {
    36L: 8, 37L: 8, 170L: 8, 180L: 8, 186L: 4, 426L: 6, 452L: 8, 464L: 8, 466L: 8, 467L: 8, 547L: 8, 548L: 8, 552L: 4, 562L: 4, 608L: 8, 610L: 5, 643L: 7, 705L: 8, 725L: 2, 740L: 5, 800L: 8, 835L: 8, 836L: 8, 849L: 4, 869L: 7, 870L: 7, 871L: 2, 896L: 8, 897L: 8, 900L: 6, 902L: 6, 905L: 8, 911L: 8, 916L: 3, 918L: 7, 921L: 8, 933L: 8, 944L: 8, 945L: 8, 951L: 8, 955L: 4, 956L: 8, 979L: 2, 998L: 5, 999L: 7, 1000L: 8, 1001L: 8, 1008L: 2, 1014L: 8, 1017L: 8, 1041L: 8, 1042L: 8, 1043L: 8, 1044L: 8, 1056L: 8, 1059L: 1, 1114L: 8, 1161L: 8, 1162L: 8, 1163L: 8, 1176L: 8, 1177L: 8, 1178L: 8, 1179L: 8, 1180L: 8, 1181L: 8, 1190L: 8, 1191L: 8, 1192L: 8, 1196L: 8, 1227L: 8, 1228L: 8, 1235L: 8, 1237L: 8, 1263L: 8, 1279L: 8, 1408L: 8, 1409L: 8, 1410L: 8, 1552L: 8, 1553L: 8, 1554L: 8, 1555L: 8, 1556L: 8, 1557L: 8, 1561L: 8, 1562L: 8, 1568L: 8, 1569L: 8, 1570L: 8, 1571L: 8, 1572L: 8, 1584L: 8, 1589L: 8, 1592L: 8, 1593L: 8, 1595L: 8, 1596L: 8, 1597L: 8, 1600L: 8, 1656L: 8, 1664L: 8, 1728L: 8, 1745L: 8, 1779L: 8, 1904L: 8, 1912L: 8, 1990L: 8, 1998L: 8
  },
}

# support additional internal only fingerprints
try:
  from common.fingerprints_internal import add_additional_fingerprints
  add_additional_fingerprints(_FINGERPRINTS)
except ImportError:
  pass

def eliminate_incompatible_cars(msg, candidate_cars):
  """Removes cars that could not have sent msg.

     Inputs:
      msg: A cereal/log CanData message from the car.
      candidate_cars: A list of cars to consider.

     Returns:
      A list containing the subset of candidate_cars that could have sent msg.
  """
  compatible_cars = []
  for car_name in candidate_cars:
    adr = msg.address
    if msg.src != 0 or (adr in _FINGERPRINTS[car_name] and
                        _FINGERPRINTS[car_name][adr] == len(msg.dat)):
      compatible_cars.append(car_name)
    else:
      pass
      #isin = adr in _FINGERPRINTS[car_name]
      #print "eliminate", car_name, hex(adr), isin, len(msg.dat), msg.dat.encode("hex")
  return compatible_cars

def all_known_cars():
  """Returns a list of all known car strings."""
  return _FINGERPRINTS.keys()

