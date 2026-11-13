# Op SENTINEL — running the outposts on pi00

`sentinel_sim.py` simulates the three outposts for the Day 3 afternoon project ([sentinel.md](../../sentinel.md)).
It runs on the trainer's Pi (`pi00`, `192.168.4.10` on the plant Wi-Fi) and needs only Python 3.

## Start it

1. Copy the file to `pi00` and let the participants' Pis reach it from the plant side only:
   ```bash
   sudo ufw allow in on wlan0 to any port 5020 proto tcp comment 'Op SENTINEL outposts'
   ```
2. Run it in a terminal you keep open (inside `tmux` if you want it to survive a dropped SSH session):
   ```bash
   python3 sentinel_sim.py
   ```
3. Check from any station: `python outpost_read.py`.

## Events

Type a command and press **Enter**. Outposts are `alpha`, `bravo`, `charlie`.

| Command | Effect | What participants should see |
|---|---|---|
| `status` | Prints all three outposts | — |
| `leak <outpost>` | Fuel falls about 15 % a minute | Fuel gauge dropping, then *Fuel low* |
| `refuel <outpost>` | Fuel back to 95 %, leak fixed, generator on | *CLEARED* |
| `genfail <outpost>` | Generator stops; shelter warms up | *Generator stopped*; later the shelter passes 35 °C |
| `genstart <outpost>` | Generator restarts (if it has fuel) | *CLEARED* |
| `gate <outpost>` | Opens or shuts the perimeter gate | *Gate left open* after 2 minutes |
| `resupply <outpost>` | Water back to 95 % | — |
| `silence <outpost>` | Outpost stops answering | Link `lost`, *Outpost not answering* after 60 s |
| `restore <outpost>` | Outpost answers again | Link `up`, *CLEARED* |

Without any events, fuel falls about 0.6 % a minute while a generator runs, so CHARLIE (starting at 34 %) reaches 20 % after roughly 25 minutes, and patrols open a gate for 20 seconds now and then.

## A suggested afternoon

| When | Event |
|---|---|
| After everyone's dashboard shows all three outposts | `silence bravo` for two minutes, then `restore bravo` |
| Later | `leak alpha`, wait for the emails, then `refuel alpha` |
| Later | `genfail charlie`; leave it until the shelter passes 35 °C, then `genstart charlie` |
| Before the debrief | `gate bravo`, wait three minutes, `gate bravo` again |
