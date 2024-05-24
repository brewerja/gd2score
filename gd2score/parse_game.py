from .models import Game, Inning, HalfInning, AtBat, Runner


class GameParser:
    def parse(self, plays):
        game = Game()

        active_inning = None
        active_half = None
        top_bottom = "top"

        for play in plays:
            inning_num = int(play["about"]["inning"])
            if not active_inning or active_inning.num != inning_num:
                active_inning = Inning(inning_num)
                game.add_inning(active_inning)

            if not active_half or top_bottom != play["about"]["halfInning"]:
                top_bottom = play["about"]["halfInning"]
                active_half = HalfInning()
                active_inning.add_half(active_half)

            ab = AtBat(
                int(play["atBatIndex"]),
                int(play["atBatIndex"]),
                int(play["matchup"]["batter"]["id"]),
                self.build_description(play),
                play["result"].get("eventType", "game_advisory"),
                int(play["matchup"]["pitcher"]["id"]),
                int(play["count"]["outs"]),
                int(play["result"]["homeScore"]),
                int(play["result"]["awayScore"]),
            )

            self.parse_runners(ab, play)
            active_half.add_atbat(ab)

        return game

    def build_description(self, play):
        descriptions = []
        action_index = set(play["actionIndex"])
        if action_index:
            for i, event in enumerate(play["playEvents"]):
                if i in action_index:
                    descriptions.append(event["details"]["description"])
        descriptions.append(play["result"].get("description", ""))
        return " ".join(descriptions)

    def parse_runners(self, ab, play):
        num_events = len(play["playEvents"])
        runner_index = set(play["runnerIndex"])
        # Runners placed on 2nd to begin inning
        for event in play["playEvents"]:
            if event["details"].get("eventType", "") == "runner_placed":
                base = event["base"]
                ab.add_atbat_runner(
                    Runner(event["player"]["id"], base, base, event["index"])
                )
        for i, runner in enumerate(play["runners"]):
            mvmt = runner["movement"]
            start = self.get_base(mvmt["start"])
            end = self.get_base(mvmt["end"])
            if not start and not end:
                continue
            if mvmt["outBase"]:
                end = self.get_base(mvmt["outBase"])

            # Runners that advance multiple bases are listed for each base they
            # advance. Only create one Runner object per person.
            already_added = False
            play_index = int(runner["details"]["playIndex"])
            runner_id = runner["details"]["runner"]["id"]
            for ab_runner in ab.runners:
                if ab_runner.id == runner_id and play_index + 1 == num_events:
                    if end > ab_runner.end:
                        ab_runner.end = end  # Increase end
                    if start < ab_runner.start:
                        ab_runner.start = start  # Decrease start
                    ab_runner.out = mvmt["isOut"]
                    already_added = True
                    break

            if not already_added:
                r = Runner(runner_id, start, end, play_index)
                r.out = mvmt["isOut"]

                if play_index + 1 == num_events:
                    ab.add_atbat_runner(r)
                else:
                    ab.add_mid_pa_runner(r)

    def get_base(self, base):
        if not base:
            return 0
        elif base == "score":
            return 4
        else:
            return int(base[0])
