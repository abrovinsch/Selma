import selma, selma_file_reader

s = selma.SelmaStorySimulation()
s.event_cards = selma_file_reader.load_selma_file("/Users/oskar/Egna Dokument/Programmering/Selma/cards-test.selma")

for i in range(0,25):
    s.sim_step()
print(s.log)
