import selma

s = selma.SelmaStorySimulation()
s.load_from_file("/Users/oskar/Egna Dokument/Programmering/Selma/cards-test.selma")

for c in s.event_cards.values():
    print(c)

for i in range(0,1):
    s.sim_step()
print(s.log)
