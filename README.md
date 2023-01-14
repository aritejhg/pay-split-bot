# pay-split-bot

## internal workflow

1. image uploaded with a /receipt tag as caption. (check if it works even when someone sends only pic and then edits the caption to say /receipt)
2. maybe can try 2 diff models and fuse results (its a ML hackathon trick LOL) or we exp and find best model
3. ask user to verify. if its wrong, copy paste the message and add the stuff and send back. (need some sort of post-edit command?)
4. once yes/send back, create poll which people can then fill. if not done in xx hours, a reminder is sent auto.
5. after everyone fills poll, create a reply to the og receipt message with a split. 
6. paylahbot integration?? idk how


## external user workflow
1. send image of receipt. 
2. check output. if not correct, copy, edit and send back. 
3. fill up the multi-choice poll sent
4. once everyone fills, split is sent. use paylahbot to pay?