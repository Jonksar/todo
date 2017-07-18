from engine import NetworkingLayer, Record

nl = NetworkingLayer(record=Record())
nl.init(username="joonatan", password='pth29U')

nl.full_sync()


