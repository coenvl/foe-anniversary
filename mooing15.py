def solve(lockedB,lockedT,free,freeB,freeT,freeF,silent=False):
    def _print(msg):
        if not silent:
            print(msg)

    _print('Running solver 1.5 from mooing')
    
    max = 3 * min(sum(lockedB),sum(lockedT))
    starting = 3 * sum(free)
    
    maxP = sum(lockedB) + sum(lockedT) + lockedB[3] + lockedT[3]
    
    totalB = sum(lockedB)
    totalT = sum(lockedT)
    
    totalB2 = lockedB[1] + lockedB[2] + lockedB[3]
    totalT2 = lockedT[1] + lockedT[2] + lockedT[3]
    
    _print("==Explanation==")
    _print('"Free" = Gem you can merge with other gems')
    _print('"Locked" = Locked gem')
    _print('"Bot" = Gem has bottom key piece')
    _print('"Top" = Gem has top key piece')
    _print('"Full" = Gem has a full key')
    
    _print("Merges should be done in the order below, starting with level 1 gems")
    
    _print("\n===NOTE===")
    _print('There has been some confusion on what is the "top" and "bot" key piece. As long as you are consistent, it does not matter which you use, though in-game the round colored piece is "bot" and the tip of the key "top"')
    
    _print("\n==Level 1 Merges==")
    
    while True:
        if free[0] == 0:
            _print("==Level 2 Merges==")
            break
        
        if lockedB[0] == 0 and lockedT[0] == 0:
            if free[0] >= 2:
                free[0] -= 2
                free[1] += 1
                _print("Free L1 + Free L1")
                continue
            else:
                _print("==Level 2 Merges==")
                break
        
        pick = None
        if totalB2 == totalT2:
            if totalB > totalT:
                if lockedT[0] > 0:
                    pick = "Top"
                else:
                    pick = "Bot"
            else:
                if lockedB[0] > 0:
                    pick = "Bot"
                else:
                    pick = "Top"
        elif totalB2 > totalT2:
            if lockedT[0] > 0:
                pick = "Top"
            else:
                pick = "Bot"
        else:
            if lockedB[0] > 0:
                pick = "Bot"
            else:
                pick = "Top"
                
        if pick == "Top":
            free[0] -= 1
            freeT[1] += 1
            lockedT[0] -= 1
            totalT2 += 1
            _print("Free L1 + Locked L1 Top")
        else:
            free[0] -= 1
            freeB[1] += 1
            lockedB[0] -= 1
            totalB2 += 1
            _print("Free L1 + Locked L1 Bot")
    
    totalB3 = lockedB[2] + lockedB[3]
    totalT3 = lockedT[2] + lockedT[3]
    
    while True:
        if free[1] > 1 and (lockedT[1] + freeT[1] > 0) and (lockedB[1] + freeB[1] > 0) and (lockedT[2] + freeT[2] > 0) and (lockedB[2] + freeB[2] > 0):
            if lockedT[1] > 0:
                free[1] -= 1
                lockedT[1] -= 1
                freeT[2] += 1
                _print("Free L2 + Locked L2 Top")
            else:
                free[1] -= 1
                freeT[1] -= 1
                freeT[2] += 1
                _print("Free L2 + Free L2 Top")
            if lockedB[1] > 0:
                free[1] -= 1
                lockedB[1] -= 1
                freeB[2] += 1
                _print("Free L2 + Locked L2 Bot")
            else:
                free[1] -= 1
                freeB[1] -= 1
                freeB[2] += 1
                _print("Free L2 + Free L2 Bot")
        elif freeT[1] > 0 and lockedB[1] > 0:
            freeT[1] -= 1
            freeF[2] += 1
            lockedB[1] -= 1
            _print("Free L2 Top + Locked L2 Bot")
        elif freeB[1] > 0 and lockedT[1] > 0:
            freeB[1] -= 1
            freeF[2] += 1
            lockedT[1] -= 1
            _print("Free L2 Bot + Locked L2 Top")
        elif freeB[1] > 0 and freeT[1] > 0:
            freeB[1] -= 1
            freeT[1] -= 1
            freeF[2] += 1
            _print("Free L2 Bot + Free L2 Top")
        elif free[1] > 0 and (lockedT[1] + lockedB[1]) > 0:
            pick = None
            if totalB3 == totalT3:
                if totalB > totalT:
                    if lockedT[1] > 0:
                        pick = "Top"
                    else:
                        pick = "Bot"
                else:
                    if lockedB[1] > 0:
                        pick = "Bot"
                    else:
                        pick = "Top"
            elif totalB3 > totalT3:
                if lockedT[1] > 0:
                    pick = "Top"
                else:
                    pick = "Bot"
            else:
                if lockedB[1] > 0:
                    pick = "Bot"
                else:
                    pick = "Top"
                    
            if pick == "Top":
                free[1] -= 1
                freeT[2] += 1
                lockedT[1] -= 1
                totalT3 += 1
                _print("Free L2 + Locked L2 Top")
            else:
                free[1] -= 1
                freeB[2] += 1
                lockedB[1] -= 1
                totalB3 += 1
                _print("Free L2 + Locked L2 Bot")
        elif freeT[1] > 0 and lockedT[1] > 0:
            freeT[1] -= 1
            lockedT[1] -= 1
            freeT[2] += 1
            _print("Free L2 Top + Locked L2 Top")
        elif freeB[1] > 0 and lockedB[1] > 0:
            freeB[1] -= 1
            lockedB[1] -= 1
            freeB[2] += 1
            _print("Free L2 Bot + Locked L2 Bot")
        elif freeB[1] > 0 and free[1] > 0:
            freeB[1] -= 1
            free[1] -= 1
            freeB[2] += 1
            _print("Free L2 + Free L2 Bot")
        elif freeT[1] > 0 and free[1] > 0:
            freeT[1] -= 1
            free[1] -= 1
            freeT[2] += 1
            _print("Free L2 + Free L2 Top")
        elif free[1] >= 2:
            free[1] -= 2
            free[2] += 1
            _print("Free L2 + Free L2")
        elif freeT[1] >= 2:
            freeT[1] -= 2
            freeT[2] += 1
            _print("Free L2 Top + Free L2 Top")
        elif freeB[1] >= 2:
            freeB[1] -= 2
            freeB[2] += 1
            _print("Free L2 Bot + Free L2 Bot")
        else:
            _print("==Level 3 Merges==")
            break
          
    totalB4 = lockedB[3]
    totalT4 = lockedT[3]
    while True:
        
        numTopTrios = min(free[3],lockedT[3],lockedB[3])
        
        if free[2] > 1 and (lockedT[2] + freeT[2] > 0) and (lockedB[2] + freeB[2] > 0) and (lockedT[3] - numTopTrios + freeT[3] > 0) and (lockedB[3] - numTopTrios + freeB[3] > 0):
            if lockedT[2] > 0:
                free[2] -= 1
                lockedT[2] -= 1
                freeT[3] += 1
                _print("Free L3 + Locked L3 Top")
            else:
                free[2] -= 1
                freeT[2] -= 1
                freeT[3] += 1
                _print("Free L3 + Free L3 Top")
            if lockedB[2] > 0:
                free[2] -= 1
                lockedB[2] -= 1
                freeB[3] += 1
                _print("Free L3 + Locked L3 Bot")
            else:
                free[2] -= 1
                freeB[2] -= 1
                freeB[3] += 1
                _print("Free L3 + Free L3 Bot")
        elif freeT[2] > 0 and lockedB[2] > 0:
            freeT[2] -= 1
            freeF[3] += 1
            lockedB[2] -= 1
            _print("Free L3 Top + Locked L3 Bot")
        elif freeB[2] > 0 and lockedT[2] > 0:
            freeB[2] -= 1
            freeF[3] += 1
            lockedT[2] -= 1
            _print("Free L3 Bot + Locked L3 Top")
        elif freeB[2] > 0 and freeT[2] > 0:
            freeB[2] -= 1
            freeT[2] -= 1
            freeF[3] += 1
            _print("Free L3 Bot + Free L3 Top")
        elif free[2] > 0 and lockedT[2] > 0 and (lockedB[3] - numTopTrios) > freeT[3]: # and not (free[3] > 0 and lockedT[3] > 0 and lockedB[3] > 0):
            free[2] -= 1
            lockedT[2] -= 1
            freeT[3] += 1
            _print("Free L3 + Locked L3 Top")
        elif free[2] > 0 and lockedB[2] > 0 and (lockedT[3] - numTopTrios) > freeB[3]:# and not (free[3] > 0 and lockedT[3] > 0 and lockedB[3] > 0):
            free[2] -= 1
            lockedB[2] -= 1
            freeB[3] += 1
            _print("Free L3 + Locked L3 Bot")
        elif freeF[2] > 0 and ((free[2] + freeB[2] + freeT[2] + lockedB[2] + lockedT[2]) > 0 or freeF[2] >= 2):
            if lockedB[2] > 0:
                freeF[2] -= 1
                lockedB[2] -= 1
                freeF[3] += 1
                _print("Free L3 Full + Locked L3 Bot")
            elif lockedT[2] > 0:
                freeF[2] -= 1
                lockedT[2] -= 1
                freeF[3] += 1
                _print("Free L3 Full + Locked L3 Top")
            elif free[2] > 0:
                freeF[2] -= 1
                free[2] -= 1
                freeF[3] += 1
                _print("Free L3 Full + Free L3")
            elif freeT[2] > 0:
                freeF[2] -= 1
                freeT[2] -= 1
                freeF[3] += 1
                _print("Free L3 Full + Free L3 Top")
            elif freeB[2] > 0:
                freeF[2] -= 1
                freeB[2] -= 1
                freeF[3] += 1
                _print("Free L3 Full + Free L3 Bot")
            else:
                freeF[2] -= 2
                freeF[3] += 1
                _print("Free L3 Full + Free L3 Full")
        elif free[2] > 0 and (lockedT[2] + lockedB[2]) > 0:
            pick = None
            if totalB4 == totalT4:
                if totalB > totalT:
                    if lockedT[2] > 0:
                        pick = "Top"
                    else:
                        pick = "Bot"
                else:
                    if lockedB[2] > 0:
                        pick = "Bot"
                    else:
                        pick = "Top"
            elif totalB4 > totalT4:
                if lockedT[2] > 0:
                    pick = "Top"
                else:
                    pick = "Bot"
            else:
                if lockedB[2] > 0:
                    pick = "Bot"
                else:
                    pick = "Top"
                    
            if pick == "Top":
                free[2] -= 1
                freeT[3] += 1
                lockedT[2] -= 1
                totalT4 += 1
                _print("Free L3 + Locked L3 Top")
            else:
                free[2] -= 1
                freeB[3] += 1
                lockedB[2] -= 1
                totalB4 += 1
                _print("Free L3 + Locked L3 Bot")
        elif freeT[2] > 0 and lockedT[2] > 0:
            freeT[2] -= 1
            lockedT[2] -= 1
            freeT[3] += 1
            _print("Free L3 Top + Locked L3 Top")
        elif freeB[2] > 0 and lockedB[2] > 0:
            freeB[2] -= 1
            lockedB[2] -= 1
            freeB[3] += 1
            _print("Free L3 Bot + Locked L3 Bot")
        elif freeB[2] > 0 and free[2] > 0:
            freeB[2] -= 1
            free[2] -= 1
            freeB[3] += 1
            _print("Free L3 + Free L3 Bot")
        elif freeT[2] > 0 and free[2] > 0:
            freeT[2] -= 1
            free[2] -= 1
            freeT[3] += 1
            _print("Free L3 + Free L3 Top")
        elif free[2] >= 2:
            free[2] -= 2
            free[3] += 1
            _print("Free L3 + Free L3")
        elif freeT[2] >= 2:
            freeT[2] -= 2
            freeT[3] += 1
            _print("Free L3 Top + Free L3 Top")
        elif freeB[2] >= 2:
            freeB[2] -= 2
            freeB[3] += 1
            _print("Free L3 Bot + Free L3Bot")
        else:
            _print("==Level 4 Merges==")
            break
                
    totalB4 = lockedB[3]
    totalT4 = lockedT[3]
    while True:
        if freeT[3] > 0 and lockedB[3] > 0:
            freeT[3] -= 1
            freeF[3] += 1
            lockedB[3] -= 1
            _print("Free L4 Top + Locked L4 Bot")
        elif freeB[3] > 0 and lockedT[3] > 0:
            freeB[3] -= 1
            freeF[3] += 1
            lockedT[3] -= 1
            _print("Free L4 Bot + Locked L4 Top")
        elif freeB[3] > 0 and freeT[3] > 0:
            freeB[3] -= 1
            freeT[3] -= 1
            freeF[3] += 1
            _print("Free L4 Bot + Free L4 Top")
        elif free[3] > 0 and (lockedT[3] + lockedB[3]) > 0:
            pick = None
            if totalB4 == totalT4:
                if totalB > totalT:
                    if lockedT[3] > 0:
                        pick = "Top"
                    else:
                        pick = "Bot"
                else:
                    if lockedB[3] > 0:
                        pick = "Bot"
                    else:
                        pick = "Top"
            elif totalB4 > totalT4:
                if lockedT[3] > 0:
                    pick = "Top"
                else:
                    pick = "Bot"
            else:
                if lockedB[3] > 0:
                    pick = "Bot"
                else:
                    pick = "Top"
                    
            if pick == "Top":
                free[3] -= 1
                freeT[3] += 1
                lockedT[3] -= 1
                totalT4 -= 1
                _print("Free L4 + Locked L4 Top")
            else:
                free[3] -= 1
                freeB[3] += 1
                lockedB[3] -= 1
                totalB4 -= 1
                _print("Free L4 + Locked L4 Bot")
        elif freeF[3] > 0 and (lockedB[3] + lockedT[3]) > 0:
            if lockedB[3] > 0:
                freeF[3] -= 1
                lockedB[3] -= 1
                freeF[3] += 1
                _print("Free L4 Full + Locked L4 Bot")
            elif lockedT[3] > 0:
                freeF[3] -= 1
                lockedT[3] -= 1
                freeF[3] += 1
                _print("Free L4 Full + Locked L4 Top")
        else:
            _print("==Results==")
            break
    
    res = freeF[2] + 3*freeF[3]
    
    if res == max:
      _print(f"Keys: {res}/{max} (Maximum keys picked up)")
    elif starting == res:
      _print(f"Keys: {res}/{max} (Maximum keys picked up with gems spawned)")
    else:
      _print(f"Keys: {res}/{max} (Likely best possible solution with gems spawned)")
    if freeF[2] > 0:
      if freeF[2] == 1:
        _print(f"- Level 3: {freeF[2]} keys")
      else:
        _print(f"- Level 3: {freeF[2]} keys")
    if freeF[3] > 0:
      if freeF[3] == 1:
        _print(f"- Level 4: {freeF[3]} keys")
      else:
        _print(f"- Level 4: {freeF[3]} keys")
        
    remainingP = sum(lockedB) + sum(lockedT) + lockedB[3] + lockedT[3]
    totalP = maxP - remainingP
    remainingLocked = sum(lockedB) + sum(lockedT)

    unlocked_part = sum(freeB) + sum(freeT)
    unlocked_empty = sum(free)
    
    _print(f"Progress: {totalP}/{maxP} ({remainingLocked} remaining locked gems)")
    _print("Keep in mind these results are only for the selected color")
    return (res,starting,max, totalP,maxP,remainingLocked, unlocked_part,unlocked_empty)